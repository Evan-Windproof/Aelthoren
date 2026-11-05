#!/usr/bin/env python3
"""Run preserved privacy tests and a desktop background-tab timer regression."""
import http.server
import json
from pathlib import Path
import threading
import time
import uuid

import benchmark_phase4 as perf
from run_aelthoren import prepare_profile
import verify_phase3 as privacy_tests


def main():
    destination=perf.ROOT/'docs/phase4/regression-results.json'
    if destination.exists():
        raise ValueError('Preserve previous regression results first')
    work=perf.WORK/('regression-'+uuid.uuid4().hex[:10])
    work.mkdir(parents=True)
    privacy_tests.OUTPUT=work/'privacy'
    (privacy_tests.OUTPUT/'initial-failures').mkdir(parents=True)
    privacy_tests.main()
    privacy=json.loads((privacy_tests.OUTPUT/'runtime-summary.json').read_text())
    assert privacy['result']=='PASS' and privacy['checks']==25
    name='phase4-background-'+uuid.uuid4().hex[:10]
    profile=prepare_profile(name)
    (profile/'user.js').write_text('user_pref("remote.prefs.recommended",false);\nuser_pref("network.proxy.no_proxies_on","127.0.0.1");\n')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',8766),perf.Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    browser=None
    try:
        browser=perf.Session(name,name)
        browser.b.command('Marionette:SetContext',value='content')
        original=browser.b.command('WebDriver:GetWindowHandle')
        before=browser.content('return Number(document.documentElement.dataset.tick||0);')
        tab=browser.b.command('WebDriver:NewWindow',type='tab',focus=True)
        browser.b.command('WebDriver:SwitchToWindow',handle=tab['handle'])
        browser.b.command('WebDriver:Navigate',url='http://127.0.0.1:8766/background-control')
        browser.frame()
        assert browser.chrome(perf.WINDOW+'return win.gBrowser.selectedTab!==win.gBrowser.tabs[0];')
        time.sleep(4)
        browser.b.command('Marionette:SetContext',value='content')
        browser.b.command('WebDriver:SwitchToWindow',handle=original)
        after=browser.content('return Number(document.documentElement.dataset.tick||0);')
        assert after>before,(before,after)
        result={'result':'PASS','phase3_checks':privacy['checks'],'phase3_source_revision':privacy['source_revision'],'phase3_evidence_directory':str(privacy_tests.OUTPUT),'desktop_background_timer':{'before':before,'after':after,'background_seconds':4,'result':'PASS'},'desktop_headless':browser.capabilities['moz:headless'],'profile':str(profile)}
    finally:
        if browser:
            browser.close()
        server.shutdown()
        server.server_close()
    assert browser.exit_code==0
    result['desktop_exit_code']=browser.exit_code
    result['privacy_checks']=json.loads((privacy_tests.OUTPUT/'runtime-results.json').read_text())
    result['effective_preferences']=json.loads((privacy_tests.OUTPUT/'effective-preferences.json').read_text())
    destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
