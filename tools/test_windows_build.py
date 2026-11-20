"""Regression tests for W1 patch preparation and overlay validation."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import windows_build


class WindowsBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name).resolve()
        self.repo = self.workspace / "checkout"
        self.repo.mkdir()
        self.git("init", "--quiet")
        self.git("config", "core.autocrlf", "true")
        self.git("config", "core.eol", "crlf")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.repo, check=check, capture_output=True)

    def commit_fixture(self):
        self.git("add", "--", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgSign=false", "commit", "--quiet", "-m", "Firefox fixture")
        return self.git("rev-parse", "HEAD").stdout.decode("ascii").strip()

    def test_patch_checkout_keeps_lf_with_crlf_git_settings(self):
        shutil.copyfile(windows_build.ROOT / ".gitattributes", self.repo / ".gitattributes")
        (self.repo / "patches").mkdir()
        patch_paths = [path.relative_to(windows_build.ROOT) for path in windows_build.PATCHES]
        for path in patch_paths:
            shutil.copyfile(windows_build.ROOT / path, self.repo / path)
        self.git("add", "--", ".gitattributes", "patches")

        for path in patch_paths:
            (self.repo / path).unlink()
        self.git("checkout-index", "--", *(path.as_posix() for path in patch_paths))

        for path in patch_paths:
            with self.subTest(patch=path.name):
                committed = self.git("show", f":{path.as_posix()}").stdout
                self.assertIn(b"\n", committed)
                self.assertNotIn(b"\r", committed)
                self.assertEqual((self.repo / path).read_bytes(), committed)

    def test_prepare_retries_after_failed_patch_check(self):
        (self.repo / ".gitattributes").write_bytes(b"* -text\n")
        for name in ("first.txt", "second.txt"):
            (self.repo / name).write_bytes(b"before\n")
        brand_parent = self.repo / "browser/branding"
        brand_parent.mkdir(parents=True)
        (brand_parent / "README").write_bytes(b"Upstream branding\n")
        revision = self.commit_fixture()

        project = self.workspace / "project"
        project.mkdir()
        patches = (project / "first.patch", project / "second.patch")
        patch_data = []
        for patch in patches:
            name = f"{patch.stem}.txt"
            (self.repo / name).write_bytes(b"after\n")
            patch_data.append(self.git("diff", "--", name).stdout)
            self.git("restore", "--worktree", "--", name)

        first_crlf = patch_data[0].replace(b"\n", b"\r\n")
        patches[0].write_bytes(first_crlf)
        failed = self.git("apply", "--check", str(patches[0]), check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn(b"patch does not apply", failed.stderr)
        self.assertEqual(self.git("status", "--porcelain").stdout, b"")

        asset_dir = project / "assets"
        asset_dir.mkdir()
        logo = project / "logo.svg"
        logo.write_bytes(b"<svg/>")
        with mock.patch.multiple(
            windows_build, ROOT=project, LOCK={"revision": revision}, PATCHES=patches,
            CONTENT=(), DISTRIBUTION={}, LOGO=logo, WINDOWS_ASSETS=asset_dir,
        ), mock.patch.object(windows_build, "generate_branding") as branding, redirect_stdout(io.StringIO()):
            branding.side_effect = lambda template, brand: brand.mkdir()
            patches[1].write_bytes(b"invalid patch\n")
            with self.assertRaises(subprocess.CalledProcessError):
                windows_build.prepare(self.repo)
            branding.assert_not_called()
            self.assertEqual(self.git("status", "--porcelain").stdout, b"")

            patches[1].write_bytes(patch_data[1])
            windows_build.prepare(self.repo)
            for name in ("first.txt", "second.txt"):
                self.assertEqual((self.repo / name).read_bytes(), b"after\n")
            self.assertEqual(patches[0].read_bytes(), first_crlf)

            marker = self.repo / windows_build.BRANDING / windows_build.MARKER
            previous = marker.read_bytes()
            patches[0].write_bytes(patch_data[0])
            windows_build.prepare(self.repo)
            self.assertEqual(marker.read_bytes(), previous)
            self.assertEqual(branding.call_count, 1)

    def prepared_overlay(self):
        (self.repo / ".gitattributes").write_bytes(b"* -text\n")
        (self.repo / ".gitignore").write_bytes(b"/obj*/\n*.ignored\n")
        tracked = self.repo / "browser/branding/unofficial/README"
        tracked.parent.mkdir(parents=True)
        tracked.write_bytes(b"Upstream\n")
        lock = mock.patch.dict(windows_build.LOCK, revision=self.commit_fixture())
        lock.start()
        self.addCleanup(lock.stop)
        tracked.write_bytes(b"Reviewed patch\n")

        brand = self.repo / windows_build.BRANDING
        (brand / "distribution").mkdir(parents=True)
        (brand / "configure.sh").write_bytes(b"Reviewed branding\n")
        (brand / "distribution/default.ignored").write_bytes(b"Reviewed distribution file\n")
        state = windows_build.overlay_state(self.repo, brand, windows_build.read_patches())
        (brand / windows_build.MARKER).write_text(json.dumps(state), encoding="utf-8")
        return tracked, brand

    def test_reuses_verified_overlay_for_prepare_bootstrap_and_build(self):
        _, brand = self.prepared_overlay()
        (self.repo / "empty directory").mkdir()
        objdir = self.repo / windows_build.OBJECT_DIR
        objdir.mkdir()
        (objdir / "build-output").write_bytes(b"object dir artifact")
        marker = brand / windows_build.MARKER
        before = marker.read_bytes()
        env = {"MOZCONFIG": str(windows_build.MOZCONFIG)}

        with mock.patch.object(windows_build, "require_windows"), \
             mock.patch.object(windows_build, "toolchain_environment", return_value=env), \
             mock.patch.object(windows_build, "verify_toolchain") as verify_toolchain, \
             mock.patch.object(windows_build, "mach", return_value=0) as mach, \
             mock.patch.object(windows_build, "executable", return_value=objdir / "firefox.exe"), \
             redirect_stdout(io.StringIO()):
            for command in ("prepare", "bootstrap", "build") * 2:
                args = ["windows_build.py", "--source", str(self.repo), command]
                with mock.patch.object(sys, "argv", args):
                    self.assertEqual(windows_build.main(), 0)

        self.assertEqual(mach.call_args_list, [
            mock.call(self.repo, "bootstrap", "--application-choice", "browser", env=env),
            mock.call(self.repo, "configure", env=env),
            mock.call(self.repo, "build", env=env),
        ] * 2)
        self.assertEqual(verify_toolchain.call_args_list, [mock.call(self.repo, env)] * 2)
        self.assertEqual(marker.read_bytes(), before)

    def test_rejects_unexpected_files_and_modified_overlay(self):
        tracked, brand = self.prepared_overlay()
        outside = self.repo / "unknown file"
        outside.write_bytes(b"Unexpected\n")
        with self.assertRaisesRegex(ValueError, "Unexpected untracked Firefox files.*unknown file"):
            windows_build.verify_overlay(self.repo)
        outside.unlink()

        unexpected = brand / "extra.ignored"
        unexpected.write_bytes(b"Unexpected\n")
        with self.assertRaisesRegex(ValueError, "Windows overlay or inputs changed"):
            windows_build.verify_overlay(self.repo)
        unexpected.unlink()

        for path in (brand / "configure.sh", brand / "distribution/default.ignored", tracked):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(b"Modified\n")
                with self.assertRaisesRegex(ValueError, "Windows overlay or inputs changed"):
                    windows_build.verify_overlay(self.repo)
                path.write_bytes(original)
        windows_build.verify_overlay(self.repo)

    def test_selects_local_1450_before_inherited_tools(self):
        toolset = self.workspace / "VS BuildTools" / "14.50.35729"
        vc_bin = toolset / "bin/Hostx64/x64"
        vc_bin.mkdir(parents=True)
        (vc_bin / "cl.exe").touch()
        atl_headers = toolset / "atlmfc/include"
        atl_headers.mkdir(parents=True)
        (atl_headers / "atlbase.h").touch()
        (toolset / "atlmfc/lib/x64").mkdir(parents=True)
        sdk = self.workspace / "Windows Kits/10"
        (sdk / "Include").mkdir(parents=True)
        (sdk / "Lib").mkdir()
        inherited = str(self.workspace / "14.52.37025/bin/Hostx64/x64")
        with mock.patch.dict(os.environ, {
            "PATH": inherited, "VC_PATH": str(toolset), "WINDOWSSDKDIR": str(sdk),
            "INCLUDE": "old headers", "LIB": "old libraries", "LIBPATH": "old library path",
        }, clear=True):
            env = windows_build.toolchain_environment()
            self.assertEqual(os.environ["INCLUDE"], "old headers")
        self.assertEqual(env["PATH"].split(os.pathsep), [str(vc_bin), inherited])
        self.assertEqual(env["VC_PATH"], toolset.as_posix())
        self.assertEqual(env["WINDOWSSDKDIR"], sdk.as_posix())
        self.assertTrue({"INCLUDE", "LIB", "LIBPATH"}.isdisjoint(env))

    def test_build_checks_configured_headers_before_compiling(self):
        config_dir = self.repo / windows_build.OBJECT_DIR
        config_dir.mkdir()
        config = config_dir / "config.status.json"
        good = self.workspace / "MSVC/14.50.35729/include"
        bad = self.workspace / "MSVC/14.52.37025/include"
        for includes in (good, bad):
            includes.mkdir(parents=True)
            (includes / "yvals_core.h").touch()
        compiler = [str(self.workspace / "Mozilla clang/bin/clang-cl.exe"), "--target=x86_64-pc-windows-msvc"]
        env = {"MOZCONFIG": str(windows_build.MOZCONFIG)}

        def configure_with(includes):
            config.write_text(json.dumps({"substs": {
                "CC_TYPE": "clang-cl", "CC_VERSION": "21.1.8",
                "INCLUDE": includes, "LIB": "configured libraries",
                "CXXCPP": [compiler[0], "-E", *compiler[1:]],
            }}), encoding="utf-8")

        def probe(args, *, cwd, env):
            path = Path(args[-1])
            self.assertEqual(args[:-1], [*compiler, "/Zs"])
            self.assertEqual(path.parent.parent, config_dir)
            self.assertEqual(path.read_bytes(), b"#include <vector>\n#include <windows.h>\n")
            self.assertEqual(cwd, self.repo)
            self.assertEqual(env["INCLUDE"], str(good))
            self.assertEqual(env["LIB"], "configured libraries")
            return subprocess.CompletedProcess(args, 0)

        args = ["windows_build.py", "--source", str(self.repo), "build"]
        with mock.patch.object(sys, "argv", args), \
             mock.patch.object(windows_build, "require_windows"), \
             mock.patch.object(windows_build, "toolchain_environment", return_value=env), \
             mock.patch.object(windows_build, "executable", return_value=config_dir / "firefox.exe"), \
             mock.patch.object(windows_build, "mach", return_value=0) as mach, \
             mock.patch.object(windows_build, "verify_overlay") as verify_overlay, \
             mock.patch.object(windows_build.subprocess, "run", side_effect=probe) as run, \
             redirect_stdout(io.StringIO()):
            configure_with(f"{bad};{good}")
            with self.assertRaisesRegex(ValueError, "14.50.*14.52"):
                windows_build.verify_toolchain(self.repo, env)
            with self.assertRaises(SystemExit) as error, mock.patch.object(sys, "stderr", io.StringIO()):
                windows_build.main()
            self.assertEqual(error.exception.code, 1)
            mach.assert_called_once_with(self.repo, "configure", env=env)
            run.assert_not_called()

            mach.reset_mock()
            configure_with(str(good))
            run.side_effect = None
            run.return_value = subprocess.CompletedProcess(compiler, 1)
            with self.assertRaises(SystemExit) as error, mock.patch.object(sys, "stderr", io.StringIO()):
                windows_build.main()
            self.assertEqual(error.exception.code, 1)
            mach.assert_called_once_with(self.repo, "configure", env=env)

            mach.reset_mock()
            run.reset_mock()
            run.side_effect = probe
            self.assertEqual(windows_build.main(), 0)
            self.assertEqual(mach.call_args_list, [
                mock.call(self.repo, "configure", env=env), mock.call(self.repo, "build", env=env),
            ])
            run.assert_called_once()
            self.assertEqual(verify_overlay.call_count, 3)


if __name__ == "__main__":
    unittest.main()
