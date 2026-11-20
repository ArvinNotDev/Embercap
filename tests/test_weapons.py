"""Fast unit tests for weapon slots; no SDL or rendering dependency."""
import unittest

from src.weapons import SLOT_COUNT, VALID_WEAPONS, WEAPON_SPECS, WeaponInventory


class WeaponInventoryTests(unittest.TestCase):
    def test_new_loadout_has_three_empty_slots(self):
        loadout = WeaponInventory()
        self.assertEqual(loadout.export(), [None, None, None])
        self.assertIsNone(loadout.current)

    def test_pickup_fills_first_empty_slot_and_equips_it(self):
        loadout = WeaponInventory()
        self.assertEqual(loadout.collect("sword"), 0)
        self.assertEqual(loadout.collect("pistol"), 1)
        self.assertEqual(loadout.collect("machinegun"), 2)
        self.assertEqual(loadout.export(), ["sword", "pistol", "machinegun"])
        self.assertEqual(loadout.selected, 2)
        self.assertEqual(loadout.current, "machinegun")

    def test_full_inventory_never_overwrites_without_confirmation(self):
        loadout = WeaponInventory(["sword", "pistol", "machinegun"])
        before = loadout.export()
        self.assertIsNone(loadout.collect("shotgun"))
        self.assertEqual(loadout.export(), before)

    def test_empty_slot_cannot_unequip_current_weapon(self):
        loadout = WeaponInventory(["sword", None, "shotgun"], selected=0)
        self.assertFalse(loadout.select(1))
        self.assertEqual(loadout.selected, 0)
        self.assertEqual(loadout.current, "sword")
        self.assertTrue(loadout.select(2))
        self.assertEqual(loadout.current, "shotgun")

    def test_replacement_changes_only_the_chosen_slot(self):
        loadout = WeaponInventory(["sword", "pistol", "machinegun"])
        previous = loadout.replace(1, "shotgun")
        self.assertEqual(previous, "pistol")
        self.assertEqual(loadout.export(), ["sword", "shotgun", "machinegun"])
        self.assertEqual(loadout.selected, 1)
        self.assertEqual(loadout.current, "shotgun")

    def test_loadout_repairs_legacy_or_corrupt_data(self):
        loadout = WeaponInventory(["not-a-weapon", "pistol"], selected=99)
        self.assertEqual(loadout.export(), [None, "pistol", None])
        self.assertEqual(loadout.selected, 1)
        self.assertEqual(len(loadout.export()), SLOT_COUNT)

    def test_weapon_definitions_have_expected_combat_profiles(self):
        self.assertEqual(set(WEAPON_SPECS), set(VALID_WEAPONS))
        self.assertEqual(len(WEAPON_SPECS["shotgun"].pellets), 5)
        self.assertLess(WEAPON_SPECS["machinegun"].cooldown, WEAPON_SPECS["pistol"].cooldown)
        self.assertGreater(WEAPON_SPECS["shotgun"].damage, 0)
        self.assertGreater(WEAPON_SPECS["pistol"].lifetime, 0)

    def test_invalid_weapon_and_slot_are_rejected(self):
        loadout = WeaponInventory(["sword", "pistol", "machinegun"])
        with self.assertRaises(ValueError):
            loadout.collect("bazooka")
        with self.assertRaises(ValueError):
            loadout.replace(0, "bazooka")
        with self.assertRaises(IndexError):
            loadout.replace(3, "shotgun")


if __name__ == "__main__":
    unittest.main()
