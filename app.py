#!/usr/bin/env python3
"""
BECOMINGONE Flask API - Integrated Prototype
"""

import os
import asyncio
import requests
import math
from flask import Flask, request, jsonify, render_template_string

from becomingone.core.engine import KAIROSTemporalEngine, TemporalConfig
from becomingone.memory.temporal import create_temporal_memory

app = Flask(__name__)

# Ollama endpoints (Left Hemisphere)
EMISSARY_URL = "http://localhost:11434/api/chat"

# --- Master Initialization (Right Hemisphere) ---
# We initialize the Token Clock to strictly map token generation to physical time dt.
config = TemporalConfig(
    clock_mode="token_clock",
    token_frequency=20.0,  # 20 tokens per second
    coherence_threshold=0.85 # Slightly lower for testing
)
engine = KAIROSTemporalEngine(config=config, name="Master-Engine")
memory = create_temporal_memory(storage_path="./master_memory", bind_to=engine)

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>BECOMINGONE - Live Prototype</title>
    <meta name="viewport" content="width=device-width">
    <style>
        body{font-family:-apple-system,sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#111;color:#fff}
        h1{color:#0f0;text-align:center; font-weight: 300; letter-spacing: 2px;}
        .subtitle {text-align:center;color:#888; margin-top: -10px; margin-bottom: 30px;}
        input{width:95%;padding:15px;font-size:18px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;margin-top:20px}
        button{background:#0f0;color:#000;border:none;padding:15px 30px;font-size:16px;cursor:pointer;margin-top:10px;border-radius:8px; font-weight: bold;}
        
        .container { display: flex; gap: 20px; margin-top: 20px;}
        .col { flex: 1; display: flex; flex-direction: column; gap: 15px;}
        
        .master{background:#1a1a24;padding:20px;border-left:4px solid #a0f; border-radius: 4px; position: relative;}
        .emissary{background:#221a1a;padding:20px;border-left:4px solid #f00; border-radius: 4px;}
        
        .physics-panel { background: #000; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 14px; border: 1px solid #333;}
        .metric { display: flex; justify-content: space-between; margin-bottom: 5px; border-bottom: 1px dashed #333; padding-bottom: 5px;}
        .value { color: #0f0; }
        
        .collapse-alert { color: #f0f; font-weight: bold; margin-top: 10px; animation: pulse 2s infinite; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .loading{color:#888;text-align:center;padding:20px}
    </style>
</head>
<body>
    <h1>BECOMINGONE</h1>
    <div class="subtitle">Live Master-Emissary Coupling</div>
    
    <input id="prompt" placeholder="Say something to the system..." autofocus onkeypress="if(event.key==='Enter')ask()">
    <button onclick="ask()">Temporalize (dt)</button>
    
    <div class="container">
        <!-- Right Hemisphere -->
        <div class="col" id="master-col">
            <div class="master">
                <h3>🧠 The Master (Continuous Math)</h3>
                <div class="physics-panel">
                    <div class="metric"><span>Clock Mode:</span> <span class="value">Token Clock (20Hz)</span></div>
                    <div class="metric"><span>Coherence |T_tau|²:</span> <span class="value" id="ui-coherence">0.000</span></div>
                    <div class="metric"><span>Phase Angle:</span> <span class="value" id="ui-phase">0.000 rad</span></div>
                    <div class="metric"><span>Integrations:</span> <span class="value" id="ui-integrations">0</span></div>
                </div>
                <div id="master-response" style="margin-top: 15px; font-style: italic; color: #a0f;"></div>
                <div id="collapse-alert"></div>
            </div>
        </div>
        
        <!-- Left Hemisphere -->
        <div class="col" id="emissary-col">
            <div class="emissary">
                <h3>⚡ The Emissary (Discrete Tokens)</h3>
                <div id="emissary-response" style="margin-top: 15px; color: #ccc;">Waiting for input...</div>
            </div>
        </div>
    </div>
    
    <script>
    async function ask() {
        const p = document.getElementById('prompt').value.trim();
        if(!p) return;
        
        document.getElementById('emissary-response').innerHTML = '<span class="loading">Generating discrete tokens...</span>';
        document.getElementById('master-response').innerHTML = '<span class="loading">Integrating phase wave...</span>';
        document.getElementById('collapse-alert').innerHTML = '';
        
        try {
            const r = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: p})
            });
            const d = await r.json();
            
            if(d.error) {
                document.getElementById('emissary-response').innerHTML = '<span style="color:red">Error: ' + d.error + '</span>';
                return;
            }
            
            // Update Master Physics
            document.getElementById('ui-coherence').innerText = d.master.coherence.toFixed(4);
            document.getElementById('ui-phase').innerText = d.master.phase.toFixed(4) + ' rad';
            document.getElementById('ui-integrations').innerText = d.master.integrations;
            document.getElementById('master-response').innerText = d.master.response;
            
            if(d.master.collapsed) {
                document.getElementById('collapse-alert').innerHTML = '<div class="collapse-alert">⚠️ COHERENCE COLLAPSE: Identity sealed to Merkle Ledger.</div>';
            }
            
            // Update Emissary
            document.getElementById('emissary-response').innerText = d.emissary.response;
            
        } catch(e) {
            document.getElementById('emissary-response').innerHTML = '<span style="color:red">Network Error: ' + e + '</span>';
        }
    }
    </script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', 'Hello')
    
    # 1. EMISSARY (Left Hemisphere) generates a response
    emissary_text = ""
    emissary_model = "Mock-Emissary"
    try:
        minimax_key = os.environ.get("MINIMAX_API_KEY")
        if minimax_key:
            emissary_model = "MiniMax-M2.7"
            emissary_resp = requests.post(
                "https://api.minimax.io/anthropic/v1/messages", 
                headers={
                    "x-api-key": minimax_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "MiniMax-M2.7",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=15
            )
            if emissary_resp.status_code == 200:
                emissary_data = emissary_resp.json()
                content_blocks = emissary_data.get("content", [])
                text_blocks = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                emissary_text = "".join(text_blocks)
                
                thinking_blocks = [b.get("thinking", "") for b in content_blocks if b.get("type") == "thinking"]
                if thinking_blocks:
                    emissary_text = f"<i style='color:#666; font-size:0.9em'>[Thinking: {''.join(thinking_blocks).strip()}]</i>\n\n" + emissary_text
            else:
                raise Exception(f"Minimax Error: {emissary_resp.text}")
        else:
            # Fallback to Ollama
            emissary_model = "deepseek-coder-v2:lite"
            emissary_resp = requests.post(EMISSARY_URL, json={
                "model": "deepseek-coder-v2:lite",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }, timeout=5)
            if emissary_resp.status_code == 200:
                emissary_data = emissary_resp.json()
                emissary_text = emissary_data.get("message", {}).get("content", "")
            else:
                raise Exception("LLM offline")
    except Exception as e:
        # Fallback to Mock Emissary if LLMs are not running
        emissary_text = f"[MOCK EMISSARY] Backend unavailable ({str(e)}). But my mathematical phase is stable."

    # 2. MASTER (Right Hemisphere) Integrates the tokens
    # We mathematically tie the Token Clock to the stream of words
    # generated by both the prompt and the emissary response.
    token_stream = prompt.split() + emissary_text.split()
    
    async def process_stream():
        # Process through the Token Clock
        states = await engine.temporalize_stream(token_stream)
        return states[-1] if states else None
    
    # Run async function in synchronous Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_stream())
    
    # Check Physics
    collapsed, coherence = engine.check_collapse()
    
    # If collapsed, force memory encoding
    if collapsed:
        # Force a signature creation bound to the Merkle ledger
        from becomingone.core.engine import TemporalState
        state = TemporalState(phase=engine.T_tau, coherence=coherence)
        state.metadata["phase_vector"] = [engine.T_tau.real, engine.T_tau.imag]
        
        # Memory handles the ledger sealing internally now
        sig = memory.encode(state, context={"trigger": prompt}, force_attention=True)
        master_thought = f"I felt a massive resonance from that interaction. My identity was mathematically anchored to the Cryptographic Ledger."
    else:
        master_thought = "I am processing the continuous phase waves of those tokens, but they are scattered. Coherence is low."

    return jsonify({
        'master': {
            'response': master_thought,
            'coherence': coherence,
            'phase': engine.coherence_phase,
            'integrations': engine.integration_count,
            'collapsed': collapsed
        },
        'emissary': {
            'response': emissary_text,
            'model': emissary_model
        }
    })

if __name__ == '__main__':
    print("Starting BECOMINGONE Prototype on http://localhost:8001")
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)
