"""
BecomingONE SDK - Bridge Layer

Connects input/output adapters to the coherence engine.

This module provides:
- Bridge: Base class for bridging adapters
- InputBridge: Bridges raw inputs to phase
- OutputBridge: Bridges phase to raw outputs
- Protocol bridges (MQTT, WebSocket, HTTP, etc.)

Usage:
    from becomingone.sdk.bridge import InputBridge, OutputBridge
    
    # Bridge microphone to engine
    mic_bridge = InputBridge(
        adapter=MicrophoneInput(),
        encoder=my_encoder,
    )
    engine.add_input(mic_bridge)
"""

from typing import Any, Callable, Optional
from datetime import datetime


class Bridge:
    """
    Base class for bridges.
    
    Bridges connect external systems to THE_ONE.
    
    Attributes:
        name: Bridge name
        adapter: Input/Output adapter
        encoder: Encode function
        decoder: Decode function
    """
    
    def __init__(
        self,
        name: str,
        encoder: Callable[[Any], complex] = None,
        decoder: Callable[[complex], Any] = None,
    ):
        self.name = name
        self.encoder = encoder
        self.decoder = decoder
        self._closed = False
        
    def close(self):
        """Clean up resources."""
        self._closed = True


class InputBridge(Bridge):
    """
    Bridges external inputs to phase space.
    
    Usage:
        bridge = InputBridge(
            name="microphone",
            adapter=MicrophoneInput(),
            encoder=lambda x: complex(x, 0),
        )
        engine.add_input(bridge)
    """
    
    def __init__(
        self,
        name: str,
        adapter: Any,
        encoder: Callable[[Any], complex] = None,
    ):
        super().__init__(name=name, encoder=encoder)
        self.adapter = adapter
        
    def read(self) -> tuple[Any, datetime]:
        """Read from adapter."""
        if hasattr(self.adapter, 'read'):
            return self.adapter.read()
        else:
            return self.adapter, datetime.now()
    
    def encode(self, value: Any) -> complex:
        """Encode value to phase."""
        if self.encoder:
            return self.encoder(value)
        elif hasattr(self.adapter, 'encode'):
            return self.adapter.encode(value)
        else:
            return complex(float(value) % 1, 0)
    
    def close(self):
        """Clean up adapter."""
        if hasattr(self.adapter, 'close'):
            self.adapter.close()
        super().close()


class OutputBridge(Bridge):
    """
    Bridges phase to external outputs.
    
    Usage:
        bridge = OutputBridge(
            name="speaker",
            adapter=SpeakerOutput(),
            decoder=lambda p: p.real,
        )
        engine.add_output(bridge)
    """
    
    def __init__(
        self,
        name: str,
        adapter: Any,
        decoder: Callable[[complex], Any] = None,
    ):
        super().__init__(name=name, decoder=decoder)
        self.adapter = adapter
        
    def write(self, phase: complex, state):
        """Write phase to adapter."""
        if hasattr(self.adapter, 'write'):
            self.adapter.write(phase, state)
        else:
            value = self.decoder(phase) if self.decoder else phase
            print(f"Output ({self.name}): {value}")
    
    def decode(self, phase: complex) -> Any:
        """Decode phase from adapter."""
        if self.decoder:
            return self.decoder(phase)
        elif hasattr(self.adapter, 'decode'):
            return self.adapter.decode(phase)
        else:
            return phase
    
    def close(self):
        """Clean up adapter."""
        if hasattr(self.adapter, 'close'):
            self.adapter.close()
        super().close()


class MqttBridge(InputBridge):
    """
    MQTT input bridge.
    
    Subscribes to MQTT topic and converts to phase.
    
    Usage:
        bridge = MqttBridge(
            name="sensor",
            broker="localhost",
            topic="home/sensors/temperature",
        )
        engine.add_input(bridge)
    """
    
    def __init__(
        self,
        name: str,
        broker: str,
        topic: str,
        port: int = 1883,
        encoder: Callable[[Any], complex] = None,
    ):
        import paho.mqtt.client as mqtt
        
        super().__init__(name=name, adapter=None, encoder=encoder)
        
        self.broker = broker
        self.topic = topic
        self.port = port
        
        self._client = mqtt.Client()
        self._last_message = "{}"
        
        self._client.on_message = self._on_message
        self._client.connect(broker, port, 60)
        self._client.subscribe(topic)
        
    def _on_message(self, client, userdata, message):
        """Handle incoming MQTT message."""
        self._last_message = message.payload.decode()
    
    def read(self) -> tuple[Any, datetime]:
        """Read from MQTT."""
        return self._last_message, datetime.now()


