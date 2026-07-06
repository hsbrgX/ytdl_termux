"""Elemen antarmuka terminal: pesan status, banner, progress bar, dan pager."""

import os
import sys
import shutil

from config import RESET, BOLD, CYAN, GREEN, YELLOW, BLUE, MAGENTA, RED, GRAY, BAR_WIDTH


def clear_screen():
    os.system("clear")


def banner(text):
    width = min(shutil.get_terminal_size((60, 20)).columns, 60)
    line = "─" * width
    print(f"{CYAN}{line}{RESET}")
    print(f"{BOLD}{MAGENTA}{text.center(width)}{RESET}")
    print(f"{CYAN}{line}{RESET}")


def info(msg):
    print(f"{BLUE}::{RESET} {msg}")


def ok(msg):
    print(f"{GREEN}✓{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}!{RESET} {msg}")


def err(msg):
    print(f"{RED}✗{RESET} {msg}")


def prompt(label):
    return input(f"{CYAN}» {label}{RESET}").strip()


def render_progress_bar(percent, extra=""):
    filled = int(BAR_WIDTH * percent / 100)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    sys.stdout.write(f"\r{GREEN}{bar}{RESET} {percent:5.1f}%  {GRAY}{extra}{RESET}   ")
    sys.stdout.flush()


def paged_list(items, render_row, page_size=None):
    """
    Tampilkan `items` per halaman dengan navigasi ala pager (n/p/q).
    render_row(index, item) -> baris teks untuk ditampilkan.
    Return index terpilih (0-based), atau None jika dibatalkan.
    """
    if page_size is None:
        rows = shutil.get_terminal_size((80, 24)).lines
        page_size = max(5, rows - 6)

    total_pages = (len(items) + page_size - 1) // page_size
    page = 0

    while True:
        start, end = page * page_size, min(page * page_size + page_size, len(items))
        clear_screen()
        banner(f"Halaman {page + 1}/{total_pages}")
        for i in range(start, end):
            print(render_row(i, items[i]))
        print(f"\n{GRAY}[n] next  [p] prev  [q] batal  atau ketik nomor{RESET}")

        cmd = prompt("").lower()
        if cmd == "n":
            page = min(page + 1, total_pages - 1)
        elif cmd == "p":
            page = max(page - 1, 0)
        elif cmd == "q":
            return None
        elif cmd.isdigit() and 1 <= int(cmd) <= len(items):
            return int(cmd) - 1
        else:
            warn("Input tidak dikenali.")
            input("Tekan Enter untuk lanjut...")
