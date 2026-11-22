# Windows W1.1 product UI

W1.1 builds on the Windows x64 source-build workflow and Firefox ESR 153.6.0esr
at `a34c4160e3f75ab9918fbe4669ff7ae56f1977c8`. Use the existing MozillaBuild
shell, toolchain, checkout, and object directory from the [W1 build guide](WINDOWS_BUILD.md).

## Update and rebuild

Start MozillaBuild with `D:\mozilla\start-shell.bat` for the existing installation.
Run these commands from that shell for the first W1.1 checkout and build.

```sh
(
  set -e
  cd d:/mozilla-source/Aelthoren
  git fetch origin codex/aelthoren-w1-1
  git switch -c w1-1-product FETCH_HEAD
  python3 tools/windows_build.py prepare
  python3 tools/windows_build.py build
  python3 tools/windows_build.py run --profile w11-acceptance
)
```

After the branch exists, switch to `w1-1-product` and update it with
`git fetch origin codex/aelthoren-w1-1` followed by
`git merge --ff-only FETCH_HEAD`. The default source remains the sibling
`aelthoren-gecko-windows` checkout. `prepare` verifies the recorded W1 overlay,
applies the pending patch set in order, and updates the branding manifest. A second
`prepare` should report `Windows overlay verified`. If verification reports a
local edit, review it with `git -C ../aelthoren-gecko-windows status --short` and
compare the generated branding files with their source inputs before retrying.

`build` configures the existing object directory, runs both W1 toolchain probes,
then invokes Mach for an incremental build. W1.1 registers `about:aelthoren` in
Gecko's built-in About registry, so the first W1.1 build must compile that
component and relink the affected binaries. Keep `obj-aelthoren-windows` in place.
The launch command above uses a separate test profile in
`%LOCALAPPDATA%\Aelthoren\Development\Profiles\profile-w11-acceptance`.

### Resource-only checks

Run the JavaScript and overlay tests directly from Aelthoren to check edits
without compiling Gecko.

```sh
node --test tools/test_w11_ui.mjs
python3 -m unittest discover -s tools -p 'test_*.py'
```

The JavaScript tests require Node 22.15 or later for the resource import hook.
For visual iteration, a temporary preview can render the checked-in HTML and CSS
with a selected Fluent file, the local logo, and inactive shortcut buttons. The
packaged pages get their labels and behavior from the browser actor.

The pinned Mach command `mach build faster` processes resources such as JS, XUL
and CSS. It is a candidate for a resource-only pass in an already configured
W1.1 checkout using the existing Windows mozconfig. Use the wrapper above for
the first W1.1 build and any change to the About registry or other compiled files.
Apply UI changes through the overlay so the tracked diff and resource hashes
remain verifiable.

## Navigation, localization and identity

The W1 shortcuts used direct document links. Gecko has no `about:bookmarks`
module. The Settings and Privacy links target a privileged About module, and the
old About shortcut points to a browser chrome resource. The W1.1 actor opens the
Places Library for bookmarks and uses fixed browser-side destinations for
Settings, Privacy and About. The sender must be the selected tab's current
top-level New Tab or Home document with the matching content principal in the
privileged-about process. The child requires a trusted user action and the parent
validates the command. The documents use a script-free CSP. Search uses the
configured normal or private search engine via Gecko's search service.

The bundled Fluent catalogs cover `en-US`, `zh-CN` and `zh-TW`. New Tab, Home,
About, and custom text in the native About dialog read Gecko's effective
application locale. Unsupported languages fall back to English. Simplified
Chinese variants use `zh-CN`, and Traditional Chinese variants use `zh-TW`.
The overlay leaves the profile's language preferences under user control.
Existing tabs can be reloaded after applying a language change.

The native window title, Settings, and default-browser prompt use Gecko's
existing brand terms. W1 already supplies the Aelthoren display name, brand
resources, and Windows icons. W1.1 adds project information and a repository
link to the native About dialog and labels the Firefox help link as upstream.
The project About page links to both licenses and Mozilla contributors. The
executable remains `firefox.exe`, and native Windows shell registration,
installer branding, updater infrastructure, and upstream help and compatibility
surfaces are outside this phase.

