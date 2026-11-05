#!/usr/bin/env python3
"""Repeatable desktop Gecko measurements; profiles/logs stay outside the repository."""
import argparse
from collections import Counter
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import statistics
import subprocess
import sys
import threading
import time
import uuid

from phase2 import LOCK, ROOT, OBJECT, verify_overlay
from run_aelthoren import prepare_profile
from verify_phase2 import Marionette

WORK = Path('/workspace/aelthoren-benchmarks')
WINDOW = 'const win=Services.wm.getMostRecentWindow("navigator:browser");'
HZ = os.sysconf('SC_CLK_TCK')
PAGE_SIZE = os.sysconf('SC_PAGE_SIZE')


def process_tree(root):
    processes = {}
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            parts = path.read_text().rsplit(')',1)[1].split()
            processes[int(path.parent.name)] = {'parent':int(parts[1]),'cpu':(int(parts[11])+int(parts[12]))/HZ,'rss':int(parts[21])*PAGE_SIZE}
        except (OSError,ValueError,IndexError):
            continue
    selected = {root}
    while True:
        children = {pid for pid,info in processes.items() if info['parent'] in selected}
        if children <= selected:
            break
        selected |= children
    return {pid:processes[pid] for pid in selected if pid in processes}


def resource_sample(root):
    processes = process_tree(root)
    pss = 0
    readable = 0
    for pid in processes:
        try:
            fields = dict(line.split(':',1) for line in Path(f'/proc/{pid}/smaps_rollup').read_text().splitlines() if ':' in line)
            pss += int(fields['Pss'].split()[0])*1024
            readable += 1
        except (OSError,KeyError):
            pass
    return {'processes':len(processes),'rss_mib':sum(v['rss'] for v in processes.values())/2**20,'pss_mib':pss/2**20 if readable==len(processes) else None,'pss_readable_processes':readable,'cpu':{str(k):v['cpu'] for k,v in processes.items()}}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'''<!doctype html><meta charset="utf-8"><title>Aelthoren performance fixture</title><h1 id="ready">Real Gecko fixture</h1><main></main><script>const m=document.querySelector('main');for(let i=0;i<400;i++){const p=document.createElement('p');p.textContent='Aelthoren deterministic local document '+i;m.append(p)}window.payload=Array.from({length:16384},(_,i)=>({i,value:'fixture-'+i}));localStorage.setItem('phase4','persistent');document.documentElement.dataset.ready='yes';setInterval(()=>document.documentElement.dataset.tick=String(Number(document.documentElement.dataset.tick||0)+1),1000);</script>'''
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self,*args):
        pass


class Session:
    def __init__(self,name,label):
        self.log = (WORK/(label+'.log')).open('w')
        self.started = time.perf_counter()
        self.process = subprocess.Popen([sys.executable,str(ROOT/'tools/run_aelthoren.py'),'--profile',name,'--','--marionette','--remote-allow-system-access','--width','1200','--height','700','http://127.0.0.1:8766/'],env=dict(os.environ,DISPLAY=':97',XAUTHORITY=str(WORK/'Xauthority')),stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
        self.socket = None
        try:
            deadline=time.monotonic()+60
            while time.monotonic()<deadline:
                if self.process.poll() is not None:
                    raise RuntimeError('Browser startup failed; inspect '+label)
                try:
                    self.socket=socket.create_connection(('127.0.0.1',2828),timeout=1)
                    break
                except OSError:
                    time.sleep(.02)
            if self.socket is None:
                raise TimeoutError('Marionette startup')
            self.socket.settimeout(60)
            self.listener_ms=(time.perf_counter()-self.started)*1000
            self.b=Marionette(self.socket)
            self.capabilities=self.b.command('WebDriver:NewSession',capabilities={'alwaysMatch':{'acceptInsecureCerts':False}})['capabilities']
            self.b.command('WebDriver:SetTimeouts',pageLoad=30000,script=30000)
            self.wait(lambda:self.chrome(WINDOW+'return !!win.gBrowserInit?.delayedStartupFinished;'))
            self.wait(lambda:self.content('return location.href==="http://127.0.0.1:8766/" && document.documentElement.dataset.ready==="yes";'))
            self.frame()
            self.responsive_ms=(time.perf_counter()-self.started)*1000
            assert not self.capabilities['moz:headless'] and not self.capabilities['acceptInsecureCerts']
            self.chrome(WINDOW+'''win.__perfRequests=[];win.__perfObserver={observe(subject){const c=subject.QueryInterface(Ci.nsIHttpChannel);win.__perfRequests.push({host:c.URI.host,method:c.requestMethod});}};Services.obs.addObserver(win.__perfObserver,"http-on-modify-request");''')
        except BaseException:
            self.close()
            raise

    def chrome(self,script):
        self.b.command('Marionette:SetContext',value='chrome')
        return self.b.script(script)

    def content(self,script):
        self.b.command('Marionette:SetContext',value='content')
        return self.b.script(script)

    def frame(self):
        self.b.command('Marionette:SetContext',value='content')
        return self.b.command('WebDriver:ExecuteAsyncScript',script='const done=arguments[arguments.length-1];requestAnimationFrame(()=>requestAnimationFrame(()=>done({ready:document.readyState,url:location.href})));',args=[],newSandbox=True,sandbox='default')

    def wait(self,test):
        end=time.monotonic()+30
        while time.monotonic()<end:
            if value:=test():
                return value
            time.sleep(.02)
        raise TimeoutError('Browser readiness condition')

    def idle(self,tabs):
        time.sleep(2)
        self.chrome(WINDOW+'win.__perfRequests=[];')
        before=resource_sample(self.process.pid)
        start=time.perf_counter()
        samples=[]
        for _ in range(5):
            time.sleep(1)
            samples.append(resource_sample(self.process.pid))
        elapsed=time.perf_counter()-start
        previous=before['cpu']
        cpu_seconds=0
        for sample in samples:
            cpu_seconds+=sum(max(0,v-previous.get(k,0)) for k,v in sample['cpu'].items())
            previous=sample['cpu']
        network=self.chrome(WINDOW+'return win.__perfRequests.slice();')
        return {'tabs':tabs,'window_seconds':elapsed,'idle_cpu_pct_one_core':100*cpu_seconds/elapsed,'rss_mib':statistics.median(s['rss_mib'] for s in samples),'rss_min_mib':min(s['rss_mib'] for s in samples),'rss_max_mib':max(s['rss_mib'] for s in samples),'pss_mib':statistics.median(s['pss_mib'] for s in samples) if all(s['pss_mib'] is not None for s in samples) else None,'processes':statistics.median(s['processes'] for s in samples),'http_attempts':len(network),'http_hosts':dict(Counter(r['host'] for r in network))}

    def close(self):
        if self.process.poll() is None and hasattr(self,'b'):
            try:
                self.b.command('Marionette:Quit',flags=['eAttemptQuit'])
                self.exit_code=self.process.wait(timeout=30)
            except Exception:
                self.exit_code=None
        if self.process.poll() is None:
            os.killpg(self.process.pid,signal.SIGTERM)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid,signal.SIGKILL)
                self.process.wait()
        if self.socket:
            self.socket.close()
        self.log.close()


