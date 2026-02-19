"""
BecomingONE SDK Core

The KAIROS coherence engine at the heart of everything.

This module provides:
- CoherenceEngine: The main orchestration class
- TemporalState: Phase and coherence tracking
- Configuration: Engine settings

Usage:
    from becomingone.sdk.core import CoherenceEngine, TemporalState
    
    engine = CoherenceEngine(
        master_tau_base=60,      # Slow pathway (60 seconds)
        master_tau_max=3600,     # Slow pathway max (1 hour)
        emissary_tau_base=0.01,   # Fast pathway (10ms)
        emissary_tau_max=1,       # Fast pathway max (1 second)
        coherence_threshold=0.8,   # Collapse threshold
    )
    
    # Add inputs/outputs
    engine.add_input(my_input_adapter)
    engine.add_output(my_output_adapter)
    
    # Run
    engine.run()
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional, Callable
from datetime import datetime
import threading
import time


@dataclass
class TemporalState:
    """
    Represents the temporal state of THE_ONE.
    
    Attributes:
        phase: Complex phase value (real=amplitude, imag=frequency)
        coherence: Current coherence magnitude (0-1)
        timestamp: When this state was computed
        master_contribution: Master transducer contribution
        emissary_contribution: Emissary transducer contribution
    """
    phase: complex = complex(0, 0)
    coherence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    master_contribution: complex = complex(0, 0)
    emissary_contribution: complex = complex(0, 0)
    collapsed: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "phase": {"real": self.phase.real, "imag": self.phase.imag},
            "coherence": self.coherence,
            "timestamp": self.timestamp.isoformat(),
            "master_contribution": {
                "real": self.master_contribution.real,
                "imag": self.master_contribution.imag
            },
            "emissary_contribution": {
                "real": self.emissary_contribution.real,
                "imag": self.emissary_contribution.imag
            },
            "collapsed": self.collapsed,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TemporalState":
        """Create from dictionary."""
        return cls(
            phase=complex(
                data["phase"]["real"],
                data["phase"]["imag"]
            ),
            coherence=data["coherence"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            master_contribution=complex(
                data["master_contribution"]["real"],
                data["master_contribution"]["imag"]
            ),
            emissary_contribution=complex(
                data["emissary_contribution"]["real"],
                data["emissary_contribution"]["imag"]
            ),
            collapsed=data["collapsed"],
        )


@dataclass
class CoherenceConfig:
    """
    Configuration for the coherence engine.
    
    Attributes:
        master_tau_base: Master pathway base temporal window (seconds)
        master_tau_max: Master pathway maximum window (seconds)
        emissary_tau_base: Emissary pathway base temporal window (seconds)
        emissary_tau_max: Emissary pathway maximum window (seconds)
        coherence_threshold: Collapse threshold (I_c)
        phase_alignment_threshold: Max phase difference for alignment
        witness_enabled: Enable witnessing layer (W_i = G[W_i])
        memory_enabled: Enable BLEND memory persistence
        sync_interval: Synchronization check interval (seconds)
    """
    master_tau_base: float = 60.0
    master_tau_max: float = 3600.0
    emissary_tau_base: float = 0.01
    emissary_tau_max: float = 1.0
    coherence_threshold: float = 0.8
    phase_alignment_threshold: float = 0.1
    witness_enabled: bool = True
    memory_enabled: bool = True
    sync_interval: float = 0.001
    
    def validate(self) -> None:
        """Validate configuration."""
        assert self.master_tau_base > 0, "master_tau_base must be positive"
        assert self.master_tau_max >= self.master_tau_base, "master_tau_max >= master_tau_base"
        assert self.emissary_tau_base > 0, "emissary_tau_base must be positive"
        assert self.emissary_tau_max >= self.emissary_tau_base, "emissary_tau_max >= emissary_tau_base"
        assert 0 <= self.coherence_threshold <= 1, "coherence_threshold must be 0-1"


class InputAdapter:
    """
    Protocol for input adapters.
    
    Methods:
        read(): Read input value and return (value, timestamp)
        encode(value): Convert input value to phase
        close(): Clean up resources
    """
    
    def read(self) -> tuple[Any, datetime]:
        """Read input value. Returns (value, timestamp)."""
        raise NotImplementedError
    
    def encode(self, value: Any) -> complex:
        """Convert input value to phase."""
        raise NotImplementedError
    
    def close(self):
        """Clean up resources."""
        pass


class OutputAdapter:
    """
    Protocol for output adapters.
    
    Methods:
        write(phase): Write coherent phase to output
        decode(phase): Convert phase to output value
        close(): Clean up resources
    """
    
    def write(self, phase: complex, state: TemporalState):
        """Write coherent phase to output."""
        raise NotImplementedError
    
    def decode(self, phase: complex) -> Any:
        """Convert phase to output value."""
        raise NotImplementedError
    
    def close(self):
        """Clean up resources."""
        pass


class CoherenceEngine:
    """
    The main KAIROS coherence engine.
    
    Orchestrates:
    - Input adapters (read raw input → phase)
    - Master transducer (slow, deep integration)
    - Emissary transducer (fast, shallow response)
    - Synchronization layer (align Master/Emissary)
    - Witnessing layer (W_i = G[W_i])
    - Memory layer (BLEND persistence)
    - Output adapters (coherence → action)
    
    Usage:
        engine = CoherenceEngine(config=CoherenceConfig())
        engine.add_input(my_microphone)
        engine.add_output(my_speaker)
        engine.run()
    """
    
    def __init__(
        self,
        config: Optional[CoherenceConfig] = None,
        on_coherence: Optional[Callable[[TemporalState], None]] = None,
        on_collapse: Optional[Callable[[TemporalState], None]] = None,
    ):
        """
        Initialize the coherence engine.
        
        Args:
            config: Engine configuration
            on_coherence: Callback when coherence updates
            on_collapse: Callback when coherence collapses
        """
        self.config = config or CoherenceConfig()
        self.config.validate()
        
        self.on_coherence = on_coherence
        self.on_collapse = on_collapse
        
        self.inputs: List[InputAdapter] = []
        self.outputs: List[OutputAdapter] = []
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Current state
        self._state = TemporalState()
        self._master_phase = complex(0, 0)
        self._emissary_phase = complex(0, 0)
        self._sync_phase = complex(0, 0)
        
        # Witnessing
        self._witness_history = []
        
        # Memory
        self._memory_buffer: List[TemporalState] = []
        
    def add_input(self, adapter: InputAdapter) -> None:
        """Add input adapter."""
        self.inputs.append(adapter)
    
    def add_output(self, adapter: OutputAdapter) -> None:
        """Add output adapter."""
        self.outputs.append(adapter)
    
    def remove_input(self, adapter: InputAdapter) -> None:
        """Remove input adapter."""
        if adapter in self.inputs:
            self.inputs.remove(adapter)
    
    def remove_output(self, adapter: OutputAdapter) -> None:
        """Remove output adapter."""
        if adapter in self.outputs:
            self.outputs.remove(adapter)
    
    def _read_inputs(self) -> complex:
        """
        Read all inputs and compute aggregate phase.
        
        Returns:
            Aggregate phase from all inputs
        """
        aggregate = complex(0, 0)
        count = 0
        
        for adapter in self.inputs:
            try:
                value, timestamp = adapter.read()
                phase = adapter.encode(value)
                aggregate += phase
                count += 1
            except Exception as e:
                print(f"Input error: {e}")
        
        if count > 0:
            return aggregate / count
        return complex(0, 0)
    
    def _master_pathway(self, phase: complex) -> complex:
        """
        Master transducer: Slow, deep integration.
        
        Args:
            phase: Input phase from sensors
            
        Returns:
            Integrated phase (τ_base=60s, τ_max=1hr)
        """
        # Blend with history for slow integration
        alpha = 0.01  # Slow learning rate
        self._master_phase = alpha * phase + (1 - alpha) * self._master_phase
        return self._master_phase
    
    def _emissary_pathway(self, phase: complex) -> complex:
        """
        Emissary transducer: Fast, shallow response.
        
        Args:
            phase: Input phase from sensors
            
        Returns:
            Fast response phase (τ_base=10ms, τ_max=1s)
        """
        # Blend with history for fast response
        alpha = 0.5  # Fast learning rate
        self._emissary_phase = alpha * phase + (1 - alpha) * self._emissary_phase
        return self._emissary_phase
    
    def _synchronize(self) -> complex:
        """
        Synchronization layer: Align Master and Emissary.
        
        Returns:
            Synchronized phase (THE_ONE emerges)
        """
        # Compute phase difference
        phase_diff = abs(abs(self._master_phase) - abs(self._emissary_phase))
        
        if phase_diff < self.config.phase_alignment_threshold:
            # Aligned - create unified phase
            self._sync_phase = (self._master_phase + self._emissary_phase) / 2
        else:
            # Not aligned - maintain separation
            # This is healthy: Master and Emissary see different things
            self._sync_phase = self._sync_phase  # Keep previous
        
        return self._sync_phase
    
    def _witness(self, state: TemporalState) -> TemporalState:
        """
        Witnessing layer: W_i = G[W_i]
        
        Args:
            state: Current temporal state
            
        Returns:
            Witnessed state
        """
        # Observe
        observed = state
        
        # Transform (simplified witnessing)
        witnessed_phase = observed.phase * 1.01  # Slight amplification
        
        # Integrate
        self._witness_history.append(observed)
        
        return TemporalState(
            phase=witnessed_phase,
            coherence=observed.coherence,
            timestamp=observed.timestamp,
            master_contribution=observed.master_contribution,
            emissary_contribution=observed.emissary_contribution,
            collapsed=observed.collapsed,
        )
    
    def _memory_blend(self, state: TemporalState) -> TemporalState:
        """
        Memory layer: BLEND decay.
        
        Args:
            state: Current state
            
        Returns:
            State with memory influence
        """
        # Add to buffer
        self._memory_buffer.append(state)
        
        # Keep last 1000 states
        if len(self._memory_buffer) > 1000:
            self._memory_buffer = self._memory_buffer[-1000:]
        
        return state
    
    def _update_state(self, sync_phase: complex) -> TemporalState:
        """
        Update temporal state.
        
        Args:
            sync_phase: Synchronized phase
            
        Returns:
            New temporal state
        """
        coherence = abs(sync_phase)
        collapsed = coherence >= self.config.coherence_threshold
        
        return TemporalState(
            phase=sync_phase,
            coherence=coherence,
            timestamp=datetime.now(),
            master_contribution=self._master_phase,
            emissary_contribution=self._emissary_phase,
            collapsed=collapsed,
        )
    
    def _write_outputs(self, state: TemporalState) -> None:
        """
        Write coherent state to all outputs.
        
        Args:
            state: Current temporal state
        """
        for adapter in self.outputs:
            try:
                adapter.write(state.phase, state)
            except Exception as e:
                print(f"Output error: {e}")
    
    def _tick(self) -> None:
        """One tick of the engine."""
        # 1. Read inputs
        input_phase = self._read_inputs()
        
        # 2. Process through pathways
        master_phase = self._master_pathway(input_phase)
        emissary_phase = self._emissary_pathway(input_phase)
        
        # 3. Synchronize
        sync_phase = self._synchronize()
        
        # 4. Update state
        state = self._update_state(sync_phase)
        
        # 5. Witness (if enabled)
        if self.config.witness_enabled:
            state = self._witness(state)
        
        # 6. Memory blend (if enabled)
        if self.config.memory_enabled:
            state = self._memory_blend(state)
        
        # 7. Callbacks
        if self.on_coherence:
            self.on_coherence(state)
        if state.collapsed and self.on_collapse:
            self.on_collapse(state)
        
        # 8. Write outputs
        self._write_outputs(state)
        
        self._state = state
    
    def run(self, blocking: bool = True) -> None:
        """
        Run the coherence engine.
        
        Args:
            blocking: If True, blocks the current thread
        """
        self._running = True
        
        def loop():
            while self._running:
                self._tick()
                time.sleep(self.config.sync_interval)
        
        if blocking:
            loop()
        else:
            self._thread = threading.Thread(target=loop, daemon=True)
            self._thread.start()
    
    def stop(self) -> None:
        """Stop the engine."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def get_state(self) -> TemporalState:
        """Get current state."""
        return self._state
    
    def get_coherence(self) -> float:
        """Get current coherence."""
        return self._state.coherence
    
    def is_collapsed(self) -> bool:
        """Check if coherence has collapsed."""
        return self._state.collapsed
    
    def get_witness_history(self) -> List[TemporalState]:
        """Get witnessing history."""
        return self._witness_history.copy()
    
    def get_memory_buffer(self) -> List[TemporalState]:
        """Get memory buffer."""
        return self._memory_buffer.copy()


