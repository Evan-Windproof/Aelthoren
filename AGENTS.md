# Aelthoren development instructions

## Preserve every completed milestone on GitHub

The authoritative project repository is Evan-Windproof/Aelthoren. Local commits
and published cloud-environment snapshots alone are not durable preservation.

Before implementation in a new task, inspect status, history, branch and remotes;
read the current remote default branch and verify GitHub access. Reuse existing
checkouts and branches; do not reset, force-push or overwrite existing work.

For each completed milestone:

1. Review the complete staged diff and new Git objects. Keep Firefox/Gecko source
   trees, downloaded archives/binaries, build caches, user profiles, credentials
   and temporary files outside this repository. Owner branding and intentional
   documentation images are allowed; preserve licenses and attribution.
2. Run checks appropriate to that milestone and record actual results.
3. Commit on a development branch, then run tools/preserve_milestone.sh. A normal
   push must succeed and the exact remote branch SHA must equal local HEAD.
4. Create or update the milestone PR targeting the current default branch. Report
   the remote commit and PR links. Never claim work is preserved based only on a
   local commit or environment publication.
5. If publishing fails, stop accumulating implementation work. Report the exact
   blocker and prepare a complete Git bundle outside the repository. Arrange an
   independent copy before environment switching/publication; a bundle left only
   in the same cloud filesystem is not a durable backup.

Do not rewrite history to hide unwanted committed content. Stop and report it.
Never expose credential values or add them to Git. Use existing platform GitHub
credentials normally; do not infer missing access solely from an unset token.

## Technical direction

Use genuine Firefox/Gecko and SpiderMonkey, preserving upstream Rust/JavaScript
and required languages alongside long-term C++ work. Linux development first,
Windows later. Preserve Mozilla security mechanisms and licenses. Use the owner's
actual Aelthoren logo. Privacy goals include local-first settings, DuckDuckGo and
no integrated account/cloud sync; do not claim these features before implementing
and testing them. Work incrementally within the user's current phase and scope.
