# Aelthoren validation

## Current Phase 2 result — 2026-11-05

The branded Linux artifact configure, install and standard build passed. Actual
browser HTTP/JavaScript/DOM/storage, native history/tab handling and two profile
paths passed automated checks. Normal browser launches rendered the branded
new-tab/About/Settings pages; screenshots were inspected. Nine tooling tests pass.
The engine binary/pin are unchanged. Native GUID/OS identity and release branding
remain limited; Phase 3 is not implemented. Detailed evidence follows the retained
Phase 1 record below.

# Phase 1 restart validation — 2026-11-04

## Actual outcome

A genuine Firefox ESR 153.6.0esr **artifact development browser** was configured,
assembled, launched and verified on Linux. Both Mozilla's frontend target and the
standard `mach build` target passed in artifact mode. Actual Gecko rendering and
SpiderMonkey JavaScript/DOM/localStorage behavior passed a live HTTP fixture test.
**Gecko/SpiderMonkey were precompiled by Mozilla, not compiled from source here.**
Phase 2 branding and Phase 3 privacy behavior were not started.

## Environment and preservation

- Existing branch: codex/aelthoren-restart; existing PR: #1 targeting main.
- Starting project commit: 06f95d714cae4efbcc600aa5c0b7d6f5529e5b01.
- GitHub remote was checked with ls-remote: main remains the original baseline;
  the existing development branch matched the published preservation checkpoint.
- Debian 13 x86_64, cgroup 4 CPUs / 32 GiB RAM; initially about 60 GiB free.
- Existing source reused; no Git worktree or additional PR/branch created.
- Original owner logo copied unchanged, SHA-256
  3902f792ae0e8de87ff71f33f4394674c91a33058b77596456088d28bff805f1.
  It is stored as a project asset, not integrated into browser UI in Phase 1.

## Source and downloaded input verification

Official repository: https://github.com/mozilla-firefox/firefox.git
Tag: FIREFOX_153_6_0esr_RELEASE
Exact source HEAD: a34c4160e3f75ab9918fbe4669ff7ae56f1977c8.
Tracked source diff is empty. No engine, browser security or branding patch applied.
Official artifact task: YlYD4FnWSXGLhOw9Il8lig, indexed by the same Git revision.
See upstream.lock.json and UPSTREAM.md.

The configured cloud policy was observed current/enforced and unrestricted. The
previously denied Mozilla artifact host was successfully accessed via the inherited
proxy and normal TLS verification using approved execution outside the command
sandbox. No proxy bypass, trust override or insecure download flag was used.
The official chain-of-trust record matched the task ID and all pinned archive hashes.
It was obtained over verified HTTPS; independent signer verification is not claimed.

`python3 tools/prepare_phase1.py`: exit 0. Source was reused; three input sizes and
SHA-256 values passed before extraction or execution:

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| target.tar.xz | 86,792,624 | 5f6f4085a20f4aab226fcd1c199a23589f5e89c38b3ad26789b3c56bb706bdf0 |
| target.xpt_artifacts.zip | 262,101 | 98e903397f596faf3637775b329e4d7b9293905966d1cd3020d8899311a549b8 |
| target.common.tests.tar.zst | 72,439,669 | f8937295c5c4d811ab369c2d8e913118428cbe6954d5c2ccb9bdc99cd8094d6d |

Archives/caches are outside Git, under /workspace/aelthoren-downloads. Acquisition
log: docs/phase1/acquisition.log. The common-test archive supplies the missing updater
test binary that blocked the previous lost-work standard artifact build.

## Build commands and results

From /workspace/Aelthoren:

```sh
python3 tools/prepare_phase1.py
python3 tools/browser.py build
python3 tools/browser.py full-target
```

The build script sets workspace-local MOZBUILD_STATE_PATH, the artifact mozconfig,
existing Node, and a MOZ_ARTIFACT_FILE list of the three verified inputs. It preserves
inherited proxy/trust settings and does not introduce sandbox-disabling variables.
The source's Node check accepted installed Node 24.22.1.

