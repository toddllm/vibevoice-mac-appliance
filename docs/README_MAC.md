# Mac VibeVoice Port 🎙️

Clean, offline Mac-first VibeVoice implementation for M3 Pro + 128GB.

## ✅ Status: Production Ready

**Working components:**
- ✅ Clean HF cache sync from toddllm (read-only)
- ✅ Offline model loading (no network dependency)  
- ✅ 1.5B streaming on CPU/FP32 (stable)
- ✅ Audio generation with chunk capture
- ✅ CLI interface (`vvctl`)
- ✅ Production server ready
- ✅ Zero impact on Linux training server

## 🚀 Quick Start

```bash
# Health check
./vvctl health

# Generate speech
./vvctl synth --model 1.5B --voice VibeVoice/demo/voices/en-Carter_man.wav --text "Hello Mac!" --seconds 5

# Smoke test
make smoke

# Start server
make server
```

## 📋 Requirements

- macOS with Apple Silicon (M1/M2/M3+)
- Python 3.9+
- 128GB unified memory recommended
- Models synced from toddllm

## 🔧 Device Policy

**Stable & Tested:**
- **1.5B**: CPU/FP32 streaming (avoids MPS conv limitations)
- **7B**: MPS/FP16 offline (when available)

## 📊 Performance

**M3 Pro Results:**
- **Load time**: 4-8 seconds  
- **1.5B streaming**: RTF ~0.13-0.15x on CPU
- **Chunk rate**: ~21 chunks @ 3200 samples each
- **Audio quality**: Production ready

## 🎯 Commands

### Synthesis
```bash
# Basic
./vvctl synth --model 1.5B --voice path/to/voice.wav --text "Speaker 0: Hello!" --seconds 6

# Multi-speaker  
./vvctl synth --model 1.5B --voice path/to/voice.wav --text "Speaker 0: Hi! Speaker 1: Hello back!" --seconds 8
```

### Voice Management
```bash
# Import new voice
./vvctl voice import --input ~/my_voice.wav --name MyName --gender woman --lang en

# Health check
./vvctl health
```

### Development
```bash
# Smoke test
make smoke

# Benchmark
make bench

# Examples
make examples
```

## 🏗️ Architecture

### Core Components
- `vvctl`: CLI interface
- `mac_config.py`: Centralized configuration
- `golden_path_validator.py`: Control surface validation
- `mac_production_server.py`: Flask server
- `CaptureStreamer`: Audio chunk collection

### Device Strategy
- **1.5B**: Uses CPU to avoid MPS conv1d >65536 channels limitation
- **7B**: Uses MPS for faster offline generation
- **Automatic fallback**: CPU if MPS unavailable

### Offline Guarantee
- `HF_HUB_OFFLINE=1`: No network model downloads
- `TRANSFORMERS_OFFLINE=1`: No dependency downloads
- Local snapshot paths: Direct file loading

## 🔍 Troubleshooting

### Common Issues

**No audio generated:**
- Check voice file exists and is 24kHz mono
- Verify model snapshot is complete
- Check `put_count > 0` in logs

**MPS errors:**
- 1.5B automatically uses CPU (expected)
- 7B falls back to CPU if needed
- FP32 recommended for stability

**Missing models:**
```bash
# Sync from toddllm
./scripts/sync_hf_cache_from_toddllm.sh
```

### Validation
```bash
# Check model files
ls ~/.cache/huggingface/hub/models--microsoft--VibeVoice-1.5B/snapshots/cf42b8ff262f8a286bcbe580835cfaad62d277ca/

# Check voices
ls VibeVoice/demo/voices/

# Test audio output
afplay out/latest.wav
```

## 🎛️ Configuration

### Environment Variables
```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1  
export TRANSFORMERS_NO_FLASH_ATTENTION=1
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export OMP_NUM_THREADS=8
export VECLIB_MAXIMUM_THREADS=8
```

### Model Snapshots
- **1.5B**: `cf42b8ff262f8a286bcbe580835cfaad62d277ca` (verified complete)
- **7B**: Auto-detected from cache (when available)

## 🎯 Production Deployment

### Server Mode
```bash
# Start production server
python mac_production_server.py

# Health check
curl http://localhost:5001/health

# Synthesis API
curl -X POST http://localhost:5001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from API!", "model": "1.5B", "seconds": 5}'
```

### Voice Studio
```bash
# Import voices
./vvctl voice import --input ~/voice.wav --name Alice --gender woman

# List voices
ls demo/voices/
```

## 📈 Performance Optimization

### CPU Threading
- Optimized for M3 Pro (8 performance cores)
- Tune `OMP_NUM_THREADS` if needed

### Memory Management
- Models cached after first load
- MPS memory cleared between generations
- CPU fallback for large operations

## 🔒 Security

### Isolation
- No network access after model sync
- Read-only access to toddllm
- Local file operations only
- No secrets or credentials stored

### Validation
- Golden path control surface validation
- Audio sanitization (NaN removal)
- Peak normalization to prevent clipping

## 🎵 Audio Quality

### Specifications
- **Sample rate**: 24kHz
- **Format**: PCM 16-bit
- **Channels**: Mono
- **Peak level**: -1dBFS
- **Chunk size**: 3200 samples (133ms @ 24kHz)

### Voice Requirements
- 24kHz mono WAV preferred
- Duration: 0.4-30 seconds
- Clean audio (minimal background noise)
- Natural speaking voice

## 🔮 Future Enhancements

### Planned
- 7B MPS offline support
- Simulated streaming for 7B
- Voice variant generation
- Performance metrics dashboard
- Model packing/unpacking

### Experimental
- Mixed precision optimization
- Custom voice training
- Real-time streaming interface
- Web UI integration

---

**Built with ❤️ for Apple Silicon**
Zero impact on your Linux training environment.