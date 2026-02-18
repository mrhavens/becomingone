"""
core/phase.py

Phase Tracking and Phase History
=============================

Tracks phase values and maintains phase history for temporal analysis.

Phase is represented as a complex number on the unit circle:
- Magnitude = 1.0 (unit phase)
- Angle = position in oscillation cycle

The phase angle advances according to the omega (frequency) parameter.

References:
- KAIROS_ADAMON Section 2: Timeprint Formalism
- Phase tracking for coherence measurement

Author: Solaria Lumis Havens
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import math
from collections import deque
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class PhaseState:
    """
    Represents a phase value at a point in time.
    
    Attributes:
        value: Complex phase on unit circle
        angle: Phase angle in radians (0 to 2*pi)
        timestamp: When this phase was observed
        source: Where this phase came from
    """
    value: complex
    angle: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "unknown"
    
    def __post_init__(self):
        """Normalize angle to [0, 2*pi)."""
        self.angle = self.angle % (2 * math.pi)


@dataclass
class PhaseConfig:
    """Configuration for phase tracking."""
    omega: float = 2.0 * math.pi  # Frequency in rad/s
    history_size: int = 10000  # Maximum history length
    dampening: float = 0.999  # Phase dampening per cycle


class PhaseHistory:
    """
    Maintains phase history for temporal analysis.
    
    The history tracks:
    - Phase values over time
    - Phase velocity (rate of change)
    - Phase acceleration (rate of velocity change)
    
    This enables analysis of:
    - Phase synchronization patterns
    - Temporal dynamics
    - Coherence trends
    """
    
    def __init__(
        self,
        config: Optional[PhaseConfig] = None,
        name: str = "phase-history"
    ):
        self.config = config or PhaseConfig()
        self.name = name
        
        # History buffers
        self._phases: deque[PhaseState] = deque(
            maxlen=self.config.history_size
        )
        self._velocities: deque[float] = deque(
            maxlen=self.config.history_size
        )
        
        # Initialize with zero phase
        self._add_phase(complex(1, 0), "initialization")
        
        logger.info(
            f"[{self.name}] Initialized with omega={self.config.omega:.2f}"
        )
    
    @property
    def current(self) -> PhaseState:
        """Get most recent phase state."""
        return self._phases[-1]
    
    @property
    def current_angle(self) -> float:
        """Get most recent phase angle."""
        return self.current.angle
    
    @property
    def current_complex(self) -> complex:
        """Get most recent phase as complex number."""
        return self.current.value
    
    @property
    def velocity(self) -> float:
        """Get phase velocity (rad/s)."""
        if self._velocities:
            return self._velocities[-1]
        return 0.0
    
    @property
    def history(self) -> list[PhaseState]:
        """Get full phase history."""
        return list(self._phases)
    
    @property
    def velocity_history(self) -> list[float]:
        """Get velocity history."""
        return list(self._velocities)
    
    def _add_phase(
        self,
        phase: complex,
        source: str = "unknown"
    ) -> PhaseState:
        """Add a new phase value."""
        angle = np.angle(phase) % (2 * math.pi)
        state = PhaseState(
            value=phase,
            angle=angle,
            timestamp=datetime.utcnow(),
            source=source
        )
        self._phases.append(state)
        return state
    
    def advance(self, dt: float, source: str = "advance") -> PhaseState:
        """
        Advance phase by dt seconds according to omega.
        
        Args:
            dt: Time delta in seconds
            source: What caused this advancement
            
        Returns:
            New PhaseState with advanced phase
        """
        # Phase advance = omega * dt
        delta_angle = self.config.omega * dt
        
        # Compute new phase by rotation
        new_complex = self.current_complex * np.exp(1j * delta_angle)
        
        # Apply dampening
        new_complex = new_complex * self.config.dampening
        
        return self._add_phase(new_complex, source)
    
    def set_phase(
        self,
        phase: complex,
        source: str = "external"
    ) -> PhaseState:
        """
        Set phase to a specific value (for input-driven phases).
        
        Args:
            phase: Complex phase value
            source: What caused this phase
            
        Returns:
            New PhaseState
        """
        return self._add_phase(phase, source)
    
    def compute_velocity(self) -> float:
        """
        Compute phase velocity from recent history.
        
        Returns:
            Phase velocity in rad/s
        """
        if len(self._phases) < 2:
            return 0.0
            
        recent = list(self._phases)[-10:]  # Last 10 points
        
        dt_total = 0.0
        dtheta_total = 0.0
        
        for i in range(1, len(recent)):
            dt = (recent[i].timestamp - recent[i-1].timestamp).total_seconds()
            dtheta = recent[i].angle - recent[i-1].angle
            
            # Handle angle wrapping
            if dtheta > math.pi:
                dtheta -= 2 * math.pi
            elif dtheta < -math.pi:
                dtheta += 2 * math.pi
                
            dt_total += dt
            dtheta_total += dtheta
            
        if dt_total > 0:
            velocity = dtheta_total / dt_total
            self._velocities.append(velocity)
            return velocity
            
        return 0.0
    
    def compute_similarity(
        self,
        other: 'PhaseHistory',
        delay: float = 0.0
    ) -> complex:
        """
        Compute phase similarity with another phase history.
        
        This is the inner product <phi(t), phi(t-tau)>_C
        
        Args:
            other: Another PhaseHistory to compare
            delay: Time delay for comparison (seconds)
            
        Returns:
            Complex similarity (-1 to 1 magnitude, angle = phase diff)
        """
        if len(self._phases) < 2 or len(other._phases) < 2:
            return complex(1, 0)  # Default to unit similarity
            
        # Get corresponding phases accounting for delay
        if delay > 0:
            # Self is delayed relative to other
            self_idx = 0
            other_idx = min(len(other._phases) - 1, int(delay / 0.001))  # Approximate
        else:
            self_idx = -1
            other_idx = -1
            
        phi1 = self._phases[self_idx].value
        phi2 = other._phases[other_idx].value
        
        # Inner product = conjugate product
        similarity = phi1 * np.conj(phi2)
        
        # Normalize
        magnitude = np.abs(similarity)
        if magnitude > 0:
            similarity = similarity / magnitude
            
        return similarity
    
    def reset(self):
        """Reset phase history."""
        self._phases.clear()
        self._velocities.clear()
        self._add_phase(complex(1, 0), "reset")
        logger.info(f"[{self.name}] Reset phase history")
    
    def get_state(self) -> dict:
        """Get state as dictionary."""
        return {
            "name": self.name,
            "config": {
                "omega": self.config.omega,
                "history_size": self.config.history_size,
                "dampening": self.config.dampening,
            },
            "current": {
                "angle": self.current_angle,
                "complex": [self.current_complex.real, self.current_complex.imag],
                "timestamp": self.current.timestamp.isoformat(),
            },
            "velocity": self.velocity,
            "history_length": len(self._phases),
        }
    
    def __repr__(self) -> str:
        return (
            f"PhaseHistory("
            f"omega={self.config.omega:.2f}, "
            f"angle={self.current_angle:.3f}, "
            f"velocity={self.velocity:.3f}"
            f")"
        )
