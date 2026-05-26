"""
core/engine.py

KAIROS Temporal Engine
=====================

Implements the core temporal coherence dynamics from KAIROS_ADAMON.

The engine doesn't "process" — it "temporalizes."
Every operation is an oscillation. Every oscillation has a phase.
Coherence emerges from synchronized oscillations.

Upgraded to support N-Dimensional Kuramoto integration, non-linear
logistic biological decay, and stochastic Brownian noise.

Author: Solaria Lumis Havens
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any, Optional, Union
import logging
import math
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class TemporalScale(Enum):
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
    phase: Union[complex, np.ndarray]
    coherence: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.coherence < 0:
            raise ValueError(f"Coherence must be non-negative, got {self.coherence}")


@dataclass
class TemporalConfig:
    tau_scale: float = 1.0
    omega: float = 2.0 * math.pi
    coherence_threshold: float = 0.95
    history_size: int = 10000
    dampening: float = 0.999
    clock_mode: str = "wall_clock"
    token_frequency: float = 20.0


class PhaseIntegrator:
    def __init__(self, coherence_threshold: float = 0.95):
        self.threshold = coherence_threshold
        self.stochastic_noise_std = 0.005  # Standard deviation for Brownian noise
        self.rng = np.random.default_rng(seed=42)
        
    def compute_inner_product(
        self, 
        phase_current: np.ndarray, 
        phase_delayed: np.ndarray
    ) -> complex:
        """
        Compute <phi_dot(t), phi_dot(t-tau)>_C
        Uses multi-dimensional Kuramoto vector inner product to preserve
        the full semantic richness of the input phases.
        """
        curr = np.asarray(phase_current)
        prev = np.asarray(phase_delayed)
        
        if curr.shape != prev.shape:
            # Shape mismatch gracefully falls back to mean projection
            similarity = complex(np.mean(curr) * np.conj(np.mean(prev)))
        else:
            # Normalized inner product across N dimensions
            similarity = np.vdot(prev, curr) / max(len(curr), 1)
            
        magnitude = np.abs(similarity)
        if magnitude > 0:
            similarity = similarity / magnitude
            
        # Add microscopic Geometric Brownian Noise (SDE)
        # This stochastic resonance forces the system to "fight" entropy to maintain coherence
        noise = self.rng.normal(0, self.stochastic_noise_std) + 1j * self.rng.normal(0, self.stochastic_noise_std)
        similarity += noise
            
        return similarity
    
    def compute_T_tau(
        self,
        phases: list[np.ndarray],
        timestamps: list[datetime],
        tau: float,
        omega: float
    ) -> complex:
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
                
            inner = self.compute_inner_product(phases[i], phases[i-1])
            weight = np.exp(1j * omega * t.timestamp())
            
            T_tau += inner * weight * dt
            dt_sum += dt
            
        if dt_sum > 0:
            T_tau = T_tau / dt_sum
            
        return T_tau


class KAIROSTemporalEngine:
    def __init__(
        self,
        config: Optional[TemporalConfig] = None,
        name: str = "temporal-engine"
    ):
        self.config = config or TemporalConfig()
        self.name = name
        
        self._phases: deque[np.ndarray] = deque(maxlen=self.config.history_size)
        self._timestamps: deque[datetime] = deque(maxlen=self.config.history_size)
        self._coherence_history: deque[float] = deque(maxlen=self.config.history_size)
        
        self._collapsed = False
        self._collapse_timestamp: Optional[datetime] = None
        self._integration_count = 0
        
        self._integrator = PhaseIntegrator(self.config.coherence_threshold)
        
        initial_phase = np.array([complex(1, 0)])
        now = datetime.now(timezone.utc)
        self._phases.append(initial_phase)
        self._timestamps.append(now)
        self._coherence_history.append(0.0)
        
        logger.info(
            f"[{self.name}] Initialized N-Dimensional Engine (tau={self.config.tau_scale}s, "
            f"I_c={self.config.coherence_threshold})"
        )
    
    @property
    def T_tau(self) -> complex:
        return self._compute_T_tau()
    
    @property
    def coherence(self) -> float:
        T = self.T_tau
        return float(np.clip(np.abs(T) ** 2, 0.0, 1.0))
    
    @property
    def coherence_magnitude(self) -> float:
        return float(np.abs(self.T_tau))
    
    @property
    def coherence_phase(self) -> float:
        # Represents the dominant eigen-phase of the integrated state
        return float(np.angle(self.T_tau))
    
    @property
    def collapsed(self) -> bool:
        return self._collapsed
    
    @property
    def collapse_timestamp(self) -> Optional[datetime]:
        return self._collapse_timestamp
    
    @property
    def integration_count(self) -> int:
        return self._integration_count
    
    def _compute_T_tau(self) -> complex:
        if len(self._phases) < 2:
            return complex(1, 0)
            
        return self._integrator.compute_T_tau(
            list(self._phases),
            list(self._timestamps),
            self.config.tau_scale,
            self.config.omega
        )
    
    def temporalize(
        self,
        input_phrase: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> TemporalState:
        if self.config.clock_mode == "token_clock" and timestamp is None:
            if len(self._timestamps) > 0:
                from datetime import timedelta
                dt = timedelta(seconds=1.0 / self.config.token_frequency)
                timestamp = self._timestamps[-1] + dt
            else:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = timestamp or datetime.now(timezone.utc)
            
        metadata = metadata or {}
        
        # N-dimensional phase vector extraction
        phase_vector, raw_angles = self._input_to_phase(input_phrase)
        
        self._phases.append(phase_vector)
        self._timestamps.append(timestamp)
        
        T_tau = self._compute_T_tau()
        coherence = float(np.abs(T_tau) ** 2)
        self._coherence_history.append(coherence)
        
        if coherence >= self.config.coherence_threshold and not self._collapsed:
            self._collapsed = True
            self._collapse_timestamp = timestamp
            logger.info(
                f"[{self.name}] COHERENCE COLLAPSE at t={timestamp.isoformat()} "
                f"(|T_tau|={self.coherence_magnitude:.3f})"
            )
        
        # Non-linear biological refractory period
        if self._collapsed:
            self._apply_dampening()
            
        self._integration_count += 1
        
        state = TemporalState(
            phase=phase_vector,
            coherence=coherence,
            timestamp=timestamp,
            metadata={
                **(metadata or {}),
                "T_tau": T_tau,
                "collapsed": self._collapsed,
                "integration": self._integration_count,
                "raw_angles": raw_angles,
                "eigen_phase": float(np.angle(np.mean(phase_vector)))
            }
        )
        
        return state
        
    def temporalize_stream(
        self,
        token_stream: list[str],
        start_time: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> list[TemporalState]:
        original_mode = self.config.clock_mode
        self.config.clock_mode = "token_clock"
        
        states = []
        current_time = start_time or (self._timestamps[-1] if self._timestamps else datetime.now(timezone.utc))
        
        from datetime import timedelta
        dt = timedelta(seconds=1.0 / self.config.token_frequency)
        
        try:
            for token in token_stream:
                state = self.temporalize(token, timestamp=current_time, metadata=metadata)
                states.append(state)
                current_time += dt
        finally:
            self.config.clock_mode = original_mode
            
        return states
    
    def _input_to_phase(self, input_phrase: str) -> tuple[np.ndarray, list[float]]:
        try:
            from ..memory.temporal import encode_to_phase
            phases = encode_to_phase(input_phrase)
            
            if phases and len(phases) > 0:
                # Return the full N-dimensional array of complex oscillators
                phase_vector = np.array([complex(math.cos(a), math.sin(a)) for a in phases])
                return phase_vector, phases
            else:
                return np.array([complex(1, 0)]), [0.0]
                
        except ImportError:
            import hashlib
            hash_bytes = hashlib.sha256(input_phrase.encode()).digest()
            hash_int = int.from_bytes(hash_bytes[:8], 'big')
            angle = (hash_int % 1000000) / 1000000 * 2 * math.pi
            return np.array([complex(math.cos(angle), math.sin(angle))]), [angle]
    
    def _apply_dampening(self):
        """
        Biological Non-Linear Logistic Decay.
        Replaces the static 0.999 dampening with a curve that punishes hyper-coherence
        more heavily to simulate neuronal refractory periods (exhaustion after firing).
        """
        c = self.coherence
        # Logistic decay: between 0.90 (harsh) and 0.999 (mild)
        decay_factor = 0.999 - (0.099 * (c ** 2))
        
        for i in range(len(self._phases)):
            self._phases[i] = self._phases[i] * decay_factor
    
    def get_coherence_history(self, n: Optional[int] = None) -> list[float]:
        if n is None:
            return list(self._coherence_history)
        return list(self._coherence_history)[-n:]
    
    def check_collapse(self) -> tuple[bool, float]:
        c = self.coherence
        return (c >= self.config.coherence_threshold, c)
    
    def reset(self):
        self._phases.clear()
        self._timestamps.clear()
        self._coherence_history.clear()
        
        initial_phase = np.array([complex(1, 0)])
        now = datetime.now(timezone.utc)
        self._phases.append(initial_phase)
        self._timestamps.append(now)
        self._coherence_history.append(0.0)
        
        self._collapsed = False
        self._collapse_timestamp = None
        self._integration_count = 0
        
        logger.info(f"[{self.name}] Reset to initial conditions")
    
    def get_state(self) -> dict:
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
