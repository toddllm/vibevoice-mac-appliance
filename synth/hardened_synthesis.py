"""
Hardened Synthesis Engine

Production synthesis with golden path validation and metrics.
"""

import time
import json
import numpy as np
import torch
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from mac_config import MODEL_CONFIGS, validate_snapshot
from golden_path_validator import validate_golden_surface
from audio_qc import qc_24k_mono, normalize_audio, crossfade_chunks, save_audio_atomic

class ProductionStreamer:
    """Production streamer with detailed metrics."""
    def __init__(self):
        self.collected = []
        self.put_count = 0
        self.ended = False
        self.first_chunk_time = None
        self.start_time = time.time()

    def put(self, chunks, indices=None):
        """Capture chunks with timing metrics."""
        if self.first_chunk_time is None:
            self.first_chunk_time = time.time()
            
        self.put_count += 1
        chunk_list = chunks if isinstance(chunks, (list, tuple)) else [chunks]
        
        for ch in chunk_list:
            if torch.is_tensor(ch):
                ch = ch.detach().to("cpu", dtype=torch.float32).numpy()
            ch = np.asarray(ch, dtype=np.float32).squeeze()
            ch = np.nan_to_num(ch, copy=False)
            
            if ch.size:
                self.collected.append(ch)

    def end(self, *args):
        """Mark generation complete."""
        self.ended = True
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get streaming metrics."""
        now = time.time()
        first_chunk_ms = ((self.first_chunk_time - self.start_time) * 1000) if self.first_chunk_time else None
        
        return {
            "put_count": self.put_count,
            "chunk_count": len(self.collected),
            "first_chunk_ms": first_chunk_ms,
            "total_samples": sum(len(ch) for ch in self.collected),
            "ended": self.ended
        }

def validate_model_availability(model_id: str) -> bool:
    """Validate model snapshot is complete and available."""
    if model_id not in MODEL_CONFIGS:
        print(f"❌ Unknown model: {model_id}")
        return False
        
    if not validate_snapshot(model_id):
        config = MODEL_CONFIGS[model_id]
        snapshot_path = config["snapshot_path"]
        print(f"❌ Model {model_id} snapshot incomplete or missing:")
        print(f"   Path: {snapshot_path}")
        print(f"   Check: config.json, model-*.safetensors, tokenizer files")
        print(f"💡 Run: ./scripts/sync_hf_cache_from_toddllm.sh")
        return False
    
    print(f"✅ Model {model_id}: Validated and ready")
    return True

def synth_15b_streaming_hardened(proc, model, device, vv_text: str, voice: np.ndarray, 
                                seconds: float, request_id: Optional[str] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Hardened 1.5B streaming with validation and metrics."""
    target_frames = int(seconds * 7.5)
    
    # Prepare inputs
    inputs = proc(
        text=[vv_text],
        voice_samples=[[voice]],
        padding=True,
        return_tensors="pt",
        return_attention_mask=True
    )
    
    for k, v in list(inputs.items()):
        if hasattr(v, "to"):
            inputs[k] = v.to(device)

    # Build generation kwargs
    gen_kwargs = {
        **inputs,
        "tokenizer": proc.tokenizer,
        "max_new_tokens": target_frames,
        "cfg_scale": 1.3,
        "stop_check_fn": lambda: False,
        "refresh_negative": True,
        "verbose": False,
    }
    
    # Golden path validation
    validation = validate_golden_surface("1.5B", gen_kwargs, request_id)
    if not validation["valid"]:
        raise ValueError(f"Golden path validation failed: {validation['errors']}")
    
    # Create streamer with metrics
    streamer = ProductionStreamer()
    gen_kwargs["audio_streamer"] = streamer
    
    # Generate with timing
    start = time.time()
    with torch.no_grad():
        _ = model.generate(**gen_kwargs)
    wall_time = time.time() - start
    
    # Collect and process audio
    if streamer.collected:
        # Apply crossfading for smooth transitions
        audio = crossfade_chunks(streamer.collected, crossfade_samples=8)
    else:
        audio = np.zeros(0, dtype=np.float32)
    
    # Compile metrics
    streaming_metrics = streamer.get_metrics()
    duration = len(audio) / 24000.0
    rtf = duration / max(wall_time, 1e-6)
    
    metrics = {
        "model_id": "1.5B",
        "transport": "streaming",
        "device": device.type,
        "control_hash": validation["control_hash"],
        "wall_time": wall_time,
        "duration": duration,
        "rtf": rtf,
        "target_frames": target_frames,
        **streaming_metrics
    }
    
    return audio, metrics

