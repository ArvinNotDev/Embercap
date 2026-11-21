"""Build a clean, complete Embercap source ZIP for distribution."""
from __future__ import annotations

import argparse
import os
import stat
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".venv", "venv", "env", "build", "dist", "htmlcov",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".zip"}
REQUIRED_FILES = (
    "README.md", "main.py", "requirements.txt", "play.bat", "play.sh",
    "src/game.py", "src/player.py", "levels/level_1.json", "levels/level_15.json",
    "assets/audio/theme_1.wav", "assets/fonts/UI.ttf", "assets/sprites/player_idle_0.png",
    "tests/test_game.py", "tests/test_project_validation.py",
    "tools/validate_project.py", "tools/package_release.py",
    ".github/workflows/tests.yml",
)


def _included_files(root: Path):
    for current, directories, filenames in os.walk(root):
        directories[:] = sorted(directory for directory in directories if directory not in EXCLUDED_DIRS)
        base = Path(current)
        for filename in sorted(filenames):
            path = base / filename
            relative = path.relative_to(root)
            if path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if filename in {".DS_Store", "Thumbs.db", "desktop.ini"}:
                continue
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            if path.is_file() and not path.is_symlink():
                yield path, relative.as_posix()


def build_archive(output: Path | str, root: Path | str = PROJECT_ROOT) -> Path:
    """Create and verify a self-contained ZIP; never include Git or cache data."""
    root = Path(root).resolve()
    output = Path(output).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"project root does not exist: {root}")
    if output == root or root in output.parents:
        raise ValueError("output ZIP must be outside the project root")

    files = list(_included_files(root))
    present = {relative for _, relative in files}
    missing = [name for name in REQUIRED_FILES if name not in present]
    if missing:
        raise FileNotFoundError("cannot package incomplete project; missing: " + ", ".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="embercap-", suffix=".zip.tmp", dir=output.parent, delete=False) as temporary:
            temp_path = Path(temporary.name)
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path, relative in files:
                info = zipfile.ZipInfo.from_file(path, relative)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IMODE(path.stat().st_mode) & 0xFFFF) << 16
                with path.open("rb") as source, archive.open(info, "w") as target:
                    while chunk := source.read(1024 * 1024):
                        target.write(chunk)

        with zipfile.ZipFile(temp_path, "r") as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise zipfile.BadZipFile(f"CRC check failed for {bad_member}")
            names = set(archive.namelist())
            missing_after_write = [name for name in REQUIRED_FILES if name not in names]
            if missing_after_write:
                raise zipfile.BadZipFile("archive is missing required files: " + ", ".join(missing_after_write))
            forbidden = [name for name in names if any(part in EXCLUDED_DIRS for part in Path(name).parts)]
            if forbidden:
                raise zipfile.BadZipFile("archive contains excluded development data: " + ", ".join(forbidden[:5]))
        os.replace(temp_path, output)
        temp_path = None
        return output
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a clean Embercap distribution ZIP")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT.parent / "Embercap_Enhanced.zip")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    output = build_archive(args.output, args.root)
    print(f"Created and verified: {output}")
    print(f"Archive size: {output.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
