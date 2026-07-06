# ytdl-termux

Downloader YouTube interaktif berbasis `yt-dlp`, dirancang untuk berjalan di Termux (Android).

## Fitur

- Cari video langsung dari keyword
- List video dari sebuah channel via keyword
- Paste link YouTube langsung (video atau playlist)
- Download seluruh isi playlist sekaligus
- Pilih kualitas video (144p–1080p60) atau ekstrak audio ke MP3
- Auto-install dependency (`yt-dlp`, `ffmpeg`) jika belum terpasang
- Auto-deteksi folder `Download` di internal storage
- Progress bar real-time berbasis byte terunduh
- Navigasi list hasil pencarian dengan pager (`n`/`p`/`q`)
- Riwayat download tersimpan di `history.log`
- Prompt lanjut/keluar setelah setiap download selesai

## Instalasi

```bash
pkg update -y && pkg upgrade -y
pkg install python ffmpeg -y
pip install yt-dlp
```

## Menjalankan

```bash
git clone https://github.com/hsbrgX/ytdl_termux
cd ytdl-termux
python main.py
```

Saat pertama kali dijalankan, script akan meminta izin akses storage
(`termux-setup-storage`) jika belum diberikan sebelumnya.

## Struktur Proyek

```
ytdl-termux/
├── main.py         # entry point & alur menu
├── config.py       # konstanta warna & default
├── ui.py           # komponen terminal (banner, progress bar, pager)
├── system.py       # auto-install dependency, deteksi folder Download
├── youtube.py      # pencarian, channel, resolusi format
└── downloader.py   # proses download & riwayat
```

## Output

File hasil download disimpan di:

```
/storage/emulated/0/Download/ytdl/
```

## Catatan

- Resolusi 1080p/720p60 membutuhkan `ffmpeg` untuk merge video+audio.
- Jika `ffmpeg` gagal setelah instalasi, jalankan `pkg upgrade -y` lalu ulangi.
