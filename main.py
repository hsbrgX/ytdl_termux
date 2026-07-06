#!/usr/bin/env python3
"""
ytdl-termux — Downloader YouTube interaktif untuk Termux.
Install: pkg install python ffmpeg -y && pip install yt-dlp
Jalankan: python main.py
"""

from system import ensure_dependencies, detect_download_dir

ensure_dependencies()  # harus sebelum import yt_dlp agar auto-install jalan

from config import YELLOW, RESET, GRAY
from ui import banner, clear_screen, prompt, err, info, ok, warn, paged_list
from youtube import (
    is_youtube_url,
    video_url,
    search_videos,
    list_channel_videos,
    pick_format,
    resolve_playlist_or_video,
)
from downloader import download

DOWNLOAD_DIR = detect_download_dir()


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


def download_single(entry):
    url = video_url(entry)
    fmt = pick_format(url)
    download(url, fmt, entry.get("title", "video"), DOWNLOAD_DIR)


def download_entire_playlist(entries):
    fmt = pick_format(video_url(entries[0]))
    for n, entry in enumerate(entries, 1):
        info(f"[{n}/{len(entries)}] {entry.get('title')}")
        download(video_url(entry), fmt, entry.get("title", "video"), DOWNLOAD_DIR)


def handle_direct_link(url):
    info("Membaca link...")
    data = resolve_playlist_or_video(url)

    if "entries" not in data:
        fmt = pick_format(url)
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


def show_main_menu():
    clear_screen()
    banner("YT-DLP Termux Downloader")
    print(f"{YELLOW}1.{RESET} Cari video")
    print(f"{YELLOW}2.{RESET} List video dari channel (keyword)")
    print(f"{YELLOW}3.{RESET} Paste link YouTube (video/playlist)")
    return prompt("Pilih mode: ")


def run_once():
    mode = show_main_menu()

    if mode == "3":
        url = prompt("Paste link YouTube: ")
        if not is_youtube_url(url):
            err("Link tidak valid.")
            return
        handle_direct_link(url)
        return

    if mode == "2":
        keyword = prompt("Keyword channel: ")
        info("Mencari channel...")
        entries = list_channel_videos(keyword)
    else:
        query = prompt("Cari video (judul/keyword): ")
        if is_youtube_url(query):
            handle_direct_link(query)
            return
        info("Mencari video...")
        entries = search_videos(query) if query else []

    if not entries:
        err("Tidak ada hasil.")
        return

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
