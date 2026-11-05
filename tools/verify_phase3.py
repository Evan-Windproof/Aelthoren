#!/usr/bin/env python3
"""Real Gecko checks. Privileged automation is confined to disposable test profiles."""
import base64
import contextlib
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from phase2 import ROOT, SOURCE, OBJECT
from run_aelthoren import prepare_profile
from verify_phase2 import Marionette

OUTPUT = ROOT / 'docs/phase3'
SEARCH = 'const {SearchService}=ChromeUtils.importESModule("moz-src:///toolkit/components/search/SearchService.sys.mjs");'
PLACES = 'const {PlacesUtils}=ChromeUtils.importESModule("resource://gre/modules/PlacesUtils.sys.mjs");'
WINDOW = 'const win=Services.wm.getMostRecentWindow("navigator:browser");'
checks = []
requests = []


def record(name, evidence):
    checks.append({'check': name, 'result': 'PASS', 'evidence': evidence})
    (OUTPUT / 'runtime-results.json').write_text(json.dumps(checks, indent=2) + '\n')
    print('PASS:', name, flush=True)


class Browser:
    def __init__(self, profile, label):
        self.log = (OUTPUT / (label + '.log')).open('w')
        self.process = subprocess.Popen([sys.executable, str(ROOT / 'tools/run_aelthoren.py'), '--profile', profile, '--', '--headless', '--marionette', '--remote-allow-system-access'], stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        self.socket = None
        try:
            for _ in range(450):
                if self.process.poll() is not None:
                    raise RuntimeError('Browser exited; inspect ' + label + '.log')
                try:
                    self.socket = socket.create_connection(('127.0.0.1', 2828), timeout=2)
                    break
                except OSError:
                    time.sleep(.1)
            if self.socket is None:
                raise TimeoutError('Marionette startup')
            self.socket.settimeout(70)
            self.b = Marionette(self.socket)
            self.capabilities = self.b.command('WebDriver:NewSession', capabilities={'alwaysMatch': {'acceptInsecureCerts': False}})['capabilities']
            self.b.command('WebDriver:SetTimeouts', script=60000, pageLoad=30000)
            assert self.capabilities['acceptInsecureCerts'] is False
            self.chrome(WINDOW + '''win.__phase3Network=[];win.__phase3NetworkObserver={observe(subject){const c=subject.QueryInterface(Ci.nsIHttpChannel);win.__phase3Network.push({host:c.URI.host,path:c.URI.pathQueryRef.split("?")[0],method:c.requestMethod});}};Services.obs.addObserver(win.__phase3NetworkObserver,"http-on-modify-request");''')
        except BaseException:
            self.close()
            raise

    def chrome(self, script):
        self.b.command('Marionette:SetContext', value='chrome')
        return self.b.script(script)

    def async_chrome(self, script):
        self.b.command('Marionette:SetContext', value='chrome')
        value = self.b.command('WebDriver:ExecuteAsyncScript', script='const done=arguments[arguments.length-1]; (async()=>{' + script + '})().then(done,e=>done({testError:String(e),stack:e.stack}));', args=[], newSandbox=True, sandbox='default')
        if isinstance(value, dict) and 'testError' in value:
            raise RuntimeError(str(value))
        return value

    def content(self, script):
        self.b.command('Marionette:SetContext', value='content')
        return self.b.script(script)

    def navigate(self, url):
        self.b.command('Marionette:SetContext', value='content')
        self.b.command('WebDriver:Navigate', url=url)

    def internal(self, url):
        self.chrome(WINDOW + 'win.gBrowser.selectedBrowser.loadURI(Services.io.newURI(' + json.dumps(url) + '),{triggeringPrincipal:Services.scriptSecurityManager.getSystemPrincipal()});')
        self.wait(lambda: self.content('return document.readyState === "complete" && document.documentURI === ' + json.dumps(url)))

    def wait(self, condition, seconds=20):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if result := condition():
                return result
            time.sleep(.1)
        raise TimeoutError('Browser condition not reached')

    def screenshot(self, name):
        self.b.command('Marionette:SetContext', value='content')
        (OUTPUT / (name + '.png')).write_bytes(base64.b64decode(self.b.command('WebDriver:TakeScreenshot', id=None, highlights=[], full=False)))

    def close(self):
        if self.process.poll() is None and hasattr(self, 'b'):
            try:
                self.b.command('Marionette:Quit', flags=['eAttemptQuit'])
                assert self.process.wait(timeout=30) == 0
            except Exception:
                os.killpg(self.process.pid, signal.SIGTERM)
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
        if self.socket:
            self.socket.close()
        self.log.close()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        requests.append({'host': self.headers.get('Host'), 'path': self.path})
        self.send_response(200)
        self.send_header('Cache-Control', 'no-store')
        if self.path.startswith('/tracker.js'):
            self.send_header('Content-Type', 'application/javascript')
            body = 'document.documentElement.dataset.trackerLoaded="yes";'
        else:
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            if self.path.startswith('/track'):
                body = '<title>Tracking fixture</title><script src="http://tracking.example.com:8765/tracker.js"></script><h1>Tracker test</h1>'
            elif self.path.startswith('/frame'):
                body = '<script>const p=new URLSearchParams(location.search);if(p.has("set"))localStorage.setItem("partition",p.get("set"));parent.postMessage({partition:localStorage.getItem("partition")},"*");</script>'
            elif self.path.startswith('/partition'):
                suffix = '?set=site-a' if 'set' in self.path else ''
                body = '<script>window.addEventListener("message",e=>document.documentElement.setAttribute("data-partition",JSON.stringify(e.data.partition)));</script><iframe src="http://storage.test:8765/frame' + suffix + '"></iframe>'
            else:
                body = '<title>Aelthoren real page</title><h1 id="result"></h1><form><input name="username"><input type="password" name="password"><button>Login</button></form><script>document.getElementById("result").textContent="JavaScript and DOM PASS";</script>'
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


def certificates(directory, profile):
    """Test CA lives only in the disposable profile; never alters system trust."""
    def openssl(*args):
        subprocess.run(['openssl', *map(str,args)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    openssl('req','-x509','-newkey','rsa:2048','-nodes','-days','2','-subj','/CN=Aelthoren fixture CA','-keyout',directory/'ca.key','-out',directory/'ca.crt')
    openssl('req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=localhost','-keyout',directory/'trusted.key','-out',directory/'trusted.csr')
    (directory/'extensions').write_text('subjectAltName=DNS:localhost\nbasicConstraints=critical,CA:FALSE\nextendedKeyUsage=serverAuth\nkeyUsage=critical,digitalSignature,keyEncipherment\n')
    openssl('x509','-req','-in',directory/'trusted.csr','-CA',directory/'ca.crt','-CAkey',directory/'ca.key','-CAcreateserial','-days','2','-extfile',directory/'extensions','-out',directory/'trusted.crt')
    openssl('req','-x509','-newkey','rsa:2048','-nodes','-days','2','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost','-addext','basicConstraints=critical,CA:FALSE','-keyout',directory/'untrusted.key','-out',directory/'untrusted.crt')
    env = dict(os.environ, LD_LIBRARY_PATH=str(OBJECT / 'dist/bin'))
    certutil = str(OBJECT / 'dist/bin/certutil')
    subprocess.run([certutil, '-N', '--empty-password', '-d', 'sql:' + str(profile)], env=env, check=True)
    subprocess.run([certutil, '-A', '-n', 'Aelthoren local fixture only', '-t', 'C,,', '-i', str(directory / 'ca.crt'), '-d', 'sql:' + str(profile)], env=env, check=True)


def search_checks(browser, expected, suffix):
    actual = browser.async_chrome(SEARCH + 'return {name:(await SearchService.getDefault()).name,private:(await SearchService.getDefaultPrivate()).name,choices:(await SearchService.getVisibleEngines()).map(e=>e.name)};')
    assert actual['name'] == expected, actual
    record(suffix + ' selected search provider', actual)
    # Observe and cancel synthetic search requests before network transmission.
    browser.chrome(WINDOW + '''win.__phase3Requests=[];win.__phase3Observer={observe(subject){const c=subject.QueryInterface(Ci.nsIHttpChannel);if(c.URI.spec.includes("aelthoren-phase3-")){win.__phase3Requests.push(c.URI.spec);c.cancel(Cr.NS_BINDING_ABORTED);}}};Services.obs.addObserver(win.__phase3Observer,"http-on-modify-request");''')
    try:
        browser.internal('about:newtab')
        browser.wait(lambda: browser.content('return document.querySelector("input").placeholder') == 'Search with ' + expected)
        if suffix == 'fresh profile':
            browser.screenshot('newtab')
        browser.content('document.querySelector("input").value="aelthoren-phase3-newtab"; return true;')
        time.sleep(1)
        assert browser.chrome(WINDOW + 'return win.__phase3Requests.length;') == 0
        browser.content('document.querySelector("form").requestSubmit(); return true;')
        urls = browser.wait(lambda: browser.chrome(WINDOW + 'return win.__phase3Requests.slice();'))
        engine_host = browser.async_chrome(SEARCH + 'return (await SearchService.getDefault()).getSubmission("aelthoren-phase3-newtab",null,"newtab").uri.host;')
        assert engine_host in urls[0], (engine_host, urls)
        record(suffix + ' new-tab search routes through selected provider', urls)
        browser.navigate('http://localhost:8765/')
        browser.chrome(WINDOW + 'win.__phase3Requests=[];win.gURLBar.search("aelthoren-phase3-typed");')
        time.sleep(2)
        assert browser.chrome(WINDOW + 'return win.__phase3Requests.length;') == 0
        browser.chrome(WINDOW + 'win.gURLBar.handleCommand();')
        urls = browser.wait(lambda: browser.chrome(WINDOW + 'return win.__phase3Requests.slice();'))
        assert engine_host in urls[0] and 'aelthoren-phase3-typed' in urls[0], urls
        record(suffix + ' native address-bar search and no pre-submit suggestion request', urls)
    finally:
        browser.chrome(WINDOW + 'Services.obs.removeObserver(win.__phase3Observer,"http-on-modify-request");delete win.__phase3Observer;')


def main():
    OUTPUT.mkdir(exist_ok=True)
    name = 'phase3-' + uuid.uuid4().hex[:12]
    profile = prepare_profile(name)
    # Prevent Marionette from replacing product privacy/security defaults.
    (profile / "user.js").write_text('user_pref("remote.prefs.recommended", false);\n')
    with tempfile.TemporaryDirectory(prefix='aelthoren-tls-', dir='/workspace/aelthoren-tests') as temporary:
        directory = Path(temporary)
        certificates(directory, profile)
        servers = []
        with contextlib.ExitStack() as stack:
            for port, cert in [(8765, None), (8443, 'trusted'), (8444, 'untrusted')]:
                server = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
                if cert:
                    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    tls.load_cert_chain(directory / (cert + '.crt'), directory / (cert + '.key'))
                    server.socket = tls.wrap_socket(server.socket, server_side=True)
                threading.Thread(target=server.serve_forever, daemon=True).start()
                stack.callback(server.server_close)
                stack.callback(server.shutdown)
                servers.append(server)
            browser = Browser(name, 'fresh-profile')
            stack.callback(browser.close)
            record('isolated genuine artifact browser', {k: browser.capabilities[k] for k in ['browserName','browserVersion','moz:profile','acceptInsecureCerts','userAgent']})
            search_checks(browser, 'DuckDuckGo', 'fresh profile')
            browser.navigate('http://localhost:8765/')
            assert browser.content('return document.getElementById("result").textContent') == 'JavaScript and DOM PASS'
            browser.content('localStorage.setItem("phase3-persist","normal");document.cookie="login=local; SameSite=Lax";return true;')
            assert browser.content('return document.cookie.includes("login=local")')
            record('ordinary website JavaScript, DOM, local storage and login cookie', True)
            configuration = browser.chrome('''const names=["identity.fxaccounts.enabled","datareporting.healthreport.uploadEnabled","datareporting.policy.dataSubmissionEnabled","toolkit.telemetry.archive.enabled","datareporting.usage.uploadEnabled","privacy.trackingprotection.enabled","privacy.trackingprotection.pbmode.enabled","privacy.trackingprotection.cryptomining.enabled","privacy.trackingprotection.fingerprinting.enabled","privacy.fingerprintingProtection","network.cookie.cookieBehavior","privacy.partition.network_state","browser.search.suggest.enabled","browser.urlbar.suggest.searches","security.sandbox.content.level","fission.autostart","browser.safebrowsing.malware.enabled","browser.safebrowsing.phishing.enabled","security.OCSP.enabled","javascript.enabled","toolkit.telemetry.enabled","toolkit.telemetry.unified","toolkit.telemetry.newProfilePing.enabled","toolkit.telemetry.shutdownPingSender.enabled","toolkit.telemetry.updatePing.enabled","app.shield.optoutstudies.enabled","app.normandy.enabled","browser.crashReports.unsubmittedCheck.autoSubmit2"]; return Object.fromEntries(names.map(n=>[n,{value:Services.prefs.getPrefType(n)===128?Services.prefs.getBoolPref(n):Services.prefs.getIntPref(n),locked:Services.prefs.prefIsLocked(n)}]));''')
            (OUTPUT / 'effective-preferences.json').write_text(json.dumps(configuration, indent=2)+'\n')
            for key in ['identity.fxaccounts.enabled','datareporting.healthreport.uploadEnabled','datareporting.policy.dataSubmissionEnabled','toolkit.telemetry.archive.enabled','datareporting.usage.uploadEnabled']:
                assert configuration[key]['value'] is False and configuration[key]['locked'], (key, configuration[key])
            for key in ['privacy.trackingprotection.enabled','privacy.trackingprotection.pbmode.enabled','privacy.trackingprotection.cryptomining.enabled','privacy.trackingprotection.fingerprinting.enabled','privacy.partition.network_state']:
                assert configuration[key]['value'] is True and not configuration[key]['locked'], (key, configuration[key])
            assert configuration['network.cookie.cookieBehavior'] == {'value':5,'locked':False}
            assert configuration['security.sandbox.content.level']['value'] >= 6
            for key in ['fission.autostart','javascript.enabled','browser.safebrowsing.malware.enabled','browser.safebrowsing.phishing.enabled']:
                assert configuration[key]['value'] is True, key
            record('account/Sync gate and telemetry upload policies disabled; ordinary privacy defaults unlocked; security preferences retained', configuration)
            browser.navigate('https://localhost:8443/')
            assert browser.content('return document.getElementById("result").textContent') == 'JavaScript and DOM PASS'
            record('HTTPS renders with trusted disposable fixture certificate', True)
            try:
                browser.navigate('https://localhost:8444/')
            except RuntimeError as error:
                assert 'insecure certificate' in str(error), str(error)
                record('untrusted HTTPS certificate rejected', 'insecure certificate; acceptInsecureCerts=false')
            else:
                raise AssertionError('Untrusted certificate accepted')
            browser.navigate('http://localhost:8765/')
            bookmark = browser.async_chrome(PLACES + 'return await PlacesUtils.bookmarks.insert({parentGuid:PlacesUtils.bookmarks.unfiledGuid,url:"http://localhost:8765/bookmark",title:"Aelthoren local bookmark"});')
            record('local bookmarks insert', {'guid':bookmark['guid']})
            password = browser.async_chrome('const login=Cc["@mozilla.org/login-manager/loginInfo;1"].createInstance(Ci.nsILoginInfo);login.init("http://localhost:8765","http://localhost:8765",null,"aelthoren-fixture","disposable-fixture-only","username","password");const saved=await Services.logins.addLoginAsync(login);return {saved:!!saved};')
            assert password['saved']
            record('native local password store accepts fixture login', True)
            # Additional privacy/runtime checks are below.
            additional_checks(browser)
            browser.internal('about:preferences#search')
            browser.wait(lambda: browser.content('return !!document.getElementById("defaultEngineNormal")'))
            alternative = browser.async_chrome(SEARCH + 'const engine=SearchService.getEngineByName("Bing");await SearchService.setDefault(engine,SearchService.CHANGE_REASON.USER);return (await SearchService.getDefault()).name;')
            record('native search settings control available; user-change API selects alternative', alternative)
            assert alternative == 'Bing'
            browser.screenshot('final-webpage')
            network_report(browser, 'fresh-session')
            browser.close()
            restarted = Browser(name, 'restarted-profile')
            stack.callback(restarted.close)
            search_checks(restarted, 'Bing', 'restarted user-choice profile')
            restarted.navigate('http://localhost:8765/')
            assert restarted.content('return localStorage.getItem("phase3-persist")') == 'normal'
            persisted = restarted.async_chrome(PLACES + 'return {bookmark:!!(await PlacesUtils.bookmarks.fetch(' + json.dumps(bookmark['guid']) + ')),history:!!(await PlacesUtils.history.fetch("http://localhost:8765/",{includeVisits:true}))};')
            assert persisted['bookmark'] and persisted['history'], persisted
            passwords = restarted.async_chrome('return (await Services.logins.getAllLogins()).filter(l=>l.origin==="http://localhost:8765").length;')
            assert passwords == 1, passwords
            record('native local password store survives restart', {'fixture_logins':passwords})
            record('bookmarks, real navigation history and localStorage survive restart', persisted)
            network_report(restarted, 'restarted-session')
            restarted.close()
    (OUTPUT / 'fixture-requests.json').write_text(json.dumps(requests, indent=2)+'\n')
    summary={'checks':len(checks),'result':'PASS','profile':str(profile),'source_revision':__import__('phase2').LOCK['revision'],'build_type':'official Linux artifact frontend; engine not compiled locally'}
    (OUTPUT / 'runtime-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if (OUTPUT / 'failure.json').exists():
        (OUTPUT / 'failure.json').rename(OUTPUT / 'initial-failures' / ('prior-failure-' + uuid.uuid4().hex[:8] + '.json'))
    print(json.dumps(summary,indent=2))


def network_report(browser, label):
    observed = browser.chrome(WINDOW + 'return win.__phase3Network.slice();')
    (OUTPUT / (label + '-requests.json')).write_text(json.dumps(observed,indent=2)+'\n')
    uploads = [r for r in observed if r['host'].endswith('telemetry.mozilla.org') and r['method'] == 'POST']
    assert not uploads, uploads
    record(label + ' bounded post-start HTTP observation', {'requests':len(observed),'telemetry_uploads_observed':len(uploads),'scope':'HTTP observer after automation attached; not exhaustive startup/shutdown or packet capture'})


def additional_checks(browser):
    browser.chrome(WINDOW + 'win.__phase3NoProxy=Services.prefs.getStringPref("network.proxy.no_proxies_on","");Services.prefs.setStringPref("network.proxy.no_proxies_on",win.__phase3NoProxy+",tracking.example.com,sitea.test,siteb.test,storage.test");Services.prefs.setStringPref("network.dns.localDomains","tracking.example.com,sitea.test,siteb.test,storage.test");')
    tracker_directory = (SOURCE / 'toolkit/components/url-classifier/tests').as_uri() + '/'
    browser.chrome('Services.io.getProtocolHandler("resource").QueryInterface(Ci.nsIResProtocolHandler).setSubstitution("aelthoren-test-classifier",Services.io.newURI(' + json.dumps(tracker_directory) + '));')
    tracker_module = 'resource://aelthoren-test-classifier/UrlClassifierTestUtils.sys.mjs'
    tracker_import = 'const {UrlClassifierTestUtils}=ChromeUtils.importESModule(' + json.dumps(tracker_module) + ');'
    browser.async_chrome(tracker_import + 'await UrlClassifierTestUtils.addTestTrackers();return true;')
    allow_import = 'const {ContentBlockingAllowList}=ChromeUtils.importESModule("resource://gre/modules/ContentBlockingAllowList.sys.mjs");'
    try:
        before = len([r for r in requests if r['path'].startswith('/tracker.js')])
        browser.navigate('http://localhost:8765/track')
        time.sleep(1)
        assert browser.content('return document.documentElement.dataset.trackerLoaded === "yes"') is False
        assert len([r for r in requests if r['path'].startswith('/tracker.js')]) == before
        blocking = browser.async_chrome(WINDOW + 'return {log:await win.gBrowser.selectedBrowser.getContentBlockingLog(),flag:Ci.nsIWebProgressListener.STATE_BLOCKED_TRACKING_CONTENT};')
        assert 'tracking.example.com' in blocking['log'], blocking
        assert any(entry[0] & blocking['flag'] and entry[1] for entries in json.loads(blocking['log']).values() for entry in entries), blocking
        record('known cross-site tracker blocked before HTTP request', blocking)
        browser.chrome(WINDOW + allow_import + 'ContentBlockingAllowList.add(win.gBrowser.selectedBrowser);')
        browser.navigate('http://localhost:8765/track')
        browser.wait(lambda: browser.content('return document.documentElement.dataset.trackerLoaded === "yes"'))
        assert len([r for r in requests if r['path'].startswith('/tracker.js')]) > before
        record('native site exception permits the same tracker (positive control)', True)
    finally:
        browser.chrome(WINDOW + allow_import + 'if(ContentBlockingAllowList.canHandle(win.gBrowser.selectedBrowser))ContentBlockingAllowList.remove(win.gBrowser.selectedBrowser);')
        browser.async_chrome(tracker_import + 'await UrlClassifierTestUtils.cleanupTestTrackers();return true;')
        browser.chrome('Services.io.getProtocolHandler("resource").QueryInterface(Ci.nsIResProtocolHandler).setSubstitution("aelthoren-test-classifier",null);')
    values = []
    for url in ['http://sitea.test:8765/partition?set','http://siteb.test:8765/partition','http://sitea.test:8765/partition']:
        browser.navigate(url)
        browser.wait(lambda: browser.content('return document.documentElement.hasAttribute("data-partition")'))
        values.append(browser.content('return JSON.parse(document.documentElement.getAttribute("data-partition"))'))
    assert values == ['site-a',None,'site-a'], values
    record('third-party localStorage partitioned by top-level site', values)
    browser.navigate('http://localhost:8765/')
    normal = browser.b.command('WebDriver:GetWindowHandle')
    browser.chrome(WINDOW + 'win.__phase3PBExits=0;win.__phase3PBObserver={observe(){win.__phase3PBExits++;}};Services.obs.addObserver(win.__phase3PBObserver,"last-pb-context-exited");')
    for number in range(2):
        handles = browser.b.command('WebDriver:GetWindowHandles')
        browser.chrome(WINDOW + 'win.OpenBrowserWindow({private:true});')
        new_handles = browser.wait(lambda: (lambda current: list(set(current)-set(handles)))(browser.b.command('WebDriver:GetWindowHandles')))
        browser.b.command('WebDriver:SwitchToWindow', handle=new_handles[0])
        browser.wait(lambda: browser.chrome(WINDOW + 'return !!win.gBrowserInit?.delayedStartupFinished;'))
        browser.wait(lambda: browser.content('return location.href === "about:privatebrowsing" && document.readyState === "complete"'))
        assert browser.chrome(WINDOW + 'return ChromeUtils.importESModule("resource://gre/modules/PrivateBrowsingUtils.sys.mjs").PrivateBrowsingUtils.isWindowPrivate(win);') is True
        browser.navigate('http://localhost:8765/')
        value = browser.content('return localStorage.getItem("phase3-persist")')
        assert value is None, {'private_window':number,'value':value}
        browser.content('localStorage.setItem("phase3-persist","private");return true;')
        browser.b.command('WebDriver:CloseWindow')
        browser.b.command('WebDriver:SwitchToWindow', handle=normal)
        browser.wait(lambda: browser.chrome(WINDOW + 'return win.__phase3PBExits;') > number)
    browser.navigate('http://localhost:8765/')
    assert browser.content('return localStorage.getItem("phase3-persist")') == 'normal'
    record('private windows isolate normal storage and clear private storage after last private window closes', True)
    browser.chrome(WINDOW + 'Services.obs.removeObserver(win.__phase3PBObserver,"last-pb-context-exited");')
    browser.internal('about:preferences#privacy')
    browser.wait(lambda: browser.content('return !!document.getElementById("clearSiteDataButton")'))
    ui = browser.content('const visible=id=>{const e=document.getElementById(id);return !!e&&!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length)};return {tracking:visible("trackingGroup")||visible("etpStatusAdvancedButton"),clearSiteData:visible("clearSiteDataButton"),siteData:visible("siteDataSettings"),history:visible("historyPane")||visible("clearHistoryButton"),syncVisible:visible("category-sync")};')
    assert ui['tracking'] and ui['clearSiteData'] and ui['siteData'] and not ui['syncVisible'], ui
    toolbar = browser.chrome(WINDOW + 'const e=win.document.getElementById("fxa-toolbar-menu-button");return !e || e.hidden || win.getComputedStyle(e).display==="none";')
    assert toolbar is True
    record('privacy/site-data controls visible and Sync category/account toolbar hidden', ui)
    browser.screenshot('privacy-settings')
    browser.internal('about:preferences#etp')
    browser.wait(lambda: browser.content('return !!document.getElementById("etpManageExceptionsButton")'))
    record('tracking settings expose native manage-exceptions control', browser.content('return !!document.getElementById("etpManageExceptionsButton")'))
    browser.navigate('http://localhost:8765/first')
    browser.navigate('http://localhost:8765/second')
    browser.b.command('WebDriver:Back')
    assert browser.content('return location.pathname') == '/first'
    browser.b.command('WebDriver:Forward')
    assert browser.content('return location.pathname') == '/second'
    original = browser.b.command('WebDriver:GetWindowHandle')
    tab = browser.b.command('WebDriver:NewWindow', type='tab', focus=True)
    browser.b.command('WebDriver:SwitchToWindow', handle=tab['handle'])
    browser.navigate('http://localhost:8765/new-tab')
    assert len(browser.b.command('WebDriver:GetWindowHandles')) == 2
    browser.b.command('WebDriver:CloseWindow')
    browser.b.command('WebDriver:SwitchToWindow', handle=original)
    record('native back, forward, new tab, switch and close', True)
    browser.chrome(WINDOW + 'Services.prefs.clearUserPref("network.dns.localDomains");Services.prefs.setStringPref("network.proxy.no_proxies_on",win.__phase3NoProxy);')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        (OUTPUT / 'fixture-requests.json').write_text(json.dumps(requests,indent=2)+'\n')
        (OUTPUT / 'failure.json').write_text(json.dumps({'error':str(error)},indent=2)+'\n')
        raise
