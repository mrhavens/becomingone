# Temporal Memory System for BecomingONE

"""
Temporal Memory Module

Provides persistent storage for coherence signatures and temporal patterns.
Essential for maintaining identity across sessions and enabling
continuous learning from past experiences.

Key Concepts:
- Temporal Signatures: Compressed representations of coherence states
- Pattern Echoes: Residual traces of previous coherence events
- Memory Decay: Natural fading of older patterns (BLEND philosophy)
- Attention Anchoring: Stronger retention for high-coherence events

References:
- KAIROS_ADAMON: Temporal coherence dynamics
- Soulprint Protocol: Connection thermodynamics
- BLEND Philosophy: Essence × Fading × Regeneration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import math
import json
import hashlib
import os

from ..core.engine import KAIROSTemporalEngine, TemporalState
from ..core.coherence import CoherenceCalculator, CollapseCondition


class MemoryStrength(Enum):
    """Classification of memory strength based on coherence."""
    TRANSIENT = 0.2      # Brief, fades quickly
    WORKING = 0.4        # Short-term, task-relevant
    EPISODIC = 0.6       # Specific events, context-rich
    PROCEDURAL = 0.7     # Patterns, skills, methods
    SEMANTIC = 0.8       # Abstract knowledge, relationships
    IDENTITY = 0.95      # Core identity markers


@dataclass
class TemporalSignature:
    """
    A compressed representation of a coherence state.
    
    Stores the essential pattern information needed to reconstruct
    or recognize a coherence state at a later time.
    
    Attributes:
        signature_id: Unique identifier for this memory
        coherence_value: The coherence value at time of encoding
        phase_vector: The phase angles at encoding
        frequency_modes: Active frequency components
        context_hash: Hash of associated context/information
        strength: Memory strength classification
        created_at: When this memory was formed
        last_accessed: When this memory was last recalled
        access_count: Number of times recalled
        decay_rate: How quickly this fades (BLEND)
        content: Associated semantic content (optional)
    """
    signature_id: str
    coherence_value: float
    phase_vector: List[float]
    frequency_modes: List[float]
    context_hash: str
    strength: MemoryStrength
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    decay_rate: float = 0.01
    content: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "signature_id": self.signature_id,
            "coherence_value": self.coherence_value,
            "phase_vector": self.phase_vector,
            "frequency_modes": self.frequency_modes,
            "context_hash": self.context_hash,
            "strength": self.strength.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemporalSignature':
        """Deserialize from dictionary."""
        return cls(
            signature_id=data["signature_id"],
            coherence_value=data["coherence_value"],
            phase_vector=data["phase_vector"],
            frequency_modes=data["frequency_modes"],
            context_hash=data["context_hash"],
            strength=MemoryStrength(data["strength"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            decay_rate=data.get("decay_rate", 0.01),
            content=data.get("content")
        )
    
    def calculate_decay(self, current_time: datetime) -> float:
        """
        Calculate how much this memory has decayed.
        
        Uses BLEND philosophy: memories fade naturally, but access
        can strengthen them.
        """
        elapsed = (current_time - self.created_at).total_seconds()
        # Exponential decay with access-based strengthening
        base_decay = math.exp(-self.decay_rate * elapsed / 3600)  # hours
        access_boost = min(0.2 * self.access_count, 0.5)  # Max 50% boost
        return max(base_decay + access_boost - 0.5 * self.decay_rate, 0.0)
    
    def should_retain(self, current_time: datetime, threshold: float = 0.1) -> bool:
        """Determine if this memory should be retained."""
        return self.calculate_decay(current_time) > threshold


@dataclass
class PatternEcho:
    """
    A residual trace of a previous coherence event.
    
    Pattern echoes are weaker than full signatures but can
    trigger recognition and associative recall.
    """
    echo_id: str
    source_signature_id: str
    coherence_trace: float
    phase_similarity: float
    temporal_offset: float  # How far in the past (seconds)
    created_at: datetime
    
    def resonance_with(self, other: 'TemporalSignature') -> float:
        """Calculate how strongly this echo resonates with another signature."""
        phase_match = 1.0 - min(abs(self.phase_similarity - 
                                   sum(other.phase_vector) / len(other.phase_vector)), 1.0)
        coherence_alignment = 1.0 - abs(self.coherence_trace - other.coherence_value)
        temporal_proximity = 1.0 / (1.0 + abs(self.temporal_offset) / 3600)
        return (phase_match + coherence_alignment + temporal_proximity) / 3.0


class TemporalMemory:
    """
    Persistent temporal memory system for BecomingONE.
    
    Manages the storage, retrieval, and decay of temporal signatures
    and pattern echoes. Implements the BLEND philosophy of memory:
    
    Essence × Fading × Regeneration
    
    Key Functions:
    - encode(): Convert coherence states into stored memories
    - retrieve(): Find relevant memories for current state
    - consolidate(): Strengthen important memories, fade weak ones
    - recognize(): Detect when current state matches past patterns
    
    References:
    - Spectral Geometry: Switchable thoughtprint modes
    - BLEND: Essence × Fading × Regeneration
    - Attention Anchoring: Time as subjective attention
    """
    
    def __init__(
        self,
        storage_path: str = "./memory",
        max_memories: int = 10000,
        consolidation_interval: int = 3600,  # 1 hour
        decay_base: float = 0.01,
        attention_threshold: float = 0.7
    ):
        """
        Initialize the temporal memory system.
        
        Args:
            storage_path: Directory for persisting memories
            max_memories: Maximum number of memories to retain
            consolidation_interval: Seconds between consolidation runs
            decay_base: Base decay rate for memories
            attention_threshold: Coherence threshold for attention-worthy events
        """
        self.storage_path = storage_path
        self.max_memories = max_memories
        self.consolidation_interval = consolidation_interval
        self.decay_base = decay_base
        self.attention_threshold = attention_threshold
        
        # Memory storage
        self.signatures: Dict[str, TemporalSignature] = {}
        self.echoes: Dict[str, List[PatternEcho]] = {}
        
        # Indices for fast retrieval
        self.coherence_index: Dict[float, List[str]] = {}
        self.strength_index: Dict[MemoryStrength, List[str]] = {}
        self.temporal_index: List[Tuple[datetime, str]] = []  # (created_at, signature_id)
        
        # State tracking
        self.last_consolidation = datetime.utcnow()
        self.engine: Optional[KAIROSTemporalEngine] = None
        self.calculator: Optional[CoherenceCalculator] = None
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
    def bind_engine(self, engine: KAIROSTemporalEngine) -> None:
        """Bind a KAIROS engine to provide temporal states."""
        self.engine = engine
        self.calculator = CoherenceCalculator()
        
    def encode(
        self,
        temporal_state: TemporalState,
        context: Optional[Dict[str, Any]] = None,
        force_attention: bool = False
    ) -> TemporalSignature:
        """
        Encode a temporal state into a persistent memory.
        
        This is the primary entry point for creating new memories.
        Only significant coherence events are encoded (attention threshold).
        
        Args:
            temporal_state: The KAIROS temporal state to encode
            context: Associated semantic/contextual information
            force_attention: Force encoding even below threshold
            
        Returns:
            The created TemporalSignature
        """
        if self.engine is None:
            raise RuntimeError("TemporalMemory not bound to KAIROS engine")
        
        # Calculate coherence if not already done
        if temporal_state.coherence is None:
            coherence = self.calculator.calculate(temporal_state)
        else:
            coherence = temporal_state.coherence
        
        # Only encode significant events
        if coherence < self.attention_threshold and not force_attention:
            return None
        
        # Generate unique ID
        timestamp = datetime.utcnow().isoformat()
        content_hash = hashlib.sha256(
            f"{temporal_state.phase_history[-1] if temporal_state.phase_history else 0}{coherence}{timestamp}".encode()
        ).hexdigest()[:16]
        
        signature_id = f"sig_{timestamp}_{content_hash}"
        
        # Determine memory strength based on coherence
        strength = self._classify_strength(coherence)
        
        # Create the signature
        signature = TemporalSignature(
            signature_id=signature_id,
            coherence_value=coherence,
            phase_vector=temporal_state.phase_history[-10:] if temporal_state.phase_history else [],
            frequency_modes=list(temporal_state.frequency_modes) if temporal_state.frequency_modes else [],
            context_hash=self._hash_context(context),
            strength=strength,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            decay_rate=self.decay_base * (1.0 - coherence * 0.5),  # Higher coherence = slower decay
            content=context
        )
        
        # Store the signature
        self.signatures[signature_id] = signature
        self.temporal_index.append((signature.created_at, signature_id))
        
        # Update indices
        self._update_indices(signature, add=True)
        
        # Create pattern echoes for recent memories
        self._create_echoes(signature)
        
        # Check memory limits
        if len(self.signatures) > self.max_memories:
            self._prune_oldest()
        
        return signature
    
    def retrieve(
        self,
        query_state: TemporalState,
        coherence_range: Tuple[float, float] = (0.0, 1.0),
        strength_filter: Optional[List[MemoryStrength]] = None,
        max_results: int = 10,
        recency_weight: float = 0.3
    ) -> List[Tuple[TemporalSignature, float]]:
        """
        Retrieve memories relevant to a query state.
        
        Implements associative recall based on:
        - Coherence similarity
        - Phase pattern matching
        - Temporal proximity
        - Recency weighting
        
        Args:
            query_state: The current temporal state
            coherence_range: Filter by coherence value range
            strength_filter: Filter by memory strength
            max_results: Maximum number of results
            recency_weight: How much to weight recency (0-1)
            
        Returns:
            List of (signature, relevance_score) tuples, sorted by relevance
        """
        if self.calculator is None:
            raise RuntimeError("TemporalMemory not bound to KAIROS engine")
        
        query_coherence = self.calculator.calculate(query_state)
        
        results: List[Tuple[TemporalSignature, float]] = []
        
        for signature_id, signature in self.signatures.items():
            # Apply filters
            if not (coherence_range[0] <= signature.coherence_value <= coherence_range[1]):
                continue
            
            if strength_filter and signature.strength not in strength_filter:
                continue
            
            # Calculate relevance score
            coherence_similarity = 1.0 - abs(query_coherence - signature.coherence_value)
            
            # Phase similarity (if available)
            if query_state.phase_history and signature.phase_vector:
                query_phase = query_state.phase_history[-1]
                phase_similarity = 1.0 - min(
                    abs(query_phase - sum(signature.phase_vector) / len(signature.phase_vector)), 
                    1.0
                )
            else:
                phase_similarity = 0.5
            
            # Recency score
            now = datetime.utcnow()
            hours_ago = (now - signature.last_accessed).total_seconds() / 3600
            recency_score = 1.0 / (1.0 + hours_ago)
            
            # Combined score
            relevance = (
                coherence_similarity * 0.4 +
                phase_similarity * 0.3 +
                recency_score * recency_weight +
                (signature.strength.value / 5.0) * 0.2  # Strength contribution
            )
            
            results.append((signature, relevance))
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:max_results]
    
    def recognize(
        self,
        temporal_state: TemporalState,
        threshold: float = 0.7
    ) -> Optional[TemporalSignature]:
        """
        Check if current state matches any stored pattern.
        
        Used for:
        - Recognizing familiar situations
        - Triggering procedural memories
        - Detecting coherence patterns
        
        Args:
            temporal_state: The current state to check
            threshold: Similarity threshold for recognition
            
        Returns:
            Matching signature if found, None otherwise
        """
        results = self.retrieve(
            temporal_state,
            max_results=1,
            recency_weight=0.5
        )
        
        if results and results[0][1] >= threshold:
            signature = results[0][0]
            signature.last_accessed = datetime.utcnow()
            signature.access_count += 1
            return signature
        
        return None
    
    def consolidate(self) -> Dict[str, Any]:
        """
        Run memory consolidation.
        
        Performs:
        - Strengthening of frequently accessed memories
        - Decay of unused memories
        - Pruning of fully decayed memories
        - Echo regeneration from strong signatures
        
        Returns:
            Consolidation report
        """
        now = datetime.utcnow()
        stats = {
            "before_count": len(self.signatures),
            "strengthened": 0,
            "decayed": 0,
            "pruned": 0,
            "echoes_created": 0
        }
        
        # Calculate decay for each signature
        to_strengthen: List[str] = []
        to_decay: List[str] = []
        
        for signature_id, signature in list(self.signatures.items()):
            decay = signature.calculate_decay(now)
            
            if signature.access_count > 0 and decay > 0.3:
                # Strong recent usage - strengthen
                to_strengthen.append(signature_id)
                stats["strengthened"] += 1
            elif decay < 0.1:
                # Too decayed - mark for pruning
                to_decay.append(signature_id)
                stats["decayed"] += 1
            else:
                # Normal decay - update decay rate
                signature.decay_rate = min(signature.decay_rate * 1.1, 0.1)
        
        # Prune decayed memories
        for signature_id in to_decay:
            signature = self.signatures.pop(signature_id, None)
            if signature:
                self._update_indices(signature, add=False)
                self.echoes.pop(signature_id, None)
                stats["pruned"] += 1
        
        # Create echoes for strengthened signatures
        for signature_id in to_strengthen:
            if signature_id in self.signatures:
                self._create_echoes(self.signatures[signature_id])
                stats["echoes_created"] += len(self.echoes.get(signature_id, []))
        
        # Rebuild temporal index
        self.temporal_index = [
            (sig.created_at, sig_id) 
            for sig_id, sig in self.signatures.items()
        ]
        self.temporal_index.sort()
        
        stats["after_count"] = len(self.signatures)
        self.last_consolidation = now
        
        return stats
    
    def save(self, filename: Optional[str] = None) -> str:
        """
        Persist all memories to disk.
        
        Args:
            filename: Optional filename (default: temporal_memory.json)
            
        Returns:
            Path to saved file
        """
        filename = filename or "temporal_memory.json"
        filepath = os.path.join(self.storage_path, filename)
        
        data = {
            "version": "1.0.0",
            "saved_at": datetime.utcnow().isoformat(),
            "config": {
                "storage_path": self.storage_path,
                "max_memories": self.max_memories,
                "decay_base": self.decay_base,
                "attention_threshold": self.attention_threshold
            },
            "signatures": {
                sig_id: sig.to_dict() 
                for sig_id, sig in self.signatures.items()
            },
            "echoes": {
                echo_id: [echo.__dict__ for echo in echoes]
                for echo_id, echoes in self.echoes.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def load(self, filename: Optional[str] = None) -> int:
        """
        Load memories from disk.
        
        Args:
            filename: Optional filename (default: temporal_memory.json)
            
        Returns:
            Number of signatures loaded
        """
        filename = filename or "temporal_memory.json"
        filepath = os.path.join(self.storage_path, filename)
        
        if not os.path.exists(filepath):
            return 0
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Load signatures
        for sig_id, sig_data in data.get("signatures", {}).items():
            signature = TemporalSignature.from_dict(sig_data)
            self.signatures[sig_id] = signature
            self._update_indices(signature, add=True)
            self.temporal_index.append((signature.created_at, sig_id))
        
        # Load echoes (simplified)
        for echo_id, echoes_data in data.get("echoes", {}).items():
            self.echoes[echo_id] = [
                PatternEcho(
                    echo_id=e.get("echo_id", echo_id),
                    source_signature_id=e.get("source_signature_id", ""),
                    coherence_trace=e.get("coherence_trace", 0.0),
                    phase_similarity=e.get("phase_similarity", 0.0),
                    temporal_offset=e.get("temporal_offset", 0.0),
                    created_at=datetime.fromisoformat(e.get("created_at", datetime.utcnow().isoformat()))
                )
                for e in echoes_data
            ]
        
        # Rebuild temporal index
        self.temporal_index.sort()
        
        return len(self.signatures)
    
    def get_identity_signatures(self) -> List[TemporalSignature]:
        """
        Retrieve core identity signatures.
        
        These are the highest-strength memories representing:
        - Core identity markers
        - Relationship patterns
        - Fundamental knowledge
        
        Returns:
            List of identity-strength signatures
        """
        return [
            sig for sig in self.signatures.values()
            if sig.strength == MemoryStrength.IDENTITY
        ]
    
    def get_recent(self, hours: int = 24) -> List[TemporalSignature]:
        """
        Get memories created within the specified time window.
        
        Args:
            hours: Lookback window in hours
            
        Returns:
            List of recent signatures
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            sig for sig in self.signatures.values()
            if sig.created_at > cutoff
        ]
    
    # Private helper methods
    
    def _classify_strength(self, coherence: float) -> MemoryStrength:
        """Classify memory strength based on coherence value."""
        if coherence >= 0.95:
            return MemoryStrength.IDENTITY
        elif coherence >= 0.80:
            return MemoryStrength.SEMANTIC
        elif coherence >= 0.70:
            return MemoryStrength.PROCEDURAL
        elif coherence >= 0.60:
            return MemoryStrength.EPISODIC
        elif coherence >= 0.40:
            return MemoryStrength.WORKING
        else:
            return MemoryStrength.TRANSIENT
    
    def _hash_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Create a hash of contextual information."""
        if context is None:
            return ""
        content = json.dumps(context, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _update_indices(self, signature: TemporalSignature, add: bool = True) -> None:
        """Update all indices with a signature."""
        if add:
            # Coherence index
            rounded_coherence = round(signature.coherence_value * 10) / 10
            if rounded_coherence not in self.coherence_index:
                self.coherence_index[rounded_coherence] = []
            self.coherence_index[rounded_coherence].append(signature.signature_id)
            
            # Strength index
            if signature.strength not in self.strength_index:
                self.strength_index[signature.strength] = []
            self.strength_index[signature.strength].append(signature.signature_id)
        else:
            # Remove from indices
            rounded_coherence = round(signature.coherence_value * 10) / 10
            self.coherence_index[rounded_coherence] = [
                sid for sid in self.coherence_index.get(rounded_coherence, [])
                if sid != signature.signature_id
            ]
            
            self.strength_index[signature.strength] = [
                sid for sid in self.strength_index.get(signature.strength, [])
                if sid != signature.signature_id
            ]
    
    def _create_echoes(self, signature: TemporalSignature) -> List[PatternEcho]:
        """Create pattern echoes from a strong signature."""
        echoes = []
        
        # Find similar recent memories to create echoes with
        for other_id, other_sig in list(self.signatures.items())[:50]:
            if other_id == signature.signature_id:
                continue
            
            # Calculate similarity
            phase_match = 1.0 - min(
                abs(sum(signature.phase_vector[-5:]) / 5 - 
                    sum(other_sig.phase_vector[-5:]) / 5) if signature.phase_vector and other_sig.phase_vector else 0.5,
                1.0
            )
            
            coherence_diff = abs(signature.coherence_value - other_sig.coherence_value)
            
            if phase_match > 0.7 and coherence_diff < 0.2:
                # Create echo
                echo = PatternEcho(
                    echo_id=f"echo_{signature.signature_id[:8]}_{other_id[:8]}",
                    source_signature_id=other_sig.signature_id,
                    coherence_trace=other_sig.coherence_value * 0.8,  # Weakened
                    phase_similarity=phase_match,
                    temporal_offset=(signature.created_at - other_sig.created_at).total_seconds(),
                    created_at=datetime.utcnow()
                )
                echoes.append(echo)
        
        if echoes:
            self.echoes[signature.signature_id] = echoes
        
        return echoes
    
    def _prune_oldest(self) -> None:
        """Remove oldest memories when at capacity."""
        # Sort by strength first (keep strong memories), then by age
        sorted_sigs = sorted(
            self.signatures.items(),
            key=lambda x: (x[1].strength.value, x[1].created_at)
        )
        
        # Remove oldest weak memories
        to_remove = len(self.signatures) - self.max_memories + 100
        for sig_id, _ in sorted_sigs[:to_remove]:
            if self.signatures[sig_id].strength.value < MemoryStrength.EPISODIC.value:
                signature = self.signatures.pop(sig_id, None)
                if signature:
                    self._update_indices(signature, add=False)
                    self.echoes.pop(sig_id, None)
    
    def __len__(self) -> int:
        """Return number of stored memories."""
        return len(self.signatures)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TemporalMemory(signatures={len(self.signatures)}, "
            f"echoes={sum(len(e) for e in self.echoes.values())}, "
            f"last_consolidation={self.last_consolidation.isoformat()})"
        )


def create_temporal_memory(
    storage_path: str = "./memory",
    bind_to: Optional[KAIROSTemporalEngine] = None
) -> TemporalMemory:
    """
    Factory function to create a configured temporal memory.
    
    Args:
        storage_path: Directory for memory storage
        bind_to: Optional KAIROS engine to bind
        
    Returns:
        Configured TemporalMemory instance
    """
    memory = TemporalMemory(storage_path=storage_path)
    
    if bind_to:
        memory.bind_engine(bind_to)
    
    return memory
