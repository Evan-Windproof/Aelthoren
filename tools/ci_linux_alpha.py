#!/usr/bin/env python3
"""CI adapter for the existing Phase 5A scripts; no browser behavior changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from prepare_phase1 import ROOT

WORK = Path('/workspace/aelthoren-actions')
ORIGINAL_SHA256 = 'b40b5a7538e0d62769917e3f439907027476ad43a0d5f23f1933ea4c81440495'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'build', 'package', 'report'])
    args = parser.parse_args()
    WORK.mkdir(exist_ok=True)
    if args.stage == 'prepare':
        from prepare_phase1 import main as acquire
        from phase3 import prepare
        acquire()
        prepare()
    elif args.stage == 'build':
        import phase3
        phase3.OUTPUT = WORK / 'logs/build'
        phase3.OUTPUT.mkdir(parents=True, exist_ok=True)
        raise SystemExit(phase3.build())
    elif args.stage == 'package':
        subprocess.run([sys.executable, str(ROOT / 'tools/package_linux.py'), '--output', str(WORK / 'package')], cwd=ROOT, check=True)
    else:
        metadata = json.loads((WORK / 'package/package-result.json').read_text())
        qa = json.loads((WORK / 'qa/results.json').read_text())
        if qa['result'] != 'PASS' or qa['uid'] == 0:
            raise ValueError('A real non-root standalone package verification must pass first')
        archive = Path(metadata['path'])
        with archive.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        if sha != metadata['sha256'] or archive.stat().st_size != metadata['bytes']:
            raise ValueError('Archive differs from packaging result')
        if metadata['metadata']['project_dirty']:
            raise ValueError('Do not export a dirty-working-tree prototype')
        report = {
            'classification': 'development-only; not a public release',
            'archive': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha,
            'original_sha256': ORIGINAL_SHA256, 'byte_identical_to_original': sha == ORIGINAL_SHA256,
            'package_source_commit': metadata['metadata']['project_revision'],
            'engine_version': metadata['metadata']['engine_version'],
            'engine_revision': metadata['metadata']['engine_revision'],
            'standalone_verification': qa['result'], 'verification_checks': len(qa['checks']),
            'verification_distribution': qa['distribution'], 'verification_headless': not qa['gui'],
            'run_id': os.environ.get('GITHUB_RUN_ID'), 'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
            'comparison_limit': 'Current source/provenance, native build ID, tools and dates can differ; this does not claim full-engine reproducibility.',
        }
        (WORK / 'package/comparison.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            with Path(summary).open('a') as output:
                output.write(f'''## Development-only Linux alpha export

- Archive: `{archive.name}`
- Size: **{report['bytes']:,} bytes**
- Inner archive SHA-256: `{sha}`
- Original SHA-256: `{ORIGINAL_SHA256}`
- Byte-identical to original: **{'YES' if report['byte_identical_to_original'] else 'NO'}**
- Standalone browser verification: **PASS**, {report['verification_checks']} checks, UID {qa['uid']}.
- Engine: {report['engine_version']}, `{report['engine_revision']}`.

Download the `aelthoren-linux-alpha-development` workflow artifact below, unzip the
Actions transport ZIP, then verify its included `.sha256` before extracting the
`.tar.xz`. Actions' ZIP digest is different from the inner archive digest above.
Requires GitHub sign-in/repository read access. Retention is 14 days; this is not a
GitHub Release or a supported production browser. Native identity, signing,
security-update delivery and redistribution compliance gates remain unfinished.
''')


if __name__ == '__main__':
    main()
