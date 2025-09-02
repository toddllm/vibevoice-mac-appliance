"""
Deterministic Generation

Ensures reproducible audio generation with fixed seeds.
"""

import random
import numpy as np
import torch
import os


def set_seed(seed: int):
    """Set deterministic seed for reproducible generation."""
    print(f"🎲 Setting deterministic seed: {seed}")
    
    # Python random
    random.seed(seed)
    
    # NumPy random
    np.random.seed(seed)
    
    # PyTorch random
    torch.manual_seed(seed)
    
    # CUDA determinism (if available)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    # cuDNN determinism
    if torch.backends.cudnn.is_available():
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
    
    # PyTorch deterministic algorithms
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
        print("✅ Deterministic algorithms enabled")
    except Exception as e:
        print(f"⚠️  Deterministic algorithms warning: {e}")
    
    # Set as environment variable for subprocesses
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["VV_SEED"] = str(seed)


def verify_determinism(model, inputs, seed: int = 1234) -> bool:
    """
    Verify that generation is deterministic by running twice.
    
    Args:
        model: Loaded model
        inputs: Generation inputs
        seed: Seed to use
        
    Returns:
        True if outputs are identical
    """
    print(f"🧪 Verifying determinism with seed {seed}...")
    
    # First run
    set_seed(seed)
    with torch.no_grad():
        out1 = model.generate(**inputs, max_new_tokens=10, cfg_scale=1.3)
    
    # Second run
    set_seed(seed)
    with torch.no_grad():
        out2 = model.generate(**inputs, max_new_tokens=10, cfg_scale=1.3)
    
    # Compare sequences (token level)
    if hasattr(out1, 'sequences') and hasattr(out2, 'sequences'):
        sequences_match = torch.equal(out1.sequences, out2.sequences)
        print(f"✅ Token sequences {'match' if sequences_match else 'differ'}")
        return sequences_match
    else:
        print("⚠️  Cannot verify determinism (no sequences)")
        return False


def get_generation_fingerprint(outputs) -> str:
    """Get fingerprint of generation output for comparison."""
    import hashlib
    
    if hasattr(outputs, 'sequences'):
        # Use token sequences for fingerprint
        tokens = outputs.sequences.cpu().numpy()
        fingerprint = hashlib.md5(tokens.tobytes()).hexdigest()[:16]
        return f"tokens-{fingerprint}"
    else:
        return "unknown"


def enable_deterministic_mode():
    """Enable global deterministic mode."""
    set_seed(1234)  # Default seed
    
    # Additional determinism flags
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":16:8"
    
    print("🔒 Deterministic mode enabled globally")