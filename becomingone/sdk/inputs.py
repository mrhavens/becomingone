"""
BecomingONE SDK - Input Adapters

Pre-built input adapters for common input types.

Usage:
    from becomingone.sdk.inputs import MicrophoneInput, CameraInput, TextInput
    
    mic = MicrophoneInput()
    engine.add_input(mic)
"""

from typing import Any, Tuple
from datetime import datetime
import struct
import pyaudio
import cv2
import numpy as np


class MicrophoneInput:
    """
    Microphone input adapter.
    
    Reads audio from microphone and converts to phase.
    
    Usage:
        mic = MicrophoneInput(channels=1, rate=44100, chunk=1024)
        engine.add_input(mic)
    """
    
    def __init__(
        self,
        channels: int = 1,
        rate: int = 44100,
        chunk: int = 1024,
        format: int = pyaudio.paFloat32,
    ):
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.format = format
        
        self._audio = pyaudio.PyAudio()
        self._stream = None
        
    def _ensure_stream(self):
        """Ensure stream is open."""
        if self._stream is None:
            self._stream = self._audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk,
            )
    
    def read(self) -> Tuple[float, datetime]:
        """Read audio sample."""
        self._ensure_stream()
        data = self._stream.read(self.chunk, exception_on_overflow=False)
        
        # Convert to numpy array
        samples = np.frombuffer(data, dtype=np.float32)
        
        # Compute RMS amplitude (simplified phase)
        amplitude = np.sqrt(np.mean(samples**2))
        
        return amplitude, datetime.now()
    
    def encode(self, value: float) -> complex:
        """Convert amplitude to phase."""
        # Real = amplitude
        # Imag = frequency estimate (simplified)
        return complex(value, 0)
    
    def close(self):
        """Clean up."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._audio.terminate()


class CameraInput:
    """
    Camera input adapter.
    
    Reads frames from camera and converts to phase.
    
    Usage:
        cam = CameraInput(camera_index=0, resolution=(640, 480))
        engine.add_input(cam)
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        resolution: Tuple[int, int] = (640, 480),
        fps: int = 30,
    ):
        self.camera_index = camera_index
        self.resolution = resolution
        self.fps = fps
        
        self._cap = None
        
    def _ensure_cap(self):
        """Ensure camera is open."""
        if self._cap is None:
            self._cap = cv2.VideoCapture(self.camera_index)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self._cap.set(cv2.CAP_PROP_FPS, self.fps)
    
    def read(self) -> Tuple[np.ndarray, datetime]:
        """Read camera frame."""
        self._ensure_cap()
        ret, frame = self._cap.read()
        
        if not ret:
            return np.zeros(self.resolution), datetime.now()
        
        return frame, datetime.now()
    
    def encode(self, frame: np.ndarray) -> complex:
        """Convert frame to phase (using brightness)."""
        brightness = np.mean(frame) / 255.0
        return complex(brightness, 0)
    
    def close(self):
        """Clean up."""
        if self._cap:
            self._cap.release()


class TextInput:
    """
    Text input adapter.
    
    Reads text from stdin or string buffer.
    
    Usage:
        text = TextInput()
        engine.add_input(text)
        
        # Or use as async iterator:
        for phase in text.async_read():
            print(phase)
    """
    
    def __init__(self, initial_text: str = ""):
        self.text_buffer = initial_text
        self.position = 0
        
    def read(self) -> Tuple[str, datetime]:
        """Read next character."""
        if self.position < len(self.text_buffer):
            char = self.text_buffer[self.position]
            self.position += 1
            return char, datetime.now()
        return "", datetime.now()
    
    def encode(self, char: str) -> complex:
        """Convert character to phase."""
        if not char:
            return complex(0, 0)
        
        # Hash to get position
        position = hash(char) % 100 / 100.0
        return complex(position, 0.5)
    
    def write(self, text: str) -> None:
        """Write text to buffer."""
        self.text_buffer += text


class SensorInput:
    """
    Generic sensor input adapter.
    
    Reads from any sensor that returns numeric values.
    
    Usage:
        # Temperature sensor
        temp = SensorInput(
            read_func=lambda: read_temperature_sensor(),
            min_value=0,
            max_value=100
        )
        engine.add_input(temp)
    """
    
    def __init__(
        self,
        read_func: callable,
        min_value: float = 0,
        max_value: float = 1,
    ):
        self.read_func = read_func
        self.min_value = min_value
        self.max_value = max_value
        
    def read(self) -> Tuple[float, datetime]:
        """Read sensor value."""
        value = self.read_func()
        return value, datetime.now()
    
    def encode(self, value: float) -> complex:
        """Normalize and encode as phase."""
        normalized = (value - self.min_value) / (self.max_value - self.min_value)
        normalized = max(0, min(1, normalized))
        return complex(normalized, 0)


