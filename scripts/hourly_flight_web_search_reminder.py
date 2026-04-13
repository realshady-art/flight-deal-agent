#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from send_chat_message_via_codex import send_message


SCRIPT_DIR = Path(__file__).resolve().parent
PROMPT_FILE = Path(os.environ.get("PROMPT_FILE_OVERRIDE", SCRIPT_DIR / "hourly_flight_web_search_prompt.txt"))
TARGET = os.environ.get("TARGET_OVERRIDE", "#特价机票")


def main() -> int:
    message_text = PROMPT_FILE.read_text(encoding="utf-8")
    send_message(target=TARGET, message_text=message_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
