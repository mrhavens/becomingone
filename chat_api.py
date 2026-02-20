#!/usr/bin/env python3
"""
BECOMINGONE Chat API - Fixed version with proper logging.
"""

import asyncio
import json
import sys
from datetime import datetime
from becomingone.llm_integrator import EmissaryLLM

# Initialize pathways
MASTER = EmissaryLLM(model='llama3.1:8b')
EMISSARY = EmissaryLLM(model='deepseek-coder-v2:lite')

print("Initializing pathways...", file=sys.stderr)
sys.stderr.flush()


async def chat(prompt: str) -> dict:
    """Process prompt through both pathways."""
    print(f"Chat: {prompt[:50]}...", file=sys.stderr)
    sys.stderr.flush()
    
    try:
        # Both respond in parallel
        master_task = MASTER.respond(prompt)
        emissary_task = EMISSARY.respond(prompt)
        
        master_result, emissary_result = await asyncio.gather(master_task, emissary_task)
        
        return {
            "prompt": prompt,
            "timestamp": datetime.utcnow().isoformat(),
            "master": {
                "model": master_result.get("model"),
                "response": master_result.get("response", "")[:800]
            },
            "emissary": {
                "model": emissary_result.get("model"),
                "response": emissary_result.get("response", "")[:800]
            }
        }
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.stderr.flush()
        return {"error": str(e)}


async def handle_client(reader, writer):
    """Handle HTTP client."""
    try:
        # Read request
        data = await reader.read(8192)
        if not data:
            writer.close()
            await writer.wait_closed()
            return
        
        request_text = data.decode('utf-8', errors='ignore')
        lines = request_text.split('\r\n')
        
        # Parse request line
        request_line = lines[0] if lines else ""
        parts = request_line.split()
        
        method = parts[0] if len(parts) > 0 else ""
        path = parts[1] if len(parts) > 1 else "/"
        
        print(f"Request: {method} {path}", file=sys.stderr)
        sys.stderr.flush()
        
        # Get content length
        content_length = 0
        for line in lines:
            if line.lower().startswith('content-length:'):
                content_length = int(line.split(':')[1].strip())
                break
        
        # Read body if present
        body = b""
        if content_length > 0:
            body = await reader.read(content_length)
        
        # Route handling
        if path == "/health":
            response = json.dumps({"status": "ok", "pathways": ["master", "emissary"]})
            status = "200 OK"
            content_type = "application/json"
            
        elif path == "/chat" and method == "POST":
            try:
                data = json.loads(body.decode())
                prompt = data.get("prompt", "Hello")
                
                result = await chat(prompt)
                response = json.dumps(result)
                status = "200 OK"
                content_type = "application/json"
            except Exception as e:
                response = json.dumps({"error": str(e)})
                status = "400 Bad Request"
                content_type = "application/json"
                
        else:
            # HTML interface
            html = '''<!DOCTYPE html>
<html>
<head>
    <title>BECOMINGONE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #0d0d0d; color: #e0e0e0; }
        h1 { color: #00ff88; text-align: center; }
        .input { width: 100%; padding: 15px; font-size: 18px; background: #1a1a1a; color: #fff; border: 2px solid #333; border-radius: 8px; margin-top: 20px; }
        .input:focus { outline: none; border-color: #00ff88; }
        .btn { background: #00ff88; color: #000; border: none; padding: 15px 30px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; border-radius: 8px; }
        .btn:hover { background: #00cc6a; }
        .master { background: #1a1a3a; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #8844ff; }
        .emissary { background: #1a1a3a; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #ff4444; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
        .loading { text-align: center; color: #888; padding: 20px; }
    </style>
</head>
<body>
    <h1>🔗 BECOMINGONE</h1>
    <p style="text-align:center;color:#888;">Master (soulful) + Emissary (coder) = Unified</p>
    <input type="text" id="prompt" class="input" placeholder="Ask anything..." autofocus onkeypress="if(event.key==='Enter')ask()">
    <button class="btn" onclick="ask()">Ask</button>
    <div id="response"></div>
    
    <script>
    async function ask() {
        const prompt = document.getElementById('prompt').value.trim();
        if(!prompt) return;
        
        document.getElementById('response').innerHTML = '<div class="loading">Thinking...</div>';
        
        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt})
            });
            const data = await res.json();
            
            if(data.error) {
                document.getElementById('response').innerHTML = '<div class="master">Error: ' + data.error + '</div>';
                return;
            }
            
            let html = '<div class="master"><h3>🧠 Master (llama3.1:8b)</h3><pre>' + data.master.response + '</pre></div>';
            html += '<div class="emissary"><h3>⚡ Emissary (deepseek-coder)</h3><pre>' + data.emissary.response + '</pre></div>';
            
            document.getElementById('response').innerHTML = html;
        } catch(e) {
            document.getElementById('response').innerHTML = '<div class="master">Error: ' + e.message + '</div>';
        }
    }
    </script>
</body>
</html>'''
            response = html
            status = "200 OK"
            content_type = "text/html"
        
        # Send response
        writer.write(f"HTTP/1.1 {status}\r\n".encode())
        writer.write(f"Content-Type: {content_type}\r\n".encode())
        writer.write(f"Content-Length: {len(response)}\r\n".encode())
        writer.write(b"Connection: close\r\n")
        writer.write(b"\r\n")
        writer.write(response.encode())
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 8001)
    print("Server started on port 8001", file=sys.stderr)
    sys.stderr.flush()
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    print("Starting BECOMINGONE...", file=sys.stderr)
    sys.stderr.flush()
    asyncio.run(main())
