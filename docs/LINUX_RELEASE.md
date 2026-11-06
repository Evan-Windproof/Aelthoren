# Linux 0.1.0-alpha packaging

**Development-only internal test artifact. No public GitHub Release or download URL
has been published.** Product version 0.1.0-alpha is the portable package/wrapper
version; the native application/engine version remains 153.6.0. This is not a fully
independent, signed or automatically supported Aelthoren release. Development-only
is a readiness/support classification, not an amendment to MPL or other licenses.

## Build and package

Use the verified Firefox ESR 153.6.0esr source revision
`a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`, the three pinned official artifact
archives and the existing reviewed branding/privacy overlay. Do not redownload
valid inputs or use unknown precompiled runtimes. Building an engine from C++/Rust
has not been completed; the workflow uses official genuine Gecko/SpiderMonkey.

```sh
python3 tools/phase3.py prepare
python3 tools/phase3.py build
python3 tools/package_linux.py
```

The packager checks the source/branding guard and all three archive sizes/SHA-256,
runs Mozilla's official `./mach package`, and wraps its complete runtime. It does
not assemble a browser by guessing DLLs or merely renaming a Firefox binary.
For a repeated wrapper build, `--mozilla-package PATH` reuses the exact local
package just produced by mach for this verified overlay. Native Firefox/libxul
bytes must match the verified build. Do not supply arbitrary external packages.

Default output is outside Git:
`/workspace/aelthoren-packaging/output/aelthoren-0.1.0-alpha-linux-x86_64.tar.xz`,
with a sibling `.sha256` and `package-result.json`. Existing archives/partials are
refused. A clean project commit is required for the final verified artifact's
source availability; dirty working-tree prototypes are explicitly marked as such.
The wrapper tar uses sorted paths, fixed owner/modes and a source-commit timestamp;
reproducibility is assessed against identical clean source and Mozilla-package
inputs. This is not a claim of reproducible full engine compilation from scratch.

## Obtain, verify, extract, launch

There is currently no official public binary download. Obtain the operator's
verified internal artifact plus its exact checksum through an approved export, or
build it yourself. Never use a fabricated releases/latest URL or an unrelated
Firefox archive under this filename. Once those files actually exist locally:

```sh
sha256sum -c aelthoren-0.1.0-alpha-linux-x86_64.tar.xz.sha256
tar -xJf aelthoren-0.1.0-alpha-linux-x86_64.tar.xz
cd aelthoren-0.1.0-alpha
sha256sum -c MANIFEST.sha256
./aelthoren
./aelthoren --about
./aelthoren --version
./aelthoren --profile second
./aelthoren -- --private-window
```

No root or system installation is required. Launching needs only the bundled
runtime, ordinary POSIX shell utilities and the documented system shared libraries;
no Firefox source tree, Git, compiler, Python or Codex-specific modules. Run the
wrapper, not runtime/firefox. Extraction paths with spaces are supported. The
prototype ran from a read-only application bind mount; final tests independently
extract into user-owned temporary directories. The input archive remains read-only
and profiles/cache are external.

## Identity and desktop integration

The package supplies Aelthoren's official icon, product/version metadata, local
alpha About page, supported Name/Vendor/RemotingName/Profile overrides and explicit
`--no-remote` isolation. Automatic profile migration is disabled in packaged app
configuration. Default profile storage is
`${XDG_DATA_HOME:-$HOME/.local/share}/aelthoren-alpha/profiles/default`;
`--profile NAME` selects another marked profile using simple ASCII names only.
Nonempty unmarked data and symlinked managed profile paths are refused. Existing
Firefox profiles are not adopted or modified. Do not infer complete native identity
from the separate data/desktop names: native GUID, native version, executable
basename and some updater/crash/metadata identity remain inherited.

Optional per-user integration requires system Python 3, only for this helper:

```sh
python3 desktop-entry.py print
python3 desktop-entry.py install
python3 desktop-entry.py remove
```

