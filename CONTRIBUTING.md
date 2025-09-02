# Contributing to VibeVoice Mac Appliance

Thank you for your interest in contributing! This project aims to provide a rock-solid, boring, reliable TTS appliance for Mac users.

## 🎯 Development Philosophy

- **Boring is beautiful** - Predictable, stable, maintainable
- **Apple Silicon first** - Optimized for M1/M2/M3 performance
- **Offline by design** - No external dependencies after setup
- **Enterprise quality** - Production hardening and validation

## 🚀 Quick Start

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3+)
- Python 3.9+ with native ARM support
- Git with submodule support

### Setup
```bash
# Clone with submodules
git clone --recursive https://github.com/toddllm/vibevoice-mac-appliance.git
cd vibevoice-mac-appliance

# Bootstrap development environment
./scripts/bootstrap.sh

# Activate virtual environment
source .venv/bin/activate

# Install in development mode
pip install -e .[dev]
```

### Development Workflow
```bash
# Essential validation loop
make warmup     # Prime caches
make health     # System check
make accept     # Full validation

# Run tests
make test       # Complete test suite
make bench      # Performance benchmarks
make lint       # Code quality checks
```

## 🛡️ Quality Standards

### **Code Quality**
- **Black** formatting (100 char line length)
- **Ruff** linting with strict rules
- **MyPy** type checking required
- **Comprehensive docstrings** for public APIs

### **Testing Requirements**
- All new features must have tests
- `make accept` must pass before PR submission
- Performance regression tests for audio generation
- Golden path validation for synthesis pipeline

### **Audio Quality**
- 24kHz mono output only
- -1dBFS peak normalization
- No NaN/Inf values allowed
- Deterministic generation with fixed seeds

## 📋 Contribution Process

### 1. **Issue First**
- Open an issue describing the problem or enhancement
- Discuss approach before starting implementation
- Reference issue in your PR

### 2. **Branch Strategy**
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Work on your changes
# ...

# Ensure tests pass
make test

# Check code quality
make lint
```

### 3. **Pull Request**
- Clear title and description
- Reference related issues
- Include test results: `make accept` output
- Add documentation updates if needed

### 4. **Review Process**
- Automated checks must pass
- Code review from maintainers
- Performance validation on Apple Silicon
- Documentation review

## 🎯 Areas for Contribution

### **High Priority**
- 7B model MPS optimization
- Voice cloning and management tools
- Performance optimization for Apple Silicon
- Documentation improvements

### **Medium Priority**
- Web UI for synthesis
- Batch processing capabilities
- Advanced audio post-processing
- Integration examples

### **Low Priority**
- Additional model support
- Cross-platform compatibility
- Advanced streaming features

## 🧪 Testing Guidelines

### **Unit Tests**
```bash
# Run unit tests
pytest tests/unit/

# With coverage
pytest --cov=cli --cov=server --cov=synth tests/
```

### **Integration Tests**
```bash
# Audio pipeline tests
pytest tests/integration/

# Full synthesis tests
make bench
```

### **Acceptance Tests**
```bash
# Golden path validation
make accept

# Performance baseline
make bench
```

## 📊 Performance Standards

### **Benchmarks (M3 Pro + 128GB)**
- **Load time**: <8s first run, <2s cached
- **1.5B RTF**: 0.13-0.16x on CPU
- **First chunk**: <2000ms
- **Success rate**: >99%

### **Quality Gates**
- Audio output must pass QC validation
- Golden reference hashes must match
- No memory leaks in long-running tests
- Service startup must complete <30s

## 🔧 Architecture Guidelines

### **Device Policy**
- **1.5B**: CPU/FP32 streaming (stability over speed)
- **7B**: MPS/FP16 offline (speed where stable)
- **Graceful fallback**: Always degrade to CPU if needed

### **Code Organization**
- **cli/**: Command-line interface and user tools
- **server/**: Flask API server and production deployment
- **synth/**: Core synthesis engine and validation
- **configs/**: Configuration management and validation

### **Dependencies**
- Pin critical versions (transformers==4.51.3)
- Minimal dependency surface
- Apple Silicon native packages preferred

## 🐛 Bug Reports

### **Required Information**
```bash
# Include this diagnostic output
./cli/vvctl diag --json

# And acceptance test results
make accept

# Plus support bundle if needed
./cli/vvctl support-bundle
```

### **Issue Template**
Use the [Incident Template](docs/INCIDENT_TEMPLATE.md) for structured reporting.

## 📖 Documentation

### **Required Documentation**
- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update Day-2 runbook for operational changes
- Include performance impact notes

### **Documentation Standards**
- Clear, concise writing
- Code examples that work out of the box
- Troubleshooting steps for common issues
- Performance implications clearly stated

## 🤝 Community

### **Code of Conduct**
- Be respectful and professional
- Focus on technical merit
- Help newcomers learn and contribute
- Maintain the "boring reliability" culture

### **Getting Help**
- Check existing issues and documentation first
- Provide complete diagnostic information
- Be specific about your environment and use case
- Include reproduction steps

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make Mac TTS boring and reliable!** 🎧✨