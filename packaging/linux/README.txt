Aelthoren 0.1.0-alpha / Linux x86_64 / DEVELOPMENT-ONLY TEST ARTIFACT

Extract the archive into a writable user-selected directory, then run:
  ./aelthoren
  ./aelthoren --about
  ./aelthoren --version
  ./aelthoren --profile second
  ./aelthoren -- --private-window
No root, Firefox source, Git, compiler, Python or Codex tools are required to launch.
Do not run the runtime/firefox binary directly: the wrapper selects Aelthoren's
application data, disables remoting and isolates its profile from Firefox.

Optional desktop integration (requires system Python 3):
  python3 desktop-entry.py install
  python3 desktop-entry.py remove
It writes only your XDG_DATA_HOME/applications directory, does not set a default
browser, and generates paths for this exact extraction directory (including spaces).
After moving the directory, rerun install. Do not install system-wide automatically. Because --no-remote is retained, URL
forwarding into an already-running alpha profile is not supported; a second launch
can report a profile lock. Do not set this alpha as your default browser.

Profiles: ${XDG_DATA_HOME:-$HOME/.local/share}/aelthoren-alpha/profiles/<name>
Only ASCII letters, digits, underscores and hyphens are accepted as profile names.
An existing unmarked nonempty profile is refused. Ordinary Firefox profiles are
not imported. Removing the extracted application does not erase profile data.
To remove all alpha data, first exit every instance, back up needed data and
manually remove ONLY your aelthoren-alpha data directory if desired.

System runtime dependencies (not bundled): x86_64 Linux with glibc >= 2.34,
compatible libstdc++/libgcc, GTK 3, GLib/GIO, X11 or Wayland libraries, fontconfig,
FreeType/fonts, ALSA and the ordinary GTK/X11 dependency chain. Headless still
requires native shared libraries. See RUNTIME-DEPENDENCIES.txt and docs/LINUX_RELEASE.md
in the source repository for actual tested distributions and limitations.

Privacy defaults/Gecko security protections are retained. Browser accounts/Sync
and telemetry uploads are disabled; DuckDuckGo is the changeable initial provider.
Mozilla/security/component services can still connect. This does not provide
anonymity, guaranteed security updates or compatibility with every website.

Engine: Firefox ESR 153.6.0esr, source a34c4160e3f75ab9918fbe4669ff7ae56f1977c8.
Product alpha version is 0.1.0-alpha; native engine/application version stays
153.6.0 for compatibility. This is not a fully independent branded native release.
No automatic safe production update channel is provided. Do not use for sensitive
or general browsing. Keep the upstream security assessment current before use.

Required Mozilla/third-party notices remain in runtime about:license and licenses/.
Original Aelthoren code uses LICENSE; upstream covered code retains its own licenses.
The owner's logo is not permission to use Aelthoren/Mozilla trademarks elsewhere.
See SOURCES.md for exact upstream and modified application-source availability.
No public downloadable release is implied by the existence of this local archive.
