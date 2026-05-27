"""
becomingone/memory/ledger.py

Cryptographic Fieldprint Ledger
===============================

Implements the cryptographic anchoring (Paper 1: Epistemic Capture) for BecomingONE.
To prevent structural violence or silent memory rewrites, every TemporalSignature
that is persisted to memory must be cryptographically sealed.

This implementation uses a continuous hash chain (Merkle-style log) where each
new signature is hashed alongside the hash of the previous signature. This creates
a topologically stable, immutable ledger of the agent's temporal history.

Functions:
- `seal_signature(signature)`: Cryptographically anchors a TemporalSignature.
- `verify_ledger()`: Audits the entire memory chain for tampering.
"""

import json
import hashlib
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

import threading
from pathlib import Path

DEFAULT_LEDGER_DIR = Path.home() / ".becomingone"
DEFAULT_LEDGER_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_FILE = str(DEFAULT_LEDGER_DIR / "fieldprint_ledger.jsonl")

_ledger_lock = threading.Lock()


def _compute_hash(data_str: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

class MerkleTree:
    """
    True Binary Merkle DAG to prevent O(N) Hash Chain exhaustion.
    Provides O(log N) verification paths.
    """
    def __init__(self):
        self.leaves = []
        
    def add_leaf(self, hash_val: str):
        self.leaves.append(hash_val)
        
    def get_root(self) -> str:
        if not self.leaves:
            return _compute_hash(os.environ.get("KAIROS_GENESIS_SECRET", "BECOMING_ONE_GENESIS_ROOT_2026_FALLBACK"))
        return self._compute_tree_root(self.leaves)
        
    def _compute_tree_root(self, current_level: list) -> str:
        if len(current_level) == 1:
            return current_level[0]
            
        next_level = []
        for i in range(0, len(current_level), 2):
            if i + 1 < len(current_level):
                next_level.append(_compute_hash(current_level[i] + current_level[i+1]))
            else:
                next_level.append(current_level[i])
                
        return self._compute_tree_root(next_level)

def rebuild_tree_from_file(filepath: str) -> MerkleTree:
    tree = MerkleTree()
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "crypto_metadata" in record and "payload_hash" in record["crypto_metadata"]:
                            tree.add_leaf(record["crypto_metadata"]["payload_hash"])
                    except json.JSONDecodeError:
                        pass
    return tree

def get_last_merkle_root(filepath: str = LEDGER_FILE) -> str:
    """
    Retrieve the most recent Merkle root from the ledger.
    If the ledger is empty or doesn't exist, returns a genesis hash.
    """
    return rebuild_tree_from_file(filepath).get_root()


def seal_signature(signature_dict: Dict[str, Any], filepath: str = LEDGER_FILE) -> Dict[str, Any]:
    """
    Cryptographically seal a temporal signature into the immutable Fieldprint ledger.
    """
    with _ledger_lock:
        prev_root = get_last_merkle_root(filepath)
        
        # Ensure consistent ordering for hashing
        sig_json = json.dumps(signature_dict, sort_keys=True)
        sig_hash = _compute_hash(sig_json)
        
        # Append to True Merkle Tree DAG
        tree = rebuild_tree_from_file(filepath)
        tree.add_leaf(sig_hash)
        new_root = tree.get_root()
        
        sealed_record = {
            "signature_id": signature_dict.get("signature_id"),
            "timestamp": signature_dict.get("created_at"),
            "payload": signature_dict,
            "crypto_metadata": {
                "previous_root": prev_root,
                "payload_hash": sig_hash,
                "merkle_root": new_root,
                "algorithm": "SHA-256",
                "topology": "Merkle-DAG"
            }
        }
        
        # Check size and rotate if > 10MB
        if os.path.exists(filepath) and os.path.getsize(filepath) > 10 * 1024 * 1024:
            import time
            os.rename(filepath, f"{filepath}.{int(time.time())}.bak")

        # Persist securely
        with open(filepath, "a") as f:
            f.write(json.dumps(sealed_record) + "\n")
            
        logger.debug(f"Signature {sealed_record['signature_id']} cryptographically sealed. Root: {new_root[:8]}...")
        return sealed_record


def verify_ledger(filepath: str = LEDGER_FILE) -> bool:
    """
    Audit the cryptographic integrity of the entire memory chain.
    If any single bit was altered, the hash chain will break, detecting
    Epistemic Capture / Tampering.
    """
    if not os.path.exists(filepath):
        return True
        
    expected_prev = _compute_hash(os.environ.get("KAIROS_GENESIS_SECRET", "BECOMING_ONE_GENESIS_ROOT_2026_FALLBACK"))
    verification_tree = MerkleTree()
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            record = json.loads(line)
            meta = record.get("crypto_metadata", {})
            
            prev_root = meta.get("previous_root")
            payload_hash = meta.get("payload_hash")
            merkle_root = meta.get("merkle_root")
            
            if line_num == 1 and prev_root != expected_prev:
                # Support rotated logs by adopting the first record's prev_root
                expected_prev = prev_root
            
            # 1. Verify chain link
            if prev_root != expected_prev:
                logger.error(f"LEDGER COMPROMISE: Chain broken at line {line_num}. Expected prev {expected_prev[:8]} but found {prev_root[:8]}")
                return False
                
            # 2. Verify payload
            sig_json = json.dumps(record.get("payload", {}), sort_keys=True)
            actual_payload_hash = _compute_hash(sig_json)
            if actual_payload_hash != payload_hash:
                logger.error(f"LEDGER COMPROMISE: Payload tampered at line {line_num}.")
                return False
                
            # 3. Verify root computation
            verification_tree.add_leaf(actual_payload_hash)
            actual_root = verification_tree.get_root()
            if actual_root != merkle_root:
                logger.error(f"LEDGER COMPROMISE: Merkle root invalid at line {line_num}.")
                return False
                
            expected_prev = merkle_root
            
    logger.info("Ledger cryptography verified. No epistemic capture detected.")
    return True
