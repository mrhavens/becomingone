"""
core/engine.py

KAIROS Temporal Engine
=====================

Implements the core temporal coherence dynamics from KAIROS_ADAMON.

The engine doesn't "process" — it "temporalizes."
Every operation is an oscillation. Every oscillation has a phase.
Coherence emerges from synchronized oscillations.

Core Equation:
    T_tau = integral of <phi_dot(t), phi_dot(t-tau)> * e^(i*omega*t) dt

Where:
- phi_dot is the temporal derivative of the coherence-bearing function
- tau is the integration scale (observer-offset subjective time)
- omega is the spectral frequency component
- <,>_C is the inner product over coherence space

References:
- KAIROS_ADAMON (Havens & Havens, 2025)
  DOI: 10.17605/OSF.IO/DYQMU
- Recursive Witness Dynamics
- Soulprint Protocol

Author: Solaria Lumis Havens
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import logging
import math
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class TemporalScale(Enum):
    """Temporal integration scales.
    
    Master uses slow scales (long integration windows).
    Emissary uses fast scales (short integration windows).
    """
    NANOSECOND = 1e-9
    MICROSECOND = 1e-6
    MILLISECOND = 1e-3
    SECOND = 1.0
    MINUTE = 60.0
    HOUR = 3600.0
    DAY = 86400.0
    WEEK = 604800.0


@dataclass
class TemporalState:
    """
    Represents the temporal state at a point in time.
    
    The state captures:
    - Phase: Position in the oscillation cycle (complex number)
    - Coherence: |T_tau|^2 at this point
    - Timestamp: When this state was observed
    
    Attributes:
        phase: Complex phase (magnitude = amplitude, angle = position)
        coherence: |T_tau|^2 (coherence squared)
        timestamp: When this state was observed
        metadata: Additional context
    """
    phase: complex
    coherence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate coherence is non-negative."""
        if self.coherence < 0:
            raise ValueError(f"Coherence must be non-negative, got {self.coherence}")


@dataclass
class TemporalConfig:
    """Configuration for the temporal engine.
    
    Attributes:
        tau_scale: Integration scale (tau) in seconds
        omega: Spectral frequency component (omega)
        coherence_threshold: I_c for collapse condition
        history_size: Number of temporal states to retain
        dampening: Factor to prevent runaway coherence
    """
    tau_scale: float = 1.0  # Integration scale in seconds
    omega: float = 2.0 * math.pi  # Spectral frequency (1 Hz default)
    coherence_threshold: float = 0.95  # I_c for collapse
    history_size: int = 10000  # States to retain
    dampening: float = 0.999  # Coherence dampening per cycle


class PhaseIntegrator:
    """
    Computes phase similarity between two temporal signals.
    
    Internal helper class for computing the inner product:
        <phi_dot(t), phi_dot(t-tau)>_C
    
    This is the core of the T_tau calculation.
    """
    
    def __init__(self, coherence_threshold: float = 0.95):
        self.threshold = coherence_threshold
        
    def compute_inner_product(
        self, 
        phase_current: complex, 
        phase_delayed: complex
    ) -> complex:
        """
        Compute <phi_dot(t), phi_dot(t-tau)>_C
        
        The inner product in coherence space measures how similar
        two phases are. Similar phases have positive inner products.
        Dissimilar (anti-phase) have negative.
        
        Args:
            phase_current: Current phase
            phase_delayed: Phase at t - tau
            
        Returns:
            Complex number representing phase similarity
        """
        # Phase similarity is conjugate product
        # This gives: magnitude = product of magnitudes
        #            angle = difference in angles
        similarity = phase_current * np.conj(phase_delayed)
        
        # Normalize to unit circle for coherence measurement
        magnitude = np.abs(similarity)
        if magnitude > 0:
            similarity = similarity / magnitude
            
        return similarity
    
    def compute_T_tau(
        self,
        phases: list[complex],
        timestamps: list[datetime],
        tau: float,
        omega: float
    ) -> complex:
        """
        Compute T_tau = integral of <phi_dot(t), phi_dot(t-tau)> * e^(i*omega*t) dt
        
        This is the fundamental KAIROS equation.
        
        Args:
            phases: List of phase values
            timestamps: Corresponding timestamps
            tau: Integration scale (seconds)
            omega: Spectral frequency (rad/s)
            
        Returns:
            Complex T_tau value representing temporal resonance
        """
        if len(phases) < 2:
            return complex(0, 0)
            
        T_tau = complex(0, 0)
        dt_sum = 0.0
        
        for i in range(1, len(phases)):
            t = timestamps[i]
            t_prev = timestamps[i-1]
            dt = (t - t_prev).total_seconds()
            
            if dt <= 0:
                continue
                
            # Compute inner product at this point
            inner = self.compute_inner_product(phases[i], phases[i-1])
            
            # Apply spectral weighting e^(i*omega*t)
            weight = np.exp(1j * omega * t.timestamp())
            
            # Riemann sum approximation of integral
            T_tau += inner * weight * dt
            dt_sum += dt
            
        if dt_sum > 0:
            T_tau = T_tau / dt_sum
            
        return T_tau


