# Phase 4 performance protocol

Measurements start from merged Phase 3 main commit
6ff8051 (implementation bc08257), with the same pinned Firefox ESR 153.6.0esr
revision a34c4160e3f75ab9918fbe4669ff7ae56f1977c8 and existing verified official
artifact browser. No optimization is applied until the baseline is recorded.

The authenticated Xorg dummy display is 1366×768×24, browser window 1200×700;
this is a real desktop browser, not headless. Debian 13 x86_64, four CPU quota,
32 GiB cgroup RAM limit. Ten different loopback IP origins serve identical local
pages (400 DOM nodes, 16,384 JS objects, one 1 Hz timer). The native process model
and security services remain unchanged. Benchmark profiles, display authority,
server logs and temporary files stay outside Git.

Three fresh profiles and immediate restarts of the same profiles provide three
profile-cold and three warm runs per condition. OS caches cannot be flushed in
this shared environment: **physical disk-cold startup is not measured**. Fresh
profile startup must not be confused with an OS cold boot. Warm restart follows
the complete multi-tab workload and clean shutdown. Automation, software rendering,
shared-host scheduling and inherited remote-service retries affect results.

Startup is launcher spawn → automation listener and launcher spawn → initial local
DOM ready plus two animation frames. Responsiveness is this operational first-page
proxy, not an OS input-to-photon measurement. Native tab creation includes automation,
switch/navigation and two frames; switching includes automation and two frames.
New-tab load is about:blank → branded about:newtab with current-provider placeholder
ready plus two frames, measured in a separate scratch tab. Three loads per browser
session; per-session medians will be compared rather than treating all inner
measurements as independent launches.

Resource measurements wait two seconds, then sample five one-second intervals at
1, 5 and 10 tabs and again after closing back to one. Aggregate browser-descendant
RSS includes the launcher and double-counts shared pages. PSS is reported only
when every process permits smaps_rollup access; otherwise it is unavailable.
CPU is CPU seconds over elapsed seconds ×100 (100% = one core), summed across
current descendants; short-lived processes between samples can be missed.
Process counts are measured, never artificially reduced. Network counts are
attempted HTTP channels during the five-second windows, not bytes, successful
responses or a complete startup/shutdown/WebSocket trace. Local loopback exceptions
are confined to test profiles. Remote proxy/TLS/security settings remain intact.

A bounded open/switch/close cycle checks JS, DOM, localStorage, history, normal
background timers and orderly exit. Memory after closure is not proof of a leak
or its absence: Gecko legitimately retains processes/caches and manages its own GC.

Candidate acceptance: retain source/artifact/branding/privacy/security guards;
measure unchanged configuration/profile writes and targeted preparation time;
report all browser regressions as well as improvements. A small I/O improvement
must not be marketed as faster startup or lower memory without supporting browser
measurements. Consistent material regression outside observed baseline variation
requires rejection or a justified benefit. No Firefox comparison is performed.

The baseline below was recorded before any product changes. Candidate results and
final decision will follow in this same Phase 4 branch.

## Reproduction

The host already supplies Xorg with the dummy driver. No new browser engine or
unofficial binary is downloaded. Start an isolated display in a separate shell:

```sh
mkdir -p /workspace/aelthoren-benchmarks
python3 - <<'PY'
import secrets, subprocess
subprocess.run(['xauth', '-f', '/workspace/aelthoren-benchmarks/Xauthority',
                'add', ':97', '.', secrets.token_hex(16)], check=True)
PY
/usr/lib/xorg/Xorg :97 -config /workspace/Aelthoren/config/xorg-benchmark.conf \
  -logfile /workspace/aelthoren-benchmarks/Xorg.log \
  -auth /workspace/aelthoren-benchmarks/Xauthority \
  -nolisten tcp -noreset -novtswitch -seat aelthoren-benchmark
```

Display access control is enabled, TCP listening disabled. Same-user local clients
may also be authorized by Xorg; the authority file is never committed. Both
conditions use the same running display, native build and artifact files.

```sh
python3 tools/benchmark_phase4.py baseline
python3 tools/benchmark_launcher_io.py baseline
# Preserve baseline before applying the candidate.
python3 tools/benchmark_phase4.py candidate
python3 tools/benchmark_launcher_io.py candidate
python3 tools/summarize_phase4.py
```

Stage files refuse overwrite. Raw JSON measurements are intentional evidence in
docs/phase4; browser logs, profiles, authority and temporary fixtures stay outside
Git in /workspace/aelthoren-benchmarks and /workspace/aelthoren-user-data. Socket/
display operations need approved execution outside the Codex command sandbox.
Use the correct source revision for each stage; do not run both against the final
optimized code and call the first one a baseline. The targeted preparation timing
uses disposable files, seven batches of 200 repetitions, without fsync; it excludes
the full provenance guard and browser initialization.

## Preserved baseline checkpoint

Six complete browser runs (three fresh-profile/warm pairs), all orderly exit 0.

- profile-cold first-page responsive: median 2037.42 ms, range 1922.03–2152.90 ms, n=3.
- warm first-page responsive: median 1525.75 ms, range 1335.86–1541.58 ms, n=3.
- All six launches rewrote five unchanged managed files.
- Full per-run resource, process, network and latency data: docs/phase4/baseline.json.
- Targeted buffered-I/O preparation measurements: baseline-launcher.json.
- Product source, privacy configuration, source pin and official logo hashes: baseline-input-hashes.json.

Initial incomplete harness attempts were excluded. They exposed content/chrome
automation context assumptions, transient handles during privileged-page process
changes and history assertions depending on restored warm-profile state. The final
protocol uses native closure, a scratch new-tab tab and explicit history URLs.
Failed logs/partial data remain outside Git in /workspace/aelthoren-benchmarks;
no incomplete attempt is included in the six-run baseline.
