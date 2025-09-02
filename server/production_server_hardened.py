#!/usr/bin/env python3
"""
Hardened Mac VibeVoice Production Server

Production Flask server with backpressure, validation, and metrics.
"""

import os
import re
import time
import json
import uuid
import threading
from queue import Empty
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import numpy as np
import torch

# Hardened environment
ENV_VARS = {
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "TRANSFORMERS_NO_FLASH_ATTENTION": "1",
    "PYTORCH_ENABLE_MPS_FALLBACK": "1",
    "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "0.0",
    "OMP_NUM_THREADS": "8",
    "VECLIB_MAXIMUM_THREADS": "8"
}

for key, value in ENV_VARS.items():
    os.environ.setdefault(key, value)

from hardened_synthesis import synthesize_with_validation, validate_model_availability
from atomic_audio import atomic_write_wav

app = Flask(__name__)
CORS(app)

# One-slot semaphore for 1.5B CPU stability
_1P5B_SEM = threading.Semaphore(1)

# Request metrics
_REQUEST_METRICS = []
_METRICS_LOCK = threading.Lock()

def log_request_metrics(metrics: dict):
    """Log request metrics with rotation."""
    with _METRICS_LOCK:
        metrics["timestamp"] = datetime.utcnow().isoformat()
        _REQUEST_METRICS.append(metrics)
        
        # Keep last 100 requests
        if len(_REQUEST_METRICS) > 100:
            _REQUEST_METRICS.pop(0)
    
    # Also log to stdout as JSON
    print(json.dumps(metrics, separators=(',', ':')))

def looks_vibevoice(text: str) -> bool:
    """Check if text is pre-formatted."""
    return bool(re.search(r"^Speaker\s+\d+:", text, flags=re.M))

