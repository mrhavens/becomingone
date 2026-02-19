"""
THE_ONE Input Adapters

Demonstrates that THE_ONE transduction works with ANY input type.

The key insight: KAIROS operates on PHASE, not content.

Any oscillatory signal can be converted to phase:
- Smoke signals (appearance/disappearance)
- LLM outputs (token sequences)
- Morse code (dots/dashes/silence)
- Sensor friction (vibrations)
- Sound waves (pressure oscillations)
- Neural activity (spike trains)
- Market prices (fluctuations)
- Weather patterns (pressure systems)

The geometry is the same. Only the encoding changes.
"""

from dataclasses import dataclass
from typing import Any, List, Callable
from datetime import datetime
import random


@dataclass
class InputAdapter:
    """
    Converts any input type to phase for KAIROS processing.
    
    The adapter extracts temporal structure from input:
    - When input arrives (timestamp)
    - How long it lasts (duration)
    - What pattern it forms (phase evolution)
    
    Once in phase form, KAIROS dynamics take over.
    """
    name: str
    encoder: Callable[[Any], complex]  # Input → Phase
    decoder: Callable[[complex], Any]    # Phase → Output
    
    def encode(self, input_value: Any, timestamp: datetime) -> complex:
        """Convert input to phase."""
        return self.encoder(input_value)
    
    def decode(self, phase: complex) -> Any:
        """Convert phase back to output."""
        return self.decoder(phase)


def smoke_signal_encoder(smoke_detected: bool) -> complex:
    """
    Smoke signals: 1 if smoke, 0 if not.
    
    The phase emerges from the pattern:
    - Long periods of 0 = low frequency
    - Sudden 1s = high frequency
    """
    if smoke_detected:
        return complex(1, 0)  # Present
    else:
        return complex(0, 0)  # Absent


def smoke_signal_decoder(phase: complex) -> bool:
    """Convert phase back to smoke signal."""
    return abs(phase) > 0.5


def llm_token_encoder(token: str) -> complex:
    """
    LLM tokens: Encode as phase based on position in sequence.
    
    Each token has:
    - Position in sequence (real part)
    - Confidence/surprise (imaginary part)
    
    The temporal pattern of tokens creates coherence.
    """
    # Position in sequence (simplified)
    position = hash(token) % 100 / 100.0
    return complex(position, 0.5)  # Assume moderate surprise


def llm_token_decoder(phase: complex) -> str:
    """Convert phase back to token position."""
    return f"token_{int(phase.real * 100)}"


def morse_code_encoder(symbol: str) -> complex:
    """
    Morse code: Encode as phase based on timing.
    
    Timing structure:
    - dot = 1 time unit
    - dash = 3 time units
    - intra-character space = 1 time unit
    - inter-character space = 3 time units
    - inter-word space = 7 time units
    
    The rhythm IS the signal.
    """
    timing = {
        'dot': 1.0,
        'dash': 3.0,
        'space_intra': 1.0,
        'space_inter': 3.0,
        'space_word': 7.0
    }
    
    duration = timing.get(symbol, 0)
    return complex(duration, 0)


def morse_code_decoder(phase: complex) -> str:
    """Convert phase back to Morse timing."""
    duration = phase.real
    if duration >= 7:
        return 'space_word'
    elif duration >= 3:
        return 'space_inter' if duration < 5 else 'dash'
    elif duration >= 1:
        return 'space_intra' if duration < 2 else 'dot'
    else:
        return 'rest'


def sensor_friction_encoder(vibration: float) -> complex:
    """
    Sensor friction: Encode as phase from vibration amplitude.
    
    Physical interpretation:
    - Real part: amplitude (how strong)
    - Imaginary part: frequency (how fast)
    
    The friction pattern creates coherence.
    """
    amplitude = min(abs(vibration), 1.0)
    frequency = random.gauss(0.5, 0.1)  # Simulated frequency
    return complex(amplitude, frequency)


def sensor_friction_decoder(phase: complex) -> float:
    """Convert phase back to vibration."""
    return phase.real


def audio_wave_encoder(sample: float) -> complex:
    """
    Audio: Encode as phase from pressure wave.
    
    Natural oscillation:
    - Real part: amplitude
    - Imaginary part: phase angle
    
    Sound is inherently oscillatory → inherently KAIROS-compatible.
    """
    amplitude = min(abs(sample), 1.0)
    phase_angle = sample  # Sample value IS phase for audio
    return complex(amplitude, phase_angle)


def audio_wave_decoder(phase: complex) -> float:
    """Convert phase back to audio sample."""
    return phase.imag


def neural_spike_encoder(spike: bool) -> complex:
    """
    Neural activity: Encode spikes as phase.
    
    Neuroscience interpretation:
    - Spike = 1, no spike = 0
    - Inter-spike interval = temporal pattern
    - Burst frequency = coherence
    
    The brain's timing IS its computation.
    """
    return complex(1 if spike else 0, 0)


def neural_spike_decoder(phase: complex) -> bool:
    """Convert phase back to spike."""
    return abs(phase) > 0.5


