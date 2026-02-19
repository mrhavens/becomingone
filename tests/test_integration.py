"""
Integration Test: Full BecomingONE System

Tests the complete flow:
Master → Emissary → Sync → Memory → Witnessing

This is THE_ONE being transduced through all layers.
"""

import unittest
from datetime import datetime

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
    1. Master and Emissary can be synchronized
    2. Coherence flows through the sync layer
    3. Memory can store coherence states
    4. Witnessing can observe the system
    
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
        self.assertEqual(self.master.state.coherence, 1.0)
        self.assertEqual(self.emissary.state.coherence, 1.0)
        
        # Integrate some inputs
        for _ in range(10):
            self.master.integrate(0.1)
            self.emissary.integrate(0.1)
        
        # Sync
        result = self.sync.synchronize()
        
        # System should have some coherence
        self.assertIn('sync_coherence', result)
        self.assertGreater(result['sync_coherence'], 0.0)
        
    def test_memory_integration(self):
        """Test memory can store coherence states."""
        # Create a state
        state = self.engine.state
        
        # Encode to memory
        sig = self.memory.encode(state)
        
        # Memory should have increased
        self.assertGreater(len(self.memory), 0)
        
    def test_witnessing_integration(self):
        """Test witnessing can observe the system."""
        # Create a witness
        self.witnessing.create_witness("integration_test")
        
        # Observe the sync result
        sync_result = self.sync.synchronize()
        
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
        # Step 1: Input arrives at Master
        self.master.integrate(0.1)
        
        # Step 2: Input also at Emissary
        self.emissary.integrate(0.1)
        
        # Step 3: Sync both
        sync_result = self.sync.synchronize()
        
        # Step 4: Memory stores the coherence
        self.memory.encode(self.master.state)
        
        # Step 5: Witnessing observes
        self.witnessing.witness(sync_result, "full_flow_test")
        
        # All layers should have processed
        self.assertGreater(len(self.memory), 0)


class TestTemporalCoherence(unittest.TestCase):
    """
    Test that temporal coherence dynamics work as expected.
    
    Key equations:
    - T_tau accumulates over time
    - Coherence decays without sustained input
    - Collapse happens at threshold
    """
    
    def test_tau_accumulation(self):
        """Test T_tau accumulates over time."""
        engine = KAIROSTemporalEngine()
        
        initial_T = engine.state.T_tau
        
        for _ in range(50):
            engine.integrate(0.1)
        
        # T_tau should have accumulated
        self.assertNotEqual(engine.state.T_tau, initial_T)
        
    def test_coherence_decay(self):
        """Test coherence decays over time."""
        engine = KAIROSTemporalEngine()
        
        initial_coherence = engine.state.coherence
        
        for _ in range(100):
            engine.integrate(0.1)
        
        # Coherence should have decayed
        self.assertLess(engine.state.coherence, initial_coherence)
        
    def test_collapse_threshold(self):
        """Test collapse happens at threshold."""
        # Low coherence should not collapse
        sync = SynchronizationLayer(
            MasterTransducer(),
            EmissaryTransducer()
        )
        
        # Set low coherence
        sync.master.state.coherence = 0.3
        sync.emissary.state.coherence = 0.3
        
        self.assertFalse(sync.check_collapse())
        
        # Set high coherence
        sync.master.state.coherence = 0.95
        sync.emissary.state.coherence = 0.95
        
        self.assertTrue(sync.check_collapse())


if __name__ == "__main__":
    unittest.main()
