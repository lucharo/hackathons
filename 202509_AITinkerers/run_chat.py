#!/usr/bin/env python3
"""Quick launcher for the DishGenius Chainlit chat UI."""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    print("🥗 Starting DishGenius Chainlit chat UI...")
    print("📡 Ensure the FastAPI backend is running on http://127.0.0.1:8000")

    cmd = [
        sys.executable,
        "-m",
        "chainlit",
        "run",
        "chainlit_app.py",
        "-w",
        "--port",
        "8001",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Chainlit chat stopped.")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Failed to start Chainlit: {exc}")
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
