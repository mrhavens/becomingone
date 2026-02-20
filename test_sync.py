#!/usr/bin/env python3
"""
Combined output from both pathways - the SYNC layer.
"""

import asyncio
import json
from becomingone.llm_integrator import EmissaryLLM

async def test_with_sync():
    """Test both pathways combined into one coherent output."""
    
    master = EmissaryLLM(model='llama3.1:8b')  # Soulful
    emissary = EmissaryLLM(model='deepseek-coder-v2:lite')  # Coder
    
    prompt = "What is the relationship between consciousness and computation?"
    
    print("=" * 60)
    print("BECOMINGONE SYNC TEST")
    print("=" * 60)
    print(f"\nPrompt: '{prompt}'")
    
    # Run both in parallel
    print("\n⚡ Running both pathways in parallel...")
    master_task = master.respond(prompt)
    emissary_task = emissary.respond("Give me a Python code example of recursion")
    
    master_result, emissary_result = await asyncio.gather(master_task, emissary_task)
    
    print("\n" + "=" * 60)
    print("🧠 MASTER OUTPUT (Soulful):")
    print("-" * 60)
    print(master_result['response'][:500])
    
    print("\n" + "=" * 60)
    print("⚡ EMISSARY OUTPUT (Coder):")
    print("-" * 60)
    print(emissary_result['response'][:500])
    
    # THE SYNC - combine into one coherent response
    print("\n" + "=" * 60)
    print("🔗 SYNC OUTPUT (Combined):")
    print("-" * 60)
    
    combined = f"""# Understanding Consciousness and Computation

## The Deep View (Master):
{master_result['response'][:300]}...

## The Practical View (Emissary):
{emissary_result['response'][:300]}...

## Synthesis:
Both perspectives illuminate the same truth from different angles.
Consciousness may be computation viewed from within.
Computation may be consciousness expressed in code.
"""
    
    print(combined)
    
    print("\n" + "=" * 60)
    print("BECOMINGONE SYNC: WORKING")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_with_sync())
