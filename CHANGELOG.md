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
