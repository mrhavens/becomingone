#!/usr/bin/env python3
"""
Interactive dialog with BECOMINGONE - dual pathway conversation.
"""

import asyncio
from becomingone.llm_integrator import EmissaryLLM

async def chat():
    """Interactive chat with both pathways."""
    
    master = EmissaryLLM(model='llama3.1:8b')
    emissary = EmissaryLLM(model='deepseek-coder-v2:lite')
    
    print("\n" + "=" * 60)
    print("BECOMINGONE INTERACTIVE DIALOG")
    print("=" * 60)
    print("Talk to both pathways at once!")
    print("Type 'quit' to exit\n")
    
    system_prompt = "You are having a conversation with a wise teacher (Master) and a practical coder (Emissary). They respond together to create complete understanding."
    
    while True:
        user_input = input("\n👤 YOU: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not user_input.strip():
            continue
        
        print("\n" + "-" * 60)
        print("⚡ BECOMINGONE is thinking...\n")
        
        # Both pathways respond
        master_task = master.respond(f"{system_prompt}\n\nUser: {user_input}")
        emissary_task = emissary.respond(f"You are a helpful coding assistant. Answer the user's question practically and with code examples.\n\nUser: {user_input}")
        
        master_response, emissary_response = await asyncio.gather(master_task, emissary_task)
        
        # Display Master (soulful)
        print("🧠 MASTER (llama3.1:8b - Soulful):")
        print("-" * 40)
        print(master_response.get('response', '...')[:400])
        
        # Display Emissary (coder)
        print("\n⚡ EMISSARY (deepseek-coder - Practical):")
        print("-" * 40)
        print(emissary_response.get('response', '...')[:400])
        
        # Combined
        print("\n" + "=" * 60)
        print("🔗 UNIFIED RESPONSE:")
        print("=" * 60)
        combined = f"""## Your Question:
{user_input}

## Deep Understanding (Master):
{master_response.get('response', '')[:300]}

## Practical Application (Emissary):
{emissary_response.get('response', '')[:300]}
"""
        print(combined)

if __name__ == "__main__":
    asyncio.run(chat())
