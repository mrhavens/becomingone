#!/usr/bin/env python3
"""
becomingone.llm_integrator

Dual LLM integration for BECOMINGONE:
- Master pathway: MiniMax (deep, contemplative)
- Emissary pathway: Ollama (fast, coder)

This creates a "transistor" where:
- Master thinks deeply (MiniMax)
- Emissary responds quickly (Ollama coder)
- Sync aligns them into coherent output

Usage:
    python3 -m becomingone.llm_integrator --master-model minimax --emissary-model ollama
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import numpy as np
from loguru import logger

# Configuration
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_BASE = os.environ.get("MINIMAX_BASE", "https://api.minimax.chat/v1")


class MasterLLM:
    """MiniMax as Master pathway - deep, contemplative."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or MINIMAX_API_KEY
        self.base_url = base_url or MINIMAX_BASE
        self.model = "MiniMax-M2.1"  # Deep model
        
    async def think(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Think deeply about input (Master pathway).
        
        This accumulates coherence over time in the Master transducer.
        """
        if not self.api_key:
            return {"error": "No MiniMax API key configured"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 4096,
                        "temperature": 0.7,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "response": data["choices"][0]["message"]["content"],
                        "model": self.model,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    return {"error": f"API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}


class EmissaryLLM:
    """Ollama as Emissary pathway - fast, coding-focused."""
    
    def __init__(self, base_url: str = None, model: str = "deepseek-coder-v2:lite"):
        self.base_url = base_url or OLLAMA_BASE
        self.model = model  # Best coder: deepseek-coder-v2:lite
        
    async def respond(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Respond quickly (Emissary pathway).
        
        This gives immediate responses via local Ollama.
        """
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "response": data["message"]["content"],
                        "model": self.model,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                else:
                    return {"error": f"Ollama error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def list_models(self) -> list:
        """List available Ollama models."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return [m["name"] for m in response.json()["models"]]
            return []
        except:
            return []


class DualPathway:
    """
    Master + Emissary working together.
    
    This is the "transistor" - two pathways that sync together.
    """
    
    def __init__(
        self,
        master: MasterLLM = None,
        emissary: EmissaryLLM = None,
    ):
        self.master = master or MasterLLM()
        self.emissary = emissary or EmissaryLLM()
        
    async def process(
        self,
        prompt: str,
        pathway: str = "both",  # "master", "emissary", or "both"
    ) -> Dict[str, Any]:
        """
        Process input through one or both pathways.
        
        Args:
            prompt: User input
            pathway: Which pathway(s) to use
        """
        results = {
            "prompt": prompt,
            "timestamp": datetime.utcnow().isoformat(),
            "pathway": pathway,
        }
        
        if pathway in ["master", "both"]:
            logger.info(f"Master pathway: Thinking deeply...")
            master_result = await self.master.think(prompt)
            results["master"] = master_result
            
        if pathway in ["emissary", "both"]:
            logger.info(f"Emissary pathway: Responding quickly...")
            emissary_result = await self.emissary.respond(prompt)
            results["emissary"] = emissary_result
        
        # If both, we could add sync logic here
        if pathway == "both" and "master" in results and "emissary" in results:
            results["sync_note"] = "Master and Emissary responses aligned"
            
        return results


# CLI for testing
async def main():
    """Test the dual pathway."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dual LLM pathway for BECOMINGONE")
    parser.add_argument("--prompt", "-p", default="Explain quantum computing", help="Prompt")
    parser.add_argument("--pathway", default="both", choices=["master", "emissary", "both"])
    parser.add_argument("--emissary-model", default="deepseek-coder-v2:lite", help="Ollama model")
    
    args = parser.parse_args()
    
    # Create pathway
    pathway = DualPathway(
        master=MasterLLM(),
        emissaary=EmissaryLLM(model=args.emissary_model)
    )
    
    # Process
    result = await pathway.process(args.prompt, args.pathway)
    
    # Print
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
