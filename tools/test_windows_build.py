"""Regression tests for W1 patch checkout and preparation."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import windows_build


class WindowsPatchPreparation(unittest.TestCase):
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
        self.git("add", "--", ".gitattributes", "first.txt", "second.txt", "browser")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "--quiet", "-m", "LF source")
        revision = self.git("rev-parse", "HEAD").stdout.decode("ascii").strip()

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


if __name__ == "__main__":
    unittest.main()