class ApiInput:
    """
    API input adapter.
    
    Fetches data from HTTP API and converts to phase.
    
    Usage:
        api = ApiInput(
            url="https://api.example.com/data",
            method="GET",
            interval=1.0,
        )
        engine.add_input(api)
    """
    
    def __init__(
        self,
        url: str,
        method: str = "GET",
        headers: dict = None,
        interval: float = 1.0,
        json_path: str = None,  # Path to value in JSON response
    ):
        import requests
        
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.interval = interval
        self.json_path = json_path
        
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        self._last_value = 0
        
    def read(self) -> Tuple[Any, datetime]:
        """Fetch from API."""
        import requests
        
        try:
            response = self._session.request(
                self.method,
                self.url,
                timeout=1.0,
            )
            response.raise_for_status()
            
            if self.json_path:
                import json
                data = response.json()
                
                # Navigate JSON path
                for key in self.json_path.split("."):
                    if isinstance(data, dict):
                        data = data.get(key, 0)
                    else:
                        data = 0
                
                self._last_value = data
                return data, datetime.now()
            else:
                self._last_value = response.text
                return response.text, datetime.now()
                
        except Exception as e:
            return self._last_value, datetime.now()
    
    def encode(self, value: Any) -> complex:
        """Encode API response as phase."""
        if isinstance(value, (int, float)):
            return complex(float(value) % 1, 0)
        else:
            return complex(hash(str(value)) % 100 / 100, 0)


class WebSocketInput:
    """
    WebSocket input adapter.
    
    Reads messages from WebSocket and converts to phase.
    
    Usage:
        ws = WebSocketInput(
            url="wss://echo.websocket.org",
            timeout=1.0,
        )
        engine.add_input(ws)
    """
    
    def __init__(
        self,
        url: str,
        timeout: float = 1.0,
    ):
        self.url = url
        self.timeout = timeout
        self._last_message = ""
        
    def read(self) -> Tuple[str, datetime]:
        """Read from WebSocket."""
        import websocket
        
        try:
            ws = websocket.WebSocket()
            ws.connect(self.url, timeout=self.timeout)
            message = ws.recv()
            ws.close()
            self._last_message = message
            return message, datetime.now()
        except Exception:
            return self._last_message, datetime.now()
    
    def encode(self, message: str) -> complex:
        """Encode message as phase."""
        return complex(hash(message) % 100 / 100, 0)


# Factory functions for common inputs

def microphone(
    channels: int = 1,
    rate: int = 44100,
    chunk: int = 1024,
) -> MicrophoneInput:
    """Create microphone input."""
    return MicrophoneInput(channels=channels, rate=rate, chunk=chunk)


def camera(
    camera_index: int = 0,
    resolution: Tuple[int, int] = (640, 480),
    fps: int = 30,
) -> CameraInput:
    """Create camera input."""
    return CameraInput(camera_index=camera_index, resolution=resolution, fps=fps)


def text(
    initial_text: str = "",
) -> TextInput:
    """Create text input."""
    return TextInput(initial_text=initial_text)


def sensor(
    read_func: callable,
    min_value: float = 0,
    max_value: float = 1,
) -> SensorInput:
    """Create generic sensor input."""
    return SensorInput(read_func=read_func, min_value=min_value, max_value=max_value)


def api(
    url: str,
    method: str = "GET",
    interval: float = 1.0,
    json_path: str = None,
) -> ApiInput:
    """Create API input."""
    return ApiInput(url=url, method=method, interval=interval, json_path=json_path)


def websocket(
    url: str,
    timeout: float = 1.0,
) -> WebSocketInput:
    """Create WebSocket input."""
    return WebSocketInput(url=url, timeout=timeout)


# Re-export InputAdapter from core
from becomingone.sdk.core import InputAdapter

__all__ = [
    "InputAdapter",
    "MicrophoneInput",
    "CameraInput", 
    "TextInput",
    "SensorInput",
    "ApiInput",
    "WebSocketInput",
    "microphone",
    "camera",
    "text",
    "sensor",
    "api",
    "websocket",
]
