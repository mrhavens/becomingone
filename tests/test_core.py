import pytest
"""
Tests for BecomingONE Core Engine

Tests that core modules can be imported and initialized correctly.
"""

import unittest
from datetime import datetime
from datetime import timezone

from becomingone import (
    KAIROSTemporalEngine, 
    PhaseHistory, 
    CoherenceCalculator, 
    CollapseCondition
)


class TestKAIROSTemporalEngine(unittest.TestCase):
    """Tests for the KAIROS temporal engine."""
    
    @pytest.mark.asyncio
    async def test_import(self):
        """Test engine can be imported."""
        self.assertIsNotNone(KAIROSTemporalEngine)
    
    @pytest.mark.asyncio
    async def test_instantiate(self):
        """Test engine can be instantiated."""
        engine = KAIROSTemporalEngine()
        self.assertIsNotNone(engine)
        self.assertEqual(engine.coherence, 1.0)
    
    @pytest.mark.asyncio
    async def test_temporalize(self):
        """Test temporalize method works."""
        import asyncio
        engine = KAIROSTemporalEngine()
        result = await engine.temporalize("test phrase")
        self.assertIsNotNone(result)
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """Test reset works."""
        import asyncio
        engine = KAIROSTemporalEngine()
        await engine.temporalize("test phrase")
        engine.reset()
        self.assertEqual(engine.coherence, 1.0)
        self.assertEqual(engine.integration_count, 0)


class TestPhaseHistory(unittest.TestCase):
    """Tests for phase history tracking."""
    
    @pytest.mark.asyncio
    async def test_import(self):
        """Test PhaseHistory can be imported."""
        self.assertIsNotNone(PhaseHistory)
    
    @pytest.mark.asyncio
    async def test_instantiate(self):
        """Test PhaseHistory can be instantiated."""
        history = PhaseHistory()
        self.assertIsNotNone(history)
    
    @pytest.mark.asyncio
    async def test_advance(self):
        """Test advance method works."""
        history = PhaseHistory()
        state = history.advance(0.1, "test")
        self.assertIsNotNone(state)
    
    @pytest.mark.asyncio
    async def test_set_phase(self):
        """Test set_phase method works."""
        history = PhaseHistory()
        state = history.set_phase(0.5 + 0.5j, "test")
        self.assertIsNotNone(state)
    
    @pytest.mark.asyncio
    async def test_current(self):
        """Test current property returns state."""
        history = PhaseHistory()
        current = history.current
        self.assertIsNotNone(current)
    
    @pytest.mark.asyncio
    async def test_velocity(self):
        """Test velocity property works."""
        history = PhaseHistory()
        # Advance a few times
        for _ in range(5):
            history.advance(0.1, "test")
        velocity = history.velocity
        self.assertIsNotNone(velocity)


class TestCoherenceCalculator(unittest.TestCase):
    """Tests for coherence calculation."""
    
    @pytest.mark.asyncio
    async def test_import(self):
        """Test CoherenceCalculator can be imported."""
        self.assertIsNotNone(CoherenceCalculator)
    
    @pytest.mark.asyncio
    async def test_instantiate(self):
        """Test calculator can be instantiated."""
        calc = CoherenceCalculator()
        self.assertIsNotNone(calc)
    
    @pytest.mark.asyncio
    async def test_update(self):
        """Test update method works."""
        calc = CoherenceCalculator()
        result = calc.update(1.0 + 0.5j)
        self.assertIsNotNone(result)
    
    @pytest.mark.asyncio
    async def test_compute_from_phases(self):
        """Test compute_from_phases method works."""
        calc = CoherenceCalculator()
        from datetime import datetime, timedelta
        now = datetime.now(timezone.utc)
        timestamps = [now + timedelta(seconds=i) for i in range(3)]
        result = calc.compute_from_phases(
            [0.1+0.1j, 0.2+0.2j, 0.3+0.3j], 
            timestamps=timestamps,
            tau=1.0,
            omega=0.1
        )
        self.assertIsNotNone(result)


class TestCollapseCondition(unittest.TestCase):
    """Tests for collapse condition enforcement."""
    
    @pytest.mark.asyncio
    async def test_import(self):
        """Test CollapseCondition can be imported."""
        self.assertIsNotNone(CollapseCondition)
    
    @pytest.mark.asyncio
    async def test_instantiate(self):
        """Test collapse can be instantiated."""
        collapse = CollapseCondition()
        self.assertIsNotNone(collapse)
    
    @pytest.mark.asyncio
    async def test_evaluate(self):
        """Test evaluate method works."""
        collapse = CollapseCondition()
        result = collapse.evaluate(0.95)
        self.assertIsNotNone(result)
    
    @pytest.mark.asyncio
    async def test_reset(self):
        """Test reset works."""
        collapse = CollapseCondition()
        collapse.evaluate(0.95)
        collapse.reset()
        self.assertFalse(collapse.collapsed)


if __name__ == "__main__":
    unittest.main()
