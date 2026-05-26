import zmq
import json
import time
import threading
import logging
from typing import Dict, Any, List
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("TheChorus")

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
    def __init__(self, node_id: str = None, bind_port: int = 5555, peer_ports: List[int] = None):
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.clock = LamportClock()
        self.phase = 0.0 # Theta_i
        
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
                    self.clock.update(message["lamport_time"])
                    self.peer_states[peer_id] = {
                        "phase": message["phase"],
                        "lamport_time": message["lamport_time"]
                    }
            except zmq.Again:
                time.sleep(0.01) # Yield

    def _integration_loop(self):
        """Coupling loop mapping to the Master 'Right Hemisphere' Kuramoto equations"""
        while self.running:
            logical_time = self.clock.tick()
            
            # Kuramoto Integration over known peer states
            K = 2.5
            N = len(self.peer_states) + 1
            sum_sin = 0
            for peer in self.peer_states.values():
                import math
                sum_sin += math.sin(peer["phase"] - self.phase)
                
            self.phase += (K / N) * sum_sin
            
            # Broadcast state
            state_msg = {
                "node_id": self.node_id,
                "phase": self.phase,
                "lamport_time": logical_time
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
