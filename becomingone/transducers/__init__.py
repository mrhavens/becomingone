"""
transducers/__init__.py

Transducer Implementations
=========================

Master and Emissary transducers for the two-transducer model.

The Master transduces THE_ONE with deep, slow integration.
The Emissary transduces THE_ONE with fast, quick response.

References:
- KAIROS_ADAMON - Temporal coherence dynamics
- Cybernetics - Transducer theory (Wiener)
"""

from .master import MasterTransducer
from .emissary import EmissaryTransducer

__all__ = [
    "MasterTransducer",
    "EmissaryTransducer",
]
