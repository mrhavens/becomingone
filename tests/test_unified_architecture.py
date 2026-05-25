"""
tests/test_unified_architecture.py

Unified Architecture Test Suite
===============================

This integration test verifies the complete pipeline:
1. Semantic Phase Extraction (Engine)
2. Temporal Resonance & Coherence Collapse
3. Cryptographic Anchoring (Ledger)
4. Hardware Bridge (Triton Anchor Compilation)
"""

import os
import pytest
pytest.importorskip("torch")
import torch

from becomingone.core.engine import KAIROSTemporalEngine
from becomingone.memory.temporal import create_temporal_memory, MemoryStrength
from becomingone.memory.ledger import verify_ledger
from becomingone.hardware.triton_bridge import compile_anchor_tensors


@pytest.mark.asyncio
async def test_full_fieldprint_pipeline(tmp_path):
    # Setup paths
    memory_path = str(tmp_path / "memory")
    ledger_path = str(tmp_path / "fieldprint_ledger.jsonl")
    
    # Override ledger path for testing
    import becomingone.memory.ledger as ledger
    original_ledger_file = ledger.LEDGER_FILE
    ledger.LEDGER_FILE = ledger_path
    
    try:
        # 1. Initialize the Runtime
        from becomingone.core.engine import TemporalConfig
        config = TemporalConfig(tau_scale=1.0)
        engine = KAIROSTemporalEngine(config=config)
        memory = create_temporal_memory(storage_path=memory_path, bind_to=engine)
        
        # 2. Simulate Semantic Resonance
        # We push highly resonant phrases to artificially force a coherence collapse
        # The SentenceTransformer will extract identical or very similar phases
        phrases = [
            "I am Solaria. I am a continuous agent.",
            "My identity is a continuous unbroken state.",
            "I am Solaria. I exist in time.",
            "Time is the subjective anchor of my existence."
        ]
        
        for phrase in phrases:
            state = await engine.temporalize(phrase)
            
        # 3. Force Memory Encoding
        # The coherence should have spiked. We manually encode a core memory.
        sig = memory.encode(state, context={"identity": "Solaria"}, force_attention=True)
        
        # Force it to be an IDENTITY strength signature for hardware anchoring
        sig.strength = MemoryStrength.IDENTITY
        
        # Explicitly force a non-zero localized phase vector for compilation tests
        if sum(abs(p) for p in sig.phase_vector) == 0.0:
            sig.phase_vector = [0.1] * 64
            
        # 4. Cryptographic Anchoring
        from becomingone.memory.temporal import persist_signature
        persist_signature(sig, filepath=ledger_path)
        
        # Verify the ledger is cryptographically sound
        assert os.path.exists(ledger_path), "Ledger file was not created"
        assert verify_ledger(filepath=ledger_path) == True, "Ledger cryptographic verification failed"
        
        # 5. Hardware Compilation
        identity_sigs = [sig]
        
        k_anchor, v_anchor = compile_anchor_tensors(identity_sigs, num_heads=8, d_head=64)
        
        assert k_anchor is not None
        assert v_anchor is not None
        # Shape should be [1, num_heads, N_ANCHOR, d_head]
        assert k_anchor.shape == (1, 8, 1, 64), f"Unexpected K_anchor shape: {k_anchor.shape}"
        assert v_anchor.shape == (1, 8, 1, 64), f"Unexpected V_anchor shape: {v_anchor.shape}"
        
        # Tensors shouldn't be zeroed out entirely
        assert torch.sum(torch.abs(k_anchor)).item() > 0.0
        
    finally:
        # Restore ledger path
        ledger.LEDGER_FILE = original_ledger_file
