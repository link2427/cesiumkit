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
import hashlib
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Version of the Cesium release to vendor. Keep in sync with
# cesiumkit/_html.py DEFAULT_CESIUM_VERSION.
DEFAULT_VERSION = "1.144"
# SHA-256 published for Cesium-1.144.zip in the official GitHub release.
# Keep this paired with DEFAULT_VERSION when upgrading Cesium.
DEFAULT_SHA256 = "7c8e22976e8fd57e01b1b49dd056d56d81d30d2c2b2ea609d01bd6b94a70a614"

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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_checksum(version: str, checksum: str | None, verify: bool) -> str | None:
    """Return the required digest, or ``None`` for an explicit opt-out."""
    if not verify:
        return None
    if checksum is not None:
        normalized = checksum.lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("--sha256 must be a 64-character hexadecimal SHA-256 digest")
        return normalized
    if version == DEFAULT_VERSION:
        return DEFAULT_SHA256
    raise ValueError(
        f"Cesium {version} has no pinned checksum; pass --sha256 <digest> "
        "or explicitly acknowledge the risk with --no-verify"
    )


def _extract_build(archive: zipfile.ZipFile, dest: Path, url: str) -> None:
    members = [member for member in archive.namelist() if member.startswith("Build/Cesium/")]
    if not members:
        raise RuntimeError(f"Build/Cesium/ not found in {url}")
    for member in members:
        rel = member[len("Build/Cesium/") :]
        if not rel or rel.endswith("/"):
            continue
        if Path(rel).name in PRUNE:
            continue
        if ".." in Path(rel).parts or Path(rel).is_absolute():
            raise RuntimeError(f"unsafe member path in archive: {member}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)

    # Cesium is Apache-2.0; redistributing Build/Cesium in the wheel requires
    # the license alongside it. NOTICE.md is only present in some releases.
    if "LICENSE.md" not in archive.namelist():
        raise RuntimeError("LICENSE.md not found in archive")
    for license_file in ("LICENSE.md", "NOTICE.md"):
        if license_file not in archive.namelist():
            print(f"note: {license_file} not present in archive; skipping")
            continue
        with archive.open(license_file) as source, (dest / license_file).open("wb") as output:
            shutil.copyfileobj(source, output)


def _validate_build(dest: Path) -> None:
    cesium_js = dest / "Cesium.js"
    if not cesium_js.is_file() or cesium_js.stat().st_size < 500_000:
        raise RuntimeError("vendored Cesium.js missing or suspiciously small; aborting")
    if not (dest / "Assets" / "Textures" / "NaturalEarthII").is_dir():
        raise RuntimeError("bundled NaturalEarthII assets not found; aborting")


def _replace_directory(staged: Path, dest: Path) -> None:
    """Atomically replace ``dest`` after a fully verified extraction."""
    backup = dest.with_name(f".{dest.name}.previous")
    if backup.exists():
        shutil.rmtree(backup)
    if dest.exists():
        dest.replace(backup)
    try:
        staged.replace(dest)
    except Exception:
        if backup.exists() and not dest.exists():
            backup.replace(dest)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def fetch(version: str, dest: Path, checksum: str | None) -> None:
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/CesiumGS/cesium/releases/download/{version}/Cesium-{version}.zip"
    with tempfile.TemporaryDirectory(dir=dest.parent, prefix=".cesiumkit-fetch-") as tmp:
        zip_path = Path(tmp) / "cesium.zip"
        _download(url, zip_path)
        if checksum is None:
            print("warning: checksum verification deliberately disabled", file=sys.stderr)
        else:
            actual = _file_sha256(zip_path)
            if actual != checksum:
                raise RuntimeError(
                    f"SHA-256 mismatch for {url}: expected {checksum}, got {actual}; refusing to extract"
                )
            print(f"Verified SHA-256: {actual}")

        staged = Path(tmp) / "cesium"
        with zipfile.ZipFile(zip_path) as archive:
            _extract_build(archive, staged, url)
        _validate_build(staged)
        (staged / ".cesiumkit-version").write_text(f"{version}\n", encoding="utf-8")
        _replace_directory(staged, dest)

    total_mb = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"Vendored Cesium {version} into {dest} ({total_mb:.1f} MiB total)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Cesium release to vendor")
    parser.add_argument("--dest", default="cesiumkit/vendor/cesium", help="destination directory")
    checksum_group = parser.add_mutually_exclusive_group()
    checksum_group.add_argument("--sha256", help="expected SHA-256 for a custom Cesium release")
    checksum_group.add_argument(
        "--no-verify",
        action="store_true",
        help="deliberately download without checksum verification (not for releases or CI)",
    )
    args = parser.parse_args()
    try:
        checksum = resolve_checksum(args.version, args.sha256, not args.no_verify)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        fetch(args.version, Path(args.dest), checksum)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()
