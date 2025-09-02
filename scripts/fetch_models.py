#!/usr/bin/env python3
"""
Fetch VibeVoice models into HF cache (public path).

No LAN assumed. Downloads from Hugging Face and verifies integrity.
Places models in standard HF cache layout for compatibility.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

def setup_hf_environment():
    """Setup optimal Hugging Face download environment."""
    # Enable fast downloads if available
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
    
    # Ensure we can download
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)

def fetch_model(model_id: str, revision: str = None):
    """
    Fetch model to HF cache with validation.
    
    Args:
        model_id: Model identifier (1.5B or 7B)
        revision: Git revision to fetch
        
    Returns:
        Local snapshot path
    """
    from huggingface_hub import snapshot_download, HfApi
    
    # Model configurations
    MODELS = {
        "1.5B": {
            "repo_id": "microsoft/VibeVoice-1.5B",
            "revision": revision or os.getenv("VV_1P5B_REV", "cf42b8ff262f8a286bcbe580835cfaad62d277ca"),
            "expected_files": [
                "config.json",
                "model-00001-of-00003.safetensors",
                "model-00002-of-00003.safetensors", 
                "model-00003-of-00003.safetensors",
                "model.safetensors.index.json"
            ]
        },
        "7B": {
            "repo_id": "WestZhang/VibeVoice-Large-pt",
            "revision": revision or os.getenv("VV_7B_REV", "main"),
            "expected_files": [
                "config.json",
                "model.safetensors",
                "generation_config.json"
            ]
        }
    }
    
    if model_id not in MODELS:
        raise ValueError(f"Unknown model: {model_id}. Available: {list(MODELS.keys())}")
    
    config = MODELS[model_id]
    repo_id = config["repo_id"]
    rev = config["revision"]
    
    print(f"📦 Fetching {model_id}: {repo_id}@{rev}")
    
    try:
        # Download to standard HF cache
        snapshot_path = snapshot_download(
            repo_id=repo_id,
            revision=rev,
            local_files_only=False,
            ignore_patterns=["*.pt", "*.bin"],  # Only safetensors
            cache_dir=None  # Use default HF cache
        )
        
        print(f"✅ Downloaded to: {snapshot_path}")
        
        # Validate critical files exist
        missing_files = []
        for expected_file in config["expected_files"]:
            file_path = Path(snapshot_path) / expected_file
            if not file_path.exists():
                missing_files.append(expected_file)
        
        if missing_files:
            print(f"⚠️  Warning: Missing files: {missing_files}")
            print(f"   Model may not work correctly")
        else:
            print(f"✅ All expected files present")
        
        # Also download required tokenizer if needed
        if model_id == "1.5B":
            print(f"📦 Fetching tokenizer: Qwen/Qwen2.5-1.5B")
            tokenizer_path = snapshot_download(
                repo_id="Qwen/Qwen2.5-1.5B",
                local_files_only=False,
                allow_patterns=["tokenizer*", "vocab*", "merges*", "special_tokens*"]
            )
            print(f"✅ Tokenizer ready: {tokenizer_path}")
        
        return snapshot_path
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print(f"💡 Check your internet connection and Hugging Face access")
        raise

def main():
    """Main fetcher entry point."""
    if len(sys.argv) < 2:
        print("Usage: fetch_models.py <model_id> [revision]")
        print("Models: 1.5B, 7B")
        sys.exit(1)
    
    model_id = sys.argv[1]
    revision = sys.argv[2] if len(sys.argv) > 2 else None
    
    setup_hf_environment()
    
    try:
        snapshot_path = fetch_model(model_id, revision)
        
        # Output result as JSON for programmatic use
        result = {
            "model_id": model_id,
            "snapshot_path": snapshot_path,
            "success": True
        }
        
        print(f"\n📊 Fetch Result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        result = {
            "model_id": model_id,
            "error": str(e),
            "success": False
        }
        
        print(f"\n❌ Fetch Failed:")
        print(json.dumps(result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()