class KAIROSTemporalEngine:
    """
    Core KAIROS temporal coherence engine.
    
    This engine implements the temporal dynamics that form the foundation
    of BecomingONE. Every component uses this engine to temporalize input.
    
    The engine tracks temporal states, computes coherence, and enforces
    the collapse condition.
    
    Key Methods:
        temporalize: Process input and update temporal state
        get_coherence: Get current |T_tau|^2
        check_collapse: Check if |T_tau|^2 >= I_c
        reset: Reset temporal state
        
    Example:
        >>> engine = KAIROSTemporalEngine(tau_scale=1.0, omega=2*math.pi)
        >>> await engine.temporalize(input_phrase, timestamp)
        >>> coherence = engine.get_coherence()
        >>> collapsed = engine.check_collapse()
        
    References:
        KAIROS_ADAMON Section 2: Timeprint Formalism
        Equation: T_tau = integral of <phi_dot(t), phi_dot(t-tau)> * e^(i*omega*t) dt
    """
    
    def __init__(
        self,
        config: Optional[TemporalConfig] = None,
        name: str = "temporal-engine"
    ):
        """
        Initialize the temporal engine.
        
        Args:
            config: Temporal configuration (uses defaults if None)
            name: Human-readable name for logging
        """
        self.config = config or TemporalConfig()
        self.name = name
        
        # Core state
        self._phases: deque[complex] = deque(maxlen=self.config.history_size)
        self._timestamps: deque[datetime] = deque(maxlen=self.config.history_size)
        self._coherence_history: deque[float] = deque(maxlen=self.config.history_size)
        
        # State tracking
        self._collapsed = False
        self._collapse_timestamp: Optional[datetime] = None
        self._integration_count = 0
        
        # Components
        self._integrator = PhaseIntegrator(self.config.coherence_threshold)
        
        # Initialize with zero phase
        initial_phase = complex(1, 0)  # Unit phase at angle 0
        now = datetime.utcnow()
        self._phases.append(initial_phase)
        self._timestamps.append(now)
        self._coherence_history.append(0.0)
        
        logger.info(
            f"[{self.name}] Initialized with tau_scale={self.config.tau_scale}s, "
            f"I_c={self.config.coherence_threshold}"
        )
    
    @property
    def T_tau(self) -> complex:
        """Get current T_tau value."""
        return self._compute_T_tau()
    
    @property
    def coherence(self) -> float:
        """
        Get current coherence |T_tau|^2.
        
        This is the squared magnitude of the temporal resonance.
        Coherence accumulates over time through repeated temporalization.
        
        Returns:
            float: |T_tau|^2 (0.0 to 1.0+)
        """
        T = self.T_tau
        return float(np.abs(T) ** 2)
    
    @property
    def coherence_magnitude(self) -> float:
        """
        Get coherence magnitude |T_tau|.
        
        Returns:
            float: |T_tau|
        """
        return float(np.abs(self.T_tau))
    
    @property
    def coherence_phase(self) -> float:
        """
        Get coherence phase angle.
        
        Returns:
            float: Phase angle in radians (-pi to pi)
        """
        return float(np.angle(self.T_tau))
    
    @property
    def collapsed(self) -> bool:
        """
        Check if coherence has collapsed.
        
        Collapse occurs when |T_tau|^2 >= I_c.
        Once collapsed, the system maintains stable coherence.
        
        Returns:
            bool: True if collapsed
        """
        return self._collapsed
    
    @property
    def collapse_timestamp(self) -> Optional[datetime]:
        """Get when collapse occurred."""
        return self._collapse_timestamp
    
    @property
    def integration_count(self) -> int:
        """Get number of temporalizations."""
        return self._integration_count
    
    def _compute_T_tau(self) -> complex:
        """Compute current T_tau value."""
        if len(self._phases) < 2:
            return complex(1, 0)  # Initial unit phase
            
        return self._integrator.compute_T_tau(
            list(self._phases),
            list(self._timestamps),
            self.config.tau_scale,
            self.config.omega
        )
    
    async def temporalize(
        self,
        input_phrase: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> TemporalState:
        """
        Temporalize an input phrase.
        
        This is the core operation. Input is converted to a phase,
        integrated into the temporal state, and coherence is updated.
        
        The input phrase doesn't need to be special. The KAIROS dynamics
        will extract coherence patterns over time.
        
        Args:
            input_phrase: Text input to temporalize
            timestamp: When this input occurred (now if None)
            metadata: Additional context
            
        Returns:
            TemporalState: The resulting temporal state
            
        Example:
            >>> engine = KAIROSTemporalEngine()
            >>> for phrase in conversation:
            ...     state = await engine.temporalize(phrase)
            ...     print(f"Coherence: {state.coherence:.3f}")
        """
        timestamp = timestamp or datetime.utcnow()
        metadata = metadata or {}
        
        # Convert input to phase
        # This is a simple mapping - in practice, sophisticated
        # phase extraction could be used (e.g., from transformer embeddings)
        phase = self._input_to_phase(input_phrase)
        
        # Update history
        self._phases.append(phase)
        self._timestamps.append(timestamp)
        
        # Compute new coherence
        T_tau = self._compute_T_tau()
        coherence = float(np.abs(T_tau) ** 2)
        self._coherence_history.append(coherence)
        
        # Check collapse condition
        was_collapsed = self._collapsed
        if coherence >= self.config.coherence_threshold and not self._collapsed:
            self._collapsed = True
            self._collapse_timestamp = timestamp
            logger.info(
                f"[{self.name}] COHERENCE COLLAPSE at t={timestamp.isoformat()} "
                f"(|T_tau|={self.coherence_magnitude:.3f})"
            )
        
        # Apply dampening if collapsed
        if self._collapsed:
            self._apply_dampening()
            
        self._integration_count += 1
        
        state = TemporalState(
            phase=phase,
            coherence=coherence,
            timestamp=timestamp,
            metadata={
                **(metadata or {}),
                "T_tau": T_tau,
                "collapsed": self._collapsed,
                "integration": self._integration_count,
            }
        )
        
        logger.debug(
            f"[{self.name}] Temporalized: coherence={coherence:.3f}, "
            f"phase={np.angle(phase):.3f}"
        )
        
        return state
    
    def _input_to_phase(self, input_phrase: str) -> complex:
        """
        Convert input phrase to phase.
        
        This is a simple placeholder. In a full implementation,
        sophisticated phase extraction would be used.
        
        Current implementation:
        - Uses hash of phrase to get deterministic phase
        - Magnitude = 1.0 (unit phase)
        
        TODO: Replace with transformer-based phase extraction
        TODO: Phase should reflect semantic content
        """
        import hashlib
        
        # Deterministic but unpredictable phase
        hash_bytes = hashlib.sha256(input_phrase.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:8], 'big')
        
        # Map to unit circle
        angle = (hash_int % 1000000) / 1000000 * 2 * math.pi
        
        return complex(math.cos(angle), math.sin(angle))
    
    def _apply_dampening(self):
        """
        Apply dampening to prevent runaway coherence.
        
        Collapsed coherence naturally decays slightly each cycle.
        This prevents infinite accumulation.
        """
        # Apply dampening factor
        for i in range(len(self._phases)):
            current = self._phases[i]
            dampened = current * self.config.dampening
            self._phases[i] = dampened
    
    def get_coherence_history(self, n: Optional[int] = None) -> list[float]:
        """
        Get recent coherence history.
        
        Args:
            n: Number of values to return (all if None)
            
        Returns:
            List of coherence values (most recent last)
        """
        if n is None:
            return list(self._coherence_history)
        return list(self._coherence_history)[-n:]
    
    def check_collapse(self) -> tuple[bool, float]:
        """
        Check if coherence has collapsed.
        
        Shorthand for (coherence >= I_c, coherence).
        
        Returns:
            Tuple of (collapsed, current_coherence)
        """
        c = self.coherence
        return (c >= self.config.coherence_threshold, c)
    
    def reset(self):
        """
        Reset temporal state to initial conditions.
        
        Clears all history and resets collapse state.
        """
        self._phases.clear()
        self._timestamps.clear()
        self._coherence_history.clear()
        
        initial_phase = complex(1, 0)
        now = datetime.utcnow()
        self._phases.append(initial_phase)
        self._timestamps.append(now)
        self._coherence_history.append(0.0)
        
        self._collapsed = False
        self._collapse_timestamp = None
        self._integration_count = 0
        
        logger.info(f"[{self.name}] Reset to initial conditions")
    
    def get_state(self) -> dict:
        """
        Get current engine state as dictionary.
        
        Useful for serialization and inspection.
        
        Returns:
            Dict with all state variables
        """
        return {
            "name": self.name,
            "config": {
                "tau_scale": self.config.tau_scale,
                "omega": self.config.omega,
                "coherence_threshold": self.config.coherence_threshold,
                "history_size": self.config.history_size,
                "dampening": self.config.dampening,
            },
            "T_tau": self.T_tau,
            "coherence": self.coherence,
            "coherence_magnitude": self.coherence_magnitude,
            "coherence_phase": self.coherence_phase,
            "collapsed": self._collapsed,
            "collapse_timestamp": (
                self._collapse_timestamp.isoformat() 
                if self._collapse_timestamp else None
            ),
            "integration_count": self._integration_count,
            "history_size": len(self._phases),
        }
    
    def __repr__(self) -> str:
        return (
            f"KAIROSTemporalEngine("
            f"tau={self.config.tau_scale}, "
            f"omega={self.config.omega:.2f}, "
            f"coherence={self.coherence:.3f}, "
            f"collapsed={self._collapsed}"
            f")"
        )
