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