| Underlying command, source cwd | Exit | Result |
| --- | ---: | --- |
| ./mach --no-interactive configure | 0 | Generated artifact build configuration |
| ./mach artifact install | 0 | Installed verified local browser/XPT/common-test archives |
| ./mach build faster | 0 | Frontend/application-layer target passed |
| ./mach --no-interactive build | 0 | Standard target passed in artifact mode |
| ./mach run --headless --version | 0 | Mozilla Firefox 153.6.0esr |

The updater-xpcshell test binary is now present under
obj-aelthoren-restart/_tests/xpcshell/toolkit/mozapps/update/tests/ (5,016,280 bytes).
No binary substitution, test disabling or assertion removal was used to get a pass.
The standard target result is still an **artifact** build, not a full Gecko source
compile. Logs are in docs/phase1/. The first smoke pass exercised frontend output;
when the standard target updated package files, the final output was tested again.

## Actual browser rendering and functional tests

`python3 tools/browser.py smoke` runs the actual browser and unchanged security
settings, with an explicit fresh disposable profile and --no-remote. A temporary
server bound to 127.0.0.1:8765 serves docs/smoke/index.html. It is a test webpage,
not a fake browser UI. The browser command is:

```sh
./mach run --headless --no-remote \
  -profile /workspace/aelthoren-phase1-profile \
  --screenshot /workspace/Aelthoren/docs/phase1/smoke.png \
  http://127.0.0.1:8765/
```

Both initial and final smoke browser runs exited **0**. The final HTTP log records
GET / -> 200 and GET /result?status=pass -> 200. That callback is sent by JavaScript
only after localStorage write/read/delete succeeds and the DOM text is updated.
The server result was exactly ['pass']; smoke-result.json reports passed=true.
The final PNG was opened and visually inspected: expected heading, blue rectangle,
and **PASS: JavaScript, DOM, and storage**. Its SHA-256 is recorded in the JSON.
Initial frontend-only evidence is retained under docs/phase1/frontend-smoke/;
final standard artifact-build evidence is under docs/phase1/.

Browser and fixture server were stopped after verification. Approved execution
outside the socket-limited command sandbox was required for localhost testing;
no browser sandbox/security protections were disabled. Headless graphics and
inherited remote-service/shutdown warnings appear in the logs; they did not prevent
the tested request, assertions, screenshot or normal process exit.

## Tooling checks and scope

`python3 -m unittest discover -s tools -p 'test_*.py' -v`: **4 passed, 0 failed,
0 skipped**. They exercise valid pins, same-size corruption, wrong sizes, and
rejecting a different source revision without resetting it. Source/input checks
were also exercised directly against real files after the helper's final update.
These tests are distinct from the actual browser functional verification.

Runnable output: /workspace/aelthoren-gecko/obj-aelthoren-restart/dist/bin/firefox.
Precompiled engine: the adjacent libxul.so. Actual binary sizes/hashes and source
cleanliness are recorded in docs/phase1/binary-provenance.json; binaries are not
committed. The source, downloaded archives, object files, user profile and caches
are outside the project tree. Only source/scripts/docs, the owner SVG and small
intentional screenshot/log evidence are included in the milestone commit.

Not verified/implemented: full engine source compilation, HTTPS browser navigation,
upstream regression suites, exhaustive security audit, Windows builds, installers,
release signing/update infrastructure, Phase 2 branding or Phase 3 privacy defaults.
Default Firefox accounts/sync/remote services remain inherited; no current privacy,
anonymity, performance or account-free product claim is made. This is not a supported
release. Licenses and Mozilla attribution/security mechanisms are retained.

## GitHub preservation gate

The completed milestone must be committed and pushed to the existing
codex/aelthoren-restart branch with tools/preserve_milestone.sh. Its remote SHA must
match local HEAD, and existing PR #1 must be updated with these actual results.
The final task report gives the remotely verified commit link. No environment
snapshot or local-only commit is treated as durable preservation.


# Phase 2 branding/interface — 2026-11-05

## Repository preflight and scope

Initial project branch was codex/aelthoren-restart at 5af403b (published Phase 1).
Read-only GitHub checks showed PR #1 closed and main at
0172d112b11b9870aba8975a0a0a6e07a9cd461c. Fetched main and fast-forwarded the
same development branch to that merge commit. No history was rewritten, work
removed, new branch/environment created or extra PR opened.

