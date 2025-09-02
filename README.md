# 🎙️ VibeVoice Mac Appliance

**Enterprise-grade, offline Text-to-Speech appliance for Apple Silicon**

Transform your Mac into a boring, dependable TTS appliance with VibeVoice. Works out-of-the-box with public models, then runs completely offline.

> 💡 **Branch Note**: This branch downloads models from Hugging Face (no LAN required). For LAN+rsync optimization, see the [`lan-optimized`](../../tree/lan-optimized) branch.

## ✨ Features

- 🔒 **Offline After Setup** - Downloads once, runs offline forever
- ⚡ **Apple Silicon Optimized** - Native MPS acceleration for M1/M2/M3
- 🎵 **Production Audio Quality** - 24kHz, -1dBFS normalized output
- 🛡️ **Enterprise Hardened** - Golden path validation, atomic operations
- 📊 **Self-Monitoring** - Comprehensive metrics and health checks
- 🚀 **Out-of-Box Setup** - No external dependencies required

## 🚀 Quick Start (Public)

```bash
# 1. Clone with submodules
git clone --recursive https://github.com/toddllm/vibevoice-mac-appliance.git
cd vibevoice-mac-appliance

# 2. Setup environment
make setup

# 3. Download 1.5B model (~6GB)
make download-1p5b

# 4. Generate speech  
make smoke

# 5. First synthesis
./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --text "Hello Mac!" --seconds 5
```

### Optional: High-Quality 7B Model
```bash
# Download 7B model (~26GB) 
make download-7b

# Test 7B generation
./cli/vvctl synth --model 7B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --text "High quality test" --seconds 6
```

## 📋 Requirements

- **macOS** with Apple Silicon (M1/M2/M3+)
- **Python 3.9+** with native ARM support
- **128GB+ unified memory** recommended for optimal performance
- **Access to pre-trained models** (see setup instructions)

## 🎯 Daily Commands

```bash
# Essential workflow
make health         # System validation
make bench          # Performance check
make accept         # Full acceptance gates

# Generate speech
./cli/vvctl synth --model 1.5B --voice path/to/voice.wav --text "Your text" --seconds 6

# System maintenance
make warmup         # Populate caches
make diag          # Diagnostic output
```

## 🏗️ Architecture

### Device Policy (Optimized for Stability)
- **1.5B Model**: CPU/FP32 streaming (avoids MPS conv limitations)
- **7B Model**: MPS/FP16 offline (when available)
- **Automatic Fallback**: CPU if MPS unavailable

### Quality Assurance
- **Golden Path Validation** - Frozen control surface parameters
- **Audio QC Pipeline** - Normalization, DC blocking, clipping prevention
- **Deterministic Generation** - Reproducible output with fixed seeds
- **Atomic Operations** - Crash-safe file writes

### Performance
- **RTF**: 0.13-0.16x on M3 Pro (1.5B streaming)
- **First Chunk**: 800-1500ms latency
- **Load Time**: 4-8s (cached after warmup)
- **Memory**: Optimized for Apple Silicon unified memory

## 📊 Performance Baselines

**M3 Pro + 128GB Results:**
- Load time: 4-8 seconds
- 1.5B streaming: RTF ~0.13-0.15x on CPU
- Audio quality: Production-ready WAV output
- Chunk delivery: <2s to first chunk
- Success rate: 100% in testing

## 🔧 Installation

### Automated Setup
```bash
./scripts/bootstrap.sh
```

### Manual Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r configs/requirements.txt

# Install VibeVoice
cd vendor/VibeVoice && pip install -e . && cd ../..

# Create directories
mkdir -p out temp logs golden
```

## 📖 Documentation

- **[Production Ready Guide](docs/PRODUCTION_READY.md)** - Complete feature overview
- **[Day-2 Operations](docs/DAY2_RUNBOOK.md)** - Troubleshooting and maintenance
- **[Final Checklist](docs/FINAL_CHECKLIST.md)** - Production validation steps
- **[Incident Template](docs/INCIDENT_TEMPLATE.md)** - Issue reporting format

## 🎵 Audio Pipeline

### Supported Models
- **VibeVoice-1.5B**: Streaming generation, CPU optimized
- **VibeVoice-7B**: Offline generation, MPS accelerated (when synced)

### Voice Requirements
- **Sample Rate**: 24kHz (auto-resampled if different)
- **Channels**: Mono (auto-converted from stereo)
- **Duration**: 0.4-30 seconds
- **Quality**: Clean audio, minimal background noise

### Output Specifications
- **Format**: WAV PCM 16-bit
- **Sample Rate**: 24kHz
- **Peak Level**: -1dBFS normalized
- **Channels**: Mono

## 🛡️ Security & Isolation

- **Offline Operation**: No network access after model sync
- **Local Processing**: All operations on-device
- **No External Dependencies**: Self-contained after setup
- **Safe Defaults**: Conservative resource usage

## 🚀 API Server

### Start Server
```bash
python server/production_server_hardened.py
```

### Health Check
```bash
curl http://localhost:5001/health
```

### Synthesis API
```bash
curl -X POST http://localhost:5001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from API!", "model": "1.5B", "seconds": 5}'
```

## 🔍 Troubleshooting

### Common Issues
- **No audio generated**: Check voice file format and model availability
- **Slow first request**: Run `make warmup` after boot
- **MPS errors**: 1.5B automatically uses CPU (expected behavior)

### Diagnostic Tools
```bash
# System diagnostic
./cli/vvctl diag

# Cache verification
./cli/vvctl verify-cache --all

# Support bundle
./cli/vvctl support-bundle
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run the test suite: `make test`
4. Submit a pull request

### Development Setup
```bash
# Install in development mode
pip install -e .

# Run tests
make test

# Check code quality
make lint
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Microsoft VibeVoice Team** - Original model and implementation
- **Apple MLX Team** - Apple Silicon optimization insights
- Built with ❤️ for the Mac development community

---

**Transform your Mac into a professional TTS appliance.** 🎧✨