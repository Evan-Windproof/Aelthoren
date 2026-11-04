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
