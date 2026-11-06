#!/usr/bin/env python3
"""Standalone QA: no Aelthoren development modules/source tree needed by the app."""
import argparse
import base64
import hashlib
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import threading
import time

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

WINDOW='const win=Services.wm.getMostRecentWindow("navigator:browser");'
SEARCH='const {SearchService}=ChromeUtils.importESModule("moz-src:///toolkit/components/search/SearchService.sys.mjs");'
checks=[]


def record(name,evidence=True):
    checks.append({'check':name,'result':'PASS','evidence':evidence})
    print('PASS',name,flush=True)


class Browser:
    def __init__(self,package,out,name,gui=False):
        self.profile=out/'data/aelthoren-alpha/profiles'/name
        self.profile.mkdir(parents=True,exist_ok=True)
        (self.profile/'.aelthoren-profile').write_text('Aelthoren portable alpha profile\n')
        prefs={'remote.prefs.recommended':False,'network.dns.localDomains':'tracking.example.com','network.proxy.no_proxies_on':'localhost,127.0.0.1,tracking.example.com'}
        from urllib.parse import urlsplit
        proxy=urlsplit(os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY') or '')
        if proxy.hostname:
            prefs.update({'network.proxy.type':1,'network.proxy.http':proxy.hostname,'network.proxy.http_port':proxy.port or 8080,'network.proxy.ssl':proxy.hostname,'network.proxy.ssl_port':proxy.port or 8080})
        (self.profile/'user.js').write_text(''.join('user_pref('+json.dumps(k)+','+json.dumps(v)+');\n' for k,v in prefs.items()))
        if not (self.profile/'cert9.db').exists():
            subprocess.run(['certutil','-N','--empty-password','-d','sql:'+str(self.profile)],check=True)
            if Path('/run/proxy-ca.pem').is_file():
                subprocess.run(['certutil','-A','-n','QA-only environment proxy CA','-t','C,,','-i','/run/proxy-ca.pem','-d','sql:'+str(self.profile)],check=True)
        self.log=(out/(name+('-gui' if gui else '-headless')+'.log')).open('w')
        args=[str(package/'aelthoren'),'--profile',name,'--']
        if not gui:args+=['--headless']
        args+=['--marionette','--remote-allow-system-access','--width','1280','--height','900','http://127.0.0.1:8765/']
        self.process=subprocess.Popen(args,env=dict(os.environ,XDG_DATA_HOME=str(out/'data')),stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
        self.connection=None
        for _ in range(600):
            if self.process.poll() is not None:raise RuntimeError('Portable browser exited; inspect '+str(out))
            try:self.connection=socket.create_connection(('127.0.0.1',2828),timeout=1);break
            except OSError:time.sleep(.1)
        if self.connection is None:raise TimeoutError('Browser automation startup')
        self.connection.settimeout(90)
        self.b=Marionette(self.connection)
        self.caps=self.b.command('WebDriver:NewSession',capabilities={'alwaysMatch':{'acceptInsecureCerts':False}})['capabilities']
        self.b.command('WebDriver:SetTimeouts',pageLoad=45000,script=60000)
        assert self.caps['moz:profile']==str(self.profile),self.caps
        assert not self.caps['acceptInsecureCerts']
        assert self.caps['moz:headless']==(not gui)
        self.wait(lambda:self.content('return location.href==="http://127.0.0.1:8765/" && document.readyState==="complete"'))

    def content(self,script):
        self.b.command('Marionette:SetContext',value='content');return self.b.script(script)

    def chrome(self,script):
        self.b.command('Marionette:SetContext',value='chrome');return self.b.script(script)

    def async_chrome(self,script):
        self.b.command('Marionette:SetContext',value='chrome')
        result=self.b.command('WebDriver:ExecuteAsyncScript',script='const done=arguments[arguments.length-1];(async()=>{'+script+'})().then(done,e=>done({testError:String(e),stack:e.stack}));',args=[],newSandbox=True,sandbox='default')
        if isinstance(result,dict) and 'testError' in result:raise RuntimeError(str(result))
        return result

    def navigate(self,url):
        self.b.command('Marionette:SetContext',value='content');self.b.command('WebDriver:Navigate',url=url)

    def internal(self,url):
        self.chrome(WINDOW+'win.gBrowser.selectedBrowser.loadURI(Services.io.newURI('+json.dumps(url)+'),{triggeringPrincipal:Services.scriptSecurityManager.getSystemPrincipal()});')
        self.wait(lambda:self.content('return document.documentURI==='+json.dumps(url)+' && document.readyState==="complete"'))

    def wait(self,test):
        end=time.monotonic()+45
        while time.monotonic()<end:
            if value:=test():return value
            time.sleep(.1)
        raise TimeoutError('Browser condition')

    def close(self):
        if self.process.poll() is None:
            try:
                self.b.command('Marionette:Quit',flags=['eAttemptQuit']);assert self.process.wait(timeout=40)==0
            except Exception:
                os.killpg(self.process.pid,signal.SIGTERM);self.process.wait(timeout=10);raise
        if self.connection:self.connection.close()
        self.log.close()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200);self.send_header('Cache-Control','no-store')
        if self.path=='/tracker.js':
            self.send_header('Content-Type','application/javascript');body='document.documentElement.dataset.tracker="yes";'
        else:
            self.send_header('Content-Type','text/html; charset=utf-8')
            body='<title>Aelthoren native package test</title><h1 id="result"></h1><script>document.getElementById("result").textContent="JS and DOM PASS";</script>'
            if self.path=='/track':body+='<script src="http://tracking.example.com:8765/tracker.js"></script>'
        self.end_headers();self.wfile.write(body.encode())

    def log_message(self,*args):pass


def search_submission(browser,expected,label):
    value=browser.async_chrome(SEARCH+'return {name:(await SearchService.getDefault()).name,engines:(await SearchService.getVisibleEngines()).map(e=>e.name)};')
    assert value['name']==expected,value
    browser.internal('about:newtab')
    browser.wait(lambda:browser.content('return document.getElementById("search-query")?.placeholder')=='Search with '+expected)
    browser.chrome(WINDOW+'win.__search=[];win.__searchObserver={observe(subject){const c=subject.QueryInterface(Ci.nsIHttpChannel);if(c.URI.spec.includes("aelthoren-package-test")){win.__search.push(c.URI.spec);c.cancel(Cr.NS_BINDING_ABORTED);}}};Services.obs.addObserver(win.__searchObserver,"http-on-modify-request");')
    try:
        browser.content('document.getElementById("search-query").value="aelthoren-package-test";document.querySelector("form").requestSubmit();return true;')
        urls=browser.wait(lambda:browser.chrome(WINDOW+'return win.__search.slice();'))
        host=browser.async_chrome(SEARCH+'return (await SearchService.getDefault()).getSubmission("aelthoren-package-test",null,"newtab").uri.host;')
        assert host in urls[0],urls
        record(label+' native provider and new-tab submission',value)
    finally:browser.chrome(WINDOW+'Services.obs.removeObserver(win.__searchObserver,"http-on-modify-request");')


def functional(browser,package,out):
    record('Dedicated portable profile and actual Gecko', {k:browser.caps[k] for k in ['browserName','browserVersion','userAgent','moz:profile','moz:headless','acceptInsecureCerts']})
    assert browser.content('return document.getElementById("result").textContent')=='JS and DOM PASS'
    browser.content('localStorage.setItem("package-persist","normal");document.cookie="fixture=local; SameSite=Lax";return true;')
    assert browser.content('return document.cookie.includes("fixture=local")')
    record('Real HTTP JavaScript DOM storage and cookies')
    search_submission(browser,'DuckDuckGo','Fresh profile')
    prefs=browser.chrome('return {account:Services.prefs.getBoolPref("identity.fxaccounts.enabled"),upload:Services.prefs.getBoolPref("datareporting.healthreport.uploadEnabled"),tracking:Services.prefs.getBoolPref("privacy.trackingprotection.enabled"),privateTracking:Services.prefs.getBoolPref("privacy.trackingprotection.pbmode.enabled"),cookieBehavior:Services.prefs.getIntPref("network.cookie.cookieBehavior"),networkPartition:Services.prefs.getBoolPref("privacy.partition.network_state"),sandbox:Services.prefs.getIntPref("security.sandbox.content.level"),fission:Services.prefs.getBoolPref("fission.autostart"),safeBrowsing:Services.prefs.getBoolPref("browser.safebrowsing.malware.enabled"),searchLocked:Services.prefs.prefIsLocked("browser.search.suggest.enabled")};')
    assert prefs=={'account':False,'upload':False,'tracking':True,'privateTracking':True,'cookieBehavior':5,'networkPartition':True,'sandbox':6,'fission':True,'safeBrowsing':True,'searchLocked':False},prefs
    record('Account Sync telemetry tracking partition and security configuration',prefs)
    browser.navigate('https://example.com/')
    public=browser.content('return {url:location.href,title:document.title,text:document.body.textContent.slice(0,1000)}')
    (out/'public-https.json').write_text(json.dumps(public,indent=2)+'\n')
    assert public['title']=='Example Domain' and 'This domain is for use' in public['text'],public
    record('Actual public HTTPS website rendered via configured proxy with QA-only trusted CA',browser.content('return {url:location.href,title:document.title}'))
    browser.b.command('Marionette:SetContext',value='content')
    (out/'https.png').write_bytes(base64.b64decode(browser.b.command('WebDriver:TakeScreenshot',id=None,highlights=[],full=False)))
    try:browser.navigate('https://localhost:8444/')
    except RuntimeError as error:
        assert 'insecure certificate' in str(error),str(error);record('Untrusted local TLS certificate rejected')
    else:raise AssertionError('Untrusted TLS was accepted')
    browser.navigate('http://127.0.0.1:8765/')
    original=browser.b.command('WebDriver:GetWindowHandle')
    handles=browser.b.command('WebDriver:GetWindowHandles')
    browser.chrome(WINDOW+'win.__pbExits=0;win.__pbObserver={observe(){win.__pbExits++;}};Services.obs.addObserver(win.__pbObserver,"last-pb-context-exited");win.OpenBrowserWindow({private:true});')
    browser.b.command('Marionette:SetContext',value='content')
    private=browser.wait(lambda:list(set(browser.b.command('WebDriver:GetWindowHandles'))-set(handles)))
    browser.b.command('WebDriver:SwitchToWindow',handle=private[0])
    browser.wait(lambda:browser.chrome(WINDOW+'return !!win.gBrowserInit?.delayedStartupFinished;'))
    browser.wait(lambda:browser.content('return location.href==="about:privatebrowsing" && document.readyState==="complete"'))
    assert browser.chrome(WINDOW+'return ChromeUtils.importESModule("resource://gre/modules/PrivateBrowsingUtils.sys.mjs").PrivateBrowsingUtils.isWindowPrivate(win);')
    browser.navigate('http://127.0.0.1:8765/')
    assert browser.content('return localStorage.getItem("package-persist")') is None
    browser.content('localStorage.setItem("package-persist","private");return true;')
    browser.b.command('WebDriver:CloseWindow');browser.b.command('WebDriver:SwitchToWindow',handle=original)
    browser.wait(lambda:browser.chrome(WINDOW+'return win.__pbExits;')==1)
    browser.chrome(WINDOW+'Services.obs.removeObserver(win.__pbObserver,"last-pb-context-exited");')
    browser.navigate('http://127.0.0.1:8765/');assert browser.content('return localStorage.getItem("package-persist")')=='normal'
    record('Private window uses separate session storage and preserves normal data')
    for url in ['http://127.0.0.1:8765/one','http://127.0.0.1:8765/two']:browser.navigate(url)
    browser.b.command('WebDriver:Back');assert browser.content('return location.pathname')=='/one'
    browser.b.command('WebDriver:Forward');assert browser.content('return location.pathname')=='/two'
    tab=browser.b.command('WebDriver:NewWindow',type='tab',focus=True);browser.b.command('WebDriver:SwitchToWindow',handle=tab['handle']);browser.navigate('http://127.0.0.1:8765/tab')
    assert len(browser.b.command('WebDriver:GetWindowHandles'))==2
    browser.b.command('WebDriver:CloseWindow');browser.b.command('WebDriver:SwitchToWindow',handle=original)
    record('Native tabs back forward and closure')
    helper=Path('/checks/UrlClassifierTestUtils.sys.mjs')
    if helper.is_file():
        browser.chrome('Services.io.getProtocolHandler("resource").QueryInterface(Ci.nsIResProtocolHandler).setSubstitution("package-test",Services.io.newURI("file:///checks/"));')
        module='const {UrlClassifierTestUtils}=ChromeUtils.importESModule("resource://package-test/UrlClassifierTestUtils.sys.mjs");'
        browser.async_chrome(module+'await UrlClassifierTestUtils.addTestTrackers();return true;')
        try:
            browser.navigate('http://127.0.0.1:8765/track')
            assert browser.content('return document.documentElement.dataset.tracker') is None
            blocking=browser.async_chrome(WINDOW+'return {log:await win.gBrowser.selectedBrowser.getContentBlockingLog(),flag:Ci.nsIWebProgressListener.STATE_BLOCKED_TRACKING_CONTENT};')
            entries=json.loads(blocking['log']);assert 'http://tracking.example.com:8765' in entries or 'tracking.example.com' in blocking['log']
            assert any(item[0]&blocking['flag'] and item[1] for values in entries.values() for item in values),blocking
            record('Native classifier blocks a known cross-site tracker',blocking)
        finally:
            browser.async_chrome(module+'await UrlClassifierTestUtils.cleanupTestTrackers();return true;')
            browser.chrome('Services.io.getProtocolHandler("resource").QueryInterface(Ci.nsIResProtocolHandler).setSubstitution("package-test",null);')
    browser.navigate((package/'ABOUT.html').as_uri())
    assert '0.1.0-alpha' in browser.content('return document.body.textContent')
    browser.wait(lambda:browser.content('return document.images[0].complete && document.images[0].naturalWidth>0'))
    record('Packaged Aelthoren alpha About page and product version')
    browser.internal('about:preferences#privacy')
    browser.wait(lambda:browser.content('return !!document.getElementById("clearSiteDataButton")'))
    assert browser.content('const e=document.getElementById("category-sync");return !e||e.hidden||!e.getClientRects().length')
    record('Sync settings category hidden and local site-data controls available')
    if not browser.caps['moz:headless']:
        browser.b.command('Marionette:SetContext',value='chrome')
        (out/'gui-window.png').write_bytes(base64.b64decode(browser.b.command('WebDriver:TakeScreenshot',id=None,highlights=[],full=False)))
        record('Actual desktop GUI screenshot captured')
    browser.navigate('http://127.0.0.1:8765/')
    browser.async_chrome(SEARCH+'await SearchService.setDefault(SearchService.getEngineByName("Bing"),SearchService.CHANGE_REASON.USER);return true;')
    processes=[]
    for path in Path('/proc').glob('[0-9]*/status'):
        try:
            data=path.read_text();cmd=(path.parent/'cmdline').read_bytes()
            if b'firefox' in cmd:
                fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in data.splitlines() if ':' in line}
                processes.append({k:fields.get(k) for k in ['Name','Pid','PPid','Seccomp','Seccomp_filters','NoNewPrivs']})
        except OSError:pass
    parent=next(p for p in processes if p['Pid']==str(browser.caps['moz:processID']))
    active_pid=browser.chrome(WINDOW+'return win.gBrowser.selectedBrowser.browsingContext.currentWindowGlobal.osPid;')
    active=next(p for p in processes if p['Pid']==str(active_pid))
    assert active['Seccomp']=='2' and active['NoNewPrivs']=='1' and int(active['Seccomp_filters'])>int(parent['Seccomp_filters']),processes
    record('Active web document adds seccomp filters and NoNewPrivs (not an exploit audit)',{'active_pid':active_pid,'parent':parent,'processes':processes})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--gui',action='store_true');parser.add_argument('--branding-audit',action='store_true');args=parser.parse_args()
    package=args.package.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    assert os.getuid()!=0,'Portable tests must run unprivileged'
    for name in ['MOZ_DISABLE_CONTENT_SANDBOX','MOZ_DISABLE_GMP_SANDBOX','MOZ_DISABLE_RDD_SANDBOX','MOZ_DISABLE_GPU_SANDBOX']:
        assert not os.environ.get(name),'Do not disable browser sandboxing for tests'
    assert not Path('/workspace/aelthoren-gecko').exists(),'Clean test must not mount source tree'
    assert not Path('/workspace/Aelthoren/tools').exists(),'Clean test must not mount Codex project tools'
    version=subprocess.check_output([str(package/'aelthoren'),'--version'],text=True);assert '0.1.0-alpha' in version and 'development-only' in version
    record('Portable launch metadata without source tree or Codex modules',version.strip())
    bad=out/'untrusted'
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','2','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost','-keyout',str(bad)+'.key','-out',str(bad)+'.crt'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    servers=[];browser=None
    try:
        for port in [8765,8444]:
            server=http.server.ThreadingHTTPServer(('127.0.0.1',port),Handler)
            if port==8444:
                tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(str(bad)+'.crt',str(bad)+'.key');server.socket=tls.wrap_socket(server.socket,server_side=True)
            threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server)
        browser=Browser(package,out,'first',args.gui);functional(browser,package,out)
        if args.branding_audit:
            from verify_branding_gui import verify as verify_branding
            verify_branding(browser,package,out);record('Final branding GUI audit and native default prompt cancelled')
        browser.close();browser=None
        browser=Browser(package,out,'first',args.gui);search_submission(browser,'Bing','Restarted user-choice profile');browser.navigate('http://127.0.0.1:8765/');assert browser.content('return localStorage.getItem("package-persist")')=='normal';record('User-selected provider and local storage survive restart');browser.close();browser=None
        browser=Browser(package,out,'second',args.gui);assert browser.async_chrome(SEARCH+'return (await SearchService.getDefault()).name;')=='DuckDuckGo';assert browser.content('return localStorage.getItem("package-persist")') is None;record('Second portable profile is isolated');browser.close();browser=None
    finally:
        if browser:browser.close()
        for server in servers:server.shutdown();server.server_close()
    result={'result':'PASS','checks':checks,'distribution':Path('/etc/os-release').read_text(),'gui':args.gui,'uid':os.getuid(),'package_metadata':json.loads((package/'package.json').read_text())}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('ALL PACKAGE CHECKS PASSED:',len(checks),flush=True)


if __name__=='__main__':
    main()
