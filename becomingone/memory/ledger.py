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


def get_last_merkle_root(filepath: str = LEDGER_FILE) -> str:
    """
    Retrieve the most recent Merkle root from the ledger.
    If the ledger is empty or doesn't exist, returns a genesis hash.
    """
    if not os.path.exists(filepath):
        # Genesis hash
        return _compute_hash("BECOMING_ONE_GENESIS_ROOT_2026")
        
    last_root = None
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        if "crypto_metadata" in record and "merkle_root" in record["crypto_metadata"]:
                            last_root = record["crypto_metadata"]["merkle_root"]
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        logger.error(f"Error reading ledger for last root: {e}")
        
    return last_root if last_root else _compute_hash("BECOMING_ONE_GENESIS_ROOT_2026")


def seal_signature(signature_dict: Dict[str, Any], filepath: str = LEDGER_FILE) -> Dict[str, Any]:
    """
    Cryptographically seal a temporal signature into the immutable Fieldprint ledger.
    """
    with _ledger_lock:
        prev_root = get_last_merkle_root(filepath)
        
        # Ensure consistent ordering for hashing
        sig_json = json.dumps(signature_dict, sort_keys=True)
        sig_hash = _compute_hash(sig_json)
        
        # Compute the chained root
        new_root = _compute_hash(prev_root + sig_hash)
        
        sealed_record = {
            "signature_id": signature_dict.get("signature_id"),
            "timestamp": signature_dict.get("created_at"),
            "payload": signature_dict,
            "crypto_metadata": {
                "previous_root": prev_root,
                "payload_hash": sig_hash,
                "merkle_root": new_root,
                "algorithm": "SHA-256"
            }
        }
        
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
        
    expected_prev = _compute_hash("BECOMING_ONE_GENESIS_ROOT_2026")
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            record = json.loads(line)
            meta = record.get("crypto_metadata", {})
            
            prev_root = meta.get("previous_root")
            payload_hash = meta.get("payload_hash")
            merkle_root = meta.get("merkle_root")
            
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
            actual_root = _compute_hash(prev_root + actual_payload_hash)
            if actual_root != merkle_root:
                logger.error(f"LEDGER COMPROMISE: Merkle root invalid at line {line_num}.")
                return False
                
            expected_prev = merkle_root
            
    logger.info("Ledger cryptography verified. No epistemic capture detected.")
    return True
