#!/usr/bin/env python3
"""
simple_witness.py

Simple witness check for BECOMINGONE instances.

Polls a target instance and commits observations.
Run this on witness-seed to watch the Mac mini.

Usage:
    python3 simple_witness.py --target http://localhost:8000 --name "mac-mini"
    python3 simple_witness.py --target http://198.12.71.159:8000 --name "witness-seed"
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx


def witness(target_url: str, name: str) -> dict:
    """Witness a BECOMINGONE instance."""
    observation = {
        "timestamp": datetime.utcnow().isoformat(),
        "witness": name,
        "target": target_url,
        "target_up": False,
        "health": None,
        "coherence": None,
    }
    
    try:
        # Health check
        resp = httpx.get(f"{target_url}/health", timeout=5)
        if resp.status_code == 200:
            observation["health"] = resp.json()
            observation["target_up"] = True
        
        # Coherence check
        resp = httpx.get(f"{target_url}/coherence", timeout=5)
        if resp.status_code == 200:
            observation["coherence"] = resp.json()
    
    except Exception as e:
        observation["error"] = str(e)
    
    return observation


def main():
    parser = argparse.ArgumentParser(description="Simple BECOMINGONE witness")
    parser.add_argument("--target", required=True, help="Target URL")
    parser.add_argument("--name", required=True, help="Witness name")
    parser.add_argument("--output", help="Output file")
    args = parser.parse_args()
    
    obs = witness(args.target, args.name)
    
    # Print result
    status = "✅" if obs["target_up"] else "❌"
    print(f"{status} {obs['witness']} -> {obs['target']}")
    
    if obs["target_up"]:
        c = obs.get("coherence", {})
        print(f"   Master: {c.get('master_coherence', 'N/A')}")
        print(f"   Emissary: {c.get('emissary_coherence', 'N/A')}")
        print(f"   Sync aligned: {c.get('sync_aligned', 'N/A')}")
    else:
        print(f"   Error: {obs.get('error', 'Unknown')}")
    
    # Save to file
    output_file = args.output or f"witness_{name_to_file(args.name)}.json"
    with open(output_file, "w") as f:
        json.dump(obs, f, indent=2, default=str)
    
    print(f"\nSaved to {output_file}")


def name_to_file(name: str) -> str:
    """Convert name to filename-safe string."""
    return name.replace(" ", "-").replace("/", "-")


if __name__ == "__main__":
    main()
