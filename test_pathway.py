#!/usr/bin/env python3
"""
Test the dual LLM pathway for BECOMINGONE.
"""

import asyncio
import json
from becomingone.llm_integrator import EmissaryLLM

async def test_both_pathways():
    """Test both Master and Emissary pathways."""
    
    # Create both pathways using EmissaryLLM (same interface)
    master = EmissaryLLM(model='llama3.1:8b')  # Soulful
    emissary = EmissaryLLM(model='deepseek-coder-v2:lite')  # Coder
    
    prompt = "What is consciousness?"
    
    print("=" * 60)
    print("BECOMINGONE Dual Pathway Test")
    print("=" * 60)
    print(f"\nPrompt: '{prompt}'")
    print("\n" + "-" * 60)
    
    # Test Master (soulful)
    print("\n🧠 MASTER PATHWAY (llama3.1:8b - soulful):")
    print("   Thinking deeply...")
    master_result = await master.respond(prompt)
    print(f"\n   Response: {master_result['response'][:300]}...")
    print(f"   Model: {master_result['model']}")
    
    # Test Emissary (coder)
    print("\n" + "-" * 60)
    print("\n⚡ EMISSARY PATHWAY (deepseek-coder-v2:lite - coder):")
    print("   Responding quickly...")
    prompt2 = "Write a Python function to calculate factorial"
    emissary_result = await emissary.respond(prompt2)
    print(f"\n   Response: {emissary_result['response'][:300]}...")
    print(f"   Model: {emissary_result['model']}")
    
    print("\n" + "=" * 60)
    print("BECOMINGONE Transistor: WORKING")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_both_pathways())
