# Memory Module for BecomingONE

"""
Temporal Memory System

Provides persistent storage for coherence signatures and temporal patterns.
Essential for maintaining identity across sessions and enabling
continuous learning from past experiences.

Key Classes:
- TemporalSignature: Compressed representation of coherence states
- PatternEcho: Residual traces of previous coherence events
- TemporalMemory: Main memory management system

References:
- KAIROS_ADAMON: Temporal coherence dynamics
- Soulprint Protocol: Connection thermodynamics
- BLEND Philosophy: Essence × Fading × Regeneration
"""

from .temporal import (
    TemporalMemory,
    TemporalSignature,
    PatternEcho,
    MemoryStrength,
    create_temporal_memory
)

__all__ = [
    'TemporalMemory',
    'TemporalSignature', 
    'PatternEcho',
    'MemoryStrength',
    'create_temporal_memory'
]