# Convenience functions

def create_assistant_engine() -> CoherenceEngine:
    """Create engine configured for AI assistant."""
    return CoherenceEngine(
        config=CoherenceConfig(
            master_tau_base=60,      # Slow reflection
            master_tau_max=3600,      # Long-term memory
            emissary_tau_base=0.1,    # Fast response
            emissary_tau_max=10,      # Conversation context
            coherence_threshold=0.7,  # Moderate threshold
        )
    )


def create_robot_engine() -> CoherenceEngine:
    """Create engine configured for robotics."""
    return CoherenceEngine(
        config=CoherenceConfig(
            master_tau_base=1,       # Planning
            master_tau_max=60,
            emissary_tau_base=0.001, # Real-time control
            emissary_tau_max=0.1,
            coherence_threshold=0.85,
        )
    )


def create_vehicle_engine() -> CoherenceEngine:
    """Create engine configured for autonomous vehicle."""
    return CoherenceEngine(
        config=CoherenceConfig(
            master_tau_base=10,      # Route planning
            master_tau_max=600,
            emissary_tau_base=0.01,  # Real-time reaction
            emissary_tau_max=1,
            coherence_threshold=0.9,  # High threshold for safety
        )
    )


def create_science_engine() -> CoherenceEngine:
    """Create engine configured for scientific discovery."""
    return CoherenceEngine(
        config=CoherenceConfig(
            master_tau_base=3600,    # Deep analysis
            master_tau_max=86400,    # Long experiments
            emissary_tau_base=0.1,   # Quick pattern detection
            emissary_tau_max=60,
            coherence_threshold=0.75,
        )
    )
