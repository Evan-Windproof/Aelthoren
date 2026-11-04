# Aelthoren

**Lightweight. Private. Account-free.**

Aelthoren is a planned independent desktop browser based on genuine Mozilla
Firefox, Gecko and SpiderMonkey. Development starts on Linux; Windows support is
planned. C++ is the primary long-term language alongside required upstream Rust,
JavaScript and other languages. The owner's official logo is preserved unchanged
in assets/A_text.svg.

Phase 2 now adds Linux development branding, an isolated launcher and a minimal
local new-tab/About interface to the verified Phase 1 artifact browser. Native
Gecko toolbar/address-bar/navigation/tab controls are retained. See
[docs/BRANDING.md](docs/BRANDING.md) for supported identity changes and limitations.

```sh
python3 tools/phase2.py prepare
python3 tools/phase2.py build
python3 tools/run_aelthoren.py
```

The original owner SVG remains unchanged. Configure, artifact installation and the
standard artifact build passed. Two real browser sessions passed HTTP JavaScript,
DOM, localStorage, tab/history and profile-isolation checks; new-tab/About/Settings
screenshots were inspected. This uses Mozilla's precompiled Gecko and SpiderMonkey,
not local engine compilation or a simulated browser. Native Firefox GUID and some
OS/trademark identity remain inherited. Use the launcher rather than the raw binary.

See [VALIDATION.md](VALIDATION.md) for exact results. Development continues on
codex/aelthoren-restart; Phase 1 PR #1 is closed/merged. Each completed milestone is
pushed and its remote SHA verified; no environment snapshot is treated as Git backup.

Planned product behavior includes DuckDuckGo, no integrated account/cloud sync,
local-first data and privacy defaults. **Those Phase 3 changes are not implemented here**:
the current upstream development browser still has inherited account, sync and
remote-service behavior. The slogan states intended goals, not a current privacy
or performance guarantee. No Gecko security mechanisms are deliberately disabled.

Aelthoren is independent of Mozilla and is not endorsed by Mozilla. Keep upstream
copyright/license notices and do not redistribute modified builds under protected
Firefox branding. This is a development baseline, not a supported release.
See LICENSE, THIRD_PARTY_NOTICES.md and UPSTREAM.md.
