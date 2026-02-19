"""
Tests for BecomingONE Memory and Witnessing

Tests temporal memory system and witnessing layer.
"""

import unittest
import os
import shutil
from datetime import datetime, timedelta, timezone

from becomingone import (
    KAIROSTemporalEngine,
    TemporalMemory, 
    TemporalSignature,
    WitnessingLayer,
    WitnessingMode
)
from becomingone.memory.temporal import MemoryStrength


class TestTemporalSignature(unittest.TestCase):
    """Tests for TemporalSignature."""
    
    def test_create_signature(self):
        """Test creating a temporal signature."""
        sig = TemporalSignature(
            signature_id="test_123",
            coherence_value=0.85,
            phase_vector=[0.0, 0.1, 0.2],
            frequency_modes={"omega1": 0.1},
            context_hash="abc123",
            strength=None,  # Optional
            created_at=datetime.now(timezone.utc),
            last_accessed=datetime.now(timezone.utc),
            access_count=0
        )
        
        self.assertEqual(sig.signature_id, "test_123")
        self.assertEqual(sig.coherence_value, 0.85)
    
    def test_signature_serialization(self):
        """Test signature to/from dict."""
        sig = TemporalSignature(
            signature_id="test_456",
            coherence_value=0.75,
            phase_vector=[0.1, 0.2],
            frequency_modes={},
            context_hash="xyz",
            strength=MemoryStrength.WORKING,
            created_at=datetime.now(timezone.utc),
            last_accessed=datetime.now(timezone.utc)
        )
        
        data = sig.to_dict()
        self.assertIn("signature_id", data)
        self.assertEqual(data["signature_id"], "test_456")


class TestTemporalMemory(unittest.TestCase):
    """Tests for TemporalMemory system."""
    
    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.test_dir = "/tmp/becomingone_test_memory"
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.memory = TemporalMemory(storage_path=self.test_dir)
        
        # Create engine and bind
        engine = KAIROSTemporalEngine()
        self.memory.bind_engine(engine)
    
    def tearDown(self):
        """Clean up test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test memory initializes correctly."""
        self.assertEqual(len(self.memory), 0)
        self.assertIsNotNone(self.memory.engine)
    
    def test_instantiate(self):
        """Test memory can be instantiated."""
        memory = TemporalMemory()
        self.assertIsNotNone(memory)


class TestWitnessingLayer(unittest.TestCase):
    """Tests for WitnessingLayer."""
    
    def test_create_witness(self):
        """Test creating a witness."""
        witnessing = WitnessingLayer()
        witness = witnessing.create_witness(
            "test_witness",
            mode=WitnessingMode.OBSERVE
        )
        
        self.assertEqual(witness.witness_id, "test_witness")
        self.assertEqual(witness.mode, WitnessingMode.OBSERVE)
    
    def test_observe(self):
        """Test observing content."""
        witnessing = WitnessingLayer()
        witnessing.create_witness("observer1")
        
        content = {"data": "test_content", "value": 42}
        
        witnessed = witnessing.observe(content, "observer1")
        
        self.assertIsNotNone(witnessed)
        self.assertEqual(witnessed.witness_id, "observer1")
    
    def test_integrate(self):
        """Test integrating witnessed content."""
        witnessing = WitnessingLayer()
        witnessing.create_witness("integrator")
        
        content = "test"
        witnessed = witnessing.observe(content, "integrator")
        
        contribution = witnessing.integrate(witnessed, "integrator")
        
        self.assertGreaterEqual(contribution, 0.0)
    
    def test_witness_modes(self):
        """Test different witnessing modes."""
        modes = list(WitnessingMode)
        
        for mode in modes:
            witnessing = WitnessingLayer()
            witness = witnessing.create_witness(
                f"mode_test_{mode.value}",
                mode=mode
            )
            self.assertEqual(witness.mode, mode)


if __name__ == "__main__":
    unittest.main()
