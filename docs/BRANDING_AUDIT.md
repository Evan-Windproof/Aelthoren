# Final Mozilla/Firefox branding audit — Linux 0.1.0-alpha

**Public experimental binary distribution remains blocked.** This cleanup does
not establish legal compliance or independent native identity. It does not approve
the Draft Release, publish a Release, merge this branch or archive the repository.

## Scope and reproducible evidence

Started from remote main `2267b4bb862f69d1a595274dddc025c191462b4b`, containing
Phases 1–5A. New branch: `codex/aelthoren-final-branding`. Upstream remains Firefox
ESR 153.6.0esr, `a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`; genuine Gecko and
SpiderMonkey from the pinned official artifacts. No source acquisition or native
binary identifier patching is needed for this resource-only packaging overlay.

Preserved original package outside Git:
`/workspace/aelthoren-packaging/output/aelthoren-0.1.0-alpha-linux-x86_64.tar.xz`,
88,591,204 bytes, SHA-256
`b40b5a7538e0d62769917e3f439907027476ad43a0d5f23f1933ea4c81440495`.
It was rehashed and extracted to a separate audit directory. It is not overwritten.

`tools/audit_branding.py` enumerates every regular package member, both omni
resource archives, every image resource and text resources containing Mozilla,
Firefox or their domains. [Original inventory](branding/original-inventory.json)
records package file hashes, all image resource hashes, code resource match counts
and localizable/legal text matches. Binary token counts identify inherited native
references; they do not imply that every token should be removed. Large compiled
code lines are truncated in excerpts; native code and dynamic/remote UI cannot be
legally cleared by a string scan. All images are indexed; the two contact sheets
were used to visually inspect the selected product artwork and additional
onboarding/default illustrations. This is a scoped engineering audit with explicit
unresolved gates, not a claim to exhaustive legal clearance.

## Findings and dispositions

| Surface | Finding and action |
| --- | --- |
| Main icon, window icon, toolbar, desktop entry | Existing owner Aelthoren logo/name retained. No new primary logo. Existing desktop ID/profile isolation retained. |
| Onboarding, default browser, account/backup, private browsing, AI sidebar and password illustrations | Recognizable fox mascots and product logos found, including artwork whose names did not contain Firefox. Replaced reviewed resources with original neutral browser-window artwork or the owner's existing icon. Disabled features still contain resources; disabled does not mean absent. |
| Home, Suggest, View, Labs, Screenshots, Translations | Product-facing Fluent term values renamed Aelthoren; technical term identifiers remain unchanged. This does not add/enable these optional features. |
| Vendor label | Fluent vendor-short-name changed to Aelthoren. Actual upstream copyright/vendor information is retained in legal/native attribution. |
| First-run messages | Removed two false assertions that this independent project is backed by the Mozilla Foundation. Existing first-run policy remains unchanged. |
| Network/error pages | Literal Firefox labels in the two appstrings resources replaced; protocol/security instructions retain their meaning. |
| Certificate interception explanation | Reworded the false statement that this product is backed by Mozilla; retains truthful Mozilla CA-store explanation. Certificate validation and distrust behavior unchanged. |
| Product Help/feedback and About legal links | Product support/feedback now point to Aelthoren repository documentation/issues; About terms/privacy point to project LICENSE/PRIVACY. Service-specific Mozilla security/help URLs remain truthful external-service references. |
| About/credits/licenses | Existing Aelthoren About and Mozilla/Gecko/SpiderMonkey attribution retained; no sponsorship implied. about:license, MPL, copyright and upstream contributors remain. |
| Search and browser UI | Existing toolbar/address/tabs/new-tab/search functionality and DuckDuckGo/user choice retained. Provider logos/name references identify real external services and are not renamed. |
| Installation/package metadata | Portable shell launcher and desktop template are already Aelthoren. Native process/basename/application.ini/GUID remain inherited: **distribution blocker**, not falsely certified as cleaned. |

