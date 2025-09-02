#!/usr/bin/env python3
"""
Mac VibeVoice Production Server

Production Flask server with device policy and LLM bypass.
"""

import os
import re
import time
import json
import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import numpy as np
import torch

# Environment setup
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_NO_FLASH_ATTENTION", "1")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.0")
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "8")

app = Flask(__name__)
CORS(app)

def pick_device(model_id: str):
    """Device policy for Mac."""
    if model_id == "1.5B":
        return torch.device("cpu"), torch.float32
    elif model_id == "7B":
        return (torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu"),
                torch.float16 if torch.backends.mps.is_available() else torch.float32)
    else:
        return torch.device("cpu"), torch.float32

def looks_vibevoice(text: str) -> bool:
    """Check if text is already in Speaker N: format."""
    return bool(re.search(r"^Speaker\s+\d+:", text, flags=re.M))

def to_vv_format(text: str) -> str:
    """Convert to VibeVoice format."""
    return text if looks_vibevoice(text) else f"Speaker 0: {text.strip()}"

# Global model cache
MODEL_CACHE = {}

def load_model(model_id: str):
    """Load model with caching."""
    if model_id in MODEL_CACHE:
        return MODEL_CACHE[model_id]
    
    from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor
    from vibevoice.modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference
    
    device, dtype = pick_device(model_id)
    
    # Get snapshot path
    if model_id == "1.5B":
        snapshot_path = os.path.expanduser(
            "~/.cache/huggingface/hub/models--microsoft--VibeVoice-1.5B/snapshots/cf42b8ff262f8a286bcbe580835cfaad62d277ca"
        )
    else:
        return None  # 7B not implemented yet
    
    proc = VibeVoiceProcessor.from_pretrained(snapshot_path, trust_remote_code=True, local_files_only=True)
    model = VibeVoiceForConditionalGenerationInference.from_pretrained(
        snapshot_path,
        trust_remote_code=True,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
        local_files_only=True,
        attn_implementation="eager"
    ).to(device).eval()
    
    MODEL_CACHE[model_id] = (proc, model, device, dtype)
    return MODEL_CACHE[model_id]

@app.route('/health')
def health():
    """Health check endpoint."""
    device_info = {
        "mps_available": torch.backends.mps.is_available(),
        "device_policy": {
            "1.5B": "cpu/fp32 (streaming)",
            "7B": "mps/fp16 (offline)" if torch.backends.mps.is_available() else "cpu/fp32"
        }
    }
    
    return jsonify({
        "status": "healthy",
        "mac_profile": True,
        "offline_mode": True,
        "device_info": device_info,
        "llm": {"enabled": False}  # Mac bypasses LLM for Speaker N: text
    })

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Main synthesis endpoint with Mac optimizations."""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        model_id = data.get('model', '1.5B')
        seconds = float(data.get('seconds', 6.0))
        
        if not text:
            return jsonify({"error": "Empty text"}), 400
        
        # Mac optimization: bypass LLM for Speaker N: format
        if looks_vibevoice(text):
            processed_text = text
            print(f"Mac: Using pre-formatted text (skipping LLM)")
        else:
            processed_text = to_vv_format(text)
            print(f"Mac: Wrapped text in Speaker 0 format")
        
        # Load model
        try:
            proc, model, device, dtype = load_model(model_id)
        except Exception as e:
            return jsonify({"error": f"Model load failed: {e}"}), 500
        
        # Generate audio using appropriate method
        start_time = time.time()
        
        # For now, use CPU streaming (working path)
        from mac_production_ready import synth_15b_streaming, load_voice_24k
        
        voice = load_voice_24k("VibeVoice/demo/voices/en-Carter_man.wav")
        audio, chunks = synth_15b_streaming(proc, model, device, processed_text, voice, seconds)
        
        gen_time = time.time() - start_time
        
        if len(audio) > 0:
            # Save temporary file
            temp_id = str(uuid.uuid4())
            temp_path = f"temp_{temp_id}.wav"
            
            # Normalize and save
            peak = float(np.max(np.abs(audio))) or 1.0
            if peak > 0:
                audio = np.clip(audio / peak * 0.95, -1.0, 1.0)
            sf.write(temp_path, audio, 24000, subtype="PCM_16")
            
            duration = len(audio) / 24000
            rtf = duration / gen_time
            
            # Return success response
            return jsonify({
                "success": True,
                "audio_file": temp_path,
                "duration": duration,
                "generation_time": gen_time,
                "rtf": rtf,
                "chunks": chunks,
                "model": model_id,
                "device": device.type,
                "transport": "streaming" if model_id == "1.5B" else "offline"
            })
        else:
            return jsonify({"error": "No audio generated"}), 500
            
    except Exception as e:
        print(f"Synthesis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/models')
def list_models():
    """List available models."""
    return jsonify({
        "models": [
            {
                "id": "1.5B",
                "name": "VibeVoice-1.5B", 
                "device": "cpu",
                "transport": "streaming",
                "available": get_snapshot_path("1.5B") is not None
            },
            {
                "id": "7B",
                "name": "VibeVoice-7B",
                "device": "mps" if torch.backends.mps.is_available() else "cpu", 
                "transport": "offline",
                "available": get_snapshot_path("7B") is not None
            }
        ]
    })

def get_snapshot_path(model_id: str):
    """Get snapshot path for model."""
    if model_id == "1.5B":
        path = os.path.expanduser(
            "~/.cache/huggingface/hub/models--microsoft--VibeVoice-1.5B/snapshots/cf42b8ff262f8a286bcbe580835cfaad62d277ca"
        )
        return path if os.path.exists(path) else None
    elif model_id == "7B":
        base_path = os.path.expanduser("~/.cache/huggingface/hub/models--WestZhang--VibeVoice-Large-pt")
        if os.path.exists(base_path):
            snapshots = os.path.join(base_path, "snapshots")
            if os.path.exists(snapshots):
                snap_dirs = [d for d in os.listdir(snapshots) if os.path.isdir(os.path.join(snapshots, d))]
                if snap_dirs:
                    return os.path.join(snapshots, snap_dirs[0])
    return None

if __name__ == "__main__":
    print("🎯 Mac VibeVoice Production Server")
    print("Device policy: 1.5B on CPU, 7B on MPS")
    print("Offline mode: Models from local cache only")
    print("")
    
    port = int(os.getenv("PORT", "5001"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting on {host}:{port}")
    print(f"🏥 Health: http://localhost:{port}/health")
    print(f"🎙️  Synthesis: POST http://localhost:{port}/synthesize")
    
    app.run(host=host, port=port, debug=False, threaded=True)