Reused official Firefox ESR 153.6.0esr source at
**a34c4160e3f75ab9918fbe4669ff7ae56f1977c8** and the verified Phase 1 local browser,
XPT and common-test archives. upstream.lock.json and the original owner SVG are
unchanged. Owner asset SHA-256 remains
3902f792ae0e8de87ff71f33f4394674c91a33058b77596456088d28bff805f1.

## Implemented frontend and identity

- Generated a separate browser/branding/aelthoren overlay from the pinned unofficial
  template, preserving MPL headers. Inkscape generated Linux PNG icons from the
  owner's exact SVG artwork. Integration viewBox/dimensions encompass negative
  artwork coordinates without redesigning shapes/colors or changing the original.
- Aelthoren Fluent/properties names, wordmarks and About assets; Settings screenshot
  shows the owner icon, product labels, About Aelthoren and Aelthoren support.
- Script-free, strict-CSP local about:newtab with logo, slogan, instruction to use
  the native address bar, and Bookmarks/Settings/About links. No new page scripts,
  remote assets, fonts, recommendation services or animations.
- A packaged About page with Mozilla attribution/license links and explicit
  development/Phase 3/identity limitations. This is content inside the real browser,
  not an HTML replacement for native browser navigation or rendering.
- Preserved native toolbar/address bar/reload/tabs/history controls. No engine,
  networking or browser-security implementation changes.
- Runtime launcher uses supported -app metadata with Name/Vendor Aelthoren,
  RemotingName aelthoren and own Profile field, retaining native Firefox GUID and
  Gecko version requirements. Separate named profiles under
  /workspace/aelthoren-user-data/profiles; arbitrary paths/app/profile passthrough
  are rejected and nonempty unmarked user profiles are not adopted. --no-remote
  prevents attaching to another Firefox process. No personal profile migration.

Only two tracked upstream frontend files change, captured in
patches/0001-phase2-ui.patch: the new-tab redirector and two About attribution lines.
The local static page avoids waiting for the unused Activity Stream renderer;
URI security flags, process guard and loadInfo remain intact. Other inherited
new-tab addon services/remote behavior remain present, not globally disabled.
Expected source/branding files are content-hashed; repeated preparation verifies
them and refuses unknown modifications instead of overwriting/resetting work.

## Commands and build results

```sh
cd /workspace/Aelthoren
python3 tools/phase2.py prepare
python3 tools/phase2.py build
python3 -m unittest discover -s tools -p 'test_*.py' -v
python3 tools/verify_phase2.py
```

The build helper sets the same inherited proxy/trust environment, local verified
MOZ_ARTIFACT_FILE list, explicit Node and workspace-local state as Phase 1, selecting
config/mozconfig.linux-aelthoren and obj-aelthoren-phase2. Final commands, source cwd:

| Command | Exit | Actual result |
| --- | ---: | --- |
| ./mach --no-interactive configure | 0 | Branded artifact configuration |
| ./mach artifact install | 0 | Verified local browser/XPT/test inputs |
| ./mach build | 0 | Standard artifact build completed |

Initial branding build also passed; initial UI verification exposed a routing/loading
problem described below. The final corrected overlay was rebuilt and all runtime
checks then passed. Existing Inkscape user-config/GTK warnings were nonfatal.
Preparation was repeated successfully: existing overlay verified, no files replaced.

Precompiled libxul.so is byte-identical to Phase 1: 185,074,264 bytes, SHA-256
4c2cbbfb8a0b85effa9a623fd3ffd293db3fb16bcacf5f1bf9acc7aa32ef02fc.
See docs/phase2/engine-comparison.json. No local Gecko/SpiderMonkey source
compilation is claimed. No additional dependencies were fetched for Phase 2.

## Actual browser verification

The HTTP harness temporarily enabled Mozilla's loopback-only Marionette interface
on dedicated test profiles. No privileged system-access opt-in was used; production
launcher does not enable automation. All HTTP tests use the actual browser/native
WebDriver operations, not mock objects. Both sessions ended through Marionette's
normal quit command and browser exit **0**:

