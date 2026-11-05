# Privacy and search

Aelthoren uses Firefox ESR's genuine Gecko/SpiderMonkey and mature local profile,
password, bookmark, history, private-window and site-data implementations. This is
an independently modified **development artifact build**, not an anonymity tool or
a supported, independently updated browser release. The slogan describes product
priorities; it is not a performance, anonymity or absolute protection guarantee.

## Defaults and user control

- DuckDuckGo is the initial regular/private search provider. Address-bar searches
  use Mozilla's search service. The local new-tab form asks that same service for
  the current provider and its submission URL. Search-engine choice is not locked;
  Firefox's one-time enterprise default respects a subsequent user choice.
- Remote search suggestions (including private suggestions), speculative URL-bar
  connections, link prefetching and the network predictor default off. Ordinary
  page/network activity still occurs. Submitting a search sends its terms to the
  selected provider; installing/selecting providers remains possible in Settings.
- The supported `DisableAccounts` policy disables Firefox Accounts and its Sync
  integration and hides supported account/Sync entry points. No Aelthoren account,
  synchronization service or mandatory login exists. This is a feature gate, not
  deletion of upstream source. Website logins and local passwords remain available.
- Known cross-site tracking content is blocked in normal and private windows.
  Mozilla's supported cryptomining, known-fingerprinting and suspected-fingerprinting
  protections are enabled. Cookie behavior 5 retains partitioning of third-party
  state; network-state partitioning remains enabled. Lists and heuristics have
  limits, and protection can break a site. This is not blanket fingerprint resistance.
- Search, tracking and suggestion defaults are **not locked**. Use the address-bar
  shield/site exceptions and Settings → Privacy & Security to review protection,
  cookies, site data, history and clearing controls. Settings → Search changes the
  default provider. The new-tab page links to Privacy & Security.
- Bookmarks, history, passwords and settings stay in the selected local Aelthoren
  profile. Website data is still exchanged with visited sites. Closing all private
  windows discards private session storage; downloaded files/bookmarks and external
  network records are not erased by private browsing. Deleting a profile is not
  automatic, and disk encryption is an OS/user responsibility.

Accounts, telemetry submission and studies are intentionally product-level gates.
Mozilla's corresponding policies lock their upload/account/study preferences (and
study-controlled recommendation gates). Ordinary browsing/privacy choices remain
editable. Existing profiles may have user overrides of defaults; these are not
silently cleared. Previously stored account tokens/data or telemetry archives are
not claimed to be securely erased by applying a policy.

## Telemetry, recommendations and crash reports

`DisableTelemetry` disables Firefox health/technical and usage uploads, data
submission and telemetry archiving using supported policy gates. Additional
unlocked distribution defaults disable telemetry pings; `DisableFirefoxStudies`
disables studies. Normandy defaults off. UserMessaging/FirefoxHome policies suppress
promotional messaging, recommendations and sponsored home content. The local
new-tab page loads no ads, remote content, suggestion API or page scripts.

There are no Aelthoren analytics collectors or advertising identifiers. Disabling
telemetry does not remove all upstream metrics code or all Mozilla networking.
Local diagnostic logs and inherited local client/metrics identifiers can still exist;
an upload gate is not a promise that no identifier is created on disk. Crash reporting is separate from telemetry;
the inherited automatic content-crash submission preference
`browser.crashReports.unsubmittedCheck.autoSubmit2` was verified false and unlocked
in the fresh profile. No crash was deliberately generated or submitted in this phase. Review the inherited
crash-report consent/automatic-submission controls before submitting reports; their
contents may include URLs, memory or personal data. We do not claim all possible
crash-reporting paths have been audited or removed.

## Inherited remote-service audit

No global Mozilla-domain blocklist, TLS exception, Safe Browsing disablement or
proxy bypass is installed by the product. Hostnames/URLs below identify categories,
not an exhaustive permanent endpoint list; upstream configuration can change them.

