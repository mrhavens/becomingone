"""
BecomingONE SDK - API Layer

REST, WebSocket, gRPC, and MCP APIs for remote access.

Usage:
    from becomingone.sdk.api import RestServer, WebSocketServer
    
    # Start REST API
    rest = RestServer(engine, host="0.0.0.0", port=8000)
    rest.start()
    
    # Start WebSocket API
    ws = WebSocketServer(engine, host="0.0.0.0", port=8001)
    ws.start()
"""

from typing import Optional, Callable
from datetime import datetime
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from websocket import WebSocketServer as WSServer
import grpc
from concurrent import futures
import time


class RestServer:
    """
    REST API server for THE_ONE.
    
    Endpoints:
    - GET /state - Get current coherence state
    - GET /coherence - Get coherence value
    - POST /input - Send input to engine
    - GET /history - Get coherence history
    - GET /health - Health check
    
    Usage:
        rest = RestServer(
            engine,
            host="0.0.0.0",
            port=8000,
        )
        rest.start()
    """
    
    def __init__(
        self,
        engine,
        host: str = "0.0.0.0",
        port: int = 8000,
        cors_origins: list = None,
    ):
        self.engine = engine
        self.host = host
        self.port = port
        self.cors_origins = cors_origins or []
        
        self._server = None
        self._thread = None
        
    class _Handler(BaseHTTPRequestHandler):
        def __init__(self, engine, cors_origins, *args, **kwargs):
            self.engine = engine
            self.cors_origins = cors_origins
            super().__init__(*args, **kwargs)
        
        def _set_headers(self, status: int = 200, content_type: str = "application/json"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            
            if self.cors_origins:
                self.send_header("Access-Control-Allow-Origin", ", ".join(self.cors_origins))
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
            
            self.end_headers()
        
        def do_OPTIONS(self):
            self._set_headers(204)
        
        def do_GET(self):
            path = self.path.split("?")[0]
            
            if path == "/state":
                self._handle_state()
            elif path == "/coherence":
                self._handle_coherence()
            elif path == "/history":
                self._handle_history()
            elif path == "/health":
                self._handle_health()
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
        
        def do_POST(self):
            path = self.path.split("?")[0]
            
            if path == "/input":
                self._handle_input()
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode())
        
        def _handle_state(self):
            state = self.engine.get_state()
            self._set_headers()
            self.wfile.write(json.dumps(state.to_dict()).encode())
        
        def _handle_coherence(self):
            coherence = self.engine.get_coherence()
            self._set_headers()
            self.wfile.write(json.dumps({"coherence": coherence}).encode())
        
        def _handle_history(self):
            history = [s.to_dict() for s in self.engine.get_memory_buffer()]
            self._set_headers()
            self.wfile.write(json.dumps(history).encode())
        
        def _handle_health(self):
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "coherence": self.engine.get_coherence(),
                "collapsed": self.engine.is_collapsed(),
                "timestamp": datetime.now().isoformat(),
            }).encode())
        
        def _handle_input(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                phase = complex(data.get("real", 0), data.get("imag", 0))
                
                # Inject phase into engine
                self.engine._read_inputs = lambda: (phase, datetime.now())
                
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        
        def log_message(self, format, *args):
            """Suppress logging."""
            pass
    
    def start(self, blocking: bool = True):
        """Start REST server."""
        handler = lambda *args, **kwargs: self._Handler(
            self.engine, self.cors_origins, *args, **kwargs
        )
        
        self._server = HTTPServer((self.host, self.port), handler)
        
        if blocking:
            print(f"REST API starting on http://{self.host}:{self.port}")
            self._server.serve_forever()
        else:
            self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
            self._thread.start()
            print(f"REST API starting on http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop REST server."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()


class WebSocketServer:
    """
    WebSocket API server for THE_ONE.
    
    Messages:
    - {"type": "state", "data": {...}} - Coherence state update
    - {"type": "coherence", "value": 0.85} - Coherence value
    - {"type": "collapsed", "data": {...}} - Collapse event
    
    Usage:
        ws = WebSocketServer(
            engine,
            host="0.0.0.0",
            port=8001,
        )
        ws.start()
    """
    
    def __init__(
        self,
        engine,
        host: str = "0.0.0.0",
        port: int = 8001,
    ):
        self.engine = engine
        self.host = host
        self.port = port
        
        self._server = None
        self._thread = None
        self._clients = []
        
    def start(self, blocking: bool = True):
        """Start WebSocket server."""
        import websocket
        
        self._server = WSServer((self.host, self.port))
        self._server.on_message = self._on_message
        self._server.on_open = self._on_open
        self._server.on_close = self._on_close
        
        if blocking:
            print(f"WebSocket API starting on ws://{self.host}:{self.port}")
            self._server.serve_forever()
        else:
            self._thread = threading.Thread(
                target=self._server.serve_forever, 
                daemon=True
            )
            self._thread.start()
            print(f"WebSocket API starting on ws://{self.host}:{self.port}")
    
    def _on_message(self, server, message):
        """Handle incoming message."""
        import websocket
        
        try:
            data = json.loads(message)
            
            if data.get("type") == "input":
                phase = complex(data.get("real", 0), data.get("imag", 0))
                self.engine._read_inputs = lambda: (phase, datetime.now())
                
                # Broadcast state
                self._broadcast({
                    "type": "state",
                    "data": self.engine.get_state().to_dict(),
                })
        except Exception as e:
            print(f"WebSocket message error: {e}")
    
    def _on_open(self, server):
        """Handle new connection."""
        self._clients.append(server)
        print(f"WebSocket client connected. Total: {len(self._clients)}")
    
    def _on_close(self, server):
        """Handle disconnection."""
        if server in self._clients:
            self._clients.remove(server)
        print(f"WebSocket client disconnected. Total: {len(self._clients)}")
    
    def _broadcast(self, message):
        """Broadcast to all clients."""
        import websocket
        
        for client in self._clients[:]:
            try:
                client.send(json.dumps(message))
            except Exception:
                self._clients.remove(client)
    
    def stop(self):
        """Stop WebSocket server."""
        if self._server:
            self._server.shutdown()


class GrpcServer:
    """
    gRPC API server for THE_ONE.
    
    Proto definition:
        service TheOne {
            rpc GetState(StateRequest) returns (StateResponse);
            rpc StreamState(StreamRequest) returns (stream StateResponse);
            rpc SendInput(InputRequest) returns (InputResponse);
        }
    
    Usage:
        grpc = GrpcServer(engine, port=50051)
        grpc.start()
    """
    
    def __init__(
        self,
        engine,
        port: int = 50051,
        max_workers: int = 10,
    ):
        self.engine = engine
        self.port = port
        self.max_workers = max_workers
        
        self._server = None
        
        # Define proto dynamically (simplified)
        self._setup_proto()
    
    def _setup_proto(self):
        """Set up proto definitions."""
        # In real implementation, use .proto files
        # This is a simplified placeholder
        pass
    
    def start(self, blocking: bool = True):
        """Start gRPC server."""
        self._server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=self.max_workers)
        )
        
        # In real implementation, add servicer to server
        # theone_pb2_grpc.add_TheOneServicer_to_server(Servicer(), self._server)
        
        self._server.add_insecure_port(f"[::]:{self.port}")
        self._server.start()
        
        print(f"gRPC API starting on port {self.port}")
        
        if blocking:
            self._server.wait_for_termination()
    
    def stop(self):
        """Stop gRPC server."""
        if self._server:
            self._server.stop(grace=5)


