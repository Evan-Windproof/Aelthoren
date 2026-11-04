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


## Phase 3 application changes

0002-phase3-search.patch changes only browser/actors/AboutNewTabChild.sys.mjs and
AboutNewTabParent.sys.mjs. The child binds the static local form through the
existing actor. The parent checks the current top-level about:newtab/about:home
URI, bounds/validates a textual query, obtains the current normal/private engine
through this revision's SearchService module and navigates using its HTTP(S)
submission URI/POST data. Provider URLs are not hardcoded; arbitrary website URLs
or commands are not accepted. The local page remains script-free with strict CSP.
Native URI flags/process guards and other actors are unchanged.

0003-phase3-account-settings.patch adds two account-enabled checks in
browser/components/preferences/preferences.js. The redesigned Settings otherwise
shows its Account & Sync category even when DisableAccounts is active. The patch
hides that navigation category in both settings layouts; the supported policy
remains the actual functional account/Sync gate. Local browser data functionality
is retained. No core engine/security/network code is modified.

config/privacy-policies.json and config/distribution.ini use supported upstream
configuration loaders. Ordinary defaults remain unlocked; account/upload/study
gates intentionally use supported product policies. phase3.py can upgrade a verified
unchanged Phase 2 overlay or prepare a clean pinned tree. Unknown edits are refused.
Review actor API/signatures, settings navigation, policy schema/allowed preferences
and user-choice persistence on each upstream rebase. Run actual privacy/search/TLS
checks and keep PRIVACY.md's service audit current. Full native release identity
still requires separate full-build work, not additional engine patches here.
