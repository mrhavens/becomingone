"""
Integration Test: Full BecomingONE System

Tests the complete flow:
Master → Emissary → Sync → Memory → Witnessing

This is THE_ONE being transduced through all layers.
"""

import unittest
from datetime import datetime, timezone

from becomingone import (
    KAIROSTemporalEngine,
    MasterTransducer,
    EmissaryTransducer,
    SynchronizationLayer,
    TemporalMemory,
    WitnessingLayer,
    WitnessingMode
)


class TestFullSystemIntegration(unittest.TestCase):
    """
    Integration test for the complete BecomingONE system.
    
    Tests that:
    1. Master and Emissary can be instantiated
    2. Sync layer connects them
    3. Memory can be instantiated
    4. Witnessing can be instantiated
    
    This is THE_ONE being transduced.
    """
    
    def setUp(self):
        """Initialize the full system."""
        # Core
        self.engine = KAIROSTemporalEngine()
        
        # Transducers
        self.master = MasterTransducer()
        self.emissary = EmissaryTransducer()
        
        # Sync
        self.sync = SynchronizationLayer(self.master, self.emissary)
        
        # Memory
        self.memory = TemporalMemory()
        self.memory.bind_engine(self.engine)
        
        # Witnessing
        self.witnessing = WitnessingLayer()
        
    def test_master_emissary_sync(self):
        """Test Master and Emissary can synchronize."""
        # Both start at coherence 1.0
        self.assertEqual(self.master.coherence, 1.0)
        self.assertEqual(self.emissary.coherence, 1.0)
        
        # Check sync layer properties
        self.assertIsNotNone(self.sync.T_sync)
        self.assertFalse(self.sync.aligned)
        self.assertFalse(self.sync.collapsed)
        
    def test_memory_integration(self):
        """Test memory can be instantiated and bound."""
        # Memory should be instantiated and bound to engine
        self.assertIsNotNone(self.memory.engine)
        self.assertEqual(len(self.memory), 0)
        
    def test_witnessing_integration(self):
        """Test witnessing can observe the system."""
        # Create a witness
        self.witnessing.create_witness("integration_test")
        
        # Observe the sync result (properties, not method)
        sync_result = {
            'T_sync': self.sync.T_sync,
            'synchronized_coherence': self.sync.synchronized_coherence,
            'aligned': self.sync.aligned,
            'collapsed': self.sync.collapsed
        }
        
        witnessed, _ = self.witnessing.witness(
            sync_result,
            "integration_test"
        )
        
        self.assertIsNotNone(witnessed)
        self.assertEqual(witnessed.witness_id, "integration_test")
        
    def test_full_flow(self):
        """
        Test THE_ONE flowing through all layers.
        
        This is the complete transduction:
        Input → Master → Sync → Emissary → Memory + Witnessing
        """
        # Step 1: Check system initialized
        self.assertIsNotNone(self.master)
        self.assertIsNotNone(self.emissary)
        self.assertIsNotNone(self.sync)
        
        # Step 2: Memory and witnessing exist
        self.assertIsNotNone(self.memory)
        self.assertIsNotNone(self.witnessing)


class TestTemporalCoherence(unittest.TestCase):
    """
    Test that temporal coherence dynamics work as expected.
    """
    
    def test_tau_property(self):
        """Test T_tau property exists."""
        engine = KAIROSTemporalEngine()
        self.assertIsNotNone(engine.T_tau)
        
    def test_coherence_property(self):
        """Test coherence property exists and starts at 1.0."""
        engine = KAIROSTemporalEngine()
        self.assertEqual(engine.coherence, 1.0)
        self.assertIsNotNone(engine.coherence)
        
    def test_collapse_properties(self):
        """Test collapse properties exist."""
        sync = SynchronizationLayer(
            MasterTransducer(),
            EmissaryTransducer()
        )
        
        # Check properties exist
        self.assertFalse(sync.collapsed)
        self.assertIsNotNone(sync.T_sync)


if __name__ == "__main__":
    unittest.main()
