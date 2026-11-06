# Security

Aelthoren is an experimental Firefox ESR artifact-based browser frontend. Gecko
and SpiderMonkey are official checksum-pinned Mozilla binaries, not engines
compiled locally. The source revision and artifact provenance remain recorded in
upstream.lock.json and UPSTREAM.md. No supported release, independent update
service, signing, incident-response SLA or complete security audit is claimed.

Keep TLS certificate verification, content sandboxing, Fission/process isolation,
Safe Browsing and upstream exploit mitigations enabled. Phase 3 changes product
policies, distribution defaults and a narrowly scoped browser application actor;
it does not patch these mechanisms or trade them for memory/network reductions.
Never disable TLS verification, accept all certificates or disable sandboxing to
make cloud builds/tests pass. Review security advisories and upstream maintenance
before any public release; a pinned revision is reproducible but does not update
itself. Native identity and release/update infrastructure still require full-source
build and distribution work. Mozilla trademarks/licenses remain applicable.

The new-tab search actor checks the current top-level document against about:newtab
and about:home, validates a bounded textual query and obtains the submission through
Mozilla SearchService. It accepts no page-supplied URL and only navigates to an
HTTP(S) provider URI. Preserve these checks on rebase. The bundled page uses a
restrictive script-free CSP; the existing privileged Mozilla actor handles form
submission. Ordinary websites gain no new actor entry point or elevated interface.

Accounts/telemetry policies intentionally disable those product services; ordinary
search/tracking preferences remain editable. Local profile segregation prevents
accidental adoption of Firefox data, but is not OS-level filesystem isolation or
encryption. Only use the supported launcher. Downloaded artifacts and user profiles
remain outside Git. SHA-256/official HTTPS metadata checks must not be bypassed.

Tests use dedicated disposable profiles and loopback servers. Privileged Marionette
requires the explicit test-only `--remote-allow-system-access` flag; it is never
added to normal launches. `remote.prefs.recommended=false` prevents automation from
disabling real Safe Browsing/private tracking defaults. A local test CA is installed
only into that test profile, with a separate untrusted-certificate negative control.
Keys and profiles are not committed. Temporary DNS and narrowly scoped proxy
exclusions map fixture hosts to loopback only; no remote service restriction is
bypassed. The exact pinned Mozilla classifier helper is mapped as a test-only
resource and cleaned up after the tracking test. These are not product defaults.

See VALIDATION.md for observed results. Preference checks and rendering tests do
not prove sandbox enforcement against exploits, complete tracker coverage, working
security update delivery or all remote-service paths. Inherited network failures
and upstream diagnostics are disclosed in PRIVACY.md. Avoid sensitive browsing
with this development build. Report security issues privately through GitHub's
private vulnerability reporting if enabled; do not post secrets in a public issue.
For upstream vulnerabilities, use Mozilla's published security reporting process.


## Linux alpha distribution status

Phase 5A produces development-only test packages. Native Firefox GUID/version and
some executable/update/crash identity remain inherited; supported name/profile/
remoting overrides do not establish a fully independent native release. Runtime
launch uses an explicit user-local profile and disables remoting/automatic profile
migration, never root or relaxed sandbox/TLS flags. Source tree/Codex tools are not
runtime dependencies. Desktop integration is optional, per-user and never changes
the default browser automatically.

Before any external distribution, recheck current Mozilla ESR metadata/advisories,
review asset/trademark and every dependency/source obligation, establish independent
signing and tested security-update delivery, and satisfy RELEASE_CHECKLIST.md.
The 2026-11-05 UTC vendor snapshot lists the pin 153.6.0esr as current ESR and MFSA
2026-120 as fixed in 153.6, but also schedules the next release for 2026-11-06. It
is not a future security guarantee. Do not use an unsupported/vulnerable engine for
general browsing or describe this unreviewed alpha as safe.

Maintain security updates by monitoring official advisories/version metadata; on a
security release, separately update exact upstream tag/commit/task/archive hashes,
rebase/review the small frontend patches, rebuild/package, repeat clean Linux GUI/
headless and privacy/TLS/sandbox tests, preserve sources/notices, sign/verify and
replace through an explicitly tested delivery mechanism. Do not assume Mozilla's
Firefox update server safely updates modified Aelthoren builds, or disable update
checks to hide errors. Current cloud remote-service/update limitations remain.

QA-only proxy CA trust and privileged automation stay in disposable test profiles,
not in the archive. Public HTTPS is tested through the configured proxy with TLS
verification enabled; untrusted local certificates must still fail. Container
seccomp and Firefox's additional content filters/NoNewPrivs are inspected; this is
not a complete exploit or user-namespace enforcement audit.

Final clean Debian/Ubuntu headless and X11 GUI tests passed with the active web
process adding a seccomp filter and NoNewPrivs, while TLS rejected an untrusted
certificate. Outer container policy denies some user-namespace creation; do not
interpret preference values/process labels as a complete sandbox-enforcement audit.
Only active initialized web-process state is asserted; initializing spare processes
are retained in diagnostic snapshots. No protections were lowered to pass.
The inherited generic Settings “latest/safest” text is not an Aelthoren update/
security guarantee; it remains a public-release copy/identity gate. The package
is development-only despite the point-in-time current ESR metadata match.
