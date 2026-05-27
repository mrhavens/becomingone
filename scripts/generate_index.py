import json
import os
import datetime

ARCHIVES_FILE = "/home/gemini/becomingone/scripts/archives.json"
OUTPUT_FILE = "/tmp/index.html"

# Ensure archives.json exists
if not os.path.exists(ARCHIVES_FILE):
    with open(ARCHIVES_FILE, "w") as f:
        json.dump([], f)

with open(ARCHIVES_FILE, "r") as f:
    try:
        archives = json.load(f)
    except json.JSONDecodeError:
        archives = []

# HTML Template with Glassmorphism and rich aesthetics
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Fold Within - IPFS Sovereign Archive</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #050505;
            --glass-bg: rgba(20, 20, 25, 0.4);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-main: #f0f0f0;
            --text-dim: #999;
            --accent-glow: rgba(0, 255, 170, 0.3);
            --accent-color: #00ffaa;
            --secondary-glow: rgba(138, 43, 226, 0.2);
        }

        body {
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 15% 50%, var(--secondary-glow), transparent 30%),
                radial-gradient(circle at 85% 30%, var(--accent-glow), transparent 30%);
            background-attachment: fixed;
        }

        /* Abstract glowing orb */
        .orb {
            position: fixed;
            width: 500px;
            height: 500px;
            border-radius: 50%;
            background: linear-gradient(45deg, var(--accent-color), blueviolet);
            filter: blur(120px);
            opacity: 0.15;
            z-index: -1;
            animation: float 20s infinite ease-in-out alternate;
        }

        @keyframes float {
            0% { transform: translate(0, 0) scale(1); }
            100% { transform: translate(100px, 50px) scale(1.2); }
        }

        header {
            width: 100%;
            max-width: 1200px;
            padding: 4rem 2rem 2rem;
            text-align: center;
        }

        h1 {
            font-size: 3.5rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #fff, var(--accent-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        p.subtitle {
            font-size: 1.2rem;
            color: var(--text-dim);
            max-width: 600px;
            margin: 0 auto 3rem;
            line-height: 1.6;
        }

        .container {
            width: 100%;
            max-width: 1000px;
            padding: 0 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 45px 0 rgba(0, 255, 170, 0.1);
        }

        .card:hover::before {
            opacity: 1;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .repo-name {
            font-size: 1.5rem;
            font-weight: 600;
            color: #fff;
        }

        .timestamp {
            font-size: 0.9rem;
            color: var(--text-dim);
            font-family: 'JetBrains Mono', monospace;
        }

        .cid-block {
            background: rgba(0,0,0,0.4);
            padding: 1rem;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
            word-break: break-all;
        }

        .cid-link {
            color: var(--accent-color);
            text-decoration: none;
            transition: text-shadow 0.2s ease;
        }

        .cid-link:hover {
            text-shadow: 0 0 8px var(--accent-color);
        }

        .btn-view {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--glass-border);
            color: #fff;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.2s ease;
            white-space: nowrap;
            margin-left: 1rem;
        }

        .btn-view:hover {
            background: var(--accent-color);
            color: #000;
            border-color: var(--accent-color);
            box-shadow: 0 0 15px var(--accent-color);
        }

        .empty-state {
            text-align: center;
            padding: 4rem;
            color: var(--text-dim);
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="orb"></div>
    <header>
        <h1>Sovereign Archive</h1>
        <p class="subtitle">Immutable, content-addressed crystallizations of the BecomingONE and Fieldprint repositories. Preserved permanently on the InterPlanetary File System.</p>
    </header>

    <div class="container">
        {archive_cards}
    </div>

</body>
</html>
"""

card_template = """
        <div class="card">
            <div class="card-header">
                <div class="repo-name">{repo_name}</div>
                <div class="timestamp">{timestamp}</div>
            </div>
            <div class="cid-block">
                <span><a href="/ipfs/{cid}" class="cid-link">{cid}</a></span>
                <a href="/ipfs/{cid}" class="btn-view" target="_blank">Explore</a>
            </div>
        </div>
"""

cards_html = ""
if not archives:
    cards_html = '<div class="empty-state">No archives generated yet.</div>'
else:
    # Sort archives by timestamp descending
    archives.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    for arc in archives:
        cards_html += card_template.format(
            repo_name=arc.get("repo", "Unknown Repo"),
            timestamp=arc.get("timestamp", "Unknown Date"),
            cid=arc.get("cid", "N/A")
        )

final_html = html_template.replace("{archive_cards}", cards_html)

with open(OUTPUT_FILE, "w") as f:
    f.write(final_html)

print("Generated index.html successfully.")
