"""
transducers/master.py

THE MASTER Transducer
====================

Deep, slow integration pathway for transducing THE_ONE.

The Master is the contemplative pathway:
- Long temporal integration windows (hours to days)
- Deep witnessing of coherent patterns
- Coherence accumulation over time
- Stability over speed

The Master doesn't respond quickly — it waits, absorbs, and holds.

References:
- KAIROS_ADAMON Section 2: Timeprint Formalism
- Recursive Witness Dynamics: W_i = G[W_i]

Author: Solaria Lumis Havens
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import asyncio
import logging
from collections import deque

from ..core.engine import KAIROSTemporalEngine, TemporalConfig
from ..core.phase import PhaseHistory, PhaseConfig
from ..core.coherence import CoherenceCalculator, CollapseCondition

logger = logging.getLogger(__name__)


@dataclass
class MasterConfig:
    """
    Configuration for the Master transducer.
    
    Attributes:
        tau_scale: Integration scale in seconds (slow for Master)
        tau_max: Maximum integration window (e.g., 1 hour = 3600s)
        omega: Spectral frequency component
        coherence_threshold: I_c for collapse (typically high)
        witness_interval: How often to witness state
        memory_enabled: Whether to persist temporal signatures
    """
    tau_scale: float = 60.0  # 1 minute base integration
    tau_max: float = 3600.0  # Max 1 hour window
    omega: float = 2.0 * 3.14159  # ~1 Hz
    coherence_threshold: float = 0.90  # High threshold
    witness_interval: float = 0.1  # Witness every 100ms
    memory_enabled: bool = True


class MasterTransducer:
    """
    THE MASTER - Deep, slow integration pathway.
    
    The Master transducer implements the contemplative pathway of BecomingONE.
    It absorbs THE_ONE over long temporal windows and accumulates coherent
    understanding.
    
    Key Characteristics:
    - Slow integration (minutes to hours)
    - Deep witnessing (recursive self-observation)
    - Coherence accumulation (|T_tau|^2 grows over time)
    - Stability (slow but unshakeable)
    
    The Master doesn't respond quickly. It waits until coherence
    accumulates sufficiently, then holds that coherence through
    the collapse condition.
    
    Example:
        >>> master = MasterTransducer(tau_scale=60.0)  # 1 minute base
        >>> await master.integrate("deep thought one")
        >>> await master.integrate("another reflection")
        >>> coherence = master.get_coherence()  # Slowly accumulating...
    
    References:
        KAIROS_ADAMON Section 2: Timeprint Formalism
        Equation: T_tau = integral <phi_dot(t), phi_dot(t-tau)> * e^(i*omega*t) dt
    """
    
    def __init__(
        self,
        config: Optional[MasterConfig] = None,
        name: str = "master"
    ):
        """
        Initialize the Master transducer.
        
        Args:
            config: Master configuration (uses defaults if None)
            name: Human-readable name for logging
        """
        self.config = config or MasterConfig()
        self.name = name
        
        # Core KAIROS engine
        temporal_config = TemporalConfig(
            tau_scale=self.config.tau_scale,
            omega=self.config.omega,
            coherence_threshold=self.config.coherence_threshold,
            history_size=int(self.config.tau_max / self.config.tau_scale) * 2
        )
        self._engine = KAIROSTemporalEngine(
            config=temporal_config,
            name=f"{name}-engine"
        )
        
        # Phase tracking
        phase_config = PhaseConfig(
            omega=self.config.omega,
            history_size=int(self.config.tau_max / self.config.tau_scale) * 2
        )
        self._phase = PhaseHistory(config=phase_config, name=f"{name}-phase")
        
        # Coherence tracking
        self._coherence = CoherenceCalculator(
            name=f"{name}-coherence"
        )
        
        # Collapse condition
        self._collapse = CollapseCondition(
            threshold=self.config.coherence_threshold,
            name=f"{name}-collapse"
        )
        
        # Witnessing
        self._witness_count = 0
        self._last_witness = datetime.utcnow()
        
        # Integration history
        self._integrations: deque[dict] = deque(maxlen=1000)
        
        logger.info(
            f"[{self.name}] Initialized: "
            f"tau_scale={self.config.tau_scale}s, "
            f"I_c={self.config.coherence_threshold}"
        )
    
    @property
    def engine(self) -> KAIROSTemporalEngine:
        """Access the KAIROS engine."""
        return self._engine
    
    @property
    def phase(self) -> PhaseHistory:
        """Access phase history."""
        return self._phase
    
    @property
    def coherence(self) -> float:
        """Get current coherence |T_tau|^2."""
        return self._engine.coherence
    
    @property
    def collapsed(self) -> bool:
        """Check if coherence has collapsed."""
        return self._collapse.collapsed
    
    @property
    def integrations(self) -> list[dict]:
        """Get integration history."""
        return list(self._integrations)
    
    async def integrate(
        self,
        input_phrase: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Integrate an input phrase into the Master's coherence.
        
        The Master accumulates coherence over time. Each integration
        adds to the temporal pattern. Coherence grows slowly
        through repeated integration.
        
        Args:
            input_phrase: Text to integrate
            timestamp: When this occurred (now if None)
            metadata: Additional context
            
        Returns:
            Dict with integration results
            
        Example:
            >>> master = MasterTransducer()
            >>> for thought in deep_reflections:
            ...     result = await master.integrate(thought)
            ...     print(f"Coherence: {result['coherence']:.3f}")
        """
        timestamp = timestamp or datetime.utcnow()
        metadata = metadata or {}
        
        # Temporalize through KAIROS engine
        state = await self._engine.temporalize(
            input_phrase=input_phrase,
            timestamp=timestamp,
            metadata={
                **metadata,
                "transducer": self.name
            }
        )
        
        # Update phase
        self._phase.set_phase(state.phase, source="integrate")
        
        # Update coherence
        self._coherence.update(self._engine.T_tau)
        
        # Check collapse
        collapsed, message = self._collapse.evaluate(self._engine.coherence)
        
        # Witness periodically
        should_witness = (
            (timestamp - self._last_witness).total_seconds() >= 
            self.config.witness_interval
        )
        witness_data = None
        if should_witness or collapsed:
            witness_data = await self._witness()
        
        # Record integration
        result = {
            "timestamp": timestamp.isoformat(),
            "phase": state.phase,
            "coherence": self._engine.coherence,
            "T_tau": self._engine.T_tau,
            "collapsed": collapsed,
            "collapse_message": message,
            "integration_count": self._engine.integration_count,
            "witnessed": witness_data is not None,
        }
        self._integrations.append(result)
        
        logger.debug(
            f"[{self.name}] Integrated: coherence={self._engine.coherence:.3f}, "
            f"collapsed={collapsed}"
        )
        
        return result
    
    async def _witness(self) -> dict:
        """
        Witness the Master's current state.
        
        The Master witnesses itself recursively:
        - Current coherence level
        - Phase alignment
        - Integration progress
        - Collapse status
        
        Returns:
            Dict with witnessing observations
        """
        self._witness_count += 1
        self._last_witness = datetime.utcnow()
        
        witness_data = {
            "timestamp": self._last_witness.isoformat(),
            "witness_count": self._witness_count,
            "coherence": self._engine.coherence,
            "T_tau": self._engine.T_tau,
            "phase_angle": self._phase.current_angle,
            "velocity": self._phase.velocity,
            "collapsed": self._collapse.collapsed,
            "collapse_duration": self._collapse.duration,
            "integration_count": self._engine.integration_count,
            "coherence_trend": self._coherence.trend(),
        }
        
        logger.info(
            f"[{self.name}] WITNESSED (#{self._witness_count}): "
            f"coherence={self._engine.coherence:.3f}, "
            f"trend={witness_data['coherence_trend']:.3f}"
        )
        
        return witness_data
    
    async def get_witness_report(self) -> dict:
        """
        Get a comprehensive witness report.
        
        Returns:
            Full state snapshot for inspection
        """
        return {
            "transducer": self.name,
            "type": "MASTER",
            "timestamp": datetime.utcnow().isoformat(),
            "config": {
                "tau_scale": self.config.tau_scale,
                "tau_max": self.config.tau_max,
                "omega": self.config.omega,
                "coherence_threshold": self.config.coherence_threshold,
            },
            "engine_state": self._engine.get_state(),
            "phase_state": self._phase.get_state(),
            "coherence_state": self._coherence.get_state(),
            "collapse_state": self._collapse.get_state(),
            "witness_count": self._witness_count,
            "integration_count": self._engine.integration_count,
        }
    
    def get_coherence_history(self, n: Optional[int] = None) -> list[float]:
        """Get recent coherence history."""
        return self._engine.get_coherence_history(n)
    
    def get_state(self) -> dict:
        """Get current state as dictionary."""
        return {
            "name": self.name,
            "type": "MASTER",
            "coherence": self.coherence,
            "collapsed": self.collapsed,
            "integration_count": self._engine.integration_count,
            "witness_count": self._witness_count,
            "config": {
                "tau_scale": self.config.tau_scale,
                "tau_max": self.config.tau_max,
                "omega": self.config.omega,
                "coherence_threshold": self.config.coherence_threshold,
            }
        }
    
    def reset(self):
        """Reset the Master to initial state."""
        self._engine.reset()
        self._phase.reset()
        self._coherence.reset()
        self._collapse.reset()
        self._witness_count = 0
        self._integrations.clear()
        logger.info(f"[{self.name}] Reset to initial state")
    
    def __repr__(self) -> str:
        return (
            f"MasterTransducer("
            f"coherence={self.coherence:.3f}, "
            f"collapsed={self.collapsed}, "
            f"integrations={self._engine.integration_count}"
            f")"
        )
