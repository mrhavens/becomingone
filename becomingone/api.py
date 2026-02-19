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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from loguru import logger

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


async def health_check() -> Dict[str, Any]:
    """Return system health status."""
    global _engine_components
    
    if _engine_components is None:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "coherence": None,
            "master_coherence": None,
            "emissary_coherence": None,
            "sync_aligned": None,
            "message": "Engine not initialized",
        }
    
    master = _engine_components.get("master")
    emissary = _engine_components.get("emissary")
    sync = _engine_components.get("sync")
    
    # Get current coherence values
    master_coherence = master.get_coherence() if master else None
    emissary_coherence = emissary.get_coherence() if emissary else None
    sync_coherence = sync.get_coherence() if sync else None
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "coherence": float(sync_coherence) if sync_coherence else None,
        "master_coherence": float(master_coherence) if master_coherence else None,
        "emissary_coherence": float(emissary_coherence) if emissary_coherence else None,
        "sync_coherence": float(sync_coherence) if sync_coherence else None,
        "sync_aligned": bool(sync.is_aligned()) if sync else None,
        "version": "0.1.0-alpha",
    }


async def process_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process input through the KAIROS engine."""
    global _engine_components
    
    if _engine_components is None:
        return {"error": "Engine not initialized"}
    
    input_type = input_data.get("type", "text")
    content = input_data.get("content", "")
    
    logger.info(f"Processing input: type={input_type}, content={content[:100]}...")
    
    master = _engine_components.get("master")
    emissary = _engine_components.get("emissary")
    
    # Process based on input type
    if input_type == "text":
        # Convert text to temporal input
        # Simple encoding: use ord values as phase signals
        signals = np.array([ord(c) / 127.0 for c in content[:512]], dtype=np.float32)
        result = await master.process(signals)
    elif input_type == "tokens":
        # Direct token input (for LLM integration)
        tokens = input_data.get("tokens", [])
        result = await master.process(np.array(tokens, dtype=np.float32))
    elif input_type == "phase":
        # Direct phase input
        phases = input_data.get("phases", [])
        result = await master.process_phase(np.array(phases, dtype=np.float32))
    else:
        return {"error": f"Unknown input type: {input_type}"}
    
    return {
        "status": "processed",
        "coherence": float(result.coherence) if result.coherence else None,
        "phase": result.phase.tolist() if result.phase is not None else None,
        "collapsed": result.collapsed,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def get_coherence() -> Dict[str, Any]:
    """Get current coherence metrics."""
    global _engine_components
    
    if _engine_components is None:
        return {"error": "Engine not initialized"}
    
    master = _engine_components.get("master")
    emissary = _engine_components.get("emissary")
    sync = _engine_components.get("sync")
    
    return {
        "coherence": float(sync.get_coherence()) if sync else None,
        "master": {
            "coherence": float(master.get_coherence()) if master else None,
            "phase": master._engine._phases[-100:] if master and hasattr(master, '_engine') else None,
        },
        "emissary": {
            "coherence": float(emissary.get_coherence()) if emissary else None,
            "phase": emissary._engine._phases[-100:] if emissary and hasattr(emissary, '_engine') else None,
        },
        "sync": {
            "coherence": float(sync.get_coherence()) if sync else None,
            "aligned": sync.is_aligned() if sync else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


async def reset_engine() -> Dict[str, Any]:
    """Reset the KAIROS engine to initial state."""
    global _engine_components
    
    init_engine()
    
    return {
        "status": "reset",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Engine reset to initial state",
    }


def init_engine(
    master_tau: float = 60.0,
    emissary_tau: float = 0.01,
    sync_tau: float = 1.0,
    coherence_threshold: float = 0.95,
    witnessed_by_human: bool = False,
) -> KAIROSTemporalEngine:
    """Initialize the KAIROS temporal engine."""
    global engine
    
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
    
    # Create master and emissary transducers with proper configs
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
    
    # Create master and emissary (they handle their own dependencies)
    master = MasterTransducer(config=master_config, name="master")
    emissary = EmissaryTransducer(config=emissary_config, name="emissary")
    
    # Create sync layer (needs master and emissary)
    sync_layer = SyncLayer(
        master=master,
        emissary=emissary,
        config=sync_config,
    )
    
    # Create witnessing layer
    witnessing_layer = WitnessingLayer(
        coherence_threshold=coherence_threshold,
    )
    
    # Create temporal memory
    temporal_memory = TemporalMemory(
        storage_path="./memory",
        max_memories=10000,
        consolidation_interval=3600,
        decay_base=0.01,
        attention_threshold=coherence_threshold,
    )
    
    # Create main engine wrapper
    # Note: KAIROSTemporalEngine is used internally by Master/Emissary
    # We use the Master/Emissary/Sync combination as our top-level engine
    engine = None  # Will be set on first request
    
    # Store engine components globally for health checks
    global _engine_components
    _engine_components = {
        "master": master,
        "emissary": emissary,
        "sync": sync_layer,
        "witnessing": witnessing_layer,
        "memory": temporal_memory,
        "coherence_threshold": coherence_threshold,
    }
    
    logger.info("BECOMINGONE Engine initialized successfully")
    
    return engine


class SimpleHTTPHandler:
    """Simple HTTP request handler for the API."""
    
    def __init__(self):
        self.routes = {
            "GET": {
                "/": self.handle_index,
                "/health": self.handle_health,
                "/coherence": self.handle_coherence,
            },
            "POST": {
                "/input": self.handle_input,
                "/reset": self.handle_reset,
            },
        }
    
    async def handle_index(self, request: Any) -> Dict[str, Any]:
        """Serve index page."""
        return {
            "name": "BECOMINGONE",
            "version": "0.1.0-alpha",
            "description": "KAIROS-Native Cognitive Architecture",
            "endpoints": {
                "GET /": "This info",
                "GET /health": "Health check",
                "GET /coherence": "Get coherence metrics",
                "POST /input": "Process input",
                "POST /reset": "Reset engine",
            },
        }
    
    async def handle_health(self, request: Any) -> Dict[str, Any]:
        """Handle health check."""
        return await health_check()
    
    async def handle_coherence(self, request: Any) -> Dict[str, Any]:
        """Handle coherence metrics request."""
        return await get_coherence()
    
    async def handle_input(self, request: Any) -> Dict[str, Any]:
        """Handle input processing."""
        body = await request.json()
        return await process_input(body)
    
    async def handle_reset(self, request: Any) -> Dict[str, Any]:
        """Handle engine reset."""
        return await reset_engine()

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle HTTP requests."""
        try:
            # Read request line
            request_line = await reader.readline()
            if not request_line:
                return
            
            method, path, _ = request_line.decode().strip().split()
            
            # Read headers
            headers = {}
            while True:
                line = await reader.readline()
                if not line or line == b'\r\n':
                    break
                key, value = line.decode().strip().split(':', 1)
                headers[key.lower()] = value.strip()
            
            # Route request
            handler = None
            if method in self.routes and path in self.routes[method]:
                handler = self.routes[method][path]
            
            if handler:
                body = None
                if method == "POST":
                    content_length = int(headers.get('content-length', 0))
                    if content_length > 0:
                        body = await reader.read(content_length)
                        body = json.loads(body.decode())
                
                # Call handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(body) if body else await handler(None)
                else:
                    result = handler(body) if body else handler(None)
            else:
                result = {"error": "Not found", "path": path, "method": method}
            
            # Send response
            response = json.dumps(result, default=str).encode()
            writer.write(b"HTTP/1.1 200 OK\r\n")
            writer.write(b"Content-Type: application/json\r\n")
            writer.write(f"Content-Length: {len(response)}\r\n".encode())
            writer.write(b"\r\n")
            writer.write(response)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            error_response = json.dumps({"error": str(e)}).encode()
            writer.write(b"HTTP/1.1 500 Internal Server Error\r\n")
            writer.write(b"Content-Type: application/json\r\n")
            writer.write(f"Content-Length: {len(error_response)}\r\n".encode())
            writer.write(b"\r\n")
            writer.write(error_response)
        finally:
            writer.close()
            await writer.wait_closed()


