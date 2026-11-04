#!/usr/bin/env python3
"""Acquire/reuse the exact official source and checksum-pinned Linux artifacts."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/workspace/aelthoren-gecko')
DOWNLOADS = Path('/workspace/aelthoren-downloads')
LOCK = json.loads((ROOT / 'upstream.lock.json').read_text())


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(path, item):
    if path.stat().st_size != item['size'] or sha256(path) != item['sha256']:
        raise ValueError('Pinned size/SHA-256 mismatch: ' + str(path))


def verify_source():
    revision = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != LOCK['revision']:
        raise ValueError('Existing source differs from pin; preserve it and stop')
    subprocess.run(['git', '-C', str(SOURCE), 'diff', '--quiet', 'HEAD', '--'], check=True)
    return revision


def main():
    if not SOURCE.exists():
        subprocess.run(['git', 'init', str(SOURCE)], check=True)
        subprocess.run(['git', '-C', str(SOURCE), 'remote', 'add', 'origin', LOCK['repository']], check=True)
        subprocess.run(['git', '-C', str(SOURCE), 'fetch', '--depth=1', 'origin', LOCK['revision']], check=True)
        subprocess.run(['git', '-C', str(SOURCE), 'checkout', '--detach', 'FETCH_HEAD'], check=True)
    revision = verify_source()
    DOWNLOADS.mkdir(exist_ok=True)
    base = f"https://firefoxci.taskcluster-artifacts.net/{LOCK['artifact_task']}/0/public/"
    with urllib.request.urlopen(base + 'chain-of-trust.json', timeout=30) as response:
        cot_bytes = response.read()
    cot = json.loads(cot_bytes)
    if cot['taskId'] != LOCK['artifact_task']:
        raise ValueError('Wrong official artifact task')
    for item in LOCK['artifacts']:
        if cot['artifacts']['public/build/' + item['name']]['sha256'] != item['sha256']:
            raise ValueError('Official metadata conflicts with reviewed pin')
        target = DOWNLOADS / item['name']
        if target.exists():
            verify(target, item)
            print('Reused verified', item['name'], flush=True)
            continue
        temporary = target.with_suffix(target.suffix + '.partial')
        created = False
        try:
            if temporary.exists():
                raise ValueError('Preserve existing partial download: ' + str(temporary))
            with temporary.open('xb') as output, urllib.request.urlopen(base + 'build/' + item['name'], timeout=60) as response:
                created = True
                for data in iter(lambda: response.read(1024 * 1024), b''):
                    output.write(data)
            verify(temporary, item)
            temporary.rename(target)
        except Exception:
            if created:
                temporary.unlink(missing_ok=True)
            raise
        print('Verified', item['name'], item['sha256'], flush=True)
    (DOWNLOADS / 'chain-of-trust.json').write_bytes(cot_bytes)
    print('Source reused/pinned:', revision)


if __name__ == '__main__':
    main()