It generates `org.aelthoren.Browser.Alpha.desktop` under the user's
XDG_DATA_HOME/applications, with Network/WebBrowser categories, the official icon
and HTTP/HTTPS/HTML MIME declarations. The Exec line uses standard `/bin/sh` with
the absolute script path as an argument, never shell `-c`; URL arguments are not
evaluated. Desktop escaping/URI forwarding is tested, including unusual extraction
paths. No system-wide file or default-browser setting is automatically changed.
Conservative `--no-remote` also means URL forwarding into an already-running
alpha profile is not implemented; a second launch can report a profile lock. Do
not make this test artifact a system default browser. Independent native remoting/
URL integration is a release gate. Moving the extraction directory requires
rerunning install to update absolute paths; unknown owner desktop files are preserved. Actual GNOME/KDE menu/default-
browser/Wayland registration has not been comprehensively tested.

## Runtime dependencies and compatibility scope

The package bundles Mozilla runtime/resources and NSS/NSPR dependencies supplied
by the official packager; it does not bundle a complete Linux operating system.
The observed packaged ELF symbol floor is **GLIBC_2.34** across all included ELF
files (the main engine alone has a lower floor). Require compatible x86_64 glibc,
libstdc++/libgcc, GTK 3, GLib/GIO, X11 or Wayland libraries, fontconfig/FreeType/fonts,
ALSA and their normal transitive dependencies. Headless execution still needs
native libraries. `RUNTIME-DEPENDENCIES.txt` lists actual DT_NEEDED names/symbols.
The QA Dockerfile documents the official Debian/Ubuntu package dependency sets;
install missing OS libraries normally through trusted distribution repositories.
The application never installs them automatically. A symbol floor is not a promise
of compatibility with every older distribution.

The final archive passed clean Debian 13 and Ubuntu 24.04.5 LTS containers in both
headless and actual X11 GUI modes as UID 1000: 16 checks per headless case, 17 per
GUI case. Each case independently extracted the tarball and verified its internal
manifest. Source tree/Codex modules were absent. These are containers sharing the
managed host kernel, not full physical-desktop or every-distribution certification. Containers are not complete physical desktop installations.

## Security, licensing and release blockers

The archive retains Mozilla/third-party license material in runtime about:license
and licenses/, Aelthoren's independent-code MIT notice, owner-asset caveats, exact
source availability instructions and MPL-covered patches. Do not relicense Mozilla
covered code as MIT or noncommercial. The author's logo and Mozilla's marks have
separate rights; no permission to redistribute protected Firefox marks is implied.
See RELEASE_CHECKLIST.md for the unresolved public-distribution gates.

The official Mozilla version metadata and ESR advisory index were fetched over
verified HTTPS on 2026-11-05 UTC (2026-11-06 Asia/Taipei). They list 153.6.0esr as
current ESR and MFSA 2026-120 as the 153.6 fixes. This is a point-in-time vendor
snapshot, not an exhaustive vulnerability audit or future security guarantee.
A new release was scheduled for 2026-11-06 in that metadata; recheck before any
external distribution. No vulnerable/unsupported pin should be described as safe.
Independent update delivery/signing is not established; inherited update errors
and remote-service diagnostics remain. Do not use this alpha for general or
sensitive browsing. No TLS bypass, sandbox reduction or root execution is used.

## Remove

Exit every alpha instance. If installed, run `python3 desktop-entry.py remove`,
then delete only the extracted application directory. Profile data is retained.
Back up wanted bookmarks/data, then manually delete only your `aelthoren-alpha`
data directory if you also want to remove its profiles. Never delete `.mozilla`
or other browsers' data. The helper removes only its own desktop entry.

## Artifact/export status

The final verified archive is:

`/workspace/aelthoren-packaging/output/aelthoren-0.1.0-alpha-linux-x86_64.tar.xz`

- Size: **88,591,204 bytes** (about 84.5 MiB).
- SHA-256: `b40b5a7538e0d62769917e3f439907027476ad43a0d5f23f1933ea4c81440495`.
- Source commit used for packaging: `4e59ba872ff7cfe059f617f98f28869ebf33e71f` (clean and published before packaging).
- An identical-input second build under `/workspace/aelthoren-packaging/repro` has the exact same size/hash. No reproducible full-engine-build claim is made.
- Final verification QA fixes/evidence are preserved in the same Phase 5 branch; they do not change packaged runtime inputs from that source commit.

The tool inventory exposes incoming file download but no artifact upload/export
endpoint. This archive exists in the workspace; external/client file retrieval was
not verified and no public download/release asset was published. Do not advertise
local availability as a public downloadable release. Checksums/metadata and the
repeatable workflow are preserved in Git, not the large archive.

