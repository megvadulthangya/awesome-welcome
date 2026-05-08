"""Configuration constants and global flags."""
import os

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================
APP_TITLE = "Manjaro Awesome Respin AI Welcome"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
AUTOSTART_FILE = os.path.join(AUTOSTART_DIR, "awesome-welcome.desktop")
SOURCE_DESKTOP_FILE = "/usr/share/applications/awesome-welcome.desktop"

LINKS_PROJECT = {
    "GitHub Repo": "https://github.com/megvadulthangya/iso-profiles",
    "\u2615Buy me a Coffee": "https://buymeacoffee.com/rohambili",
}
LINKS_MANJARO = {
    "Manjaro Forum": "https://forum.manjaro.org",
    "Manjaro Wiki": "https://wiki.manjaro.org",
    "Donate to Manjaro": "https://manjaro.org/donate"
}

# Nord Colors
NORD_COLORS = {
    "dark0": "#2E3440",
    "dark1": "#3B4252",
    "dark2": "#434C5E",
    "dark3": "#4C566A",
    "light0": "#D8DEE9",
    "light1": "#E5E9F0",
    "light2": "#ECEFF4",
    "frost0": "#8FBCBB",
    "frost1": "#88C0D0",
    "frost2": "#81A1C1",
    "frost3": "#5E81AC",
    "red": "#BF616A",
    "orange": "#D08770",
    "yellow": "#EBCB8B",
    "green": "#A3BE8C",
    "purple": "#B48EAD",
}

# ============================================================================
# GLOBAL FLAGS (set by argparse / entry points)
# ============================================================================
DRY_RUN = False
UI_MODE = None  # "gui" or "tui"
