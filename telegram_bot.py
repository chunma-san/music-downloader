#!/usr/bin/env python3

import asyncio
import os
import re
import signal
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BASE = Path(__file__).resolve().parent
DOWNLOADER = BASE / "music_dl.py"

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_ID = int(
    os.environ.get("TELEGRAM_ALLOWED_USER_ID", "0")
)

download_process = None
download_url = None
download_task = None
progress_current = None
progress_total = None
progress_track = None
lock = asyncio.Lock()


def allowed(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == ALLOWED_USER_ID)


async def reject(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text("Unauthorized.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update):
        await reject(update)
        return

    await update.message.reply_text(
        "Music Downloader ready.\n\n"
        "/dl <URL> - download track / album / playlist\n"
        "/status - current download status\n"
        "/cancel - cancel current download\n"
        "/help - show commands"
    )


async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await start(update, context)


async def run_download(chat_id: int, url: str, app: Application):
    global download_process, download_url, download_task
    global progress_current, progress_total, progress_track

    try:
        download_process = await asyncio.create_subprocess_exec(
            sys.executable, str(DOWNLOADER),
            url,
            cwd=str(BASE),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )

        tail = []

        assert download_process.stdout is not None

        while True:
            line = await download_process.stdout.readline()

            if not line:
                break

            text = line.decode(
                "utf-8",
                errors="replace",
            ).rstrip()

            if text:
                print(text, flush=True)
                tail.append(text)

                if len(tail) > 12:
                    tail.pop(0)

                match = re.search(
                    r"Downloading item (\d+) of (\d+)",
                    text,
                )
                if match:
                    progress_current = int(match.group(1))
                    progress_total = int(match.group(2))

                if "[ExtractAudio] Destination:" in text:
                    path = text.split(
                        "[ExtractAudio] Destination:",
                        1,
                    )[1].strip()

                    progress_track = Path(path).stem

        code = await download_process.wait()

        if code == 0:
            # Trigger an immediate incremental Navidrome scan.
            scan = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                "navidrome",
                "navidrome",
                "scan",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            try:
                scan_output, _ = await asyncio.wait_for(
                    scan.communicate(),
                    timeout=30,
                )

                if scan.returncode == 0:
                    await app.bot.send_message(
                        chat_id,
                        "Download finished successfully.\n"
                        "Navidrome scan completed.",
                    )
                else:
                    text = scan_output.decode(
                        "utf-8",
                        errors="replace",
                    )

                    print(
                        "Navidrome scan failed:\n" + text,
                        flush=True,
                    )

                    await app.bot.send_message(
                        chat_id,
                        "Download finished successfully, "
                        "but Navidrome scan failed.",
                    )

            except asyncio.TimeoutError:
                scan.kill()
                await scan.wait()

                print(
                    "Navidrome scan timed out after 30 seconds.",
                    flush=True,
                )

                await app.bot.send_message(
                    chat_id,
                    "Download finished successfully.\n"
                    "Navidrome scan timed out.",
                )
        elif code in (-signal.SIGTERM, -signal.SIGINT):
            await app.bot.send_message(
                chat_id,
                "Download cancelled.",
            )
        else:
            details = "\n".join(tail[-6:])

            if len(details) > 2500:
                details = details[-2500:]

            message = (
                f"Download failed (exit code {code})."
            )

            if details:
                message += f"\n\nLast output:\n{details}"

            await app.bot.send_message(
                chat_id,
                message,
            )

    except asyncio.CancelledError:
        raise

    except Exception as exc:
        await app.bot.send_message(
            chat_id,
            f"Downloader error: {type(exc).__name__}: {exc}",
        )

    finally:
        async with lock:
            download_process = None
            download_url = None
            download_task = None
            progress_current = None
            progress_total = None
            progress_track = None


async def dl(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    global download_task, download_url

    if not allowed(update):
        await reject(update)
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/dl https://..."
        )
        return

    url = context.args[0].strip()

    if not url.startswith(("https://", "http://")):
        await update.message.reply_text(
            "Invalid URL. Send an http/https link."
        )
        return

    async with lock:
        if download_task is not None:
            await update.message.reply_text(
                "A download is already running.\n"
                "Use /status or /cancel."
            )
            return

        download_url = url

        download_task = asyncio.create_task(
            run_download(
                update.effective_chat.id,
                url,
                context.application,
            )
        )

    await update.message.reply_text(
        "Download started.\n"
        "Use /status to check it."
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not allowed(update):
        await reject(update)
        return

    async with lock:
        running = (
            download_task is not None
            and not download_task.done()
        )
        url = download_url
        current = progress_current
        total = progress_total
        track = progress_track

    if not running:
        await update.message.reply_text(
            "No download is running."
        )
        return

    lines = ["Download is running."]

    if current is not None and total is not None:
        lines.append(f"Progress: {current} / {total}")

    if track:
        lines.append(f"Current: {track}")

    lines.append(f"URL: {url}")

    await update.message.reply_text(
        "\n".join(lines)
    )


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    global download_process

    if not allowed(update):
        await reject(update)
        return

    async with lock:
        process = download_process

    if process is None or process.returncode is not None:
        await update.message.reply_text(
            "No download is running."
        )
        return

    try:
        os.killpg(
            os.getpgid(process.pid),
            signal.SIGTERM,
        )
    except ProcessLookupError:
        pass

    await update.message.reply_text(
        "Cancellation requested."
    )


def main():
    if not TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is missing"
        )

    if not ALLOWED_USER_ID:
        raise SystemExit(
            "TELEGRAM_ALLOWED_USER_ID is missing"
        )

    if not DOWNLOADER.exists():
        raise SystemExit(
            f"Downloader not found: {DOWNLOADER}"
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("dl", dl))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancel", cancel))

    print(
        f"Bot started. Allowed user: {ALLOWED_USER_ID}",
        flush=True,
    )

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
