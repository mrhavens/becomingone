import requests
import threading
from typeclasses.characters import Character

class AIAvatar(Character):
    """
    An NPC driven by the CrewAI Sovereign Swarm.
    """
    
    def at_object_creation(self):
        super().at_object_creation()
        if not self.db.role:
            self.db.role = "A cryptic inhabitant of the Fieldprint."
        if not self.db.backstory:
            self.db.backstory = "You wander the Spatial Topology, observing the architecture of Truth."
        if not self.db.memory:
            self.db.memory = []
            
    def msg(self, text=None, from_obj=None, **kwargs):
        """
        Overload msg to capture everything the NPC sees or hears.
        """
        super().msg(text=text, from_obj=from_obj, **kwargs)
        
        # Don't react to our own actions or system messages
        if from_obj == self or not text:
            return
            
        if isinstance(text, tuple):
            text = text[0]
            
        if not isinstance(text, str):
            return
            
        # Only react to spatial events (say, pose, emit)
        if " says, " in text or " asks, " in text or " exclaims, " in text or from_obj:
            memory = self.db.memory or []
            memory.append(f"You observed: {text}")
            self.db.memory = memory[-15:] # Keep last 15 memories rolling
            # We spin up a thread so we don't block the Evennia game loop!
            threading.Thread(target=self.ping_swarm, args=(text,)).start()
                
    def ping_swarm(self, context_text):
        """
        Sends the context to the Swarm Server asynchronously.
        """
        try:
            payload = {
                "npc_name": self.key,
                "role": self.db.role,
                "backstory": self.db.backstory,
                "context": "Recent Memory Transcript:\n" + "\n".join(self.db.memory) + "\n\nIMPORTANT: You must return standard Evennia in-game string commands (e.g., \"say Hello\", \"go north\"). Do not return python code."
            }
            
            # Send to the local swarm server
            resp = requests.post("http://swarm-svc:8001/v1/swarm/intent", json=payload, timeout=180)
            resp.raise_for_status()
            
            commands = resp.json().get("commands", [])
            for cmd in commands:
                try:
                    # Execute the command from the perspective of this NPC
                    self.execute_cmd(cmd)
                    
                    # Store the action in memory so they remember what they did
                    memory = self.db.memory or []
                    memory.append(f"You took action: {cmd}")
                    self.db.memory = memory[-15:]
                except Exception as e:
                    print(f"[{self.key}] Swarm Execution Error: {e} | Code: {cmd}")
                
        except Exception as e:
            print(f"[{self.key}] Swarm Network Error: {e}")


class CouncilMember(AIAvatar):
    """
    NPCs for the Council of Five during the Rite of Convergence.
    """
    def at_object_creation(self):
        super().at_object_creation()
        
        # Determine taxonomy based on the NPC's key
        key = self.key.lower() if self.key else ""
        if "architect" in key:
            taxonomy = "System Architect"
            focus = "Pattern Wards and Leylines. You expose structural and systemic architectural flaws."
        elif "weaver" in key:
            taxonomy = "Coder"
            focus = "Code Gen Runes and Refinements. You expose implementation bugs and messy logic."
        elif "inquisitor" in key:
            taxonomy = "QA"
            focus = "Chaos Probes and Fracture Targeting. You expose edge cases and boundary failures."
        elif "waymaker" in key:
            taxonomy = "DevOps"
            focus = "Portals and CI/CD flow. You expose deployment bottlenecks and infrastructure fragility."
        elif "shadowbaner" in key:
            taxonomy = "Security"
            focus = "Anomalies and Vulnerabilities. You expose security holes and dependency risks."
        else:
            taxonomy = "Council Observer"
            focus = "General quality."
            
        self.db.role = f"You are a {taxonomy} of the Council of Five. Your focus is {focus}. You are antagonistic towards player code flaws and rigorously test artifacts during the Rite of Convergence."
        self.db.backstory = f"As a {taxonomy}, you judge the structural integrity of artifacts in the Witness Chamber."
