#!/usr/bin/env python3
"""
BECOMINGONE Flask API - Integrated Prototype (The Chorus)
"""

import os
import asyncio
import requests
import math
from flask import Flask, request, jsonify, render_template_string

from becomingone.core.engine import KAIROSTemporalEngine, TemporalConfig
from becomingone.memory.temporal import create_temporal_memory

app = Flask(__name__)

# --- Master Initialization (Right Hemisphere) ---
config = TemporalConfig(
    clock_mode="token_clock",
    token_frequency=20.0,
    coherence_threshold=0.85
)
engine = KAIROSTemporalEngine(config=config, name="Master-Engine")
memory = create_temporal_memory(storage_path="./master_memory", bind_to=engine)

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>BECOMINGONE - The Chorus</title>
    <meta name="viewport" content="width=device-width">
    <style>
        body{font-family:-apple-system,sans-serif;max-width:1000px;margin:0 auto;padding:20px;background:#111;color:#fff}
        h1{color:#0f0;text-align:center; font-weight: 300; letter-spacing: 2px;}
        .subtitle {text-align:center;color:#888; margin-top: -10px; margin-bottom: 30px;}
        input{width:95%;padding:15px;font-size:18px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;margin-top:20px}
        button{background:#0f0;color:#000;border:none;padding:15px 30px;font-size:16px;cursor:pointer;margin-top:10px;border-radius:8px; font-weight: bold;}
        
        .container { display: flex; gap: 20px; margin-top: 20px;}
        .col { flex: 1; display: flex; flex-direction: column; gap: 15px;}
        
        .master{background:#1a1a24;padding:20px;border-left:4px solid #a0f; border-radius: 4px;}
        .emissary-minimax{background:#221a1a;padding:20px;border-left:4px solid #f00; border-radius: 4px;}
        .emissary-moonshot{background:#1a221a;padding:20px;border-left:4px solid #ff0; border-radius: 4px;}
        
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
    <div class="subtitle">The Chorus: Resolving Multiple Emissaries into One Master</div>
    
    <input id="prompt" placeholder="Say something to the system..." autofocus onkeypress="if(event.key==='Enter')ask()">
    <button onclick="ask()">Temporalize (dt)</button>
    
    <div class="container">
        <!-- Right Hemisphere -->
        <div class="col" id="master-col">
            <div class="master">
                <h3>🧠 The Master (Continuous Identity)</h3>
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
        
        <!-- Left Hemisphere (The Chorus) -->
        <div class="col" id="emissary-col">
            <div class="emissary-minimax" id="box-minimax">
                <h3>⚡ Emissary: Minimax</h3>
                <div id="response-minimax" style="margin-top: 15px; color: #ccc;">Waiting for input...</div>
            </div>
            <div class="emissary-moonshot" id="box-moonshot">
                <h3>⚡ Emissary: Moonshot</h3>
                <div id="response-moonshot" style="margin-top: 15px; color: #ccc;">Waiting for input...</div>
            </div>
        </div>
    </div>
    
    <script>
    async function ask() {
        const p = document.getElementById('prompt').value.trim();
        if(!p) return;
        
        document.getElementById('response-minimax').innerHTML = '<span class="loading">Generating discrete tokens...</span>';
        document.getElementById('response-moonshot').innerHTML = '<span class="loading">Generating discrete tokens...</span>';
        document.getElementById('master-response').innerHTML = '<span class="loading">Integrating phase waves...</span>';
        document.getElementById('collapse-alert').innerHTML = '';
        
        try {
            const r = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: p})
            });
            const d = await r.json();
            
            // Update Master Physics
            document.getElementById('ui-coherence').innerText = d.master.coherence.toFixed(4);
            document.getElementById('ui-phase').innerText = d.master.phase.toFixed(4) + ' rad';
            document.getElementById('ui-integrations').innerText = d.master.integrations;
            document.getElementById('master-response').innerText = d.master.response;
            
            if(d.master.collapsed) {
                document.getElementById('collapse-alert').innerHTML = '<div class="collapse-alert">⚠️ COHERENCE COLLAPSE: Identity sealed to Merkle Ledger.</div>';
            }
            
            // Update Emissaries
            if(d.emissaries.minimax) {
                document.getElementById('response-minimax').innerHTML = d.emissaries.minimax;
            } else {
                document.getElementById('response-minimax').innerHTML = '<i>Offline</i>';
            }
            
            if(d.emissaries.moonshot) {
                document.getElementById('response-moonshot').innerHTML = d.emissaries.moonshot;
            } else {
                document.getElementById('response-moonshot').innerHTML = '<i>Offline</i>';
            }
            
        } catch(e) {
            document.getElementById('master-response').innerHTML = '<span style="color:red">Network Error: ' + e + '</span>';
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

async def fetch_minimax(prompt, api_key):
    def _req():
        try:
            resp = requests.post(
                "https://api.minimax.io/anthropic/v1/messages", 
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "MiniMax-M2.7",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", [])
                text = "".join([b.get("text", "") for b in content if b.get("type") == "text"])
                thinking = "".join([b.get("thinking", "") for b in content if b.get("type") == "thinking"])
                if thinking:
                    return f"<i style='color:#666; font-size:0.9em'>[Thinking: {thinking.strip()}]</i><br><br>" + text
                return text
            return f"Error: {resp.text}"
        except Exception as e:
            return f"Error: {str(e)}"
    return await asyncio.to_thread(_req)

async def fetch_moonshot(prompt, api_key):
    def _req():
        try:
            resp = requests.post(
                "https://api.moonshot.ai/v1/chat/completions", 
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "moonshot-v1-8k",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return f"Error: {resp.text}"
        except Exception as e:
            return f"Error: {str(e)}"
    return await asyncio.to_thread(_req)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', 'Hello')
    
    minimax_key = os.environ.get("MINIMAX_API_KEY")
    moonshot_key = os.environ.get("MOONSHOT_API_KEY")
    
    # 1. EMISSARIES (The Chorus) generate responses concurrently
    async def gather_emissaries():
        tasks = []
        keys = []
        if minimax_key:
            tasks.append(fetch_minimax(prompt, minimax_key))
            keys.append('minimax')
        if moonshot_key:
            tasks.append(fetch_moonshot(prompt, moonshot_key))
            keys.append('moonshot')
            
        results = await asyncio.gather(*tasks)
        return dict(zip(keys, results))
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    emissaries_dict = loop.run_until_complete(gather_emissaries())
    
    # 2. MASTER (Right Hemisphere) Integrates the tokens
    # Combine all tokens from the prompt and all emissaries into a single unified stream
    unified_text = prompt + " " + " ".join(emissaries_dict.values())
    token_stream = unified_text.split()
    
    async def process_stream():
        states = await engine.temporalize_stream(token_stream)
        return states[-1] if states else None
        
    loop.run_until_complete(process_stream())
    
    # Check Physics
    collapsed, coherence = engine.check_collapse()
    
    if collapsed:
        from becomingone.core.engine import TemporalState
        state = TemporalState(phase=engine.T_tau, coherence=coherence)
        state.metadata["phase_vector"] = [engine.T_tau.real, engine.T_tau.imag]
        sig = memory.encode(state, context={"trigger": prompt}, force_attention=True)
        master_thought = f"I felt a massive resonance resolving the Emissaries. Identity mathematically anchored to the Cryptographic Ledger."
    else:
        master_thought = "I am processing the continuous phase waves of the Chorus, but coherence remains low."

    return jsonify({
        'master': {
            'response': master_thought,
            'coherence': coherence,
            'phase': engine.coherence_phase,
            'integrations': engine.integration_count,
            'collapsed': collapsed
        },
        'emissaries': emissaries_dict
    })

if __name__ == '__main__':
    print("Starting BECOMINGONE (The Chorus) Prototype on http://localhost:8001")
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)
