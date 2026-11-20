"""Persistence checks that do not require Pygame or an SDL display."""
import json
import tempfile
import unittest
from pathlib import Path

from src.save_system import SaveStore


class CheckpointPersistenceTests(unittest.TestCase):
    def test_checkpoint_roundtrip_preserves_loadout_and_collected_pickups(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            store = SaveStore(path)
            store.data["checkpoint"] = {
                "level": 8,
                "index": 2,
                "inventory": ["sword", "shotgun", "machinegun"],
                "slot": 1,
                "max_health": 4,
                "taken": [0, 1, 3],
            }
            store.flush()
            restored = SaveStore(path).data["checkpoint"]
            self.assertEqual(restored["level"], 8)
            self.assertEqual(restored["index"], 2)
            self.assertEqual(restored["inventory"], ["sword", "shotgun", "machinegun"])
            self.assertEqual(restored["slot"], 1)
            self.assertEqual(restored["max_health"], 4)
            self.assertEqual(restored["taken"], [0, 1, 3])

    def test_legacy_checkpoint_without_inventory_does_not_grant_a_weapon(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text(json.dumps({"checkpoint": {"level": 2, "index": 0}}))
            checkpoint = SaveStore(path).data["checkpoint"]
            self.assertEqual(checkpoint["inventory"], [None, None, None])
            self.assertEqual(checkpoint["slot"], 0)

    def test_invalid_checkpoint_fields_are_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text(json.dumps({
                "checkpoint": {
                    "level": 3,
                    "index": 999,
                    "inventory": ["laser", "pistol", None, "shotgun"],
                    "slot": 10,
                    "max_health": 100,
                    "taken": [0, -1, 999, "2"],
                }
            }))
            checkpoint = SaveStore(path).data["checkpoint"]
            self.assertEqual(checkpoint["inventory"], [None, "pistol", None])
            self.assertEqual(checkpoint["slot"], 2)
            self.assertEqual(checkpoint["max_health"], 4)
            self.assertEqual(checkpoint["taken"], [0])


if __name__ == "__main__":
    unittest.main()
