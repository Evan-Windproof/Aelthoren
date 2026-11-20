# Windows x64 development build

Phase W1 prepares a full source build of Aelthoren using Firefox ESR
`153.6.0esr` at `a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`. The source
pin comes from [upstream.lock.json](../upstream.lock.json). Gecko and
SpiderMonkey compile locally. The Linux artifact workflow and its validation
reports remain available in [BUILDING.md](../BUILDING.md).

## Required software

- A native x64 Windows 10 or 11 host or VM with a desktop session for acceptance
  testing. Allow at least the 40 GB of free space in Mozilla's guide, with extra
  room for the object dir and toolchain cache.
- Current [MozillaBuild](https://ftp.mozilla.org/pub/mozilla/libraries/win32/MozillaBuildSetup-Latest.exe)
  using its default install path. It supplies the MSYS shell, Git, Python, and
  other utilities. Start `C:\mozilla-build\start-shell.bat` and run the commands
  below in that shell. Use short local paths without spaces for the checkouts.
- Mozilla's full desktop bootstrap and configure supply or select the build
  toolchain. It uses Clang/LLVM for the MSVC ABI, Rust, and Microsoft C++ headers,
  libraries, and Windows SDK tooling. The pinned tree's bootstrap configuration
  points to Mozilla's VS 2026 toolchain with Microsoft Windows SDK 10.0.26100.
  Let Mach resolve these dependencies and reuse its `.mozbuild` cache. Install
  missing tools only if Mach reports a specific requirement.

Mozilla documents the host setup and basic Mach commands in
[Building Firefox on Windows](https://firefox-source-docs.mozilla.org/setup/windows_build.html).
The exact revision's setup guide and toolchain manifest are in
[Firefox source docs](https://github.com/mozilla-firefox/firefox/blob/a34c4160e3f75ab9918fbe4669ff7ae56f1977c8/docs/setup/windows_build.rst)
and [the SDK manifest](https://github.com/mozilla-firefox/firefox/blob/a34c4160e3f75ab9918fbe4669ff7ae56f1977c8/build/vs/vs2026.yaml).

## Source and build

Place the Aelthoren checkout containing these W1 files at
`C:\mozilla-source\Aelthoren`. For a first build, fetch the pinned Firefox commit
into a separate sibling checkout. Skip this fetch when reusing that checkout at
the same revision.

```sh
cd c:/mozilla-source
git init aelthoren-gecko-windows
git -C aelthoren-gecko-windows config core.longpaths true
git -C aelthoren-gecko-windows remote add origin https://github.com/mozilla-firefox/firefox.git
git -C aelthoren-gecko-windows fetch --depth=1 origin a34c4160e3f75ab9918fbe4669ff7ae56f1977c8
git -C aelthoren-gecko-windows checkout --detach FETCH_HEAD
```

From the Aelthoren checkout, prepare the overlay, bootstrap once, and build.
The bootstrap invokes Mozilla's `mach bootstrap --application-choice browser`.
If Mozilla asks to add Microsoft Defender exclusions, decline to keep the host's
existing protection settings. If Rust was installed during bootstrap, reopen
MozillaBuild before building if Mach prompts you to do so.

```sh
cd c:/mozilla-source/Aelthoren
python3 tools/windows_build.py prepare
python3 tools/windows_build.py bootstrap
python3 tools/windows_build.py build
python3 tools/windows_build.py run --profile w1-smoke
```

The wrapper selects [the Windows mozconfig](../config/mozconfig.windows-x64) for
`mach build`. The executable should be at
`aelthoren-gecko-windows/obj-aelthoren-windows/dist/bin/firefox.exe`. The build
checks that the file has an AMD64 Windows PE header and that the reviewed
distribution files exist beside it. The launcher uses an explicit persistent
profile at `%LOCALAPPDATA%\Aelthoren\Development\Profiles\profile-w1-smoke` and
starts a separate browser instance with the Aelthoren remoting name. The
launcher waits for the browser process to exit. Relaunch with the same profile
name to reuse its data.

Use `--source PATH` before the subcommand to select a different dedicated Firefox
checkout. Prepare checks the pinned HEAD and requires a clean starting tree. It
verifies the generated files and tracked changes on subsequent runs. Keep build
logs and profiles outside both source trees. Reuse the prepared source, build
outputs, and Mach cache for incremental builds.

### Retry bootstrap with an existing overlay

The Windows branding directory and the five patched Firefox files are expected
after `prepare`. Verification checks the recorded file paths and hashes, the
tracked source diff, and the overlay inputs. It lists individual untracked files
so empty directories do not affect the result. Git's standard exclusions apply
to generated output such as the object directory.

If bootstrap previously rejected a prepared overlay, update your Aelthoren
branch and retry from the MozillaBuild shell:

```sh
(
  set -e
  cd d:/mozilla-source/Aelthoren
  git switch w1-windows
  git fetch origin codex/aelthoren-w1-windows
  git merge --ff-only FETCH_HEAD
  python3 tools/windows_build.py prepare
  python3 tools/windows_build.py bootstrap
)
```

Expect `Windows overlay verified` from `prepare`. To inspect a path reported by
the validator, run `git -C ../aelthoren-gecko-windows status --short --untracked-files=all`
from Aelthoren and review the file before retrying.

### Recover from a patch application failure

Git can retain CRLF patch files in an existing worktree even after the
`text eol=lf` rule is in effect. `git ls-files --eol` shows this as
`i/lf w/crlf attr/text eol=lf`. Prepare converts CRLF to LF in temporary copies
and checks the complete patch set before applying it. A failed patch check
leaves the Firefox checkout clean, so it can be reused.

In your MozillaBuild shell, run the following from Aelthoren. Use your actual
drive and local branch name. The commands stop if the branch cannot fast-forward
or if the tracked patch files have staged or unstaged content edits. The archive
command refreshes those files from the current commit even when Git considers
the existing CRLF files up to date.

```sh
(
  set -euo pipefail
  cd d:/mozilla-source/Aelthoren
  git switch w1-windows
  git fetch origin codex/aelthoren-w1-windows
  git merge --ff-only FETCH_HEAD
  git diff --exit-code -- 'patches/*.patch'
  git diff --cached --exit-code -- 'patches/*.patch'
  git archive --format=tar HEAD -- 'patches/*.patch' | tar -xf -
  git ls-files --eol -- 'patches/*.patch'
  python3 tools/windows_build.py prepare
)
```

Expect `i/lf w/lf attr/text eol=lf` for each patch. If an interrupted run left
modifications in the Firefox checkout, review `git status --short` there. To
preserve that checkout and retry with the same locally available source, create
a separate worktree from the pin:

```sh
git -C ../aelthoren-gecko-windows worktree add --detach ../aelthoren-gecko-windows-retry a34c4160e3f75ab9918fbe4669ff7ae56f1977c8
python3 tools/windows_build.py --source ../aelthoren-gecko-windows-retry prepare
```

## Reused frontend and compatibility

- The [existing three frontend patches](../patches/README.md) provide the local
  new-tab and About pages, search submission through Gecko's SearchService, and
  account-settings visibility. The source build installs the [existing policies](../config/privacy-policies.json)
  and [distribution preferences](../config/distribution.ini) through Mozilla's
  build manifest. They set DuckDuckGo as the normal and private default and
  disable the integrated account and Sync flow. Use a test host with no
  conflicting Firefox enterprise policy for the W1 checks.
- The Windows brand uses Mozilla's unofficial template with the Aelthoren name,
  wordmark, and the [owner's SVG](../assets/A_text.svg). The Windows PNGs and
  multi-size ICO are renders of that SVG with the same framing as the Linux
  frontend. The source build uses the checked-in artwork directly, with no image
  tool installation step.
- Gecko's sandbox, TLS certificate handling, and process-isolation configuration
  use upstream defaults. The executable basename and application GUID are
  inherited from Firefox. The final Linux package's resource edits are specific
  to its pinned archives, so some inherited Mozilla labels and secondary
  resources can still appear in this development build.
- W1 targets unsigned, local x64 development builds. Windows installer,
  default-browser integration, independent updates, and ARM64 and x86 builds are
  outside this workflow. Use the result for development and acceptance testing.

## Verification status

The implementation was checked on Linux x86_64. The official release tag
resolved to the locked SHA, the three patches and branding overlay prepared
successfully in a separate pinned checkout, and a repeat prepare verified the
existing overlay. A wrong pin or an unexpected source change stopped preparation.
The pinned Mozilla build readers parsed the mozconfig and resolved the
distribution install paths. The policy JSON passed the pinned schema.

The patch failure was reproduced on Linux against the pinned Firefox source.
All three LF copies passed `git apply --check`. A checkout with
`core.autocrlf=true` and `core.eol=crlf` kept the patches at LF. The recovery
commands refreshed deliberately stale CRLF files in that checkout. Preparation
with the stale files succeeded on the same pinned source after the failed
preflight, and re-running it after refreshing the files verified the same
overlay.

On the pinned Linux checkout, an empty directory reproduced the former overlay
rejection while Git status continued to show only the intended changes. The
updated check verified the existing overlay and rejected an unexpected file.
Regression tests exercise repeated preparation and the validation paths for
bootstrap and build with Mach stubbed. All 21 tooling tests passed.

Git for Windows under MozillaBuild 4.2.1, native Windows bootstrap, compilation,
and Windows runtime checks remain unverified on this Linux host.

## Acceptance on a Windows host

Start with a fresh test profile and keep the build log. Record the Windows
version, Firefox SHA, Aelthoren SHA, and the result of each check.

| Check | How to verify |
| --- | --- |
| Native x64 launch | Run the launcher and confirm the Aelthoren window opens from the x64 executable path it prints. Check the build output and visit `about:support` for the runtime build, sandbox and process information. |
| Local HTML | Press Ctrl+O and open `branding/content/about-aelthoren.html` from the Aelthoren checkout. Confirm the local page renders. |
| JavaScript and DOM | Serve the existing smoke fixture with the loopback command below. At `http://127.0.0.1:8765/`, confirm the page displays `PASS: JavaScript, DOM, and storage`. |
| HTTPS and certificate validation | Open `https://example.com/` and `https://www.mozilla.org/` and confirm Firefox reports a secure connection without an exception. |
| Tabs and product defaults | Open and close a tab. Confirm the Aelthoren new-tab page appears and submits a search to DuckDuckGo. In `about:policies`, check that `DisableAccounts` and the DuckDuckGo defaults are active. Confirm the account category is absent in Settings. |
| Profile persistence | Bookmark the loopback page, exit normally and relaunch with `--profile w1-smoke`. Confirm the bookmark is still present. |
| Clean exit | While the browser is running, record the browser processes under this build's `dist\bin` path. Use the browser menu to exit, wait for the launcher to return, then confirm those processes have exited. |

In a second MozillaBuild shell from the Aelthoren repository, serve the fixture.
The static server returns 404 for the fixture's result callback. The page status
and request for `/result?status=pass` indicate that the checks ran.

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs/smoke
```

In PowerShell, use the built executable's directory to inspect only this
development build's processes. Run the query before and after normal exit.

```powershell
$dist = 'C:\mozilla-source\aelthoren-gecko-windows\obj-aelthoren-windows\dist\bin\'
Get-CimInstance Win32_Process |
  Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith($dist, [StringComparison]::OrdinalIgnoreCase) } |
  Select-Object Name, ProcessId, ParentProcessId, ExecutablePath
```

Phase W1 is complete after a genuine native build and the checks above succeed
on Windows.
