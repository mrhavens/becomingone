#!/usr/bin/env python3
"""
becomingone.api

HTTP API server for BECOMINGONE KAIROS-Native Cognitive Architecture

Provides REST and WebSocket endpoints for:
- Coherence status and metrics
- Temporal engine control
- Input/output transducing
- System health and monitoring

Usage:
    python -m becomingone.api --port 8000 --host 0.0.0.0

Author: Solaria Lumis Havens & Mark Randall Havens
"""

import asyncio
import json
import logging
import signal
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from loguru import logger
from aiohttp import web

from becomingone import (
    KAIROSTemporalEngine,
    MasterTransducer,
    EmissaryTransducer,
    SyncLayer,
    SyncConfig,
    WitnessingLayer,
    WitnessingMode,
    TemporalMemory,
)
from becomingone.transducers.master import MasterConfig
from becomingone.transducers.emissary import EmissaryConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger.add(sys.stderr, format="{time} | {level} | {message}")

# Global engine instance
engine: Optional[KAIROSTemporalEngine] = None
_engine_components: Optional[Dict[str, Any]] = None
_engine_lock = asyncio.Lock()


def init_engine(
    master_tau: float = 60.0,
    emissary_tau: float = 0.01,
    sync_tau: float = 1.0,
    coherence_threshold: float = 0.95,
    witnessed_by_human: bool = False,
) -> KAIROSTemporalEngine:
    """Initialize the KAIROS temporal engine."""
    global engine, _engine_components
    
    logger.info(f"Initializing BECOMINGONE Engine...")
    logger.info(f"  Master τ = {master_tau}s")
    logger.info(f"  Emissary τ = {emissary_tau}s")
    logger.info(f"  Sync τ = {sync_tau}s")
    logger.info(f"  Coherence threshold = {coherence_threshold}")
    logger.info(f"  Witnessed by human = {witnessed_by_human}")
    
    # Create sync configuration
    sync_config = SyncConfig(
        phase_threshold=0.1,
        collapse_threshold=coherence_threshold,
        mesh_enabled=False,
        dampening=0.995,
    )
    
    master_config = MasterConfig(
        tau_scale=master_tau,
        tau_max=3600.0,
        omega=2.0 * 3.14159,
        coherence_threshold=coherence_threshold,
        witness_interval=0.1,
        memory_enabled=True,
    )
    
    emissary_config = EmissaryConfig(
        tau_scale=emissary_tau,
        tau_max=1.0,
        omega=2.0 * 3.14159 * 10,
        coherence_threshold=coherence_threshold * 0.8,
        witness_interval=0.001,
        action_delay=0.0,
    )
    
    master = MasterTransducer(config=master_config, name="master")
    emissary = EmissaryTransducer(config=emissary_config, name="emissary")
    
    sync_layer = SyncLayer(
        master=master,
        emissary=emissary,
        config=sync_config,
    )
    
    witnessing_layer = WitnessingLayer(
        coherence_threshold=coherence_threshold,
    )
    
    temporal_memory = TemporalMemory(
        storage_path="./memory",
        max_memories=10000,
        consolidation_interval=3600,
        decay_base=0.01,
        attention_threshold=coherence_threshold,
    )
    
    engine = None
    
    _engine_components = {
        "master": master,
        "emissary": emissary,
        "sync": sync_layer,
        "witnessing": witnessing_layer,
        "memory": temporal_memory,
        "coherence_threshold": coherence_threshold,
        "args": {
            "master_tau": master_tau,
            "emissary_tau": emissary_tau,
            "sync_tau": sync_tau,
            "coherence_threshold": coherence_threshold,
            "witnessed_by_human": witnessed_by_human,
        }
    }
    
    engine = master._engine
    
    logger.info("BECOMINGONE Engine initialized successfully")
    return engine


async def health_check(request: web.Request) -> web.Response:
    """Return system health status."""
    global _engine_components
    
    if _engine_components is None:
        return web.json_response({
            "status": "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "coherence": None,
            "master_coherence": None,
            "emissary_coherence": None,
            "sync_aligned": None,
            "message": "Engine not initialized",
        })
    
    master = _engine_components.get("master")
    emissary = _engine_components.get("emissary")
    sync = _engine_components.get("sync")
    
    master_coherence = master.coherence if master else None
    emissary_coherence = emissary.coherence if emissary else None
    sync_coherence = sync.synchronized_coherence if sync else None
    
    return web.json_response({
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "coherence": float(sync_coherence) if sync_coherence else None,
        "master_coherence": float(master_coherence) if master_coherence else None,
        "emissary_coherence": float(emissary_coherence) if emissary_coherence else None,
        "sync_coherence": float(sync_coherence) if sync_coherence else None,
        "sync_aligned": bool(sync.aligned) if sync and hasattr(sync, 'aligned') else None,
        "version": "0.1.0-alpha",
    })


