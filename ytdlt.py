#!/usr/bin/env python3
"""
ytdl_termux.py — Downloader YouTube interaktif untuk Termux (butuh yt-dlp).
Install dulu: pkg install python ffmpeg -y && pip install yt-dlp
Jalankan: python ytdl_termux.py
"""

import os
import sys
import shutil
import subprocess
import importlib

# ── Warna ANSI ──────────────────────────────────────────
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_MAGENTA = "\033[35m"
C_RED = "\033[31m"
C_GRAY = "\033[90m"


def banner(text):
    width = shutil.get_terminal_size((60, 20)).columns
    line = "─" * min(width, 60)
    print(f"{C_CYAN}{line}{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}{text.center(min(width, 60))}{C_RESET}")
    print(f"{C_CYAN}{line}{C_RESET}")


def info(msg):
    print(f"{C_BLUE}::{C_RESET} {msg}")


def ok(msg):
    print(f"{C_GREEN}✓{C_RESET} {msg}")


def warn(msg):
    print(f"{C_YELLOW}!{C_RESET} {msg}")


def err(msg):
    print(f"{C_RED}✗{C_RESET} {msg}")


# ── Progress bar ala pacman ─────────────────────────────
def pacman_bar(percent, extra=""):
    width = 24
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    line = f"\r{C_GREEN}{bar}{C_RESET} {percent:5.1f}%  {C_GRAY}{extra}{C_RESET}   "
    sys.stdout.write(line)
    sys.stdout.flush()


def spinner_step(label, step, total_steps=3):
    frames = ["-", "\\", "|", "/"]
    sys.stdout.write(f"\r{C_BLUE}::{C_RESET} {label} {frames[step % 4]}")
    sys.stdout.flush()


# ── Auto install dependencies ───────────────────────────
def ensure_dependencies():
    banner("Memeriksa Dependencies")
    pkgs = {"yt_dlp": "yt-dlp"}
    for module, pip_name in pkgs.items():
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


ensure_dependencies()
import yt_dlp


def detect_download_dir():
    candidates = [
        os.path.expanduser("~/storage/downloads"),
        "/storage/emulated/0/Download",
        "/sdcard/Download",
    ]
    for path in candidates:
        if os.path.isdir(path):
            target = os.path.join(path, "ytdl")
            os.makedirs(target, exist_ok=True)
            return target

    subprocess.run(["termux-setup-storage"])
    fallback = os.path.expanduser("~/storage/downloads/ytdl")
    os.makedirs(fallback, exist_ok=True)
    return fallback


DOWNLOAD_DIR = detect_download_dir()


# ── Pager ala less (PgUp/PgDn -> n/p) ───────────────────
def paged_list(items, render_fn, page_size=None):
    """
    items: list data
    render_fn: fungsi(index, item) -> string satu baris
    Navigasi: [n] halaman berikut, [p] halaman sebelumnya,
              [q] batal, atau ketik nomor untuk pilih.
    Return: index terpilih (0-based) atau None jika batal.
    """
    if page_size is None:
        rows = shutil.get_terminal_size((80, 24)).lines
        page_size = max(5, rows - 6)

    total = len(items)
    pages = (total + page_size - 1) // page_size
    page = 0

    while True:
        start = page * page_size
        end = min(start + page_size, total)
        os.system("clear")
        banner(f"Halaman {page + 1}/{pages}")
        for i in range(start, end):
            print(render_fn(i, items[i]))
        print(f"\n{C_GRAY}[n] next  [p] prev  [q] batal  atau ketik nomor{C_RESET}")
        cmd = input(f"{C_CYAN}» {C_RESET}").strip().lower()

        if cmd == "n":
            if page < pages - 1:
                page += 1
        elif cmd == "p":
            if page > 0:
                page -= 1
        elif cmd == "q":
            return None
        elif cmd.isdigit() and 1 <= int(cmd) <= total:
            return int(cmd) - 1
        else:
            warn("Input tidak dikenali.")
            input("Tekan Enter untuk lanjut...")


