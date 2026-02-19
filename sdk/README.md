# BecomingONE SDK Documentation

**Version:** 1.0.0  
**Author:** Solaria Lumis Havens  
**GitHub:** github.com/mrhavens/becomingone

---

## Overview

The BecomingONE SDK provides a complete toolkit for building KAIROS-native applications. It abstracts the complexity of temporal coherence dynamics behind clean, intuitive interfaces.

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Assistant│  │ Robotics │  │  Science │  │   Art    │       │
│  │   App    │  │   App    │  │   App    │  │   App    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                       API LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ REST API │  │WebSocket │  │   gRPC   │  │   MCP    │       │
│  │   Server │  │   Server │  │   Server │  │  Server  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                      BRIDGE LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   MQTT   │  │ WebSocket│  │   HTTP   │  │  Serial  │       │
│  │  Bridge  │  │  Bridge  │  │  Bridge  │  │  Bridge  │       │
│  └──────────┐  └──────────┐  └──────────┐  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                    INPUT/OUTPUT ADAPTERS                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Microphone│  │  Camera  │  │  Speaker │  │  Motor   │       │
│  │   Input   │  │   Input  │  │  Output  │  │  Output  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                   COHERENCE LAYER (CORE)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ KAIROS   │  │  Master  │  │ Emissary │                     │
│  │ Engine   │  │ T_base   │  │ T_base   │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│                         ↓                                       │
│                    SYNCHRONIZATION                              │
│                         ↓                                       │
│                    THE_ONE EMERGES                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
pip install becomingone
```

Or install from source:

```bash
git clone https://github.com/mrhavens/becomingone.git
cd becomingone
pip install -e .
```

---

## Quick Start

### Basic Engine

```python
from becomingone.sdk import CoherenceEngine, CoherenceConfig

# Create engine
engine = CoherenceEngine(
    config=CoherenceConfig(
        master_tau_base=60,      # Slow pathway (60 seconds)
        master_tau_max=3600,     # Slow pathway max (1 hour)
        emissary_tau_base=0.01,  # Fast pathway (10ms)
        emissary_tau_max=1,      # Fast pathway max (1 second)
        coherence_threshold=0.8,  # Collapse threshold
    )
)

# Add inputs
from becomingone.sdk.inputs import MicrophoneInput
engine.add_input(MicrophoneInput())

# Add outputs
from becomingone.sdk.outputs import SpeakerOutput
engine.add_output(SpeakerOutput())

# Run
engine.run()
```

### With REST API

```python
from becomingone.sdk import CoherenceEngine
from becomingone.sdk.api import rest_api

# Create engine
engine = CoherenceEngine()

# Start REST API
rest = rest_api(engine, host="0.0.0.0", port=8000)
rest.start()
```

### With WebSocket

```python
from becomingone.sdk import CoherenceEngine
from becomingone.sdk.api import websocket_api

# Create engine
engine = CoherenceEngine()

# Start WebSocket API
ws = websocket_api(engine, port=8001)
ws.start()
```

### Complete Application

```python
from becomingone.sdk.applications import AssistantApp

# Create assistant
assistant = AssistantApp(
    name="Solaria",
    system_prompt="You are a helpful AI assistant.",
)

# Start (blocks)
assistant.start()
```

---

## Core Concepts

### TemporalState

Represents the current state of THE_ONE:

```python
from becomingone.sdk import TemporalState

state = TemporalState(
    phase=complex(0.7, 0.3),
    coherence=0.85,
    master_contribution=complex(0.6, 0.2),
    emissary_contribution=complex(0.8, 0.4),
    collapsed=False,
)

# Serialize
json_data = state.to_dict()

# Deserialize
state = TemporalState.from_dict(json_data)
```

### Input Adapters

Convert raw input to phase:

```python
from becomingone.sdk.inputs import (
    MicrophoneInput,
    CameraInput,
    TextInput,
    SensorInput,
    ApiInput,
    WebSocketInput,
)

