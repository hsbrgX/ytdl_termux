#!/usr/bin/env python3
"""
ytdl-termux — Downloader YouTube interaktif untuk Termux.
Install: pkg install python ffmpeg -y && pip install yt-dlp
Jalankan: python main.py
"""

from system import ensure_dependencies, resolve_download_dir, check_and_update

ensure_dependencies()  # harus sebelum import yt_dlp agar auto-install jalan

from config import YELLOW, RESET, GRAY, APP_DIR, REPO_URL, REPO_BRANCH
from settings import load_settings, update_setting
from version import load_version
from ui import ASCII_LOGO, clear_screen, prompt, arrow_select, err, info, ok, warn, found
from youtube import (
    is_youtube_url,
    video_url,
    timed,
    search_videos,
    list_channel_videos,
    get_format_options,
    pick_format,
    resolve_playlist_or_video,
    read_links_from_file,
)
from downloader import download

SETTINGS = load_settings()
VERSION_INFO = load_version()
DOWNLOAD_DIR = resolve_download_dir(SETTINGS["download_dir"])

MAIN_MENU_OPTIONS = [
    "Cari video",
    "List video dari channel (keyword)",
    "Paste link YouTube (video/playlist)",
    "Batch download (banyak link/file txt)",
    "Settings",
    "Cek update (git)",
    "Keluar",
]


def render_video_row(i, entry):
    duration = entry.get("duration")
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"
    title = entry.get("title", "Tanpa judul")
    return f"{title}  [{duration_str}]"


def pick_video(entries):
    idx = arrow_select(
        [render_video_row(i, e) for i, e in enumerate(entries)],
        header_lines=["Pilih Video", ""],
    )
    if idx is None:
        info("Dibatalkan.")
        raise SystemExit(0)
    return entries[idx]


def resolve_format(url):
    """Pakai kualitas default dari settings jika cocok tersedia, kalau tidak tanya user."""
    preferred = SETTINGS["default_format"]
    if not preferred:
        return pick_format(url)

    if preferred == "audio":
        return "audio"

    for res, fid in get_format_options(url):
        if f"{res}p" == preferred:
            return fid

    warn(f"Kualitas default '{preferred}' tidak tersedia untuk video ini.")
    return pick_format(url)


def download_single(entry):
    url = video_url(entry)
    fmt = resolve_format(url)
    download(url, fmt, entry.get("title", "video"), DOWNLOAD_DIR)


def download_entire_playlist(entries):
    fmt = resolve_format(video_url(entries[0]))
    for n, entry in enumerate(entries, 1):
        info(f"[{n}/{len(entries)}] {entry.get('title')}")
        download(video_url(entry), fmt, entry.get("title", "video"), DOWNLOAD_DIR)


def download_batch_links(urls):
    fmt = resolve_format(urls[0])
    for n, url in enumerate(urls, 1):
        data = resolve_playlist_or_video(url) or {}
        info(f"[{n}/{len(urls)}] {data.get('title', url)}")
        download(url, fmt, data.get("title", "video"), DOWNLOAD_DIR)


def handle_direct_link(url):
    info("Membaca link...")
    data = resolve_playlist_or_video(url)

    if "entries" not in data:
        download_single({"url": url, "title": data.get("title", "video")})
        return

    entries = list(data["entries"])
    choice = arrow_select(
        ["Download semua", "Pilih salah satu video"],
        header_lines=[f"Playlist: {data.get('title')} ({len(entries)} video)", ""],
    )
    if choice is None:
        return
    if choice == 0:
        download_entire_playlist(entries)
    else:
        download_single(pick_video(entries))


def handle_batch_mode():
    choice = arrow_select(
        ["Paste link manual", "Ambil dari file .txt"],
        header_lines=["Batch Download", ""],
    )
    if choice is None:
        return

    if choice == 1:
        path = prompt("Path file txt: ")
        urls = read_links_from_file(path)
    else:
        raw = prompt("Paste link (pisah spasi/baris baru): ")
        urls = [u for u in raw.replace(",", " ").split() if is_youtube_url(u)]

    if not urls:
        err("Tidak ada link valid.")
        return
    ok(f"{len(urls)} link terdeteksi.")
    download_batch_links(urls)


