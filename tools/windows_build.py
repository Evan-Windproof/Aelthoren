#!/usr/bin/env python3
"""Prepare, build, and launch the native Windows x64 Aelthoren development tree."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
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
CLANG_VERSION = "21.1.8"
MSVC_SERIES = "14.50"
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
    state = overlay_state(source, brand, read_patches())
    if json.loads(marker.read_text(encoding="utf-8")) != state:
        raise ValueError("Windows overlay or inputs changed. Preserve edits and prepare a clean checkout.")

    allowed = {os.fsencode((BRANDING / name).as_posix()) for name in (*state["branding"], MARKER)}
    untracked = git(source, "ls-files", "--others", "--exclude-standard", "-z")
    for path in untracked.split(b"\0"):
        if path and path not in allowed:
            raise ValueError(f"Unexpected untracked Firefox files. Review {os.fsdecode(path)!r}.")


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
        raise ValueError("Toolchain checks, bootstrap, build, and run require native Windows x64.")
    if not os.environ.get("MOZILLABUILD"):
        raise ValueError("Start the MozillaBuild shell with C:\\mozilla-build\\start-shell.bat.")


def toolchain_environment():
    env = dict(os.environ, MOZCONFIG=MOZCONFIG.as_posix())
    for name in ("INCLUDE", "LIB", "LIBPATH", "EXTERNAL_INCLUDE", "CL", "_CL_"):
        env.pop(name, None)

    vc_path = env.get("VC_PATH")
    sdk_path = env.get("WINDOWSSDKDIR")
    if bool(vc_path) != bool(sdk_path):
        raise ValueError("Set both VC_PATH and WINDOWSSDKDIR to select a local toolchain.")
    if vc_path:
        if env.get("WINSYSROOT"):
            raise ValueError("Unset WINSYSROOT before selecting a local VC_PATH and WINDOWSSDKDIR.")
        vc = Path(vc_path).resolve()
        sdk = Path(sdk_path).resolve()
        vc_bin = vc / "bin/Hostx64/x64"
        if not vc.name.startswith(MSVC_SERIES + ".") or not (vc_bin / "cl.exe").is_file():
            raise ValueError(f"VC_PATH must point to the x64 MSVC {MSVC_SERIES} toolset: {vc}")
        if not (vc / "atlmfc/include/atlbase.h").is_file() or not (vc / "atlmfc/lib/x64").is_dir():
            raise ValueError(f"Install the matching x64/x86 ATL component for MSVC {MSVC_SERIES}: {vc}")
        if not (sdk / "Include").is_dir() or not (sdk / "Lib").is_dir():
            raise ValueError(f"WINDOWSSDKDIR must point to a Windows SDK root: {sdk}")
        env.update(VC_PATH=vc.as_posix(), WINDOWSSDKDIR=sdk.as_posix())
        # Configure looks for cl.exe on PATH before its selected toolset directory.
        env["PATH"] = str(vc_bin) + os.pathsep + env["PATH"]
    return env


def mach(source, *args, env):
    return subprocess.run([sys.executable, "mach", *args], cwd=source, env=env).returncode


def check_header_probe(args, cwd, env, expected_headers):
    result = subprocess.run(
        args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace",
    )
    if result.returncode:
        print(result.stdout, file=sys.stderr, end="")
        raise ValueError("The configured compiler failed the MSVC STL and Windows SDK header check.")

    headers = []
    for line in result.stdout.splitlines():
        _, found, path = line.partition("Note: including file:")
        if found:
            headers.append(Path(path.strip()))
    for expected in expected_headers:
        opened = {path.resolve() for path in headers if path.name.lower() == expected.name}
        if opened != {expected.resolve()}:
            actual = ", ".join(str(path) for path in sorted(opened)) or "no include trace"
            raise ValueError(f"Expected Clang to open {expected}, but observed {actual}.")
        print(f"Verified header: {expected.resolve()}")


def check_cargo_headers(source, directory, substs, env, expected_headers):
    vendor = json.dumps((source / "third_party/rust").as_posix(), ensure_ascii=False)
    config = directory / "vendor.toml"
    config.write_text(
        '[source.crates-io]\nreplace-with = "vendored-sources"\n'
        f"[source.vendored-sources]\ndirectory = {vendor}\n", encoding="utf-8",
    )
    (directory / "Cargo.toml").write_text(
        '[package]\nname = "w1-header-probe"\nversion = "0.0.0"\nedition = "2021"\n'
        '[lib]\npath = "lib.rs"\n[workspace]\n[build-dependencies]\ncc = "=1.2.30"\n',
        encoding="utf-8",
    )
    (directory / "lib.rs").touch()
    (directory / "headers.c").write_bytes(b"#include <stdlib.h>\n#include <windows.h>\n")
    (directory / "build.rs").write_bytes(
        b'fn main() {\n'
        b'    cc::Build::new().file("headers.c").flag("/showIncludes").compile("probe_c");\n'
        b'    cc::Build::new().cpp(true).file("headers.cpp").flag("/showIncludes").compile("probe_cpp");\n'
        b'}\n'
    )
    cargo_env = dict(env, RUSTC=substs["RUSTC"], CC_SHELL_ESCAPED_FLAGS="1")
    for compiler, preprocessor in (("CC", "CPP"), ("CXX", "CXXCPP")):
        command = substs[preprocessor]
        separator = command.index("-E")
        cargo_env[f"{compiler}_x86_64_pc_windows_msvc"] = command[separator - 1]
        cargo_env[f"{compiler}FLAGS_x86_64_pc_windows_msvc"] = shlex.join(command[separator + 1:])
    print("Compiling the C and C++ probes through vendored cc-rs (offline)", flush=True)
    check_header_probe(
        [substs["CARGO"], "check", "--offline", "-vv", "--config", str(config),
         "--target", "x86_64-pc-windows-msvc", "--target-dir", str(directory / "target")],
        directory, cargo_env, expected_headers,
    )


def verify_toolchain(source, env, *, cargo=False):
    configuration = source / OBJECT_DIR / "config.status.json"
    substs = json.loads(configuration.read_text(encoding="utf-8"))["substs"]
    for cc in ("CC", "HOST_CC"):
        compiler = substs[f"{cc}_TYPE"]
        version = substs[f"{cc}_VERSION"]
        if (compiler, version) != ("clang-cl", CLANG_VERSION):
            raise ValueError(f"Expected Mozilla clang-cl {CLANG_VERSION}, configured {cc} as {compiler} {version}.")

    includes = substs["INCLUDE"]
    directories = [Path(path).resolve() for path in includes.split(";") if path]
    stl = next((path for path in directories if (path / "yvals_core.h").is_file()), None)
    if stl is None or not stl.parent.name.startswith(MSVC_SERIES + "."):
        raise ValueError(
            f"Clang {version} expected MSVC {MSVC_SERIES} STL headers, found {stl}. "
            "Use a fresh MozillaBuild shell or select the side-by-side toolset in docs/WINDOWS_BUILD.md."
        )
    um = next((path for path in directories if path.name.lower() == "um" and (path / "windows.h").is_file()), None)
    if um is None or um.parent.parent.name.lower() != "include":
        raise ValueError("Could not locate the configured Windows SDK header directory.")
    vc = stl.parent
    vc_bin = vc / "bin/Hostx64/x64"
    if not (vc_bin / "cl.exe").is_file():
        raise ValueError(f"Could not locate the configured x64 MSVC tools: {vc_bin}")

    # cc-rs uses the developer environment instead of rediscovering Visual Studio
    # when VCINSTALLDIR and the target architecture are set and cl.exe is on PATH.
    build_env = dict(
        env,
        VCINSTALLDIR=str(vc.parent.parent.parent),
        VCTOOLSINSTALLDIR=str(vc),
        VSCMD_ARG_TGT_ARCH="x64",
        PATH=str(vc_bin) + os.pathsep + env["PATH"],
        INCLUDE=includes,
        LIB=substs["LIB"],
    )
    # clang-cl appends _CL_ to its arguments, including in cc-rs child processes.
    build_env["_CL_"] = subprocess.list2cmdline([
        f"/vctoolsdir:{vc.as_posix()}",
        f"/winsdkdir:{um.parent.parent.parent.as_posix()}",
        f"/winsdkversion:{um.parent.name}",
    ])

    print(f"Compiling toolchain probe with clang-cl {CLANG_VERSION} and MSVC {vc.name}", flush=True)
    command = list(substs["CXXCPP"])
    command.remove("-E")
    expected_headers = (stl / "yvals_core.h", um / "windows.h")
    with TemporaryDirectory(prefix="w1-toolchain-", dir=configuration.parent) as temporary:
        probe = Path(temporary) / "headers.cpp"
        probe.write_bytes(b"#include <vector>\n#include <windows.h>\n")
        check_header_probe(
            [*command, "/c", "/showIncludes", f"/Fo{probe.with_suffix('.obj')}", str(probe)],
            source, build_env, expected_headers,
        )
        if cargo:
            check_cargo_headers(source, probe.parent, substs, build_env, expected_headers)
    return build_env


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
    for command in ("prepare", "bootstrap", "verify-toolchain", "build"):
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
            return mach(source, "bootstrap", "--application-choice", "browser", env=toolchain_environment())
        if args.command in ("verify-toolchain", "build"):
            env = toolchain_environment()
            status = mach(source, "configure", env=env)
            if status:
                return status
            env = verify_toolchain(source, env, cargo=args.command == "verify-toolchain")
            if args.command == "verify-toolchain":
                return 0
            status = mach(source, "build", env=env)
            if status:
                return status
            print(f"Windows x64 build output: {executable(source)}")
            return 0
        return launch(executable(source), args.profile)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
