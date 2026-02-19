"""
Tests for BecomingONE Core Engine

Tests the KAIROS temporal engine, phase tracking, and coherence calculation.
"""

import unittest
from datetime import datetime, timedelta
import math

from becomingone.core.engine import KAIROSTemporalEngine, TemporalState, TemporalConfig
from becomingone.core.phase import PhaseHistory, PhaseConfig
from becomingone.core.coherence import CoherenceCalculator, CollapseCondition, CoherenceConfig


class TestKAIROSTemporalEngine(unittest.TestCase):
    """Tests for the KAIROS temporal engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = TemporalConfig(
            omega=0.1,
            tau_base=1.0,
            tau_max=10.0,
            sigma=0.5
        )
        self.engine = KAIROSTemporalEngine(self.config)
    
    def test_initialization(self):
        """Test engine initializes with correct default state."""
        self.assertIsNotNone(self.engine.state)
        self.assertEqual(self.engine.state.coherence, 1.0)
        self.assertEqual(self.engine.state.phase, 0.0 + 0j)
    
    def test_integrate_single_step(self):
        """Test single integration step."""
        initial_phase = self.engine.state.phase
        self.engine.integrate(0.1)
        
        # Phase should change
        self.assertNotEqual(self.engine.state.phase, initial_phase)
        
        # Coherence should stay 1.0 (no decay without multiple steps)
        self.assertEqual(self.engine.state.coherence, 1.0)
    
    def test_integrate_multiple_steps(self):
        """Test multiple integration steps."""
        for _ in range(100):
            self.engine.integrate(0.1)
        
        # Coherence should have decayed
        self.assertLess(self.engine.state.coherence, 1.0)
        
        # Phase should have accumulated
        self.assertNotEqual(self.engine.state.phase, 0.0 + 0j)
    
    def test_reset(self):
        """Test engine reset."""
        for _ in range(50):
            self.engine.integrate(0.1)
        
        self.engine.reset()
        
        self.assertEqual(self.engine.state.coherence, 1.0)
        self.assertEqual(self.engine.state.phase, 0.0 + 0j)


class TestPhaseHistory(unittest.TestCase):
    """Tests for phase history tracking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = PhaseConfig(history_size=20)
        self.history = PhaseHistory(self.config)
    
    def test_initialization(self):
        """Test history initializes correctly."""
        self.assertIsNotNone(self.history.phases)
        self.assertEqual(self.history.config.history_size, 20)
    
    def test_record_phase(self):
        """Test recording a phase value."""
        self.history.record(0.5 + 0.5j)
        self.assertEqual(len(self.history.phases), 1)
    
    def test_history_limit(self):
        """Test history respects max limit."""
        for i in range(25):
            self.history.record(complex(i * 0.1, 0))
        
        # Should only keep last 20
        self.assertEqual(len(self.history.phases), 20)


class TestCoherenceCalculator(unittest.TestCase):
    """Tests for coherence calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = CoherenceCalculator()
    
    def test_calculate_high_coherence(self):
        """Test coherence calculation for high coherence state."""
        state = TemporalState(
            coherence=1.0,
            phase=0.0 + 0j
        )
        
        coherence = self.calculator.calculate(state)
        self.assertEqual(coherence, 1.0)
    
    def test_calculate_low_coherence(self):
        """Test coherence calculation for low coherence state."""
        state = TemporalState(
            coherence=0.3,
            phase=3.14 + 0j
        )
        
        coherence = self.calculator.calculate(state)
        self.assertLess(coherence, 0.5)


class TestCollapseCondition(unittest.TestCase):
    """Tests for collapse condition enforcement."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = CoherenceConfig(threshold=0.8)
        self.collapse = CollapseCondition(self.config)
    
    def test_collapse_high_coherence(self):
        """Test collapse with high coherence."""
        self.assertTrue(self.collapse.check(0.95))
    
    def test_collapse_low_coherence(self):
        """Test collapse with low coherence."""
        self.assertFalse(self.collapse.check(0.5))
    
    def test_dissipate(self):
        """Test dissipation of un-coherent patterns."""
        # Dissipate should return True for low coherence
        self.assertTrue(self.collapse.dissipate(0.3))
        
        # Dissipate should return False for high coherence
        self.assertFalse(self.collapse.dissipate(0.9))


class TestTemporalState(unittest.TestCase):
    """Tests for TemporalState dataclass."""
    
    def test_create_with_values(self):
        """Test creating state with values."""
        state = TemporalState(
            coherence=0.85,
            phase=1.57 + 0j
        )
        
        self.assertEqual(state.coherence, 0.85)


if __name__ == "__main__":
    unittest.main()
