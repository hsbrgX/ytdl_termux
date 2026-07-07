"""Baca metadata repo (owner, nama, versi) dari version.json lokal."""

import json
import os

from config import APP_DIR

VERSION_PATH = os.path.join(APP_DIR, "version.json")

DEFAULT_VERSION = {"owner": "hsbrgX", "repo": "https://github.com/hsbrgX/ytdl_termux", "version": "1.0", "branch": "main"}


def load_version():
    if not os.path.isfile(VERSION_PATH):
        return dict(DEFAULT_VERSION)
    try:
        with open(VERSION_PATH, "r", encoding="utf-8") as f:
            return {**DEFAULT_VERSION, **json.load(f)}
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_VERSION)
