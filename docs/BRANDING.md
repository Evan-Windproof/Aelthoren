# Phase 2 — Linux artifact branding and initial interface

Aelthoren uses genuine Firefox ESR 153.6.0esr / Gecko / SpiderMonkey at
`a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`. The verified Phase 1 local browser,
XPT and common-test archives are reused. No engine source or security flags change.

## Build and launch

```sh
cd /workspace/Aelthoren
python3 tools/phase2.py prepare
python3 tools/phase2.py build
python3 tools/run_aelthoren.py
# Separate named profile:
python3 tools/run_aelthoren.py --profile development
```

The generator requires the installed Inkscape CLI. It copies the pinned unofficial
branding template into `browser/branding/aelthoren`, generates Linux icons and
wordmarks from the real owner logo, and applies `patches/0001-phase2-ui.patch`.
The original SVG is unchanged. An integration copy adjusts its viewBox/dimensions
because negative-coordinate artwork was clipped by the original viewport; no paths,
colors or shapes were redesigned. The generated brand's MPL notices are preserved.
Content/provenance hashes detect any modified overlay and stop rather than overwrite
it. Re-running prepare on the current overlay verified it unchanged.

Only two tracked upstream frontend files are patched: the new-tab redirector and
two About-dialog attribution strings. The new-tab default URL points to a locally
registered resource with strict CSP, no scripts, fonts, ads or external page assets.
The local page does not wait for the unused Activity Stream renderer's startup
barrier. URI security flags, loadInfo and process/sandbox checks remain unchanged.
The underlying new-tab addon/background services are not globally disabled or audited.

The object directory is `obj-aelthoren-phase2`; earlier Phase 1 objects remain.
Configure, artifact install and standard `mach build` all passed. This builds frontend
resources around precompiled Mozilla Gecko; it does not compile the engine locally.
The Phase 1 tool intentionally rejects tracked source modifications; after applying
the Phase 2 overlay use phase2.py. Do not reset the source to run old commands.

The launcher uses supported `-app` metadata to set runtime Name/Vendor Aelthoren,
RemotingName aelthoren and Profile aelthoren. It preserves the native Firefox GUID
and engine version requirements. Always use the launcher: the raw binary still has
inherited native identity and does not enforce Aelthoren profile paths.

## Interface and storage

- Native Firefox toolbar, address bar, back/forward/reload and tab controls retained.
- Script-free Aelthoren new tab with logo, slogan and local Bookmarks/Settings/About links.
- A local branded About page with Mozilla attribution, licensing links and honest
  development/Phase 3 disclaimers; this is a browser content page, not a fake browser UI.
- Aelthoren names and icon in supported Settings/About-branding resources.
- Dedicated storage: `/workspace/aelthoren-user-data/profiles/<name>`.

Names cannot be arbitrary filesystem paths. The launcher rejects profile/app
passthrough overrides, refuses nonempty unmarked user profiles and always uses
--no-remote. No personal Firefox profile data is imported. Default-browser/desktop
registration is not performed, and the default profile is separate from test profiles.

## Actual verification

```sh
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/verify_phase2.py
```

Nine tooling tests passed. The browser harness used two named profiles and Mozilla's
temporary loopback-only Marionette interface for HTTP tests. Both sessions exited 0;
capabilities confirmed the exact profile paths and `acceptInsecureCerts=false`.
Real rendering/JavaScript/DOM/localStorage, back/forward history and native tab
creation/switch/close passed. No test uses acceptInsecureCerts=true or privileged
system-access automation. The listener is enabled only by the test command, not the
normal launcher. The fixture server and browsers are stopped after testing.

Internal UI was captured through normal headless command-line launches, preserving
Mozilla's internal-page automation restrictions. about:newtab, the packaged About
page and Settings all exited 0; their actual screenshots were visually inspected.
Use a fresh output location/preserve prior screenshots before repeating the harness.
See phase2/runtime-results.json, internal-pages.json and VALIDATION.md for exact
commands, initial failures/fixes, logs and scope. Browser resources and API behavior,
not a mocked UI or substitute engine, are tested.

## Artifact/native identity and distribution limits

The executable basename, application GUID, user agent and some OS/native identifiers
remain Firefox-derived. A fully independent compiled identity and complete OS
integration remain full source-build/platform-validation work; they are not claimed
from an application.ini override. Concurrent desktop Firefox interoperability,
default-browser registration, extension ecosystem behavior, comprehensive security
and HTTPS browser tests remain unverified beyond explicit profile/no-remote isolation.

Mozilla illustrations, Firefox Labs/More from Mozilla and some inherited service/legal
links remain visible. Account/sync and privacy defaults are deliberately unchanged:
Phase 3 has not started. The slogan states goals, not verified privacy/performance
or anonymity claims. Inherited update mechanisms are not a signed Aelthoren release
channel. Do not redistribute this development package as a supported browser or
under protected Firefox trademarks without appropriate permission. Keep Mozilla
attribution/MPL/source-availability obligations, and define the owner asset's public
distribution license before release. Windows/macOS template assets are not validated.
