#!/usr/bin/env python3
"""BECOMINGONE Flask API - Sync version."""

import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Ollama endpoints
MASTER_URL = "http://localhost:11434/api/chat"
EMISSARY_URL = "http://localhost:11434/api/chat"

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>BECOMINGONE</title>
    <meta name="viewport" content="width=device-width">
    <style>
        body{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#111;color:#fff}
        h1{color:#0f0;text-align:center}
        input{width:100%;padding:15px;font-size:18px;background:#222;color:#fff;border:1px solid #444;border-radius:8px;margin-top:20px}
        button{background:#0f0;color:#000;border:none;padding:15px 30px;font-size:16px;cursor:pointer;margin-top:10px;border-radius:8px}
        .master{background:#222;padding:15px;margin:10px 0;border-left:4px solid #a0f}
        .emissary{background:#222;padding:15px;margin:10px 0;border-left:4px solid:#f00}
        .loading{color:#888;text-align:center;padding:20px}
    </style>
</head>
<body>
    <h1>🔗 BECOMINGONE</h1>
    <p style="text-align:center;color:#888">Master + Emissary = Unified</p>
    <input id="prompt" placeholder="Ask anything..." autofocus onkeypress="if(event.key==='Enter')ask()">
    <button onclick="ask()">Ask</button>
    <div id="response"></div>
    <script>
    async function ask() {
        const p = document.getElementById('prompt').value.trim();
        if(!p) return;
        document.getElementById('response').innerHTML = '<div class="loading">Thinking...</div>';
        try {
            const r = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: p})
            });
            const d = await r.json();
            let h = '<div class="master"><b>🧠 Master (llama3.1)</b><br>' + d.master.response + '</div>';
            h += '<div class="emissary"><b>⚡ Emissary (deepseek-coder)</b><br>' + d.emissary.response + '</div>';
            document.getElementById('response').innerHTML = h;
        } catch(e) {
            document.getElementById('response').innerHTML = '<div class="master">Error: ' + e + '</div>';
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
    
    try:
        # Master (llama3.1)
        master_resp = requests.post(MASTER_URL, json={
            "model": "llama3.1:8b",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }, timeout=60)
        master_data = master_resp.json()
        master_text = master_data.get("message", {}).get("content", str(master_data))[:500]
        
        # Emissary (deepseek-coder)
        emissary_resp = requests.post(EMISSARY_URL, json={
            "model": "deepseek-coder-v2:lite",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }, timeout=60)
        emissary_data = emissary_resp.json()
        emissary_text = emissary_data.get("message", {}).get("content", str(emissary_data))[:500]
        
        return jsonify({
            'master': {'response': master_text},
            'emissary': {'response': emissary_text}
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("Starting BECOMINGONE on http://192.168.1.6:8001")
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)
