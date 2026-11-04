# Patch ledger

Base: upstream.lock.json, Firefox ESR 153.6.0esr,
a34c4160e3f75ab9918fbe4669ff7ae56f1977c8.

0001-phase2-ui.patch changes only:

- browser/components/newtab/AboutNewTabRedirector.sys.mjs: use the bundled local
  Aelthoren new-tab resource and avoid waiting for an Activity Stream renderer for
  this specific static page. Native URI flags, loadInfo and process guards retained.
- browser/locales/en-US/browser/aboutDialog.ftl: independent-project attribution
  and an honest development/update/distribution notice replacing the donation prompt.

The generated branding directory is separate from upstream tracked files. The
preparation tool checks the exact source revision/clean baseline before first
application and hashes all expected patched/overlay files for subsequent runs.
Unknown modifications stop the tool; nothing is silently overwritten or reset.

Security impact: local script-free page with restrictive CSP; no new privileged
interfaces for websites, native security bypasses or Phase 3 preference changes.
Validate about:newtab routing, branding pages, HTTP JS/DOM/storage, profile isolation
and navigation/tab behavior on every rebase. On an upstream update, review/rebase
the small diff and regenerate the derived branding template against the new pin.
Preserve MPL notices and upstream attribution. No engine patch is included.