| Service | Phase 3 treatment and possible transmission |
| --- | --- |
| Search (initially `duckduckgo.com`) | Search terms/normal request metadata only when submitted; the selected provider supplies its results and privacy policy. Suggestions default off. |
| Accounts/Sync (`accounts.firefox.com`, Sync services) | Integration disabled by policy; no account required. Ordinary visits to websites are not blocked. |
| Telemetry (`incoming.telemetry.mozilla.org`) / studies | Upload gates disabled; no Aelthoren replacement collector. Test scope and limits are in VALIDATION.md. |
| Remote Settings (`firefox.settings.services.mozilla.com` and attachments/CDNs) | Retained for security/blocklists and upstream configuration, including search configuration. Requests expose IP/request metadata. Nimbus/Remote Settings code may still run; disabling studies is not proof every experiment-related request disappears. |
| Safe Browsing (upstream Google/Mozilla providers) | Retained. List updates, reputation/download checks and configured real-time checks may contact upstream providers. Do not claim these requests disappear. |
| Certificate validation | TLS verification/OCSP and inherited revocation/CRLite mechanisms retained. They may contact certificate issuers/Mozilla services. No invalid-certificate acceptance is enabled. |
| Browser/add-on updates and blocklists | Inherited checks retained. Modified development builds have no independently supported Aelthoren update/signing channel. Do not infer safe future updates from an enabled preference; release/update compatibility needs separate work. |
| DNS/DoH, connectivity/captive portal, region/time services | Inherited behavior retained; configuration/OS/provider may perform DNS, connectivity checks and region discovery. This phase does not promise a silent startup. |
| Visited sites, downloads, favicons, extensions | Normal web traffic remains. Extensions/providers can introduce their own networking; user-installed extensions are not covered by these defaults. |
| Push (`push.services.mozilla.com`) | Retained for native web notifications/push; may establish a background service connection without an Aelthoren account. |
| Optional components (`update.googleapis.com`, `ciscobinary.openh264.org`) | Inherited component/codec update checks and possible downloads remain. They are not Aelthoren analytics; review upstream settings/licensing before distribution. |
| Crash submission | Separate inherited consent paths, not triggered/tested here; see above. |

The bounded fresh-session observer recorded 170 attempted HTTP requests, including
`detectportal.firefox.com`, `firefox.settings.services.mozilla.com`,
`firefox-settings.mozilla-backup.org`, `push.services.mozilla.com`, `aus5.mozilla.org`,
`aus5.mozilla-backup.org`, `update.googleapis.com` and `ciscobinary.openh264.org`.
The short restarted-session observer recorded six attempts. Synthetic search requests
were cancelled before transmission. Counts include local fixtures and repeated
attempts, not successful responses or a full traffic inventory. No telemetry-host
POST was observed in those windows.

Observed cloud sessions include region/Remote Settings network failures and an
inherited `ServiceRequest` proxy-diagnostic API error when policies are active.
These are visible limitations, not evidence the services are deliberately disabled
or fully functional. No settings were weakened to hide those errors. Security
service reachability, production updates and an exhaustive packet-level traffic
inventory remain unverified. Use a maintained supported browser for sensitive use.

## Implementation and evidence

`config/privacy-policies.json` is installed as `distribution/policies.json` beside
the built binary. Preferences supported by that policy use `Status: default`.
Additional product defaults use Firefox's supported `distribution.ini` mechanism
(`config/distribution.ini`), not profile `user.js` or a script that overwrites user
choices at each start. The launcher installs reviewed configuration, refuses unknown
owner-edited distribution files and preserves separate profiles. See BUILDING.md.

The only new privileged application interface is a bounded search request in the
existing new-tab actor: top-level about:newtab/about:home only, textual query,
current search engine, HTTP(S) submission only. A page cannot submit an arbitrary
privileged URL. The local page keeps its strict CSP; no engine/network/TLS/sandbox
code is patched. Exact actual tests, failures and limits are in VALIDATION.md.
