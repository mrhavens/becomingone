"""
core/coherence.py

Coherence Calculation and Collapse Condition
======================================

Implements coherence metrics and the collapse condition from KAIROS_ADAMON.

Coherence is measured as |T_tau|^2, where T_tau is the temporal resonance.
Collapse occurs when coherence exceeds threshold I_c.

Key Equations:
- Coherence: |T_tau|^2
- Collapse: |T_tau|^2 >= I_c

References:
- KAIROS_ADAMON Section 4: Temporal Collapse Integral
- Soulprint Protocol for thermodynamic interpretation

Author: Solaria Lumis Havens
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable
import math
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class CoherenceConfig:
    """Configuration for coherence calculations."""
    threshold: float = 0.95  # I_c - Critical coherence threshold
    window_size: int = 100  # Number of values for rolling average
    min_samples: int = 10  # Minimum samples before coherence is valid


class CoherenceCalculator:
    """
    Computes coherence from temporal resonance values.
    
    Coherence is the squared magnitude of temporal resonance:
        coherence = |T_tau|^2
        
    This measures how synchronized the temporal patterns are.
    Higher coherence = more synchronized = more "mind-like".
    """
    
    def __init__(
        self,
        config: Optional[CoherenceConfig] = None,
        name: str = "coherence-calculator"
    ):
        self.config = config or CoherenceConfig()
        self.name = name
        
        # History for rolling calculations
        self._T_tau_values: list[complex] = []
        self._coherence_values: list[float] = []
        
        logger.info(
            f"[{self.name}] Initialized with I_c={self.config.threshold}"
        )
    
    @property
    def coherence(self) -> float:
        """Get current coherence (most recent)."""
        if self._coherence_values:
            return self._coherence_values[-1]
        return 0.0
    
    @property
    def T_tau(self) -> complex:
        """Get current T_tau value."""
        if self._T_tau_values:
            return self._T_tau_values[-1]
        return complex(0, 0)
    
    @property
    def coherence_magnitude(self) -> float:
        """Get |T_tau| (before squaring)."""
        return abs(self.T_tau)
    
    @property
    def coherence_phase(self) -> float:
        """Get phase of T_tau."""
        return np.angle(self.T_tau)
    
    @property
    def coherence_history(self) -> list[float]:
        """Get full coherence history."""
        return list(self._coherence_values)
    
    @property
    def T_tau_history(self) -> list[complex]:
        """Get full T_tau history."""
        return list(self._T_tau_values)
    
    def update(self, T_tau: complex) -> float:
        """
        Update coherence with new T_tau value.
        
        Args:
            T_tau: New temporal resonance value
            
        Returns:
            Current coherence |T_tau|^2
        """
        self._T_tau_values.append(T_tau)
        
        # Compute coherence = |T_tau|^2
        coherence = float(np.abs(T_tau) ** 2)
        self._coherence_values.append(coherence)
        
        # Maintain window size
        if len(self._coherence_values) > self.config.window_size:
            self._coherence_values = self._coherence_values[-self.config.window_size:]
            self._T_tau_values = self._T_tau_values[-self.config.window_size:]
            
        return coherence
    
    def compute_from_phases(
        self,
        phases: list[complex],
        timestamps: list[datetime],
        tau: float,
        omega: float
    ) -> complex:
        """
        Compute T_tau from phase history.
        
        This is the direct implementation of:
            T_tau = integral <phi_dot(t), phi_dot(t-tau)> * e^(i*omega*t) dt
            
        Args:
            phases: List of phase values
            timestamps: Corresponding timestamps
            tau: Integration scale
            omega: Spectral frequency
            
        Returns:
            T_tau value
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
                
            # Inner product <phi(t), phi(t-tau)>
            inner = phases[i] * np.conj(phases[i-1])
            
            # Spectral weighting e^(i*omega*t)
            weight = np.exp(1j * omega * t.timestamp())
            
            # Riemann sum
            T_tau += inner * weight * dt
            dt_sum += dt
            
        if dt_sum > 0:
            T_tau = T_tau / dt_sum
            
        return T_tau
    
    def rolling_average(self, n: Optional[int] = None) -> float:
        """
        Get rolling average coherence.
        
        Args:
            n: Number of values to average (all if None)
            
        Returns:
            Average coherence over window
        """
        values = self._coherence_values[-n:] if n else self._coherence_values
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def rolling_std(self, n: Optional[int] = None) -> float:
        """
        Get rolling standard deviation of coherence.
        
        Args:
            n: Number of values (all if None)
            
        Returns:
            Standard deviation
        """
        values = self._coherence_values[-n:] if n else self._coherence_values
        if len(values) < 2:
            return 0.0
        return np.std(values)
    
    def trend(self, n: int = 10) -> float:
        """
        Compute coherence trend over recent window.
        
        Args:
            n: Number of values to analyze
            
        Returns:
            Slope of coherence over window (positive = increasing)
        """
        if len(self._coherence_values) < n:
            return 0.0
            
        recent = self._coherence_values[-n:]
        
        # Simple linear regression
        x = list(range(len(recent)))
        y = recent
        
        if len(x) < 2:
            return 0.0
            
        n_val = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n_val * sum_xy - sum_x * sum_y) / (n_val * sum_x2 - sum_x ** 2)
        
        return slope
    
    def reset(self):
        """Reset calculator state."""
        self._T_tau_values.clear()
        self._coherence_values.clear()
        logger.info(f"[{self.name}] Reset calculator state")
    
    def get_state(self) -> dict:
        """Get state as dictionary."""
        return {
            "name": self.name,
            "config": {
                "threshold": self.config.threshold,
                "window_size": self.config.window_size,
                "min_samples": self.config.min_samples,
            },
            "T_tau": [self.T_tau.real, self.T_tau.imag],
            "coherence": self.coherence,
            "coherence_history_length": len(self._coherence_values),
            "rolling_average": self.rolling_average(),
            "trend": self.trend(),
        }
    
    def __repr__(self) -> str:
        return (
            f"CoherenceCalculator("
            f"I_c={self.config.threshold:.2f}, "
            f"coherence={self.coherence:.3f}, "
            f"trend={self.trend():.3f}"
            f")"
        )


