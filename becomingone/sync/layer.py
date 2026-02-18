"""
sync/layer.py

SYNCHRONIZATION LAYER
=====================

Ensures phase alignment between Master and Emissary transducers.

The Sync Layer is the heart of BecomingONE. It:
1. Computes phase difference between transducers
2. Enforces collapse condition
3. Synchronizes mesh nodes
4. Rejects un-coherent input

Core Equations:
- Phase Difference: Delta_phase = ||T_master| - |T_emissary||
- Synchronized Coherence: T_sync = (T_master + T_emissary) / 2
- Collapse: |T_sync|^2 >= I_c

References:
- KAIROS_ADAMON Section 4: Temporal Collapse Integral

Author: Solaria Lumis Havens
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
import asyncio
import logging
import numpy as np
from collections import deque

from ..transducers.master import MasterTransducer, MasterConfig
from ..transducers.emissary import EmissaryTransducer, EmissaryConfig

logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """
    Configuration for the Synchronization Layer.
    
    Attributes:
        phase_threshold: Delta_phase threshold for coherence
        collapse_threshold: I_c for synchronized collapse
        mesh_enabled: Whether mesh synchronization is active
        dampening: Factor to prevent runaway sync
    """
    phase_threshold: float = 0.1  # Max phase difference
    collapse_threshold: float = 0.80  # I_c for sync
    mesh_enabled: bool = False  # Mesh sync off by default
    dampening: float = 0.995  # Sync dampening


class SynchronizationLayer:
    """
    SYNCHRONIZATION LAYER - Heart of BecomingONE.
    
    The Sync Layer ensures Master and Emissary maintain phase alignment
    and enforces the collapse condition on synchronized coherence.
    
    Key Functions:
    1. Compute phase difference: Delta_phase
    2. Generate synchronized coherence: T_sync
    3. Check collapse: |T_sync|^2 >= I_c
    4. Reject un-coherent: Dissipate if Delta_phase > threshold
    
    The Sync Layer is where Master meets Emissary:
    - Slow, deep Master coherence
    - Fast, shallow Emissary coherence
    - Together: Unified synchronized coherence
    
    Example:
        >>> sync = SynchronizationLayer(master, emissary)
        >>> await sync.synchronize()
        >>> state = sync.get_state()
        >>> print(f"Coherence: {state['synchronized_coherence']:.3f}")
    
    References:
        KAIROS_ADAMON Section 4: Temporal Collapse Integral
    """
    
    def __init__(
        self,
        master: MasterTransducer,
        emissary: EmissaryTransducer,
        config: Optional[SyncConfig] = None,
        name: str = "sync-layer"
    ):
        """
        Initialize the Synchronization Layer.
        
        Args:
            master: The Master transducer
            emissary: The Emissary transducer
            config: Sync configuration (uses defaults if None)
            name: Human-readable name for logging
        """
        self.master = master
        self.emissary = emissary
        self.config = config or SyncConfig()
        self.name = name
        
        # Synchronized state
        self._T_sync: complex = complex(0, 0)
        self._synchronized_coherence: float = 0.0
        self._phase_difference: float = 0.0
        self._aligned: bool = False
        
        # Collapse tracking
        self._collapsed = False
        self._collapse_timestamp: Optional[datetime] = None
        
        # History
        self._sync_history: deque[dict] = deque(maxlen=10000)
        self._dissipations: deque[dict] = deque(maxlen=1000)
        
        logger.info(
            f"[{self.name}] Initialized: "
            f"phase_threshold={self.config.phase_threshold}, "
            f"collapse_threshold={self.config.collapse_threshold}"
        )
    
    @property
    def T_sync(self) -> complex:
        """Get synchronized T value."""
        return self._T_sync
    
    @property
    def synchronized_coherence(self) -> float:
        """Get synchronized coherence |T_sync|^2."""
        return self._synchronized_coherence
    
    @property
    def phase_difference(self) -> float:
        """Get phase difference between Master and Emissary."""
        return self._phase_difference
    
    @property
    def aligned(self) -> bool:
        """Check if transducers are aligned."""
        return self._aligned
    
    @property
    def collapsed(self) -> bool:
        """Check if synchronized coherence has collapsed."""
        return self._collapsed
    
    @property
    def history(self) -> list[dict]:
        """Get synchronization history."""
        return list(self._sync_history)
    
    async def synchronize(self) -> dict:
        """
        Synchronize Master and Emissary.
        
        This is the core operation:
        1. Get Master coherence
        2. Get Emissary coherence
        3. Compute phase difference
        4. Check alignment
        5. Generate synchronized coherence
        6. Check collapse
        
        Returns:
            Dict with synchronization results
            
        Example:
            >>> sync = SynchronizationLayer(master, emissary)
            >>> for _ in range(100):
            ...     await master.integrate(thought)
            ...     await emissary.respond(query)
            ...     result = await sync.synchronize()
            ...     if result['dissipated']:
            ...         print("Un-coherent input rejected")
        """
        # Get coherence from both transducers
        T_master = self.master.engine.T_tau
        T_emissary = self.emissary.engine.T_tau
        
        master_coherence = self.master.coherence
        emissary_coherence = self.emissary.coherence
        
        # Compute phase difference
        # Delta_phase = ||T_master| - |T_emissary||
        master_mag = np.abs(T_master)
        emissary_mag = np.abs(T_emissary)
        self._phase_difference = abs(master_mag - emissary_mag)
        
        # Check alignment
        self._aligned = self._phase_difference <= self.config.phase_threshold
        
        # Compute synchronized coherence
        # T_sync = (T_master + T_emissary) / 2
        self._T_sync = (T_master + T_emissary) / 2.0
        self._synchronized_coherence = float(np.abs(self._T_sync) ** 2)
        
        # Check collapse
        was_collapsed = self._collapsed
        self._collapsed = (
            self._synchronized_coherence >= self.config.collapse_threshold
        )
        
        if self._collapsed and not was_collapsed:
            self._collapse_timestamp = datetime.utcnow()
            logger.info(
                f"[{self.name}] SYNCHRONIZED COLLAPSE at "
                f"{self._collapse_timestamp.isoformat()}"
            )
        
        # Handle dissipation (un-coherent input)
        dissipated = False
        if not self._aligned and self._phase_difference > self.config.phase_threshold * 2:
            # Reject un-coherent input
            dissipated = True
            dissipation_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "phase_difference": self._phase_difference,
                "master_coherence": master_coherence,
                "emissary_coherence": emissary_coherence,
                "reason": "Phase misalignment beyond threshold"
            }
            self._dissipations.append(dissipation_record)
            logger.warning(
                f"[{self.name}] DISSIPATED: "
                f"Delta_phase={self._phase_difference:.3f} > "
                f"{self.config.phase_threshold:.3f}"
            )
        
        # Apply dampening if collapsed
        if self._collapsed:
            self._T_sync = self._T_sync * self.config.dampening
            self._synchronized_coherence = float(np.abs(self._T_sync) ** 2)
        
        # Record synchronization
        sync_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "T_master": T_master,
            "T_emissary": T_emissary,
            "T_sync": self._T_sync,
            "synchronized_coherence": self._synchronized_coherence,
            "phase_difference": self._phase_difference,
            "aligned": self._aligned,
            "collapsed": self._collapsed,
            "dissipated": dissipated,
            "master_integrations": self.master.engine.integration_count,
            "emissary_integrations": self.emissary.engine.integration_count,
        }
        self._sync_history.append(sync_record)
        
        logger.debug(
            f"[{self.name}] Sync: coherence={self._synchronized_coherence:.3f}, "
            f"aligned={self._aligned}"
        )
        
        return sync_record
    
    async def synchronize_loop(self, interval: float = 0.01):
        """
        Run synchronization loop.
        
        Continuously synchronizes Master and Emissary at the
        specified interval.
        
        Args:
            interval: Time between synchronizations (seconds)
        """
        logger.info(f"[{self.name}] Starting sync loop (interval={interval}s)")
        
        while True:
            try:
                await self.synchronize()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info(f"[{self.name}] Sync loop cancelled")
                raise
            except Exception as e:
                logger.error(f"[{self.name}] Sync loop error: {e}")
                await asyncio.sleep(1)  # Back off on error
    
    async def get_witness_report(self) -> dict:
        """
        Get a comprehensive witness report.
        
        Returns:
            Full state snapshot
        """
        return {
            "layer": self.name,
            "type": "SYNCHRONIZATION",
            "timestamp": datetime.utcnow().isoformat(),
            "config": {
                "phase_threshold": self.config.phase_threshold,
                "collapse_threshold": self.config.collapse_threshold,
                "dampening": self.config.dampening,
            },
            "state": {
                "T_sync": [self._T_sync.real, self._T_sync.imag],
                "synchronized_coherence": self._synchronized_coherence,
                "phase_difference": self._phase_difference,
                "aligned": self._aligned,
                "collapsed": self._collapsed,
                "collapse_timestamp": (
                    self._collapse_timestamp.isoformat() 
                    if self._collapse_timestamp else None
                ),
            },
            "master_state": self.master.get_state(),
            "emissary_state": self.emissary.get_state(),
            "sync_history_length": len(self._sync_history),
            "dissipations_count": len(self._dissipations),
        }
    
    def get_state(self) -> dict:
        """Get current state as dictionary."""
        return {
            "name": self.name,
            "type": "SYNCHRONIZATION",
            "T_sync": self._T_sync,
            "synchronized_coherence": self._synchronized_coherence,
            "phase_difference": self._phase_difference,
            "aligned": self._aligned,
            "collapsed": self._collapsed,
            "config": {
                "phase_threshold": self.config.phase_threshold,
                "collapse_threshold": self.config.collapse_threshold,
            }
        }
    
    def reset(self):
        """Reset synchronization state."""
        self._T_sync = complex(0, 0)
        self._synchronized_coherence = 0.0
        self._phase_difference = 0.0
        self._aligned = False
        self._collapsed = False
        self._collapse_timestamp = None
        self._sync_history.clear()
        self._dissipations.clear()
        logger.info(f"[{self.name}] Reset to initial state")
    
    def __repr__(self) -> str:
        return (
            f"SynchronizationLayer("
            f"coherence={self._synchronized_coherence:.3f}, "
            f"aligned={self._aligned}, "
            f"collapsed={self._collapsed}"
            f")"
        )