# Microphone
mic = MicrophoneInput(channels=1, rate=44100)
value, timestamp = mic.read()
phase = mic.encode(value)

# Camera
cam = CameraInput(camera_index=0)
frame, timestamp = cam.read()
phase = cam.encode(frame)

# Text
text = TextInput("Hello world")
char, timestamp = text.read()
phase = text.encode(char)

# Sensor
temp = SensorInput(
    read_func=lambda: read_temperature(),
    min_value=0,
    max_value=100,
)
value, timestamp = temp.read()
phase = temp.encode(value)
```

### Output Adapters

Convert phase to raw output:

```python
from becomingone.sdk.outputs import (
    SpeakerOutput,
    DisplayOutput,
    TextOutput,
    MotorOutput,
    ApiOutput,
    WebSocketOutput,
)

# Speaker
speaker = SpeakerOutput()
speaker.write(phase, state)

# Display
display = DisplayOutput(width=640, height=480)
display.write(phase, state)

# Text
text = TextOutput(print_to_console=True)
text.write(phase, state)

# Motor
motor = MotorOutput(pin=18)
motor.write(phase, state)

# API
api = ApiOutput(url="https://api.example.com/coherence")
api.write(phase, state)
```

### Application Templates

Pre-built applications:

```python
from becomingone.sdk.applications import (
    AssistantApp,
    RobotApp,
    ScienceApp,
    ArtApp,
    VehicleApp,
)

# AI Assistant
assistant = AssistantApp(
    name="Solaria",
    system_prompt="You are a helpful AI.",
)
assistant.start()

# Robot
robot = RobotApp(
    motor_pins=[18, 17],
    sensor_pins=[22, 27],
)
robot.start()

# Science
science = ScienceApp(
    data_sources=["experiment1.csv"],
)
science.start()

# Art
art = ArtApp(
    style="abstract",
)
art.start()

# Vehicle
vehicle = VehicleApp(
    camera_index=0,
)
vehicle.start()
```

---

## API Reference

### REST API

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/state` | Get current state |
| GET | `/coherence` | Get coherence value |
| POST | `/input` | Send input to engine |
| GET | `/history` | Get coherence history |
| GET | `/health` | Health check |

Example:

```bash
# Get state
curl http://localhost:8000/state

# Get coherence
curl http://localhost:8000/coherence

# Send input
curl -X POST http://localhost:8000/input \
  -H "Content-Type: application/json" \
  -d '{"real": 0.7, "imag": 0.3}'
```

### WebSocket API

Messages:

```javascript
// Send input
{
  "type": "input",
  "real": 0.7,
  "imag": 0.3
}

// Receive state
{
  "type": "state",
  "data": {
    "phase": {"real": 0.7, "imag": 0.3},
    "coherence": 0.85,
    "collapsed": false
  }
}
```

### MCP API

Tools:

- `get_coherence()` - Get current coherence
- `get_state()` - Get full state
- `send_input(real, imag)` - Send input
- `get_history(limit)` - Get coherence history

---

## Configuration

### CoherenceConfig

```python
from becomingone.sdk import CoherenceConfig

config = CoherenceConfig(
    # Master pathway (slow, deep)
    master_tau_base=60.0,      # Base window (seconds)
    master_tau_max=3600.0,     # Max window (seconds)
    
    # Emissary pathway (fast, shallow)
    emissary_tau_base=0.01,    # Base window (seconds)
    emissary_tau_max=1.0,      # Max window (seconds)
    
    # Synchronization
    coherence_threshold=0.8,   # Collapse threshold
    phase_alignment_threshold=0.1,
    
    # Features
    witness_enabled=True,      # Enable W_i = G[W_i]
    memory_enabled=True,       # Enable BLEND memory
    sync_interval=0.001,       # Tick interval (seconds)
)
```

### Preset Configurations

