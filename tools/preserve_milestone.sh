#!/usr/bin/env bash
set -euo pipefail
project_root=$(git rev-parse --show-toplevel)
cd "$project_root"
if [ -n "$(git status --porcelain)" ]; then
    echo 'Stop: commit/preserve outstanding work before milestone publication.' >&2
    exit 1
fi
branch=$(git symbolic-ref --quiet --short HEAD)
case "$branch" in
    codex/*) ;;
    *) echo 'Stop: use an explicit codex/ development branch.' >&2; exit 1 ;;
esac
remote=$(git remote get-url --push origin)
case "$remote" in
    https://github.com/Evan-Windproof/Aelthoren|https://github.com/Evan-Windproof/Aelthoren.git) ;;
    *) echo 'Stop: origin push URL is not the expected HTTPS repository.' >&2; exit 1 ;;
esac
local_sha=$(git rev-parse 'HEAD^{commit}')
git push -u origin "HEAD:refs/heads/$branch"
remote_sha=$(git ls-remote --exit-code origin "refs/heads/$branch" | cut -f1)
if [ "$local_sha" != "$remote_sha" ]; then
    echo 'Stop: remote SHA differs from local HEAD; publication is unverified.' >&2
    exit 1
fi
printf 'Verified remote commit: https://github.com/Evan-Windproof/Aelthoren/commit/%s\n' "$local_sha"
printf 'Branch: %s\n' "$branch"
