# Linux alpha and future release checklist

This is a readiness checklist, not a replacement for MPL/third-party licenses.
Development-only classification does not impose a noncommercial source license.

## Internal test package

- [x] Reuse exact pinned genuine Gecko/SpiderMonkey artifacts and reviewed source overlay.
- [x] Official `mach package` produced the runtime successfully.
- [x] Portable shell wrapper, explicit profile separation and own alpha metadata/icon.
- [x] Optional user-local desktop template/generator; no automatic default/system changes.
- [x] Prototype clean Debian launch/HTTP/HTTPS/JS/storage/privacy checks, without source/Codex modules.
- [x] Preserve available upstream license materials, independent code notice and source/patch instructions.
- [x] Final package built from a clean published source commit.
- [x] Exact artifact size/SHA and internal manifest checked after extraction.
- [x] Identical-input wrapper packaging reproduced byte-for-byte.
- [x] Final Debian 13 and Ubuntu 24.04 headless checks.
- [x] Actual desktop GUI rendering/branding check, separately identified from headless.
- [x] Review/commit/push final evidence and verify remote branch SHA/PR at Phase 5A completion.

## Public release gates — intentionally not complete

- [ ] Establish independent native application GUID/version/executable/desktop/Wayland identity using an appropriate supported full-build workflow; do not treat renaming as independence.
- [ ] Recheck current Mozilla ESR advisories/security support and update the pin if necessary; a past snapshot is insufficient.
- [ ] Correct/audit inherited generic “latest/safest version” status copy so it cannot imply a validated independent alpha update channel.
- [ ] Independent signing, trusted artifact provenance and a tested security-update/replacement delivery process.
- [ ] Complete Mozilla trademark/branding and official owner-asset redistribution rights review.
- [ ] Complete all applicable Mozilla/dependency license/copyright/source-availability obligations, including corresponding source for the exact distributed binary.
- [ ] Dedicated-host and real-user distro/desktop interoperability, MIME/default-browser behavior, accessibility and longer stability/security validation.
- [ ] Explicit owner authorization for publishing actual downloadable release assets.

No public GitHub Release, installer or supported general-browsing product is created
by Phase 5A. Keep incomplete gates visible; do not silently waive them or disable
security mechanisms to make a package pass tests.
