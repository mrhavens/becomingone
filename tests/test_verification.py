import json
import math
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from becomingone.distributed_mesh import MeshNode

def verify_fix():
    print("--- DISTILLATION & PROOF ARCHITECT: Lamport Drift Verification ---")
    
    # 1. Setup Node
    node = MeshNode(node_id="master-node", max_lamport_jump=128)
    node.clock.time = 459201 
    
    # 2. PROVING THE FIX: The "Hidden Tear" now quarantined
    # Delta = 100 
    # Peer frequency = 12.4 Hz
    # Latency = 1ms
    # Expected ticks = 0.0124. 
    # max_allowed_jump = min(max(0.0124 * 16, 32), 128) = 32.
    # 100 > 32 -> Should be quarantined.
    
    hidden_tear_msg = {
        "node_id": "drifting-peer",
        "phase": 0.5,
        "lamport_time": 459201 - 100,
        "token_hz": 12.4,
        "latency_ms": 1.0
    }
    
    print("Simulating Hidden Tear (Delta=100, Latency=1ms)...")
    success = node._accept_peer_message(hidden_tear_msg)
    
    if not success:
        reason = node.quarantined_peers.get("drifting-peer")
        print(f"[SUCCESS]: Hidden tear quarantined. Reason: {reason}")
        return True
    else:
        print("[FAILURE]: Hidden tear was ACCEPTED. Patch failed.")
        return False

if __name__ == "__main__":
    if verify_fix():
        sys.exit(0)
    else:
        sys.exit(1)
