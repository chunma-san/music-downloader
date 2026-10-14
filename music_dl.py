#!/usr/bin/env python3

import re
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(os.getenv("MUSIC_ROOT", "./data/music"))

SPOTIFY_DIR = BASE / "spotify"
YOUTUBE_DIR = BASE / "youtube"
YTMUSIC_DIR = BASE / "youtube-music"

YTDLP = Path(os.getenv("YTDLP_BIN", str(Path(__file__).resolve().parent / "venv/bin/yt-dlp")))
SPOTDL = Path(os.getenv("SPOTDL_BIN", str(Path(__file__).resolve().parent / "venv/bin/spotdl")))

for directory in (SPOTIFY_DIR, YOUTUBE_DIR, YTMUSIC_DIR):
    directory.mkdir(parents=True, exist_ok=True)


def detect_service(url):
    try:
        host = urlparse(url).hostname or ""
        host = host.lower()
    except Exception:
        return None

    if host in {"open.spotify.com", "www.open.spotify.com"}:
        return "spotify"

    if host == "music.youtube.com":
        return "youtube-music"

    if host in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
    }:
        return "youtube"

    return None


def run(cmd):
    print()
    print("=" * 60)
    print("Starting download")
    print("=" * 60)
    print()

    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nDownload cancelled.")
        return 130


def download_spotify(url):
    print("Service : Spotify")
    print("Folder  :", SPOTIFY_DIR)

    cmd = [
        str(SPOTDL),
        "download",
        url,

        # Try YouTube Music first, then regular YouTube.
        "--audio",
        "youtube-music",
        "youtube",

        # Spotify metadata is preserved by spotDL.
        # Albums/playlists can therefore be browsed correctly in Navidrome.
        "--output",
        str(
            SPOTIFY_DIR
            / "{album-artist} - {album}"
            / "{track-number} - {artists} - {title}.{output-ext}"
        ),
    ]

    return run(cmd)


def download_youtube(url, youtube_music=False):
    destination = (
        YTMUSIC_DIR if youtube_music else YOUTUBE_DIR
    )

    print(
        "Service :",
        "YouTube Music" if youtube_music else "YouTube",
    )
    print("Folder  :", destination)

    archive = (
        Path(os.getenv("DOWNLOAD_STATE_DIR", str(Path(__file__).resolve().parent / "state")))
        / (
            "youtube-music.archive"
            if youtube_music
            else "youtube.archive"
        )
    )

    cmd = [
        str(YTDLP),

        # Audio only
        "-x",
        "--audio-format",
        "opus",

        # Metadata / artwork
        "--embed-metadata",
        "--embed-thumbnail",

        # Resume partial downloads
        "--continue",

        # Don't download the same YouTube ID twice
        "--download-archive",
        str(archive),

        # Continue playlist if one item fails
        "--ignore-errors",

        # Playlist tracks get numbered automatically.
        "-o",
        str(
            destination
            / "%(playlist_title,album|Singles)s"
            / "%(playlist_index,track_number|0)02d - "
              "%(artist,uploader)s - %(title)s "
              "[%(id)s].%(ext)s"
        ),

        url,
    ]

    return run(cmd)


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print('  music_dl.py "URL"')
        sys.exit(2)

    url = sys.argv[1].strip()

    if not re.match(r"^https?://", url, re.I):
        print("ERROR: Please provide an http/https URL.")
        sys.exit(2)

    service = detect_service(url)

    if service == "spotify":
        code = download_spotify(url)

    elif service == "youtube-music":
        code = download_youtube(
            url,
            youtube_music=True,
        )

    elif service == "youtube":
        code = download_youtube(url)

    else:
        print("ERROR: Unsupported URL.")
        print(
            "Supported: Spotify, YouTube, "
            "YouTube Music"
        )
        sys.exit(2)

    print()

    if code == 0:
        print("Download finished.")
    else:
        print(f"Downloader exited with code {code}")

    sys.exit(code)


if __name__ == "__main__":
    main()
