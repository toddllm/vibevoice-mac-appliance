# VibeVoice Mac Appliance Makefile
# Clean, reliable commands for daily operations

.PHONY: all health smoke bench accept test warmup install-service diag lint clean

# Default target
all: setup

# Setup environment (public-first)
setup:
	@echo "🐍 Setting up Mac VibeVoice environment..."
	@python3 -m venv .venv
	@. .venv/bin/activate && pip install -U pip wheel setuptools
	@. .venv/bin/activate && pip install -r configs/requirements.txt
	@. .venv/bin/activate && pip install huggingface_hub hf-transfer
	@cd vendor/VibeVoice && ../../.venv/bin/pip install -e .
	@echo "✅ Setup complete"

# Download models
download-1p5b:
	@echo "📦 Downloading VibeVoice-1.5B (~6GB)..."
	@. .venv/bin/activate && HF_HUB_ENABLE_HF_TRANSFER=1 python scripts/fetch_models.py 1.5B

download-7b:
	@echo "📦 Downloading VibeVoice-7B (~26GB)..."
	@. .venv/bin/activate && HF_HUB_ENABLE_HF_TRANSFER=1 python scripts/fetch_models.py 7B

# System health check
health:
	@. .venv/bin/activate && ./cli/vvctl health

# Quick smoke test
smoke: 
	@echo "🔥 Running smoke test..."
	@. .venv/bin/activate && ./cli/vvctl health
	@. .venv/bin/activate && ./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --text "Smoke test" --seconds 3
	@echo "✅ Smoke test complete"

# Performance benchmark
bench:
	@echo "📊 Running performance benchmark..."
	@./cli/vvctl bench --iters 3 --seconds 4 --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav

# Acceptance test (fail-fast validation)
accept:
	@echo "🎯 Running acceptance test..."
	@./scripts/accept.sh
	@echo "🥇 Checking golden audio reference..."
	@./scripts/check_golden.sh

# Combined test suite
test: smoke bench accept
	@echo "✅ All tests passed!"

# Warmup models and caches
warmup:
	@echo "🔥 Warming up models..."
	@./cli/vvctl warmup --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav

# System diagnostic
diag:
	@echo "🔍 System diagnostic..."
	@./cli/vvctl diag

# Install as system service
install-service:
	@echo "🚀 Installing Mac VibeVoice service..."
	@./scripts/install_service.sh

# Code quality checks
lint:
	@echo "🧹 Running code quality checks..."
	@black --check --diff cli/ server/ synth/ configs/
	@ruff check cli/ server/ synth/ configs/
	@mypy cli/ server/ synth/ configs/

# Format code
format:
	@echo "✨ Formatting code..."
	@black cli/ server/ synth/ configs/
	@ruff --fix cli/ server/ synth/ configs/

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -rf out/ temp/ logs/ .pytest_cache/ __pycache__/
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name "*~" -delete
	@echo "✅ Clean complete"

# Development setup
dev-setup:
	@echo "🛠️ Setting up development environment..."
	@python3 -m venv .venv
	@source .venv/bin/activate && pip install -e .[dev]
	@echo "✅ Development environment ready"

# Package for distribution
package:
	@echo "📦 Building package..."
	@python -m build
	@echo "✅ Package built in dist/"

# Show usage examples
examples:
	@echo "🎯 VibeVoice Mac Appliance Examples:"
	@echo ""
	@echo "# Essential workflow:"
	@echo "make health                    # System validation"
	@echo "make warmup                    # Cache population"
	@echo "make accept                    # Full acceptance gates"
	@echo ""
	@echo "# Speech synthesis:"
	@echo "./cli/vvctl synth --model 1.5B --voice vendor/VibeVoice/demo/voices/en-Carter_man.wav --text \"Hello Mac!\" --seconds 5"
	@echo ""
	@echo "# Performance monitoring:"
	@echo "make bench                     # Performance benchmarks"
	@echo "./cli/vvctl diag              # System diagnostic"
	@echo ""
	@echo "# Service management:"
	@echo "make install-service          # Install auto-start service"
	@echo "curl http://localhost:5001/health  # Health check API"
	@echo ""
	@echo "# Issue reporting:"
	@echo "./cli/vvctl support-bundle    # Create diagnostic bundle"

# Help target
help: examples