#!/usr/bin/env python3
"""Opt-in, pinned mcbuild launcher for the KNEEKURA Minecraft building genre.

Only Python standard-library dependencies are used by this launcher. It never
installs packages, calls an LLM, or edits a Minecraft world merely by import.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MINECRAFT_DIR = HERE.parents[1]
LOCAL = MINECRAFT_DIR / "local-artifacts" / "mcbuild"
UPSTREAM = LOCAL / "upstream"
RUNS = LOCAL / "runs"
MANIFEST = HERE / "manifest.json"


def metadata() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = data["upstream"]
    if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
        raise RuntimeError("Upstream commit must be a full 40-character SHA")
    if source["clone_url"] != "https://github.com/harrynull/mcbuild.git":
        raise RuntimeError("Unexpected upstream clone URL; review manifest change first")
    return data


def _output(cmd: list[str]) -> str:
    p = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd[0]}), exit={p.returncode}: {p.stderr.strip()}")
    return p.stdout.strip()


def verify_checkout() -> None:
    expected = metadata()["upstream"]
    if not (UPSTREAM / ".git").exists():
        raise RuntimeError("mcbuild is not prepared; run 'prepare' first")
    actual_url = _output(["git", "-C", str(UPSTREAM), "remote", "get-url", "origin"])
    actual_sha = _output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"])
    dirty = _output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"])
    if actual_url != expected["clone_url"] or actual_sha != expected["commit"] or dirty:
        raise RuntimeError("mcbuild source does not match pinned, clean upstream; refusing to execute")


def run_command(action: str, prompt: str, max_iters: int, model: str, cost_ceiling: float) -> list[str]:
    """Pure command construction; never invokes a subprocess."""
    if not 1 <= max_iters <= 20:
        raise ValueError("--max-iters must be between 1 and 20")
    cmd = [
        "uv", "run", "--offline", "--frozen", "--no-sync", "mcbuild", prompt,
        "--max-iters", str(max_iters), "--out", str(RUNS), "--display", "off",
    ]
    if action == "demo":
        cmd.extend(["--fake-llm"])
    elif action == "build":
        if not (cost_ceiling > 0 and cost_ceiling <= 100):
            raise ValueError("--cost-ceiling must be > 0 and <= 100 USD")
        if not model.strip():
            raise ValueError("Model id cannot be blank")
        cmd.extend(["--model", model, "--cost-ceiling", str(cost_ceiling)])
    else:
        raise ValueError("Unsupported action")
    return cmd


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Optional pinned mcbuild integration (no automatic world edits)")
    sub = p.add_subparsers(dest="action", required=True)
    sub.add_parser("status", help="Read-only local installation status")
    sub.add_parser("prepare", help="Explicitly git-clone the pinned upstream source into ignored local-artifacts")
    sub.add_parser("install", help="Explicitly install the pinned upstream uv.lock dependencies (network)")
    demo = sub.add_parser("demo", help="Run upstream FakeLLM pipeline without API/network access")
    demo.add_argument("--prompt", default="a tiny stone hut")
    demo.add_argument("--max-iters", type=int, default=3)
    build = sub.add_parser("build", help="Explicitly call the online model and output .schem")
    build.add_argument("--prompt", required=True)
    build.add_argument("--model", default="anthropic/claude-sonnet-5")
    build.add_argument("--max-iters", type=int, default=6)
    build.add_argument("--cost-ceiling", type=float, default=2.0, help="Upstream best-effort API budget in USD")
    build.add_argument("--online", action="store_true", help="Required acknowledgement of OpenRouter API usage")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        source = metadata()["upstream"]
        if args.action == "status":
            verified = False
            reason = "not prepared"
            if UPSTREAM.exists():
                try:
                    verify_checkout()
                    verified, reason = True, "pinned clean checkout"
                except (RuntimeError, OSError) as exc:
                    reason = str(exc)
            print(json.dumps({
                "genre": "建築",
                "upstream_commit": source["commit"],
                "source_directory": str(UPSTREAM),
                "installed": UPSTREAM.exists(),
                "source_verified": verified,
                "source_status": reason,
                "git_available": shutil.which("git") is not None,
                "uv_available": shutil.which("uv") is not None,
                "run_directory": str(RUNS),
                "live_world_edit": False,
            }, ensure_ascii=False, indent=2))
            return 0
        if args.action == "prepare":
            if UPSTREAM.exists():
                verify_checkout()
                print("Pinned mcbuild checkout is already prepared.")
                return 0
            if not shutil.which("git"):
                raise RuntimeError("git is required for prepare")
            LOCAL.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--no-checkout", source["clone_url"], str(UPSTREAM)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(UPSTREAM), "checkout", "--detach", source["commit"]],
                check=True,
            )
            verify_checkout()
            print("Prepared pinned mcbuild source at", UPSTREAM)
            return 0
        if args.action == "build":
            if not args.online:
                raise RuntimeError("Online model invocation requires --online")
            if not os.environ.get("OPENROUTER_API_KEY"):
                raise RuntimeError("Set OPENROUTER_API_KEY in your environment (never in Git)")
        verify_checkout()
        if not shutil.which("uv"):
            raise RuntimeError("Install uv first: https://docs.astral.sh/uv/")
        if args.action == "install":
            print("Installing pinned upstream dependencies in the local checkout...")
            return subprocess.call(["uv", "sync", "--frozen"], cwd=UPSTREAM)
        # demo and build are explicitly invoked; no auto package installation.
        cmd = run_command(
            args.action, args.prompt, args.max_iters,
            getattr(args, "model", ""), getattr(args, "cost_ceiling", 0.0),
        )
        RUNS.mkdir(parents=True, exist_ok=True)
        print("Output directory:", RUNS)
        return subprocess.call(cmd, cwd=UPSTREAM)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"mcbuild bridge: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
