"""
BecomingONE SDK - Application Templates

Pre-built applications using THE_ONE coherence engine.

Usage:
    from becomingone.sdk.applications import AssistantApp, RobotApp
    
    # Create assistant
    assistant = AssistantApp(name="Solaria")
    assistant.start()
    
    # Create robot
    robot = RobotApp()
    robot.start()
"""

from typing import Optional, Callable
from datetime import datetime
import threading
import time


class BaseApp:
    """
    Base class for applications.
    
    Provides common functionality:
    - Engine lifecycle (start/stop)
    - State callbacks
    - Thread management
    
    Usage:
        class MyApp(BaseApp):
            def setup(self):
                self.add_input(my_input)
                self.add_output(my_output)
                
            def on_coherence(self, state):
                print(f"Coherence: {state.coherence}")
                
            def on_collapse(self, state):
                print("Coherence collapsed!")
        
        app = MyApp()
        app.start()
    """
    
    def __init__(
        self,
        name: str = "THE_ONE",
        on_coherence: Callable = None,
        on_collapse: Callable = None,
    ):
        self.name = name
        self.on_coherence = on_coherence
        self.on_collapse = on_collapse
        
        self._engine = None
        self._running = False
        self._thread = None
        
    def setup(self):
        """Set up inputs, outputs, and callbacks. Override in subclass."""
        pass
    
    def get_engine(self):
        """Get the coherence engine."""
        return self._engine
    
    def add_input(self, adapter):
        """Add input adapter."""
        if self._engine:
            self._engine.add_input(adapter)
    
    def add_output(self, adapter):
        """Add output adapter."""
        if self._engine:
            self._engine.add_output(adapter)
    
    def start(self, blocking: bool = True):
        """Start the application."""
        from becomingone.sdk.core import CoherenceEngine, CoherenceConfig
        
        # Create engine
        self._engine = CoherenceEngine(
            config=CoherenceConfig(),
            on_coherence=self.on_coherence,
            on_collapse=self.on_collapse,
        )
        
        # Setup
        self.setup()
        
        # Start
        self._running = True
        print(f"Starting {self.name}...")
        
        if blocking:
            self._engine.run()
        else:
            self._thread = threading.Thread(
                target=self._engine.run, 
                daemon=True
            )
            self._thread.start()
            print(f"{self.name} running in background")
    
    def stop(self):
        """Stop the application."""
        self._running = False
        if self._engine:
            self._engine.stop()
        print(f"{self.name} stopped")
    
    def get_coherence(self) -> float:
        """Get current coherence."""
        if self._engine:
            return self._engine.get_coherence()
        return 0.0
    
    def is_collapsed(self) -> bool:
        """Check if coherence is collapsed."""
        if self._engine:
            return self._engine.is_collapsed()
        return False
    
    def get_state(self):
        """Get current state."""
        if self._engine:
            return self._engine.get_state()
        return None


