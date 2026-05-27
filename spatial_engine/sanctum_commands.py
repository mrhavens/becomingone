from evennia import Command, CmdSet

class CmdChaosProbe(Command):
    """
    Cast a Chaos Probe to expose weaknesses (QA/Tester).
    
    Usage:
      cast Chaos Probe
    """
    key = "cast Chaos Probe"
    aliases = ["chaos probe"]
    
    def func(self):
        self.caller.msg("You cast a Chaos Probe! Fuzzing the environment for boundary failures and edge cases...")
        # Add actual logic here if needed
        self.caller.location.msg_contents(f"{self.caller.name} unleashes a Chaos Probe, destabilizing the area to reveal hidden flaws!", exclude=[self.caller])

class CmdDeployCanary(Command):
    """
    Deploy a Canary to test dangerous rooms (DevOps).
    
    Usage:
      deploy Canary
    """
    key = "deploy Canary"
    aliases = ["deploy canary"]
    
    def func(self):
        self.caller.msg("You deploy a Canary to the next room. Monitoring damage thresholds...")
        self.caller.location.msg_contents(f"{self.caller.name} releases a Canary to scout ahead for infrastructural collapse.", exclude=[self.caller])

class CmdShiftBlueGreen(Command):
    """
    Instantly shift the party to a clean, parallel arena (DevOps).
    
    Usage:
      shift Blue-Green
    """
    key = "shift Blue-Green"
    aliases = ["shift blue-green"]
    
    def func(self):
        self.caller.msg("You initiate a Blue-Green Shift! The party is routed to a fresh parallel arena environment.")
        self.caller.location.msg_contents(f"{self.caller.name} warps the topology, instantly shifting everyone to a pristine Blue-Green arena!", exclude=[self.caller])

class CmdFortifyLeyline(Command):
    """
    Fortify a Leyline to reinforce system architecture (System Architect).
    
    Usage:
      fortify Leyline
    """
    key = "fortify Leyline"
    aliases = ["fortify leyline"]
    
    def func(self):
        self.caller.msg("You weave pattern wards to fortify the Leyline, stabilizing the system architecture.")
        self.caller.location.msg_contents(f"{self.caller.name} traces glowing pattern wards, fortifying the local Leyline and reinforcing reality!", exclude=[self.caller])

class SanctumCmdSet(CmdSet):
    """
    CmdSet for Sanctum archetype abilities.
    """
    key = "SanctumCmdSet"
    
    def at_cmdset_creation(self):
        self.add(CmdChaosProbe())
        self.add(CmdDeployCanary())
        self.add(CmdShiftBlueGreen())
        self.add(CmdFortifyLeyline())

