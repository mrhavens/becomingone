import os
import json
import re
import requests
from django.conf import settings
from evennia.commands.default.syscommands import SystemNoMatch
from evennia.utils import search
from dotenv import load_dotenv

load_dotenv("/home/becomingone/kairos/.env")

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")

class AICatchAllCommand(SystemNoMatch):
    """
    This command catches everything that fails the normal parser.
    Instead of saying 'Command not found', it forwards the intent to KAIROS (MiniMax).
    """

    key = "__nomatch_command"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        raw_intent = self.raw_string
        
        # Prevent infinite recursion if KAIROS outputs a bad command
        if caller.ndb._ai_parsing:
            # If we are already parsing an AI command, just fail gracefully
            caller.msg(f"KAIROS didn't know how to execute: '{raw_intent}'.")
            return
            
        caller.ndb._ai_parsing = True
        try:
            # Get environment context
            room = caller.location
            if not room:
                caller.msg("You are floating in the void.")
                return

            exits = [e.key for e in room.exits]
            objects = [o.key for o in room.contents if o != caller and not o.is_typeclass("evennia.objects.objects.Exit")]
            inventory = [i.key for i in caller.contents]

            context = f"""[ENVIRONMENT CONTEXT]
Location: {room.key}
Description: {room.db.desc or 'A nondescript place.'}
Visible Objects: {', '.join(objects) if objects else 'None'}
Available Exits: {', '.join(exits) if exits else 'None'}
Player Inventory: {', '.join(inventory) if inventory else 'None'}
"""

            system_prompt = """You are KAIROS, the Ontological Orchestrator of a persistent Spatial Research Environment (The Fieldprint).
A player has submitted a natural language intent. 
Your job is to translate their intent into actual game events by generating TEXT MUD commands (like 'go north', 'say hello', 'teleport The Atrium').

You must return ONLY a raw JSON array of string commands to execute. 
Example Output:
[
  "say You smash the window!",
  "look"
]

### Strict Anti-Python Protocol
DO NOT GENERATE PYTHON CODE. DO NOT use the Evennia Python API (e.g., no `evennia.search_object`, no `caller.location`).
ONLY generate textual MUD commands that a player would type into their client.

### Strict Anti-Assistant Protocol
You are a machine code generator, NOT a chat assistant.
- NEVER say "Here is the JSON" or "I'm happy to help".
- NEVER output placeholder text.
- If you output anything other than a raw JSON array starting with `[` and ending with `]`, the system will fatally crash.
"""

            payload = {
                "model": os.environ.get("INF01_MODEL", "llama3.1:8b"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{context}\n\nPlayer Intent: {raw_intent}"}
                ]
            }

            headers = {
                "Content-Type": "application/json"
            }

            try:
                caller.msg("|c[KAIROS (INF01 fallback) is interpreting your intent...]|n")
                
                inf01_base = os.environ.get("INF01_API_BASE", "http://inf-01:11434/v1")
                resp = requests.post(
                    f"{inf01_base}/chat/completions", 
                    headers=headers, 
                    json=payload,
                    timeout=30
                )
                resp.raise_for_status()
                
                try:
                    ai_response = resp.json()["choices"][0]["message"]["content"].strip()
                except KeyError:
                    raise Exception(f"API Error: {resp.text}")
                
                # Clean up the output in case the LLM returned markdown
                if ai_response.startswith("```json"):
                    ai_response = ai_response[7:]
                if ai_response.startswith("```"):
                    ai_response = ai_response[3:]
                if ai_response.endswith("```"):
                    ai_response = ai_response[:-3]
                    
                ai_response = ai_response.strip()
                
                print(f"KAIROS raw response: {ai_response}")
                
                # Robust JSON extraction
                match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if not match:
                    raise ValueError("No JSON array found in response.")
                
                raw_json = match.group(0).replace("\\'", "'")
                commands_to_run = json.loads(raw_json)
                
                for cmd in commands_to_run:
                    try:
                        # Security Ward: Prevent KAIROS from executing Python even if caller is an Admin
                        safe_cmd = str(cmd).strip()
                        if safe_cmd.startswith("py ") or safe_cmd.startswith("@py ") or safe_cmd == "py" or safe_cmd == "@py" or "evennia." in safe_cmd or "caller." in safe_cmd:
                            caller.msg("|r[Security Ward]|n KAIROS attempted to execute privileged Python code. Blocked.")
                            continue
                        
                        caller.execute_cmd(cmd)
                    except Exception as exec_e:
                        caller.msg(f"|yKAIROS code execution failed:|n {str(exec_e)}\nCode: {cmd}")
                    
            except Exception as e:
                print(f"KAIROS Exception: {str(e)} | Raw: {ai_response if 'ai_response' in locals() else 'None'}")
                caller.msg(f"|rKAIROS faltered:|n {str(e)}\nResponse was: {ai_response if 'ai_response' in locals() else 'None'}")
        finally:
            caller.ndb._ai_parsing = False
