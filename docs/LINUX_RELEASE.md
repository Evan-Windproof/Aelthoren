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
bundle is read-only at runtime in the clean tests; profiles/cache stay external.

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

The initial prototype passed 16 checks in clean Debian 13. Final clean-source
artifact, byte-for-byte repackaging comparison, Ubuntu 24.04 and actual desktop GUI
results are recorded after verification below; untested distributions are not
supported by inference. Containers are not complete physical desktop installations.

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

Final path, size, SHA-256, source commit and test results are added after the
clean-source build. No external artifact upload/export endpoint or public release
is assumed. Local workspace availability must not be advertised as an available
public download.
