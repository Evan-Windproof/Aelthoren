# Downloadable development alpha through GitHub Actions

The `Linux Alpha development artifact` workflow reproduces the Phase 5A workflow
on an Ubuntu 24.04 GitHub-hosted runner. It does not upload a Codex-local binary or
publish a GitHub Release. Browser behavior, owner branding, upstream.lock.json,
privacy configuration and the Phase 5A runtime packaging scripts are unchanged.

It acquires the exact pinned Mozilla source and three official artifacts with
the existing size/SHA/chain-of-trust checks, uses Mozilla's supported artifact-mode
bootstrap, runs the existing artifact build and official packaging scripts, then
extracts the generated archive in a non-root clean Debian container without a
source tree/Codex project mount. The existing standalone verification exercises
real public HTTPS and local JS/DOM/storage, TLS rejection, tabs/private browsing,
search/provider persistence, privacy gates and active web-process seccomp filters.
It never disables TLS/sandboxing or substitutes another engine. On a failed
Mozilla dependency download the job stops; no package is exported as successful.

The CI adapter only redirects build logs outside the tracked checkout (so the
existing clean-source packaging guard remains meaningful) and records comparison
metadata after successful runtime verification. The normal application and its
branding/configuration are not changed. Official GitHub-owned actions are pinned
to immutable commits and the repository token has contents-read permission only.
The built browser is still **development-only**, with all Phase 5A native identity,
update/signing, default-browser/URL-forwarding and redistribution limitations.

## Trigger and download

Pushing workflow/build changes on `codex/linux-alpha-actions-export` triggers a
run before merge. Once merged into main, use Actions → Linux Alpha development
artifact → Run workflow and choose the desired ref. The manual trigger normally
requires the workflow to be present on the default branch. No merge is automatic.

1. Open the repository's Actions tab and the specific successful run.
2. Check that its source commit and `Record actual checksum` step are the intended ones.
3. Under Artifacts, download **aelthoren-linux-alpha-development** while signed in
   to GitHub with repository read access. Artifacts expire after 14 days.
4. Unzip the Actions transport ZIP. This yields the `.tar.xz`, its `.sha256`,
   `package-result.json` and `comparison.json`.
5. In the extracted directory, run:

```sh
sha256sum -c aelthoren-0.1.0-alpha-linux-x86_64.tar.xz.sha256
tar -xJf aelthoren-0.1.0-alpha-linux-x86_64.tar.xz
cd aelthoren-0.1.0-alpha
./aelthoren
```

From a normally authenticated GitHub CLI:

```sh
gh run download RUN_ID --repo Evan-Windproof/Aelthoren --name aelthoren-linux-alpha-development --dir linux-alpha-download
```

`RUN_ID` must be the actual completed successful run reported in the PR/validation,
not an invented/example download URL. `linux-alpha-export-diagnostics` is a separate
log artifact, not the runnable browser. Profiles, keys, X authority and caches are
not uploaded. The artifact transport ZIP's GitHub digest is not the inner `.tar.xz`
checksum. Read `comparison.json` and the run summary for the inner checksum/size.

## Original archive comparison

Original workspace archive: 88,591,204 bytes, SHA-256
`b40b5a7538e0d62769917e3f439907027476ad43a0d5f23f1933ea4c81440495`.
The workflow computes its actual generated archive hash and a literal
`byte_identical_to_original` boolean. Source/provenance commit, native build ID,
source-date timestamp and system tools can differ from the original clean commit
4e59ba872ff7cfe059f617f98f28869ebf33e71f. Functional reproduction is not assumed to
imply byte identity; only measured output can establish that. No expected checksum
is substituted for the measured digest. No full-engine reproducibility is claimed.

Actual run outcome, dependency blockers, output bytes/SHA and exact run/artifact
links are recorded after execution. Until a run succeeds and the browser artifact
exists, this file is a workflow/download procedure, not a claim of an available
binary. The prior empty draft Release is not used by this export workflow.