def configuration_fingerprints(profile):
    folder=OBJECT/'dist/bin/distribution'
    paths=[folder/'policies.json',folder/'distribution.ini',folder/'.aelthoren-policies.json-sha256',folder/'.aelthoren-distribution.ini-sha256',profile/'.aelthoren-profile']
    return {str(p):p.stat().st_mtime_ns for p in paths}


def measure(name,label):
    profile=prepare_profile(name)
    before=configuration_fingerprints(profile)
    browser=Session(name,label)
    try:
        after=configuration_fingerprints(profile)
        result={'label':label,'profile':name,'startup_listener_ms':browser.listener_ms,'startup_responsive_ms':browser.responsive_ms,'unchanged_files_rewritten':sum(before[k]!=after[k] for k in before),'resources':[],'tab_create_ms':[],'tab_switch_ms':[],'newtab_load_ms':[]}
        browser.b.command('Marionette:SetContext',value='content')
        original=browser.b.command('WebDriver:GetWindowHandle')
        handles=[original]
        result['resources'].append(browser.idle(1))
        for number in range(2,11):
            browser.b.command('Marionette:SetContext',value='content')
            started=time.perf_counter()
            tab=browser.b.command('WebDriver:NewWindow',type='tab',focus=True)
            handles.append(tab['handle'])
            browser.b.command('WebDriver:SwitchToWindow',handle=tab['handle'])
            browser.b.command('WebDriver:Navigate',url=f'http://127.0.0.{number}:8766/')
            browser.frame()
            assert browser.content('return document.documentElement.dataset.ready')=='yes'
            result['tab_create_ms'].append((time.perf_counter()-started)*1000)
            if number in [5,10]:
                result['resources'].append(browser.idle(number))
        for handle in handles:
            browser.b.command('Marionette:SetContext',value='content')
            started=time.perf_counter()
            browser.b.command('WebDriver:SwitchToWindow',handle=handle)
            browser.frame()
            result['tab_switch_ms'].append((time.perf_counter()-started)*1000)
            assert browser.content('return localStorage.getItem("phase4")')=='persistent'
        scratch=browser.b.command('WebDriver:NewWindow',type='tab',focus=True)
        browser.b.command('WebDriver:SwitchToWindow',handle=scratch['handle'])
        for _ in range(3):
            browser.chrome(WINDOW+'win.gBrowser.selectedBrowser.loadURI(Services.io.newURI("about:blank"),{triggeringPrincipal:Services.scriptSecurityManager.getSystemPrincipal()});')
            browser.wait(lambda:browser.content('return location.href==="about:blank"'))
            started=time.perf_counter()
            browser.chrome(WINDOW+'win.gBrowser.selectedBrowser.loadURI(Services.io.newURI("about:newtab"),{triggeringPrincipal:Services.scriptSecurityManager.getSystemPrincipal()});')
            browser.wait(lambda:browser.content('return document.querySelector("#search-query")?.placeholder==="Search with DuckDuckGo"'))
            browser.frame()
            result['newtab_load_ms'].append((time.perf_counter()-started)*1000)
        native_count=browser.chrome(WINDOW+'return win.gBrowser.tabs.length;')
        assert native_count==11,native_count
        browser.chrome(WINDOW+'const tabs=[...win.gBrowser.tabs];for(const tab of tabs.slice(1)){win.gBrowser.removeTab(tab);}win.gBrowser.selectedTab=win.gBrowser.tabs[0];')
        browser.b.command('Marionette:SetContext',value='content')
        remaining=browser.b.command('WebDriver:GetWindowHandles')
        assert len(remaining)==1,remaining
        browser.b.command('WebDriver:SwitchToWindow',handle=remaining[0])
        browser.b.command('WebDriver:Navigate',url='http://127.0.0.1:8766/history-first')
        browser.b.command('WebDriver:Navigate',url='http://127.0.0.1:8766/history-second')
        browser.b.command('WebDriver:Back')
        assert browser.content('return location.pathname')=='/history-first'
        browser.b.command('WebDriver:Forward')
        assert browser.content('return location.pathname')=='/history-second'
        result['after_tab_closure']=browser.idle(1)
        result['security']=browser.chrome('return {sandbox:Services.prefs.getIntPref("security.sandbox.content.level"),fission:Services.prefs.getBoolPref("fission.autostart"),tracking:Services.prefs.getBoolPref("privacy.trackingprotection.enabled"),cookieBehavior:Services.prefs.getIntPref("network.cookie.cookieBehavior"),safeBrowsing:Services.prefs.getBoolPref("browser.safebrowsing.malware.enabled"),account:Services.prefs.getBoolPref("identity.fxaccounts.enabled"),telemetryUpload:Services.prefs.getBoolPref("datareporting.healthreport.uploadEnabled")};')
        assert result['security']=={'sandbox':6,'fission':True,'tracking':True,'cookieBehavior':5,'safeBrowsing':True,'account':False,'telemetryUpload':False},result['security']
        result['background_tick_verified']=browser.content('return Number(document.documentElement.dataset.tick)>0')
        assert result['background_tick_verified']
    finally:
        browser.close()
    assert browser.exit_code==0,browser.exit_code
    result['exit_code']=browser.exit_code
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['baseline','candidate'])
    parser.add_argument('--repetitions',type=int,default=3)
    args=parser.parse_args()
    verify_overlay()
    destination=ROOT/'docs/phase4'/(args.stage+'.json')
    if destination.exists():
        raise ValueError('Preserve existing benchmark data before reusing this stage')
    WORK.mkdir(exist_ok=True)
    servers=[]
    results=[]
    report={'stage':args.stage,'source_revision':LOCK['revision'],'project_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'conditions':{'display':':97 Xorg dummy 1366x768x24; window 1200x700; not headless','cpu_quota':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_limit_bytes':int(Path('/sys/fs/cgroup/memory.max').read_text()),'kernel':os.uname().release,'python':sys.version.split()[0],'cold_definition':'fresh profile; OS page cache is not flushed','warm_definition':'immediate restart of same profile after complete cold workload','idle_seconds_per_sample':5,'rss_includes':'launcher + Firefox descendants; shared pages double counted','pss':'only reported if every descendant smaps_rollup is readable','network':'normal inherited remote networking retained; observed after automation attaches','fixture':'ten distinct loopback IP sites; each 400 DOM nodes, 16384 JS objects, 1Hz timer'},'runs':results}
    try:
        for number in range(1,11):
            server=http.server.ThreadingHTTPServer((f'127.0.0.{number}',8766),Handler)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            servers.append(server)
        for repeat in range(args.repetitions):
            name=f'phase4-{args.stage}-{uuid.uuid4().hex[:10]}'
            profile=prepare_profile(name)
            hosts=','.join(f'127.0.0.{i}' for i in range(1,11))
            (profile/'user.js').write_text('user_pref("remote.prefs.recommended", false);\nuser_pref("network.proxy.no_proxies_on",'+json.dumps(hosts)+');\n')
            for mode in ['profile-cold','warm']:
                label=f'{args.stage}-{repeat+1}-{mode}'
                print('START',label,flush=True)
                result=measure(name,label)
                result.update(mode=mode,repetition=repeat+1)
                results.append(result)
                destination.write_text(json.dumps(report,indent=2)+'\n')
                print('DONE',label,'responsive_ms',round(result['startup_responsive_ms'],1),flush=True)
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
    print('Saved',destination,flush=True)


if __name__=='__main__':
    main()
