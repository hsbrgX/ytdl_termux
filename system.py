"""Persiapan lingkungan: instalasi dependency dan deteksi folder penyimpanan."""

import os
import sys
import shutil
import subprocess
import importlib

from ui import banner, info, ok, warn

REQUIRED_PIP_PACKAGES = {"yt_dlp": "yt-dlp"}

# Kandidat lokasi folder Download di Android/Termux, diurutkan dari yang
# paling umum tersedia tanpa setup tambahan ke yang butuh izin storage.
DOWNLOAD_DIR_CANDIDATES = [
    os.path.expanduser("~/storage/downloads"),
    "/storage/emulated/0/Download",
    "/sdcard/Download",
]


def ensure_dependencies():
    banner("Memeriksa Dependencies")

    for module, pip_name in REQUIRED_PIP_PACKAGES.items():
        try:
            importlib.import_module(module)
            ok(f"{pip_name} sudah terinstall")
        except ImportError:
            warn(f"{pip_name} belum ada, menginstall...")
            subprocess.run([sys.executable, "-m", "pip", "install", pip_name], check=True)
            ok(f"{pip_name} berhasil diinstall")

    if shutil.which("ffmpeg") is None:
        warn("ffmpeg belum ada, menginstall...")
        subprocess.run(["pkg", "install", "-y", "ffmpeg"], check=True)
        ok("ffmpeg berhasil diinstall")
    else:
        ok("ffmpeg sudah terinstall")
    print()


def detect_download_dir():
    for path in DOWNLOAD_DIR_CANDIDATES:
        if os.path.isdir(path):
            target = os.path.join(path, "ytdl")
            os.makedirs(target, exist_ok=True)
            return target

    # Belum ada akses storage — minta izin lalu pakai folder internal Termux.
    subprocess.run(["termux-setup-storage"])
    fallback = os.path.expanduser("~/storage/downloads/ytdl")
    os.makedirs(fallback, exist_ok=True)
    return fallback
