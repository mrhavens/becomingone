#!/usr/bin/env python3
"""BECOMINGONE Chat API - Simplified."""

import asyncio
import json

# Import at module level
from becomingone.llm_integrator import EmissaryLLM

MASTER = None
EMISSARY = None

async def init_models():
    global MASTER, EMISSARY
    print("Initializing models...")
    MASTER = EmissaryLLM(model='llama3.1:8b')
    EMISSARY = EmissaryLLM(model='deepseek-coder-v2:lite')
    print("Models initialized")

async def chat(prompt: str) -> dict:
    """Process through both pathways."""
    print(f"Processing: {prompt[:30]}...")
    
    try:
        m, e = await asyncio.wait_for(
            asyncio.gather(
                MASTER.respond(prompt),
                EMISSARY.respond(prompt),
                return_exceptions=True
            ),
            timeout=60
        )
        
        return {
            "prompt": prompt,
            "master": {"response": str(m)[:500] if isinstance(m, Exception) else m.get("response", str(m))[:500]},
            "emissary": {"response": str(e)[:500] if isinstance(e, Exception) else e.get("response", str(e))[:500]}
        }
    except asyncio.TimeoutError:
        return {"error": "Timeout"}
    except Exception as ex:
        return {"error": str(ex)}


HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>BECOMINGONE</title>
    <meta name="viewport" content="width=device-width">
    <style>
        body{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;background:#111;color:#fff}
        h1{color:#0f0;text-align:center}
        input{width:100%;padding:15px;font-size:18px;background:#222;color:#fff;border:1px solid #444;border-radius:8px}
        button{background:#0f0;color:#000;border:none;padding:15px 30px;font-size:16px;cursor:pointer;margin:10px 0;border-radius:8px}
        .master{background:#222;padding:15px;margin:10px 0;border-left:4px solid #a0f}
        .emissary{background:#222;padding:15px;margin:10px 0;border-left:4px solid #f00}
    </style>
</head>
<body>
    <h1>🔗 BECOMINGONE</h1>
    <p style="text-align:center;color:#888">Master + Emissary = Unified</p>
    <input id="p" placeholder="Ask anything..." autofocus onkeypress="if(event.key==='Enter')ask()">
    <button onclick="ask()">Ask</button>
    <div id="r"></div>
    <script>
    async function ask() {
        const prompt = document.getElementById('p').value.trim();
        if(!prompt) return;
        document.getElementById('r').innerHTML = '<p style="color:#888">Thinking...</p>';
        try {
            const res = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt})});
            const data = await res.json();
            if(data.error) { document.getElementById('r').innerHTML = '<div class="master">Error: '+data.error+'</div>'; return; }
            let h = '<div class="master"><b>🧠 Master</b><pre>'+data.master.response+'</pre></div>';
            h += '<div class="emissary"><b>⚡ Emissary</b><pre>'+data.emissary.response+'</pre></div>';
            document.getElementById('r').innerHTML = h;
        } catch(e) { document.getElementById('r').innerHTML = '<div class="master">Error: '+e+'</div>'; }
    }
    </script>
</body>
</html>'''


async def handle(reader, writer):
    try:
        data = await reader.read(4096)
        if not data:
            return
        
        text = data.decode('utf-8', errors='ignore')
        lines = text.split('\r\n')
        parts = lines[0].split()
        method, path = parts[0], parts[1] if len(parts) > 1 else '/'
        
        # Get body
        body = b""
        for line in lines:
            if line.lower().startswith('content-length:'):
                cl = int(line.split(':')[1].strip())
                body = await reader.read(cl)
                break
        
        # Routes
        if path == '/health':
            resp = json.dumps({"status": "ok"})
            content_type = "application/json"
        elif path == '/chat' and method == 'POST':
            try:
                d = json.loads(body.decode())
                result = await chat(d.get('prompt', 'Hi'))
                resp = json.dumps(result)
                content_type = "application/json"
            except Exception as e:
                resp = json.dumps({"error": str(e)})
                content_type = "application/json"
        else:
            resp = HTML
            content_type = "text/html"
        
        writer.write(b"HTTP/1.1 200 OK\r\n")
        writer.write(f"Content-Type: {content_type}\r\n".encode())
        writer.write(f"Content-Length: {len(resp)}\r\n".encode())
        writer.write(b"Connection: close\r\n\r\n")
        writer.write(resp.encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    await init_models()
    server = await asyncio.start_server(handle, '0.0.0.0', 8001)
    print("Server running on port 8001")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
