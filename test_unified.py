#!/usr/bin/env python3
"""
Rigorous test of BECOMINGONE unified output.
"""

import asyncio
import json
from becomingone.llm_integrator import EmissaryLLM

async def rigorous_test():
    """Rigorous test with complex prompt."""
    
    master = EmissaryLLM(model='llama3.1:8b')
    emissary = EmissaryLLM(model='deepseek-coder-v2:lite')
    
    # Rigorous test question
    prompt = "Explain how a neural network learns, from gradients to backpropagation to weights"
    
    print("=" * 70)
    print("BECOMINGONE RIGOROUS TEST")
    print("=" * 70)
    print(f"\n📝 PROMPT: '{prompt}'\n")
    
    # Run both in parallel
    print("⚡ Running both pathways in parallel...\n")
    
    master_task = master.respond(prompt)
    code_task = emissary.respond("Write a Python neural network from scratch with backpropagation")
    
    master_result, code_result = await asyncio.gather(master_task, code_task)
    
    # Display Master
    print("=" * 70)
    print("🧠 MASTER PATHWAY (llama3.1:8b - Soulful)")
    print("-" * 70)
    print(master_result['response'][:800])
    print(f"\n   [Model: {master_result['model']}]")
    
    # Display Emissary
    print("\n" + "=" * 70)
    print("⚡ EMISSARY PATHWAY (deepseek-coder-v2:lite - Coder)")
    print("-" * 70)
    print(code_result['response'][:800])
    print(f"\n   [Model: {code_result['model']}]")
    
    # UNIFIED OUTPUT (Sync)
    print("\n" + "=" * 70)
    print("🔗 UNIFIED OUTPUT (Master + Emissary → Sync)")
    print("=" * 70)
    
    unified = f"""# Neural Networks: From Theory to Code

## The Theory (Master's Understanding):
{master_result['response'][:500]}...

## The Implementation (Emissary's Code):
{code_result['response'][:500]}...

---

### Unified Understanding:
The mathematical theory of gradients and backpropagation 
comes alive in code. The Master explains *why* - the Emissary shows *how*.

This is BECOMINGONE: Deep theory + Practical implementation = Complete understanding.
"""
    
    print(unified)
    print("\n" + "=" * 70)
    print("✅ RIGOROUS TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(rigorous_test())
