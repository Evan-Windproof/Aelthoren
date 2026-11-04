#!/usr/bin/env python3
"""Official artifact workflow and real Gecko rendering verification for Phase 1."""
import argparse
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading

from prepare_phase1 import DOWNLOADS, LOCK, ROOT, SOURCE, verify, verify_source

OUTPUT = ROOT / 'docs/phase1'
OBJECT = SOURCE / 'obj-aelthoren-restart'
PROFILE = Path('/workspace/aelthoren-phase1-profile')


def environment():
    verify_source()
    for item in LOCK['artifacts']:
        verify(DOWNLOADS / item['name'], item)
    node = shutil.which('node')
    if not node:
        raise ValueError('Node is missing; use pinned source diagnostics, do not disable it')
    env = dict(os.environ, MOZBUILD_STATE_PATH='/workspace/aelthoren-tools/mozbuild',
               MOZCONFIG=str(ROOT / 'config/mozconfig.linux-artifact'), NODEJS=node,
               MOZ_ARTIFACT_FILE=os.pathsep.join(str(DOWNLOADS / i['name']) for i in LOCK['artifacts']))
    for name in ('MOZ_ARTIFACT_URL', 'MOZ_ARTIFACT_REVISION', 'MOZ_ARTIFACT_TASK', 'MOZ_ARTIFACT_TASK_LINUX64_OPT'):
        env.pop(name, None)
    return env


def mach(arguments, log_name):
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT / log_name).open('w') as log:
        result = subprocess.run(['./mach', *arguments], cwd=SOURCE, env=environment(), stdout=log, stderr=subprocess.STDOUT)
    print('mach', *arguments, 'exit:', result.returncode, 'log:', str(OUTPUT / log_name), flush=True)
    return result.returncode


def smoke():
    PROFILE.mkdir(exist_ok=True)
    image = OUTPUT / 'smoke.png'
    if image.exists():
        raise ValueError('Preserve previous screenshot before a new smoke run')
    results = []
    with (OUTPUT / 'http.log').open('w') as requests:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/result?status='):
                    results.append(self.path.split('=', 1)[1])
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'OK')
                else:
                    super().do_GET()

            def log_message(self, template, *args):
                requests.write(template % args + '\n')
                requests.flush()

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(Handler, directory=str(ROOT / 'docs/smoke')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        command = ['./mach', 'run', '--headless', '--no-remote', '-profile', str(PROFILE), '--screenshot', str(image), 'http://127.0.0.1:8765/']
        try:
            with (OUTPUT / 'smoke-browser.log').open('w') as log:
                process = subprocess.Popen(command, cwd=SOURCE, env=environment(), stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    code = process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    code = 124
        finally:
            server.shutdown()
            server.server_close()
    passed = code == 0 and image.is_file() and results == ['pass']
    report = {'source_revision': LOCK['revision'], 'version': LOCK['version'], 'build_type': 'official precompiled Gecko artifact + local browser frontend',
              'command': command, 'exit_code': code, 'fixture_callbacks': results, 'passed': passed,
              'screenshot_sha256': hashlib.sha256(image.read_bytes()).hexdigest() if image.exists() else None}
    (OUTPUT / 'smoke-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'full-target', 'run', 'smoke'))
    args = parser.parse_args()
    if args.command == 'build':
        for arguments, log in [(['--no-interactive', 'configure'], 'configure.log'), (['artifact', 'install'], 'install.log'), (['build', 'faster'], 'build-faster.log')]:
            if result := mach(arguments, log):
                return result
        return 0
    if args.command == 'full-target':
        return mach(['--no-interactive', 'build'], 'full-target.log')
    if args.command == 'smoke':
        return smoke()
    PROFILE.mkdir(exist_ok=True)
    return subprocess.call(['./mach', 'run', '--no-remote', '-profile', str(PROFILE)], cwd=SOURCE, env=environment())


if __name__ == '__main__':
    raise SystemExit(main())
