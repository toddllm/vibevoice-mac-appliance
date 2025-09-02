"""
vvctl diag command

Single command diagnostic output for issue reporting.
"""

import json
import os
import time
import torch
from datetime import datetime
from pathlib import Path

def cmd_diag(args):
    """Comprehensive diagnostic output for issue reporting."""
    
    diag_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {},
        "environment": {},
        "models": {},
        "performance": {},
        "health": {}
    }
    
    # System info
    import platform
    diag_data["system"] = {
        "platform": platform.system(),
        "machine": platform.machine(), 
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "pytorch_version": torch.__version__
    }
    
    # Environment variables
    env_keys = [
        "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "TRANSFORMERS_NO_FLASH_ATTENTION",
        "PYTORCH_ENABLE_MPS_FALLBACK", "PYTORCH_MPS_HIGH_WATERMARK_RATIO",
        "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"
    ]
    
    diag_data["environment"] = {key: os.environ.get(key, "unset") for key in env_keys}
    
    # Device capabilities
    diag_data["devices"] = {
        "mps_available": torch.backends.mps.is_available(),
        "mps_device_count": 1 if torch.backends.mps.is_available() else 0,
        "cpu_count": os.cpu_count()
    }
    
    # Model status
    from mac_config import MODEL_CONFIGS, validate_snapshot
    
    for model_id in ["1.5B", "7B"]:
        config = MODEL_CONFIGS.get(model_id, {})
        snapshot_path = config.get("snapshot_path", "")
        
        model_info = {
            "snapshot_path": snapshot_path,
            "exists": os.path.exists(snapshot_path) if snapshot_path else False,
            "validated": validate_snapshot(model_id) if snapshot_path else False,
            "device_policy": f"{config.get('device', 'unknown')}/{config.get('dtype', 'unknown')}"
        }
        
        # Get snapshot hash if available
        if os.path.exists(snapshot_path):
            try:
                config_path = os.path.join(snapshot_path, "config.json")
                if os.path.exists(config_path):
                    import hashlib
                    with open(config_path, 'rb') as f:
                        config_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    model_info["config_hash"] = config_hash
            except:
                pass
        
        diag_data["models"][model_id] = model_info
    
    # Performance baseline (if recent metrics available)
    try:
        # Check for recent benchmark or warmup data
        if os.path.exists("temp/last_warmup.json"):
            with open("temp/last_warmup.json", "r") as f:
                warmup_data = json.load(f)
                diag_data["performance"]["last_warmup"] = warmup_data
    except:
        pass
    
    # Voice directory status
    voices_dir = Path("demo/voices")
    if voices_dir.exists():
        voices = list(voices_dir.glob("*.wav"))
        diag_data["voices"] = {
            "directory_exists": True,
            "count": len(voices),
            "files": [v.name for v in voices[:5]]  # First 5
        }
    else:
        diag_data["voices"] = {"directory_exists": False}
    
    # Output directory status
    out_dir = Path("out")
    if out_dir.exists():
        recent_files = sorted(out_dir.glob("*.wav"), key=lambda x: x.stat().st_mtime, reverse=True)
        diag_data["output"] = {
            "directory_exists": True,
            "recent_files": len(recent_files),
            "latest_file": recent_files[0].name if recent_files else None,
            "total_size_mb": sum(f.stat().st_size for f in recent_files) // 1024 // 1024
        }
    else:
        diag_data["output"] = {"directory_exists": False}
    
    # Health summary
    models_ready = sum(1 for m in diag_data["models"].values() if m["validated"])
    diag_data["health"] = {
        "models_ready": f"{models_ready}/{len(diag_data['models'])}",
        "mps_available": diag_data["devices"]["mps_available"],
        "environment_ok": all(diag_data["environment"][k] == "1" for k in ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"]),
        "ready_for_synthesis": models_ready > 0
    }
    
    if args.json:
        print(json.dumps(diag_data, indent=2))
    else:
        # Human-readable format
        print("🔍 Mac VibeVoice Diagnostic Report")
        print("=" * 50)
        
        print(f"\n💻 System:")
        print(f"   Platform: {diag_data['system']['platform']} {diag_data['system']['machine']}")
        print(f"   Python: {diag_data['system']['python_version']}")
        print(f"   PyTorch: {diag_data['system']['pytorch_version']}")
        print(f"   MPS: {'Available' if diag_data['devices']['mps_available'] else 'Not available'}")
        
        print(f"\n🤖 Models:")
        for model_id, info in diag_data["models"].items():
            status = "✅ Ready" if info["validated"] else "❌ Missing"
            print(f"   {model_id}: {status} ({info['device_policy']})")
            if info.get("config_hash"):
                print(f"      Config hash: {info['config_hash']}")
        
        print(f"\n🎤 Voices: {diag_data['voices']['count']} available" if diag_data['voices']['directory_exists'] else "\n🎤 Voices: Directory not found")
        
        print(f"\n📁 Output: {diag_data['output']['recent_files']} files" if diag_data['output']['directory_exists'] else "\n📁 Output: Directory not found")
        
        if diag_data["performance"].get("last_warmup"):
            warmup = diag_data["performance"]["last_warmup"]
            print(f"\n🔥 Last warmup: {warmup['warmup_time']:.2f}s")
        
        print(f"\n🎯 Status: {'Ready for synthesis' if diag_data['health']['ready_for_synthesis'] else 'Setup required'}")
        
        if not diag_data['health']['ready_for_synthesis']:
            print(f"💡 Run: ./scripts/sync_hf_cache_from_toddllm.sh")
    
    return 0

# Add this to vvctl_final main() subparsers:
def add_diag_command(subparsers):
    """Add diagnostic command to CLI."""
    diag_parser = subparsers.add_parser("diag", help="System diagnostic for issue reporting")
    diag_parser.add_argument("--json", action="store_true", help="Output JSON format")
    return diag_parser