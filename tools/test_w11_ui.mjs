import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { registerHooks } from "node:module";
import test from "node:test";

const ui = new URL("../branding/w11/", import.meta.url);
const brand = new URL("../branding/windows/", import.meta.url);
const read = file => readFileSync(new URL(file, ui), "utf8");
registerHooks({
  resolve(specifier, context, nextResolve) {
    const prefix = "resource://aelthoren-w11/";
    return nextResolve(
      specifier.startsWith(prefix) ? new URL(specifier.slice(prefix.length), ui).href : specifier,
      context
    );
  },
});

const engines = [];
let initSearch = async () => {};
let submittedScheme = "https";
globalThis.ChromeUtils = {
  defineESModuleGetters(lazy) {
    function engine(name) {
      engines.push(name);
      return {
        name,
        getSubmission(query, responseType, purpose) {
          assert.equal(responseType, null);
          assert.equal(purpose, "newtab");
          const uri = { scheme: submittedScheme, spec: "https://example.test/?q=" + encodeURIComponent(query) };
          return { uri, postData: "search post body" };
        },
      };
    }
    lazy.SearchService = {
      init: () => initSearch(),
      getDefault: () => engine("DuckDuckGo"),
      getDefaultPrivate: () => engine("Private engine"),
    };
  },
};
globalThis.JSWindowActorParent = class {};
globalThis.JSWindowActorChild = class {};

const sources = [];
globalThis.L10nRegistry = class {
  registerSources(files) {
    sources.push(...files);
  }
};
globalThis.L10nFileSource = class {
  constructor(name, metaSource, locales, prePath) {
    Object.assign(this, { name, metaSource, locales, prePath });
  }
};
const messages = Object.fromEntries(["en-US", "zh-CN", "zh-TW"].map(locale => [
  locale,
  new Map(read("l10n/" + locale + "/aelthoren.ftl").trim().split("\n").map(line => line.split(" = "))),
]));
globalThis.Localization = class {
  constructor(resources, sync, registry, locales) {
    assert.deepEqual(resources, ["aelthoren.ftl"]);
    this.locales = locales;
  }
  async formatValue(key, args) {
    for (const locale of this.locales) {
      const value = messages[locale].get(key);
      if (value) {
        return args ? value.replace("{ $engine }", args.engine) : value;
      }
    }
    return null;
  }
  async formatValues(keys) {
    return Promise.all(keys.map(key => this.formatValue(key)));
  }
};
globalThis.Services = {
  locale: { appLocaleAsBCP47: "en-US" },
  scriptSecurityManager: { getSystemPrincipal: () => "system" },
};
const { AelthorenParent } = await import(new URL("AelthorenParent.sys.mjs", ui));
const { AelthorenChild } = await import(new URL("AelthorenChild.sys.mjs", ui));
const { createLocalization, resolveLocale } = await import(new URL("AelthorenL10n.sys.mjs", ui));

function parent(uri = "about:newtab") {
  const actor = new AelthorenParent();
  const calls = [];
  const browser = {
    ownerGlobal: {
      PlacesCommandHook: { showPlacesOrganizer: item => calls.push(["organizer", item]) },
      openTrustedLinkIn: (...args) => calls.push(args),
    },
  };
  browser.ownerGlobal.gBrowser = { selectedBrowser: browser };
  actor.manager = {
    remoteType: "privilegedabout",
    documentURI: { spec: uri },
    documentPrincipal: { isContentPrincipal: true, URI: { spec: uri } },
  };
  actor.browsingContext = {
    loadURI: (...args) => calls.push(["loadURI", ...args]),
    currentWindowGlobal: actor.manager,
    embedderElement: browser,
  };
  actor.browsingContext.top = actor.browsingContext;
  return { actor, browser, calls };
}

