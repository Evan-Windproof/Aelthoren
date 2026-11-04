# Mandatory GitHub milestone preservation

The previous local history was unavailable after a cloud environment restore.
Every new completed milestone must therefore be pushed and remotely verified
before it is treated as preserved. Publishing an environment is not a substitute.

## Verified restart baseline

- Repository: https://github.com/Evan-Windproof/Aelthoren
- Default branch: main
- Initial local/remote commit: 2afaec7a14ff6db1d98b5de67cc803a81e39503b
- Development branch: codex/aelthoren-restart
- An actual normal push created this branch successfully before implementation.
- GitHub repository API reported push permission; PR capability is tested by the
  preservation checkpoint's draft PR. The assistant reports its actual URL.

No earlier implementation is recreated or claimed recovered by this checkpoint.
The original README is unchanged; browser work starts in later milestones.

## Repeat for each milestone

```sh
git status --short --branch
git diff --stat
git diff --cached
# Review intended files and new history for archives, binaries and credentials.
# Run relevant checks, then explicitly stage only intended project files.
git add <reviewed-files>
git commit -m "Describe the completed milestone"
./tools/preserve_milestone.sh
```

The helper does not stage, commit, force-push, merge or change implementation.
It refuses dirty checkouts, non-development branches and an unexpected remote.
It pushes normally, then compares local HEAD with the advertised remote SHA.
Run network commands through the configured proxy and approved execution context
where required. Never disable TLS or extract platform credentials.

Create a PR with gh pr create --draft --base main --head <branch> --body-file FILE,
or update an existing PR; recheck the default branch if repository settings change.
Future tasks should fetch and reuse pushed work rather than assume cloud snapshots
retain local commits. Do not merge or publish releases without authorization.

## If publication fails

Stop implementation and retain the current checkout. On the development branch:

```sh
git bundle create /workspace/aelthoren-milestone.bundle HEAD
git bundle verify /workspace/aelthoren-milestone.bundle
```

The bundle includes commit ancestry. Audit it for prohibited content and obtain an
independent copy before leaving the environment; creating it on the same disk alone
is insufficient. Report the branch, full SHA, failed command and precise error.
Do not reset, force-push or rewrite history. No secret values belong in diagnostics.
