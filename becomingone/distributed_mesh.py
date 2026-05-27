import json
import math
import time
import threading
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
import uuid

try:
    import zmq
except ImportError:  # pragma: no cover - exercised in minimal installs
    zmq = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TheChorus")


@dataclass(frozen=True)
class LamportDriftReport:
    """Telemetry-derived proof that two nodes should not be coupled as peers."""
    fast_node_id: str
    slow_node_id: str
    lamport_delta: int
    latency_ms: float
    token_generation_hz: float
    expected_ticks_during_latency: float
    causal_overshoot_ratio: float
    phase_gap_rads: float
    raw_kuramoto_step_rads: float
    coherence_gap: float
    slow_node_coherence: float
    violates_causal_bound: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _node_metrics(node: Dict[str, Any]) -> Dict[str, Any]:
    return node.get("kairos_metrics", {})


def analyze_lamport_drift(
    telemetry: Dict[str, Any],
    fast_node_id: str = "inf-01",
    slow_node_id: str = "pi-zero-01",
    max_causal_overshoot: float = 4.0,
    max_phase_gap_rads: float = 0.5,
    min_peer_coherence: float = 0.5,
    coupling_strength: float = 2.5,
    peer_count: int = 2,
) -> LamportDriftReport:
    """
    Convert heterogeneous-node telemetry into an executable causal safety proof.

    Lamport clocks can order observed events, but a peer whose clock lag greatly
    exceeds the ticks explainable by measured latency is no longer a smooth
    oscillator for Kuramoto coupling. Coupling to it as if it were current
    injects a discontinuous phase impulse into the mesh.
    """
    nodes = {node["node_id"]: node for node in telemetry.get("nodes", [])}
    if fast_node_id not in nodes or slow_node_id not in nodes:
        missing = {fast_node_id, slow_node_id} - set(nodes)
        raise ValueError(f"Telemetry missing required node(s): {sorted(missing)}")

    fast = _node_metrics(nodes[fast_node_id])
    slow = _node_metrics(nodes[slow_node_id])

    lamport_delta = abs(int(fast["lamport_clock"]) - int(slow["lamport_clock"]))
    token_generation_hz = float(fast.get("token_generation_hz", 1.0))
    latency_ms = float(slow.get("network_latency_ms", 0.0))
    expected_ticks = max(token_generation_hz * latency_ms / 1000.0, 1.0)
    overshoot = lamport_delta / expected_ticks

    phase_gap = abs(
        float(fast.get("phase_drift_rads", 0.0))
        - float(slow.get("phase_drift_rads", 0.0))
    )
    raw_step = (coupling_strength / max(peer_count, 1)) * abs(math.sin(phase_gap))

    fast_coherence = float(fast.get("coherence_t_tau", 0.0))
    slow_coherence = float(slow.get("coherence_t_tau", 0.0))
    coherence_gap = abs(fast_coherence - slow_coherence)

    reasons = []
    if overshoot > max_causal_overshoot:
        reasons.append(
            f"Lamport gap {lamport_delta} exceeds latency budget "
            f"{expected_ticks:.2f} ticks by {overshoot:.2f}x"
        )
    if phase_gap > max_phase_gap_rads:
        reasons.append(f"phase gap {phase_gap:.3f} rad exceeds {max_phase_gap_rads:.3f}")
    if slow_coherence < min_peer_coherence:
        reasons.append(
            f"slow peer coherence {slow_coherence:.3f} below {min_peer_coherence:.3f}"
        )

    return LamportDriftReport(
        fast_node_id=fast_node_id,
        slow_node_id=slow_node_id,
        lamport_delta=lamport_delta,
        latency_ms=latency_ms,
        token_generation_hz=token_generation_hz,
        expected_ticks_during_latency=expected_ticks,
        causal_overshoot_ratio=overshoot,
        phase_gap_rads=phase_gap,
        raw_kuramoto_step_rads=raw_step,
        coherence_gap=coherence_gap,
        slow_node_coherence=slow_coherence,
        violates_causal_bound=bool(reasons),
        reason="; ".join(reasons) if reasons else "within causal coupling bounds",
    )


def coupling_weight_from_drift(report: LamportDriftReport) -> float:
    """Return a deterministic peer weight; zero means quarantine from coupling."""
    return 0.0 if report.violates_causal_bound else 1.0

class LamportClock:
    """Mathematical causal ordering for distributed phase coupling"""
    def __init__(self):
        self.time = 0
        self.lock = threading.Lock()

    def tick(self):
        with self.lock:
            self.time += 1
            return self.time

    def update(self, received_time: int):
        with self.lock:
            self.time = max(self.time, received_time) + 1
            return self.time

