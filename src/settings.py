"""Game constants. Physics runs at a fixed 120 Hz, rendering at up to 60 Hz."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 640, 360
TILE = 24
FPS = 60
STEP = 1 / 120
GRAVITY = 900.0
JUMP_SPEED = 340.0
WALK_SPEED, RUN_SPEED = 125.0, 185.0
EXTRA_LIFE_SCORE = 3000
TITLE = 'Embercap: The Fifteen Lanterns'
PALETTES = [
    {'sky': '#a4dbd5', 'far': '#72aaa2', 'near': '#477c70', 'top': '#a5d95d', 'soil': '#65513f', 'edge': '#344e42', 'accent': '#ffe6a0'},
    {'sky': '#151e37', 'far': '#273556', 'near': '#384664', 'top': '#87d9d0', 'soil': '#41445f', 'edge': '#242a40', 'accent': '#85f2ed'},
    {'sky': '#b3c8ed', 'far': '#91a6cd', 'near': '#727eab', 'top': '#ede2b3', 'soil': '#8f869c', 'edge': '#4f526f', 'accent': '#fff0bd'},
    {'sky': '#291f32', 'far': '#583044', 'near': '#854139', 'top': '#e4a66b', 'soil': '#66505b', 'edge': '#352e40', 'accent': '#ffb452'},
    {'sky': '#171c32', 'far': '#30314c', 'near': '#484364', 'top': '#b2a6c6', 'soil': '#58516d', 'edge': '#2b2c46', 'accent': '#e4b4fa'}]
