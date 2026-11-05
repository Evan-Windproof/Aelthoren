#!/usr/bin/env python3
"""Wrap Mozilla's official package as a relocatable, development-only Linux alpha."""
import argparse
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile

from phase2 import SOURCE, OBJECT, ROOT, LOCK, environment, verify_overlay

VERSION = '0.1.0-alpha'
NAME = 'aelthoren-' + VERSION
FILENAME = NAME + '-linux-x86_64.tar.xz'
PORTABLE_FILES = ['aelthoren', 'desktop-entry.py', 'ABOUT.html', 'README.txt', 'org.aelthoren.Browser.Alpha.desktop.in']


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=ROOT, text=True).strip()


def native_package(log):
    with log.open('w') as output:
        subprocess.run(['./mach', 'package'], cwd=SOURCE, env=environment(), stdout=output, stderr=subprocess.STDOUT, check=True)
    return OBJECT / 'dist/firefox-153.6.0.en-US.linux-x86_64.tar.xz'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('/workspace/aelthoren-packaging/output'))
    parser.add_argument('--mozilla-package', type=Path, help='Reuse a package just produced by ./mach package for this exact verified overlay')
    parser.add_argument('--allow-dirty-prototype', action='store_true', help='Explicitly mark an internal prototype; never use for final verified packages')
    args = parser.parse_args()
    verify_overlay()
    environment()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Keep binaries/staging outside the project repository')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / FILENAME
    if archive.exists() or archive.with_suffix(archive.suffix + '.partial').exists():
        raise ValueError('Preserve existing archive/partial output before rebuilding')
    official = args.mozilla_package.resolve() if args.mozilla_package else native_package(output / 'mach-package.log')
    official_hash = digest(official)
    revision = git('rev-parse', 'HEAD')
    dirty = bool(git('status', '--porcelain'))
    if dirty and not args.allow_dirty_prototype:
        raise ValueError('Commit/publish packaging inputs first, or explicitly request a dirty internal prototype')
    epoch = int(git('show', '-s', '--format=%ct', 'HEAD'))
    source_inputs = [ROOT / 'packaging/linux' / name for name in PORTABLE_FILES] + [ROOT / p for p in ['tools/package_linux.py', 'upstream.lock.json', 'config/privacy-policies.json', 'config/distribution.ini', 'LICENSE', 'THIRD_PARTY_NOTICES.md']]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in source_inputs}
    with tempfile.TemporaryDirectory(prefix='alpha-stage-', dir=output.parent) as temporary:
        stage = Path(temporary) / NAME
        stage.mkdir()
        extracted = Path(temporary) / 'mozilla'
        extracted.mkdir()
        with tarfile.open(official, 'r:xz') as source:
            members = source.getmembers()
            if any(not (m.name == 'firefox' or m.name.startswith('firefox/')) for m in members):
                raise ValueError('Unexpected Mozilla package root')
            source.extractall(extracted, filter='data')
        shutil.move(extracted / 'firefox', stage / 'runtime')
        runtime = stage / 'runtime'
        for path in runtime.rglob('*'):
            if path.is_symlink():
                if path.resolve().is_relative_to(runtime.resolve()):
                    continue
                raise ValueError('Runtime symlink escapes application: ' + str(path))
        for name in ['firefox', 'libxul.so']:
            if digest(runtime / name) != digest(OBJECT / 'dist/bin' / name):
                raise ValueError('Native package binary differs from verified build: ' + name)
        original = configparser.ConfigParser(interpolation=None)
        original.optionxform = str
        original.read(runtime / 'application.ini')
        if original['App']['Version'] != LOCK['version'].removesuffix('esr'):
            raise ValueError('Packaged native version differs from pin')
        if original['App']['BuildID'] != config_build_id():
            raise ValueError('Packaged build ID differs from current artifact build')
        original['App'].update(Name='Aelthoren', Vendor='Aelthoren', RemotingName='aelthoren-alpha', Profile='aelthoren-alpha')
        original['XRE']['EnableProfileMigrator'] = '0'
        appfile = runtime / 'browser/aelthoren-application.ini'
        with appfile.open('w') as stream:
            original.write(stream, space_around_delimiters=False)
        distribution = runtime / 'distribution'
        distribution.mkdir(exist_ok=True)
        for source, name in [('config/privacy-policies.json', 'policies.json'), ('config/distribution.ini', 'distribution.ini')]:
            shutil.copyfile(ROOT / source, distribution / name)
        for name in PORTABLE_FILES:
            shutil.copyfile(ROOT / 'packaging/linux' / name, stage / name)
        for source, name in [('LICENSE', 'LICENSE'), ('THIRD_PARTY_NOTICES.md', 'THIRD_PARTY_NOTICES.md')]:
            shutil.copyfile(ROOT / source, stage / name)
        icon = runtime / 'browser/chrome/icons/default/default128.png'
        if not icon.is_file():
            raise ValueError('Official Aelthoren branding icon absent from Mozilla package')
        shutil.copyfile(icon, stage / 'icon.png')
        licenses = stage / 'licenses'
        licenses.mkdir()
        shutil.copyfile(SOURCE / 'LICENSE', licenses / 'Mozilla-LICENSE.txt')
        shutil.copyfile(SOURCE / 'toolkit/content/license.html', licenses / 'Mozilla-third-party-license.html')
        patchdir = stage / 'source/patches'
        patchdir.mkdir(parents=True)
        for path in sorted((ROOT / 'patches').glob('*.patch')):
            shutil.copyfile(path, patchdir / path.name)
        (stage / 'SOURCES.md').write_text(f'''# Source availability and provenance\n\nDevelopment-only internal alpha; not a public release or completed compliance review.\n\nUpstream repository: {LOCK['repository']}\nRelease tag: {LOCK['tag']}\nExact Gecko/SpiderMonkey source revision: {LOCK['revision']}\nArtifact task: {LOCK['artifact_task']}\n\nAelthoren source and build/packaging scripts:\nhttps://github.com/Evan-Windproof/Aelthoren/tree/{revision}\nProject working tree modified at packaging: {dirty}\nExact packaging input hashes: package.json.\nMPL-covered application patches are also bundled in source/patches; apply them to\nthe exact upstream revision with the branding generator in the Aelthoren source.\nPreserve MPL and all third-party notices. Original independent scripts use LICENSE;\nthat MIT notice does not relicense upstream covered code or grant trademark rights.\nThe complete upstream tree contains the covered/dependency sources; runtime\nabout:license and licenses/ retain applicable notices. Before public redistribution,\nreview every applicable source-availability and trademark/asset obligation; links\nand internal validation alone are not a declaration that all obligations are met.\n''')
        dependencies = dependency_report(runtime)
        (stage / 'RUNTIME-DEPENDENCIES.txt').write_text(dependencies)
        metadata = {'product':'Aelthoren','version':VERSION,'platform':'linux-x86_64','distribution_class':'development-only-internal-test','public_release':False,'signed':False,'engine_version':LOCK['version'],'engine_revision':LOCK['revision'],'artifact_task':LOCK['artifact_task'],'native_application_version':original['App']['Version'],'native_guid':original['App']['ID'],'native_guid_inherited':True,'native_build_id':original['App']['BuildID'],'desktop_id':'org.aelthoren.Browser.Alpha','profile_root':'${XDG_DATA_HOME:-$HOME/.local/share}/aelthoren-alpha/profiles','project_revision':revision,'project_dirty':dirty,'source_date_epoch':epoch,'mozilla_package_sha256':official_hash,'packaging_inputs':hashes,'production_blockers':['Native GUID/version/executable metadata remain inherited','Complete Mozilla trademark and dependency/source-availability review pending','Independent signing/security-update delivery not established','Distribution compatibility is limited to actual recorded tests']}
        (stage / 'package.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
        lines=[]
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                lines.append(digest(path) + '  ' + str(path.relative_to(stage)))
        (stage / 'MANIFEST.sha256').write_text('\n'.join(lines) + '\n')
        temporary_archive = archive.with_suffix(archive.suffix + '.partial')
        with tarfile.open(temporary_archive, 'w:xz', preset=6, format=tarfile.PAX_FORMAT) as tar:
            for path in [stage] + sorted(stage.rglob('*')):
                info = tar.gettarinfo(str(path), arcname=str(path.relative_to(stage.parent)))
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                info.mtime = epoch
                info.pax_headers = {}
                info.mode = 0o755 if path.is_dir() or path.name in ['aelthoren', 'desktop-entry.py'] or (path.is_file() and os.access(path, os.X_OK)) else 0o644
                if info.isfile():
                    with path.open('rb') as stream:
                        tar.addfile(info, stream)
                else:
                    tar.addfile(info)
        temporary_archive.replace(archive)
    result = {'path':str(archive),'bytes':archive.stat().st_size,'sha256':digest(archive),'metadata':metadata}
    (output / (FILENAME + '.sha256')).write_text(result['sha256'] + '  ' + FILENAME + '\n')
    (output / 'package-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


def config_build_id():
    config = configparser.ConfigParser(interpolation=None)
    config.read(OBJECT / 'dist/bin/application.ini')
    return config['App']['BuildID']


def dependency_report(runtime):
    needed = set()
    versions = set()
    for path in sorted(runtime.rglob('*')):
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                continue
        dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
        needed.update(re.findall(r'Shared library: \[(.*?)\]', dynamic))
        symbols = subprocess.check_output(['readelf', '--version-info', str(path)], text=True)
        versions.update(re.findall(r'GLIBC_[0-9.]+', symbols))
    system = sorted(name for name in needed if not (runtime / name).exists())
    return 'ELF DT_NEEDED names not supplied at runtime root (plus their transitive dependencies):\n' + '\n'.join(system) + '\n\nObserved GLIBC symbol versions across packaged ELF files:\n' + '\n'.join(sorted(versions, key=lambda v:tuple(map(int,v.split('_')[1].split('.'))))) + '\n\nGTK 3/GLib, X11 or Wayland, fonts/fontconfig, ALSA and their OS dependencies remain system requirements. This is not a universal compatibility guarantee. See documented actual distro tests.\n'


if __name__ == '__main__':
    main()