## Actual verification and observed limits

See `docs/phase5/compatibility-results.json`, `final-package.json`,
`reproducibility.json`, `identity-audit.json` and `security-review.json`. GUI images:
[Debian](phase5/debian13-gui.png), [Ubuntu](phase5/ubuntu2404-gui.png).
Public HTTPS images are recorded separately. Source availability, clean extraction,
public HTTPS (through configured proxy plus test-profile CA trust), rejected
untrusted TLS, JS/DOM/local storage, native tabs/navigation, search selection and
restart, account/Sync gates, classifier blocking, private browsing and second-profile
isolation all passed. 17 tooling tests passed. The active web document adds its
own seccomp filter above the container/browser parent and sets NoNewPrivs; sandbox
level 6, Fission and Safe Browsing settings remain enabled. Outer runtime denies
some user-namespace creation; no exploit or complete namespace audit is claimed.

Both GUI cases report headless=false and native browser chrome was visually
inspected. Test-only remote automation indicators can appear in the screenshots;
normal launcher invocation does not enable automation/system-access flags. The
alpha About page's product version and loaded official icon were checked. Native
GUID/version/executable identity remains inherited as recorded in identity-audit.

The generic inherited Settings status can say “latest, safest version” based on
upstream UI state. It is **not evidence of a supported/safely updated independent
Aelthoren release** and must be corrected/reviewed before public distribution.
Other upstream services/diagnostics and lack of a supported update channel remain.
Minimal test images have limited fonts (including missing CJK glyphs on the public
sample page); install suitable OS fonts for full script coverage. Wayland, real
GNOME/KDE/default-browser behavior, accessibility and exhaustive site/security
compatibility remain unverified. These limits keep the package development-only.


## Exact validation commands

```sh
python3 tools/test_linux_containers.py /workspace/aelthoren-packaging/output/aelthoren-0.1.0-alpha-linux-x86_64.tar.xz --output /workspace/aelthoren-packaging/final-headless-verified
```

GUI QA needs an unused local :97 display. Do not replace the authority of a display
that is already running. In a separate shell, before the GUI command:

```sh
mkdir -p /workspace/aelthoren-packaging
python3 - <<'PY'
import secrets, subprocess
subprocess.run(['xauth', '-f', '/workspace/aelthoren-packaging/Xauthority',
                'add', ':97', '.', secrets.token_hex(16)], check=True)
PY
/usr/lib/xorg/Xorg :97 -config /workspace/Aelthoren/config/xorg-benchmark.conf \
  -logfile /workspace/aelthoren-packaging/Xorg.log \
  -auth /workspace/aelthoren-packaging/Xauthority \
  -nolisten tcp -noreset -novtswitch -seat aelthoren-package-test
```

```sh
python3 tools/test_linux_containers.py /workspace/aelthoren-packaging/output/aelthoren-0.1.0-alpha-linux-x86_64.tar.xz --gui --output /workspace/aelthoren-packaging/final-gui-verified
```

Use `--build-images` if the two QA images are absent. Base OCI digests/image IDs
are recorded in compatibility-results.json. The QA Dockerfile installs only
signed official distribution packages; Python/certutil/OpenSSL are QA tools, not
portable app dependencies. Current cloud QA requires its provided CODEX_PROXY_CERT
as a read-only test mount; ordinary portable execution has no such Codex dependency.
The client Xauthority file uses the existing server cookie with hostname-wildcard
matching for container clients; no access control is disabled. Stage directories
refuse overwrite. Raw output and test profiles remain outside Git.

To reproduce the recorded archive bytes, use a separate clean checkout of source
commit 4e59ba872ff7cfe059f617f98f28869ebf33e71f and the exact Mozilla package input
SHA recorded in final-package.json. Do not reset an active checkout. A different
project commit changes provenance/date metadata and therefore changes the hash.
Two runs with identical inputs/tools matched; cross-toolchain/full-engine-build
reproducibility is not established. Sources/recipes are preserved on GitHub; the
large local archive itself has no independent exported backup in this session.
Export it through an available client/workspace mechanism before discarding the
workspace if that exact binary is needed.
