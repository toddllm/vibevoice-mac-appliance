"""
Mac VibeVoice Configuration

Centralized configuration for stable Mac deployment.
"""

import os

# Pinned snapshot paths (known-good, complete models)
SNAP_1P5B = os.path.expanduser(
    "~/.cache/huggingface/hub/models--microsoft--VibeVoice-1.5B/snapshots/cf42b8ff262f8a286bcbe580835cfaad62d277ca"
)

SNAP_7B = os.path.expanduser(
    "~/.cache/huggingface/hub/models--WestZhang--VibeVoice-Large-pt/snapshots/0b68ee6da8ca6bca98484758d06cbe9c33f49e7b"
)  # Update with actual 7B snapshot when synced

# Environment configuration
MAC_ENV = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1", 
    "TRANSFORMERS_NO_FLASH_ATTENTION": "1",
    "PYTORCH_ENABLE_MPS_FALLBACK": "1",
    "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "0.0",
    "OMP_NUM_THREADS": "8",
    "VECLIB_MAXIMUM_THREADS": "8"
}

# Model configurations
MODEL_CONFIGS = {
    "1.5B": {
        "snapshot_path": SNAP_1P5B,
        "device": "cpu",
        "dtype": "float32",
        "transport": "streaming",
        "control_surface": {
            "cfg_scale": 1.3,
            "refresh_negative": True,
            "verbose": False,
            "attn_implementation": "eager"
        },
        "performance": {
            "target_rtf": 0.15,
            "max_wall_seconds": 60,
            "chunk_size": 3200,
            "frame_rate": 7.5
        }
    },
    "7B": {
        "snapshot_path": SNAP_7B,
        "device": "mps",  # Falls back to CPU if MPS unavailable
        "dtype": "float16",
        "transport": "offline",
        "control_surface": {
            "cfg_scale": 1.2,
            "return_speech": True,
            "generation_config": {"do_sample": True, "temperature": 0.6},
            "attn_implementation": "sdpa"
        },
        "performance": {
            "target_rtf": 0.8,
            "max_wall_seconds": 30,
            "frame_rate": 7.5
        }
    }
}

# Voice validation settings
VOICE_VALIDATION = {
    "sample_rate": 24000,
    "min_duration": 0.4,
    "max_duration": 30.0,
    "target_peak_dbfs": -1.0,
    "supported_formats": [".wav", ".mp3", ".flac", ".m4a"]
}

# Output settings
OUTPUT_CONFIG = {
    "sample_rate": 24000,
    "format": "PCM_16", 
    "peak_normalize": -1.0,  # dBFS
    "output_dir": "out",
    "temp_dir": "temp"
}

def setup_environment():
    """Setup Mac environment variables."""
    for key, value in MAC_ENV.items():
        os.environ.setdefault(key, value)

def validate_snapshot(model_id: str) -> bool:
    """Validate model snapshot is complete."""
    config = MODEL_CONFIGS.get(model_id)
    if not config:
        return False
    
    snapshot_path = config["snapshot_path"]
    if not os.path.exists(snapshot_path):
        return False
    
    # Check required files
    required_files = [
        "config.json",
        "model-00001-of-00003.safetensors",
        "model-00002-of-00003.safetensors", 
        "model-00003-of-00003.safetensors",
        "model.safetensors.index.json"
    ]
    
    for file in required_files:
        if not os.path.exists(os.path.join(snapshot_path, file)):
            return False
    
    return True

def get_model_config(model_id: str):
    """Get configuration for model."""
    return MODEL_CONFIGS.get(model_id, MODEL_CONFIGS["1.5B"])

def get_voice_config():
    """Get voice validation config."""
    return VOICE_VALIDATION

def get_output_config():
    """Get output configuration."""
    return OUTPUT_CONFIG