The three Aelthoren catalogs are bundled. The rest of the browser still needs a
compatible Gecko UI language pack for Chinese. If the local build doesn't offer
one in **Settings → General → Language**, these are the upstream ESR 153.6.0
[zh-CN pack](https://archive.mozilla.org/pub/firefox/releases/153.6.0esr/win64/xpi/zh-CN.xpi)
and [zh-TW pack](https://archive.mozilla.org/pub/firefox/releases/153.6.0esr/win64/xpi/zh-TW.xpi).
Install through **Add-ons and themes → Languages** in the test profile if Gecko
accepts the pack for this build. Upstream packs may include stock Firefox
branding in the shared browser UI. Do not change signing or compatibility
checks to install a pack. W1.1 does not distribute complete Aelthoren-branded
language packs for Gecko's chrome.

## Windows runtime acceptance

Record the Aelthoren and Firefox SHAs, the effective UI locale reported in
`about:support` under **Internationalization & Localization**, and any result
that differs from the table. Repeat the page checks for each of English,
Simplified Chinese and Traditional Chinese after selecting the language in
**Settings → General → Language** and applying the browser's restart prompt.
For the fallback check, select a compatible UI language outside those three,
such as French, and confirm the two custom pages use English.

| Check | Expected result |
| --- | --- |
| New Tab and Home | Ctrl+T and `about:home` display the branded search form and four localized shortcuts. |
| Bookmarks | The button opens Gecko's Library at All Bookmarks. Add a test bookmark beforehand and find it there. |
| Settings and Privacy | Settings opens `about:preferences`. Privacy opens `about:preferences#privacy` with the Privacy & Security section visible. |
| About | The shortcut and direct address `about:aelthoren` render the localized About page. Open each repository, license, and credits link and verify the destination. |
| Search | Enter a query with spaces and Chinese characters. Submit once with Enter and once with the button. Verify DuckDuckGo receives the full query. Open `about:newtab` in a private window and verify the configured private engine there. |
| Keyboard and accessibility | Tab from the search field through Search, Bookmarks, Settings, Privacy controls and About. Use Shift+Tab to reverse. Activate the buttons with Space and Enter. Verify visible focus and accessible names with a screen reader. |
| Layout | In light and dark mode, narrow the window and zoom to 200%. Check that text wraps, controls stay visible, and the page remains scrollable without horizontal overflow. |
| Identity | Check the window title, Settings, native About, default-browser prompt if shown, and taskbar icon. Native About should link to the project and identify Mozilla's Firefox help. |
| Privacy | `about:policies` shows account disabling and the normal/private DuckDuckGo defaults. Settings still omit the integrated account pane. The About page explicitly describes the limits of tracking protection. |
| Privilege boundary | On New Tab, synthetic `button.click()` or script-dispatched submit on the page should leave the tab unchanged. A web page should have no Aelthoren actor. Confirm browser console reports no actor errors during valid actions. |

## Files and verification

- `branding/w11/` contains both pages, shared CSS, the actor modules and all three Fluent catalogs.
- `patches/0005-w11-product-ui.patch` registers the actor and About page, moves New Tab and Home to the W1.1 resources, replaces the W1 search bridge and updates the native About dialog.
- `tools/windows_build.py` packages and hashes the new resources and upgrades verified W1 overlays.
- `tools/test_windows_build.py` and `tools/test_w11_ui.mjs` cover upgrade and rollback, the four actions, locale selection, search behavior, branding resources, keyboard semantics and authorization checks.

On Linux, all 27 Python tooling tests and six Node UI tests passed. Fresh
preparation, an upgrade from W1, and a repeated integrity check passed at the
locked revision. Gecko's jar maker resolved all W1.1 resources in the generated
branding manifest. Gecko's Fluent parser accepted all three catalogs. A separate
Firefox ESR 153.6.0 Linux runtime formatted each language and the English
fallback through the shipped localization module. The cloud sandbox could not
keep Gecko content processes running for an end-to-end actor test.

The native Windows incremental build, signed language pack compatibility, live
browser navigation, and visual and assistive-technology acceptance are pending.
