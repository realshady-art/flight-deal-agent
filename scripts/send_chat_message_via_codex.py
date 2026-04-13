#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
WORKDIR = SCRIPT_DIR.parent
ENV_FILE = SCRIPT_DIR / ".chat_bridge.env"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key, value)


def load_bridge_from_proc() -> dict[str, str]:
    pattern = re.compile(
        r'mcp_servers\.chat\.args=\["([^"]+)","--agent-id","([^"]+)","--server-url","([^"]+)","--auth-token","([^"]+)"\]'
    )
    proc_dir = Path("/proc")
    if proc_dir.is_dir():
        for pid in os.listdir(proc_dir):
            if not pid.isdigit():
                continue
            try:
                raw = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
            except OSError:
                continue
            args = [a.decode("utf-8", "ignore") for a in raw if a]
            joined = " ".join(args)
            if "chat-bridge.js" not in joined or "mcp_servers.chat.enabled=true" not in joined:
                continue
            for arg in args:
                if "mcp_servers.chat.args=" not in arg:
                    continue
                match = pattern.search(arg)
                if match:
                    bridge_path, agent_id, server_url, auth_token = match.groups()
                    return {
                        "CHAT_BRIDGE_PATH": bridge_path,
                        "CHAT_AGENT_ID": agent_id,
                        "CHAT_SERVER_URL": server_url,
                        "CHAT_AUTH_TOKEN": auth_token,
                    }
    else:
        result = subprocess.run(
            ["ps", "-axo", "command="],
            check=True,
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            if "chat-bridge.js" not in line or "mcp_servers.chat.enabled=true" not in line:
                continue
            match = pattern.search(line)
            if match:
                bridge_path, agent_id, server_url, auth_token = match.groups()
                return {
                    "CHAT_BRIDGE_PATH": bridge_path,
                    "CHAT_AGENT_ID": agent_id,
                    "CHAT_SERVER_URL": server_url,
                    "CHAT_AUTH_TOKEN": auth_token,
                }
    raise RuntimeError("Could not find a running Codex process with chat bridge configuration")


def load_bridge_from_ps() -> dict[str, str]:
    pattern = re.compile(
        r'mcp_servers\.chat\.args=\["([^"]+)","--agent-id","([^"]+)","--server-url","([^"]+)","--auth-token","([^"]+)"\]'
    )
    output = subprocess.check_output(["ps", "-axww", "-o", "pid=,command="], text=True)
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "chat-bridge.js" not in line or "mcp_servers.chat.enabled=true" not in line:
            continue
        match = pattern.search(line)
        if match:
            bridge_path, agent_id, server_url, auth_token = match.groups()
            return {
                "CHAT_BRIDGE_PATH": bridge_path,
                "CHAT_AGENT_ID": agent_id,
                "CHAT_SERVER_URL": server_url,
                "CHAT_AUTH_TOKEN": auth_token,
            }
    raise RuntimeError("Could not find a running Codex process with chat bridge configuration")


def ensure_bridge_env() -> dict[str, str]:
    load_env_file(ENV_FILE)
    keys = ["CHAT_BRIDGE_PATH", "CHAT_AGENT_ID", "CHAT_SERVER_URL", "CHAT_AUTH_TOKEN"]
    values = {key: os.environ.get(key, "") for key in keys}
    if all(values.values()):
        return values

    if os.path.isdir("/proc"):
        try:
            discovered = load_bridge_from_proc()
        except RuntimeError:
            discovered = load_bridge_from_ps()
    else:
        discovered = load_bridge_from_ps()

    for key, value in discovered.items():
        os.environ.setdefault(key, value)
    return {key: os.environ[key] for key in keys}


def build_prompt(target: str, message_text: str) -> str:
    return (
        "Use send_message exactly once.\n"
        f"The only valid target is: {target}\n"
        "Do not send to any other target.\n"
        "Send this exact message content:\n\n"
        f"{message_text}"
    )


def resolve_codex_bin() -> str:
    codex_bin = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not codex_bin:
        raise RuntimeError("Could not find `codex` in PATH. Set CODEX_BIN explicitly.")
    return codex_bin


def send_message(target: str, message_text: str, workdir: Path = WORKDIR) -> None:
    bridge = ensure_bridge_env()
    codex_bin = resolve_codex_bin()

    cmd = [
        codex_bin,
        "exec",
        "-C",
        str(workdir),
        "-m",
        os.environ.get("CODEX_MODEL", "gpt-5.4"),
        "-s",
        "workspace-write",
        "--dangerously-bypass-approvals-and-sandbox",
        "-c",
        'model_reasoning_effort="medium"',
        "-c",
        'mcp_servers.chat.command="node"',
        "-c",
        (
            'mcp_servers.chat.args='
            f'["{bridge["CHAT_BRIDGE_PATH"]}","--agent-id","{bridge["CHAT_AGENT_ID"]}",'
            f'"--server-url","{bridge["CHAT_SERVER_URL"]}","--auth-token","{bridge["CHAT_AUTH_TOKEN"]}"]'
        ),
        "-c",
        "mcp_servers.chat.startup_timeout_sec=30",
        "-c",
        "mcp_servers.chat.tool_timeout_sec=300",
        "-c",
        "mcp_servers.chat.enabled=true",
        "-c",
        "mcp_servers.chat.required=true",
        build_prompt(target, message_text),
    ]
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a chat message through Codex + chat bridge.")
    parser.add_argument("--target", required=True, help="Chat target, e.g. #channel or dm:@name")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--message", help="Exact message content")
    group.add_argument("--message-file", type=Path, help="Path to a text file with exact message content")
    parser.add_argument("--workdir", type=Path, default=WORKDIR, help="Codex working directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    message_text = args.message or args.message_file.read_text(encoding="utf-8")
    send_message(target=args.target, message_text=message_text, workdir=args.workdir)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"send_chat_message_via_codex.py failed: {exc}", file=sys.stderr)
        raise
