import os
import sys
import pygame

pygame.init()
pygame.mixer.init()

def get_asset_path(filename):
    """Resolves correct path for assets in the local res directory."""
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "res", filename)

# Visual Constants
BOARD_WIDTH, BOARD_HEIGHT = 600, 600
TOP_PANEL_HEIGHT = 80
BOTTOM_PANEL_HEIGHT = 80
TOTAL_WIDTH = BOARD_WIDTH  # 600px wide
TOTAL_HEIGHT = TOP_PANEL_HEIGHT + BOARD_HEIGHT + BOTTOM_PANEL_HEIGHT  # 760px high

# Frame Offset Adjustments
BOARD_PADDING = 12
PLAYABLE_WIDTH = BOARD_WIDTH - (BOARD_PADDING * 2)
PLAYABLE_HEIGHT = BOARD_HEIGHT - (BOARD_PADDING * 2)

ROWS, COLS = 8, 8
SQUARE_SIZE_X = PLAYABLE_WIDTH / COLS
SQUARE_SIZE_Y = PLAYABLE_HEIGHT / COLS

# Game Settings: 2 Minutes Total Bank per Player
INITIAL_TIME_LIMIT = 120

# Colors
RED = (200, 50, 50)
BROWN = (120, 60, 20)  # Player 2 border & crown color
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (50, 120, 200)
GREEN = (40, 160, 60)
HIGHLIGHT = (255, 255, 100)
PANEL_BG = (45, 45, 45)
TEXT_WHITE = (255, 255, 255)
OVERLAY_BG = (0, 0, 0, 180)
GOLD = (255, 215, 0)

WIN = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
pygame.display.set_caption("AMAD - Custom Face Pieces")
FONT_UI = pygame.font.SysFont("arial", 15, bold=True)
FONT_TIMER = pygame.font.SysFont("arial", 18, bold=True)
FONT_START_BTN = pygame.font.SysFont("arial", 22, bold=True)
FONT_POPUP_TITLE = pygame.font.SysFont("arial", 26, bold=True)
FONT_POPUP_BTN = pygame.font.SysFont("arial", 18, bold=True)

# Load Board Image Dynamically from res/
BOARD_IMAGE_PATH = get_asset_path("board.png")

try:
    raw_board_img = pygame.image.load(BOARD_IMAGE_PATH)
    BOARD_IMG = pygame.transform.smoothscale(raw_board_img, (BOARD_WIDTH, BOARD_HEIGHT))
except Exception as e:
    print(f"Warning: Could not load board image ({e}).")
    BOARD_IMG = None

# --- LOAD AUDIO FILES ---
# Audio Asset Paths (Relative to res/)
BACKGROUND_MUSIC_PATH = get_asset_path("L's theme A.mp3")
KILL_SINGLE_PATH       = get_asset_path("faaah.mp3")
KILL_DOUBLE_PATH       = get_asset_path("announcer_kill_double_01.mp3")
KILL_TRIPLE_PATH       = get_asset_path("announcer_kill_triple_01.mp3")
CELEBRATE_MUSIC_PATH   = get_asset_path("celebrate-good-time-celebration.mp3")

MUSIC_LOADED = False
SOUND_SINGLE = None
SOUND_DOUBLE = None
SOUND_TRIPLE = None
SOUND_CELEBRATE = None

if os.path.exists(BACKGROUND_MUSIC_PATH):
    try:
        pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
        MUSIC_LOADED = True
    except Exception as e:
        print(f"Warning: Could not load music ({e}).")

if os.path.exists(KILL_SINGLE_PATH):
    try:
        SOUND_SINGLE = pygame.mixer.Sound(KILL_SINGLE_PATH)
    except Exception as e:
        print(f"Warning: Could not load single kill SFX ({e}).")

if os.path.exists(KILL_DOUBLE_PATH):
    try:
        SOUND_DOUBLE = pygame.mixer.Sound(KILL_DOUBLE_PATH)
    except Exception as e:
        print(f"Warning: Could not load double kill SFX ({e}).")

if os.path.exists(KILL_TRIPLE_PATH):
    try:
        SOUND_TRIPLE = pygame.mixer.Sound(KILL_TRIPLE_PATH)
    except Exception as e:
        print(f"Warning: Could not load triple kill SFX ({e}).")

# Celebration Victory Music Loop
if os.path.exists(CELEBRATE_MUSIC_PATH):
    try:
        SOUND_CELEBRATE = pygame.mixer.Sound(CELEBRATE_MUSIC_PATH)
    except Exception as e:
        print(f"Warning: Could not load celebration SFX ({e}).")