"""
Golden Path Validator

Validates control surface parameters for stable VibeVoice generation.
Ensures frozen control surface compliance.
"""

import hashlib
import json
from typing import Dict, Any, Optional

# Frozen control surface for 1.5B streaming (proven working)
GOLDEN_1P5B_STREAMING = {
    "cfg_scale": 1.3,
    "refresh_negative": True,
    "verbose": False,
    "stop_check_fn": "lambda",  # Special handling for functions
}

# Frozen control surface for 7B offline
GOLDEN_7B_OFFLINE = {
    "cfg_scale": 1.2,
    "return_speech": True,
    "generation_config": {"do_sample": True, "temperature": 0.6}
}

class GoldenPathValidator:
    """Validates generation parameters against golden paths."""
    
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.golden_params = self._get_golden_params()
        
    def _get_golden_params(self) -> Dict[str, Any]:
        """Get golden parameters for model."""
        if self.model_id == "1.5B":
            return GOLDEN_1P5B_STREAMING
        elif self.model_id == "7B":
            return GOLDEN_7B_OFFLINE
        else:
            return {}
    
    def validate_control_surface(self, gen_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate generation kwargs against golden path.
        
        Args:
            gen_kwargs: Generation parameters
            
        Returns:
            Validation result with warnings/errors
        """
        result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "control_hash": self._compute_hash(gen_kwargs)
        }
        
        # Check required parameters
        for param, expected in self.golden_params.items():
            if param == "stop_check_fn":
                # Special handling for functions
                if param not in gen_kwargs:
                    result["errors"].append(f"Missing required parameter: {param}")
                continue
                
            if param not in gen_kwargs:
                result["errors"].append(f"Missing required parameter: {param}")
                continue
                
            actual = gen_kwargs[param]
            
            if param == "generation_config":
                # Deep check for generation config
                if not isinstance(actual, dict):
                    result["errors"].append(f"{param} must be dict, got {type(actual)}")
                    continue
                    
                for key, val in expected.items():
                    if key not in actual:
                        result["warnings"].append(f"Missing generation_config.{key}")
                    elif actual[key] != val:
                        result["warnings"].append(f"generation_config.{key}: expected {val}, got {actual[key]}")
            else:
                if actual != expected:
                    result["warnings"].append(f"{param}: expected {expected}, got {actual}")
        
        # Check for unexpected parameters
        expected_keys = set(self.golden_params.keys())
        expected_keys.update(["input_ids", "attention_mask", "voice_samples", "tokenizer", 
                             "audio_streamer", "max_new_tokens"])  # Allow these
        
        for key in gen_kwargs:
            if key not in expected_keys:
                result["warnings"].append(f"Unexpected parameter: {key}")
        
        if result["errors"]:
            result["valid"] = False
            
        return result
    
    def _compute_hash(self, gen_kwargs: Dict[str, Any]) -> str:
        """Compute hash of control surface parameters."""
        # Create hashable representation
        hashable = {}
        for key, value in gen_kwargs.items():
            if key in ["input_ids", "attention_mask", "voice_samples", "tokenizer", "audio_streamer"]:
                continue  # Skip data/object parameters
            elif callable(value):
                hashable[key] = "callable"
            elif isinstance(value, dict):
                hashable[key] = json.dumps(value, sort_keys=True)
            else:
                hashable[key] = str(value)
        
        hash_input = json.dumps(hashable, sort_keys=True)
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    def log_validation(self, result: Dict[str, Any], request_id: Optional[str] = None):
        """Log validation results."""
        prefix = f"[{request_id}] " if request_id else ""
        
        if result["valid"]:
            print(f"✅ {prefix}Golden path validation passed (hash: {result['control_hash']})")
        else:
            print(f"❌ {prefix}Golden path validation failed (hash: {result['control_hash']})")
            
        for warning in result["warnings"]:
            print(f"⚠️  {prefix}{warning}")
            
        for error in result["errors"]:
            print(f"❌ {prefix}{error}")

def validate_golden_surface(model_id: str, gen_kwargs: Dict[str, Any], request_id: Optional[str] = None):
    """
    Validate generation parameters against golden path.
    
    Args:
        model_id: Model identifier ("1.5B" or "7B")
        gen_kwargs: Generation parameters to validate
        request_id: Optional request ID for logging
        
    Returns:
        Validation result dictionary
    """
    validator = GoldenPathValidator(model_id)
    result = validator.validate_control_surface(gen_kwargs)
    validator.log_validation(result, request_id)
    return result

# Quick validation helpers
def ensure_15b_streaming_golden(gen_kwargs: Dict[str, Any]) -> bool:
    """Ensure 1.5B streaming uses golden path."""
    result = validate_golden_surface("1.5B", gen_kwargs)
    return result["valid"]

def ensure_7b_offline_golden(gen_kwargs: Dict[str, Any]) -> bool:
    """Ensure 7B offline uses golden path.""" 
    result = validate_golden_surface("7B", gen_kwargs)
    return result["valid"]