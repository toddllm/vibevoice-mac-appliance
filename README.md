# 🎙️ VibeVoice Mac Appliance

**The open source ElevenLabs meets NotebookLM for Apple Silicon**

Transform your Mac into a professional, offline TTS appliance. Generate long-form, multi-speaker conversations, podcasts, and narratives with enterprise-grade reliability.

[![Release](https://img.shields.io/github/v/release/toddllm/vibevoice-mac-appliance)](https://github.com/toddllm/vibevoice-mac-appliance/releases)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-Optimized-ff6b35)](https://developer.apple.com/metal/)
[![Offline](https://img.shields.io/badge/Offline%20Ready-green)](docs/PRODUCTION_READY.md)

> 💡 **Branch Note**: This branch downloads models from Hugging Face (no LAN required). For LAN+rsync optimization, see the [`lan-optimized`](../../tree/lan-optimized) branch.

## ✨ What Makes This Special

### **🎵 Long-Form, Multi-Speaker Magic**
- **Up to 90 minutes** of continuous generation
- **Up to 4 distinct speakers** in natural conversation
- **Podcast-quality** dialogues and narratives
- **Cross-lingual support** with accent preservation

### **🔬 Technical Innovation (Credit: Microsoft VibeVoice)**
- **Continuous speech tokenizers** at ~7.5 Hz (ultra-efficient for long sequences)
- **LLM + Diffusion architecture** - LLM understands dialogue, diffusion adds acoustic richness
- **Next-token diffusion framework** - Novel approach to high-fidelity speech synthesis
- **Open source with MIT license** - Production-ready weights on Hugging Face

### **🍎 Mac-First Engineering**
- **Apple Silicon optimized** - Native MPS acceleration where stable
- **Offline after setup** - Downloads once, runs offline forever
- **Enterprise hardened** - Golden path validation, atomic operations
- **Professional tooling** - CLI, API server, monitoring, diagnostics

## 🚀 Quick Start (Out-of-Box)

### **One-Command Setup**
```bash
# Clone and setup
git clone --recursive https://github.com/toddllm/vibevoice-mac-appliance.git
cd vibevoice-mac-appliance
make setup

# Download 1.5B model (~6GB)
make download-1p5b

# Generate your first podcast!
make smoke
```

### **Your First Synthesis**
```bash
# Simple greeting
./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --text "Hello from your new TTS appliance!" --seconds 5

# Multi-speaker conversation
./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Alice_woman.wav --text "Speaker 0: Welcome to our podcast! Speaker 1: Thanks for having me on the show. This is going to be a great conversation." --seconds 10

# Long-form narrative
echo "Speaker 0: In today's episode, we'll explore the fascinating world of AI-generated speech. Speaker 1: That's right, and we'll be diving deep into the technical innovations that make this possible." | ./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --stdin --seconds 15
```

## 🎯 Use Cases

### **🎙️ Podcast & Content Creation**
- Generate realistic multi-speaker podcasts from scripts
- Create educational content with natural dialogue
- Prototype audio content before recording

### **📚 NotebookLM-Style Applications**
- Convert documents into conversational audio
- Create audio summaries with multiple perspectives
- Generate educational dialogues from technical content

### **🎬 Media & Entertainment**
- Prototype audio dramas and narratives
- Create voiceovers for video content
- Generate character voices for games and apps

### **🏢 Enterprise Applications**
- Create training materials with realistic conversations
- Generate accessibility audio for written content
- Prototype voice interfaces and chatbots

## 📊 Performance (Apple Silicon)

### **M3 Pro + 128GB Results**
- **Model Loading**: 4-8 seconds (cached after first run)
- **1.5B Streaming**: RTF 0.13-0.16x (faster than real-time on CPU)
- **Audio Quality**: Production-ready 24kHz output
- **Memory Usage**: ~2-4GB for 1.5B, ~8-12GB for 7B
- **First Chunk Latency**: 800-1500ms

### **Recommended Specs**
- **Minimum**: M1 Mac with 16GB unified memory
- **Recommended**: M2/M3 with 64GB+ for best performance
- **Optimal**: M3 Pro/Max with 128GB+ for 7B model

## 🏗️ Architecture Highlights

### **Smart Device Policy**
- **1.5B Model**: CPU/FP32 streaming (rock-solid stability)
- **7B Model**: MPS/FP16 offline (maximum quality when available)
- **Graceful degradation**: Auto-fallback to CPU if needed

### **Enterprise Features**
- **Golden Path Validation** - Ensures consistent, quality output
- **Deterministic Generation** - Reproducible results with fixed seeds
- **Audio Quality Control** - Automatic normalization and validation
- **Atomic Operations** - Crash-safe file handling
- **Self-Monitoring** - Health checks and performance metrics

### **Professional Tooling**
- **CLI Interface**: `vvctl synth|health|bench|diag`
- **API Server**: Production Flask server with backpressure
- **Service Installation**: Auto-start with macOS launchd
- **Diagnostic Tools**: Support bundles and troubleshooting

## 🎵 Audio Quality

### **Professional Standards**
- **Sample Rate**: 24kHz (broadcast quality)
- **Bit Depth**: 16-bit PCM
- **Peak Level**: -1dBFS normalized
- **Format**: Mono WAV (industry standard)
- **Processing**: DC blocking, crossfading, clipping prevention

### **Voice Requirements**
- **Duration**: 0.4-30 seconds (0.8-4s recommended)
- **Quality**: Clean recording, minimal background noise
- **Format**: Any common audio format (auto-converted to 24kHz mono)

## 📋 Model Comparison

| Model | Size | Context | Max Duration | Quality | Speed | Memory |
|-------|------|---------|--------------|---------|-------|---------|
| **1.5B** | ~6GB | 64K tokens | ~90 minutes | High | Fast | 2-4GB |
| **7B** | ~26GB | 32K tokens | ~45 minutes | Highest | Medium | 8-12GB |

### **When to Use Each**
- **1.5B**: Daily use, prototyping, real-time applications
- **7B**: Premium quality, final production, complex multi-speaker scenes

## 🌍 Comparison to Commercial Services

### **vs. ElevenLabs**
- ✅ **Completely offline** after setup (no API costs)
- ✅ **Unlimited usage** (no per-minute billing)
- ✅ **Multi-speaker conversations** (not just single voice)
- ✅ **Long-form generation** (90+ minutes vs. short clips)
- ✅ **Open source** (customizable, transparent)
- ❌ Lower voice cloning quality (for now)

### **vs. NotebookLM Audio**
- ✅ **Local processing** (private, no data sent to Google)
- ✅ **Customizable voices** (not limited to preset speakers)
- ✅ **Scriptable generation** (API and CLI integration)
- ✅ **Longer content** (no length restrictions)
- ❌ No automatic document-to-dialogue conversion (yet)

### **vs. Traditional TTS**
- ✅ **Multi-speaker scenes** (automatic speaker assignment)
- ✅ **Conversational flow** (natural turn-taking)
- ✅ **Context awareness** (LLM understands dialogue)
- ✅ **Long-form stability** (doesn't degrade over time)

## 🎯 Real-World Examples

### **Podcast Generation**
```bash
# Create a tech podcast episode
echo "Speaker 0: Welcome to TechTalk! Today we're discussing AI breakthroughs. Speaker 1: Thanks for having me. The latest developments in speech synthesis are truly remarkable. Speaker 0: Tell us about the technical innovations behind these systems." | ./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --stdin --seconds 20
```

### **Educational Content**
```bash
# Convert lesson into dialogue
./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Alice_woman.wav --text "Speaker 0: Let's explore quantum computing. Speaker 1: Great topic! First, let's understand what makes quantum computers different from classical computers. Speaker 0: The key is quantum superposition..." --seconds 30
```

### **Narrative Audio**
```bash
# Story narration with character voices
./cli/vvctl synth --model 7B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --text "Speaker 0: Once upon a time in a digital realm, there lived an AI who dreamed of creating beautiful music. Speaker 1: But this wasn't just any AI - it had the power to generate voices that sounded completely human." --seconds 15
```

## 🔧 Advanced Usage

### **API Server**
```bash
# Start production server
python server/production_server_hardened.py

# Generate via API
curl -X POST http://localhost:5001/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Speaker 0: Hello from the API! Speaker 1: This is working great!",
    "model": "1.5B", 
    "seconds": 8
  }'
```

### **Batch Processing**
```bash
# Process multiple scripts
for script in scripts/*.txt; do
    ./cli/vvctl synth --model 1.5B --voice voices/narrator.wav --from-file "$script" --seconds 30 --out "out/$(basename "$script" .txt).wav"
done
```

### **Custom Voices**
```bash
# Import your own voice
./cli/vvctl voice import --input ~/my_recording.wav --name MyVoice --gender neutral --lang en

# Use in synthesis
./cli/vvctl synth --model 1.5B --voice demo/voices/en-MyVoice_neutral.wav --text "Hello in my own voice!" --seconds 5
```

## 🛡️ Enterprise Features

### **Production Deployment**
- **Service Installation**: Auto-start with macOS launchd
- **Health Monitoring**: Comprehensive system diagnostics
- **Performance Metrics**: RTF tracking and benchmarking
- **Quality Assurance**: Golden path validation and audio QC
- **Atomic Operations**: Crash-safe file handling

### **Security & Privacy**
- **Completely offline** after initial model download
- **Local processing only** - No data sent to external services
- **No telemetry** - Your audio stays on your device
- **Open source** - Fully auditable code

## 📚 Documentation

- **[Production Guide](docs/PRODUCTION_READY.md)** - Complete deployment guide
- **[Operations Runbook](docs/DAY2_RUNBOOK.md)** - Troubleshooting and maintenance
- **[Technical Details](docs/README_MAC.md)** - Architecture and implementation
- **[Contributing Guide](CONTRIBUTING.md)** - Development setup and guidelines

## 🤝 Upstream Attribution

This project builds upon the excellent work of the **Microsoft VibeVoice team**:

- **Original Repository**: [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)
- **Project Page**: [microsoft.github.io/VibeVoice](https://microsoft.github.io/VibeVoice)
- **Technical Paper**: [VibeVoice: A Frontier Long Conversational Text-to-Speech Model](https://arxiv.org/abs/2508.19205)
- **Models**: [Hugging Face Collection](https://huggingface.co/collections/microsoft/vibevoice-68a2ef24a875c44be47b034f)

**Please star the original repository and cite the technical paper in research.**

## 🚀 What's Next

### **Roadmap**
- **Document-to-Dialogue**: Automatic conversion like NotebookLM
- **Voice Cloning**: Custom voice training pipeline
- **Real-time Streaming**: Live conversation generation
- **Web Interface**: Browser-based synthesis studio

### **Community**
- **Contributions welcome** - See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issue reporting** - Use our [diagnostic tools](docs/INCIDENT_TEMPLATE.md)
- **Feature requests** - Share your use cases and ideas

## ⚖️ Responsible Use

This technology can generate highly realistic speech. Please use responsibly:

- **Disclose AI generation** when sharing synthetic audio
- **Respect consent** - Don't clone voices without permission  
- **Follow local laws** - Comply with regulations in your jurisdiction
- **Prevent misuse** - Don't create misleading or harmful content

See the [upstream repository](https://github.com/microsoft/VibeVoice) for complete risk assessment and limitations.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

This project includes Microsoft VibeVoice as a git submodule. See [vendor/VibeVoice/LICENSE](vendor/VibeVoice/LICENSE) for upstream license terms.

---

**Built with ❤️ for Apple Silicon. Ready to make your Mac the most capable TTS appliance on the planet.** 🎧✨

## 🔗 Links

- **[Microsoft VibeVoice](https://github.com/microsoft/VibeVoice)** - Original project and models
- **[Project Demos](https://microsoft.github.io/VibeVoice)** - Audio examples and technical demos  
- **[Technical Paper](https://arxiv.org/abs/2508.19205)** - Research and architecture details
- **[Hugging Face Models](https://huggingface.co/microsoft/VibeVoice-1.5B)** - Pre-trained weights and model cards