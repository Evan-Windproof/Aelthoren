# Linux Gecko artifact development

## Current Phase 3 workflow

Use the existing verified source/artifacts and prerequisites below. Do not reacquire
valid archives or reset the existing overlay. For a pristine pinned source, the
preparation command generates branding and applies the three reviewed frontend
patches. For an unchanged, marked Phase 2 overlay, it verifies every existing file
against its marker before applying the Phase 3 patches/content. Unknown source,
branding or distribution edits stop preparation/launch for review.

```sh
cd /workspace/Aelthoren
python3 tools/phase3.py prepare
python3 tools/phase3.py build
python3 tools/run_aelthoren.py --profile default
python3 -m unittest discover -s tools -p 'test_*.py'
python3 -u tools/verify_phase3.py
```

`phase3.py build` runs the official `./mach --no-interactive configure`,
`./mach artifact install` and `./mach build`, using the pinned local archives and
config/mozconfig.linux-aelthoren. Outputs go to docs/phase3; compiled files stay in
/workspace/aelthoren-gecko/obj-aelthoren-phase2. It then installs reviewed policies
and distribution defaults beside the binary, not into user prefs.js. The launcher
reinstalls/verifies these files on each launch and refuses unmanaged modifications.
A source-head mismatch or archive size/SHA-256 mismatch stops the build. This is an
artifact frontend build, not local Gecko/SpiderMonkey C++/Rust compilation.

Runtime verification needs Python, OpenSSL and the matching Mozilla certutil
(already present from the pinned common-test artifact), free loopback ports 8765,
8443, 8444 and Marionette 2828. Run it only when another browser/test is not using
these ports. It creates unique disposable profiles outside Git. A local fixture
CA is trusted only in that test profile; keys remain in a temporary directory
outside Git. It does not import the cloud interception CA or disable TLS errors.
The negative certificate test must fail normally.

The script alone passes `--remote-allow-system-access` for privileged verification
and sets `remote.prefs.recommended=false` only in its test profiles, preventing
Marionette from overriding real privacy/security defaults. Normal launches do
neither. Test-only classifier data comes from the pinned Mozilla source helper;
DNS mappings and narrow proxy exclusions send synthetic fixture hosts to loopback,
not to remote blocked hosts. Existing remote proxy/TLS settings remain intact.
Profiles are retained outside Git for inspection and must not be used for normal
browsing because they contain fixture trust/configuration. Runtime reports and
screenshots are in docs/phase3; preserve prior evidence before rerunning.

No new build toolchain downloads or full engine compilation are needed for this
phase. Full source compilation remains the long-term engine verification target;
see official Mozilla bootstrap/build documentation below. Windows remains a
separate future native distribution target. Phase 3 changes are published on
codex/aelthoren-phase3 in a new PR targeting main; do not merge automatically.

## Historical Phase 1 workflow

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
See PRIVACY.md for the Phase 3 audit and retained services. Do not use this development build for sensitive
browsing or distribute it as a supported Aelthoren release.

Windows is a future separate target using official native MozillaBuild tooling:
https://firefox-source-docs.mozilla.org/setup/windows_build.html . A Linux artifact
run does not validate Windows. No Windows build/installer, independent branding or
full engine source build is claimed here.

Before any environment switch/publication, commit and run tools/preserve_milestone.sh;
verify remote SHA and create/update the applicable milestone PR. Local caches/snapshots are disposable.


## Phase 2 branded frontend

The Phase 1 build remains preserved, but its strict clean-source guard intentionally
rejects the reviewed Phase 2 frontend patch. Use tools/phase2.py and the separate
config/mozconfig.linux-aelthoren for current branded work. See docs/BRANDING.md.
Do not reset upstream work to satisfy the old guard. The pinned HEAD is unchanged;
only the explicit patch/derived branding directory differ. All archives remain
outside Git and no additional environment, source tree or PR is created.


## Phase 5A portable Linux alpha

After the verified artifact build, run `python3 tools/package_linux.py`. It invokes
Mozilla's official `./mach package` and wraps that runtime, preserving the engine
version/GUID while providing supported Aelthoren name/profile/remoting overrides.
Outputs stay outside Git. `--mozilla-package PATH` can reuse the exact current
local mach output; existing outputs are refused. The app launches through its
packaged POSIX shell wrapper with no development source/modules. Optional desktop
integration uses Python 3, separately from runtime requirements. See
docs/LINUX_RELEASE.md for exact extraction, dependencies, checksums and limitations.
Clean-distro QA uses `tools/test_linux_containers.py ARCHIVE --build-images`; this
is test infrastructure, not a runtime requirement. Do not publish a GitHub Release.

Final Phase 5A archive was built from clean published source commit
4e59ba872ff7cfe059f617f98f28869ebf33e71f. Repeating with that source and the exact
same Mozilla package input produced identical bytes. Packaging requires a clean
project; `--allow-dirty-prototype` is only an explicitly marked internal experiment.
For GUI QA, start the authenticated Xorg display described in the Linux release
notes/Phase 4 protocol with authority under /workspace/aelthoren-packaging; use
`tools/test_linux_containers.py ARCHIVE --gui --output EXTERNAL_DIRECTORY`.
The QA tool makes a hostname-compatible client authority file without disabling
X access control. Never use --privileged, sandbox-disable flags or TLS bypasses.
Final QA fixes are in the current branch; source/runtime packaging inputs remain
those of the clean archive source commit. See docs/phase5 for exact results.


The development-only [GitHub Actions export workflow](docs/ACTIONS_EXPORT.md)
builds with the existing scripts, verifies standalone execution and uploads an
expiring workflow artifact instead of a public Release. Use actual successful run
links/results; an unrun or failed workflow does not supply a downloadable package.
