#!/usr/bin/env python3
"""Exercise the actual browser through Mozilla's loopback-only Marionette protocol."""
import base64
import functools
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time

from phase2 import OUTPUT, ROOT


class Marionette:
    def __init__(self, connection):
        self.connection = connection
        self.sequence = 0
        self.receive()

    def receive(self):
        prefix = b''
        while not prefix.endswith(b':'):
            value = self.connection.recv(1)
            if not value:
                raise EOFError('Browser connection closed')
            prefix += value
        length = int(prefix[:-1])
        if length > 20 * 1024 * 1024:
            raise ValueError('Unexpected response size')
        data = b''
        while len(data) < length:
            value = self.connection.recv(length - len(data))
            if not value:
                raise EOFError('Browser connection closed')
            data += value
        return json.loads(data)

    def command(self, name, **parameters):
        self.sequence += 1
        data = json.dumps([0, self.sequence, name, parameters]).encode()
        self.connection.sendall(str(len(data)).encode() + b':' + data)
        message = self.receive()
        if message[1] != self.sequence or message[2]:
            raise RuntimeError(str(message))
        result = message[3]
        return result.get('value', result) if isinstance(result, dict) else result

    def script(self, script):
        return self.command('WebDriver:ExecuteScript', script=script, args=[], newSandbox=True, sandbox='default')

    def screenshot(self, name):
        path = OUTPUT / (name + '.png')
        if path.exists():
            raise ValueError('Preserve previous screenshot first: ' + str(path))
        path.write_bytes(base64.b64decode(self.command('WebDriver:TakeScreenshot', id=None, highlights=[], full=False)))


def browser_case(profile, comprehensive):
    command = [sys.executable, str(ROOT / 'tools/run_aelthoren.py'), '--profile', profile, '--', '--headless', '--marionette']
    with (OUTPUT / (profile + '.log')).open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        connection = None
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('Browser exited before automation connected')
                try:
                    connection = socket.create_connection(('127.0.0.1', 2828), timeout=2)
                    break
                except OSError:
                    time.sleep(0.1)
            if connection is None:
                raise TimeoutError('Marionette did not start')
            connection.settimeout(30)
            browser = Marionette(connection)
            session = browser.command('WebDriver:NewSession', capabilities={'alwaysMatch': {'acceptInsecureCerts': False}})
            capabilities = session['capabilities']
            expected = '/workspace/aelthoren-user-data/profiles/' + profile
            assert capabilities['moz:profile'] == expected, capabilities
            assert capabilities['acceptInsecureCerts'] is False
            browser.command('WebDriver:Navigate', url='http://127.0.0.1:8765/')
            assert browser.script('return document.getElementById("result").textContent') == 'PASS: JavaScript, DOM, and storage'
            checks = ['isolated profile', 'certificate errors not accepted', 'real HTTP JavaScript/DOM/localStorage']
            if comprehensive:
                browser.command('WebDriver:Navigate', url='http://127.0.0.1:8765/')
                assert browser.script('return document.getElementById("result").textContent') == 'PASS: JavaScript, DOM, and storage'
                assert browser.script('return localStorage.getItem("aelthoren-smoke")') is None
                browser.screenshot('smoke')
                browser.command('WebDriver:Navigate', url='http://127.0.0.1:8765/second')
                assert browser.script('return document.title') == 'Second test page'
                browser.command('WebDriver:Back')
                assert browser.script('return document.getElementById("result").textContent').startswith('PASS:')
                browser.command('WebDriver:Forward')
                assert browser.script('return document.title') == 'Second test page'
                original = browser.command('WebDriver:GetWindowHandle')
                window = browser.command('WebDriver:NewWindow', type='tab', focus=True)
                browser.command('WebDriver:SwitchToWindow', handle=window['handle'])
                browser.command('WebDriver:Navigate', url='http://127.0.0.1:8765/second')
                assert len(browser.command('WebDriver:GetWindowHandles')) == 2
                assert browser.script('return document.title') == 'Second test page'
                browser.command('WebDriver:CloseWindow')
                browser.command('WebDriver:SwitchToWindow', handle=original)
                assert len(browser.command('WebDriver:GetWindowHandles')) == 1
                checks += ['native back/forward history', 'native tab creation/switch/close']
            browser.command('Marionette:Quit', flags=['eAttemptQuit'])
            code = process.wait(timeout=30)
            assert code == 0, code
            return {'profile': expected, 'browser_version': capabilities['browserVersion'], 'acceptInsecureCerts': capabilities['acceptInsecureCerts'], 'checks': checks, 'exit_code': code}
        finally:
            if connection:
                connection.close()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


def internal_pages():
    reports = []
    for name, url in [('newtab', 'about:newtab'), ('about', 'chrome://branding/content/about-aelthoren.html'), ('settings', 'about:preferences')]:
        image = OUTPUT / (name + '.png')
        if image.exists():
            raise ValueError('Preserve existing screenshot: ' + str(image))
        command = [sys.executable, str(ROOT / 'tools/run_aelthoren.py'), '--profile', 'phase2-ui-final', '--', '--headless', '--window-size', '1366,1000', '--screenshot', str(image), url]
        with (OUTPUT / (name + '.log')).open('w') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                raise
        assert code == 0 and image.exists(), (name, code)
        reports.append({'page': url, 'exit_code': code, 'screenshot': str(image)})
    return reports


def main():
    OUTPUT.mkdir(exist_ok=True)
    results = []
    with (OUTPUT / 'http.log').open('w') as requests:
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/second':
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'<!doctype html><title>Second test page</title><h1>Second real HTTP page</h1>')
                elif self.path.startswith('/result?status='):
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
        try:
            for profile, comprehensive in [('phase2-verification', True), ('phase2-second', False)]:
                results.append(browser_case(profile, comprehensive))
        finally:
            server.shutdown()
            server.server_close()
            (OUTPUT / 'runtime-results.json').write_text(json.dumps(results, indent=2) + '\n')
    pages = internal_pages()
    (OUTPUT / 'internal-pages.json').write_text(json.dumps(pages, indent=2) + '\n')
    print(json.dumps({'http_cases': results, 'internal_pages': pages}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
