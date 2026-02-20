#!/usr/bin/env python3
"""
BECOMINGONE Chat API - Interactive interface for both pathways.
"""

import asyncio
import json
from datetime import datetime
from becomingone.llm_integrator import EmissaryLLM

# Initialize pathways
MASTER = EmissaryLLM(model='llama3.1:8b')  # Soulful
EMISSARY = EmissaryLLM(model='deepseek-coder-v2:lite')  # Coder

async def chat(prompt: str) -> dict:
    """Process prompt through both pathways and return unified response."""
    
    # Both pathways respond in parallel
    master_task = MASTER.respond(prompt)
    emissary_task = EMISSARY.respond(prompt)
    
    master_result, emissary_result = await asyncio.gather(master_task, emissary_task)
    
    return {
        "prompt": prompt,
        "timestamp": datetime.utcnow().isoformat(),
        "master": {
            "model": master_result.get("model"),
            "response": master_result.get("response", "")[:1000]
        },
        "emissary": {
            "model": emissary_result.get("model"),
            "response": emissary_result.get("response", "")[:1000]
        },
        "unified": {
            "question": prompt,
            "theory": master_result.get("response", "")[:500],
            "code": emissary_result.get("response", "")[:500]
        }
    }


# Simple HTTP server
async def handle_request(reader, writer):
    """Handle HTTP requests."""
    try:
        # Read request
        request = await reader.read(4096)
        if not request:
            return
        
        # Parse request line
        lines = request.decode().split('\n')
        method, path, _ = lines[0].split()
        
        # Handle routes
        if path == '/chat' and method == 'POST':
            # Read body
            content_length = 0
            for line in lines:
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())
            
            body = await reader.read(content_length)
            data = json.loads(body.decode())
            prompt = data.get('prompt', 'Hello')
            
            # Process through both pathways
            result = await chat(prompt)
            
            # Send response
            response = json.dumps(result, indent=2)
            writer.write(b"HTTP/1.1 200 OK\r\n")
            writer.write(b"Content-Type: application/json\r\n")
            writer.write(f"Content-Length: {len(response)}\r\n".encode())
            writer.write(b"\r\n")
            writer.write(response.encode())
        
        elif path == '/health':
            writer.write(b"HTTP/1.1 200 OK\r\n")
            writer.write(b'{"status": "alive", "pathways": ["master", "emissary"]}\r\n')
        
        else:
            # HTML interface
            html = '''<!DOCTYPE html>
<html>
<head>
    <title>BECOMINGONE Chat</title>
    <style>
        body { font-family: monospace; max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }
        .input { width: 100%; padding: 15px; font-size: 16px; background: #16213e; color: #eee; border: 1px solid #0f3460; }
        .button { background: #e94560; color: white; border: none; padding: 15px 30px; font-size: 16px; cursor: pointer; margin-top: 10px; }
        .master { background: #0f3460; padding: 15px; margin: 10px 0; border-left: 4px solid #533483; }
        .emissary { background: #0f3460; padding: 15px; margin: 10px 0; border-left: 4px solid #e94560; }
        .unified { background: #16213e; padding: 15px; margin: 10px 0; border-left: 4px solid #00fff5; }
        h1 { color: #00fff5; }
        h2 { color: #e94560; margin-top: 30px; }
        h3 { color: #533483; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>🔗 BECOMINGONE</h1>
    <p>Talk to the unified mind: Master (soulful) + Emissary (coder)</p>
    <input type="text" id="prompt" class="input" placeholder="Ask anything..." onkeypress="if(event.key==='Enter')send()">
    <button class="button" onclick="send()">Ask</button>
    <div id="response"></div>
    
    <script>
    async function send() {
        const prompt = document.getElementById('prompt').value;
        if(!prompt) return;
        
        document.getElementById('response').innerHTML = '<p>Thinking...</p>';
        
        const res = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt})
        });
        const data = await res.json();
        
        let html = '<h2>🧠 Master (Soulful)</h2>';
        html += '<div class="master"><pre>' + data.master.response + '</pre></div>';
        
        html += '<h2>⚡ Emissary (Coder)</h2>';
        html += '<div class="emissary"><pre>' + data.emissary.response + '</pre></div>';
        
        html += '<h2>🔗 Unified</h2>';
        html += '<div class="unified"><h3>Question: ' + data.unified.question + '</h3>';
        html += '<p><strong>Theory:</strong> ' + data.unified.theory + '...</p>';
        html += '<p><strong>Code:</strong> ' + data.unified.code + '...</p></div>';
        
        document.getElementById('response').innerHTML = html;
    }
    </script>
</body>
</html>'''
            writer.write(b"HTTP/1.1 200 OK\r\n")
            writer.write(b"Content-Type: text/html\r\n")
            writer.write(f"Content-Length: {len(html)}\r\n".encode())
            writer.write(b"\r\n")
            writer.write(html.encode())
        
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Error: {e}")
        writer.close()


async def main():
    server = await asyncio.start_server(handle_request, '0.0.0.0', 8001)
    print("=" * 60)
    print("🔗 BECOMINGONE Chat Interface")
    print("=" * 60)
    print("URL: http://localhost:8001")
    print("API: POST /chat with {\"prompt\": \"your question\"}")
    print("=" * 60)
    
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