@app.route('/health')
def health():
    """Enhanced health endpoint with metrics."""
    # Calculate recent performance
    with _METRICS_LOCK:
        recent = _REQUEST_METRICS[-10:] if _REQUEST_METRICS else []
    
    performance = {}
    if recent:
        rtfs = [m.get('rtf', 0) for m in recent if m.get('rtf')]
        first_chunks = [m.get('first_chunk_ms', 0) for m in recent if m.get('first_chunk_ms')]
        
        if rtfs:
            performance["rtf_p50"] = sorted(rtfs)[len(rtfs)//2]
        if first_chunks:
            performance["first_chunk_p95"] = sorted(first_chunks)[int(len(first_chunks)*0.95)]
    
    return jsonify({
        "status": "healthy",
        "mac_profile": True,
        "offline_mode": True,
        "device_policy": {
            "1.5B": "cpu/fp32 (streaming)",
            "7B": "mps/fp16 (offline)" if torch.backends.mps.is_available() else "cpu/fp32"
        },
        "models": {
            "1.5B": {"available": validate_model_availability("1.5B")},
            "7B": {"available": validate_model_availability("7B")}
        },
        "llm": {"enabled": False},  # Mac bypasses LLM for Speaker N: text
        "performance": performance,
        "request_count": len(_REQUEST_METRICS)
    })

@app.route('/synthesize', methods=['POST'])
def synthesize():
    """Hardened synthesis with backpressure and validation."""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        model_id = data.get('model', '1.5B')
        seconds = float(data.get('seconds', 6.0))
        
        if not text:
            return jsonify({"error": "Empty text"}), 400
            
        if seconds > 30.0:
            return jsonify({"error": "Duration too long (max 30s)"}), 400
        
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        
        # One-slot backpressure for 1.5B
        if model_id == "1.5B":
            if not _1P5B_SEM.acquire(blocking=False):
                return jsonify({
                    "error": "Server busy with 1.5B synthesis",
                    "model": model_id,
                    "retry_after": 10
                }), 429, {"Retry-After": "10"}
        
        try:
            # Mac optimization: bypass LLM for Speaker N: format
            if looks_vibevoice(text):
                processed_text = text
                used_llm = False
            else:
                processed_text = f"Speaker 0: {text.strip()}"
                used_llm = False  # Mac always bypasses LLM
            
            # Generate temporary output path
            temp_id = str(uuid.uuid4())
            temp_path = f"temp/synth_{temp_id}.wav"
            os.makedirs("temp", exist_ok=True)
            
            # Synthesize with validation
            result = synthesize_with_validation(
                model_id=model_id,
                text=processed_text,
                voice_path="VibeVoice/demo/voices/en-Carter_man.wav",  # Default voice
                seconds=seconds,
                output_path=temp_path,
                request_id=request_id
            )
            
            if result["success"]:
                metrics = result["metrics"]
                metrics.update({
                    "request_id": request_id,
                    "used_llm": used_llm,
                    "text_length": len(text),
                    "processed_text_length": len(processed_text)
                })
                
                # Log metrics
                log_request_metrics(metrics)
                
                # Read audio file for response
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up temp file
                os.remove(temp_path)
                
                return Response(
                    audio_data,
                    mimetype='audio/wav',
                    headers={
                        'X-Request-ID': request_id,
                        'X-Model': model_id,
                        'X-Transport': metrics['transport'],
                        'X-Device': metrics['device'],
                        'X-Duration': str(metrics['duration']),
                        'X-RTF': str(metrics['rtf']),
                        'X-Control-Hash': metrics['control_hash']
                    }
                )
            else:
                # Log failure
                log_request_metrics({
                    "request_id": request_id,
                    "model_id": model_id,
                    "success": False,
                    "error": result["error"]
                })
                
                return jsonify({
                    "error": result["error"],
                    "request_id": request_id
                }), 500
                
        finally:
            # Always release semaphore
            if model_id == "1.5B":
                _1P5B_SEM.release()
                
    except Exception as e:
        print(f"Synthesis error: {e}")
        import traceback
        traceback.print_exc()
        
        # Log exception
        log_request_metrics({
            "request_id": request_id if 'request_id' in locals() else 'unknown',
            "success": False,
            "error": str(e),
            "exception": True
        })
        
        return jsonify({"error": str(e)}), 500

@app.route('/metrics')
def metrics():
    """Performance metrics endpoint."""
    with _METRICS_LOCK:
        recent = _REQUEST_METRICS[-50:] if _REQUEST_METRICS else []
    
    if not recent:
        return jsonify({"message": "No metrics available"})
    
    # Calculate statistics
    successful = [m for m in recent if m.get('success', False)]
    failed = [m for m in recent if not m.get('success', True)]
    
    stats = {
        "total_requests": len(recent),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": len(successful) / len(recent) if recent else 0
    }
    
    if successful:
        rtfs = [m['rtf'] for m in successful if 'rtf' in m]
        durations = [m['duration'] for m in successful if 'duration' in m]
        first_chunks = [m['first_chunk_ms'] for m in successful if 'first_chunk_ms' in m and m['first_chunk_ms']]
        
        if rtfs:
            stats["rtf"] = {
                "p50": sorted(rtfs)[len(rtfs)//2],
                "p95": sorted(rtfs)[int(len(rtfs)*0.95)] if len(rtfs) >= 5 else max(rtfs),
                "avg": sum(rtfs) / len(rtfs)
            }
            
        if first_chunks:
            stats["first_chunk_ms"] = {
                "p50": sorted(first_chunks)[len(first_chunks)//2],
                "p95": sorted(first_chunks)[int(len(first_chunks)*0.95)] if len(first_chunks) >= 5 else max(first_chunks)
            }
    
    return jsonify(stats)

@app.route('/warmup', methods=['POST'])
def warmup():
    """Warmup endpoint to populate caches."""
    try:
        # Quick warmup synthesis
        result = synthesize_with_validation(
            model_id="1.5B",
            text="Warmup test",
            voice_path="VibeVoice/demo/voices/en-Carter_man.wav",
            seconds=1.0,
            output_path="temp/warmup.wav",
            request_id="warmup"
        )
        
        if result["success"]:
            # Clean up warmup file
            try:
                os.remove("temp/warmup.wav")
            except:
                pass
                
            return jsonify({
                "status": "warmed_up",
                "load_time": result["metrics"]["wall_time"]
            })
        else:
            return jsonify({
                "error": "Warmup failed",
                "details": result["error"]
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🎯 Mac VibeVoice Hardened Production Server")
    print("Device policy: 1.5B CPU streaming, 7B MPS offline")
    print("Features: Backpressure, validation, metrics, atomic writes")
    print("")
    
    # Validate models on startup
    if not validate_model_availability("1.5B"):
        print("❌ 1.5B model not available")
        print("💡 Run: ./scripts/sync_hf_cache_from_toddllm.sh")
        exit(1)
    
    port = int(os.getenv("PORT", "5001"))
    host = os.getenv("HOST", "127.0.0.1")  # Localhost only for security
    
    print(f"🚀 Starting on {host}:{port}")
    print(f"🏥 Health: http://localhost:{port}/health")
    print(f"📊 Metrics: http://localhost:{port}/metrics")
    print(f"🎙️  Synthesis: POST http://localhost:{port}/synthesize")
    print(f"🔥 Warmup: POST http://localhost:{port}/warmup")
    
    app.run(host=host, port=port, debug=False, threaded=True)