Every changed resource is listed in [resource-changes.md](branding/resource-changes.md).
`branding/final-resources.json` pins the exact original SHA-256 of each resource
and each literal text substitution. `tools/final_branding.py` applies this only
to the temporary packaged runtime after native binary provenance is checked.
Unexpected bytes/missing resources/wrong upstream revision stop packaging. The
input Mozilla package and working source/object tree are never overwritten.
The resulting omni archives use ordinary ZIP resources supported by Gecko; no
ELF bytes, signed add-on binaries, native library IDs, security preferences or
user-agent compatibility tokens are rewritten. BRANDING-CHANGES.json in the package
records the actual before/after hashes. Modified resource instructions and original
neutral artwork are bundled under source/; original license materials remain.

## Assets, provenance and licenses

- Primary logo: owner-supplied `assets/A_text.svg`, unchanged SHA-256
  `3902f792ae0e8de87ff71f33f4394674c91a33058b77596456088d28bff805f1`.
  Existing generated branding raster/SVG resources are reused. The owner's
  redistribution/trademark permission still needs explicit confirmation; MIT
  licensing of independent scripts does not license that mark on their behalf.
- Secondary illustration: `branding/artwork/neutral-browser.svg`, newly authored
  simple geometric browser window/line in existing brand colors. Original project
  artwork under repository MIT LICENSE, no external library or imitated fox/logo.
- Raster fox decorations use the existing owner icon at the original dimensions.
  Packaging uses Pillow for this conversion (tested Pillow 13.0.0); install from
  the official Python package index or trusted distro repository, with TLS enabled.
- No third-party artwork was downloaded. Upstream service/provider/compatibility
  artwork and notices retain upstream ownership/licensing, not an Aelthoren claim.

## Legitimate references intentionally retained

Mozilla MPL and third-party notices; Firefox ESR source/version provenance; Gecko
and SpiderMonkey attribution; about:credits/about:mozilla historical attribution;
Mozilla CA-store/vendor/security-policy/blocklist explanations; OpenH264/service
attribution; AMO/extension compatibility IDs, NSS issuer/PKCS#11 names; enterprise
policy names; source/module/chrome namespaces; developer tooling target names and
logos for actual external Firefox channels; Mozilla VPN/Monitor/Relay/Focus and
other service names/icons where identifying those actual services; user agent
compatibility; native ABI/version/GUID/crash/update metadata. External services
must not be renamed Aelthoren or represented as independently provided features.
Some promotional/optional resources remain packaged even when policy hides their
entry points; this is explicitly not an all-Mozilla-artwork removal claim.

## Native identity and public-release blockers

The supported wrapper uses `-app` with Aelthoren Name/Vendor/RemotingName/Profile,
`--no-remote`, owned dedicated profiles and desktop ID `org.aelthoren.Browser.Alpha`.
The compiled executable/process remains `firefox`/`firefox-bin`, and native
application.ini and Firefox GUID remain inherited. Earlier GUID experimentation
was not a supported verified independent identity; it is not repeated or papered
over with binary string replacement. The Artifact Build reuses compiled Gecko
and launcher constants. Complete changes require a maintained full source-build
configuration (MOZ_APP_NAME/BASENAME/REMOTINGNAME/application ID/native launcher,
crash/update identity), matching frontend resources and dedicated Linux desktop/
Wayland/default-handler testing. A renamed wrapper is not sufficient evidence.

Additional gates: inherited generic latest/safest/update copy is not proof of an
independent update channel; no independent signing or security-update delivery;
current advisory/security support must be rechecked before any eventual release;
corresponding-source/dependency obligations and owner asset rights require review.
Default-browser/URL-forwarding and all desktop/accessibility combinations remain
uncertified. Repository archival would not remove these maintenance obligations.

Official policies reviewed over verified HTTPS (HTTP 200, 2026-11-06):
- https://www.mozilla.org/en-US/foundation/trademarks/policy/
- https://www.mozilla.org/en-US/foundation/trademarks/distribution-policy/

The distribution policy distinguishes unaltered distribution from modified
software and says modified software may not be redistributed using Mozilla marks
without prior written consent. This package is modified; no permission is assumed.
Technical attribution is retained rather than indiscriminately deleting names.
This engineering review is not legal advice or a complete compliance determination.

## Build and GUI verification status

The original pinned artifact frontend/native package is reused; only reviewed
resources in the new staged package change. Prototype and final commands, actual
outcomes, screenshots, final size/SHA and remaining test limits are recorded in
VALIDATION.md and accompanying branding evidence. Pending checks are not passes.