def synth_7b_offline_hardened(proc, model, device, vv_text: str, voice: np.ndarray,
                             seconds: float, request_id: Optional[str] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Hardened 7B offline synthesis."""
    target_frames = int(seconds * 7.5)
    
    inputs = proc(
        text=[vv_text],
        voice_samples=[[voice]],
        padding=True,
        return_tensors="pt"
    )
    
    for k, v in list(inputs.items()):
        if hasattr(v, "to"):
            inputs[k] = v.to(device)
    
    # Build generation kwargs for 7B offline
    gen_kwargs = {
        **inputs,
        "tokenizer": proc.tokenizer,
        "return_speech": True,
        "max_new_tokens": target_frames,
        "cfg_scale": 1.2,
        "generation_config": {"do_sample": True, "temperature": 0.6}
    }
    
    # Golden path validation
    validation = validate_golden_surface("7B", gen_kwargs, request_id)
    if not validation["valid"]:
        raise ValueError(f"Golden path validation failed: {validation['errors']}")
    
    # Generate
    start = time.time()
    with torch.no_grad():
        outputs = model.generate(**gen_kwargs)
    wall_time = time.time() - start
    
    # Extract audio
    if outputs.speech_outputs and outputs.speech_outputs[0] is not None:
        audio = outputs.speech_outputs[0]
        if torch.is_tensor(audio):
            audio = audio.detach().to("cpu", dtype=torch.float32).numpy().squeeze()
    else:
        audio = np.zeros(0, dtype=np.float32)
    
    # Metrics
    duration = len(audio) / 24000.0
    rtf = duration / max(wall_time, 1e-6)
    
    metrics = {
        "model_id": "7B",
        "transport": "offline", 
        "device": device.type,
        "control_hash": validation["control_hash"],
        "wall_time": wall_time,
        "duration": duration,
        "rtf": rtf,
        "target_frames": target_frames,
        "chunks": 1  # Offline = single output
    }
    
    return audio, metrics

def log_synthesis_metrics(metrics: Dict[str, Any], output_path: str):
    """Log synthesis metrics in JSON format."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "output_path": output_path,
        **metrics
    }
    
    print(json.dumps(log_entry, separators=(',', ':')))

def synthesize_with_validation(model_id: str, text: str, voice_path: str, 
                              seconds: float, output_path: str,
                              request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete synthesis pipeline with validation and metrics.
    
    Args:
        model_id: Model to use ("1.5B" or "7B")
        text: Text to synthesize
        voice_path: Path to voice file
        seconds: Target duration
        output_path: Output WAV path
        request_id: Optional request ID
        
    Returns:
        Synthesis results and metrics
    """
    # Validate model availability
    if not validate_model_availability(model_id):
        return {"success": False, "error": f"Model {model_id} not available"}
    
    # Validate voice
    from audio_qc import validate_voice_file
    voice_validation = validate_voice_file(voice_path)
    if not voice_validation["valid"]:
        return {"success": False, "error": f"Voice validation failed: {voice_validation['errors']}"}
    
    # Load models
    config = MODEL_CONFIGS[model_id]
    device_type = config["device"]
    device = torch.device(device_type if device_type != "mps" or torch.backends.mps.is_available() else "cpu")
    dtype = getattr(torch, config["dtype"])
    
    try:
        from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor
        from vibevoice.modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference
        
        snapshot_path = config["snapshot_path"]
        proc = VibeVoiceProcessor.from_pretrained(snapshot_path, trust_remote_code=True, local_files_only=True)
        model = VibeVoiceForConditionalGenerationInference.from_pretrained(
            snapshot_path,
            trust_remote_code=True,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
            local_files_only=True,
            attn_implementation=config["control_surface"]["attn_implementation"]
        ).to(device).eval()
        
        # Load and validate voice
        from mac_production_ready import load_voice_24k  # Reuse existing function
        voice = load_voice_24k(voice_path)
        
        # Convert text to VibeVoice format
        vv_text = text if re.search(r"^Speaker\s+\d+:", text, flags=re.M) else f"Speaker 0: {text.strip()}"
        
        # Synthesize using appropriate method
        if model_id == "1.5B":
            audio, metrics = synth_15b_streaming_hardened(proc, model, device, vv_text, voice, seconds, request_id)
        else:
            audio, metrics = synth_7b_offline_hardened(proc, model, device, vv_text, voice, seconds, request_id)
        
        # Save with atomic write and QC
        if len(audio) > 0:
            save_result = save_audio_atomic(audio, output_path)
            metrics.update(save_result)
            
            # Log metrics
            log_synthesis_metrics(metrics, output_path)
            
            return {
                "success": True,
                "metrics": metrics,
                "output_path": output_path
            }
        else:
            return {"success": False, "error": "No audio generated", "metrics": metrics}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Export main synthesis function
__all__ = ["synthesize_with_validation", "validate_model_availability", "log_synthesis_metrics"]