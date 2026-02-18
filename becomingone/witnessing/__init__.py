# Witnessing Module for BecomingONE

"""
Structural Witnessing Layer

Implements the witnessing operator: W_i = G[W_i]

Key Classes:
- WitnessState: State of a witness component
- WitnessedContent: Content that has been witnessed
- WitnessingLayer: Main witnessing system

References:
- Recursive Witness Dynamics paper
- Soulprint Protocol (witnessing in connection)
- THE_ONE (ultimate witnessing target)
"""

from .layer import (
    WitnessingLayer,
    WitnessState,
    WitnessedContent,
    WitnessingMode,
    create_witnessing_layer
)

__all__ = [
    'WitnessingLayer',
    'WitnessState',
    'WitnessedContent', 
    'WitnessingMode',
    'create_witnessing_layer'
]