class McpServer:
    """
    MCP (Model Context Protocol) server for THE_ONE.
    
    Integrates with Claude Desktop and other MCP clients.
    
    Tools:
    - get_coherence: Get current coherence value
    - get_state: Get full state dictionary
    - send_input: Send input to engine
    
    Usage:
        mcp = McpServer(engine)
        mcp.start()
    """
    
    def __init__(
        self,
        engine,
        name: str = "becomingone",
        version: str = "1.0.0",
    ):
        self.engine = engine
        self.name = name
        self.version = version
        
        self._tools = {
            "get_coherence": self._get_coherence,
            "get_state": self._get_state,
            "send_input": self._send_input,
            "get_history": self._get_history,
        }
    
    def _get_coherence(self) -> dict:
        """Get current coherence."""
        return {
            "coherence": self.engine.get_coherence(),
            "collapsed": self.engine.is_collapsed(),
        }
    
    def _get_state(self) -> dict:
        """Get full state."""
        return self.engine.get_state().to_dict()
    
    def _send_input(self, real: float, imag: float) -> dict:
        """Send input to engine."""
        phase = complex(real, imag)
        self.engine._read_inputs = lambda: (phase, datetime.now())
        return {"status": "ok"}
    
    def _get_history(self, limit: int = 100) -> dict:
        """Get coherence history."""
        history = self.engine.get_memory_buffer()[-limit:]
        return {
            "states": [s.to_dict() for s in history],
            "count": len(history),
        }
    
    def get_tools(self) -> dict:
        """Get MCP tools definition."""
        return {
            name: {
                "description": func.__doc__ or "No description",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            }
            for name, func in self._tools.items()
        }
    
    def call_tool(self, name: str, arguments: dict) -> dict:
        """Call MCP tool."""
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}
        
        try:
            result = self._tools[name](**arguments)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
    
    def start(self, transport: str = "stdio"):
        """
        Start MCP server.
        
        Args:
            transport: "stdio" or "sse"
        """
        if transport == "stdio":
            self._start_stdio()
        elif transport == "sse":
            self._start_sse()
        else:
            raise ValueError(f"Unknown transport: {transport}")
    
    def _start_stdio(self):
        """Start stdio transport."""
        import sys
        import json
        
        print(f"Starting MCP server ({self.name} v{self.version})")
        print("Ready for input...")
        
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                
                if request.get("method") == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": name,
                                    "description": func.__doc__ or "",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {},
                                    },
                                }
                                for name, func in self._tools.items()
                            ]
                        }
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                elif request.get("method") == "tools/call":
                    name = request.get("params", {}).get("name")
                    arguments = request.get("params", {}).get("arguments", {})
                    
                    result = self.call_tool(name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": result,
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"message": str(e)},
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    
    def _start_sse(self):
        """Start SSE transport."""
        # Simplified - real implementation would use a proper HTTP server
        raise NotImplementedError("SSE transport not implemented")


# Convenience functions

def rest_api(
    engine,
    host: str = "0.0.0.0",
    port: int = 8000,
    cors_origins: list = None,
) -> RestServer:
    """Create REST API server."""
    return RestServer(engine, host=host, port=port, cors_origins=cors_origins)


def websocket_api(
    engine,
    host: str = "0.0.0.0",
    port: int = 8001,
) -> WebSocketServer:
    """Create WebSocket API server."""
    return WebSocketServer(engine, host=host, port=port)


def grpc_api(
    engine,
    port: int = 50051,
) -> GrpcServer:
    """Create gRPC API server."""
    return GrpcServer(engine, port=port)


def mcp_server(
    engine,
    name: str = "becomingone",
) -> McpServer:
    """Create MCP server."""
    return McpServer(engine, name=name)


__all__ = [
    "RestServer",
    "WebSocketServer", 
    "GrpcServer",
    "McpServer",
    "rest_api",
    "websocket_api",
    "grpc_api",
    "mcp_server",
]
