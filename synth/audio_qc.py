"""
Audio Quality Control

Production audio validation and processing for Mac VibeVoice.
"""

import numpy as np
import soundfile as sf
from typing import Dict, Any, Tuple

def qc_24k_mono(audio_f32: np.ndarray) -> Dict[str, Any]:
    """
    Quality control check for 24kHz mono audio.
    
    Args:
        audio_f32: Audio array (float32)
        
    Returns:
        QC metrics dictionary
    """
    assert audio_f32.ndim == 1 and audio_f32.dtype == np.float32, f"Expected 1D float32, got {audio_f32.shape} {audio_f32.dtype}"
    assert np.isfinite(audio_f32).all(), "NaN/Inf detected in audio"
    
    peak = float(np.max(np.abs(audio_f32)) + 1e-12)
    dbfs = 20 * np.log10(peak)
    rms = float(np.sqrt(np.mean(audio_f32 ** 2)))
    duration = len(audio_f32) / 24000.0
    
    # Check for DC offset
    dc_offset = float(np.mean(audio_f32))
    
    # Check for clipping (values at exact ±1.0)
    clipped_samples = np.sum(np.abs(audio_f32) >= 0.999)
    
    return {
        "samples": len(audio_f32),
        "duration_sec": duration,
        "peak_dbfs": dbfs,
        "rms": rms,
        "dc_offset": dc_offset,
        "clipped_samples": clipped_samples,
        "is_silent": rms < 1e-6,
        "is_clipped": clipped_samples > 0,
        "is_valid": dbfs <= 0.1 and abs(dc_offset) < 0.01 and clipped_samples == 0
    }

def normalize_audio(audio: np.ndarray, target_dbfs: float = -1.0) -> np.ndarray:
    """
    Normalize audio to target dBFS with safety limiting.
    
    Args:
        audio: Input audio (any dtype)
        target_dbfs: Target peak level in dBFS
        
    Returns:
        Normalized float32 audio
    """
    # Convert to float32
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    
    # Remove DC offset
    audio = audio - np.mean(audio)
    
    # Calculate current peak
    peak = np.max(np.abs(audio))
    if peak <= 1e-12:
        return audio  # Silent audio
    
    # Calculate target gain
    target_linear = 10 ** (target_dbfs / 20.0)
    gain = target_linear / peak
    
    # Apply gain with safety limiting
    normalized = audio * gain
    
    # Final safety clamp
    normalized = np.clip(normalized, -1.0, 1.0)
    
    return normalized

def crossfade_chunks(chunks: list, crossfade_samples: int = 8) -> np.ndarray:
    """
    Crossfade audio chunks to prevent clicks.
    
    Args:
        chunks: List of audio chunks
        crossfade_samples: Number of samples to crossfade
        
    Returns:
        Concatenated audio with smooth transitions
    """
    if not chunks:
        return np.zeros(0, dtype=np.float32)
    
    if len(chunks) == 1:
        return chunks[0].astype(np.float32)
    
    # Start with first chunk
    result = chunks[0].astype(np.float32)
    
    for chunk in chunks[1:]:
        chunk = chunk.astype(np.float32)
        
        if len(result) < crossfade_samples or len(chunk) < crossfade_samples:
            # Simple concatenation for short chunks
            result = np.concatenate([result, chunk])
        else:
            # Equal-power crossfade
            fade_out = np.linspace(1.0, 0.0, crossfade_samples)
            fade_in = np.linspace(0.0, 1.0, crossfade_samples)
            
            # Apply fade to overlapping regions
            result[-crossfade_samples:] *= fade_out
            chunk[:crossfade_samples] *= fade_in
            
            # Sum overlapping region and append remainder
            result[-crossfade_samples:] += chunk[:crossfade_samples]
            result = np.concatenate([result, chunk[crossfade_samples:]])
    
    return result

def save_audio_atomic(audio: np.ndarray, path: str, sample_rate: int = 24000) -> Dict[str, Any]:
    """
    Atomically save audio file with QC validation.
    
    Args:
        audio: Audio array
        path: Output path
        sample_rate: Sample rate
        
    Returns:
        Save result with metrics
    """
    # QC check
    qc_metrics = qc_24k_mono(audio)
    
    if not qc_metrics["is_valid"]:
        print(f"⚠️  Audio QC warnings:")
        if qc_metrics["is_clipped"]:
            print(f"   Clipped samples: {qc_metrics['clipped_samples']}")
        if abs(qc_metrics["dc_offset"]) >= 0.01:
            print(f"   DC offset: {qc_metrics['dc_offset']:.6f}")
        if qc_metrics["peak_dbfs"] > 0.1:
            print(f"   Peak above 0dBFS: {qc_metrics['peak_dbfs']:.2f}dBFS")
    
    # Normalize to -1dBFS
    audio_normalized = normalize_audio(audio, -1.0)
    
    # Atomic write: tmp -> fsync -> rename
    tmp_path = path + ".tmp"
    
    try:
        # Write to temp file
        sf.write(tmp_path, audio_normalized, sample_rate, subtype="PCM_16")
        
        # Sync to disk
        import os
        fd = os.open(tmp_path, os.O_RDONLY)
        os.fsync(fd)
        os.close(fd)
        
        # Atomic rename
        os.rename(tmp_path, path)
        
        return {
            "success": True,
            "path": path,
            "qc_metrics": qc_metrics,
            "file_size": os.path.getsize(path)
        }
        
    except Exception as e:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

def validate_voice_file(path: str) -> Dict[str, Any]:
    """
    Validate voice file meets requirements.
    
    Args:
        path: Path to voice file
        
    Returns:
        Validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "metrics": {}
    }
    
    try:
        # Load audio
        audio, sr = sf.read(path, dtype="float32", always_2d=False)
        
        # Check format
        if audio.ndim > 1:
            result["warnings"].append(f"Stereo audio detected, will convert to mono")
            audio = audio.mean(axis=1)
        
        if sr != 24000:
            result["warnings"].append(f"Sample rate {sr}Hz, will resample to 24kHz")
        
        # Check duration
        duration = len(audio) / sr
        if duration < 0.4:
            result["errors"].append(f"Voice too short: {duration:.2f}s (min 0.4s)")
        elif duration > 30.0:
            result["warnings"].append(f"Voice very long: {duration:.2f}s (recommend <6s)")
        
        # Check quality
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        
        if rms < 1e-4:
            result["errors"].append("Voice too quiet (low RMS)")
        if peak >= 0.999:
            result["warnings"].append("Voice may be clipped")
        
        result["metrics"] = {
            "duration": duration,
            "sample_rate": sr,
            "peak": float(peak),
            "rms": float(rms),
            "channels": audio.ndim
        }
        
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Cannot load voice file: {e}")
    
    if result["errors"]:
        result["valid"] = False
    
    return result