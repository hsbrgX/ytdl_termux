"""Konstanta global: warna terminal dan konfigurasi default."""

import os

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RED = "\033[31m"
GRAY = "\033[90m"

SEARCH_MAX_RESULTS = 25
CHANNEL_MAX_RESULTS = 30
BAR_WIDTH = 24

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")

# Ganti sesuai URL repo git kamu.
REPO_URL = "https://github.com/USERNAME/ytdl-termux.git"
REPO_BRANCH = "main"

DEFAULT_SETTINGS = {
    "download_dir": None,   # None = auto-detect
    "default_format": None, # None = tanya tiap kali
    "country": "ID",
}
