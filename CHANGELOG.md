# Changelog

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
