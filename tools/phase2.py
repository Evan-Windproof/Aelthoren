#!/usr/bin/env python3
"""Prepare/build the isolated Aelthoren frontend overlay without engine changes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from prepare_phase1 import DOWNLOADS, LOCK, ROOT, SOURCE, verify

BRAND = SOURCE / 'browser/branding/aelthoren'
OBJECT = SOURCE / 'obj-aelthoren-phase2'
OUTPUT = ROOT / 'docs/phase2'
PATCHED = ['browser/components/newtab/AboutNewTabRedirector.sys.mjs', 'browser/locales/en-US/browser/aboutDialog.ftl', 'browser/actors/AboutNewTabChild.sys.mjs', 'browser/actors/AboutNewTabParent.sys.mjs', 'browser/components/preferences/preferences.js']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    paths = [ROOT / 'assets/A_text.svg', ROOT / 'patches/0001-phase2-ui.patch', ROOT / 'patches/0002-phase3-search.patch', ROOT / 'patches/0003-phase3-account-settings.patch', Path(__file__)] + sorted((ROOT / 'branding/content').iterdir())
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def content_hashes():
    return {str(p.relative_to(BRAND)): digest(p) for p in BRAND.rglob('*') if p.is_file() and p.name != '.aelthoren-overlay.json'}


def verify_overlay():
    if subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() != LOCK['revision']:
        raise ValueError('Source HEAD differs from pin')
    marker = json.loads((BRAND / '.aelthoren-overlay.json').read_text())
    if marker['inputs'] != inputs() or marker['files'] != content_hashes():
        raise ValueError('Overlay modified; preserve it and review before rebuilding')
    changed = subprocess.check_output(['git', '-C', str(SOURCE), 'diff', '--name-only', 'HEAD'], text=True).splitlines()
    if sorted(changed) != sorted(PATCHED) or marker['patched'] != {p: digest(SOURCE / p) for p in PATCHED}:
        raise ValueError('Unexpected upstream modifications')


def prepare():
    if BRAND.exists():
        verify_overlay()
        print('Existing overlay verified; nothing overwritten')
        return
    if subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() != LOCK['revision']:
        raise ValueError('Wrong source revision')
    subprocess.run(['git', '-C', str(SOURCE), 'diff', '--quiet', 'HEAD'], check=True)
    patch = ROOT / 'patches/0001-phase2-ui.patch'
    subprocess.run(['git', '-C', str(SOURCE), 'apply', '--check', str(patch)], check=True)
    shutil.copytree(SOURCE / 'browser/branding/unofficial', BRAND)
    svg = ET.parse(ROOT / 'assets/A_text.svg')
    svg.getroot().set('viewBox', '-57 -40 130 130')
    svg.getroot().set('width', '512')
    svg.getroot().set('height', '512')
    logo = BRAND / 'content/about-logo.svg'
    svg.write(logo, encoding='utf-8', xml_declaration=True)
    targets = {f'default{size}.png': size for size in (16, 22, 24, 32, 48, 64, 128, 256)}
    targets.update({'content/' + name: 384 if '@2x' in name else 192 for name in ('about-logo.png', 'about-logo@2x.png', 'about.png', 'about-logo-private.png', 'about-logo-private@2x.png')})
    for relative, size in targets.items():
        subprocess.run(['inkscape', str(logo), '--export-filename=' + str(BRAND / relative), '--export-width=' + str(size), '--export-height=' + str(size)], check=True, stdout=subprocess.DEVNULL)
    wordmark = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 88"><text x="0" y="42" font-family="sans-serif" font-size="40" fill="context-fill">Aelthoren</text><text x="1" y="75" font-family="sans-serif" font-size="17" fill="context-fill">Lightweight. Private. Account-free.</text></svg>\n'
    for name in ('about-wordmark.svg', 'firefox-wordmark.svg'):
        (BRAND / 'content' / name).write_text(wordmark)
    for name in ('brand.ftl', 'brand.properties'):
        p = BRAND / 'locales/en-US' / name
        p.write_text(p.read_text().replace('= Nightly', '= Aelthoren').replace('=Nightly', '=Aelthoren').replace('-brand-product-name = Firefox', '-brand-product-name = Aelthoren'))
    p = BRAND / 'configure.sh'
    p.write_text(p.read_text().replace('MOZ_APP_DISPLAYNAME=Nightly', 'MOZ_APP_DISPLAYNAME=Aelthoren'))
    p = BRAND / 'content/aboutDialog.css'
    p.write_text(p.read_text().replace('#130829', '#1b1b1b') + '\n#rightBox { background-size: 360px auto; }\n')
    for source in (ROOT / 'branding/content').iterdir():
        shutil.copyfile(source, BRAND / 'content' / source.name)
    p = BRAND / 'content/jar.mn'
    p.write_text(p.read_text() + ''.join('  content/branding/' + name + '\n' for name in ('newtab.html', 'about-aelthoren.html', 'aelthoren.css')) + '% resource aelthoren %content/branding/\n')
    subprocess.run(['git', '-C', str(SOURCE), 'apply', str(patch)], check=True)
    for name in ('0002-phase3-search.patch', '0003-phase3-account-settings.patch'):
        subprocess.run(['git', '-C', str(SOURCE), 'apply', '--check', str(ROOT / 'patches' / name)], check=True)
        subprocess.run(['git', '-C', str(SOURCE), 'apply', str(ROOT / 'patches' / name)], check=True)
    marker = {'revision': LOCK['revision'], 'inputs': inputs(), 'files': content_hashes(), 'patched': {p: digest(SOURCE / p) for p in PATCHED}}
    (BRAND / '.aelthoren-overlay.json').write_text(json.dumps(marker, indent=2) + '\n')
    verify_overlay()


def environment():
    import os
    verify_overlay()
    for item in LOCK['artifacts']:
        verify(DOWNLOADS / item['name'], item)
    env = dict(os.environ, MOZBUILD_STATE_PATH='/workspace/aelthoren-tools/mozbuild', MOZCONFIG=str(ROOT / 'config/mozconfig.linux-aelthoren'), NODEJS=shutil.which('node') or '', MOZ_ARTIFACT_FILE=':'.join(str(DOWNLOADS / i['name']) for i in LOCK['artifacts']))
    for key in ('MOZ_ARTIFACT_URL', 'MOZ_ARTIFACT_REVISION', 'MOZ_ARTIFACT_TASK', 'MOZ_ARTIFACT_TASK_LINUX64_OPT'):
        env.pop(key, None)
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'build'))
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    if args.command == 'prepare':
        prepare()
        return 0
    for arguments, name in [(['--no-interactive', 'configure'], 'configure'), (['artifact', 'install'], 'install'), (['build'], 'build')]:
        with (OUTPUT / (name + '.log')).open('w') as log:
            result = subprocess.run(['./mach', *arguments], cwd=SOURCE, env=environment(), stdout=log, stderr=subprocess.STDOUT)
        print(name, 'exit', result.returncode, flush=True)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