1. Profile /workspace/aelthoren-user-data/profiles/phase2-verification:
   capabilities confirmed exact profile and version 153.6.0,
   acceptInsecureCerts=false. Real HTTP page rendered; JS DOM text was
   PASS: JavaScript, DOM, and storage; the fixture's localStorage key was removed
   after its write/read/delete assertion. Screenshot captured and inspected.
   Native Back/Forward navigated between two actual HTTP pages. Created a native
   second tab, switched, navigated, verified two handles, closed it and verified
   only the original handle remained.
2. Profile /workspace/aelthoren-user-data/profiles/phase2-second:
   independently confirmed profile path, version, acceptInsecureCerts=false and
   the same real JS/DOM/storage assertions; exit **0**.

Result JSON: docs/phase2/runtime-results.json. HTTP requests and successful JS
callbacks are retained in http.log. The page could be served from cache on repeat
navigation, so logs are not claimed to count every navigation as a network fetch.

Internal UI used normal browser command-line launches instead of privileged
WebDriver navigation. Commands were run via tools/run_aelthoren.py with own
phase2-ui-final profile, --headless, --window-size 1366,1000, --screenshot and the
respective real browser URL. Each exited **0**:

| URL | Visually inspected output |
| --- | --- |
| about:newtab | Owner logo, Aelthoren, official slogan, address-bar instruction, local shortcuts |
| chrome://branding/content/about-aelthoren.html | Branded About page, version, attribution/license links and development limitations |
| about:preferences | Owner icon and Aelthoren labels; inherited account/sync UI still present |

Images: docs/phase2/newtab.png, about.png, settings.png and smoke.png. Metadata is
in internal-pages.json and identity.json. Normal screenshots verify visible UI;
HTTP automation separately verifies live behavior. Browser/server instances were
stopped after tests. Headless graphics and inherited remote-service/shutdown errors
remain in logs, but final assertions, screenshots and all five normal exits passed.
No SSL acceptance, sandbox-disabling flags or security preference overrides were
introduced. acceptInsecureCerts=false is a capability check, not a separate invalid
certificate/HTTPS site test; that broader behavior remains unverified.

## Initial failures, supported correction and test limits

The initial local page used a chrome URI through the inherited new-tab redirector.
WebDriver refused about:newtab navigation as unsupported in that context. That
failure is recorded under docs/phase2/automation-restriction; no system-access
permission or browser security restriction was disabled to bypass it.

Normal headless about:newtab navigation in that initial form then timed out at
60 seconds without a screenshot. The test process group was stopped. Evidence is
under local-page-channel-failure. Final source uses an explicitly registered local
resource URI and skips only the renderer-startup wait for that specific static
resource. Security URI/process/loadInfo flags were not changed. The final build
and runtime suite above were run after this correction. No incomplete attempt is
reported as passed, and the failed trace files are retained as diagnostic evidence.

Nine tooling tests passed, zero failed/skipped: the four preserved Phase 1 pin
checks plus five profile/identity tests (path escape, preservation of unmarked user
data, separate named storage, runtime name with preserved GUID/version, and reserved
profile argument rejection before browser execution). Unit fixtures are synthetic
and are not substituted for the real browser checks above.

## Remaining limitations and integration

- Artifact launcher retains native Firefox GUID, executable basename, user agent
  and some OS identifiers. Fully independent native identity/platform integration
  remains full-build work; no such change was tested or claimed here.
- Mozilla illustrations, Firefox Labs/More from Mozilla and some upstream service/
  legal links remain. No comprehensive trademark/distribution audit, independent
  signing/update infrastructure or supported release is claimed. Owner asset
  rights and upstream MPL notices remain; public redistribution needs review.
- No account/sync removal, default-search changes, telemetry audit or privacy
  behavior changes: Phase 3 has not started. The new-tab slogan is a product goal;
  the About page explains that the corresponding privacy functionality is pending.
- Full engine compilation, Windows/macOS packaging, native About-dialog visual
  inspection, exhaustive security/HTTPS/extension/default-browser interoperability
  checks remain unverified. Equivalent packaged About UI is what passed.
