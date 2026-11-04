#!/usr/bin/env python3
"""Run the actual branded artifact browser with dedicated profile/process identity."""
import argparse
import configparser
from pathlib import Path
import subprocess

from phase2 import OBJECT, verify_overlay

PROFILE_ROOT = Path('/workspace/aelthoren-user-data/profiles')


def prepare_profile(name):
    import re
    if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
        raise ValueError('Use a profile name, not an arbitrary profile path')
    profile = PROFILE_ROOT / name
    if profile.resolve().parent != PROFILE_ROOT.resolve():
        raise ValueError('Profile path escapes Aelthoren storage')
    marker = profile / '.aelthoren-profile'
    if profile.exists() and any(profile.iterdir()) and not marker.is_file():
        raise ValueError('Refusing to adopt nonempty, unmarked profile data')
    profile.mkdir(parents=True, exist_ok=True)
    marker.write_text('Aelthoren development profile\n')
    return profile


def application_file():
    verify_overlay()
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    binary = OBJECT / 'dist/bin'
    config.read(binary / 'application.ini')
    config['App'].update(Name='Aelthoren', Vendor='Aelthoren', RemotingName='aelthoren', Profile='aelthoren')
    target = binary / 'browser/aelthoren-application.ini'
    import io
    data = io.StringIO()
    config.write(data, space_around_delimiters=False)
    if not target.exists() or target.read_text() != data.getvalue():
        temporary = target.with_suffix('.ini.tmp')
        temporary.write_text(data.getvalue())
        temporary.replace(target)
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='default')
    parser.add_argument('browser_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    rest = args.browser_args[1:] if args.browser_args[:1] == ['--'] else args.browser_args
    reserved = ('-profile', '--profile', '-p', '-profilemanager', '--profilemanager', '-app', '--app')
    if any(value.lower().split('=')[0] in reserved for value in rest):
        parser.error('Application/profile overrides are reserved for the launcher')
    app = application_file()
    profile = prepare_profile(args.profile)
    return subprocess.call([str(OBJECT / 'dist/bin/firefox'), '-app', str(app), '--no-remote', '-profile', str(profile), *rest])


if __name__ == '__main__':
    raise SystemExit(main())
