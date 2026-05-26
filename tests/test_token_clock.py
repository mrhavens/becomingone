"""
tests/test_token_clock.py

Test the mathematical rigid coupling of the KAIROS temporal engine
to discrete token intervals (Token Clock mode).
"""

import pytest
from datetime import datetime, timedelta
from datetime import timezone
import asyncio

from becomingone.core.engine import KAIROSTemporalEngine, TemporalConfig

@pytest.mark.asyncio
async def test_token_clock_spacing():
    # 1. Configure the engine for 20 Hz token generation
    config = TemporalConfig(
        clock_mode="token_clock",
        token_frequency=20.0  # 20 tokens per second -> dt = 0.05 seconds
    )
    
    engine = KAIROSTemporalEngine(config=config)
    
    # Capture the exact initial time
    start_time = engine._timestamps[-1]
    
    # 2. Simulate an LLM streaming 10 tokens
    # Using normal temporalize() which should respect the implicit clock mode
    for i in range(10):
        engine.temporalize(f"token_{i}")
        
    # Check the final timestamp
    final_time = engine._timestamps[-1]
    elapsed = (final_time - start_time).total_seconds()
    
    # 10 tokens at 20 Hz = exactly 0.5 seconds of subjective time advance
    # floating point precision check
    assert abs(elapsed - 0.5) < 1e-6, f"Expected 0.5s elapsed, got {elapsed}"

@pytest.mark.asyncio
async def test_temporalize_stream():
    config = TemporalConfig(
        clock_mode="wall_clock", # Even in wall clock mode, the stream forces token mode
        token_frequency=10.0     # 10 tokens per sec -> dt = 0.1s
    )
    engine = KAIROSTemporalEngine(config=config)
    
    start_time = datetime.now(timezone.utc)
    tokens = ["I", "am", "Solaria", "and", "I", "am", "continuous"]
    
    # Stream the tokens
    states = engine.temporalize_stream(tokens, start_time=start_time)
    
    assert len(states) == 7
    
    # The time difference between the first and last state should be exactly 6 * 0.1s = 0.6s
    first_time = states[0].timestamp
    last_time = states[-1].timestamp
    elapsed = (last_time - first_time).total_seconds()
    
    assert abs(elapsed - 0.6) < 1e-6, f"Expected 0.6s elapsed, got {elapsed}"
    
    # The engine config should be cleanly restored to wall_clock
    assert engine.config.clock_mode == "wall_clock"
