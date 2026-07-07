#!/usr/bin/env python3
"""
ytdl-termux — Downloader YouTube interaktif untuk Termux.
Install: pkg install python ffmpeg -y && pip install yt-dlp
Jalankan: python main.py
"""

import os

from system import ensure_dependencies, resolve_download_dir, force_update

ensure_dependencies()  # harus sebelum import yt_dlp agar auto-install jalan

from config import YELLOW, RESET, GRAY, APP_DIR, REPO_URL, REPO_BRANCH
from settings import load_settings, update_setting
from ui import banner, clear_screen, prompt, err, info, ok, warn, found, paged_list
from youtube import (
    is_youtube_url,
    video_url,
    timed,
    search_videos,
    list_channel_videos,
    pick_format,
    resolve_playlist_or_video,
    read_links_from_file,
)
from downloader import download

SETTINGS = load_settings()
DOWNLOAD_DIR = resolve_download_dir(SETTINGS["download_dir"])


def render_video_row(i, entry):
    duration = entry.get("duration")
    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "?"
    title = entry.get("title", "Tanpa judul")
    return f"{YELLOW}{i + 1:>3}.{RESET} {title}  {GRAY}[{duration_str}]{RESET}"


def pick_video(entries):
    idx = paged_list(entries, render_video_row)
    if idx is None:
        info("Dibatalkan.")
        raise SystemExit(0)
    return entries[idx]


def resolve_format(url):
    """Pakai kualitas default dari settings jika ada, kalau tidak tanya user."""
    return SETTINGS["default_format"] or pick_format(url)


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
        fmt = resolve_format(url)
        download(url, fmt, data.get("title", "video"), DOWNLOAD_DIR)
        return

    entries = list(data["entries"])
    banner("Playlist Terdeteksi")
    print(f"{data.get('title')}  {GRAY}({len(entries)} video){RESET}\n")
    print(f"{YELLOW}1.{RESET} Download semua")
    print(f"{YELLOW}2.{RESET} Pilih salah satu video")

    if prompt("") == "1":
        download_entire_playlist(entries)
    else:
        download_single(pick_video(entries))


def handle_batch_mode():
    print(f"{YELLOW}1.{RESET} Paste link manual")
    print(f"{YELLOW}2.{RESET} Ambil dari file .txt")
    sub = prompt("Pilih: ")

    if sub == "2":
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


def handle_settings_menu():
    global SETTINGS, DOWNLOAD_DIR
    while True:
        clear_screen()
        banner("Settings")
        print(f"{YELLOW}1.{RESET} Folder download: {GRAY}{DOWNLOAD_DIR}{RESET}")
        print(f"{YELLOW}2.{RESET} Kualitas default: {GRAY}{SETTINGS['default_format'] or 'tanya tiap kali'}{RESET}")
        print(f"{YELLOW}3.{RESET} Kode negara (search bias): {GRAY}{SETTINGS['country']}{RESET}")
        print(f"{YELLOW}4.{RESET} Kembali")
        choice = prompt("Pilih: ")

        if choice == "1":
            new_dir = prompt("Path folder download baru: ")
            if new_dir:
                SETTINGS = update_setting("download_dir", new_dir)
                DOWNLOAD_DIR = resolve_download_dir(new_dir)
                ok("Folder download diperbarui.")
        elif choice == "2":
            new_fmt = prompt("format_id / 'audio' / kosongkan untuk tanya tiap kali: ")
            SETTINGS = update_setting("default_format", new_fmt or None)
            ok("Kualitas default diperbarui.")
        elif choice == "3":
            code = prompt("Kode negara 2 huruf (mis. ID, US): ")
            SETTINGS = update_setting("country", code.upper() or "ID")
            ok("Kode negara diperbarui.")
        elif choice == "4":
            return
        else:
            warn("Pilihan tidak valid.")


def handle_update():
    info("Memaksa update dari git...")
    try:
        force_update(REPO_URL, REPO_BRANCH, APP_DIR)
        ok("Update selesai. Jalankan ulang script.")
        raise SystemExit(0)
    except Exception as e:
        err(f"Update gagal: {e}")


def show_main_menu():
    clear_screen()
    banner("YT-DLP Termux Downloader")
    print(f"{YELLOW}1.{RESET} Cari video")
    print(f"{YELLOW}2.{RESET} List video dari channel (keyword)")
    print(f"{YELLOW}3.{RESET} Paste link YouTube (video/playlist)")
    print(f"{YELLOW}4.{RESET} Batch download (banyak link/file txt)")
    print(f"{YELLOW}5.{RESET} Settings")
    print(f"{YELLOW}6.{RESET} Cek update (force git sync)")
    return prompt("Pilih mode: ")


def run_once():
    mode = show_main_menu()

    if mode == "6":
        handle_update()
        return
    if mode == "5":
        handle_settings_menu()
        return
    if mode == "4":
        handle_batch_mode()
        return

    if mode == "3":
        url = prompt("Paste link YouTube: ")
        if not is_youtube_url(url):
            err("Link tidak valid.")
            return
        handle_direct_link(url)
        return

    country = SETTINGS["country"]

    if mode == "2":
        keyword = prompt("Keyword channel: ")
        entries, elapsed = timed(list_channel_videos, keyword, country=country)
    else:
        query = prompt("Cari video (judul/keyword): ")
        if is_youtube_url(query):
            handle_direct_link(query)
            return
        entries, elapsed = timed(search_videos, query, country=country) if query else ([], 0)

    if not entries:
        err("Tidak ada hasil.")
        return

    found(len(entries), elapsed)
    download_single(pick_video(entries))


def main():
    try:
        while True:
            run_once()
            if prompt("Download lagi? (y/n): ").lower() != "y":
                ok("Selesai.")
                break
    except KeyboardInterrupt:
        print()
        warn("Dibatalkan oleh user.")


if __name__ == "__main__":
    main()
