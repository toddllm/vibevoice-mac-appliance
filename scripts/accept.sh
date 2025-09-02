#!/usr/bin/env bash
"""
Acceptance Test Script

Automation-friendly gates that fail the build if anything drifts.
"""

set -euo pipefail

echo "🎯 Mac VibeVoice Acceptance Test"
echo "==============================="

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "❌ jq not found. Install with: brew install jq"
    exit 1
fi

echo "1️⃣  Checking model snapshots and golden surface..."

# Health check with JSON output
if ! ./vvctl health --json >/tmp/health.json 2>/dev/null; then
    echo "❌ Health check failed"
    exit 1
fi

# Validate model availability and completeness
if ! jq -e '.models["1.5B"].present == true and .models["1.5B"].shards >= 3' /tmp/health.json >/dev/null; then
    echo "❌ 1.5B model snapshot incomplete"
    cat /tmp/health.json | jq '.models["1.5B"]'
    exit 1
fi

echo "✅ Model snapshots validated"

echo "2️⃣  Running synthesis acceptance test..."

# Quick synthesis with metrics output
out_file="out/acceptance_$(date +%s).wav"
if ! ./vvctl synth --model 1.5B --voice VibeVoice/demo/voices/en-Carter_man.wav \
  --text "Speaker 0: Acceptance test run." --seconds 3 --out "$out_file" --metrics >/tmp/synth.json 2>/dev/null; then
    echo "❌ Synthesis failed"
    exit 1
fi

# Validate synthesis output
if ! jq -e '.duration >= 2.5 and .chunk_count > 0 and .first_chunk_ms < 2000 and .rtf > 0' /tmp/synth.json >/dev/null; then
    echo "❌ Synthesis metrics failed validation"
    cat /tmp/synth.json | jq '{duration, chunk_count, first_chunk_ms, rtf}'
    exit 1
fi

# Check output file exists and has reasonable size
if [[ ! -f "$out_file" ]]; then
    echo "❌ Output file not created: $out_file"
    exit 1
fi

file_size=$(stat -f%z "$out_file" 2>/dev/null || echo "0")
if [[ "$file_size" -lt 10000 ]]; then  # Less than 10KB is suspicious
    echo "❌ Output file too small: ${file_size} bytes"
    exit 1
fi

echo "✅ Synthesis acceptance passed"

echo "3️⃣  Checking audio quality..."

# Basic audio validation using Python
python3 -c "
import soundfile as sf
import numpy as np

audio, sr = sf.read('$out_file')
duration = len(audio) / sr
peak = np.max(np.abs(audio))
rms = np.sqrt(np.mean(audio**2))

print(f'Audio: {duration:.2f}s, peak={peak:.3f}, rms={rms:.6f}')

# Validate
assert sr == 24000, f'Wrong sample rate: {sr}'
assert duration >= 2.0, f'Too short: {duration}'
assert peak <= 1.0, f'Clipped: {peak}'
assert rms > 1e-5, f'Silent: {rms}'
assert np.isfinite(audio).all(), 'NaN/Inf detected'

print('✅ Audio QC passed')
"

echo "✅ Audio quality validated"

# Clean up temp files
rm -f /tmp/health.json /tmp/synth.json

echo ""
echo "🎉 ACCEPTANCE TEST: PASSED"
echo "✅ Model snapshots complete"
echo "✅ Synthesis pipeline working"  
echo "✅ Audio quality validated"
echo "✅ Performance metrics good"
echo ""
echo "🎯 Mac VibeVoice is production ready!"