test("the four shortcut commands use their fixed Gecko destinations", async () => {
  for (const url of ["about:newtab", "about:home?jscache"]) {
    const { actor, calls } = parent(url);
    for (const data of ["bookmarks", "settings", "privacy", "about"]) {
      await actor.receiveMessage({ name: "Aelthoren:Open", data });
    }
    assert.deepEqual(calls, [
      ["organizer", "AllBookmarks"],
      ["about:preferences", "current"],
      ["about:preferences#privacy", "current"],
      ["about:aelthoren", "current"],
    ]);
  }
});

test("the parent rejects unknown commands and unauthorized senders", async () => {
  const open = { name: "Aelthoren:Open", data: "settings" };
  const invalidActors = [
    parent("https://example.test/"),
    parent("about:newtab-other"),
    parent("about:aelthoren"),
    parent("about:blank"),
    parent(),
    parent(),
    parent(),
    parent(),
    parent(),
    parent(),
  ];
  invalidActors[4].actor.browsingContext.top = {};
  invalidActors[5].actor.browsingContext.currentWindowGlobal = {};
  invalidActors[6].actor.manager.remoteType = "web";
  invalidActors[7].actor.manager.documentPrincipal.isContentPrincipal = false;
  invalidActors[8].actor.manager.documentPrincipal.URI.spec = "https://example.test/";
  invalidActors[9].browser.ownerGlobal.gBrowser.selectedBrowser = {};
  for (const { actor, calls } of invalidActors) {
    await assert.rejects(actor.receiveMessage(open), /current, local new tab/);
    assert.deepEqual(calls, []);
  }

  const { actor, calls } = parent();
  for (const data of ["https://example.test/", "__proto__", { destination: "settings" }, null]) {
    await assert.rejects(actor.receiveMessage({ ...open, data }), /Unknown Aelthoren shortcut/);
  }
  await assert.rejects(actor.receiveMessage({ name: "Aelthoren:Navigate" }), /Unknown Aelthoren message/);
  assert.deepEqual(calls, []);
});

test("search uses normal and private configured engines and rejects unsafe or stale requests", async () => {
  const { actor, calls } = parent();
  assert.equal(await actor.receiveMessage({ name: "Aelthoren:GetSearchEngine" }), "DuckDuckGo");
  const search = data => actor.receiveMessage({ name: "Aelthoren:Search", data });
  await search("  海邊 & trees  ");
  actor.browsingContext.usePrivateBrowsing = true;
  await search("private");
  assert.deepEqual(engines, ["DuckDuckGo", "DuckDuckGo", "Private engine"]);
  assert.deepEqual(calls[0], [
    "loadURI",
    { scheme: "https", spec: "https://example.test/?q=" + encodeURIComponent("海邊 & trees") },
    { triggeringPrincipal: "system", postData: "search post body" },
  ]);
  for (const value of ["", "  ", "x".repeat(4097), { query: "bad" }]) {
    await assert.rejects(search(value), /Invalid search query/);
  }
  submittedScheme = "javascript";
  await assert.rejects(search("blocked"), /Unsupported search provider URL/);
  submittedScheme = "https";
  initSearch = async () => {
    actor.browsingContext.currentWindowGlobal = {};
  };
  await assert.rejects(search("in flight"), /current, local new tab/);
  initSearch = async () => {};
  assert.equal(calls.length, 2);
});

test("locale selection follows the effective UI locale with English fallback", async () => {
  for (const [input, expected] of [
    ["en-GB", "en-US"], ["fr", "en-US"], ["invalid_locale", "en-US"],
    ["zh-CN", "zh-CN"], ["zh-Hans-SG", "zh-CN"], ["zh-Hans-TW", "zh-CN"],
    ["zh-TW", "zh-TW"], ["zh-HK", "zh-TW"], ["zh-Hant", "zh-TW"],
  ]) {
    assert.equal(resolveLocale(input), expected, input);
  }
  for (const [locale, text] of [["en-US", "Bookmarks"], ["zh-CN", "书签"], ["zh-TW", "書籤"]]) {
    assert.equal(await createLocalization(locale).formatValue("open-bookmarks"), text);
  }
  assert.deepEqual(createLocalization("zh-TW").locales, ["zh-TW", "en-US"]);
  assert.equal(sources.length, 1);
  assert.deepEqual(sources[0].locales, ["en-US", "zh-CN", "zh-TW"]);
});

