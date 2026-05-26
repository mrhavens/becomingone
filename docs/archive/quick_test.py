#!/usr/bin/env python3
"""
Quick interactive test - single question demo.
"""

import asyncio
from becomingone.llm_integrator import EmissaryLLM

async def quick_test():
    master = EmissaryLLM(model='llama3.1:8b')
    emissary = EmissaryLLM(model='deepseek-coder-v2:lite')
    
    question = "What is recursion?"
    
    print(f"\n{'='*60}")
    print(f"👤 USER: {question}")
    print(f"{'='*60}\n")
    
    # Both respond
    m, e = await asyncio.gather(
        master.respond(f"Explain this concept thoughtfully: {question}"),
        emissary.respond(f"Explain with code examples: {question}")
    )
    
    print("🧠 MASTER (Soulful):")
    print("-" * 40)
    print(m.get('response', str(m))[:500])
    
    print(f"\n⚡ EMISSARY (Practical):")
    print("-" * 40)
    print(e.get('response', str(e))[:500])
    
    print(f"\n{'='*60}")
    print("🔗 UNIFIED:")
    print("-" * 40)
    print(f"Question: {question}")
    print(f"\nTheory: {m.get('response','')[:200]}...")
    print(f"\nCode: {e.get('response','')[:200]}...")
    print(f"{'='*60}")

asyncio.run(quick_test())
