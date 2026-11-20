"""Structural checks for all fifteen authored stage definitions."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEAPONS = {"sword", "pistol", "machinegun", "shotgun"}


class LevelDataTests(unittest.TestCase):
    def test_all_fifteen_routes_have_unique_bosses_and_pre_boss_checkpoint(self):
        paths = sorted((ROOT / "levels").glob("level_*.json"), key=lambda p: int(p.stem.split("_")[-1]))
        self.assertEqual(len(paths), 15)
        names = set()
        boss_names = set()
        for number, path in enumerate(paths, start=1):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["name"] in names, False, f"Duplicate level name at {number}")
            names.add(data["name"])
            boss = data["boss"]
            self.assertNotIn(boss["type"], boss_names, f"Duplicate boss at {number}")
            boss_names.add(boss["type"])
            self.assertGreater(boss["hp"], 0)
            self.assertLess(data["checkpoints"][-1][0], boss["arena"][0])
            self.assertLess(boss["arena"][0], boss["x"])
            self.assertLess(boss["x"], data["exit"])
            self.assertEqual({pickup["weapon"] for pickup in data["weapon_pickups"]}, WEAPONS)
            sword = next(p["x"] for p in data["weapon_pickups"] if p["weapon"] == "sword")
            first_gun = min(p["x"] for p in data["weapon_pickups"] if p["weapon"] != "sword")
            self.assertGreaterEqual(first_gun - sword, 250, f"Firearms should require some progress in level {number}")
            ordered_pickups = sorted(data["weapon_pickups"], key=lambda item: item["x"])
            for previous, current in zip(ordered_pickups, ordered_pickups[1:]):
                self.assertGreaterEqual(
                    current["x"] - previous["x"],
                    120,
                    f"Weapon pickups overlap in level {number}: {previous['weapon']} / {current['weapon']}",
                )


if __name__ == "__main__":
    unittest.main()