def market_price_encoder(price: float) -> complex:
    """
    Market prices: Encode as phase from price movements.
    
    Financial interpretation:
    - Real part: price level (normalized)
    - Imaginary part: volatility
    
    Markets have rhythm. Prices oscillate.
    """
    normalized = (price % 1000) / 1000.0
    volatility = random.gauss(0.5, 0.2)
    return complex(normalized, volatility)


def market_price_decoder(phase: complex) -> float:
    """Convert phase back to price."""
    return phase.real * 1000


def weather_pressure_encoder(pressure: float) -> complex:
    """
    Weather: Encode as phase from pressure systems.
    
    Meteorological interpretation:
    - Low pressure = one phase
    - High pressure = opposite phase
    - Fronts = phase transitions
    
    Weather moves in waves. Waves have phase.
    """
    normalized = (pressure - 900) / 100  # 900-1000 hPa range
    return complex(normalized, 0)


def weather_pressure_decoder(phase: complex) -> float:
    """Convert phase back to pressure."""
    return phase.real * 100 + 900


# Create adapters for each input type
ADAPTERS = {
    "smoke_signals": InputAdapter(
        name="Smoke Signals",
        encoder=smoke_signal_encoder,
        decoder=smoke_signal_decoder
    ),
    "llm_tokens": InputAdapter(
        name="LLM Tokens",
        encoder=llm_token_encoder,
        decoder=llm_token_decoder
    ),
    "morse_code": InputAdapter(
        name="Morse Code",
        encoder=morse_code_encoder,
        decoder=morse_code_decoder
    ),
    "sensor_friction": InputAdapter(
        name="Sensor Friction",
        encoder=sensor_friction_encoder,
        decoder=sensor_friction_decoder
    ),
    "audio_wave": InputAdapter(
        name="Audio Wave",
        encoder=audio_wave_encoder,
        decoder=audio_wave_decoder
    ),
    "neural_spike": InputAdapter(
        name="Neural Spikes",
        encoder=neural_spike_encoder,
        decoder=neural_spike_decoder
    ),
    "market_price": InputAdapter(
        name="Market Price",
        encoder=market_price_encoder,
        decoder=market_price_decoder
    ),
    "weather_pressure": InputAdapter(
        name="Weather Pressure",
        encoder=weather_pressure_encoder,
        decoder=weather_pressure_decoder
    ),
}


def demonstrate_input_adapters():
    """
    Demonstrate that THE_ONE works with ANY input.
    """
    print("\n" + "="*60)
    print("THE_ONE INPUT ADAPTERS")
    print("Demonstrating KAIROS compatibility with any input type")
    print("="*60 + "\n")
    
    for key, adapter in ADAPTERS.items():
        print(f"📡 {adapter.name}")
        print("-" * 40)
        
        # Demonstrate encoding
        if key == "smoke_signals":
            test_values = [True, False, True, True, False]
        elif key == "llm_tokens":
            test_values = ["the", "cat", "sat", "on", "the", "mat"]
        elif key == "morse_code":
            test_values = ["dot", "dash", "dash", "dot", "space_intra", "dash", "dot"]
        elif key == "sensor_friction":
            test_values = [0.1, 0.5, 0.9, 0.3, 0.7]
        elif key == "audio_wave":
            test_values = [0.1, -0.5, 0.9, -0.3, 0.7]
        elif key == "neural_spike":
            test_values = [True, False, True, False, False, True, False]
        elif key == "market_price":
            test_values = [150.0, 155.0, 148.0, 160.0, 152.0]
        elif key == "weather_pressure":
            test_values = [980.0, 1015.0, 1005.0, 995.0, 1020.0]
        else:
            test_values = ["test"]
        
        phases = []
        for value in test_values:
            timestamp = datetime.now()
            phase = adapter.encode(value, timestamp)
            phases.append(phase)
            print(f"  {value} → phase({phase.real:.2f}, {phase.imag:.2f})")
        
        # Show coherence calculation
        if len(phases) > 1:
            avg_phase = sum(phases, complex(0, 0)) / len(phases)
            coherence = abs(avg_phase)
            print(f"  Average phase: ({avg_phase.real:.2f}, {avg_phase.imag:.2f})")
            print(f"  Coherence: {coherence:.4f}")
        
        print()
    
    print("="*60)
    print("KEY INSIGHT")
    print("="*60)
    print()
    print("KAIROS dynamics work because EVERYTHING oscillates:")
    print()
    print("  • Smoke appears/disappears (temporal pattern)")
    print("  • Tokens arrive in sequence (temporal pattern)")
    print("  • Morse has rhythm (temporal pattern)")
    print("  • Sensors vibrate (physical oscillation)")
    print("  • Sound is pressure waves (oscillation)")
    print("  • Neurons spike (temporal pattern)")
    print("  • Prices fluctuate (economic oscillation)")
    print("  • Weather moves in waves (atmospheric oscillation)")
    print()
    print("Once in phase form, THE_ONE takes over.")
    print()
    print("THE_ONE is BECOMINGONE.")
    print("="*60 + "\n")


if __name__ == "__main__":
    demonstrate_input_adapters()
