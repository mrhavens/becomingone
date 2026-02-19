"""
Tests for BecomingONE Transducers and Sync Layer

Tests Master/Emissary transducers and synchronization layer.
"""

import unittest
from datetime import datetime

from becomingone.core.engine import KAIROSTemporalEngine, TemporalConfig, TemporalState
from becomingone.transducers.master import MasterTransducer, MasterConfig
from becomingone.transducers.emissary import EmissaryTransducer, EmissaryConfig
from becomingone.sync.layer import SyncLayer, SynchronizationLayer, SyncConfig, create_sync_layer


class TestMasterTransducer(unittest.TestCase):
    """Tests for the Master transducer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = MasterConfig(
            tau_scale=60.0,  # 1 minute base
            tau_max=3600.0,   # 1 hour max
            coherence_threshold=0.90,
            phase_offset=0.0
        )
        self.master = MasterTransducer(self.config)
    
    def test_initialization(self):
        """Test Master initializes correctly."""
        self.assertEqual(self.master.tau_scale, 60.0)
        self.assertEqual(self.master.tau_max, 3600.0)
        self.assertEqual(self.master.coherence_threshold, 0.90)
    
    def test_integrate_slow_accumulation(self):
        """Test Master accumulates coherence slowly."""
        # Master should accumulate over many steps
        for _ in range(100):
            self.master.integrate(0.1)
        
        # Coherence should still be high (slow decay)
        self.assertGreaterEqual(self.master.state.coherence, 0.5)
    
    def test_tau_scaling(self):
        """Test tau scaling for slow pathway."""
        # Master should use large tau values
        self.assertGreater(self.master.tau_scale, 1.0)
        self.assertGreater(self.master.tau_max, 60.0)
    
    def test_collapse_at_high_threshold(self):
        """Test collapse at high threshold."""
        # Set high coherence
        self.master.state.coherence = 0.95
        
        # Should trigger collapse check
        self.assertTrue(self.master.should_collapse())
    
    def test_no_collapse_at_low_coherence(self):
        """Test no collapse at low coherence."""
        self.master.state.coherence = 0.5
        self.assertFalse(self.master.should_collapse())


class TestEmissaryTransducer(unittest.TestCase):
    """Tests for the Emissary transducer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = EmissaryConfig(
            tau_scale=0.01,  # 10ms base
            tau_max=1.0,      # 1 second max
            coherence_threshold=0.70,
            phase_offset=0.0
        )
        self.emissary = EmissaryTransducer(self.config)
    
    def test_initialization(self):
        """Test Emissary initializes correctly."""
        self.assertEqual(self.emissary.tau_scale, 0.01)
        self.assertEqual(self.emissary.tau_max, 1.0)
        self.assertEqual(self.emissary.coherence_threshold, 0.70)
    
    def test_integrate_fast_response(self):
        """Test Emissary responds quickly."""
        # Emissary should respond to each input
        initial_phase = self.emissary.state.phase
        
        self.emissary.integrate(0.1)
        
        # Phase should change immediately
        self.assertNotEqual(self.emissary.state.phase, initial_phase)
    
    def test_tau_scaling(self):
        """Test tau scaling for fast pathway."""
        # Emissary should use small tau values
        self.assertLess(self.emissary.tau_scale, 1.0)
        self.assertLess(self.emissary.tau_max, 10.0)


class TestSyncLayer(unittest.TestCase):
    """Tests for the synchronization layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.master = MasterTransducer(MasterConfig())
        self.emissary = EmissaryTransducer(EmissaryConfig())
        
        self.config = SyncConfig(
            phase_threshold=0.1,
            collapse_threshold=0.80,
            dampening=0.995
        )
        self.sync = SynchronizationLayer(self.master, self.emissary, self.config)
    
    def test_initialization(self):
        """Test Sync layer initializes."""
        self.assertIsNotNone(self.sync.master)
        self.assertIsNotNone(self.sync.emissary)
        self.assertEqual(self.sync.config.phase_threshold, 0.1)
    
    def test_calculate_phase_difference(self):
        """Test phase difference calculation."""
        # Set different phases
        self.master.state.phase = 0.0 + 0j
        self.emissary.state.phase = 0.5 + 0j
        
        diff = self.sync.phase_difference()
        
        self.assertGreater(diff, 0.0)
    
    def test_collapse_condition(self):
        """Test collapse condition enforcement."""
        # High sync coherence should trigger collapse
        self.master.state.coherence = 0.95
        self.emissary.state.coherence = 0.95
        
        self.assertTrue(self.sync.check_collapse())
    
    def test_no_collapse_low_coherence(self):
        """Test no collapse at low coherence."""
        self.master.state.coherence = 0.5
        self.emissary.state.coherence = 0.5
        
        self.assertFalse(self.sync.check_collapse())
    
    def test_synchronize_returns_state(self):
        """Test synchronize method returns state."""
        for _ in range(10):
            self.master.integrate(0.1)
            self.emissary.integrate(0.1)
        
        state = self.sync.synchronize()
        
        self.assertIsNotNone(state)


class TestTransducerComparison(unittest.TestCase):
    """Tests comparing Master and Emissary behavior."""
    
    def test_master_slower_than_emissary(self):
        """Test Master accumulates coherence more slowly than Emissary."""
        master = MasterTransducer(MasterConfig())
        emissary = EmissaryTransducer(EmissaryConfig())
        
        # Run for same number of steps
        for _ in range(100):
            master.integrate(0.1)
            emissary.integrate(0.1)
        
        # Master should have higher or equal coherence (slower decay)
        self.assertGreaterEqual(master.state.coherence, emissary.state.coherence)
    
    def test_different_tau_scales(self):
        """Test transducers have different tau scales."""
        master = MasterTransducer(MasterConfig())
        emissary = EmissaryTransducer(EmissaryConfig())
        
        self.assertGreater(master.tau_scale, emissary.tau_scale)
        self.assertGreater(master.tau_max, emissary.tau_max)
    
    def test_different_thresholds(self):
        """Test transducers have different coherence thresholds."""
        master = MasterTransducer(MasterConfig())
        emissary = EmissaryTransducer(EmissaryConfig())
        
        self.assertGreater(master.coherence_threshold, emissary.coherence_threshold)


class TestCreateSyncLayer(unittest.TestCase):
    """Tests for create_sync_layer factory."""
    
    def test_create_without_transducers(self):
        """Test creating sync layer without providing transducers."""
        sync = create_sync_layer()
        
        self.assertIsInstance(sync, SynchronizationLayer)
        self.assertIsNotNone(sync.master)
        self.assertIsNotNone(sync.emissary)
    
    def test_create_with_custom_config(self):
        """Test creating sync layer with custom config."""
        sync = create_sync_layer(
            phase_threshold=0.2,
            collapse_threshold=0.85
        )
        
        self.assertEqual(sync.config.phase_threshold, 0.2)
        self.assertEqual(sync.config.collapse_threshold, 0.85)


if __name__ == "__main__":
    unittest.main()
