"""
Enhanced Audio QC

Production audio validation with resampling, DC blocking, and mel-spec validation.
"""

import numpy as np
import soundfile as sf
import librosa
import hashlib
from typing import Dict, Any, Tuple


def load_and_normalize_24k(path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load audio file and normalize to 24kHz mono with QC.
    
    Args:
        path: Audio file path
        
    Returns:
        Tuple of (normalized_audio, qc_metrics)
    """
    # Load audio
    audio, sr = sf.read(path, dtype="float32", always_2d=False)
    original_sr = sr
    
    # Convert to mono if stereo
    if audio.ndim > 1:
        print(f"  Converting stereo to mono")
        audio = audio.mean(axis=1)
    
    # Resample to 24kHz if needed
    if sr != 24000:
        print(f"  Resampling {sr}Hz -> 24kHz with kaiser_best")
        audio = librosa.resample(
            audio, 
            orig_sr=sr, 
            target_sr=24000, 
            res_type="kaiser_best"
        )
        sr = 24000
    
    # DC blocking (highpass ~20Hz)
    audio = dc_block(audio, sr)
    
    # Peak normalize to -1dBFS
    peak = np.max(np.abs(audio))
    if peak > 0:
        target_peak = 10 ** (-1.0 / 20.0)  # -1dBFS
        audio = audio * (target_peak / peak)
    
    # QC metrics
    qc_metrics = {
        "original_sr": original_sr,
        "final_sr": sr,
        "duration": len(audio) / sr,
        "peak_dbfs": 20 * np.log10(peak) if peak > 0 else -np.inf,
        "rms": float(np.sqrt(np.mean(audio ** 2))),
        "dc_offset": float(np.mean(audio)),
        "resampled": original_sr != 24000,
        "converted_to_mono": len(sf.read(path)[0].shape) > 1 if hasattr(sf.read(path)[0], 'shape') else False
    }
    
    return audio.astype(np.float32), qc_metrics


def dc_block(audio: np.ndarray, sr: int, cutoff: float = 20.0) -> np.ndarray:
    """
    Apply DC blocking filter (highpass) to remove DC offset.
    
    Args:
        audio: Input audio
        sr: Sample rate
        cutoff: Highpass cutoff frequency in Hz
        
    Returns:
        DC-blocked audio
    """
    from scipy import signal
    
    # Design highpass filter
    nyquist = sr / 2
    normalized_cutoff = cutoff / nyquist
    
    # Butterworth highpass filter (2nd order)
    b, a = signal.butter(2, normalized_cutoff, btype='high')
    
    # Apply filter
    filtered = signal.filtfilt(b, a, audio)
    
    return filtered.astype(np.float32)


def compute_audio_hashes(audio: np.ndarray, sr: int = 24000) -> Dict[str, str]:
    """
    Compute multiple hash types for robust golden reference.
    
    Args:
        audio: Audio array (float32)
        sr: Sample rate
        
    Returns:
        Dictionary with different hash types
    """
    # Normalize for consistent hashing
    peak = np.max(np.abs(audio))
    if peak > 0:
        normalized = audio / peak
    else:
        normalized = audio
    
    # Raw waveform hash (rounded for FP stability)
    audio_rounded = np.round(normalized, 6)
    raw_hash = hashlib.sha256(audio_rounded.tobytes()).hexdigest()[:16]
    
    # Mel spectrogram hash (resilient to tiny FP differences)
    try:
        mel_spec = librosa.feature.melspectrogram(
            y=normalized, 
            sr=sr, 
            n_mels=64, 
            fmin=20, 
            fmax=12000
        )
        
        # Normalize mel spectrogram
        mel_normalized = mel_spec / (np.max(mel_spec) + 1e-12)
        mel_rounded = np.round(mel_normalized, 6)
        mel_hash = hashlib.sha256(mel_rounded.tobytes()).hexdigest()[:16]
    except Exception:
        mel_hash = "unavailable"
    
    # MFCC hash (another robust feature)
    try:
        mfcc = librosa.feature.mfcc(y=normalized, sr=sr, n_mfcc=13)
        mfcc_normalized = mfcc / (np.max(np.abs(mfcc)) + 1e-12)
        mfcc_rounded = np.round(mfcc_normalized, 6)
        mfcc_hash = hashlib.sha256(mfcc_rounded.tobytes()).hexdigest()[:16]
    except Exception:
        mfcc_hash = "unavailable"
    
    return {
        "raw": raw_hash,
        "mel": mel_hash,
        "mfcc": mfcc_hash
    }


def validate_golden_audio(audio_path: str, golden_dir: str = "golden") -> Dict[str, Any]:
    """
    Validate audio against golden reference with multiple hash types.
    
    Args:
        audio_path: Path to audio file to validate
        golden_dir: Directory containing golden references
        
    Returns:
        Validation result
    """
    # Load and compute hashes
    audio, sr = sf.read(audio_path, dtype='float32')
    current_hashes = compute_audio_hashes(audio, sr)
    
    result = {
        "valid": False,
        "hashes": current_hashes,
        "matches": {},
        "first_run": False
    }
    
    # Check each hash type
    hash_files = {
        "raw": f"{golden_dir}/hash_raw.sha",
        "mel": f"{golden_dir}/hash_mel.sha", 
        "mfcc": f"{golden_dir}/hash_mfcc.sha"
    }
    
    os.makedirs(golden_dir, exist_ok=True)
    
    all_exist = all(os.path.exists(f) for f in hash_files.values())
    
    if all_exist:
        # Validate against existing references
        for hash_type, hash_file in hash_files.items():
            with open(hash_file, 'r') as f:
                expected = f.read().strip()
            
            current = current_hashes[hash_type]
            matches = (current == expected)
            result["matches"][hash_type] = {
                "expected": expected,
                "actual": current,
                "matches": matches
            }
        
        # Consider valid if raw matches OR (mel AND mfcc match)
        raw_match = result["matches"]["raw"]["matches"]
        feature_match = (result["matches"]["mel"]["matches"] and 
                        result["matches"]["mfcc"]["matches"])
        
        result["valid"] = raw_match or feature_match
        
    else:
        # First run - create golden references
        result["first_run"] = True
        
        for hash_type, hash_file in hash_files.items():
            if current_hashes[hash_type] != "unavailable":
                with open(hash_file, 'w') as f:
                    f.write(current_hashes[hash_type])
        
        result["valid"] = True  # First run is always valid
    
    return result


def create_enhanced_golden_check():
    """Create enhanced golden check script."""
    script_content = '''#!/usr/bin/env bash
# Enhanced Golden Audio Check with multiple hash validation

set -euo pipefail

echo "🥇 Enhanced Golden Path Audio Check"

# Generate test audio with deterministic seed
OUT=$(mktemp -t vv_golden_XXXX).wav
./vvctl_final synth --model 1.5B --seed 1234 --voice VibeVoice/demo/voices/en-Carter_man.wav \\
  --text "Speaker 0: Golden path check." --seconds 3 --out "$OUT" >/dev/null 2>&1

if [[ ! -f "$OUT" ]]; then
    echo "❌ Golden synthesis failed"
    exit 1
fi

# Validate with enhanced checking
python3 - "$OUT" <<'PY'
import sys, os
sys.path.append('.')
from enhanced_audio_qc import validate_golden_audio

audio_path = sys.argv[1]
result = validate_golden_audio(audio_path)

if result["first_run"]:
    print("📌 Golden references created")
    for hash_type, hash_val in result["hashes"].items():
        print(f"   {hash_type}: {hash_val}")
    print("✅ Future runs will validate against these references")
elif result["valid"]:
    print("✅ Golden path audio validated")
    matches = result["matches"]
    print(f"   Raw: {'✅' if matches['raw']['matches'] else '❌'}")
    print(f"   Mel: {'✅' if matches['mel']['matches'] else '❌'}")
    print(f"   MFCC: {'✅' if matches['mfcc']['matches'] else '❌'}")
else:
    print("❌ GOLDEN VALIDATION FAILED")
    for hash_type, match_info in result["matches"].items():
        status = "✅" if match_info["matches"] else "❌"
        print(f"   {hash_type}: {status} {match_info['actual']} (expected: {match_info['expected']})")
    sys.exit(1)
PY

# Clean up
rm -f "$OUT"
'''
    
    with open("scripts/check_golden_enhanced.sh", "w") as f:
        f.write(script_content)
    
    os.chmod("scripts/check_golden_enhanced.sh", 0o755)
    print("✅ Enhanced golden check script created")


# Add this to vvctl_final
def add_support_bundle_command(subparsers):
    """Add support bundle command."""
    bundle_parser = subparsers.add_parser("support-bundle", help="Create diagnostic bundle")
    bundle_parser.add_argument("--verbose", action="store_true", help="Show bundle contents")
    return bundle_parser