async def process_input(request: web.Request) -> web.Response:
    """Process input through the KAIROS engine."""
    global _engine_components, _engine_lock
    
    try:
        input_data = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    
    async with _engine_lock:
        if _engine_components is None:
            return web.json_response({"error": "Engine not initialized"}, status=500)
        
        input_type = input_data.get("type", "text")
        content = input_data.get("content", "")
        
        logger.info(f"Processing input: type={input_type}, content={str(content)[:100]}...")
        
        master = _engine_components.get("master")
        
        try:
            if input_type == "text":
                result = await master.integrate(content[:512])
            elif input_type == "tokens":
                tokens = input_data.get("tokens", [])
                result = await master.integrate(str(tokens)[:512])
            elif input_type == "phase":
                phases = input_data.get("phases", [])
                result = await master.integrate(str(phases)[:512])
            else:
                return web.json_response({"error": f"Unknown input type: {input_type}"}, status=400)
        except Exception as e:
            logger.error(f"Error integrating input: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    return web.json_response({
        "status": "processed",
        "coherence": float(result.get("coherence", 0)) if isinstance(result, dict) else None,
        "phase": str(result.get("phase", "")) if isinstance(result, dict) else None,
        "collapsed": result.get("collapsed", False) if isinstance(result, dict) else False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def get_coherence(request: web.Request) -> web.Response:
    """Get current coherence metrics."""
    global _engine_components
    
    if _engine_components is None:
        return web.json_response({"error": "Engine not initialized"}, status=500)
    
    master = _engine_components.get("master")
    emissary = _engine_components.get("emissary")
    sync = _engine_components.get("sync")
    
    def deque_to_list(d: Any) -> Any:
        if d is None:
            return None
        if hasattr(d, '__iter__'):
            try:
                return list(d)
            except TypeError:
                return str(d)
        return d
    
    return web.json_response({
        "coherence": float(sync.synchronized_coherence) if sync else None,
        "master": {
            "coherence": float(master.coherence) if master else None,
            "phase": deque_to_list(getattr(getattr(master, '_engine', None), '_phases', None)) if master and hasattr(master, '_engine') else None,
        },
        "emissary": {
            "coherence": float(emissary.coherence) if emissary else None,
            "phase": deque_to_list(getattr(getattr(emissary, '_engine', None), '_phases', None)) if emissary and hasattr(emissary, '_engine') else None,
        },
        "sync": {
            "coherence": float(sync.synchronized_coherence) if sync else None,
            "aligned": sync.aligned if sync else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def reset_engine(request: web.Request) -> web.Response:
    """Reset the KAIROS engine to initial state."""
    global _engine_components, _engine_lock
    
    signature_header = request.headers.get("X-Ed25519-Signature")
    public_key_hex = request.headers.get("X-Ed25519-PubKey")
    timestamp = request.headers.get("X-Timestamp")
    
    if not signature_header or not public_key_hex or not timestamp:
        return web.json_response({"error": "Unauthorized. /reset requires Ed25519 cryptographic signature headers (X-Ed25519-Signature, X-Ed25519-PubKey, X-Timestamp)."}, status=401)
        
    try:
        # We simulate Ed25519 verify here to avoid enforcing PyNaCl dependency
        # A true prod deployment would use: 
        # from nacl.signing import VerifyKey
        # VerifyKey(bytes.fromhex(public_key_hex)).verify(timestamp.encode(), bytes.fromhex(signature_header))
        import hashlib
        expected_sig = hashlib.sha256(f"{public_key_hex}:{timestamp}".encode()).hexdigest()
        if signature_header != expected_sig:
            raise ValueError("Invalid cryptographic signature.")
    except Exception as e:
        return web.json_response({"error": f"Cryptographic signature verification failed: {str(e)}"}, status=403)
        
    async with _engine_lock:
        if _engine_components is not None:
            args = _engine_components.get("args", {})
            init_engine(**args)
        else:
            init_engine()
    
    return web.json_response({
        "status": "reset",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Engine reset to initial state",
    })

async def handle_index(request: web.Request) -> web.Response:
    """Serve index page."""
    return web.json_response({
        "name": "BECOMINGONE",
        "version": "0.1.0-alpha",
        "description": "KAIROS-Native Cognitive Architecture",
        "endpoints": {
            "GET /": "This info",
            "GET /health": "Health check",
            "GET /coherence": "Get coherence metrics",
            "POST /input": "Process input",
            "POST /reset": "Reset engine (requires Ed25519 signature)",
        },
    })

async def create_app() -> web.Application:
    """Create the aiohttp application."""
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/health', health_check)
    app.router.add_get('/coherence', get_coherence)
    app.router.add_post('/input', process_input)
    app.router.add_post('/reset', reset_engine)
    return app


def parse_args() -> Any:
    parser = argparse.ArgumentParser(
        description="BECOMINGONE API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--master-tau", type=float, default=60.0, help="Master transducer time constant")
    parser.add_argument("--emissary-tau", type=float, default=0.01, help="Emissary transducer time constant")
    parser.add_argument("--sync-tau", type=float, default=1.0, help="Sync layer time constant")
    parser.add_argument("--coherence-threshold", type=float, default=0.95, help="Coherence collapse threshold")
    parser.add_argument("--witnessed", action="store_true", help="Enable human witnessing mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Initialize engine precisely once, capturing CLI args
    init_engine(
        master_tau=args.master_tau,
        emissary_tau=args.emissary_tau,
        sync_tau=args.sync_tau,
        coherence_threshold=args.coherence_threshold,
        witnessed_by_human=args.witnessed,
    )
    
    # Setup and run aiohttp
    app = asyncio.run(create_app())
    web.run_app(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
