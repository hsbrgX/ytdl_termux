"""Interaksi dengan YouTube via yt-dlp: pencarian, channel, dan pemilihan format."""

import os
import time
import yt_dlp

from config import SEARCH_MAX_RESULTS, CHANNEL_MAX_RESULTS
from ui import info, warn


def is_youtube_url(text):
    return text.startswith("http") and ("youtube.com" in text or "youtu.be" in text)


def video_url(entry):
    return entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}"


def timed(fn, *args, **kwargs):
    """Jalankan fn, kembalikan (hasil, durasi_detik)."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - start


def _base_search_opts(country=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "geo_bypass": True,
        "socket_timeout": 15,
    }
    if country:
        opts["geo_bypass_country"] = country.upper()
    return opts


def search_videos(query, max_results=SEARCH_MAX_RESULTS, country=None):
    # Prefix ytsearchN: eksplisit lebih reliable daripada opsi default_search
    # (default_search kadang tidak ter-trigger tergantung versi yt-dlp).
    opts = _base_search_opts(country)
    search_query = f"ytsearch{max(max_results * 2, 20)}:{query}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(search_query, download=False) or {}
    entries = [e for e in data.get("entries", []) if e]
    return entries[:max_results]


def list_channel_videos(keyword, max_results=CHANNEL_MAX_RESULTS, country=None):
    # Trik: cari video dari keyword lalu ambil channel_url pemilik video
    # teratas, karena yt-dlp tidak punya "cari channel" langsung.
    opts = _base_search_opts(country)
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(f"ytsearch1:{keyword} channel", download=False) or {}
        entries = [e for e in data.get("entries", []) if e]
        if not entries:
            return []
        channel_url = entries[0].get("channel_url") or entries[0].get("url")

    opts = _base_search_opts(country)
    opts["playlistend"] = max_results
    with yt_dlp.YoutubeDL(opts) as ydl:
        channel_data = ydl.extract_info(channel_url, download=False) or {}

    videos = []
    for item in channel_data.get("entries", []) or []:
        if not item:
            continue
        videos.extend(item["entries"] if "entries" in item else [item])
    return videos[:max_results]


def fetch_formats(url):
    opts = {"quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(url, download=False)
    return data.get("formats", []), data.get("title", "video")


def get_format_options(url):
    """Return list[(label, format_id)] resolusi unik untuk sebuah video."""
    formats, _ = fetch_formats(url)
    resolutions = {}
    for f in formats:
        if f.get("vcodec") == "none":
            continue
        res = f.get("format_note") or f.get("height")
        if res and res not in resolutions:
            resolutions[res] = f["format_id"]
    return list(resolutions.items())


def pick_format(url):
    from ui import arrow_select

    info("Mengambil daftar format...")
    options = get_format_options(url)

    labels = ["Audio only (MP3, kualitas terbaik)"] + [f"{res}p" for res, _ in options]
    idx = arrow_select(labels, header_lines=["Pilih Kualitas", ""])
    if idx is None:
        warn("Dibatalkan, pakai default (best).")
        return "best"
    if idx == 0:
        return "audio"
    return options[idx - 1][1]


def resolve_playlist_or_video(url):
    """Ekstrak metadata dari link. Return dict yt-dlp (punya 'entries' jika playlist)."""
    opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def read_links_from_file(path):
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    return [line for line in lines if is_youtube_url(line)]
