#!/usr/bin/env python3
"""Prepare, build, and launch the native Windows x64 Aelthoren development tree."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
DEFAULT_SOURCE = ROOT.parent / "aelthoren-gecko-windows"
MOZCONFIG = ROOT / "config/mozconfig.windows-x64"
OBJECT_DIR = "obj-aelthoren-windows"
BRANDING = Path("browser/branding/aelthoren-windows")
MARKER = ".aelthoren-windows.json"
PATCHES = tuple(ROOT / "patches" / name for name in (
    "0001-phase2-ui.patch",
    "0002-phase3-search.patch",
    "0003-phase3-account-settings.patch",
))
CONTENT = tuple(ROOT / "branding/content" / name for name in (
    "newtab.html", "about-aelthoren.html", "aelthoren.css",
))
WINDOWS_ASSETS = ROOT / "branding/windows"
LOGO = ROOT / "assets/A_text.svg"
DISTRIBUTION = {
    "policies.json": ROOT / "config/privacy-policies.json",
    "distribution.ini": ROOT / "config/distribution.ini",
}


def git(source, *args):
    return subprocess.check_output(["git", *args], cwd=source)


def verify_source(source):
    if source.is_relative_to(ROOT):
        raise ValueError("Keep the Firefox checkout outside the Aelthoren repository.")
    root = Path(os.fsdecode(git(source, "rev-parse", "--show-toplevel").rstrip()))
    if root.resolve() != source:
        raise ValueError(f"Use the root of a dedicated Firefox checkout: {source}")
    revision = git(source, "rev-parse", "HEAD").decode("ascii").strip()
    if revision != LOCK["revision"]:
        raise ValueError(f"Firefox HEAD {revision} differs from the pin {LOCK['revision']}")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_patches():
    return {path: path.read_bytes().replace(b"\r\n", b"\n") for path in PATCHES}


def overlay_state(source, brand, patches):
    inputs = dict(patches)
    for path in (*CONTENT, *DISTRIBUTION.values(), LOGO, *WINDOWS_ASSETS.iterdir()):
        inputs[path] = path.read_bytes()
    return {
        "revision": LOCK["revision"],
        "inputs": {path.relative_to(ROOT).as_posix(): digest(data) for path, data in inputs.items()},
        "tracked_diff": digest(git(
            source, "diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD", "--",
        )),
        "branding": {
            path.relative_to(brand).as_posix(): digest(path.read_bytes())
            for path in brand.rglob("*") if path.is_file() and path != brand / MARKER
        },
    }


def verify_overlay(source):
    verify_source(source)
    brand = source / BRANDING
    marker = brand / MARKER
    if not marker.is_file():
        raise ValueError("Windows overlay is missing. Run prepare in a clean, pinned checkout.")
    untracked = git(source, "ls-files", "--others", "--exclude-standard", "--directory", "-z")
    if untracked != f"{BRANDING.as_posix()}/\0".encode("ascii"):
        raise ValueError("Unexpected untracked Firefox files. Review the checkout before continuing.")
    if json.loads(marker.read_text(encoding="utf-8")) != overlay_state(source, brand, read_patches()):
        raise ValueError("Windows overlay or inputs changed. Preserve edits and prepare a clean checkout.")


def edit_text(path, replacements=(), suffix=""):
    content = path.read_text(encoding="utf-8")
    for before, after in replacements:
        if before not in content:
            raise ValueError(f"Branding template differs from the expected source: {path}")
        content = content.replace(before, after)
    path.write_bytes((content + suffix).encode("utf-8"))


def generate_branding(template, brand):
    shutil.copytree(template, brand)
    content = brand / "content"
    logo = ET.parse(LOGO)
    logo.getroot().attrib.update(viewBox="-57 -40 130 130", width="512", height="512")
    logo.write(content / "about-logo.svg", encoding="utf-8", xml_declaration=True)
    for size in (16, 32, 48, 64, 128):
        shutil.copyfile(WINDOWS_ASSETS / f"logo{size}.png", brand / f"default{size}.png")
    for name in ("about.png", "about-logo.png", "about-logo-private.png"):
        shutil.copyfile(WINDOWS_ASSETS / "logo192.png", content / name)
    for name in ("about-logo@2x.png", "about-logo-private@2x.png"):
        shutil.copyfile(WINDOWS_ASSETS / "logo384.png", content / name)
    for size in (70, 150):
        for name in ("VisualElements", "PrivateBrowsing"):
            shutil.copyfile(WINDOWS_ASSETS / f"logo{size}.png", brand / f"{name}_{size}.png")
    for name in ("firefox.ico", "firefox64.ico", "pbmode.ico"):
        shutil.copyfile(WINDOWS_ASSETS / "aelthoren.ico", brand / name)
    for name in ("about-wordmark.svg", "firefox-wordmark.svg"):
        shutil.copyfile(WINDOWS_ASSETS / "wordmark.svg", content / name)

    edit_text(brand / "configure.sh", (("MOZ_APP_DISPLAYNAME=Nightly", "MOZ_APP_DISPLAYNAME=Aelthoren"),))
    locale = brand / "locales/en-US"
    edit_text(locale / "brand.ftl", (("= Nightly", "= Aelthoren"),
                                    ("-brand-product-name = Firefox", "-brand-product-name = Aelthoren")))
    edit_text(locale / "brand.properties", (("=Nightly", "=Aelthoren"),))
    edit_text(content / "aboutDialog.css", (("#130829", "#1b1b1b"),),
              suffix="\n#rightBox { background-size: 360px auto; }\n")
    for path in CONTENT:
        shutil.copyfile(path, content / path.name)
    edit_text(content / "jar.mn", suffix=(
        "\n" + "".join(f"  content/branding/{path.name}\n" for path in CONTENT)
        + "% resource aelthoren %content/branding/\n"
    ))

    (brand / "distribution").mkdir()
    for name, path in DISTRIBUTION.items():
        shutil.copyfile(path, brand / "distribution" / name)
    edit_text(brand / "moz.build", suffix=(
        '\nFINAL_TARGET_FILES[".."].distribution += [\n'
        + "".join(f'    "distribution/{name}",\n' for name in sorted(DISTRIBUTION))
        + "]\n"
    ))


def prepare(source):
    verify_source(source)
    brand = source / BRANDING
    if brand.exists():
        verify_overlay(source)
        print(f"Windows overlay verified at {LOCK['revision']}")
        return
    if git(source, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise ValueError("Prepare requires a clean Windows-specific Firefox checkout.")

    patches = read_patches()
    with TemporaryDirectory(prefix="aelthoren-brand-", dir=brand.parent) as temporary:
        staging = Path(temporary)
        patch_args = []
        for path, data in patches.items():
            staged_patch = staging / path.name
            staged_patch.write_bytes(data)
            patch_args.append(str(staged_patch))
        git(source, "apply", "--check", *patch_args)
        staged_brand = staging / brand.name
        generate_branding(brand.parent / "unofficial", staged_brand)
        git(source, "apply", *patch_args)
        try:
            manifest = json.dumps(overlay_state(source, staged_brand, patches), indent=2, sort_keys=True)
            (staged_brand / MARKER).write_bytes((manifest + "\n").encode("utf-8"))
            staged_brand.rename(brand)
        except (OSError, subprocess.CalledProcessError):
            git(source, "apply", "--reverse", *patch_args)
            raise
    verify_overlay(source)
    print(f"Prepared Windows overlay at {LOCK['revision']}")


def require_windows():
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise ValueError("Bootstrap, build, and run require native Windows x64. Source preparation is available here.")
    if not os.environ.get("MOZILLABUILD"):
        raise ValueError("Start the MozillaBuild shell with C:\\mozilla-build\\start-shell.bat.")


def mach(source, *args):
    env = dict(os.environ, MOZCONFIG=MOZCONFIG.as_posix())
    return subprocess.run([sys.executable, "mach", *args], cwd=source, env=env).returncode


def executable(source):
    binary = source / OBJECT_DIR / "dist/bin/firefox.exe"
    with binary.open("rb") as stream:
        header = stream.read(64)
        if len(header) != 64 or header[:2] != b"MZ":
            raise ValueError(f"Expected a native Windows executable: {binary}")
        stream.seek(struct.unpack_from("<I", header, 60)[0])
        if stream.read(6) != b"PE\0\0\x64\x86":
            raise ValueError(f"Expected an AMD64 PE executable: {binary}")
    for name, path in DISTRIBUTION.items():
        if (binary.parent / "distribution" / name).read_bytes() != path.read_bytes():
            raise ValueError(f"Build output has unexpected distribution config: {name}")
    return binary


def launch(binary, profile_name):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", profile_name):
        raise ValueError("Profile name must be 1–40 letters, digits, underscores, or hyphens.")
    local_appdata = Path(os.environ["LOCALAPPDATA"])
    profile = local_appdata / "Aelthoren/Development/Profiles" / f"profile-{profile_name}"
    profile.mkdir(parents=True, exist_ok=True)
    print(f"Launching {binary} with profile {profile}", flush=True)
    return subprocess.run(
        [str(binary), "-wait-for-browser", "-new-instance", "-profile", str(profile)],
        cwd=binary.parent,
    ).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Dedicated Firefox checkout")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "bootstrap", "build"):
        commands.add_parser(command)
    run = commands.add_parser("run")
    run.add_argument("--profile", default="default")
    args = parser.parse_args()
    source = args.source.resolve()
    try:
        if args.command == "prepare":
            prepare(source)
            return 0
        require_windows()
        verify_overlay(source)
        if args.command == "bootstrap":
            return mach(source, "bootstrap", "--application-choice", "browser")
        if args.command == "build":
            status = mach(source, "build")
            if status:
                return status
            print(f"Windows x64 build output: {executable(source)}")
            return 0
        return launch(executable(source), args.profile)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
