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


def resolve_download_dir(configured_path):
    """Pakai path dari settings jika valid, kalau tidak fallback ke auto-detect."""
    if configured_path and os.path.isdir(configured_path):
        return configured_path
    if configured_path:
        os.makedirs(configured_path, exist_ok=True)
        return configured_path
    return detect_download_dir()


def force_update(repo_url, branch, app_dir):
    """
    Paksa sinkron kode dengan git, tanpa bergantung file versi (json).
    Jika app_dir sudah repo git: fetch + hard reset ke origin/branch.
    Jika belum: clone ke folder sementara lalu timpa semua file kecuali
    settings.json dan history.log agar pengaturan user tidak hilang.
    """
    git_dir = os.path.join(app_dir, ".git")

    if os.path.isdir(git_dir):
        subprocess.run(["git", "-C", app_dir, "fetch", "--all"], check=True)
        subprocess.run(
            ["git", "-C", app_dir, "reset", "--hard", f"origin/{branch}"],
            check=True,
        )
        return

    tmp_dir = app_dir + "_update_tmp"
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
    subprocess.run(
        ["git", "clone", "--branch", branch, "--depth", "1", repo_url, tmp_dir],
        check=True,
    )

    keep = {"settings.json", "history.log"}
    for name in os.listdir(tmp_dir):
        if name == ".git":
            continue
        src = os.path.join(tmp_dir, name)
        dst = os.path.join(app_dir, name)
        if os.path.basename(dst) in keep and os.path.exists(dst):
            continue
        if os.path.isdir(src):
            shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    shutil.rmtree(tmp_dir)