- Phase 1 object files/scripts are preserved; its clean-source guard now correctly
  rejects this intentional overlay. Use phase2.py for current builds; do not reset
  source work or infer that the Phase 1 implementation was deleted.
- Work is committed/pushed on the existing codex/aelthoren-restart branch and remote
  SHA must be verified by the preservation helper. PR #1 was already closed/merged
  at preflight; no extra PR is created. The branch's changes relative to main are
  ready for the next integration review. No release/environment publication or
  main-branch push is performed by this task.


# Phase 3 — privacy and search (2026-11-04 UTC)

This section supersedes the historical Phase 2 statement that privacy/search work
has not started. Branch codex/aelthoren-phase3 started from current main merge
4ce1d12, preserving Phase 1/2 history. No source/archive reacquisition or upstream
revision update occurred. Firefox ESR 153.6.0esr remains at
`a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`; all three archive sizes/SHA-256 were
rechecked by the build environment guard. The owner SVG and upstream.lock.json are
unchanged. This is an **official Mozilla Linux artifact frontend build** with
precompiled Gecko/SpiderMonkey, not local engine compilation or release packaging.

## Implementation and executed commands

- Added reviewed distribution policies/defaults; the launcher installs them beside
  the binary and refuses unknown owner edits. Ordinary search/tracking defaults
  are unlocked. Accounts, telemetry uploads and studies use supported product gates.
- Added a script-free new-tab search form handled by Mozilla's existing actor and
  current SearchService. Queries use the currently selected provider, not a fixed URL.
- Added a two-check frontend patch so redesigned Settings respects the disabled
  account gate. Native browsing/storage/security code is unchanged.
- Added privacy links/factual About text, privacy/security/service audit documentation,
  safe existing-overlay upgrade/build tooling and actual browser verification.

```sh
cd /workspace/Aelthoren
python3 tools/phase3.py prepare
python3 -u tools/phase3.py build > docs/phase3/build-console.log 2>&1
python3 -u tools/verify_phase3.py > docs/phase3/test-console.log 2>&1
python3 -m unittest discover -s tools -p 'test_*.py' > docs/phase3/tooling-tests.log 2>&1
node --check /workspace/aelthoren-gecko/browser/actors/AboutNewTabParent.sys.mjs
node --check /workspace/aelthoren-gecko/browser/actors/AboutNewTabChild.sys.mjs
node --check /workspace/aelthoren-gecko/browser/components/preferences/preferences.js
git diff --check
```

Preparation reported the current overlay verified. Build ran the official
`./mach --no-interactive configure`, `./mach artifact install`, `./mach build`,
all exit 0; logs are in docs/phase3/{configure,install,build}.log. Prior iterations
used phase2.py build with the same official sequence; Phase 2's historical logs
were preserved, and the final phase3.py build writes separate logs. The build
installed distribution/policies.json and distribution/distribution.ini.
Generated binaries remain outside Git in obj-aelthoren-phase2/dist/bin.
Run normally with `python3 tools/run_aelthoren.py --profile default`.

## Final actual results

`docs/phase3/runtime-summary.json` records PASS: **25 browser checks** across a
fresh profile and a restart of that same profile. `runtime-results.json` contains
the evidence. Browser reports Aelthoren 153.6.0 on Linux, genuine Gecko user agent,
headless true and acceptInsecureCerts false. Profile:
/workspace/aelthoren-user-data/profiles/phase3-37b4ec6a304f.