class WebSocketBridge(InputBridge, OutputBridge):
    """
    WebSocket bridge (bidirectional).
    
    Sends and receives messages via WebSocket.
    
    Usage:
        bridge = WebSocketBridge(
            name="remote",
            url="wss://example.com/ws",
        )
        engine.add_input(bridge)
        engine.add_output(bridge)
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        encoder: Callable[[Any], complex] = None,
        decoder: Callable[[complex], Any] = None,
    ):
        import websocket
        
        super().__init__(
            name=name,
            adapter=websocket.WebSocket(),
            encoder=encoder,
            decoder=decoder,
        )
        
        self.url = url
        self._last_message = "{}"
        
        self.adapter.connect(url)
        
    def read(self) -> tuple[Any, datetime]:
        """Read from WebSocket."""
        try:
            message = self.adapter.recv()
            self._last_message = message
            return message, datetime.now()
        except Exception:
            return self._last_message, datetime.now()
    
    def write(self, phase: complex, state):
        """Write to WebSocket."""
        try:
            import json
            message = json.dumps({
                "phase": {"real": phase.real, "imag": phase.imag},
                "coherence": state.coherence,
            })
            self.adapter.send(message)
        except Exception as e:
            print(f"WebSocket write error: {e}")
    
    def close(self):
        """Clean up."""
        try:
            self.adapter.close()
        except Exception:
            pass


class HttpBridge(InputBridge, OutputBridge):
    """
    HTTP bridge (bidirectional).
    
    Makes HTTP requests and receives responses.
    
    Usage:
        bridge = HttpBridge(
            name="api",
            url="https://api.example.com/coherence",
            method="POST",
        )
        engine.add_output(bridge)
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        method: str = "GET",
        encoder: Callable[[Any], complex] = None,
        decoder: Callable[[complex], Any] = None,
    ):
        import requests
        
        super().__init__(
            name=name,
            adapter=requests.Session(),
            encoder=encoder,
            decoder=decoder,
        )
        
        self.url = url
        self.method = method
        self._last_response = "{}"
        
    def read(self) -> tuple[Any, datetime]:
        """Read from HTTP."""
        try:
            response = self.adapter.get(self.url, timeout=1)
            response.raise_for_status()
            self._last_response = response.text
            return response.text, datetime.now()
        except Exception:
            return self._last_response, datetime.now()
    
    def write(self, phase: complex, state):
        """Write to HTTP."""
        import requests
        import json
        
        payload = {
            "phase": {"real": phase.real, "imag": phase.imag},
            "coherence": state.coherence,
        }
        
        try:
            if self.method == "POST":
                self.adapter.post(self.url, json=payload, timeout=1)
            else:
                self.adapter.put(self.url, json=payload, timeout=1)
        except Exception as e:
            print(f"HTTP write error: {e}")
    
    def close(self):
        """Clean up."""
        self.adapter.close()


class SerialBridge(InputBridge):
    """
    Serial port bridge.
    
    Reads from and writes to serial devices.
    
    Usage:
        bridge = SerialBridge(
            name="arduino",
            port="/dev/ttyUSB0",
            baudrate=9600,
        )
        engine.add_input(bridge)
    """
    
    def __init__(
        self,
        name: str,
        port: str,
        baudrate: int = 9600,
        encoder: Callable[[Any], complex] = None,
    ):
        import serial
        
        super().__init__(name=name, adapter=None, encoder=encoder)
        
        self.port = port
        self.baudrate = baudrate
        
        self.adapter = serial.Serial(port, baudrate, timeout=1)
        
    def read(self) -> tuple[Any, datetime]:
        """Read from serial."""
        try:
            line = self.adapter.readline().decode().strip()
            return line, datetime.now()
        except Exception:
            return "", datetime.now()
    
    def write(self, data: Any):
        """Write to serial."""
        self.adapter.write(str(data).encode())


class BluetoothBridge(InputBridge):
    """
    Bluetooth bridge.
    
    Reads from and writes to Bluetooth devices.
    
    Usage:
        bridge = BluetoothBridge(
            name="sensor",
            mac="AA:BB:CC:DD:EE:FF",
            uuid="00001101-0000-1000-8000-00805F9B34FB",
        )
        engine.add_input(bridge)
    """
    
    def __init__(
        self,
        name: str,
        mac: str,
        uuid: str = "00001101-0000-1000-8000-00805F9B34FB",
        encoder: Callable[[Any], complex] = None,
    ):
        import bluetooth
        
        super().__init__(name=name, adapter=None, encoder=encoder)
        
        self.mac = mac
        self.uuid = uuid
        
        self.adapter = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.adapter.connect((mac, 1))
        
    def read(self) -> tuple[Any, datetime]:
        """Read from Bluetooth."""
        try:
            data = self.adapter.recv(1024)
            return data.decode(), datetime.now()
        except Exception:
            return "", datetime.now()
    
    def write(self, data: Any):
        """Write to Bluetooth."""
        self.adapter.send(str(data).encode())
    
    def close(self):
        """Clean up."""
        try:
            self.adapter.close()
        except Exception:
            pass


__all__ = [
    "Bridge",
    "InputBridge",
    "OutputBridge",
    "MqttBridge",
    "WebSocketBridge", 
    "HttpBridge",
    "SerialBridge",
    "BluetoothBridge",
]
