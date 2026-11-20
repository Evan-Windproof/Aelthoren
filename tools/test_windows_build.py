"""Regression tests for W1 patch preparation and overlay validation."""

from contextlib import redirect_stdout
import io
import json
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

        with mock.patch.object(windows_build, "require_windows"), \
             mock.patch.object(windows_build, "mach", return_value=0) as mach, \
             mock.patch.object(windows_build, "executable", return_value=objdir / "firefox.exe"), \
             redirect_stdout(io.StringIO()):
            for command in ("prepare", "bootstrap", "build") * 2:
                args = ["windows_build.py", "--source", str(self.repo), command]
                with mock.patch.object(sys, "argv", args):
                    self.assertEqual(windows_build.main(), 0)

        self.assertEqual(mach.call_args_list, [
            mock.call(self.repo, "bootstrap", "--application-choice", "browser"),
            mock.call(self.repo, "build"),
        ] * 2)
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


if __name__ == "__main__":
    unittest.main()
