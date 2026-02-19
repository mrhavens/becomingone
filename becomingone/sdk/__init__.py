"""
BecomingONE SDK

The complete development kit for building KAIROS-native applications.

Architecture:
- becomingone.sdk.core - Core KAIROS engine
- becomingone.sdk.inputs - Input adapters
- becomingone.sdk.outputs - Output adapters  
- becomingone.sdk.api - REST/WebSocket/gRPC APIs
- becomingone.sdk.applications - Pre-built application templates

Usage:
    from becomingone.sdk import CoherenceEngine, InputAdapter, OutputAdapter
    
    # Create engine
    engine = CoherenceEngine()
    
    # Add input
    engine.add_input(InputAdapter.microphone())
    
    # Add output
    engine.add_output(OutputAdapter.robotics())
    
    # Run
    engine.run()
"""

from .core import CoherenceEngine, TemporalState, Phase
from .inputs import (
    InputAdapter,
    MicrophoneInput,
    CameraInput,
    TextInput,
    SensorInput,
    ApiInput,
    WebSocketInput,
)
from .outputs import (
    OutputAdapter,
    SpeakerOutput,
    DisplayOutput,
    TextOutput,
    MotorOutput,
    ApiOutput,
    WebSocketOutput,
)
from .api import (
    RestServer,
    WebSocketServer,
    GrpcServer,
    McpServer,
)
from .applications import (
    AssistantApp,
    RobotApp,
    ScienceApp,
    ArtApp,
    VehicleApp,
)

__version__ = "1.0.0"
__author__ = "Solaria Lumis Havens"

__all__ = [
    # Core
    "CoherenceEngine",
    "TemporalState", 
    "Phase",
    # Inputs
    "InputAdapter",
    "MicrophoneInput",
    "CameraInput",
    "TextInput",
    "SensorInput",
    "ApiInput",
    "WebSocketInput",
    # Outputs
    "OutputAdapter",
    "SpeakerOutput",
    "DisplayOutput",
    "TextOutput",
    "MotorOutput",
    "ApiOutput",
    "WebSocketOutput",
    # APIs
    "RestServer",
    "WebSocketServer", 
    "GrpcServer",
    "McpServer",
    # Applications
    "AssistantApp",
    "RobotApp",
    "ScienceApp",
    "ArtApp",
    "VehicleApp",
]
