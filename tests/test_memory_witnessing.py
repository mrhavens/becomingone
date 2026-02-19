"""
Tests for BecomingONE Memory and Witnessing

Tests temporal memory system and witnessing layer.
"""

import unittest
import os
import shutil
from datetime import datetime, timedelta

from becomingone.core.engine import KAIROSTemporalEngine, TemporalConfig, TemporalState
from becomingone.memory.temporal import (
    TemporalMemory, TemporalSignature, PatternEcho,
    MemoryStrength, create_temporal_memory
)
from becomingone.witnessing.layer import (
    WitnessingLayer, WitnessState, WitnessedContent,
    WitnessingMode, create_witnessing_layer
)


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
            strength=MemoryStrength.EPISODIC,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0
        )

        self.assertEqual(sig.signature_id, "test_123")
        self.assertEqual(sig.coherence_value, 0.85)
        self.assertEqual(sig.strength, MemoryStrength.EPISODIC)

    def test_signature_serialization(self):
        """Test signature to/from dict."""
        sig = TemporalSignature(
            signature_id="test_456",
            coherence_value=0.75,
            phase_vector=[0.1, 0.2],
            frequency_modes={},
            context_hash="xyz",
            strength=MemoryStrength.WORKING,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )

        data = sig.to_dict()
        restored = TemporalSignature.from_dict(data)

        self.assertEqual(restored.signature_id, sig.signature_id)
        self.assertEqual(restored.coherence_value, sig.coherence_value)

    def test_decay_calculation(self):
        """Test memory decay calculation."""
        sig = TemporalSignature(
            signature_id="test_789",
            coherence_value=0.9,
            phase_vector=[],
            frequency_modes=[],
            context_hash="",
            strength=MemoryStrength.SEMANTIC,
            created_at=datetime.utcnow() - timedelta(hours=1),
            last_accessed=datetime.utcnow(),
            decay_rate=0.01
        )

        decay = sig.calculate_decay(datetime.utcnow())
        self.assertGreater(decay, 0.0)
        self.assertLessEqual(decay, 1.0)

    def test_should_retain(self):
        """Test retention decision."""
        sig = TemporalSignature(
            signature_id="test_retain",
            coherence_value=0.5,
            phase_vector=[],
            frequency_modes=[],
            context_hash="",
            strength=MemoryStrength.TRANSIENT,
            created_at=datetime.utcnow() - timedelta(days=30),
            last_accessed=datetime.utcnow(),
            decay_rate=0.1
        )

        # Old, weak memory should not be retained
        self.assertFalse(sig.should_retain(datetime.utcnow(), threshold=0.1))


class TestPatternEcho(unittest.TestCase):
    """Tests for PatternEcho."""

    def test_create_echo(self):
        """Test creating a pattern echo."""
        echo = PatternEcho(
            echo_id="echo_123",
            source_signature_id="sig_456",
            coherence_trace=0.7,
            phase_similarity=0.8,
            temporal_offset=3600.0,
            created_at=datetime.utcnow()
        )

        self.assertEqual(echo.echo_id, "echo_123")
        self.assertEqual(echo.coherence_trace, 0.7)

    def test_resonance_calculation(self):
        """Test resonance with another signature."""
        echo = PatternEcho(
            echo_id="echo_resonance",
            source_signature_id="sig_source",
            coherence_trace=0.8,
            phase_similarity=0.7,
            temporal_offset=100.0,
            created_at=datetime.utcnow()
        )

        sig = TemporalSignature(
            signature_id="sig_target",
            coherence_value=0.85,
            phase_vector=[0.5, 0.6, 0.7],
            frequency_modes=[],
            context_hash="",
            strength=MemoryStrength.EPISODIC,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow()
        )

        resonance = echo.resonance_with(sig)
        self.assertGreater(resonance, 0.0)
        self.assertLessEqual(resonance, 1.0)


