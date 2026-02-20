#!/usr/bin/env python3
"""BECOMINGONE Chat - Simple."""

import asyncio
import json
from becomingone.llm_integrator import EmissaryLLM

# Use just Emissary for now (faster)
MODEL = EmissaryLLM(model='llama3.1:8b')

async def process(prompt):
    r = await MODEL.respond(prompt)
    return {"master": {"response": r.get("response", "")[:500]}, "emissary": {"response": r.get("response", "")[:500]}}

HTML = '''<!DOCTYPE html><html><head><title>BECOMINGONE</title><meta name="viewport" content="width=device-width"><style>body{font-family:sans-serif;max-width:700px;margin:0 auto;padding:20px;background:#111;color:#fff}h1{color:#0f0}input{width:100%;padding:12px;font-size:16px;background:#222;color:#fff;border:1px solid #444;border-radius:6px}button{background:#0f0;color:#000;border:none;padding:12px 24px;font-size:14px;cursor:pointer;margin:8px 0}.r{background:#222;padding:12px;margin:8px 0;border-left:4px solid #90f}</style></head><body><h1>🔗 BECOMINGONE</h1><p style="color:#888">Test Mode: Single Model</p><input id="p" placeholder="Ask anything..." onkeypress="if(event.key==='Enter')s()"><button onclick="s()">Ask</button><div id="r"></div><script>async function s(){var p=document.getElementById("p").value.trim();if(!p)return;document.getElementById("r").innerHTML="<p style=color:#888>Thinking...</p>";var r=await fetch("/c",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt:p})});var d=await r.json();document.getElementById("r").innerHTML="<div class=r><b>Response</b><br>"+d.master.response+"</div>"}</script></body></html>'''

async def handle(r, w):
    try:
        d = await r.read(4096)
        if not d: return
        txt = d.decode('utf-8', errors='ignore')
        ln = txt.split('\n')[0].split()
        method, path = ln[0], ln[1] if len(ln) > 1 else '/'
        body = b""
        for line in txt.split('\r\n'):
            if line.lower().startswith('content-length:'):
                body = await r.read(int(line.split(':')[1].strip()))
                break
        if path == '/health':
            w.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 16\r\n\r\n{"status":"ok"}')
        elif path == '/c' and method == 'POST':
            data = json.loads(body.decode())
            result = await process(data.get('prompt', 'Hi'))
            resp = json.dumps(result)
            w.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ' + str(len(resp)).encode() + b'\r\n\r\n' + resp.encode())
        else:
            w.write(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: ' + str(len(HTML)).encode() + b'\r\n\r\n' + HTML.encode())
    except Exception as e:
        print('Error:', e)
    finally:
        w.close()
        await w.wait_closed()

asyncio.run(asyncio.start_server(handle, '0.0.0.0', 8001))
print('Running on http://192.168.1.6:8001')
