#!/usr/bin/env python3
"""Prepare the reviewed privacy overlay and build the official artifact target."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

import phase2
from privacy import install_policies

OUTPUT = phase2.ROOT / 'docs/phase3'


def prepare():
    if not phase2.BRAND.exists():
        phase2.prepare()
        return
    marker_path = phase2.BRAND / '.aelthoren-overlay.json'
    marker = json.loads(marker_path.read_text())
    revision = subprocess.check_output(['git','-C',str(phase2.SOURCE),'rev-parse','HEAD'],text=True).strip()
    if revision != phase2.LOCK['revision'] or marker['revision'] != revision:
        raise ValueError('Preserve source: wrong upstream revision')
    # Validate every existing byte before upgrading a known Phase 2 overlay.
    previous = marker['patched']
    changed = subprocess.check_output(['git','-C',str(phase2.SOURCE),'diff','--name-only','HEAD'],text=True).splitlines()
    if marker['files'] != phase2.content_hashes() or sorted(changed) != sorted(previous) or previous != {p:phase2.digest(phase2.SOURCE/p) for p in previous}:
        raise ValueError('Unreviewed source/branding changes; nothing overwritten')
    if marker['inputs'] == phase2.inputs():
        phase2.verify_overlay()
        print('Current Phase 3 overlay verified')
        return
    old_files = phase2.PATCHED[:2]
    if sorted(previous) != sorted(old_files):
        raise ValueError('Only a verified Phase 2 overlay can be upgraded; preserve and review newer changes')
    for p in ['assets/A_text.svg','patches/0001-phase2-ui.patch']:
        if marker['inputs'][p] != phase2.inputs()[p]:
            raise ValueError('Phase 2 base/logo differs; preserve and review')
    for name in ['0002-phase3-search.patch','0003-phase3-account-settings.patch']:
        patch = phase2.ROOT / 'patches' / name
        subprocess.run(['git','-C',str(phase2.SOURCE),'apply','--check',str(patch)],check=True)
        subprocess.run(['git','-C',str(phase2.SOURCE),'apply',str(patch)],check=True)
    for source in (phase2.ROOT / 'branding/content').iterdir():
        shutil.copyfile(source,phase2.BRAND/'content'/source.name)
    marker = {'revision':revision,'inputs':phase2.inputs(),'files':phase2.content_hashes(),'patched':{p:phase2.digest(phase2.SOURCE/p) for p in phase2.PATCHED}}
    marker_path.write_text(json.dumps(marker,indent=2)+'\n')
    phase2.verify_overlay()
    print('Verified Phase 2 overlay upgraded; source HEAD and original logo preserved')


def build():
    OUTPUT.mkdir(exist_ok=True)
    for arguments,name in [(['--no-interactive','configure'],'configure'),(['artifact','install'],'install'),(['build'],'build')]:
        with (OUTPUT/(name+'.log')).open('w') as log:
            result = subprocess.run(['./mach',*arguments],cwd=phase2.SOURCE,env=phase2.environment(),stdout=log,stderr=subprocess.STDOUT)
        print(name,'exit',result.returncode,flush=True)
        if result.returncode:
            return result.returncode
    print('Installed',install_policies(phase2.OBJECT/'dist/bin'))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','build'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
        return 0
    return build()


if __name__ == '__main__':
    raise SystemExit(main())
