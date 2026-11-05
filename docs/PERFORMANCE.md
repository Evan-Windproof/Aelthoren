# Phase 4 performance and lightweight optimization

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
session; per-session medians are compared rather than treating all inner
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

A bounded open/switch/close cycle checks JS, DOM, localStorage, history and orderly
exit. A separate desktop regression checks a timer while its tab is in background. Memory after closure is not proof of a leak
or its absence: Gecko legitimately retains processes/caches and manages its own GC.

Candidate acceptance: retain source/artifact/branding/privacy/security guards;
measure unchanged configuration/profile writes and targeted preparation time;
report all browser regressions as well as improvements. A small I/O improvement
must not be marketed as faster startup or lower memory without supporting browser
measurements. Consistent material regression outside observed baseline variation
requires rejection or a justified benefit. No Firefox comparison is performed.

The baseline was recorded and published before product changes. The final
comparison and decision are below.

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


## Final comparison — 2026-11-06 (Asia/Taipei)

Host logs use UTC 2026-11-05. E1 means the same Debian 13 x86_64 cloud host, four
CPU quota, 32 GiB limit, fixed Xorg dummy display and identical official artifact
browser described above. Baseline source is merged main 6ff8051; the baseline
checkpoint is [e413cfd](https://github.com/Evan-Windproof/Aelthoren/commit/e413cfd8a817f1c101d52714713c06b7e3b0a891).
Candidate was measured from that checkpoint with only tools/privacy.py and
tools/run_aelthoren.py changed. Exact file hashes are recorded in the two
*-input-hashes.json files. Source pin, privacy/default configuration and official
logo hashes match. Firefox executable and libxul.so match the pinned official
archive byte-for-byte; archive verification evidence is in artifact-verification.json.
No Gecko, Rust, WebIDL, frontend patch or process configuration changed. The same
existing Phase 3 artifact build was reused, not rebuilt between conditions.

Values are medians with [minimum, maximum] across sessions; nested tab/load trials
first become per-session medians. Resource rows have six sessions from three
paired profiles, not six fully independent profiles. Percent changes are relative
to the baseline median; lower is usually better, but counts/CPU windows are noisy.
CPU changes use percentage points, small network/process counts use absolute
changes. Median process counts can be fractional because six sessions are combined.

| Metric | Baseline median [min, max] | Candidate median [min, max] | Change | Repetitions/condition | Environment |
| --- | --- | --- | --- | --- | --- |
| Fresh profile → automation listener (ms) | 681.50 [634.69, 738.60] | 671.82 [651.54, 765.66] | -1.4% | 3 | E1 |
| Fresh profile → first-page responsive (ms) | 2037.42 [1922.03, 2152.90] | 2042.34 [1846.23, 2082.39] | +0.2% | 3 | E1 |
| Warm restart → automation listener (ms) | 629.57 [541.32, 656.48] | 684.82 [528.79, 697.52] | +8.8% | 3 | E1 |
| Warm restart → first-page responsive (ms) | 1525.75 [1335.86, 1541.58] | 1450.61 [1260.76, 1494.81] | -4.9% | 3 | E1 |
| Idle CPU (% of one core), 1 tab(s) | 3.25 [3.16, 3.54] | 3.23 [2.96, 4.72] | -0.02 pp | 6 | E1 |
| Summed RSS (MiB), 1 tab(s) | 992.18 [949.35, 1039.71] | 992.04 [950.48, 1033.25] | -0.0% | 6 | E1 |
| Process count, 1 tab(s) | 12.50 [12.00, 13.00] | 12.50 [12.00, 13.00] | +0.00 processes | 6 | E1 |
| HTTP attempts / 5-second window, 1 tab(s) | 36.50 [27.00, 50.00] | 34.50 [27.00, 46.00] | -2.00 attempts | 6 | E1 |
| Summed PSS (MiB), 1 tab(s) | 445.75 [438.11, 454.08] | 445.68 [437.15, 452.23] | -0.0% | 6 | E1 |
| Idle CPU (% of one core), 5 tab(s) | 2.66 [2.36, 3.91] | 2.45 [2.15, 4.10] | -0.20 pp | 6 | E1 |
| Summed RSS (MiB), 5 tab(s) | 1347.24 [1331.17, 1360.28] | 1349.24 [1335.14, 1358.11] | +0.1% | 6 | E1 |
| Process count, 5 tab(s) | 16.50 [16.00, 17.00] | 16.50 [16.00, 17.00] | +0.00 processes | 6 | E1 |
| HTTP attempts / 5-second window, 5 tab(s) | 2.00 [0.00, 5.00] | 4.00 [0.00, 5.00] | +2.00 attempts | 6 | E1 |
| Summed PSS (MiB), 5 tab(s) | 487.00 [485.81, 490.88] | 487.81 [484.88, 500.05] | +0.2% | 6 | E1 |
| Idle CPU (% of one core), 10 tab(s) | 1.57 [0.98, 2.74] | 1.96 [1.37, 2.55] | +0.39 pp | 6 | E1 |
| Summed RSS (MiB), 10 tab(s) | 1732.32 [1664.33, 1801.34] | 1729.71 [1660.14, 1803.79] | -0.2% | 6 | E1 |
| Process count, 10 tab(s) | 21.00 [21.00, 21.00] | 21.00 [21.00, 21.00] | +0.00 processes | 6 | E1 |
| HTTP attempts / 5-second window, 10 tab(s) | 0.00 [0.00, 8.00] | 0.00 [0.00, 0.00] | +0.00 attempts | 6 | E1 |
| Summed PSS (MiB), 10 tab(s) | 532.12 [510.75, 550.92] | 530.20 [510.82, 548.16] | -0.4% | 6 | E1 |
| Tab creation + navigation (ms) | 131.12 [116.40, 149.86] | 137.16 [114.90, 150.44] | +4.6% | 6 | E1 |
| Tab switch + two frames (ms) | 31.19 [30.77, 31.56] | 31.45 [31.11, 44.28] | +0.8% | 6 | E1 |
| Branded new-tab load (ms) | 65.50 [59.55, 70.60] | 66.06 [56.13, 80.50] | +0.9% | 6 | E1 |
| RSS after closing back to one tab (MiB) | 1069.17 [981.48, 1153.94] | 1067.62 [980.93, 1153.53] | -0.1% | 6 | E1 |
| Process count after closing back to one tab | 13.00 [12.00, 14.00] | 13.00 [12.00, 14.00] | +0.00 processes | 6 | E1 |
| Unchanged managed files rewritten per launch | 5.00 [5.00, 5.00] | 0.00 [0.00, 0.00] | -100.0% | 6 | E1 |
| Marked profile + configuration preparation (µs/pair) | 651.75 [552.67, 762.36] | 129.48 [122.24, 139.52] | -80.1% | 7 batches × 200 | E1 buffered filesystem |


### Decision and interpretation

Retain the narrow launcher I/O optimization. Previously every launch rewrote both
unchanged distribution files, their two SHA ownership markers and the existing
profile marker. The candidate reads and compares their actual bytes and the
expected ownership digest before skipping those writes. First installation,
changed configuration, marker repair, unknown-edit refusal, atomic replacement on
updates, named-profile restrictions and the full source/branding verification
remain. No cached trust decision substitutes for byte verification.

- Redundant rewrites fell **5 → 0** in every measured launch and the isolated
  preparation fixture. These are logical file updates, not a measured SSD-wear,
  physical-disk-write or energy estimate.
- Targeted buffered preparation fell **651.75 → 129.48 µs** per pair, **80.1%**
  (about **0.522 ms**). It excludes browser startup and the full provenance guard.
- Fresh-profile first-page responsiveness was **2037.42 → 2042.34 ms (+0.2%)**;
  warm responsiveness **1525.75 → 1450.61 ms (-4.9%)**. Ranges overlap; sequential
  order/shared-host/cache/network confounding and n=3 do not establish a general
  startup speed improvement.
- Memory is effectively unchanged: 10-tab PSS **532.12 → 530.20 MiB (-0.4%)**,
  summed RSS **1732.32 → 1729.71 MiB (-0.2%)**. Do not interpret double-counted
  RSS as private physical memory. Process medians stayed 12.5/16.5/21 at 1/5/10 tabs.
- Regressions are visible: warm listener readiness +8.8%, tab creation +4.6%,
  switching +0.8%, new-tab loading +0.9%, and 10-tab idle CPU +0.39 percentage
  points. Their distributions mostly overlap; one candidate switching-session
  median reached 44.28 ms versus a baseline maximum 31.56 ms. This is retained as
  an observed outlier, not omitted or declared an improvement. The small samples
  do not establish a consistent material runtime regression caused by the two
  pre-launch-only changes; longer randomized/interleaved trials are needed.
- Network activity remains variable. The 5-tab median rose 2 → 4 attempts per
  five-second window; these small counts have overlapping 0–5 ranges. No background
  network reduction is attributed to this startup-only patch. Remote Settings,
  connectivity, Push and update/component retries remain, with prior cloud failures.

The improvement claim is limited to redundant file operations and targeted
preparation time. **No measurable memory reduction, broad startup/CPU advantage or
comparison-based claim of being faster/lighter than Firefox is made.** Security
services/process isolation were not sacrificed for smaller numbers. No additional
optimization was justified by these measurements.

### Investigation and remaining work

The custom new-tab page already uses local script-free markup/CSS, a single logo,
no animations, no background polling and one document-bound search handler. No
additional persistent frontend object/cache/timer was introduced. The launcher
still performs its full pinned-source/branding guard; preliminary unmodified guard
samples were about 315–328 ms and it was not removed to improve startup numbers.

After reducing 11 open tabs back to one, summed RSS was 1069.17 → 1067.62 MiB and process
median 13 → 13 (range 12–14). Gecko retains processes and caches. This bounded
cycle does not prove a memory leak or its absence; no heap-retention or long-soak
study was performed, and GC/process counts were not forced. Fixtures are small
local workloads, not video, extensions or large production websites.

All 12 desktop benchmark sessions exited 0 and exercised real JS/DOM/localStorage,
native open/switch/close and history. Post-change verification reran all **25 Phase 3
browser checks**: provider choice/restart, account/Sync gates, tracking/exception,
partitioning, private browsing, local data/passwords, TLS positive/negative controls
and security configuration. **12 tooling tests passed**. A separate desktop test
kept a tab in the background for four seconds; its normal timer advanced 0 → 3,
then the browser exited 0. Evidence: regression-results.json. Raw regression/browser
logs and screenshots remain outside Git under the recorded evidence directory;
Phase 3 historical evidence is not overwritten.

Reproduce regressions with `python3 tools/verify_phase4.py` after the benchmark
(they share automation ports and must not run concurrently). Unit checks:
`python3 -m unittest discover -s tools -p 'test_*.py'`.

Future measurements should use a controlled dedicated host, randomized/interleaved
conditions, longer idle/soak windows, input-to-paint tools, realistic pages and,
where permitted, genuine OS-cold launches. Native allocator/process/engine changes
would require the appropriate full source build and independent security review;
none are implemented. Inherited cloud networking/update limitations remain as in
PRIVACY.md/VALIDATION.md. Phase 5 has not started.