| Check | Actual result |
| --- | --- |
| Initial default | DuckDuckGo; built-in alternative engines remain available. |
| New-tab search | Actual form submission reaches selected provider's submission channel. |
| Native address bar | Actual native command routes to selected provider. No synthetic-phrase request observed while typing before submit. |
| User choice/restart | Native Search settings control present; Mozilla USER-reason search API selected Bing. After a clean shutdown/restart Bing remains selected; both search entry points use Bing. Native mouse/keyboard interaction with the provider dropdown was not separately automated. |
| Accounts/Sync | Supported account gate locked false; account toolbar and Sync category hidden after frontend correction. No account login or remote Sync attempt is needed to browse. Removal of every upstream account string/source module is not claimed. |
| Telemetry | Upload/submission/archive/usage gates false and locked; additional ping defaults false. Ordinary search, partitioning and tracking choices remain unlocked. |
| Cross-site tracking | Pinned Mozilla test classifier labels tracker; resource blocked in native content-blocking log, no tracker HTTP request reaches fixture server. Native site exception then permits that same script and server request (positive control); exception/test lists cleaned up. This is deterministic classifier testing, not a live blocklist coverage audit. |
| Partitioning | Same third-party localStorage under site A → site B → site A returns `["site-a", null, "site-a"]`. Cookie behavior 5 and network-state partitioning true/unlocked. Cookie/network cache partitioning is configured, not separately measured at packet level. |
| Private browsing | Two sequential private windows report private mode, cannot see normal localStorage, and the next private session cannot see previous private storage. Waits for actual last-private-context-exited notification. Normal data remains intact. |
| Local data | Bookmark/native password-store insert succeeds. Bookmark, password, actual navigation history and normal localStorage survive restart. Synthetic fixture login cookie works. No real website account/login was used. |
| Controls/navigation | Privacy/site-data controls and native manage-exceptions button present; back/forward and new-tab/switch/close succeed. Clear-site-data UI is visible; destructive UI clearing was not automated. |
| Real rendering | HTTP and HTTPS JavaScript/DOM execute; localStorage read/write works. Screenshots of new-tab and privacy Settings inspected. |
| TLS | Proper local CA/leaf trusted only in disposable profile renders; a separate untrusted certificate is rejected with `insecure certificate`. No acceptance override. Public HTTPS/complete certificate ecosystem testing is not claimed. |
| Security configuration | Content sandbox level 6, Fission true, Safe Browsing malware/phishing true, OCSP 1 and JavaScript true. This is not an exploit/OS sandbox enforcement audit. |
| Network observation | 170 post-attachment HTTP attempts in fresh session, six after restart, no telemetry-host POST. Includes fixture and cancelled synthetic search channels, not successful response counts. Does not cover all startup/shutdown, non-HTTP or crash paths. |

The test-only `--remote-allow-system-access` grants privileged automation only for
disposable profiles; normal launcher commands do not include it. The test profile
sets `remote.prefs.recommended=false`: Mozilla's recommended automation preferences
otherwise disable private-mode tracking and Safe Browsing and are inappropriate
for measuring product defaults. Temporary classifier resource mapping, local DNS
and narrow fixture-only proxy exclusions are testing arrangements, not product
settings or remote-network bypasses. Fixture CA keys are outside Git and deleted;
NSS test trust/profile data remain only in the named disposable profile.

**12 tooling tests passed**, zero skipped/failed: preserved Phase 1/2 pin/profile
checks plus three distribution-file preservation checks. Node syntax checks and
Git whitespace check passed. Tests are actual executed results, not placeholders.

## Initial failures and corrections

Diagnostic console/error records under docs/phase3/initial-failures are retained.
Committed logs have trailing spaces normalized; raw originals remain outside Git
in /workspace/aelthoren-tests/raw-phase3-logs. No diagnostic messages were removed.
They are not counted as passes. Initial probing also lives outside Git in
/workspace/aelthoren-tests; no build inputs/binaries were committed.

- The pinned ESR exports SearchService as a module, not Services.search; the actor
  was corrected to that official API. BrowsingContext.loadURI requires an nsIURI,
  not a string; corrected and rebuilt.
- Preferences policy rejects telemetry/app/partition keys outside its allowlist.
  Those defaults moved to supported distribution.ini; final browser log has no
  policy preference-rejection errors. No allowlist/security control was bypassed.
- Automation initially applied Mozilla's test preferences, falsely reporting private
  tracking/Safe Browsing off. Disabling that test-only override exposes the real
  product configuration, which passed. No security preference was weakened.
- Initial self-signed CA-as-server fixture was rejected; replaced with a proper
  local CA and separately issued server leaf. An untrusted negative control remains.
- A file-scheme system-module import was refused; the pinned classifier helper now
  uses a narrowly scoped test-only resource mapping, removed after testing.
- Tracker test assertions initially read the wrong sandbox global; DOM-based
  results now verify execution. Synthetic host routing needed explicit local
  fixture proxy exclusions, scoped to test profiles and localhost DNS mappings.
