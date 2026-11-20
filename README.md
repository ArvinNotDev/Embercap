# Embercap — The Fifteen Lanterns

A self-contained, keyboard-controlled 2D action platformer built with Python and Pygame. Explore fifteen long-form stages, collect melee and ranged weapons, fight themed enemies, and defeat the boss guarding each route.

## Features

- **15 stages** with editable JSON layouts, hazards, moving platforms, collectibles, and a stage boss.
- **Four weapons:** sword, pistol, machine gun, and shotgun. Each stage starts without a firearm; the sword is placed early, with the first gun further along the route.
- **Three-slot loadout:** pick up with `E`; new weapons fill the first empty slot and equip immediately. When all slots are occupied, choose `1`, `2`, or `3` to replace that exact slot, or press `Esc` to leave the weapon on the ground.
- **Distinct combat profiles:** short-range melee, balanced pistol fire, rapid machine-gun fire, and a five-pellet shotgun spread.
- **Unlimited firearm ammunition.**
- **Checkpoint recovery:** checkpoints restore health and preserve collected weapons. Every route has a final checkpoint before its boss arena.
- **Persistent progress:** the latest checkpoint, loadout, collected weapon pickups, maximum health, and unlocked stage are saved between sessions. Resuming starts at the saved checkpoint rather than the player's last frame position.
- Original graphics and audio are included; no asset-generation step is needed to play.

## Requirements

- Python 3.11 or newer
- Pygame 2.6.1

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

On Windows, `play.bat` is also provided. On Linux/macOS, run `./play.sh`.

## Controls

| Action | Keys |
|---|---|
| Move | `A` / `D` or `Left` / `Right` |
| Run | `Shift` |
| Jump | `Space`, `W`, or `Up` |
| Pick up a weapon | `E` (when close to it) |
| Switch loadout slot | `1`, `2`, or `3` (only populated slots equip) |
| Attack / fire | Hold `J` |
| Pause | `Esc` |
| Restart level | `R` (confirmation required) |
| Toggle fullscreen | `F11` |

### Weapon pickup rules

1. If one or more slots are empty, the weapon is stored in the first empty slot and becomes active. Existing weapons are untouched.
2. If all three slots are full, the game pauses for a short replacement choice. Press `1`, `2`, or `3` to replace that slot, or `Esc` to cancel.
3. Firearms have unlimited ammunition. Weapon pickups and the active slot are retained after checkpoint respawns and when resuming a saved checkpoint.

## Saves

By default, save data is stored at:

- Windows: `%USERPROFILE%\.embercap\save.json`
- Linux/macOS: `~/.embercap/save.json`

Set `EMBERCAP_SAVE_DIR` to choose a different save directory. The game writes saves atomically so an interrupted write is less likely to corrupt progress.

## Tests

Run the automated suite:

```bash
python -m unittest discover -s tests -v
```

The suite includes fast, SDL-independent unit tests for loadout rules, save-data validation, and all fifteen level definitions, plus headless Pygame integration tests for movement, weapon pickup/replacement, checkpoint respawns, bosses, progression, and route traversal. Automated tests do not replace a manual playthrough on the target machine.

A startup smoke check can be run with dummy SDL drivers:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python main.py --smoke 10
```

## Project layout

```text
assets/       Graphics, fonts, and audio
levels/       Fifteen editable stage definitions (JSON)
src/          Game loop, player, weapons, enemies, bosses, terrain, saves
tests/        Headless integration and weapon-loadout unit tests
tools/        Asset and level generation utilities
main.py       Application entry point
```

## Development notes

The weapon definitions and three-slot inventory rules are centralized in `src/weapons.py`. Stage content is data-driven; edit the matching `levels/level_N.json` file to change a route, its weapon placements, checkpoints, enemies, or boss configuration.
