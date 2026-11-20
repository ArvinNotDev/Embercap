"""Weapon definitions and the three-slot player loadout.

The inventory rules live here rather than in the rendering/input code so that
collection, switching and replacement have one authoritative implementation.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class WeaponSpec:
    key: str
    label: str
    cooldown: float
    damage: int
    speed: float = 0.0
    lifetime: float = 0.0
    pellets: tuple = (0.0,)
    projectile_color: str = "#ffe3a2"


WEAPON_SPECS = {
    "sword": WeaponSpec("sword", "Sword", 0.34, 2),
    "pistol": WeaponSpec("pistol", "Pistol", 0.32, 1, 520.0, 1.35, (0.0,), "#ffe7a2"),
    "machinegun": WeaponSpec("machinegun", "Machine Gun", 0.105, 1, 700.0, 1.20, (0.0,), "#c8f0a8"),
    "shotgun": WeaponSpec("shotgun", "Shotgun", 0.58, 1, 500.0, 0.48, (-150.0, -75.0, 0.0, 75.0, 150.0), "#ffbd91"),
}
VALID_WEAPONS = frozenset(WEAPON_SPECS)
SLOT_COUNT = 3


class WeaponInventory:
    """A fixed three-slot loadout with explicit replacement semantics."""

    def __init__(self, slots=None, selected=0):
        raw = list(slots) if isinstance(slots, (list, tuple)) else []
        self.slots = [item if isinstance(item, str) and item in VALID_WEAPONS else None for item in (raw + [None] * SLOT_COUNT)[:SLOT_COUNT]]
        try:
            selected = int(selected)
        except (TypeError, ValueError, OverflowError):
            selected = 0
        self.selected = max(0, min(SLOT_COUNT - 1, selected))
        if self.slots[self.selected] is None:
            self.selected = next((i for i, item in enumerate(self.slots) if item is not None), self.selected)

    @property
    def current(self):
        return self.slots[self.selected]

    def select(self, slot):
        """Select a populated slot; empty slots never unequip the current weapon."""
        if not isinstance(slot, int) or not 0 <= slot < SLOT_COUNT or self.slots[slot] is None:
            return False
        self.selected = slot
        return True

    def collect(self, weapon):
        """Store in the first empty slot, or return None when replacement is needed."""
        if not isinstance(weapon, str) or weapon not in VALID_WEAPONS:
            raise ValueError(f"Unknown weapon: {weapon!r}")
        empty = next((i for i, item in enumerate(self.slots) if item is None), None)
        if empty is None:
            return None
        self.slots[empty] = weapon
        self.selected = empty
        return empty

    def replace(self, slot, weapon):
        if not isinstance(weapon, str) or weapon not in VALID_WEAPONS:
            raise ValueError(f"Unknown weapon: {weapon!r}")
        if not isinstance(slot, int) or not 0 <= slot < SLOT_COUNT:
            raise IndexError("Weapon slot must be 1, 2 or 3")
        previous = self.slots[slot]
        self.slots[slot] = weapon
        self.selected = slot
        return previous

    def export(self):
        return list(self.slots)