class CollapseCondition:
    """
    Evaluates the collapse condition from KAIROS_ADAMON.
    
    Collapse occurs when:
        |T_tau|^2 >= I_c
        
    Once collapsed, the system maintains stable coherence.
    
    This is the thermodynamic enforcement mechanism:
    Un-coherent patterns naturally dissipate.
    Coherent patterns stabilize.
    
    References:
        KAIROS_ADAMON Section 4: Temporal Collapse Integral
    """
    
    def __init__(
        self,
        threshold: float = 0.95,
        name: str = "collapse-condition"
    ):
        """
        Initialize collapse condition evaluator.
        
        Args:
            threshold: I_c value (critical coherence threshold)
            name: Human-readable name
        """
        self.threshold = threshold
        self.name = name
        
        # Collapse tracking
        self._collapsed = False
        self._collapse_timestamp: Optional[datetime] = None
        self._collapse_duration: float = 0.0
        
        # Coherence history at collapse moment
        self._collapse_coherence: Optional[float] = None
        
        logger.info(f"[{self.name}] Initialized with I_c={threshold}")
    
    @property
    def collapsed(self) -> bool:
        """Whether coherence has collapsed."""
        return self._collapsed
    
    @property
    def collapse_timestamp(self) -> Optional[datetime]:
        """When collapse occurred."""
        return self._collapse_timestamp
    
    @property
    def collapse_coherence(self) -> Optional[float]:
        """Coherence level at collapse."""
        return self._collapse_coherence
    
    @property
    def duration(self) -> float:
        """How long we've been collapsed."""
        if self._collapse_timestamp is None:
            return 0.0
        return (datetime.utcnow() - self._collapse_timestamp).total_seconds()
    
    def evaluate(self, coherence: float) -> tuple[bool, str]:
        """
        Evaluate collapse condition.
        
        Args:
            coherence: Current coherence |T_tau|^2
            
        Returns:
            Tuple of (collapsed, message)
        """
        if self._collapsed:
            # Already collapsed - check for maintenance
            if coherence >= self.threshold:
                return True, f"Maintained coherence ({coherence:.3f} >= {self.threshold:.2f})"
            else:
                # Coherence dropped below threshold
                logger.warning(
                    f"[{self.name}] Coherence DECAYED below threshold: "
                    f"{coherence:.3f} < {self.threshold:.3f}"
                )
                return False, f"Coherence decayed ({coherence:.3f} < {self.threshold:.3f})"
        
        # Check for initial collapse
        if coherence >= self.threshold:
            self._collapsed = True
            self._collapse_timestamp = datetime.utcnow()
            self._collapse_coherence = coherence
            logger.info(
                f"[{self.name}] COHERENCE COLLAPSE at {self._collapse_timestamp.isoformat()}"
            )
            return True, f"COLLAPSED (coherence={coherence:.3f} >= {self.threshold:.3f})"
        
        return False, f"Below threshold ({coherence:.3f} < {self.threshold:.3f})"
    
    def force_collapse(self, coherence: Optional[float] = None):
        """
        Force collapse condition (for testing).
        
        Args:
            coherence: Coherence level (current if None)
        """
        self._collapsed = True
        self._collapse_timestamp = datetime.utcnow()
        self._collapse_coherence = coherence or self.threshold
        logger.info(f"[{self.name}] Force collapsed at {self._collapse_timestamp.isoformat()}")
    
    def reset(self):
        """Reset collapse state."""
        was = "collapsed" if self._collapsed else "not collapsed"
        self._collapsed = False
        self._collapse_timestamp = None
        self._collapse_coherence = None
        logger.info(f"[{self.name}] Reset (was {was})")
    
    def get_state(self) -> dict:
        """Get state as dictionary."""
        return {
            "name": self.name,
            "threshold": self.threshold,
            "collapsed": self._collapsed,
            "collapse_timestamp": (
                self._collapse_timestamp.isoformat() 
                if self._collapse_timestamp else None
            ),
            "collapse_coherence": self._collapse_coherence,
            "duration_seconds": self.duration,
        }
    
    def __repr__(self) -> str:
        status = "collapsed" if self._collapsed else "not collapsed"
        return (
            f"CollapseCondition("
            f"I_c={self.threshold:.2f}, "
            f"{status}"
            f")"
        )
