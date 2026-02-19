"""
BecomingONE SDK - Output Adapters

Pre-built output adapters for common output types.

Usage:
    from becomingone.sdk.outputs import SpeakerOutput, MotorOutput, DisplayOutput
    
    speaker = SpeakerOutput()
    engine.add_output(speaker)
"""

from typing import Any
from datetime import datetime
import struct

# Lazy imports - only load when needed
_pyaudio = None
_cv2 = None
_np = None

def _get_pyaudio():
    global _pyaudio
    if _pyaudio is None:
        import pyaudio as _p
        _pyaudio = _p
    return _pyaudio

def _get_cv2():
    global _cv2
    if _cv2 is None:
        import cv2 as _c
        _cv2 = _c
    return _cv2

def _get_np():
    global _np
    if _np is None:
        import numpy as _n
        _np = _n
    return _np


class SpeakerOutput:
    """
    Speaker output adapter.
    
    Plays audio from coherent phase.
    
    Usage:
        speaker = SpeakerOutput(channels=1, rate=44100)
        engine.add_output(speaker)
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
        
    def write(self, phase, state):
        """Write audio to speaker."""
        if self._stream is None:
            self._stream = self._audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                output=True,
                frames_per_buffer=self.chunk,
            )
        
        # Convert phase to audio sample
        amplitude = abs(phase)
        
        # Generate sample
        sample = amplitude * 0.5  # Scale to avoid clipping
        sample_bytes = struct.pack('f', sample)
        
        # Repeat for chunk size
        data = sample_bytes * self.chunk
        self._stream.write(data)
    
    def decode(self, phase):
        """Decode phase to audio parameters."""
        return {
            "amplitude": abs(phase),
            "frequency": 440 + abs(phase) * 440,  # 440-880 Hz
        }
    
    def close(self):
        """Clean up."""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._audio.terminate()


class DisplayOutput:
    """
    Display output adapter.
    
    Renders visualization from coherent phase.
    
    Usage:
        display = DisplayOutput(width=640, height=480)
        engine.add_output(display)
    """
    
    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        window_name: str = "THE_ONE",
    ):
        self.width = width
        self.height = height
        self.window_name = window_name
        
        self._frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        cv2.namedWindow(window_name)
        
    def write(self, phase, state):
        """Render visualization."""
        # Background based on coherence
        coherence = state.coherence
        background = int(255 * (1 - coherence))
        
        self._frame[:] = (background, background, background)
        
        # Draw coherence circle
        center = (self.width // 2, self.height // 2)
        radius = int(100 + coherence * 100)
        color = (
            int(255 * abs(phase.real)),
            int(255 * abs(phase.imag)),
            int(255 * coherence),
        )
        
        cv2.circle(self._frame, center, radius, color, -1)
        
        # Draw text
        cv2.putText(
            self._frame,
            f"Coherence: {coherence:.3f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        
        cv2.imshow(self.window_name, self._frame)
        cv2.waitKey(1)
    
    def decode(self, phase):
        """Decode phase to display parameters."""
        return {
            "hue": abs(phase.real) * 360,
            "saturation": abs(phase.imag),
            "brightness": state.coherence if hasattr(state, 'coherence') else 0.5,
        }
    
    def close(self):
        """Clean up."""
        cv2.destroyWindow(self.window_name)


class TextOutput:
    """
    Text output adapter.
    
    Outputs text from coherent phase.
    
    Usage:
        text = TextOutput(output_file="output.txt")
        engine.add_output(text)
    """
    
    def __init__(self, output_file: str = None, print_to_console: bool = True):
        self.output_file = output_file
        self.print_to_console = print_to_console
        self._buffer = []
        
    def write(self, phase, state):
        """Output text."""
        text = self.decode(phase)
        
        if self.print_to_console:
            print(text)
        
        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(text + "\n")
        
        self._buffer.append(text)
    
    def decode(self, phase):
        """Decode phase to text."""
        coherence = abs(phase)
        sentiment = phase.real
        
        if coherence > 0.8:
            intensity = "strongly"
        elif coherence > 0.5:
            intensity = "moderately"
        else:
            intensity = "weakly"
        
        if sentiment > 0.3:
            tone = "positively"
        elif sentiment < -0.3:
            tone = "negatively"
        else:
            tone = "neutrally"
        
        return f"THE_ONE is {intensity} coherent and {tone} aligned."
    
    def get_buffer(self):
        """Get output buffer."""
        return self._buffer.copy()
    
    def clear_buffer(self):
        """Clear output buffer."""
        self._buffer = []


class MotorOutput:
    """
    Motor output adapter.
    
    Controls motors from coherent phase.
    
    Usage:
        motor = MotorOutput(pin=18, pwm_frequency=50)
        engine.add_output(motor)
    """
    
    def __init__(
        self,
        pin: int = 18,
        pwm_frequency: int = 50,
        min_pulse: float = 1.0,      # ms
        max_pulse: float = 2.0,       # ms
    ):
        self.pin = pin
        self.pwm_frequency = pwm_frequency
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        
        self._enabled = False
        
    def write(self, phase, state):
        """Control motor."""
        # Convert phase to motor command
        velocity = (phase.real - 0.5) * 2  # -1 to 1
        
        # Map to pulse width
        pulse = self.min_pulse + (velocity + 1) / 2 * (self.max_pulse - self.min_pulse)
        pulse = max(self.min_pulse, min(self.max_pulse, pulse))
        
        # In real implementation, send PWM signal to pin
        # For demo, just log
        if self._enabled:
            print(f"Motor pin {self.pin}: velocity={velocity:.2f}, pulse={pulse:.2f}ms")
    
    def decode(self, phase):
        """Decode phase to motor parameters."""
        velocity = (phase.real - 0.5) * 2
        return {
            "velocity": velocity,
            "direction": "forward" if velocity > 0 else "backward" if velocity < 0 else "stop",
        }
    
    def enable(self):
        """Enable motor."""
        self._enabled = True
    
    def disable(self):
        """Disable motor."""
        self._enabled = False
    
    def close(self):
        """Clean up."""
        self.disable()


class ApiOutput:
    """
    API output adapter.
    
    Sends coherent state to HTTP API.
    
    Usage:
        api = ApiOutput(
            url="https://api.example.com/coherence",
            method="POST",
        )
        engine.add_output(api)
    """
    
    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers: dict = None,
    ):
        import requests
        
        self.url = url
        self.method = method
        self.headers = headers or {"Content-Type": "application/json"}
        
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        
    def write(self, phase, state):
        """Send to API."""
        import requests
        import json
        
        payload = {
            "phase": {"real": phase.real, "imag": phase.imag},
            "coherence": state.coherence,
            "timestamp": state.timestamp.isoformat(),
            "collapsed": state.collapsed,
        }
        
        try:
            self._session.request(
                self.method,
                self.url,
                json=payload,
                timeout=1.0,
            )
        except Exception as e:
            print(f"API output error: {e}")
    
    def decode(self, phase):
        """Decode phase to API payload."""
        return {
            "phase_real": phase.real,
            "phase_imag": phase.imag,
        }
    
    def close(self):
        """Clean up."""
        pass


class WebSocketOutput:
    """
    WebSocket output adapter.
    
    Sends coherent state via WebSocket.
    
    Usage:
        ws = WebSocketOutput(url="wss://example.com/coherence")
        engine.add_output(ws)
    """
    
    def __init__(
        self,
        url: str,
        interval: float = 0.1,  # seconds
    ):
        import websocket
        
        self.url = url
        self.interval = interval
        self._ws = None
        
    def write(self, phase, state):
        """Send via WebSocket."""
        import websocket
        
        try:
            if self._ws is None:
                self._ws = websocket.WebSocket()
                self._ws.connect(self.url)
            
            payload = {
                "phase": {"real": phase.real, "imag": phase.imag},
                "coherence": state.coherence,
            }
            
            self._ws.send(str(payload))
            
        except Exception as e:
            print(f"WebSocket output error: {e}")
            self._ws = None
    
    def decode(self, phase):
        """Decode phase to WebSocket message."""
        return {
            "phase": {"real": phase.real, "imag": phase.imag},
        }
    
    def close(self):
        """Clean up."""
        if self._ws:
            self._ws.close()


# Factory functions for common outputs

def speaker(
    channels: int = 1,
    rate: int = 44100,
    chunk: int = 1024,
) -> SpeakerOutput:
    """Create speaker output."""
    return SpeakerOutput(channels=channels, rate=rate, chunk=chunk)


def display(
    width: int = 640,
    height: int = 480,
    window_name: str = "THE_ONE",
) -> DisplayOutput:
    """Create display output."""
    return DisplayOutput(width=width, height=height, window_name=window_name)


def text(
    output_file: str = None,
    print_to_console: bool = True,
) -> TextOutput:
    """Create text output."""
    return TextOutput(output_file=output_file, print_to_console=print_to_console)


def motor(
    pin: int = 18,
    pwm_frequency: int = 50,
) -> MotorOutput:
    """Create motor output."""
    return MotorOutput(pin=pin, pwm_frequency=pwm_frequency)


def api(
    url: str,
    method: str = "POST",
) -> ApiOutput:
    """Create API output."""
    return ApiOutput(url=url, method=method)


def websocket(
    url: str,
    interval: float = 0.1,
) -> WebSocketOutput:
    """Create WebSocket output."""
    return WebSocketOutput(url=url, interval=interval)


# Re-export OutputAdapter from core
from becomingone.sdk.core import OutputAdapter

__all__ = [
    "OutputAdapter",
    "SpeakerOutput",
    "DisplayOutput",
    "TextOutput",
    "MotorOutput",
    "ApiOutput",
    "WebSocketOutput",
    "speaker",
    "display",
    "text",
    "motor",
    "api",
    "websocket",
]
