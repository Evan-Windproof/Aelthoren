#!/usr/bin/env python3
"""Optional, explicit per-user desktop integration; never sets a default browser."""
import argparse
import os
from pathlib import Path
import tempfile

IDENTIFIER = 'org.aelthoren.Browser.Alpha.desktop'
OWNER = 'X-Aelthoren-Portable=true'


def exec_argument(value):
    return '"' + value.replace('\\', '\\\\\\\\').replace('"', '\\\\"').replace('`', '\\\\`').replace('$', '\\\\$').replace('%', '%%') + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'remove', 'print'])
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if any(c in str(root) for c in '\n\r\t'):
        raise ValueError('Desktop integration does not support control characters in extraction paths')
    data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    if not data.is_absolute():
        raise ValueError('XDG_DATA_HOME must be absolute')
    target = data / 'applications' / IDENTIFIER
    if target.is_symlink():
        raise ValueError('Refusing a symlinked desktop entry')
    if target.exists() and OWNER not in target.read_text().splitlines():
        raise ValueError('Preserve the existing unowned desktop entry')
    if args.action == 'remove':
        target.unlink(missing_ok=True)
        print('Removed only', target)
        return
    icon = str(root / 'icon.png').replace('\\', '\\\\')
    template = (root / 'org.aelthoren.Browser.Alpha.desktop.in').read_text()
    text = template.replace('@AELTHOREN_EXEC@', exec_argument(str(root / 'aelthoren'))).replace('@AELTHOREN_ICON@', icon)
    if args.action == 'print':
        print(text, end='')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, prefix='.aelthoren-', delete=False) as stream:
        stream.write(text)
        temporary = Path(stream.name)
    temporary.chmod(0o644)
    temporary.replace(target)
    print('Installed only', target)
    print('Moving the application requires running install again. Default browser was not changed.')


if __name__ == '__main__':
    main()