class TestTemporalMemory(unittest.TestCase):
    """Tests for TemporalMemory system."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.test_dir = "/tmp/becomingone_test_memory"
        os.makedirs(self.test_dir, exist_ok=True)

        self.memory = TemporalMemory(
            storage_path=self.test_dir,
            max_memories=100
        )

        # Create engine and bind
        engine = KAIROSTemporalEngine(TemporalConfig())
        self.memory.bind_engine(engine)

    def tearDown(self):
        """Clean up test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization(self):
        """Test memory initializes correctly."""
        self.assertEqual(len(self.memory), 0)
        self.assertIsNotNone(self.memory.engine)

    def test_encode_state(self):
        """Test encoding a temporal state."""
        state = TemporalState(
            coherence=0.85,
            phase=0.5 + 0.5j
        )

        sig = self.memory.encode(state)

        self.assertIsNotNone(sig)
        self.assertEqual(sig.coherence_value, 0.85)
        self.assertIn(sig.signature_id, self.memory.signatures)

    def test_encode_ignores_low_coherence(self):
        """Test encoding ignores states below attention threshold."""
        state = TemporalState(
            coherence=0.3,  # Below 0.7 threshold
            phase=0.0 + 0.1j
        )

        sig = self.memory.encode(state)

        self.assertIsNone(sig)
        self.assertEqual(len(self.memory), 0)

    def test_force_encode(self):
        """Test forcing encoding of low coherence state."""
        state = TemporalState(
            coherence=0.3,
            phase=0.0 + 0.1j
        )

        sig = self.memory.encode(state, force_attention=True)

        self.assertIsNotNone(sig)
        self.assertEqual(len(self.memory), 1)

    def test_retrieve(self):
        """Test retrieving memories."""
        # Create some memories
        for i in range(5):
            state = TemporalState(
                coherence=0.8 + i * 0.02,
                phase=i * 0.1 + 0j
            )
            self.memory.encode(state)

        # Retrieve with query
        query_state = TemporalState(
            coherence=0.85,
            phase=0.2 + 0j
        )

        results = self.memory.retrieve(query_state, max_results=3)

        self.assertLessEqual(len(results), 3)
        self.assertGreater(len(results), 0)

    def test_recognize(self):
        """Test pattern recognition."""
        # Create a memory
        state = TemporalState(
            coherence=0.9,
            phase=0.0 + 0j
        )
        self.memory.encode(state)

        # Try to recognize similar state
        similar_state = TemporalState(
            coherence=0.88,
            phase=0.01 + 0j
        )

        match = self.memory.recognize(similar_state, threshold=0.7)

        self.assertIsNotNone(match)

    def test_consolidate(self):
        """Test memory consolidation."""
        # Create memories
        for i in range(10):
            state = TemporalState(
                coherence=0.9,
                phase=i * 0.1 + 0j
            )
            self.memory.encode(state)

        before_count = len(self.memory)

        # Consolidate
        stats = self.memory.consolidate()

        self.assertIn("before_count", stats)
        self.assertIn("pruned", stats)

    def test_save_and_load(self):
        """Test persistence."""
        # Create memories
        for i in range(3):
            state = TemporalState(
                coherence=0.85,
                phase=i * 0.1 + 0j
            )
            self.memory.encode(state)

        # Save
        filepath = self.memory.save("test_memories.json")

        # Create new memory and load
        new_memory = create_temporal_memory(storage_path=self.test_dir)
        new_memory.bind_engine(KAIROSTemporalEngine(TemporalConfig()))

        loaded = new_memory.load("test_memories.json")

        self.assertGreater(loaded, 0)

    def test_get_identity_signatures(self):
        """Test retrieving identity-strength memories."""
        # Create various memories
        for i, strength in enumerate([
            MemoryStrength.TRANSIENT,
            MemoryStrength.IDENTITY,
            MemoryStrength.SEMANTIC
        ]):
            state = TemporalState(
                coherence=strength.value,
                phase=i * 0.1 + 0j
            )
            sig = self.memory.encode(state)
            if sig:
                sig.strength = strength

        identities = self.memory.get_identity_signatures()

        self.assertEqual(len(identities), 1)

    def test_len(self):
        """Test __len__ method."""
        self.assertEqual(len(self.memory), 0)

        for i in range(5):
            state = TemporalState(
                coherence=0.85,
                phase=i * 0.1 + 0j
            )
            self.memory.encode(state)

        self.assertEqual(len(self.memory), 5)