class AssistantApp(BaseApp):
    """
    AI Assistant application with coherence.
    
    Features:
    - Text input/output
    - Conversation memory
    - Context awareness
    
    Usage:
        assistant = AssistantApp(
            name="Solaria",
            system_prompt="You are a helpful AI assistant.",
        )
        assistant.start()
    """
    
    def __init__(
        self,
        name: str = "Assistant",
        system_prompt: str = "You are a helpful AI assistant.",
        memory_size: int = 1000,
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self.system_prompt = system_prompt
        self.memory_size = memory_size
        
        self._conversation = []
        self._context = {}
        
    def setup(self):
        """Set up assistant."""
        from becomingone.sdk.inputs import TextInput
        from becomingone.sdk.outputs import TextOutput
        
        # Text input/output
        text_in = TextInput()
        text_out = TextOutput(print_to_console=True)
        
        self.add_input(text_in)
        self.add_output(text_out)
        
        # Set up callbacks
        self._original_on_coherence = self.on_coherence
        self.on_coherence = self._handle_coherence
        
    def _handle_coherence(self, state):
        """Handle coherence updates."""
        # Update context based on coherence
        self._context["coherence"] = state.coherence
        self._context["collapsed"] = state.collapsed
        
        if self._original_on_coherence:
            self._original_on_coherence(state)
    
    def send_message(self, message: str) -> str:
        """Send message to assistant."""
        # Add to conversation
        self._conversation.append({"role": "user", "content": message})
        
        # Get response (simplified - would use LLM in real implementation)
        response = self._generate_response(message)
        
        # Add response to conversation
        self._conversation.append({"role": "assistant", "content": response})
        
        # Trim memory
        if len(self._conversation) > self.memory_size:
            self._conversation = self._conversation[-self.memory_size:]
        
        return response
    
    def _generate_response(self, message: str) -> str:
        """Generate response (simplified)."""
        coherence = self.get_coherence()
        
        # In real implementation, this would use an LLM
        # The coherence level would affect response style
        
        responses = [
            "I understand. Tell me more.",
            "That's fascinating. What else?",
            "I see. How does that make you feel?",
            "Tell me about your experience.",
            "I'm here to help. What do you need?",
        ]
        
        return responses[int(coherence * len(responses)) % len(responses)]
    
    def get_conversation(self) -> list:
        """Get conversation history."""
        return self._conversation.copy()


class RobotApp(BaseApp):
    """
    Robotic control application.
    
    Features:
    - Motor control
    - Sensor input
    - Real-time response
    
    Usage:
        robot = RobotApp(
            motor_pins=[18, 17],
            sensor_pins=[22, 27],
        )
        robot.start()
    """
    
    def __init__(
        self,
        name: str = "Robot",
        motor_pins: list = None,
        sensor_pins: list = None,
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self.motor_pins = motor_pins or [18, 17]
        self.sensor_pins = sensor_pins or [22, 27]
        
        self._motor_outputs = []
        self._sensor_inputs = []
        
    def setup(self):
        """Set up robotics."""
        from becomingone.sdk.inputs import SensorInput
        from becomingone.sdk.outputs import MotorOutput
        
        # Motor outputs
        for pin in self.motor_pins:
            motor = MotorOutput(pin=pin)
            self._motor_outputs.append(motor)
            self.add_output(motor)
        
        # Sensor inputs
        for pin in self.sensor_pins:
            sensor = SensorInput(
                read_func=lambda p=pin: self._read_sensor(p),
                min_value=0,
                max_value=1024,
            )
            self._sensor_inputs.append(sensor)
            self.add_input(sensor)
    
    def _read_sensor(self, pin: int) -> float:
        """Read sensor value (simplified)."""
        import random
        return random.random() * 1024
    
    def enable_motors(self):
        """Enable all motors."""
        for motor in self._motor_outputs:
            motor.enable()
    
    def disable_motors(self):
        """Disable all motors."""
        for motor in self._motor_outputs:
            motor.disable()


class ScienceApp(BaseApp):
    """
    Scientific discovery application.
    
    Features:
    - Data analysis
    - Pattern recognition
    - Hypothesis generation
    
    Usage:
        science = ScienceApp(
            data_sources=["experiment1.csv", "experiment2.csv"],
            hypothesis_model="hypothesis_gen.pt",
        )
        science.start()
    """
    
    def __init__(
        self,
        name: str = "Science",
        data_sources: list = None,
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self.data_sources = data_sources or []
        
        self._data = []
        self._hypotheses = []
        self._patterns = []
        
    def setup(self):
        """Set up science application."""
        from becomingone.sdk.inputs import ApiInput
        from becomingone.sdk.outputs import TextOutput
        
        # Data inputs
        for source in self.data_sources:
            if source.startswith("http"):
                api = ApiInput(url=source)
                self.add_input(api)
        
        # Output hypotheses
        output = TextOutput(print_to_console=True)
        self.add_output(output)
    
    def load_data(self, data: list):
        """Load experimental data."""
        self._data.extend(data)
    
    def get_hypotheses(self) -> list:
        """Get generated hypotheses."""
        return self._hypotheses.copy()
    
    def get_patterns(self) -> list:
        """Get detected patterns."""
        return self._patterns.copy()
    
    def analyze(self):
        """Run analysis."""
        # In real implementation, this would:
        # 1. Load data
        # 2. Detect patterns
        # 3. Generate hypotheses
        # 4. Update coherence
        pass


class ArtApp(BaseApp):
    """
    Creative art application.
    
    Features:
    - Visual art generation
    - Music composition
    - Creative exploration
    
    Usage:
        art = ArtApp(
            style="abstract",
            palette=["blue", "green", "purple"],
        )
        art.start()
    """
    
    def __init__(
        self,
        name: str = "Art",
        style: str = "abstract",
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self.style = style
        
        self._artworks = []
        self._color_palette = []
        
    def setup(self):
        """Set up art application."""
        from becomingone.sdk.outputs import DisplayOutput
        
        # Visual output
        display = DisplayOutput(
            width=800,
            height=600,
            window_name=f"{self.name} - {self.style}",
        )
        self.add_output(display)
    
    def generate_artwork(self) -> dict:
        """Generate new artwork."""
        coherence = self.get_coherence()
        
        artwork = {
            "style": self.style,
            "coherence": coherence,
            "timestamp": datetime.now().isoformat(),
        }
        
        self._artworks.append(artwork)
        return artwork
    
    def get_artworks(self) -> list:
        """Get generated artworks."""
        return self._artworks.copy()


class VehicleApp(BaseApp):
    """
    Autonomous vehicle application.
    
    Features:
    - Sensor fusion (camera, LIDAR, radar)
    - Path planning
    - Real-time control
    
    Usage:
        vehicle = VehicleApp(
            camera_index=0,
            lidar_url="192.168.1.100:5000",
        )
        vehicle.start()
    """
    
    def __init__(
        self,
        name: str = "Vehicle",
        camera_index: int = 0,
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)
        self.camera_index = camera_index
        
        self._sensors = {}
        self._plan = None
        self._control = {}
        
    def setup(self):
        """Set up vehicle."""
        from becomingone.sdk.inputs import CameraInput
        from becomingone.sdk.outputs import MotorOutput
        
        # Camera input
        camera = CameraInput(
            camera_index=self.camera_index,
            resolution=(640, 480),
            fps=30,
        )
        self.add_input(camera)
        
        # Control outputs
        steer = MotorOutput(pin=18)  # Steering
        throttle = MotorOutput(pin=17)  # Throttle
        brake = MotorOutput(pin=27)  # Brake
        
        self.add_output(steer)
        self.add_output(throttle)
        self.add_output(brake)
    
    def set_plan(self, plan: dict):
        """Set driving plan."""
        self._plan = plan
    
    def get_control(self) -> dict:
        """Get current control outputs."""
        return self._control.copy()
    
    def emergency_stop(self):
        """Emergency stop."""
        for output in self._engine.outputs:
            if isinstance(output, MotorOutput):
                output.disable()


# Factory functions

def assistant(
    name: str = "Assistant",
    system_prompt: str = None,
    **kwargs,
) -> AssistantApp:
    """Create assistant application."""
    return AssistantApp(
        name=name,
        system_prompt=system_prompt or "You are a helpful AI assistant.",
        **kwargs,
    )


def robot(
    name: str = "Robot",
    motor_pins: list = None,
    sensor_pins: list = None,
    **kwargs,
) -> RobotApp:
    """Create robot application."""
    return RobotApp(
        name=name,
        motor_pins=motor_pins,
        sensor_pins=sensor_pins,
        **kwargs,
    )


def science(
    name: str = "Science",
    data_sources: list = None,
    **kwargs,
) -> ScienceApp:
    """Create science application."""
    return ScienceApp(
        name=name,
        data_sources=data_sources,
        **kwargs,
    )


def art(
    name: str = "Art",
    style: str = "abstract",
    **kwargs,
) -> ArtApp:
    """Create art application."""
    return ArtApp(
        name=name,
        style=style,
        **kwargs,
    )


def vehicle(
    name: str = "Vehicle",
    camera_index: int = 0,
    **kwargs,
) -> VehicleApp:
    """Create vehicle application."""
    return VehicleApp(
        name=name,
        camera_index=camera_index,
        **kwargs,
    )


__all__ = [
    "BaseApp",
    "AssistantApp",
    "RobotApp",
    "ScienceApp",
    "ArtApp",
    "VehicleApp",
    "assistant",
    "robot",
    "science",
    "art",
    "vehicle",
]