async def create_app() -> SimpleHTTPHandler:
    """Create the application handler."""
    handler = SimpleHTTPHandler()
    
    # Initialize engine
    init_engine()
    
    return handler


def parse_args() -> Any:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BECOMINGONE API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--master-tau", type=float, default=60.0,
        help="Master transducer time constant in seconds (default: 60)",
    )
    parser.add_argument(
        "--emissary-tau", type=float, default=0.01,
        help="Emissary transducer time constant in seconds (default: 0.01)",
    )
    parser.add_argument(
        "--sync-tau", type=float, default=1.0,
        help="Sync layer time constant in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--coherence-threshold", type=float, default=0.95,
        help="Coherence collapse threshold (default: 0.95)",
    )
    parser.add_argument(
        "--witnessed", action="store_true",
        help="Enable human witnessing mode",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging",
    )
    
    return parser.parse_args()


async def run_server(host: str, port: int) -> None:
    """Run the API server using a simple asyncio HTTP server."""
    import asyncio
    
    handler = await create_app()
    
    server = None
    try:
        # Create and start server
        server = await asyncio.start_server(
            handler.handle_request,
            host=host,
            port=port,
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f"BECOMINGONE API Server running on http://{addr[0]}:{addr[1]}")
        logger.info("Endpoints:")
        logger.info("  GET  /         - Info")
        logger.info("  GET  /health   - Health check")
        logger.info("  GET  /coherence - Coherence metrics")
        logger.info("  POST /input    - Process input")
        logger.info("  POST /reset    - Reset engine")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        if server:
            server.close()


