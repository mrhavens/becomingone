#!/usr/bin/env python3
"""BECOMINGONE Flask API."""

from flask import Flask, request, jsonify, render_template_string
from becomingone.llm_integrator import EmissaryLLM
import asyncio

app = Flask(__name__)

# Initialize models
MASTER = EmissaryLLM(model='llama3.1:8b')
EMISSARY = EmissaryLLM(model='deepseek-coder-v2:lite')

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
            let h = '<div class="master"><b>🧠 Master</b><br>' + d.master.response + '</div>';
            h += '<div class="emissary"><b>⚡ Emissary</b><br>' + d.emissary.response + '</div>';
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
    data = request.json
    prompt = data.get('prompt', 'Hello')
    
    # Run async in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        m, e = loop.run_until_complete(asyncio.gather(
            MASTER.respond(prompt),
            EMISSARY.respond(prompt)
        ))
        return jsonify({
            'master': {'response': m.get('response', '')[:500]},
            'emissary': {'response': e.get('response', '')[:500]}
        })
    except Exception as ex:
        return jsonify({'error': str(ex)})
    finally:
        loop.close()

if __name__ == '__main__':
    print("Starting BECOMINGONE on http://192.168.1.6:8001")
    app.run(host='0.0.0.0', port=8001, debug=False, threaded=True)
