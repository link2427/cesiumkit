#!/usr/bin/env python3
"""Fetch the official Cesium release and vendor its Build/Cesium into the package.

The vendored build is gitignored; it is fetched at release time by the PyPI
publish workflow (and manually by developers who want fully offline serving,
see README). When it is absent, cesiumkit falls back to the CDN.

Usage:
    python scripts/fetch_cesium.py [--version 1.144] [--dest cesiumkit/vendor/cesium]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Version of the Cesium release to vendor. Keep in sync with
# cesiumkit/_html.py DEFAULT_CESIUM_VERSION.
DEFAULT_VERSION = "1.144"

# Files inside Build/Cesium that are not needed at runtime.
PRUNE = {
    "index.html",
    "index.cjs",
    "index.js",
    ".gitignore",
    "package.json",
    "README.md",
}


def _download(url: str, dest: Path) -> None:
    print(f"Downloading {url} ...", flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "cesiumkit-fetch/1.0"})
    with urllib.request.urlopen(request) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)
    print(f"Saved {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MiB)", flush=True)


def fetch(version: str, dest: Path) -> None:
    dest = dest.resolve()
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/CesiumGS/cesium/releases/download/{version}/Cesium-{version}.zip"
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "cesium.zip"
        _download(url, zip_path)
        with zipfile.ZipFile(zip_path) as archive:
            members = [m for m in archive.namelist() if m.startswith("Build/Cesium/")]
            if not members:
                sys.exit(f"error: Build/Cesium/ not found in {url}")
            for member in members:
                rel = member[len("Build/Cesium/") :]
                if not rel or rel.endswith("/"):
                    continue
                if Path(rel).name in PRUNE:
                    continue
                if ".." in Path(rel).parts or Path(rel).is_absolute():
                    sys.exit(f"error: unsafe member path in archive: {member}")
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, target.open("wb") as out:
                    shutil.copyfileobj(src, out)

    cesium_js = dest / "Cesium.js"
    if not cesium_js.is_file() or cesium_js.stat().st_size < 500_000:
        sys.exit("error: vendored Cesium.js missing or suspiciously small; aborting")
    if not (dest / "Assets" / "Textures" / "NaturalEarthII").is_dir():
        sys.exit("error: bundled NaturalEarthII assets not found; aborting")
    (dest / ".cesiumkit-version").write_text(f"{version}\n", encoding="utf-8")
    print(f"Vendored Cesium {version} into {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Cesium release to vendor")
    parser.add_argument("--dest", default="cesiumkit/vendor/cesium", help="destination directory")
    args = parser.parse_args()
    fetch(args.version, Path(args.dest))


if __name__ == "__main__":
    main()
