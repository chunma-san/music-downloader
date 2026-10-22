<!-- CAT-COUNTER:START -->
<p align="center">
  <img src="https://count.himiku.com/@chunma-music-downloader-9a6830?theme=capoo-2&amp;padding=6&amp;scale=0.8&amp;darkmode=1" alt="Cute cat project visits counter" />
</p>


<!-- CAT-COUNTER:END -->

<!-- typing-title:start -->
<p align="center">
  <a href="https://github.com/DenverCoder1/readme-typing-svg">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&amp;weight=600&amp;size=28&amp;duration=3500&amp;pause=1800&amp;color=EF4444&amp;center=true&amp;vCenter=true&amp;width=760&amp;height=65&amp;repeat=true&amp;lines=Great+Love+Immortal+Venerable;Heaven+Refining+Demon+Venerable" alt="Great Love Immortal Venerable / Heaven Refining Demon Venerable" />
  </a>
</p>
<!-- typing-title:end -->

<!-- project-navigation:start -->
<p align="center"><a href="https://github.com/chunma-san">Profile &amp; projects</a> · <a href="#quick-start">Quick start</a> · <a href="https://github.com/chunma-san/music-downloader/issues">Issues</a></p>
<!-- project-navigation:end -->

# Music Downloader

A command-line music download helper with an optional owner-restricted Telegram bot.

**Runtime:** Python 3.11+ · **Configuration:** environment variables · **Deployment:** self-hosted

## Quick start

The supported deployment target is Linux. Create an isolated Python environment:

```sh
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env first. Use shell-compatible quoting for JSON and values with spaces.
set -a
. ./.env
set +a
python music_dl.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

Only source a configuration file you created and trust. Starting the application can connect to external services; configure credentials and destinations first.

## Usage

Run `python music_dl.py "https://www.youtube.com/watch?v=VIDEO_ID"` for the URL-based CLI, or `python telegram_bot.py` for Telegram control. Set TELEGRAM_ALLOWED_USER_ID before enabling the Telegram bot. Configure YTDLP_BIN and SPOTDL_BIN when the executables are not in `venv/bin/`.

## Configuration

`.env.example` contains placeholders only. Real credentials, IDs, storage locations and account settings belong in your private local configuration.

| Variable | Requirement |
| --- | --- |
| `DOWNLOAD_STATE_DIR` | Directory for downloader history files. |
| `MUSIC_ROOT` | Root directory for downloaded music. |
| `SPOTDL_BIN` | Path to the spotdl executable. |
| `TELEGRAM_ALLOWED_USER_ID` | Only this user can control the Telegram download bot. |
| `TELEGRAM_BOT_TOKEN` | BotFather bot token for the optional download bot. |
| `YTDLP_BIN` | Path to the yt-dlp executable. |

## How it works and operational notes

Requires FFmpeg and the download tools in requirements.txt. MUSIC_ROOT selects the output directory; DOWNLOAD_STATE_DIR selects duplicate-download records. Use sources you are authorized to download. Telegram credentials, cookies, downloaded media and download history stay local.

## Project layout

- Source files implement the application and integrations.
- `requirements.txt` or the project file declares dependencies.
- `.env.example` documents configuration names without live values.
- `.gitignore` excludes credentials, sessions, generated data and build output.

## Verification

See [VALIDATION.md](VALIDATION.md) for the checks performed on this publication snapshot and the remaining deployment checks. A source check is not an end-to-end test of Discord, Telegram, music sites or your host.

## Privacy and upstream services

This repository is a configurable source distribution. It does not include a production database, personal saved-link collection, message archive, credentials, media library or existing Git history. Review local changes before committing them.

Third-party APIs, libraries and products remain the work of their respective maintainers. Review their terms and licenses before redistribution or deployment.
