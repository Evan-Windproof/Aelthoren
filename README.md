# Aelthoren

**Lightweight. Private. Account-free.**

Aelthoren is a planned independent desktop browser based on genuine Mozilla
Firefox, Gecko and SpiderMonkey. Development starts on Linux; Windows support is
planned. C++ is the primary long-term language alongside required upstream Rust,
JavaScript and other languages. The owner's official logo is preserved unchanged
in assets/A_text.svg.

Phase 3 adds DuckDuckGo as the changeable initial search provider, a new-tab
search form using the same provider, disabled browser Accounts/Sync and telemetry
uploads, and practical tracking/partitioning defaults. The official Phase 2 logo,
branding, local About page and isolated launcher are preserved. Native Gecko
address bar, tabs, navigation, passwords, bookmarks/history and privacy controls
remain available. See [PRIVACY.md](PRIVACY.md) for the exact behavior and retained
remote services, and [SECURITY.md](SECURITY.md) for security limits.

```sh
python3 tools/phase3.py prepare
python3 tools/phase3.py build
python3 tools/run_aelthoren.py
```

See [BUILDING.md](BUILDING.md) for prerequisites, existing-overlay upgrades and
verification commands. This uses Mozilla's precompiled genuine Gecko/SpiderMonkey;
it is not a locally compiled engine or a simulated browser. The source remains
pinned to Firefox ESR 153.6.0esr at
`a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`. Linux is verified; Windows and
complete independent native identity/signing/update infrastructure remain future
work. Native Firefox GUID and some platform identity remain inherited; use the
launcher rather than the raw binary. [Branding limits](docs/BRANDING.md) apply.

[VALIDATION.md](VALIDATION.md) records actual artifact builds, browser tests and
known failures. The privacy slogan is not an anonymity or performance guarantee.
Security protections are retained, but production security-service reachability,
updates and exhaustive network/security testing remain unverified. This is a
development build, not a supported release for sensitive browsing.

Phase 4 records repeated desktop performance measurements and avoids five
redundant configuration/profile writes when installed bytes already match. The improvement
is limited to launcher I/O; no general startup or memory advantage is claimed.
See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for before/after data, variation and
regressions. Phase 5A provides a development-only Linux alpha package; no public release is available. Completed milestones are committed/pushed
and remote SHAs verified; cloud snapshots are not treated as backups.

Aelthoren is independent of Mozilla and is not endorsed by Mozilla. Keep upstream
copyright/license notices and do not redistribute modified builds under protected
Firefox branding. This is a development baseline, not a supported release.
See LICENSE, THIRD_PARTY_NOTICES.md and UPSTREAM.md.

Phase 5A adds an internal Linux 0.1.0-alpha portable packaging workflow. The
verified archive runs in clean Debian 13/Ubuntu 24.04 containers without a source
tree/Codex modules; native identity, signing,
updates and release compliance are incomplete, so no public release is claimed.
See [Linux packaging](docs/LINUX_RELEASE.md) and the
[release checklist](docs/RELEASE_CHECKLIST.md) for launch/dependency instructions
and actual validation status.

The Linux alpha archive is 88,591,204 bytes, with SHA-256 and exact local path in
[LINUX_RELEASE.md](docs/LINUX_RELEASE.md). Four clean container cases (Debian/Ubuntu,
headless/GUI), extraction manifests and identical-input packaging passed. This is
a workspace artifact, not a published download; no general-browsing safety or
fully independent native release is claimed.

### Final branding audit

The [final branding audit](docs/BRANDING_AUDIT.md) documents an explicit,
hash-checked packaging resource overlay and real GUI verification. Native Firefox
executable/GUID/update identity and legal/source/asset-rights gates remain public
binary distribution blockers. This is an internal development concept, not a
Mozilla-endorsed or production-ready release. No Release or archival is authorized
by passing tests; review the [release checklist](docs/RELEASE_CHECKLIST.md).