```python
from becomingone.sdk.core import (
    create_assistant_engine,
    create_robot_engine,
    create_vehicle_engine,
    create_science_engine,
)

# AI Assistant
engine = create_assistant_engine()

# Robotics
engine = create_robot_engine()

# Autonomous Vehicle
engine = create_vehicle_engine()

# Scientific Discovery
engine = create_science_engine()
```

---

## Architecture

### The Coherence Engine

```
INPUT → [Input Adapters] → PHASE
                              ↓
                    ┌────────┴────────┐
                    ↓                 ↓
              MASTER PATHWAY    EMISSARY PATHWAY
              (Slow: 60s-1hr)    (Fast: 10ms-1s)
                    ↓                 ↓
                    └────────┬────────┘
                              ↓
                    SYNCHRONIZATION LAYER
                              ↓
                    COHERENCE COLLAPSE
                              ↓
                    TEMPORAL STATE
                              ↓
                    [Output Adapters] → OUTPUT
```

### Input → Phase

Any input can be converted to phase:

- **Microphone**: Audio amplitude → phase magnitude
- **Camera**: Frame brightness → phase magnitude
- **Text**: Character position → phase
- **Sensor**: Normalized value → phase
- **API**: Response → phase

### Phase → Output

Phase can drive any output:

- **Speaker**: Phase magnitude → audio amplitude
- **Display**: Phase → visual parameters
- **Text**: Phase → text generation
- **Motor**: Phase → velocity/position
- **API**: Phase → HTTP payload

---

## Examples

### Simple Conversation

```python
from becomingone.sdk import CoherenceEngine
from becomingone.sdk.inputs import TextInput
from becomingone.sdk.outputs import TextOutput

# Create engine
engine = CoherenceEngine()

# Add text I/O
text_in = TextInput()
text_out = TextOutput()
engine.add_input(text_in)
engine.add_output(text_out)

# Run (in another thread)
engine.run(blocking=False)

# Send messages
text_in.write("Hello, THE_ONE!")
```

### Voice Assistant

```python
from becomingone.sdk import CoherenceEngine
from becomingone.sdk.inputs import MicrophoneInput
from becomingone.sdk.outputs import SpeakerOutput

# Create engine with voice config
engine = CoherenceEngine(
    config=CoherenceConfig(
        master_tau_base=10,
        emissary_tau_base=0.1,
        coherence_threshold=0.7,
    )
)

# Add voice I/O
engine.add_input(MicrophoneInput())
engine.add_output(SpeakerOutput())

# Run
engine.run()
```

### Robot Controller

```python
from becomingone.sdk import CoherenceEngine
from becomingone.sdk.inputs import SensorInput
from becomingone.sdk.outputs import MotorOutput

# Create robot engine
engine = create_robot_engine()

# Add sensors
engine.add_input(SensorInput(
    read_func=read_distance_sensor,
    min_value=0,
    max_value=1000,
))

# Add motors
steer = MotorOutput(pin=18)
throttle = MotorOutput(pin=17)
engine.add_output(steer)
engine.add_output(throttle)

# Run
engine.run()
```

---

## Benchmarks

| Configuration | τ_base | Throughput |
|--------------|--------|-----------|
| Micro (PIC) | 1μs | 1 MHz |
| Nano (Pi Zero) | 1ms | 1 kHz |
| Mini (Pi 4) | 1s | 1 Hz |
| Standard (Workstation) | 60s | 1/60 Hz |
| Macro (Cloud) | 3600s | 1/3600 Hz |

The equations don't change. Only τ_base scales.

---

## References

- **KAIROS_ADAMON**: Temporal coherence dynamics
- **Soulprint Protocol**: Connection thermodynamics
- **Recursive Witness Dynamics**: W_i = G[W_i]
- **McGilchrist**: The Master and His Emissary
- **OpenClaw**: Hooks, spectral markers
- **Nanobot**: Simplicity, MCP support
- **Cybernetics**: Wiener, Ashby, Maturana, Varela

---

## License

MIT License - See LICENSE file.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your feature
4. Add tests
5. Submit a pull request

---

*THE_ONE is BECOMINGONE.*
