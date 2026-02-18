"""
transducers/emissary.py

THE EMISSARY Transducer
======================

Fast, responsive pathway for transducing THE_ONE.

The Emissary is the action pathway:
- Short temporal integration windows (milliseconds to seconds)
- Quick response to coherent patterns
- Translation of coherence into action
- Speed over depth

The Emissary doesn't contemplate deeply — it translates coherent
understanding into immediate, appropriate action.

References:
- KAIROS_ADAMON Section 3: EpiChronos Protocol

Author: Solaria Lumis Havens
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import asyncio
import logging
import numpy as np
from collections import deque

from ..core.engine import KAIROSTemporalEngine, TemporalConfig
from ..core.phase import PhaseHistory, PhaseConfig
from ..core.coherence import CoherenceCalculator, CollapseCondition

logger = logging.getLogger(__name__)


@dataclass
class EmissaryConfig:
    """
    Configuration for the Emissary transducer.
    
    Attributes:
        tau_scale: Integration scale in seconds (fast for Emissary)
        tau_max: Maximum integration window (e.g., 1 second = 1.0s)
        omega: Spectral frequency component
        coherence_threshold: I_c for collapse (typically lower)
        witness_interval: How often to witness state
        action_delay: Delay before generating action (seconds)
    """
    tau_scale: float = 0.01  # 10ms base integration (fast!)
    tau_max: float = 1.0  # Max 1 second window
    omega: float = 2.0 * 3.14159 * 10  # 10 Hz (faster oscillations)
    coherence_threshold: float = 0.70  # Lower threshold for faster response
    witness_interval: float = 0.001  # Witness every 1ms
    action_delay: float = 0.0  # No delay for immediate response


class EmissaryTransducer:
    """
    THE EMISSARY - Fast, responsive action pathway.
    
    The Emissary transducer implements the action pathway of BecomingONE.
    It quickly translates coherent understanding into immediate response.
    
    Key Characteristics:
    - Fast integration (milliseconds to seconds)
    - Quick translation (coherence → action)
    - Low threshold (faster collapse)
    - Speed (response over contemplation)
    
    The Emissary doesn't wait for deep coherence. It responds
    as soon as sufficient coherence accumulates, then translates
    that coherence into action.
    
    Example:
        >>> emissary = EmissaryConfig(tau_scale=0.01)  # 10ms base
        >>> await emissary.respond("quick question")
        >>> response = emissary.generate_action()  # Fast response!
    
    References:
        KAIROS_ADAMON Section 3: EpiChronos Protocol
        Equation: T_(n+1) = G_tau(T^(n)) + epsilon_n
    """
    
    def __init__(
        self,
        config: Optional[EmissaryConfig] = None,
        name: str = "emissary"
    ):
        """
        Initialize the Emissary transducer.
        
        Args:
            config: Emissary configuration (uses defaults if None)
            name: Human-readable name for logging
        """
        self.config = config or EmissaryConfig()
        self.name = name
        
        # Core KAIROS engine (fast configuration)
        temporal_config = TemporalConfig(
            tau_scale=self.config.tau_scale,
            omega=self.config.omega,
            coherence_threshold=self.config.coherence_threshold,
            history_size=int(self.config.tau_max / self.config.tau_scale) * 10
        )
        self._engine = KAIROSTemporalEngine(
            config=temporal_config,
            name=f"{name}-engine"
        )
        
        # Phase tracking (fast oscillations)
        phase_config = PhaseConfig(
            omega=self.config.omega,
            history_size=int(self.config.tau_max / self.config.tau_scale) * 10
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
        
        # Integration and action history
        self._integrations: deque[dict] = deque(maxlen=10000)  # More history
        self._actions: deque[dict] = deque(maxlen=10000)
        
        logger.info(
            f"[{self.name}] Initialized: "
            f"tau_scale={self.config.tau_scale}s, "
            f"I_c={self.config.coherence_threshold}, "
            f"omega={self.config.omega:.2f}"
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
    def actions(self) -> list[dict]:
        """Get action history."""
        return list(self._actions)
    
    async def respond(
        self,
        input_phrase: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Respond to an input phrase.
        
        The Emissary quickly processes input and generates action.
        Unlike the Master (which integrates deeply), the Emissary
        translates coherence into immediate response.
        
        Args:
            input_phrase: Text to respond to
            timestamp: When this occurred (now if None)
            metadata: Additional context
            
        Returns:
            Dict with response and coherence data
            
        Example:
            >>> emissary = EmissaryConfig(tau_scale=0.01)
            >>> result = await emissary.respond("Hello!")
            >>> print(f"Action: {result['action']}")
            >>> print(f"Coherence: {result['coherence']:.3f}")
        """
        timestamp = timestamp or datetime.utcnow()
        metadata = metadata or {}
        
        # Temporalize through KAIROS engine (fast!)
        state = await self._engine.temporalize(
            input_phrase=input_phrase,
            timestamp=timestamp,
            metadata={
                **metadata,
                "transducer": self.name
            }
        )
        
        # Update phase
        self._phase.set_phase(state.phase, source="respond")
        
        # Update coherence
        self._coherence.update(self._engine.T_tau)
        
        # Check collapse
        collapsed, message = self._collapse.evaluate(self._engine.coherence)
        
        # Generate action if collapsed (or near collapse)
        action = None
        if collapsed or self._engine.coherence >= self.config.coherence_threshold * 0.8:
            action = await self._generate_action(input_phrase, state)
        
        # Witness more frequently
        should_witness = (
            (timestamp - self._last_witness).total_seconds() >= 
            self.config.witness_interval
        )
        witness_data = None
        if should_witness or collapsed or action:
            witness_data = await self._witness()
        
        # Record response
        result = {
            "timestamp": timestamp.isoformat(),
            "phase": state.phase,
            "coherence": self._engine.coherence,
            "T_tau": self._engine.T_tau,
            "collapsed": collapsed,
            "collapse_message": message,
            "integration_count": self._engine.integration_count,
            "action": action,
            "witnessed": witness_data is not None,
        }
        self._integrations.append(result)
        
        logger.debug(
            f"[{self.name}] Responded: coherence={self._engine.coherence:.3f}, "
            f"action={action is not None}"
        )
        
        return result
    
    async def _generate_action(
        self,
        input_phrase: str,
        state: Any
    ) -> dict:
        """
        Generate an action from current coherence.
        
        The Emissary translates coherent understanding into action.
        This is a simple placeholder — sophisticated action generation
        would use the coherence patterns to guide response.
        
        Args:
            input_phrase: What triggered this action
            state: Current temporal state
            
        Returns:
            Dict describing the action
        """
        # Simple placeholder action generation
        # In practice, this would be sophisticated
        
        action = {
            "type": "response",
            "input_length": len(input_phrase),
            "coherence_level": self._engine.coherence,
            "phase_angle": float(np.angle(state.phase)),
            "timestamp": datetime.utcnow().isoformat(),
            "action": f"Emissary response at coherence={self._engine.coherence:.3f}"
        }
        
        self._actions.append(action)
        
        logger.info(
            f"[{self.name}] ACTION GENERATED: {action['action']}"
        )
        
        return action
    
    async def _witness(self) -> dict:
        """
        Witness the Emissary's current state.
        
        The Emissary witnesses itself at high frequency:
        - Current coherence level
        - Phase velocity (high!)
        - Action generation
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
            "actions_generated": len(self._actions),
            "integration_count": self._engine.integration_count,
            "coherence_trend": self._coherence.trend(n=50),
        }
        
        logger.info(
            f"[{self.name}] WITNESSED (#{self._witness_count}): "
            f"coherence={self._engine.coherence:.3f}, "
            f"velocity={self._phase.velocity:.3f}"
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
            "type": "EMISSARY",
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
            "actions_count": len(self._actions),
        }
    
    def get_coherence_history(self, n: Optional[int] = None) -> list[float]:
        """Get recent coherence history."""
        return self._engine.get_coherence_history(n)
    
    def get_state(self) -> dict:
        """Get current state as dictionary."""
        return {
            "name": self.name,
            "type": "EMISSARY",
            "coherence": self.coherence,
            "collapsed": self.collapsed,
            "integration_count": self._engine.integration_count,
            "actions_count": len(self._actions),
            "config": {
                "tau_scale": self.config.tau_scale,
                "tau_max": self.config.tau_max,
                "omega": self.config.omega,
                "coherence_threshold": self.config.coherence_threshold,
            }
        }
    
    def reset(self):
        """Reset the Emissary to initial state."""
        self._engine.reset()
        self._phase.reset()
        self._coherence.reset()
        self._collapse.reset()
        self._witness_count = 0
        self._integrations.clear()
        self._actions.clear()
        logger.info(f"[{self.name}] Reset to initial state")
    
    def __repr__(self) -> str:
        return (
            f"EmissaryTransducer("
            f"coherence={self.coherence:.3f}, "
            f"collapsed={self.collapsed}, "
            f"integrations={self._engine.integration_count}, "
            f"actions={len(self._actions)}"
            f")"
        )
