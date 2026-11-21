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
             mock.patch.object(windows_build, "verify_toolchain", return_value=env) as verify_toolchain, \
             mock.patch.object(windows_build, "mach", return_value=0) as mach, \
             mock.patch.object(windows_build, "executable", return_value=objdir / "firefox.exe"), \
             redirect_stdout(io.StringIO()):
            for command in ("prepare", "bootstrap", "verify-toolchain", "build") * 2:
                args = ["windows_build.py", "--source", str(self.repo), command]
                with mock.patch.object(sys, "argv", args):
                    self.assertEqual(windows_build.main(), 0)

        self.assertEqual(mach.call_args_list, [
            mock.call(self.repo, "bootstrap", "--application-choice", "browser", env=env),
            mock.call(self.repo, "configure", env=env),
            mock.call(self.repo, "configure", env=env),
            mock.call(self.repo, "build", env=env),
        ] * 2)
        self.assertEqual(verify_toolchain.call_args_list, [
            mock.call(self.repo, env, cargo=True),
            mock.call(self.repo, env, cargo=False),
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

    def test_selects_local_1450_before_inherited_tools(self):
        program_files = self.workspace / "Program Files (x86)"
        toolset = program_files / "Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.50.35729"
        vc_bin = toolset / "bin/Hostx64/x64"
        vc_bin.mkdir(parents=True)
        (vc_bin / "cl.exe").touch()
        atl_headers = toolset / "atlmfc/include"
        atl_headers.mkdir(parents=True)
        (atl_headers / "atlbase.h").touch()
        (toolset / "atlmfc/lib/x64").mkdir(parents=True)
        sdk = program_files / "Windows Kits/10"
        (sdk / "Include").mkdir(parents=True)
        (sdk / "Lib").mkdir()
        inherited = str(self.workspace / "14.52.37025/bin/Hostx64/x64")
        with mock.patch.dict(os.environ, {
            "PATH": inherited, "VC_PATH": str(toolset), "WINDOWSSDKDIR": str(sdk),
            "INCLUDE": "old headers", "LIB": "old libraries", "LIBPATH": "old library path",
            "EXTERNAL_INCLUDE": "old headers", "CL": "old compiler flags", "_CL_": "old compiler flags",
        }, clear=True):
            env = windows_build.toolchain_environment()
            self.assertEqual(os.environ["INCLUDE"], "old headers")
        self.assertEqual(env["PATH"].split(os.pathsep), [str(vc_bin), inherited])
        self.assertEqual(env["VC_PATH"], toolset.as_posix())
        self.assertEqual(env["WINDOWSSDKDIR"], sdk.as_posix())
        self.assertTrue({"INCLUDE", "LIB", "LIBPATH", "EXTERNAL_INCLUDE", "CL", "_CL_"}.isdisjoint(env))

    def test_build_checks_configured_headers_before_compiling(self):
        config_dir = self.repo / windows_build.OBJECT_DIR
        config_dir.mkdir()
        config = config_dir / "config.status.json"
        program_files = self.workspace / "Program Files (x86)"
        vc = program_files / "Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.50.35717"
        old_header = vc / "include/yvals_core.h"
        new_header = vc.parent / "14.52.37025/include/yvals_core.h"
        sdk = program_files / "Windows Kits/10"
        windows_header = sdk / "Include/10.0.26100.0/um/windows.h"
        vc_bin = vc / "bin/Hostx64/x64"
        for path in (old_header, old_header.with_name("vector"), new_header, windows_header, vc_bin / "cl.exe"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        compiler = [str(self.workspace / "Mozilla clang/bin/clang-cl.exe"), "--target=x86_64-pc-windows-msvc"]
        resource_dir = self.workspace / "Mozilla clang/lib/clang/21"
        clang_yvals = resource_dir / "include/yvals_core.h"
        env = {"MOZCONFIG": str(windows_build.MOZCONFIG), "PATH": str(new_header.parent.parent)}
        includes = f"{old_header.parent};{windows_header.parent}"

        def configure_with(include_paths):
            config.write_text(json.dumps({"substs": {
                "CC_TYPE": "clang-cl", "CC_VERSION": "21.1.8",
                "HOST_CC_TYPE": "clang-cl", "HOST_CC_VERSION": "21.1.8",
                "INCLUDE": include_paths, "LIB": "configured libraries",
                "CXXCPP": [compiler[0], "-E", *compiler[1:]],
            }}), encoding="utf-8")

        opened_header = new_header

        def probe(args, *, cwd, env, **capture):
            path = cwd / args[-1]
            output = path.with_suffix(".obj")
            self.assertEqual(args[:-1], [
                *compiler, "/c", "/showIncludes", "/clang:-v", f"/Fo{output.name}",
            ])
            self.assertEqual(path.parent.parent, config_dir)
            self.assertEqual(path.read_bytes(), b"#include <vector>\n#include <windows.h>\n")
            self.assertEqual(args[-1], path.name)
            self.assertEqual(capture["stdout"], subprocess.PIPE)
            self.assertEqual(env["INCLUDE"], includes)
            self.assertEqual(env["LIB"], "configured libraries")
            self.assertEqual(env["VCINSTALLDIR"], str(vc.parent.parent.parent))
            self.assertEqual(env["VCTOOLSINSTALLDIR"], str(vc))
            self.assertEqual(env["VSCMD_ARG_TGT_ARCH"], "x64")
            self.assertEqual(env["PATH"].split(os.pathsep)[0], str(vc_bin))
            self.assertEqual(env["_CL_"], (
                f'/vctoolsdir "{vc.as_posix()}" /winsdkdir "{sdk.as_posix()}" /winsdkversion 10.0.26100.0'
            ))
            output.touch()
            return subprocess.CompletedProcess(
                args, 0, stdout=(
                    f"Note: including file: {opened_header.with_name('vector')}\n"
                    f"Note: including file:    {clang_yvals}\n"
                    f"Note: including file:    {opened_header}\n"
                    f"Note: including file: {windows_header}\n"
                ),
            )

        args = ["windows_build.py", "--source", str(self.repo), "build"]
        with mock.patch.object(sys, "argv", args), \
             mock.patch.object(windows_build, "require_windows"), \
             mock.patch.object(windows_build, "toolchain_environment", return_value=env), \
             mock.patch.object(windows_build, "executable", return_value=config_dir / "firefox.exe"), \
             mock.patch.object(windows_build, "mach", return_value=0) as mach, \
             mock.patch.object(windows_build, "verify_overlay") as verify_overlay, \
             mock.patch.object(windows_build.subprocess, "check_output", return_value=str(resource_dir)) as query, \
             mock.patch.object(windows_build.subprocess, "run", side_effect=probe) as run, \
             redirect_stdout(io.StringIO()):
            configure_with(f"{new_header.parent};{includes}")
            with self.assertRaisesRegex(ValueError, "14.50.*14.52"):
                windows_build.verify_toolchain(self.repo, env)
            with self.assertRaises(SystemExit) as error, mock.patch.object(sys, "stderr", io.StringIO()):
                windows_build.main()
            self.assertEqual(error.exception.code, 1)
            mach.assert_called_once_with(self.repo, "configure", env=env)
            run.assert_not_called()

            mach.reset_mock()
            configure_with(includes)
            with self.assertRaisesRegex(ValueError, "Expected Clang to open .*14.50.*observed .*14.52"):
                windows_build.verify_toolchain(self.repo, env)
            with self.assertRaises(SystemExit) as error, mock.patch.object(sys, "stderr", io.StringIO()):
                windows_build.main()
            self.assertEqual(error.exception.code, 1)
            mach.assert_called_once_with(self.repo, "configure", env=env)

            mach.reset_mock()
            run.side_effect = None
            run.return_value = subprocess.CompletedProcess(compiler, 1, stdout="STL1000\n")
            with self.assertRaises(SystemExit) as error, mock.patch.object(sys, "stderr", io.StringIO()):
                windows_build.main()
            self.assertEqual(error.exception.code, 1)
            mach.assert_called_once_with(self.repo, "configure", env=env)

            mach.reset_mock()
            run.reset_mock()
            run.side_effect = probe
            opened_header = old_header
            self.assertEqual(windows_build.main(), 0)
            selected_env = run.call_args.kwargs["env"]
            self.assertEqual(mach.call_args_list, [
                mock.call(self.repo, "configure", env=env), mock.call(self.repo, "build", env=selected_env),
            ])
            self.assertEqual(query.call_args.args[0], [*compiler, "/clang:-print-resource-dir"])
            self.assertEqual(query.call_args.kwargs["env"], selected_env)
            run.assert_called_once()
            self.assertEqual(verify_overlay.call_count, 4)

    def test_clang_forwarder_does_not_replace_the_verified_msvc_header(self):
        stl = self.workspace / "Program Files (x86)/VC/Tools/MSVC/14.50.35717/include"
        expected = stl / "yvals_core.h"
        newer = stl.parent.parent / "14.52.37025/include/yvals_core.h"
        clang_yvals = self.workspace / "Mozilla clang/lib/clang/21/include/yvals_core.h"
        trace = f"Note: including file: {clang_yvals}\n"
        for output in (trace, trace + f"Note: including file: {newer}\n"):
            with self.subTest(trace=output), mock.patch.object(
                windows_build.subprocess, "run",
                return_value=subprocess.CompletedProcess(["clang-cl"], 0, stdout=output),
            ), self.assertRaisesRegex(ValueError, "Expected Clang to open .*14.50"):
                windows_build.check_header_probe(["clang-cl"], self.repo, {}, (expected,), clang_yvals=clang_yvals)

    def test_cargo_probe_is_offline_and_uses_configured_compilers(self):
        directory = self.workspace / "toolchain probe"
        directory.mkdir()
        clang = str(self.workspace / "Mozilla clang/clang-cl.exe")
        substs = {
            "CC": clang, "CPP": [clang, "-E", "--target=x86_64-pc-windows-msvc"],
            "CXXCPP": [clang, "-E", "/std:c++20"], "RUSTC": "configured-rustc.exe",
            "CARGO": "configured-cargo.exe",
        }
        vc = self.workspace / "Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.50.35717"
        sdk = self.workspace / "Program Files (x86)/Windows Kits/10"
        env = {
            "_CL_": f'/vctoolsdir "{vc.as_posix()}" /winsdkdir "{sdk.as_posix()}" /winsdkversion 10.0.26100.0',
            "VCINSTALLDIR": str(vc.parent.parent.parent),
        }
        headers = (vc / "include/vector", vc / "include/yvals_core.h", sdk / "Include/10.0.26100.0/um/windows.h")
        clang_yvals = self.workspace / "Mozilla clang/lib/clang/21/include/yvals_core.h"
        with mock.patch.object(windows_build, "check_header_probe") as check, redirect_stdout(io.StringIO()):
            windows_build.check_cargo_headers(self.repo, directory, substs, env, headers, clang_yvals=clang_yvals)

        args, cwd, cargo_env, expected = check.call_args.args
        self.assertEqual(args, [
            "configured-cargo.exe", "check", "--offline", "-vv", "--config", str(directory / "vendor.toml"),
            "--target", "x86_64-pc-windows-msvc", "--target-dir", str(directory / "target"),
        ])
        self.assertEqual(cwd, directory)
        self.assertEqual(expected, headers)
        self.assertEqual(check.call_args.kwargs["clang_yvals"], clang_yvals)
        self.assertEqual(cargo_env["CC_x86_64_pc_windows_msvc"], clang)
        self.assertEqual(cargo_env["CXX_x86_64_pc_windows_msvc"], clang)
        self.assertEqual(cargo_env["CXXFLAGS_x86_64_pc_windows_msvc"], "/std:c++20")
        self.assertEqual(cargo_env["RUSTC"], "configured-rustc.exe")
        self.assertEqual(cargo_env["_CL_"], env["_CL_"])
        self.assertEqual(cargo_env["VCINSTALLDIR"], env["VCINSTALLDIR"])
        self.assertIn((self.repo / "third_party/rust").as_posix(), (directory / "vendor.toml").read_text())
        self.assertIn('cc = "=1.2.30"', (directory / "Cargo.toml").read_text())
        self.assertIn('.cpp(true).file("headers.cpp")', (directory / "build.rs").read_text())


if __name__ == "__main__":
    unittest.main()
