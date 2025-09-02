#!/usr/bin/env bash
# Golden Audio Sentinel
# Catches regressions by comparing against canonical reference audio.

set -euo pipefail

echo "🥇 Golden Path Audio Check"

# Generate golden reference audio with deterministic seed
OUT=$(mktemp -t vv_golden_XXXX).wav
./vvctl_final synth --model 1.5B --seed 1234 --voice VibeVoice/demo/voices/en-Carter_man.wav \
  --text "Speaker 0: Golden path check." --seconds 3 --out "$OUT" --no-save >/dev/null 2>&1

if [[ ! -f "$OUT" ]]; then
    echo "❌ Golden synthesis failed"
    exit 1
fi

# Compute normalized audio hash
python3 - "$OUT" <<'PY'
import sys, os, numpy as np, soundfile as sf, hashlib

audio_path = sys.argv[1]
audio, sr = sf.read(audio_path, dtype='float32')

# Normalize for consistent hashing
peak = np.max(np.abs(audio))
if peak > 0:
    audio = audio / peak

# Compute hash of normalized audio (rounded for stability)
audio_rounded = np.round(audio, 6)
hash_input = audio_rounded.tobytes()
current_hash = hashlib.sha256(hash_input).hexdigest()[:16]

print(f"Current hash: {current_hash}")

# Check against expected
golden_hash_file = "golden/hash.sha"
if os.path.exists(golden_hash_file):
    with open(golden_hash_file, 'r') as f:
        expected_hash = f.read().strip()
    
    print(f"Expected hash: {expected_hash}")
    
    if current_hash == expected_hash:
        print("✅ Golden path audio matches reference")
        sys.exit(0)
    else:
        print("❌ GOLDEN MISMATCH - audio regression detected!")
        print(f"   Expected: {expected_hash}")
        print(f"   Actual:   {current_hash}")
        print("💡 This indicates a potential regression in the audio pipeline")
        sys.exit(1)
else:
    # First run - save the hash as golden reference
    os.makedirs("golden", exist_ok=True)
    with open(golden_hash_file, 'w') as f:
        f.write(current_hash)
    print(f"📌 Golden reference created: {current_hash}")
    print("✅ Future runs will validate against this reference")
    sys.exit(0)
PY

# Clean up temp file
rm -f "$OUT"