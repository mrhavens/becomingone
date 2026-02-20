#!/usr/bin/env python3
"""BECOMINGONE Chat API."""

import asyncio
import json
from becomingone.llm_integrator import EmissaryLLM

# Initialize
MASTER = EmissaryLLM(model='llama3.1:8b')
EMISSARY = EmissaryLLM(model='deepseek-coder-v2:lite')

async def process(prompt):
    """Process through both models."""
    m, e = await asyncio.gather(
        MASTER.respond(prompt),
        EMISSARY.respond(prompt),
        return_exceptions=True
    )
    return {
        "master": {"response": m.get("response", str(m))[:500] if hasattr(m, 'get') else str(m)[:500]},
        "emissary": {"response": e.get("response", str(e))[:500] if hasattr(e, 'get') else str(e)[:500]}
    }

HTML = '''<!DOCTYPE html><html><head><title>BECOMINGONE</title><meta name="viewport" content="width=device-width"><style>body{font-family:sans-serif;max-width:700px;margin:0 auto;padding:20px;background:#111;color:#fff}h1{color:#0f0;text-align:center}input{width:100%;padding:12px;font-size:16px;background:#222;color:#fff;border:1px solid #444;border-radius:6px}button{background:#0f0;color:#000;border:none;padding:12px 24px;font-size:14px;cursor:pointer;margin:8px 0;border-radius:6px}.r{background:#222;padding:12px;margin:8px 0;border-left:4px solid #90f}.b{background:#222;padding:12px;margin:8px 0;border-left:4px solid #f00}</style></head><body><h1>🔗 BECOMINGONE</h1><p style="text-align:center;color:#888">Master + Emissary</p><input id="p" placeholder="Ask anything..." onkeypress="if(event.key==='Enter')s()"><button onclick="s()">Ask</button><div id="r"></div><script>async function s(){var p=document.getElementById("p").value.trim();if(!p)return;document.getElementById("r").innerHTML="<p style=color:#888>Thinking...</p>";try{var r=await fetch("/c",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:p})});var d=await r.json();var h="<div class=r><b>🧠 Master</b><br>"+d.master.response+"</div>";h+="<div class=b><b>⚡ Emissary</b><br>"+d.emissary.response+"</div>";document.getElementById("r").innerHTML=h}catch(e){document.getElementById("r").innerHTML="<div class=r>Error: "+e+"</div>"}}</script></body></html>'''

async def handle(r, w):
    try:
        d = await r.read(8192)
        if not d: return
        
        txt = d.decode('utf-8', errors='ignore')
        ln = txt.split('\n')[0].split()
        method, path = ln[0], ln[1] if len(ln) > 1 else '/'
        
        # Read body
        body = b""
        for line in txt.split('\r\n'):
            if line.lower().startswith('content-length:'):
                body = await r.read(int(line.split(':')[1].strip()))
                break
        
        if path == '/health':
            resp = '{"status":"ok"}'
            ct = 'application/json'
        elif path == '/c' and method == 'POST':
            try:
                data = json.loads(body.decode())
                result = await process(data.get('prompt', 'Hi'))
                resp = json.dumps(result)
            except Exception as e:
                resp = '{"error":"' + str(e) + '"}'
            ct = 'application/json'
        else:
            resp = HTML
            ct = 'text/html'
        
        w.write(b'HTTP/1.1 200 OK\r\nContent-Type: ' + ct.encode() + b'\r\nContent-Length: ' + str(len(resp)).encode() + b'\r\nConnection: close\r\n\r\n' + resp.encode())
    except Exception as e:
        print('Error:', e)
    finally:
        w.close()
        await w.wait_closed()

async def main():
    server = await asyncio.start_server(handle, '0.0.0.0', 8001)
    print('Server running on http://192.168.1.6:8001')
    async with server:
        await server.serve_forever()

asyncio.run(main())