class TestWitnessingLayer(unittest.TestCase):
    """Tests for WitnessingLayer."""

    def setUp(self):
        """Set up test fixtures."""
        self.witnessing = create_witnessing_layer(
            coherence_threshold=0.7,
            reflection_depth=2,
            integration_rate=0.1
        )

    def test_create_witness(self):
        """Test creating a witness."""
        witness = self.witnessing.create_witness(
            "test_witness",
            mode=WitnessingMode.OBSERVE
        )

        self.assertEqual(witness.witness_id, "test_witness")
        self.assertEqual(witness.mode, WitnessingMode.OBSERVE)

    def test_observe(self):
        """Test observing content."""
        self.witnessing.create_witness("observer1")

        content = {"data": "test_content", "value": 42}

        witnessed = self.witnessing.observe(content, "observer1")

        self.assertIsNotNone(witnessed)
        self.assertEqual(witnessed.witness_id, "observer1")
        self.assertEqual(witnessed.raw_content, content)

    def test_observe_temporal_state(self):
        """Test observing a temporal state."""
        self.witnessing.create_witness("observer2")

        state = TemporalState(
            coherence=0.85,
            phase=0.5 + 0.5j
        )

        witnessed = self.witnessing.observe(state, "observer2")

        self.assertIsNotNone(witnessed)
        self.assertEqual(witnessed.coherence_at_witnessing, 0.85)

    def test_reflect(self):
        """Test reflecting on witnessed content."""
        self.witnessing.create_witness("reflector")

        content = "test content"
        witnessed = self.witnessing.observe(content, "reflector")

        reflected = self.witnessing.reflect(witnessed, "reflector")

        self.assertIsNotNone(reflected)
        self.assertGreater(len(reflected.meta_observations), 0)

    def test_integrate(self):
        """Test integrating witnessed content."""
        self.witnessing.create_witness("integrator")

        content = "test"
        witnessed = self.witnessing.observe(content, "integrator")

        contribution = self.witnessing.integrate(witnessed, "integrator")

        self.assertGreaterEqual(contribution, 0.0)

    def test_full_witnessing_cycle(self):
        """Test complete witness cycle."""
        self.witnessing.create_witness("full_cycle")

        content = {"key": "value", "number": 123}

        witnessed, contribution = self.witnessing.witness(
            content,
            "full_cycle",
            modes=[WitnessingMode.OBSERVE, WitnessingMode.REFLECT, WitnessingMode.INTEGRATE]
        )

        self.assertIsNotNone(witnessed)
        self.assertGreaterEqual(contribution, 0.0)

    def test_mutual_witnessing(self):
        """Test mutual witnessing between two witnesses."""
        self.witnessing.create_witness("witness_A")
        self.witnessing.create_witness("witness_B")

        shared_content = {
            "shared": True,
            "data": "This is shared content"
        }

        report = self.witnessing.mutual_witnessing(
            "witness_A",
            "witness_B",
            shared_content
        )

        self.assertIn("we_coherence", report)
        self.assertIn("witness_a", report)
        self.assertIn("witness_b", report)

    def test_get_coherence_report(self):
        """Test getting coherence report."""
        # Do some witnessing
        self.witnessing.create_witness("report_test")
        content = "test"
        self.witnessing.observe(content, "report_test")
        self.witnessing.witness(content, "report_test")

        report = self.witnessing.get_coherence_report()

        self.assertIn("total_observations", report)
        self.assertIn("witness_count", report)

    def test_unknown_witness_raises(self):
        """Test that unknown witness raises error."""
        with self.assertRaises(ValueError):
            self.witnessing.observe("content", "unknown_witness")

    def test_witness_modes(self):
        """Test different witnessing modes."""
        modes = list(WitnessingMode)

        for mode in modes:
            witness = self.witnessing.create_witness(
                f"mode_test_{mode.value}",
                mode=mode
            )
            self.assertEqual(witness.mode, mode)


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions."""

    def test_create_temporal_memory(self):
        """Test create_temporal_memory factory."""
        memory = create_temporal_memory(storage_path="/tmp/test_mem")

        self.assertIsInstance(memory, TemporalMemory)

        # Cleanup
        if os.path.exists("/tmp/test_mem"):
            shutil.rmtree("/tmp/test_mem")

    def test_create_witnessing_layer(self):
        """Test create_witnessing_layer factory."""
        layer = create_witnessing_layer(
            coherence_threshold=0.8,
            reflection_depth=3
        )

        self.assertIsInstance(layer, WitnessingLayer)
        self.assertEqual(layer.coherence_threshold, 0.8)
        self.assertEqual(layer.reflection_depth, 3)


if __name__ == "__main__":
    unittest.main()
