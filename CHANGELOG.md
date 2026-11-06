# Changelog

## Unreleased — Phase 4 measured lightweight optimization

- Published the pre-change desktop baseline before product edits; measured three
  fresh-profile/warm pairs per condition with 1/5/10 distinct loopback-site tabs.
- Avoided five redundant managed-configuration/profile-marker rewrites per launch
  after byte/digest comparison, preserving installation/update/unknown-edit guards.
- Targeted buffered preparation median fell 651.75 → 129.48 µs (-80.1%); overall
  startup/memory/CPU improvements are not established. All measured regressions,
  ranges and environment limits are published in docs/PERFORMANCE.md.
- All 12 desktop measurement sessions exited cleanly. Post-change 25 Phase 3 browser
  checks, 12 tooling tests and a desktop background-tab timer check passed.
- Native Firefox/libxul match the pinned official artifacts byte-for-byte; no
  compiled component, privacy/security policy, logo, process-count or GC change.
- No full engine compilation, Firefox comparison, release or Phase 5 work claimed.

## Unreleased — Phase 3 privacy and search

- Added supported account/Sync, telemetry-upload and studies policies plus editable
  tracking, partitioning and suggestion defaults using distribution configuration.
- Added a minimal local new-tab search form using Mozilla SearchService and the
  user-selected current provider; DuckDuckGo is the one-time initial default.
- Added a privacy settings link and factual About/privacy/security documentation.
- Fixed redesigned Settings account-category visibility to respect the account gate.
- Preserved the official logo, pinned ESR/artifacts, isolated profiles, licenses,
  native browsing functions and security mechanisms. No full engine compilation,
  production update channel or Phase 4 optimization is claimed.
- Added actual browser privacy/search/HTTPS verification and preservation checks;
  exact final results and known upstream/cloud diagnostics are in VALIDATION.md.

## Unreleased — Restart Phase 1

- Reused the exact official Firefox ESR 153.6.0esr source pin and preserved owner logo.
- Added reproducible, hash-verified official artifact acquisition and Linux build/run tools.
- Built genuine Gecko/SpiderMonkey artifact browser frontend and standard artifact target.
- Verified real rendering, JavaScript, DOM and localStorage with screenshot and live callback.
- Included matching common-test artifacts, resolving the prior updater test-binary blocker.
- Kept downloads/binaries/source caches/profiles outside Git; preserved work on the existing
  restart branch and PR rather than relying on cloud snapshots.
- Phase 2 and Phase 3 have not started; local engine source compilation remains unverified.

## Unreleased — Phase 2 branding and interface

- Added generated Linux branding/icons/wordmarks using the actual unchanged owner SVG.
- Added a minimal local new-tab and About page, keeping native toolbar/navigation/tabs.
- Added a runtime Aelthoren launcher with separate named profiles and no-remote isolation.
- Branded configure/install/standard artifact build passed; actual HTTP JS/DOM/storage,
  native history/tab behavior, two profile paths and internal UI screenshots verified.
- Native Firefox GUID and some platform/trademark identity remain inherited; no full
  engine source compilation or public release/update channel is claimed.
- No Phase 3 privacy/account/sync/default-search functionality was implemented.


## Unreleased — Phase 5A Linux alpha packaging

- Official mach packaging succeeded for the verified ESR artifact runtime.
- Added a relocatable non-root portable wrapper, isolated alpha profiles, official
  icon/version About page, optional user-local desktop/URL integration and license/
  source material. Native GUID/version identity remains inherited; development-only.
- Added repeatable archive/checksum generation and clean Debian/Ubuntu QA tooling.
- Final 88,591,204-byte clean-source archive reproduced byte-for-byte; Debian 13
  and Ubuntu 24.04.5 headless/GUI suites passed, plus 17 tooling tests.
- Exact SHA/source provenance, GUI images, sandbox/TLS observations and incomplete
  release/export/identity gates are recorded. No public GitHub Release created.

## Final branding cleanup — 0.1.0-alpha development

- Add an explicit SHA-pinned omni-resource packaging overlay for inherited fox
  artwork, product labels/error text, misleading sponsorship copy and product
  support/legal links. Preserve upstream licenses, attribution and security.
- Preserve the owner logo and original verified archive; inventory packaged files,
  images and brand-bearing resource references, with GUI-specific audit checks.
- Keep inherited native identity and public-distribution/legal/update blockers
  explicit. No public release, automatic merge or repository archival.
