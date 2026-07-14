#!/usr/bin/env python3
"""Install the plugin's model-pinned agents into the user's Codex agent directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Replace existing same-name agents")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source_dir = root / "agents"
    target_dir = Path.home() / ".codex" / "agents"
    target_dir.mkdir(parents=True, exist_ok=True)

    for source in sorted(source_dir.glob("route-*.toml")):
        target = target_dir / source.name
        if target.exists() and not args.force:
            print(f"skip existing: {target}")
            continue
        shutil.copy2(source, target)
        print(f"installed: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