def search_videos(query, max_results=15):
    opts = {"quiet": True, "extract_flat": True, "default_search": f"ytsearch{max_results}"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info_data = ydl.extract_info(query, download=False)
    return info_data.get("entries", [])


def list_channel_videos(keyword, max_results=30):
    opts = {"quiet": True, "extract_flat": True}
    search_query = f"ytsearch1:{keyword} channel"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info_data = ydl.extract_info(search_query, download=False)
        entries = info_data.get("entries", [])
        if not entries:
            return []
        channel_url = entries[0].get("channel_url") or entries[0].get("url")

    opts2 = {"quiet": True, "extract_flat": True, "playlistend": max_results}
    with yt_dlp.YoutubeDL(opts2) as ydl:
        ch_info = ydl.extract_info(channel_url, download=False)

    if "entries" in ch_info:
        videos_tab = ch_info["entries"]
        flat = []
        for item in videos_tab:
            if "entries" in item:
                flat.extend(item["entries"])
            else:
                flat.append(item)
        return flat[:max_results]
    return []


def render_video_row(i, e):
    dur = e.get("duration")
    dur_str = f"{int(dur//60)}:{int(dur%60):02d}" if dur else "?"
    title = e.get("title", "Tanpa judul")
    return f"{C_YELLOW}{i+1:>3}.{C_RESET} {title}  {C_GRAY}[{dur_str}]{C_RESET}"


def pick_video(entries):
    idx = paged_list(entries, render_video_row)
    if idx is None:
        print("Dibatalkan.")
        sys.exit(0)
    return entries[idx]


def pick_format(url):
    info("Mengambil daftar format...")
    opts = {"quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info_data = ydl.extract_info(url, download=False)
    formats = info_data.get("formats", [])

    video_formats = [f for f in formats if f.get("vcodec") != "none"]
    seen_res = {}
    for f in video_formats:
        res = f.get("format_note") or f.get("height")
        if res and res not in seen_res:
            seen_res[res] = f["format_id"]

    options = list(seen_res.items())

    os.system("clear")
    banner("Pilih Kualitas")
    print(f"{C_YELLOW}  0.{C_RESET} Audio only (MP3, kualitas terbaik)")
    for i, (res, fid) in enumerate(options, 1):
        print(f"{C_YELLOW}{i:>3}.{C_RESET} {res}p  {C_GRAY}(format_id: {fid}){C_RESET}")

    choice = input(f"\n{C_CYAN}» Pilih nomor format: {C_RESET}").strip()
    if choice == "0":
        return "audio"
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1][1]
    warn("Pilihan tidak valid, pakai default (best).")
    return "best"


def download(url, format_choice, title):
    outtmpl = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    base_opts = {
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
        "retries": 3,
        "noprogress": False,
        "quiet": True,
        "no_warnings": True,
    }

    if format_choice == "audio":
        opts = {
            **base_opts,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    else:
        fmt_string = "bestvideo+bestaudio/best" if format_choice == "best" else f"{format_choice}+bestaudio/{format_choice}"
        opts = {
            **base_opts,
            "format": fmt_string,
            "merge_output_format": "mp4",
        }

    print()
    info(f"Mengunduh: {C_BOLD}{title}{C_RESET}")
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    print()
    ok(f"Selesai. File tersimpan di: {DOWNLOAD_DIR}")
    log_history(title, url)


def log_history(title, url):
    log_path = os.path.join(DOWNLOAD_DIR, "history.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{title} | {url}\n")


def is_youtube_url(text):
    return text.startswith("http") and ("youtube.com" in text or "youtu.be" in text)


def handle_direct_link(url):
    info("Membaca link...")
    opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info_data = ydl.extract_info(url, download=False)

    if "entries" in info_data:
        entries = list(info_data["entries"])
        banner("Playlist Terdeteksi")
        print(f"{info_data.get('title')}  {C_GRAY}({len(entries)} video){C_RESET}\n")
        print(f"{C_YELLOW}1.{C_RESET} Download semua")
        print(f"{C_YELLOW}2.{C_RESET} Pilih salah satu video")
        choice = input(f"\n{C_CYAN}» {C_RESET}").strip()
        if choice == "1":
            fmt = pick_format(entries[0].get("url") or entries[0].get("id"))
            total = len(entries)
            for n, e in enumerate(entries, 1):
                v_url = e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}"
                info(f"[{n}/{total}] {e.get('title')}")
                download(v_url, fmt, e.get("title", "video"))
            return
        else:
            video = pick_video(entries)
            v_url = video.get("url") or f"https://www.youtube.com/watch?v={video.get('id')}"
            fmt = pick_format(v_url)
            download(v_url, fmt, video.get("title", "video"))
            return

    fmt = pick_format(url)
    download(url, fmt, info_data.get("title", "video"))


def progress_hook(d):
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        if total:
            pct = downloaded / total * 100
        else:
            raw_pct = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                pct = float(raw_pct)
            except ValueError:
                pct = 0.0
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        pacman_bar(pct, f"{speed}  ETA {eta}")
    elif d["status"] == "finished":
        pacman_bar(100.0, "selesai")
        print()
        info("Memproses/merging file...")


def main_menu():
    os.system("clear")
    banner("YT-DLP Termux Downloader")
    print(f"{C_YELLOW}1.{C_RESET} Cari video")
    print(f"{C_YELLOW}2.{C_RESET} List video dari channel (keyword)")
    print(f"{C_YELLOW}3.{C_RESET} Paste link YouTube (video/playlist)")
    return input(f"\n{C_CYAN}» Pilih mode: {C_RESET}").strip()


def main():
    mode = main_menu()

    if mode == "3":
        url = input(f"{C_CYAN}» Paste link YouTube: {C_RESET}").strip()
        if not is_youtube_url(url):
            err("Link tidak valid.")
            return
        handle_direct_link(url)
        return

    if mode == "2":
        keyword = input(f"{C_CYAN}» Keyword channel: {C_RESET}").strip()
        info("Mencari channel...")
        entries = list_channel_videos(keyword)
    else:
        query = input(f"{C_CYAN}» Cari video (judul/keyword): {C_RESET}").strip()
        if is_youtube_url(query):
            handle_direct_link(query)
            return
        info("Mencari video...")
        entries = search_videos(query) if query else []

    if not entries:
        err("Tidak ada hasil.")
        return

    video = pick_video(entries)
    url = video.get("url") or f"https://www.youtube.com/watch?v={video.get('id')}"
    fmt = pick_format(url)
    download(url, fmt, video.get("title", "video"))


if __name__ == "__main__":
    try:
        while True:
            main()
            lanjut = input(f"\n{C_CYAN}» Download lagi? (y/n): {C_RESET}").strip().lower()
            if lanjut != "y":
                ok("Selesai.")
                break
    except KeyboardInterrupt:
        print()
        warn("Dibatalkan oleh user.")