- Private-window tests raced Firefox's initial about:privatebrowsing navigation
  and asynchronous teardown. They now wait for delayed startup/initial page and
  last-private-context-exited before navigation/reopening. Final run passed.
- Runtime exposed the redesigned Settings account category ignoring the account
  gate. The small 0003 frontend patch fixes that; final Settings screenshot confirms
  absence of account/Sync navigation. Old IDs also differ in redesigned settings;
  tests use the actual visible native controls.

## Remaining limits

No full Gecko/SpiderMonkey engine compilation, Windows build, signing/installer,
independent native application GUID/update infrastructure or supported release.
Settings visibly warns that the development browser is having trouble updating;
this warning is retained. Remote Settings/region calls fail in this cloud run.
Inherited ServiceRequest proxy diagnostics assume an array from getActivePolicies,
while the pinned policy API returns an object; this emits a TypeError. It is an
upstream diagnostic limitation, not silently patched or hidden, and security-service
reachability/production update delivery remain unverified. Other logs include
headless software-renderer/favicon/metrics and backup-directory diagnostics.

Observed remote requests include connectivity, Remote Settings (primary/backup),
Push, upstream browser/component/codec updates. No claim of zero background traffic,
complete anonymity, working production updates or exhaustive live tracker coverage
is made. Crash automatic-submission default was false/unlocked; no crash submission
was tested. See PRIVACY.md for the service inventory and data implications.

Implementation, evidence and documentation are to be committed/pushed on
codex/aelthoren-phase3, with exact remote SHA checked and a new PR to main. No
main push, automatic merge, release/environment publication or Phase 4 work.


# Phase 4 — measured lightweight optimization (2026-11-06 Asia/Taipei)

Fetched origin/main and confirmed Phase 3 merged as 6ff8051; created
codex/aelthoren-phase4 without resetting/replacing work. GitHub push/default-main
access was confirmed. Source revision remains
`a34c4160e3f75ab9918fbe4669ff7ae56f1977c8` (Firefox ESR 153.6.0esr). Official logo,
source/artifact lock and privacy/default configuration hashes are unchanged.

## Baseline preserved before changes

A fixed local Xorg dummy display (1366×768×24; window 1200×700, not headless),
four CPU quota and 32 GiB limit were used for both conditions. All six baseline
sessions completed before editing product code. Baseline data/tools/protocol were
committed and pushed in **e413cfd8a817f1c101d52714713c06b7e3b0a891**, remote SHA
verified, and preserved in draft PR #4. It is the same PR used for final Phase 4.
No new environment or branch/PR beyond the requested Phase 4 pair was created.

Baseline and candidate each used three fresh-profile/warm-restart pairs, distinct
loopback origins at 1/5/10 tabs, native switching/new-tab loading, local JS/DOM/
storage/history, CPU, process RSS/PSS/counts and bounded HTTP observations. Median,
range, n, units, measurement method and environment are in docs/PERFORMANCE.md.
Fresh profile is a startup proxy; true OS/disk-cold startup was not measured.
Initial incomplete automation-context/handle/history attempts were excluded and
retained outside Git; final six-run datasets use the same corrected protocol.

## Retained change and measured result

Only product changes: tools/privacy.py and tools/run_aelthoren.py. The installer
compares actual installed bytes and the expected ownership digest before skipping
unchanged configuration/marker writes. The named-profile helper likewise leaves
its already-correct marker untouched. New installation, reviewed updates, marker
repair and refusal of unmanaged edits retain their prior behavior. Full source/
branding verification, policies/preferences, native browser code and UI are intact.

- Rewritten unchanged files: **5 → 0** in every desktop launch and targeted fixture.
- Buffered configuration/profile preparation: **651.75 → 129.48 µs (-80.1%)**,
  seven batches × 200 repetitions. This excludes full provenance/browser startup.
- Fresh-profile responsiveness: **2037.42 → 2042.34 ms (+0.2%)**, n=3 each.
- Warm responsiveness: **1525.75 → 1450.61 ms (-4.9%)**, n=3 each; ranges overlap.
- 10-tab PSS **532.12 → 530.20 MiB (-0.4%)**, RSS **1732.32 → 1729.71 MiB**;
  10-tab process count stayed 21. No meaningful memory reduction is established.
