# Upstream provenance

- Firefox ESR: 153.6.0esr
- Repository: https://github.com/mozilla-firefox/firefox.git
- Release tag: FIREFOX_153_6_0esr_RELEASE
- Git revision: a34c4160e3f75ab9918fbe4669ff7ae56f1977c8
- Official Linux artifact task: YlYD4FnWSXGLhOw9Il8lig
- Index: gecko.v2.mozilla-esr153.shippable.revision.a34c4160e3f75ab9918fbe4669ff7ae56f1977c8.firefox.linux64-opt

The restart reuses the previously verified source/release. Check upstream.lock.json
for exact file hashes/sizes. The official Git-revision index associates the task
with this revision; build metadata also uses a Mercurial source stamp. Do not
claim that an independent full Git/Mercurial history conversion was performed.

Keep the pin fixed for normal builds. For a deliberate update, check current ESR
support and security advisories, record the new source/tag/task/hashes in a reviewed
commit, then repeat build/rendering and relevant upstream tests before distribution.
https://www.mozilla.org/security/known-vulnerabilities/firefox-esr/
An old reviewed pin does not prove continuing support; applicable security fixes
must be incorporated. No source patches or branding changes are applied in Phase 1.