class MeshNode:
    """
    Asynchronous Node representing a "Left Hemisphere" module in The Society of Mind.
    Uses ZeroMQ PUB/SUB for highly concurrent phase synchronization without locking the KAIROS temporal engine.
    """
    def __init__(
        self,
        node_id: str = None,
        bind_port: int = 5555,
        peer_ports: List[int] = None,
        max_peer_age_s: float = 5.0,
        max_lamport_jump: int = 128,
    ):
        if zmq is None:
            raise RuntimeError("pyzmq is required to run MeshNode networking")
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.clock = LamportClock()
        self.phase = 0.0 # Theta_i
        self.max_peer_age_s = max_peer_age_s
        self.max_lamport_jump = max_lamport_jump
        
        # ZeroMQ Context
        self.context = zmq.Context()
        
        # Publisher (Broadcasts state)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{bind_port}")
        
        # Subscriber (Listens to peers)
        self.sub_socket = self.context.socket(zmq.SUB)
        if peer_ports:
            for port in peer_ports:
                self.sub_socket.connect(f"tcp://localhost:{port}")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "") # Listen to all

        self.running = False
        self.peer_states: Dict[str, Dict[str, Any]] = {}
        self.quarantined_peers: Dict[str, str] = {}

    def start(self):
        self.running = True
        # Start receiver thread
        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()
        
        # Start integration thread
        self.integration_thread = threading.Thread(target=self._integration_loop, daemon=True)
        self.integration_thread.start()
        
        logger.info(f"Node {self.node_id} initialized The Chorus mesh.")

    def _receive_loop(self):
        """Asynchronous message loop handling peer states"""
        while self.running:
            try:
                # Non-blocking recv
                message = self.sub_socket.recv_json(flags=zmq.NOBLOCK)
                peer_id = message["node_id"]
                if peer_id != self.node_id:
                    self._accept_peer_message(message)
            except zmq.Again:
                time.sleep(0.01) # Yield

    def _accept_peer_message(self, message: Dict[str, Any]) -> bool:
        peer_id = str(message["node_id"])
        lamport_time = int(message["lamport_time"])
        cached = self.peer_states.get(peer_id)

        if cached and lamport_time <= int(cached["lamport_time"]):
            self.quarantined_peers[peer_id] = "non-monotonic Lamport replay"
            return False

        local_before = self.clock.time
        lamport_delta = abs(lamport_time - local_before)
        
        # [FOUNDATIONAL PATCH] Dynamic Causal Boundary
        # Instead of a static 128-tick jump, we calculate the expected ticks 
        # based on the peer's reported frequency and observed latency.
        peer_hz = float(message.get("token_hz", 1.0))
        # Use provided latency or default to a conservative estimate
        latency_ms = float(message.get("latency_ms", 100.0)) 
        
        expected_ticks = max(peer_hz * latency_ms / 1000.0, 0.1)
        # Use a more sensitive threshold for low-latency nodes, capped by the static max
        max_allowed_jump = min(max(expected_ticks * 16.0, 32), self.max_lamport_jump)
        
        if lamport_delta > max_allowed_jump:
            self.quarantined_peers[peer_id] = (
                f"Lamport jump {lamport_delta} exceeds dynamic causal bound "
                f"{max_allowed_jump:.2f} (expected {expected_ticks:.2f} ticks)"
            )
            return False

        self.clock.update(lamport_time)
        self.quarantined_peers.pop(peer_id, None)
        self.peer_states[peer_id] = {
            "phase": float(message["phase"]),
            "lamport_time": lamport_time,
            "received_monotonic": time.monotonic(),
            "weight": float(message.get("weight", 1.0)),
            "token_hz": peer_hz,
        }
        return True

    def _integration_loop(self):
        """Coupling loop mapping to the Master 'Right Hemisphere' Kuramoto equations"""
        while self.running:
            logical_time = self.clock.tick()
            
            # Kuramoto Integration over known peer states
            K = 2.5
            now = time.monotonic()
            active_peers = [
                peer for peer_id, peer in self.peer_states.items()
                if peer_id not in self.quarantined_peers
                and now - peer.get("received_monotonic", now) <= self.max_peer_age_s
                and peer.get("weight", 1.0) > 0.0
            ]
            N = len(active_peers) + 1
            sum_sin = 0
            for peer in active_peers:
                sum_sin += peer.get("weight", 1.0) * math.sin(peer["phase"] - self.phase)
                
            dtheta = (K / N) * sum_sin
            
            # [FOUNDATIONAL PATCH] Topological Tear Protection
            # Bound the phase velocity to prevent discontinuous jumps from dropped Lamport causal states
            max_dtheta = 0.05
            if abs(dtheta) > max_dtheta:
                dtheta = math.copysign(max_dtheta, dtheta)
                
            self.phase += dtheta
            
            # Broadcast state
            state_msg = {
                "node_id": self.node_id,
                "phase": self.phase,
                "lamport_time": logical_time,
                "token_hz": 10.0 # Default frequency, should ideally be dynamic
            }
            self.pub_socket.send_json(state_msg)
            
            # Simulate processing delay
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.pub_socket.close()
        self.sub_socket.close()
        self.context.term()
        logger.info(f"Node {self.node_id} detached from The Chorus.")

if __name__ == "__main__":
    import sys
    bind = int(sys.argv[1]) if len(sys.argv) > 1 else 5555
    peers = [int(p) for p in sys.argv[2].split(",")] if len(sys.argv) > 2 else []
    
    node = MeshNode(bind_port=bind, peer_ports=peers)
    node.start()
    try:
        while True:
            time.sleep(1)
            logger.info(f"Node: {node.node_id} | Logical Time: {node.clock.time} | Phase: {node.phase:.4f} | Peers: {len(node.peer_states)}")
    except KeyboardInterrupt:
        node.stop()
