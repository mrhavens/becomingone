"""
sync/__init__.py

Synchronization Layer
===================

Synchronization between Master and Emissary transducers.

The Sync Layer ensures phase alignment and enforces coherence
between the two transducers.

References:
- KAIROS_ADAMON Section 4: Temporal Collapse Integral
"""

from .layer import SynchronizationLayer, SyncConfig, create_sync_layer

# Alias for convenience
SyncLayer = SynchronizationLayer

__all__ = [
    "SynchronizationLayer",
    "SyncLayer",
    "SyncConfig",
    "create_sync_layer",
]
