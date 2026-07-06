"""Proses unduh video/audio dan pencatatan riwayat download."""

import os
import yt_dlp

from ui import render_progress_bar, info, ok


def _build_format_string(format_choice):
    if format_choice == "best":
        return "bestvideo+bestaudio/best"
    # Kunci ke resolusi yang dipilih user; fallback ke resolusi yang sama
    # tanpa audio terpisah jika stream gabungan tidak tersedia (mencegah
    # yt-dlp diam-diam turun ke kualitas lain lewat "/best").
    return f"{format_choice}+bestaudio/{format_choice}"


def _build_options(download_dir, format_choice):
    base = {
        "outtmpl": os.path.join(download_dir, "%(title)s.%(ext)s"),
        "progress_hooks": [_progress_hook],
        "retries": 3,
        "quiet": True,
        "no_warnings": True,
    }

    if format_choice == "audio":
        return {
            **base,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

    return {
        **base,
        "format": _build_format_string(format_choice),
        "merge_output_format": "mp4",
    }


def download(url, format_choice, title, download_dir):
    print()
    info(f"Mengunduh: {title}")
    with yt_dlp.YoutubeDL(_build_options(download_dir, format_choice)) as ydl:
        ydl.download([url])
    print()
    ok(f"Selesai. File tersimpan di: {download_dir}")
    _log_history(title, url, download_dir)


def _log_history(title, url, download_dir):
    log_path = os.path.join(download_dir, "history.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{title} | {url}\n")


def _progress_hook(d):
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        percent = (downloaded / total * 100) if total else _parse_percent(d)
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        render_progress_bar(percent, f"{speed}  ETA {eta}")
    elif d["status"] == "finished":
        render_progress_bar(100.0, "selesai")
        print()
        info("Memproses/merging file...")


def _parse_percent(d):
    raw = d.get("_percent_str", "0%").strip().replace("%", "")
    try:
        return float(raw)
    except ValueError:
        return 0.0
