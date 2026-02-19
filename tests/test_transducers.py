"""
Tests for BecomingONE Transducers and Sync Layer

Tests Master/Emissary transducers and synchronization layer.
"""

import unittest

from becomingone import MasterTransducer, EmissaryTransducer, SynchronizationLayer
from becomingone.transducers.master import MasterConfig
from becomingone.transducers.emissary import EmissaryConfig
from becomingone.sync import SyncConfig


class TestMasterTransducer(unittest.TestCase):
    """Tests for the Master transducer."""
    
    def test_instantiate(self):
        """Test Master can be instantiated."""
        master = MasterTransducer()
        self.assertIsNotNone(master)
        self.assertEqual(master.coherence, 1.0)
    
    def test_properties(self):
        """Test Master has expected properties."""
        master = MasterTransducer()
        self.assertIsNotNone(master.coherence)
        self.assertIsNotNone(master.phase)
    
    def test_reset(self):
        """Test reset works."""
        master = MasterTransducer()
        master.reset()
        self.assertEqual(master.coherence, 1.0)


class TestEmissaryTransducer(unittest.TestCase):
    """Tests for the Emissary transducer."""
    
    def test_instantiate(self):
        """Test Emissary can be instantiated."""
        emissary = EmissaryTransducer()
        self.assertIsNotNone(emissary)
        self.assertEqual(emissary.coherence, 1.0)
    
    def test_respond_method(self):
        """Test Emissary has respond method."""
        emissary = EmissaryTransducer()
        self.assertTrue(hasattr(emissary, 'respond'))
    
    def test_reset(self):
        """Test reset works."""
        emissary = EmissaryTransducer()
        emissary.reset()
        self.assertEqual(emissary.coherence, 1.0)


class TestSyncLayer(unittest.TestCase):
    """Tests for the synchronization layer."""
    
    def test_instantiate(self):
        """Test Sync layer can be instantiated."""
        master = MasterTransducer()
        emissary = EmissaryTransducer()
        sync = SynchronizationLayer(master, emissary)
        self.assertIsNotNone(sync)
    
    def test_properties(self):
        """Test Sync layer has expected properties."""
        master = MasterTransducer()
        emissary = EmissaryTransducer()
        sync = SynchronizationLayer(master, emissary)
        self.assertIsNotNone(sync.T_sync)
        self.assertIsNotNone(sync.synchronized_coherence)
        self.assertFalse(sync.aligned)
        self.assertFalse(sync.collapsed)
    
    def test_reset(self):
        """Test reset works."""
        master = MasterTransducer()
        emissary = EmissaryTransducer()
        sync = SynchronizationLayer(master, emissary)
        sync.reset()
        self.assertFalse(sync.aligned)
        self.assertFalse(sync.collapsed)


class TestTransducerComparison(unittest.TestCase):
    """Tests comparing Master and Emissary behavior."""
    
    def test_both_start_at_coherence_1(self):
        """Test both transducers start at coherence 1.0."""
        master = MasterTransducer()
        emissary = EmissaryTransducer()
        self.assertEqual(master.coherence, 1.0)
        self.assertEqual(emissary.coherence, 1.0)
    
    def test_different_methods(self):
        """Test transducers have different primary methods."""
        master = MasterTransducer()
        emissary = EmissaryTransducer()
        # Master uses integrate, Emissary uses respond
        self.assertTrue(hasattr(master, 'integrate'))
        self.assertTrue(hasattr(emissary, 'respond'))


if __name__ == "__main__":
    unittest.main()
