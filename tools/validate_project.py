"""Validate Embercap's 15 authored levels and runtime assets without Pygame."""
from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEVEL_COUNT = 15
WEAPONS = {"sword", "pistol", "machinegun", "shotgun"}
SOLIDS = {"ground", "platform", "moving", "collapse", "break", "block"}
ENEMIES = {"beetle", "wing", "ram", "sentry", "spark"}
HAZARDS = {"water", "lava", "vent", "trap", "rock", "saw"}
POWERUPS = {"health", "speed", "star", "wings"}
PLAYER_STATES = ("idle", "walk", "run", "jump", "fall", "land", "hurt", "death", "transform")
LIST_FIELDS = ("solids", "enemies", "hazards", "coins", "powerups", "weapon_pickups", "checkpoints", "decor", "signs")
SFX = ("boss", "break", "checkpoint", "click", "coin", "hurt", "jump", "over", "power", "stomp", "victory")
REQUIRED_FILES = (
    "README.md", "main.py", "play.bat", "play.sh", "requirements.txt",
    "src/game.py", "src/player.py", "src/level.py", "src/weapons.py", "src/save_system.py",
    "tests/test_game.py", "tools/package_release.py",
)


def _pair(value):
    return isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)


def validate_project(root: Path | str = ROOT) -> list[str]:
    """Return validation errors; an empty list means the project is distributable."""
    root = Path(root).resolve()
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append(f"missing required file: {name}")

    sprites = root / "assets" / "sprites"
    sprite_names = {p.stem for p in sprites.glob("*.png")} if sprites.is_dir() else set()
    for path in sprites.glob("*.png") if sprites.is_dir() else ():
        try:
            if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                errors.append(f"invalid PNG: {path.relative_to(root)}")
        except OSError as exc:
            errors.append(f"cannot read {path.relative_to(root)}: {exc}")

    for name in ("Title.ttf", "UI.ttf", "LICENSE.txt"):
        if not (root / "assets" / "fonts" / name).is_file():
            errors.append(f"missing font/license: assets/fonts/{name}")
    for state in PLAYER_STATES:
        for frame in range(4):
            if f"player_{state}_{frame}" not in sprite_names:
                errors.append(f"missing player sprite: player_{state}_{frame}.png")
    for name in ("decor_0", "decor_1", "decor_2", "decor_3", "decor_4", "boss_0", "boss_1", "boss_2", "boss_3"):
        if name not in sprite_names:
            errors.append(f"missing sprite: {name}.png")
    for frame in range(6):
        if f"coin_{frame}" not in sprite_names:
            errors.append(f"missing coin sprite: coin_{frame}.png")

    audio = root / "assets" / "audio"
    for name in (*SFX, *(f"theme_{i}" for i in range(1, 6))):
        path = audio / f"{name}.wav"
        if not path.is_file():
            errors.append(f"missing audio: {path.relative_to(root)}")
        elif name in SFX:
            try:
                with wave.open(str(path), "rb") as sound:
                    if sound.getnchannels() < 1 or sound.getframerate() < 1 or sound.getnframes() < 1:
                        errors.append(f"empty audio: {path.relative_to(root)}")
            except (OSError, wave.Error) as exc:
                errors.append(f"invalid audio {path.relative_to(root)}: {exc}")

    levels_dir = root / "levels"
    paths = sorted(levels_dir.glob("level_*.json"), key=lambda p: int(p.stem.split("_")[-1]) if p.stem.split("_")[-1].isdigit() else 999)
    if len(paths) != LEVEL_COUNT:
        errors.append(f"expected {LEVEL_COUNT} level JSON files, found {len(paths)}")
    names: set[str] = set()
    bosses: set[str] = set()
    for path in paths:
        label = path.relative_to(root).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: invalid JSON ({exc})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{label}: top-level JSON value must be an object")
            continue
        required = {"id", "name", "width", "height", "spawn", "exit", "boss", *LIST_FIELDS}
        missing = required - data.keys()
        if missing:
            errors.append(f"{label}: missing fields: {', '.join(sorted(missing))}")
            continue
        number = int(path.stem.split("_")[-1]) if path.stem.split("_")[-1].isdigit() else -1
        if data["id"] != number:
            errors.append(f"{label}: id does not match filename")
        if not isinstance(data["name"], str) or not data["name"].strip() or data["name"] in names:
            errors.append(f"{label}: level name is empty or duplicated")
        names.add(data["name"] if isinstance(data["name"], str) else "")
        if not isinstance(data["width"], (int, float)) or data["width"] <= 0 or not isinstance(data["height"], (int, float)) or data["height"] <= 0:
            errors.append(f"{label}: width/height must be positive")
            continue
        if not _pair(data["spawn"]) or not isinstance(data["exit"], (int, float)) or not 0 <= data["exit"] < data["width"]:
            errors.append(f"{label}: invalid spawn or exit")
        for field in LIST_FIELDS:
            if not isinstance(data[field], list):
                errors.append(f"{label}: {field} must be a list")

        palette = (number - 1) % 5
        for solid in data["solids"] if isinstance(data["solids"], list) else ():
            if not isinstance(solid, dict) or solid.get("kind") not in SOLIDS:
                errors.append(f"{label}: invalid solid definition")
                continue
            if not all(isinstance(solid.get(k), (int, float)) for k in ("x", "y", "w", "h")) or solid["w"] <= 0 or solid["h"] <= 0:
                errors.append(f"{label}: invalid solid geometry")
            if f"tile_{palette}_{solid['kind']}" not in sprite_names:
                errors.append(f"{label}: missing terrain sprite tile_{palette}_{solid['kind']}.png")
            if solid["kind"] == "moving" and (solid.get("axis") not in ("x", "y") or not isinstance(solid.get("period"), (int, float)) or solid["period"] <= 0 or not isinstance(solid.get("distance"), (int, float))):
                errors.append(f"{label}: invalid moving platform")

        for enemy in data["enemies"] if isinstance(data["enemies"], list) else ():
            kind = enemy.get("kind") if isinstance(enemy, dict) else None
            if kind not in ENEMIES:
                errors.append(f"{label}: invalid enemy kind {kind!r}")
                continue
            for frame in range(4):
                if f"{kind}_{frame}" not in sprite_names:
                    errors.append(f"{label}: missing enemy sprite {kind}_{frame}.png")

        pickups = data["weapon_pickups"] if isinstance(data["weapon_pickups"], list) else ()
        if {item.get("weapon") for item in pickups if isinstance(item, dict)} != WEAPONS:
            errors.append(f"{label}: must contain all four weapon pickup types")
        for item in data["powerups"] if isinstance(data["powerups"], list) else ():
            kind = item.get("kind") if isinstance(item, dict) else None
            if kind not in POWERUPS or kind not in sprite_names:
                errors.append(f"{label}: invalid or missing power-up sprite {kind!r}")
        if len(data["checkpoints"]) < 2 if isinstance(data["checkpoints"], list) else True:
            errors.append(f"{label}: expected at least two checkpoints")
        for point in data["checkpoints"] if isinstance(data["checkpoints"], list) else ():
            if not _pair(point):
                errors.append(f"{label}: invalid checkpoint coordinate")

        for hazard in data["hazards"] if isinstance(data["hazards"], list) else ():
            if not isinstance(hazard, dict) or hazard.get("kind") not in HAZARDS:
                errors.append(f"{label}: invalid hazard definition")
                continue
            if not all(isinstance(hazard.get(k), (int, float)) for k in ("x", "y", "w", "h")):
                errors.append(f"{label}: hazard has invalid geometry")
            if hazard["kind"] in {"vent", "trap", "rock", "saw"} and (not isinstance(hazard.get("period"), (int, float)) or hazard["period"] <= 0):
                errors.append(f"{label}: periodic hazard requires a positive period")

        boss = data["boss"]
        if not isinstance(boss, dict):
            errors.append(f"{label}: boss definition must be an object")
        else:
            boss_name = boss.get("type")
            arena = boss.get("arena")
            if not isinstance(boss_name, str) or not boss_name.strip() or boss_name in bosses:
                errors.append(f"{label}: boss type is empty or duplicated")
            bosses.add(boss_name if isinstance(boss_name, str) else "")
            if not isinstance(boss.get("hp"), (int, float)) or boss["hp"] <= 0:
                errors.append(f"{label}: boss HP must be positive")
            if not _pair(arena) or arena[0] >= arena[1] or not isinstance(boss.get("x"), (int, float)) or not arena[0] < boss["x"] < arena[1]:
                errors.append(f"{label}: invalid boss arena or position")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Embercap's level data and runtime assets")
    parser.add_argument("--root", type=Path, default=ROOT, help="project root (defaults to this repository)")
    errors = validate_project(parser.parse_args().root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed: {len(errors)} problem(s).")
        return 1
    print("Project validation passed: all 15 levels and referenced runtime assets are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
