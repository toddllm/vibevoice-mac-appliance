"""
Atomic Audio Operations

Crash-safe file operations and production utilities.
"""

import os
import tempfile
import shutil
import hashlib
import json
from pathlib import Path
from typing import Dict, Any
import numpy as np
import soundfile as sf

def atomic_write_wav(path: str, audio: np.ndarray, sample_rate: int = 24000, 
                    normalize: bool = True) -> Dict[str, Any]:
    """
    Atomically write WAV file with crash safety.
    
    Args:
        path: Output path
        audio: Audio array (float32)
        sample_rate: Sample rate
        normalize: Whether to normalize to -1dBFS
        
    Returns:
        Write result with metrics
    """
    from audio_qc import normalize_audio, qc_24k_mono
    
    # Ensure float32
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    
    # QC validation
    qc_metrics = qc_24k_mono(audio)
    
    # Normalize if requested
    if normalize:
        audio = normalize_audio(audio, target_dbfs=-1.0)
    
    # Create parent directory
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Write to temporary file first
    tmp_path = path + ".tmp"
    
    try:
        # Write audio
        sf.write(tmp_path, audio, sample_rate, subtype="PCM_16")
        
        # Force sync to disk
        with open(tmp_path, 'rb') as f:
            os.fsync(f.fileno())
        
        # Atomic rename
        os.replace(tmp_path, path)
        
        # Get final file info
        file_size = os.path.getsize(path)
        
        return {
            "success": True,
            "path": path,
            "file_size": file_size,
            "qc_metrics": qc_metrics,
            "normalized": normalize
        }
        
    except Exception as e:
        # Clean up temp file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        raise e

def compute_file_hash(path: str) -> str:
    """Compute SHA256 hash of file."""
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_cache_integrity(model_id: str) -> Dict[str, Any]:
    """
    Verify model cache integrity with SHA256 checks.
    
    Args:
        model_id: Model to verify
        
    Returns:
        Verification results
    """
    from mac_config import MODEL_CONFIGS
    
    result = {
        "model_id": model_id,
        "valid": True,
        "files": {},
        "errors": []
    }
    
    if model_id not in MODEL_CONFIGS:
        result["valid"] = False
        result["errors"].append(f"Unknown model: {model_id}")
        return result
    
    config = MODEL_CONFIGS[model_id]
    snapshot_path = Path(config["snapshot_path"])
    
    if not snapshot_path.exists():
        result["valid"] = False
        result["errors"].append(f"Snapshot path not found: {snapshot_path}")
        return result
    
    # Check critical files
    critical_files = [
        "config.json",
        "model-00001-of-00003.safetensors",
        "model-00002-of-00003.safetensors", 
        "model-00003-of-00003.safetensors",
        "model.safetensors.index.json"
    ]
    
    for file in critical_files:
        file_path = snapshot_path / file
        
        if file_path.exists():
            # Check if it's a symlink and target exists
            if file_path.is_symlink():
                target = file_path.resolve()
                if target.exists():
                    file_hash = compute_file_hash(target)
                    file_size = target.stat().st_size
                    result["files"][file] = {
                        "present": True,
                        "symlink": True,
                        "target": str(target),
                        "size": file_size,
                        "hash": file_hash[:16]  # Short hash for display
                    }
                else:
                    result["valid"] = False
                    result["errors"].append(f"Broken symlink: {file} -> {target}")
            else:
                file_hash = compute_file_hash(file_path)
                file_size = file_path.stat().st_size
                result["files"][file] = {
                    "present": True,
                    "symlink": False,
                    "size": file_size,
                    "hash": file_hash[:16]
                }
        else:
            result["valid"] = False
            result["errors"].append(f"Missing file: {file}")
    
    return result

def create_integrity_manifest(model_id: str, output_path: str) -> bool:
    """Create integrity manifest for model cache."""
    verification = verify_cache_integrity(model_id)
    
    manifest = {
        "created": datetime.now().isoformat(),
        "model_id": model_id,
        "verification": verification
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        return True
    except Exception as e:
        print(f"Failed to create manifest: {e}")
        return False

def validate_with_manifest(model_id: str, manifest_path: str) -> bool:
    """Validate model cache against stored manifest."""
    try:
        with open(manifest_path, 'r') as f:
            stored_manifest = json.load(f)
        
        current_verification = verify_cache_integrity(model_id)
        stored_verification = stored_manifest["verification"]
        
        # Compare file hashes
        stored_files = stored_verification.get("files", {})
        current_files = current_verification.get("files", {})
        
        for file, stored_info in stored_files.items():
            if file not in current_files:
                print(f"❌ File missing: {file}")
                return False
                
            current_info = current_files[file]
            if stored_info.get("hash") != current_info.get("hash"):
                print(f"❌ File changed: {file}")
                print(f"   Expected: {stored_info.get('hash')}")
                print(f"   Actual: {current_info.get('hash')}")
                return False
        
        print(f"✅ Cache integrity verified against manifest")
        return True
        
    except Exception as e:
        print(f"❌ Manifest validation failed: {e}")
        return False

# Failure injection for testing
def inject_failure(failure_type: str, **kwargs):
    """Inject controlled failures for testing robustness."""
    if failure_type == "drop_first_chunk":
        # Simulate first chunk drop
        class DropFirstStreamer:
            def __init__(self, real_streamer):
                self.real_streamer = real_streamer
                self.dropped_first = False
                
            def put(self, chunks, indices=None):
                if not self.dropped_first:
                    self.dropped_first = True
                    print("🧪 Injected: Dropping first chunk")
                    return
                return self.real_streamer.put(chunks, indices)
                
            def end(self, *args):
                return self.real_streamer.end(*args)
        
        return DropFirstStreamer
        
    elif failure_type == "nan_audio":
        # Inject NaN into audio
        def inject_nan(audio):
            if len(audio) > 100:
                audio[50:60] = np.nan
                print("🧪 Injected: NaN audio samples")
            return audio
        return inject_nan
        
    elif failure_type == "stall_end_signal":
        # Simulate end signal delay
        import time
        class StallEndStreamer:
            def __init__(self, real_streamer):
                self.real_streamer = real_streamer
                
            def put(self, chunks, indices=None):
                return self.real_streamer.put(chunks, indices)
                
            def end(self, *args):
                print("🧪 Injected: Stalling end signal for 5s")
                time.sleep(5)
                return self.real_streamer.end(*args)
        
        return StallEndStreamer
    
    else:
        raise ValueError(f"Unknown failure type: {failure_type}")

__all__ = [
    "atomic_write_wav", 
    "verify_cache_integrity", 
    "create_integrity_manifest",
    "validate_with_manifest",
    "inject_failure"
]