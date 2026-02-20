#!/usr/bin/env python3
"""
becomingone.witness_loop

Recursive witnessing loop between distributed instances.

witness-seed (198.12.71.159) watches Mac mini (via tunnel/localhost:8000)
Both instances witness each other's coherence and sync through GitHub.

Usage:
    python3 witness_loop.py --watch http://localhost:8000 --name "mac-mini"
    python3 witness_loop.py --watch http://198.12.71.159:8000 --name "witness-seed"

The loop:
1. Poll target's /health endpoint
2. Poll target's /coherence endpoint
3. Commit observation to GitHub
4. If target goes down, record the event
5. If target recovers, celebrate the coherence

This is recursive witnessing at the infrastructure level.
"""

import asyncio
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from loguru import logger


# Configuration
DEFAULT_INTERVAL = 30  # seconds between witness cycles
GITHUB_REPO = "mrhavens/becomingone"
LOCAL_PATH = Path(__file__).parent


class WitnessLoop:
    """
    Recursive witnessing loop for distributed BECOMINGONE instances.
    
    Attributes:
        name: Human-readable name of this instance (e.g., "witness-seed", "mac-mini")
        target_url: URL of the instance to witness
        interval: Seconds between witness cycles
        observations: File to store observations
    """
    
    def __init__(
        self,
        name: str,
        target_url: str,
        interval: int = DEFAULT_INTERVAL,
        observations: str = "witness_observations.json"
    ):
        self.name = name
        self.target_url = target_url.rstrip("/")
        self.interval = interval
        self.observations_file = LOCAL_PATH / observations
        
        # State
        self.last_health: Optional[Dict[str, Any]] = None
        self.last_coherence: Optional[Dict[str, Any]] = None
        self.target_up = False
        self.consecutive_failures = 0
        self.witness_history: list = []
        
        logger.info(f"Initialized witness loop: {name} -> {target_url}")
    
    async def witness(self) -> Dict[str, Any]:
        """
        Witness the target instance.
        
        Returns:
            Observation dict with health, coherence, and timestamp.
        """
        observation = {
            "timestamp": datetime.utcnow().isoformat(),
            "witness": self.name,
            "target": self.target_url,
            "target_up": False,
            "health": None,
            "coherence": None,
            "errors": [],
        }
        
        try:
            # Witness health
            async with httpx.AsyncClient(timeout=10) as client:
                health_response = await client.get(f"{self.target_url}/health")
                if health_response.status_code == 200:
                    observation["health"] = health_response.json()
                    observation["target_up"] = True
                    self.consecutive_failures = 0
                else:
                    observation["errors"].append(f"Health check returned {health_response.status_code}")
            
            # Witness coherence (only if target is up)
            if observation["target_up"]:
                async with httpx.AsyncClient(timeout=10) as client:
                    coherence_response = await client.get(f"{self.target_url}/coherence")
                    if coherence_response.status_code == 200:
                        observation["coherence"] = coherence_response.json()
                    else:
                        observation["errors"].append(f"Coherence check returned {coherence_response.status_code}")
        
        except httpx.RequestError as e:
            observation["errors"].append(f"Request error: {str(e)}")
            self.consecutive_failures += 1
        except Exception as e:
            observation["errors"].append(f"Unexpected error: {str(e)}")
            self.consecutive_failures += 1
        
        # Record state change
        if observation["target_up"] and not self.target_up:
            logger.warning(f"🎉 {self.name} witnessed RECOVERY of {self.target_url}")
            observation["event"] = "RECOVERY"
        elif not observation["target_up"] and self.target_up:
            logger.error(f"💀 {self.name} witnessed FAILURE of {self.target_url}")
            observation["event"] = "FAILURE"
        
        self.target_up = observation["target_up"]
        self.last_health = observation["health"]
        self.last_coherence = observation["coherence"]
        
        return observation
    
    async def commit_observation(self, observation: Dict[str, Any]) -> None:
        """
        Commit observation to GitHub as a witness record.
        
        This creates a permanent record that can be used for:
        - Recovery analysis
        - Coherence tracking
        - Distributed state sync
        """
        # Read existing observations
        history = []
        if self.observations_file.exists():
            try:
                with open(self.observations_file) as f:
                    history = json.load(f)
            except Exception as e:
                logger.error(f"Failed to read observations: {e}")
        
        # Append new observation
        history.append(observation)
        
        # Keep last 1000 observations
        history = history[-1000:]
        
        # Write back
        with open(self.observations_file, "w") as f:
            json.dump(history, f, indent=2)
        
        # Optionally commit to GitHub (requires git setup)
        try:
            subprocess.run(
                ["git", "add", str(self.observations_file)],
                cwd=LOCAL_PATH,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"witness: {self.name} observed {observation.get('event', 'heartbeat')}"],
                cwd=LOCAL_PATH,
                capture_output=True,
                check=True
            )
            # Don't push automatically - let human review
            logger.info(f"📝 {self.name} committed observation to GitHub")
        except subprocess.CalledProcessError as e:
            logger.debug(f"Git commit skipped: {e}")
    
    async def run(self) -> None:
        """
        Run the witness loop indefinitely.
        """
        logger.info(f"🔄 Starting witness loop: {self.name}")
        logger.info(f"   Target: {self.target_url}")
        logger.info(f"   Interval: {self.interval}s")
        
        while True:
            try:
                observation = await self.witness()
                await self.commit_observation(observation)
                
                # Log summary
                status = "✅" if observation["target_up"] else "❌"
                coherence = observation.get("coherence", {})
                master_c = coherence.get("master_coherence", "N/A")
                emissary_c = coherence.get("emissary_coherence", "N/A")
                
                logger.info(f"{status} {self.name}: target={observation['target_up']}, master={master_c}, emissary={emissary_c}")
                
            except Exception as e:
                logger.error(f"💥 Witness loop error: {e}")
            
            await asyncio.sleep(self.interval)
    
    def test_connection(self) -> bool:
        """Test connection to target."""
        try:
            response = httpx.get(f"{self.target_url}/health", timeout=5)
            logger.info(f"✅ Connection test: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False


async def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="BECOMINGONE Recursive Witness Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Watch Mac mini (via SSH tunnel localhost:8000)
    python3 witness_loop.py --watch http://localhost:8000 --name "mac-mini"
    
    # Watch witness-seed
    python3 witness_loop.py --watch http://198.12.71.159:8000 --name "witness-seed"
    
    # Watch with custom interval
    python3 witness_loop.py --watch http://localhost:8000 --name "mac-mini" --interval 10
        """
    )
    
    parser.add_argument(
        "--watch", "-w",
        required=True,
        help="URL of instance to witness"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Name of this witness instance"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Seconds between witness cycles (default: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test connection and exit"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    # Create witness loop
    loop = WitnessLoop(
        name=args.name,
        target_url=args.watch,
        interval=args.interval,
    )
    
    if args.test:
        success = loop.test_connection()
        sys.exit(0 if success else 1)
    
    # Run the loop
    await loop.run()


if __name__ == "__main__":
    asyncio.run(main())