test("localized controls have complete strings, native keyboard semantics and strict CSP", async () => {
  const newtab = read("newtab.html");
  const about = read("about.html");
  for (const locale of Object.values(messages)) {
    for (const [, key] of (newtab + about).matchAll(/data-aelthoren-l10n="([^"]+)"/g)) {
      assert.ok(locale.has(key), key);
    }
    assert.deepEqual([...locale.keys()].sort(), [...messages["en-US"].keys()].sort());
    assert.equal(locale.get("brand-name"), "Aelthoren");
  }
  assert.match(newtab, /<label for="query"/);
  assert.match(newtab, /<button class="submit" type="submit"/);
  assert.deepEqual(
    [...newtab.matchAll(/<button type="button" data-action="([^"]+)"/g)].map(match => match[1]),
    ["bookmarks", "settings", "privacy", "about"]
  );
  for (const html of [newtab, about]) {
    assert.match(html, /default-src 'none'; img-src chrome:; style-src chrome:; form-action 'none'; base-uri 'none'/);
    assert.doesNotMatch(html, /<script\b|tabindex=|\sonclick=|rel="stylesheet" href="https:/i);
    assert.match(html, /src="chrome:\/\/branding\/content\/about-logo.svg"[^>]+alt=""/);
  }
  assert.match(read("aelthoren.css"), /:focus-visible/);
  assert.match(read("aelthoren.css"), /forced-colors: active/);
  const icon = readFileSync(new URL("aelthoren.ico", brand));
  assert.equal(icon.readUInt16LE(2), 1, "application branding uses an ICO");
});

test("child binds native controls and drops synthetic or non-activated input", async () => {
  const actor = new AelthorenChild();
  const listeners = {};
  const button = {
    getAttribute: () => "bookmarks",
    addEventListener: (name, fn) => { listeners[name] = fn; },
  };
  const form = { addEventListener: (name, fn) => { listeners[name] = fn; } };
  const input = { value: "  我的查詢  " };
  const main = { hidden: true };
  const localeNodes = [
    { getAttribute: key => key === "data-aelthoren-l10n" ? "open-bookmarks" : null },
    {
      getAttribute: key => key === "data-aelthoren-l10n" ? "shortcuts-label" : "aria-label",
      setAttribute(key, value) { this[key] = value; },
    },
  ];
  const document = actor.document = {
    documentElement: {},
    querySelector: () => main,
    querySelectorAll: selector => selector === "#shortcuts button" ? [button] : localeNodes,
    getElementById: id => ({ search: form, query: input, "action-status": {} })[id],
    hasValidTransientUserGestureActivation: true,
  };
  const dispatched = [];
  actor.sendQuery = async (name, data) => {
    if (name === "Aelthoren:GetSearchEngine") {
      return "DuckDuckGo";
    }
    dispatched.push([name, data]);
  };
  Services.locale.appLocaleAsBCP47 = "zh-TW";
  await actor.handleEvent({ type: "DOMContentLoaded", target: document });
  assert.equal(document.documentElement.lang, "zh-TW");
  assert.equal(main.hidden, false);
  assert.equal(localeNodes[0].textContent, "書籤");
  assert.equal(localeNodes[1]["aria-label"], "瀏覽器快速操作");

  listeners.click({ isTrusted: false });
  listeners.submit({ isTrusted: false, preventDefault() {} });
  document.hasValidTransientUserGestureActivation = false;
  listeners.click({ isTrusted: true });
  assert.deepEqual(dispatched, []);

  document.hasValidTransientUserGestureActivation = true;
  listeners.click({ isTrusted: true });
  listeners.submit({ isTrusted: true, preventDefault() {} });
  assert.deepEqual(dispatched, [
    ["Aelthoren:Open", "bookmarks"],
    ["Aelthoren:Search", "我的查詢"],
  ]);
});
