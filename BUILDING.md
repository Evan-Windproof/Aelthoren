# Phase 1 Linux Gecko artifact workflow

## Prerequisites and paths

Official Mozilla instructions:
https://firefox-source-docs.mozilla.org/setup/linux_build.html and
https://firefox-source-docs.mozilla.org/contributing/build/artifact_builds.html .

Use the existing /workspace/Aelthoren checkout. No worktree is required.
This run has Debian 13 x86_64, 4 CPU quota, 32 GiB RAM and initially about 60 GiB
free. Python 3.12, Git, make, Node 24.22.1 and Python zstandard are available.
Node satisfies the pinned source's own version check. Missing packages on other
hosts should be installed from trusted distro/Mozilla sources using supported
bootstrap; never disable requirements to turn a failing build into a pass.

Persistent paths outside the project repository:

- Source: /workspace/aelthoren-gecko
- Verified input/cache: /workspace/aelthoren-downloads
- Mozilla Python/build state: /workspace/aelthoren-tools/mozbuild
- Object directory: /workspace/aelthoren-gecko/obj-aelthoren-restart
- Disposable development profile: /workspace/aelthoren-phase1-profile

Official source is pinned in upstream.lock.json. Existing source is reused;
a missing source directory is acquired from Mozilla's official Git repository
with a shallow fetch of the exact SHA. A different existing HEAD stops preparation
without resetting or replacing it. Dependency archives never enter Git.

## Prepare and build

```sh
cd /workspace/Aelthoren
python3 tools/prepare_phase1.py
python3 tools/browser.py build
```

Preparation fetches the exact official browser/XPT/common-test archives over HTTPS,
checks byte sizes and pinned SHA-256, and confirms the supplied digests match the
exact task's official chain-of-trust record. This is TLS/checksum provenance, not
an independent Taskcluster signing-key verification claim. Existing valid archives
are reused. A failed checksum stops execution; do not alter expected hashes.

The build tool validates inputs again, preserves inherited proxy/CA settings,
selects the installed Node explicitly, and sets workspace-local Mozilla state.
It passes MOZ_ARTIFACT_FILE as a Linux ':'-separated list of the three verified
archives, and unsets competing remote artifact revision/URL/task overrides.
The artifact mozconfig disables automatic toolchain acquisition, not integrity,
TLS, sandboxing or other browser security mechanisms. No browser security override
or precompiled engine replacement is used.

Actual commands from the source directory are:

```sh
./mach --no-interactive configure
./mach artifact install
./mach build faster
```

`mach build faster` is Mozilla's supported frontend target. Artifact mode reuses
Mozilla's precompiled Gecko/SpiderMonkey; it does not compile those engines locally.
The optional `python3 tools/browser.py full-target` runs standard mach build and
records that distinct result. Do not conflate either command with full engine
source compilation. Full source builds remain a future verification target.

## Run and verify real rendering

```sh
python3 tools/browser.py run
python3 tools/browser.py smoke
```

Run opens the actual development browser with a fresh explicit profile; there is
no Aelthoren branding or account/privacy customization in Phase 1. A cloud display
is needed for interactive run. The smoke command uses headless Firefox and a
localhost-only HTTP server serving docs/smoke, captures a PNG and requires an
actual successful callback from JS after DOM and localStorage write/read/delete
checks. A screenshot alone or a zero-test exit is insufficient; inspect the actual
PNG and JSON result. Existing screenshots are preserved rather than overwritten.

In Codex Cloud, network/socket commands need approved execution outside the command
sandbox. Keep the configured HTTP(S) proxy and CA trust; do not bypass denied hosts
or disable TLS/browser sandboxing. The rendering server and browser shut down after
the smoke test. Tooling tests: python3 -m unittest discover -s tools -p 'test_*.py'.

## Security, limitations and future platforms

Keep all upstream security, license and attribution material. No settings for TLS,
process isolation, sandboxing or exploit mitigations are changed. A local HTTP smoke
pass does not prove HTTPS, all sandbox modes, website compatibility or upstream
suite readiness. The browser can still attempt inherited remote-service calls;
Phase 3 will audit those explicitly. Do not use this development build for sensitive
browsing or distribute it as a supported Aelthoren release.

Windows is a future separate target using official native MozillaBuild tooling:
https://firefox-source-docs.mozilla.org/setup/windows_build.html . A Linux artifact
run does not validate Windows. No Windows build/installer, independent branding or
full engine source build is claimed here.

Before any environment switch/publication, commit and run tools/preserve_milestone.sh;
verify remote SHA and update existing PR #1. Local caches/snapshots are disposable.


## Phase 2 branded frontend

The Phase 1 build remains preserved, but its strict clean-source guard intentionally
rejects the reviewed Phase 2 frontend patch. Use tools/phase2.py and the separate
config/mozconfig.linux-aelthoren for current branded work. See docs/BRANDING.md.
Do not reset upstream work to satisfy the old guard. The pinned HEAD is unchanged;
only the explicit patch/derived branding directory differ. All archives remain
outside Git and no additional environment, source tree or PR is created.
