"""Interaksi dengan YouTube via yt-dlp: pencarian, channel, dan pemilihan format."""

import os
import yt_dlp

from config import CYAN, YELLOW, GRAY, RESET, SEARCH_MAX_RESULTS, CHANNEL_MAX_RESULTS
from ui import banner, clear_screen, info, prompt, warn


def is_youtube_url(text):
    return text.startswith("http") and ("youtube.com" in text or "youtu.be" in text)


def video_url(entry):
    return entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"


def search_videos(query, max_results=SEARCH_MAX_RESULTS):
    opts = {"quiet": True, "extract_flat": True, "default_search": f"ytsearch{max_results}"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(query, download=False)
    return data.get("entries", [])


def list_channel_videos(keyword, max_results=CHANNEL_MAX_RESULTS):
    # Trik: cari video dari keyword lalu ambil channel_url pemilik video
    # teratas, karena yt-dlp tidak punya "cari channel" langsung.
    opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(f"ytsearch1:{keyword} channel", download=False)
        entries = data.get("entries", [])
        if not entries:
            return []
        channel_url = entries[0].get("channel_url") or entries[0].get("url")

    opts = {"quiet": True, "extract_flat": True, "playlistend": max_results}
    with yt_dlp.YoutubeDL(opts) as ydl:
        channel_data = ydl.extract_info(channel_url, download=False)

    videos = []
    for item in channel_data.get("entries", []):
        videos.extend(item["entries"] if "entries" in item else [item])
    return videos[:max_results]


def fetch_formats(url):
    opts = {"quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(url, download=False)
    return data.get("formats", []), data.get("title", "video")


def pick_format(url):
    info("Mengambil daftar format...")
    formats, _ = fetch_formats(url)

    # Satu opsi per resolusi unik (hindari duplikat itag beda bitrate).
    resolutions = {}
    for f in formats:
        if f.get("vcodec") == "none":
            continue
        res = f.get("format_note") or f.get("height")
        if res and res not in resolutions:
            resolutions[res] = f["format_id"]
    options = list(resolutions.items())

    clear_screen()
    banner("Pilih Kualitas")
    print(f"{YELLOW}  0.{RESET} Audio only (MP3, kualitas terbaik)")
    for i, (res, fid) in enumerate(options, 1):
        print(f"{YELLOW}{i:>3}.{RESET} {res}p  {GRAY}(format_id: {fid}){RESET}")

    choice = prompt("Pilih nomor format: ")
    if choice == "0":
        return "audio"
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1][1]
    warn("Pilihan tidak valid, pakai default (best).")
    return "best"


def resolve_playlist_or_video(url):
    """Ekstrak metadata dari link. Return dict yt-dlp (punya 'entries' jika playlist)."""
    opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