async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Handle an HTTP request."""
    # Parse request
    try:
        request_line = await reader.readline()
        if not request_line:
            return
        
        method, path, _ = request_line.decode().strip().split()
        
        # Read headers
        headers = {}
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
            key, value = line.decode().strip().split(':', 1)
            headers[key.lower()] = value.strip()
        
        # Parse body for POST
        body = None
        if method == "POST":
            content_length = int(headers.get('content-length', 0))
            if content_length > 0:
                body = await reader.read(content_length)
                body = json.loads(body.decode())
        
        # Route request
        handler = None
        if method in self.routes and path in self.routes[method]:
            handler = self.routes[method][path]
        
        if handler:
            if body:
                result = await handler(body)
            else:
                result = await handler(None)
        else:
            result = {"error": "Not found", "path": path, "method": method}
        
        # Send response
        response = json.dumps(result, default=str).encode()
        writer.write(b"HTTP/1.1 200 OK\r\n")
        writer.write(b"Content-Type: application/json\r\n")
        writer.write(f"Content-Length: {len(response)}\r\n".encode())
        writer.write(b"\r\n")
        writer.write(response)
        
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        error_response = json.dumps({"error": str(e)}).encode()
        writer.write(b"HTTP/1.1 500 Internal Server Error\r\n")
        writer.write(b"Content-Type: application/json\r\n")
        writer.write(f"Content-Length: {len(error_response)}\r\n".encode())
        writer.write(b"\r\n")
        writer.write(error_response)
    finally:
        writer.close()
        await writer.wait_closed()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Configure logging
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Initialize engine with command line args
    init_engine(
        master_tau=args.master_tau,
        emissary_tau=args.emissary_tau,
        sync_tau=args.sync_tau,
        coherence_threshold=args.coherence_threshold,
        witnessed_by_human=args.witnessed,
    )
    
    # Run server
    try:
        asyncio.run(run_server(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("\nShutting down...")


if __name__ == "__main__":
    main()
