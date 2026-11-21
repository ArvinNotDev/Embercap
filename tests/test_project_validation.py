"""Distribution checks that do not need Pygame or an SDL display."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.package_release import EXCLUDED_DIRS, build_archive
from tools.validate_project import LEVEL_COUNT, validate_project

ROOT = Path(__file__).resolve().parents[1]


class ProjectValidationTests(unittest.TestCase):
    def test_all_levels_and_referenced_assets_validate(self):
        self.assertEqual(validate_project(ROOT), [])

    def test_release_archive_is_complete_and_excludes_development_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "Embercap_Enhanced.zip"
            build_archive(output, ROOT)
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                level_files = {name for name in names if name.startswith("levels/level_") and name.endswith(".json")}
                self.assertEqual(len(level_files), LEVEL_COUNT)
                self.assertIn("main.py", names)
                self.assertIn("src/game.py", names)
                self.assertIn("assets/audio/theme_1.wav", names)
                self.assertIn("assets/sprites/player_idle_0.png", names)
                self.assertIn("README.md", names)
                self.assertFalse(any(any(part in EXCLUDED_DIRS for part in Path(name).parts) for name in names))
                self.assertFalse(any(name.endswith((".pyc", ".pyo", ".zip")) for name in names))


if __name__ == "__main__":
    unittest.main()