- Regressions are published, including tab creation +4.6%, warm listener +8.8%,
  new-tab loading +0.9%, 10-tab CPU +0.39 percentage points and an elevated
  switching-session outlier. Small shared-host sequential samples do not establish
  a consistent material runtime regression caused by this pre-launch-only change.
  We retain it for deterministic I/O reduction, not a broad speed/CPU/memory claim.

All **12 desktop benchmark sessions exited 0**, with no reported crash or failed
fixture assertion in the final datasets. Native GC, process counts, tab suspension,
security services and background tasks were not disabled or retuned. After closing
back to one tab, resource/process values remained within baseline variation;
this bounded test is not a heap-leak or long-soak proof.

## Commands and actual verification

```sh
python3 tools/phase3.py prepare
python3 tools/benchmark_phase4.py baseline
python3 tools/benchmark_launcher_io.py baseline
# Commit/push/verify baseline before the two-file product change.
python3 tools/benchmark_launcher_io.py candidate
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/benchmark_phase4.py candidate
python3 tools/summarize_phase4.py
python3 -u tools/verify_phase4.py
python3 -m py_compile tools/benchmark_phase4.py tools/benchmark_launcher_io.py tools/summarize_phase4.py tools/verify_phase4.py
git diff --check
```

Display setup/authority commands, exact fixture definitions and output locations
are in PERFORMANCE.md. The existing verified artifact build was reused unchanged;
**no mach build or local C++/Rust engine compilation occurred in Phase 4** because
only Python launch preparation changed. Post-test phase2.environment() rechecked
all three pinned archive sizes/SHA-256. Installed Firefox executable and libxul.so
were streamed/hashed against those exact official archive members and match
byte-for-byte (docs/phase4/artifact-verification.json).

**25 preserved Phase 3 browser checks passed after the change**, including changed
search provider retention across restart, account/Sync UI gates, tracker blocking
and exception, storage partitioning, private-session cleanup, local bookmark/
history/password/storage persistence, native navigation, real HTTP/HTTPS JS/DOM,
untrusted certificate rejection and effective sandbox/Fission/Safe Browsing prefs.
A separate desktop two-tab test kept the original tab in the background for four
seconds and observed its timer advance **0 → 3**; browser exited 0. **12 tooling
tests passed**, zero skipped/failed, including refusal/preservation of edited or
unmanaged configuration. Syntax/whitespace checks passed.

Regression script reuses Phase 3 test-only privileged automation and disposable
NSS fixture trust with remote.prefs.recommended=false; normal launches gain no
such permissions or trust. Intentional structured results and effective preferences
are consolidated in docs/phase4/regression-results.json. Browser logs, screenshots,
profiles, keys, X authority and temporary benchmark/partial-attempt files remain
outside Git. Historical Phase 3 evidence was not overwritten. No downloaded source,
archive, binary, cache or credential is included in this milestone.

## Limits and publication

Only redundant logical writes and targeted preparation time are established
improvements. No claim of faster/lighter operation than unmodified Firefox; no
comparable Firefox measurement was performed. Short idle windows, small local pages,
shared-host scheduling, software rendering, automation/animation-frame timing,
sequential condition order, caches and inherited network retries limit inference.
CPU/network changes and a switching outlier are not concealed. Real input latency,
true OS-cold startup, network byte totals, realistic heavy sites, exhaustive leaks
and long-running stability remain future measurements.

The Phase 3 cloud region/Remote Settings/update failures and inherited proxy-
diagnostic API error remain. No security feature/proxy/TLS validation was bypassed
or disabled to hide them. Production update delivery, a supported release, full
native identity and full engine source compilation remain unverified. No compiled
optimization was attempted; those require a suitable full-build/security workflow.

Final implementation/results are published on codex/aelthoren-phase4 in PR #4
(https://github.com/Evan-Windproof/Aelthoren/pull/4), with exact remote SHA checked
by the preservation helper and GitHub API at completion. No main push, automatic
merge, environment/release publication or Phase 5 implementation.