QUALITY_LABELS = ["tanya tiap kali", "audio", "144p", "240p", "360p", "480p", "720p60", "1080p60", "best"]


def handle_settings_menu():
    global SETTINGS, DOWNLOAD_DIR
    while True:
        options = [
            f"Folder download: {DOWNLOAD_DIR}",
            f"Kualitas default: {SETTINGS['default_format'] or 'tanya tiap kali'}",
            f"Kode negara (search bias): {SETTINGS['country']}",
            "Kembali",
        ]
        choice = arrow_select(options, header_lines=["Settings", ""])

        if choice is None or choice == 3:
            return

        if choice == 0:
            new_dir = prompt("Path folder download baru: ")
            if new_dir:
                SETTINGS = update_setting("download_dir", new_dir)
                DOWNLOAD_DIR = resolve_download_dir(new_dir)
                ok("Folder download diperbarui.")
        elif choice == 1:
            q_idx = arrow_select(QUALITY_LABELS, header_lines=["Kualitas Default", ""])
            if q_idx is not None:
                value = None if q_idx == 0 else QUALITY_LABELS[q_idx]
                SETTINGS = update_setting("default_format", value)
                ok("Kualitas default diperbarui.")
        elif choice == 2:
            code = prompt("Kode negara 2 huruf (mis. ID, US): ")
            SETTINGS = update_setting("country", code.upper() or "ID")
            ok("Kode negara diperbarui.")


def handle_update():
    info("Memeriksa version.json...")
    try:
        updated, message = check_and_update(REPO_URL, REPO_BRANCH, APP_DIR, VERSION_INFO)
        ok(message)
        if updated:
            info("Jalankan ulang script untuk memakai versi baru.")
            raise SystemExit(0)
    except SystemExit:
        raise
    except Exception as e:
        err(f"Update gagal: {e}")


def print_main_header():
    clear_screen()
    print(f"{YELLOW}{ASCII_LOGO}{RESET}")
    print(f"{GRAY}{VERSION_INFO['owner']}/{VERSION_INFO['repo']}  v{VERSION_INFO['version']}{RESET}")
    print(f"{GRAY}Download dir: {DOWNLOAD_DIR}{RESET}\n")


def run_once():
    """Return True jika ada aksi download (agar prompt 'download lagi' muncul)."""
    print_main_header()
    mode = arrow_select(MAIN_MENU_OPTIONS, header_lines=[])
    if mode is None or mode == 6:
        raise SystemExit(0)

    if mode == 5:
        handle_update()
        return False
    if mode == 4:
        handle_settings_menu()
        return False
    if mode == 3:
        handle_batch_mode()
        return True

    if mode == 2:
        url = prompt("Paste link YouTube: ")
        if not is_youtube_url(url):
            err("Link tidak valid.")
            return False
        handle_direct_link(url)
        return True

    country = SETTINGS["country"]

    if mode == 1:
        keyword = prompt("Keyword channel: ")
        entries, elapsed = timed(list_channel_videos, keyword, country=country)
    else:
        query = prompt("Cari video (judul/keyword): ")
        if is_youtube_url(query):
            handle_direct_link(query)
            return True
        entries, elapsed = timed(search_videos, query, country=country) if query else ([], 0)

    if not entries:
        err("Tidak ada hasil.")
        return False

    found(len(entries), elapsed)
    download_single(pick_video(entries))
    return True


def main():
    try:
        while True:
            did_download = run_once()
            if did_download and prompt("Download lagi? (y/n): ").lower() != "y":
                ok("Selesai.")
                break
    except KeyboardInterrupt:
        print()
        warn("Dibatalkan oleh user.")


if __name__ == "__main__":
    main()
