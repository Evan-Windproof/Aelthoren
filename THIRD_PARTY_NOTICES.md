# Attribution and licensing

Mozilla Firefox, Gecko and SpiderMonkey are Mozilla/contributor projects. Their
source, artifacts and dependencies retain their upstream MPL 2.0 and applicable
third-party licenses. They are not vendored or relicensed by this repository.
Preserve their source notices, license texts and about:license materials. Before
binary distribution, meet source-availability and other applicable obligations.
MPL text: https://www.mozilla.org/MPL/2.0/ . No noncommercial restriction is added.

Aelthoren is independent and not endorsed by Mozilla. A development artifact build
is not permission to distribute a modified browser under protected Firefox marks.
Aelthoren application-layer branding is implemented, but native identity and a
complete release trademark/source-availability review remain unfinished. Phase 5A
packages are internal development test artifacts, not public releases. This
classification does not change MPL or impose a noncommercial restriction.
The official Aelthoren SVG is owner supplied and unchanged; this project's MIT
license does not grant an asset/trademark redistribution license on the owner's behalf.

## Final branding resource overlay

`branding/artwork/neutral-browser.svg` is original Aelthoren project geometric
artwork (2026), under this repository's MIT LICENSE. No external icon library or
new downloaded artwork is used. Existing owner logo-derived raster/SVG resources
remain owner assets; confirm redistribution rights independently.

`branding/final-resources.json` and `tools/final_branding.py` describe exact
modifications to packaged Mozilla application resources; the package includes the
recipe and new artwork under source/ plus before/after hashes. Upstream covered
resources retain their applicable Mozilla/contributor licensing. Preserve MPL 2.0,
about:license, copyrights, corresponding source and dependency notices; this
repository's MIT license does not relicense them. Genuine third-party service,
compatibility, certificate-store and historical attribution names remain truthful.
See docs/BRANDING_AUDIT.md for official policy references and unresolved native
identity, source-availability, trademark and asset-rights gates. Passing regression
checks is not complete legal clearance for public redistribution.
