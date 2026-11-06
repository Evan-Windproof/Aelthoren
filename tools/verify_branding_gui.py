#!/usr/bin/env python3
"""Extra real GUI checks for the final packaged branding overlay (QA only)."""
import base64
import json
import time

WINDOW='const win=Services.wm.getMostRecentWindow("navigator:browser");'


def verify(browser,package,out):
    if browser.caps['moz:headless']:raise ValueError('Branding audit requires GUI mode')
    report=[]
    def capture(name,evidence):
        browser.b.command('Marionette:SetContext',value='chrome')
        data=browser.b.command('WebDriver:TakeScreenshot',id=None,highlights=[],full=False)
        (out/(name+'.png')).write_bytes(base64.b64decode(data))
        report.append({'page':name,'evidence':evidence,'screenshot':name+'.png'})
        (out/'branding-gui.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,url in [('newtab','about:newtab'),('settings','about:preferences#privacy'),('about','chrome://branding/content/about-aelthoren.html'),('support','about:support'),('license','about:license')]:
        browser.internal(url)
        time.sleep(1)
        text=browser.content('return document.body.innerText')
        if name in ['newtab','about']:assert 'Aelthoren' in text
        if name=='settings':
            browser.wait(lambda:browser.content('return !!document.getElementById("clearSiteDataButton")'))
            assert 'Aelthoren' in text
        capture(name,{'title':browser.content('return document.title'),'text_excerpt':text[:700]})
    browser.internal('about:preferences')
    browser.chrome(WINDOW+'const {DefaultBrowserCheck}=ChromeUtils.importESModule("moz-src:///browser/components/DefaultBrowserCheck.sys.mjs");win.__brandingPrompt=DefaultBrowserCheck.prompt(win);return true;')
    # Native dialogs reject normal WebDriver commands. Use alert APIs and an
    # authenticated Xorg screenshot from the host QA controller, then dismiss.
    text=None
    for _ in range(100):
        try:
            text=browser.b.command('WebDriver:GetAlertText');break
        except RuntimeError:time.sleep(.1)
    if text is None:raise TimeoutError('Native default browser prompt')
    (out/'default-prompt.request').write_text('capture native prompt\n')
    for _ in range(200):
        if (out/'default-browser-prompt.png').is_file():break
        time.sleep(.1)
    else:raise TimeoutError('Host GUI screenshot')
    report.append({'page':'default-browser-prompt','text':text,'screenshot':'default-browser-prompt.png','inspection':'Native dialog captured; cancel only, no default-handler change'})
    browser.b.command('WebDriver:DismissAlert')
    time.sleep(.5)
    # Read only: inspect configured product support link without opening or setting defaults.
    support=browser.chrome('return Services.prefs.getCharPref("app.support.baseURL");')
    assert support.startswith('https://github.com/Evan-Windproof/Aelthoren/')
    report.append({'check':'product support URL','url':support})
    (out/'branding-gui.json').write_text(json.dumps(report,indent=2)+'\n')
