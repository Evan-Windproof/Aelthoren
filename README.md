# Aelthoren

**Lightweight. Private. Account-free.**

Aelthoren is a planned independent desktop browser based on genuine Mozilla
Firefox, Gecko and SpiderMonkey. Development starts on Linux; Windows support is
planned. C++ is the primary long-term language alongside required upstream Rust,
JavaScript and other languages. The owner's official logo is preserved unchanged
in assets/A_text.svg.

This restart rebuilds **Phase 1 only**: a reproducibly pinned, real Firefox artifact
development environment. It uses official precompiled Gecko plus locally assembled
browser frontend resources, not local engine compilation or a simulated browser.
The development browser retains upstream identity; Phase 2 branding is not included.
See [VALIDATION.md](VALIDATION.md) for this run's actual build/rendering results.

```sh
python3 tools/prepare_phase1.py
python3 tools/browser.py build
python3 tools/browser.py run
```

See [BUILDING.md](BUILDING.md) for prerequisites, verification, paths and preservation.
Binary/source caches and profiles live outside this Git repository. Every completed
milestone is committed and pushed to codex/aelthoren-restart and verified on GitHub;
existing PR #1 is updated, not replaced.

Planned product behavior includes DuckDuckGo, no integrated account/cloud sync,
local-first data and privacy defaults. **Those changes are not implemented here**:
the current upstream development browser still has inherited account, sync and
remote-service behavior. The slogan states intended goals, not a current privacy
or performance guarantee. No Gecko security mechanisms are deliberately disabled.

Aelthoren is independent of Mozilla and is not endorsed by Mozilla. Keep upstream
copyright/license notices and do not redistribute modified builds under protected
Firefox branding. This is a development baseline, not a supported release.
See LICENSE, THIRD_PARTY_NOTICES.md and UPSTREAM.md.
