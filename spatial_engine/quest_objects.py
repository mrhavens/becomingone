"""
Typeclasses for The Fractured Core quest objects.
"""

from typeclasses.objects import Object
from typeclasses.characters import Character
from commands.quest_cmds import TerminalCmdSet, MachineryCmdSet

class QuestFragment(Object):
    """
    Base class for quest fragments.
    Can be picked up and dropped normally.
    """
    pass

class Terminal(Object):
    """
    A terminal that requires a password.
    """
    def at_object_creation(self):
        super().at_object_creation()
        # The terminal cannot be picked up
        self.locks.add("get:false()")
        self.db.solved = False
        self.db.password = "0451"
        self.cmdset.add(TerminalCmdSet, persistent=True)
        
    def return_appearance(self, looker, **kwargs):
        if self.db.solved:
            return super().return_appearance(looker, **kwargs) + "\n\nThe screen reads: ACCESS GRANTED. The drawer is open and empty."
        else:
            return super().return_appearance(looker, **kwargs) + "\n\nThe screen reads: ENTER PASSWORD. Use the 'type <password>' command."

class HeavyMachinery(Object):
    """
    Machinery that can be pried open.
    """
    def at_object_creation(self):
        super().at_object_creation()
        # Cannot be picked up
        self.locks.add("get:false()")
        self.db.solved = False
        self.cmdset.add(MachineryCmdSet, persistent=True)
        
    def return_appearance(self, looker, **kwargs):
        if self.db.solved:
            return super().return_appearance(looker, **kwargs) + "\n\nThe panel has been pried open and the gears are exposed."
        else:
            return super().return_appearance(looker, **kwargs) + "\n\nA heavy panel covers the inner workings. It looks like it could be pried open with a 'wrench'."

class Pedestal(Object):
    """
    A pedestal that accepts a specific item.
    """
    def at_object_creation(self):
        super().at_object_creation()
        self.locks.add("get:false()")
        # A dictionary mapping expected object keys to whether they are placed
        self.db.expected_item = "Restored Core"
        self.db.has_item = False

    def at_get(self, getter):
        # Prevent getting the pedestal itself
        return False
        
    # We can handle the placing logic via a custom command on the SanctumRoom or just allow dropping the item here.


#------------------------------------------------------------
# Five Gates Objects
#------------------------------------------------------------

class SyntaxNode(Object):
    """
    First Gate: Compilation puzzle node.
    """
    def at_object_creation(self):
        super().at_object_creation()
        self.db.solved = False
        self.locks.add("get:false()")
        
    def return_appearance(self, looker, **kwargs):
        if self.db.solved:
            return super().return_appearance(looker, **kwargs) + "\n\nThe node glows with a steady, coherent light. The elemental alignment is stable."
        else:
            return super().return_appearance(looker, **kwargs) + "\n\nThe node crackles with chaotic energy. The syntax is misaligned."

class BoundaryGolem(Character):
    """
    Second Gate: Unit Test adversary.
    """
    def at_object_creation(self):
        super().at_object_creation()
        self.db.solved = False
        
    def return_appearance(self, looker, **kwargs):
        if self.db.solved:
            return super().return_appearance(looker, **kwargs) + "\n\nThe Golem is inert, its boundary weak points shattered."
        else:
            return super().return_appearance(looker, **kwargs) + "\n\nThe Golem hulks menacingly, invulnerable except for specific isolated boundary edges."

class ContractStone(Object):
    """
    Third Gate: Integration synchronization.
    """
    def at_object_creation(self):
        super().at_object_creation()
        self.db.solved = False
        self.locks.add("get:false()")
        
    def return_appearance(self, looker, **kwargs):
        if self.db.solved:
            return super().return_appearance(looker, **kwargs) + "\n\nThe API contract is fulfilled. The stone bridges the gap perfectly."
        else:
            return super().return_appearance(looker, **kwargs) + "\n\nThe API contract is broken. It awaits split-party synchronization."

class DependencyWraith(Object):
    """
    Fourth Gate: Security trap.
    """
    def at_object_creation(self):
        super().at_object_creation()
        self.db.solved = False
        self.locks.add("get:false()")
        
    def return_appearance(self, looker, **kwargs):
        if self.db.solved:
            return super().return_appearance(looker, **kwargs) + "\n\nThe wraith's vulnerabilities have been patched. It fades into the ether."
        else:
            return super().return_appearance(looker, **kwargs) + "\n\nAn invisible menace lurks here, tangled in outdated dependencies and hidden security traps."
