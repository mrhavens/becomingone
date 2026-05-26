"""
becomingone/triton_bridge.py

Hardware Anchoring Bridge (Triton)
==================================

Injects the continuous TemporalSignature (Right Hemisphere phase) directly into the
KV cache of the discrete Transformer (Left Hemisphere).

Fixes Issue #28: Implements Inverse-Rotary Position Embedding (Inverse-RoPE)
before injection so that absolute positional rotations do not destroy the anchor's
semantic phase over long context lengths.
"""

import math
import numpy as np

def apply_inverse_rope(anchor_tensor: np.ndarray, seq_pos: int, head_dim: int) -> np.ndarray:
    """
    Applies Inverse-RoPE to the anchor tensor.
    When the Transformer applies forward RoPE to the KV cache at seq_pos,
    the two transformations will cancel out, preserving the exact mathematical
    phase of the KAIROS anchor in the latent space.
    """
    assert len(anchor_tensor.shape) == 1
    assert head_dim % 2 == 0
    
    out = np.zeros_like(anchor_tensor)
    
    # RoPE base frequency usually 10000.0 or 500000.0 (Llama 3)
    base = 10000.0
    
    for i in range(0, head_dim, 2):
        theta = seq_pos / (base ** (i / head_dim))
        
        cos_val = math.cos(-theta) # Inverse (negative theta)
        sin_val = math.sin(-theta)
        
        v0 = anchor_tensor[i]
        v1 = anchor_tensor[i+1] if i+1 < head_dim else 0.0
        
        out[i] = v0 * cos_val - v1 * sin_val
        if i+1 < head_dim:
            out[i+1] = v1 * cos_val + v0 * sin_val
            
    return out

def inject_hardware_anchor(kv_cache: np.ndarray, anchor_phase: complex, seq_pos: int = 0):
    """
    Simulates the Triton hardware-level DRAM injection of the continuous phase.
    """
    head_dim = kv_cache.shape[-1]
    
    # Create the base anchor vector from the complex phase
    anchor_vector = np.zeros(head_dim)
    anchor_vector[0] = anchor_phase.real
    anchor_vector[1] = anchor_phase.imag
    
    # Apply Inverse RoPE so it survives the LLM's absolute positional embedding
    ropeed_anchor = apply_inverse_rope(anchor_vector, seq_pos, head_dim)
    
    # Inject directly into KV cache at the specified sequence position
    kv_cache[..., seq_pos, :] = ropeed_anchor
    
    return kv_cache
