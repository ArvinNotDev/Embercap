# Embercap — The Fifteen Lanterns

**Embercap** is a self-contained, keyboard-controlled 2D action-platformer built with Python and Pygame. Travel through fifteen long-form stages, collect melee and ranged weapons, discover power-ups, fight themed enemies, and defeat the guardian of each route.

The game aims for responsive side-scrolling action, readable encounters, expressive pixel-art environments, and a focused campaign. Its graphics, fonts, and audio are included in the repository; no asset-generation step is required to play.

## Features

- **15 authored stages** with distinct names, themed palettes, editable JSON layouts, moving and collapsing platforms, hazards, collectibles, checkpoints, and a boss arena.
- **Four weapons:** sword, pistol, machine gun, and shotgun, each with a different attack cadence and projectile profile.
- **Three-slot weapon loadout:** pick up with `E`; new weapons fill the first empty slot and equip immediately. When all slots are full, choose `1`, `2`, or `3` to replace that exact slot, or press `Esc` to cancel.
- **Five enemy families:** beetles, winged foes, rams, sentries, and sparks, with different movement and attack behavior.
- **Fifteen named boss encounters** with telegraphed attacks, three difficulty phases, and a vulnerable window that rewards a well-timed crown stomp.
- **Platforming assists:** coyote time, jump buffering, variable jump height, air control, and moving-platform support.
- **Power-ups:** health upgrades, temporary speed, temporary invulnerability, and a limited double-jump ability.
- **Checkpoint recovery:** checkpoints restore health and preserve the current loadout. Each route has a final checkpoint before its boss arena.
- **Persistent progression:** unlocked stages, resume checkpoint, loadout, collected weapon pickups, maximum health, best score, and settings are saved between sessions.
- **Settings:** music and sound-effect volume, fullscreen mode, and particle toggle.

## Requirements

- Python 3.11 or newer
- Pygame 2.6.1 (installed from `requirements.txt`)

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

On Windows, run `play.bat`. On Linux/macOS, run `./play.sh`.

## Controls

| Action | Keys |
|---|---|
| Move | `A` / `D` or `Left` / `Right` |
| Run | `Shift` |
| Jump | `Space`, `W`, or `Up` (hold for a higher jump) |
| Pick up a weapon | `E` (when close to it) |
| Switch loadout slot | `1`, `2`, or `3` |
| Attack / fire | Hold `J` |
| Pause | `Esc` |
| Restart level | `R` (confirmation required) |
| Toggle fullscreen | `F11` |

### Weapon pickup rules

1. If one or more slots are empty, the weapon is stored in the first empty slot and becomes active. Existing weapons are untouched.
2. If all three slots are full, the game pauses for a replacement choice. Press `1`, `2`, or `3` to replace that slot, or `Esc` to cancel.
3. Firearms have unlimited ammunition. Weapon pickups and the active slot are retained after checkpoint respawns and when resuming a saved checkpoint.

## Saves

Save data is stored outside the project directory:

- Windows: `%USERPROFILE%\\.embercap\\save.json`
- Linux/macOS: `~/.embercap/save.json`

Set `EMBERCAP_SAVE_DIR` to choose a different save directory. Save writes use a temporary file followed by an atomic replacement to reduce the chance of corruption after an interrupted write.

## Validation and tests

Validate all fifteen level files and the runtime assets referenced by the game (this check does not require Pygame):

```bash
python tools/validate_project.py
```

Run the automated test suite:

```bash
python -m unittest discover -s tests -v
```

Run a headless startup smoke check:

```bash
# Linux/macOS
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py --smoke 10
```

On Windows PowerShell, set `$env:SDL_VIDEODRIVER='dummy'` and `$env:SDL_AUDIODRIVER='dummy'` before running the same command. Automated tests and smoke checks do not replace a manual playthrough on the target machine.

## Build a clean release ZIP

Create a complete, verified source archive outside the repository directory:

```bash
python tools/package_release.py --output ../Embercap_Enhanced.zip
```

The packaging tool checks required project files, verifies the ZIP CRCs, and excludes `.git`, Python bytecode/cache directories, virtual environments, build outputs, and nested ZIP files. The archive contains the full source project and all runtime assets, not only modified files.

## Project layout

```text
assets/       Graphics, fonts, and audio
levels/       Fifteen editable stage definitions (JSON)
src/          Game loop, player, weapons, enemies, bosses, terrain, saves
tests/        Automated unit and headless integration tests
tools/        Asset/level generation, project validation, release packaging
main.py       Application entry point
```

The weapon definitions and three-slot inventory rules are centralized in `src/weapons.py`. Stage content is data-driven; edit the matching `levels/level_N.json` file to change its terrain, weapon placements, checkpoints, enemies, hazards, or boss configuration.
