/* SPDX-License-Identifier: MIT */

const lazy = {};
ChromeUtils.defineESModuleGetters(lazy, {
  SearchService: "moz-src:///toolkit/components/search/SearchService.sys.mjs",
});

const PREFS = "about:preferences";
const ABOUT = "about:aelthoren";
const NEW_TAB = ["about:newtab", "about:home"];

export class AelthorenParent extends JSWindowActorParent {
  #activeBrowser({ requireSelected = true } = {}) {
    const context = this.browsingContext;
    const global = this.manager;
    const uri = global?.documentURI?.spec.split(/[?#]/)[0];
    const principal = global?.documentPrincipal;
    const browser = context?.embedderElement;
    const win = browser?.ownerGlobal;
    if (
      !context ||
      context !== context.top ||
      global !== context.currentWindowGlobal ||
      global?.remoteType !== "privilegedabout" ||
      !NEW_TAB.includes(uri) ||
      !principal?.isContentPrincipal ||
      principal.URI?.spec.split(/[?#]/)[0] !== uri ||
      !win?.gBrowser ||
      (requireSelected && win.gBrowser.selectedBrowser !== browser)
    ) {
      throw new Error("Aelthoren requests require a current, local new tab");
    }
    return browser;
  }

  async receiveMessage({ name, data }) {
    switch (name) {
      case "Aelthoren:Open": {
        const browser = this.#activeBrowser();
        const win = browser.ownerGlobal;
        switch (data) {
          case "bookmarks":
            win.PlacesCommandHook.showPlacesOrganizer("AllBookmarks");
            return null;
          case "settings":
          case "privacy":
          case "about": {
            const destination = {
              settings: PREFS,
              privacy: PREFS + "#privacy",
              about: ABOUT,
            }[data];
            win.openTrustedLinkIn(destination, "current");
            return null;
          }
          default:
            throw new Error("Unknown Aelthoren shortcut");
        }
      }
      case "Aelthoren:GetSearchEngine":
      case "Aelthoren:Search": {
        const search = name === "Aelthoren:Search";
        this.#activeBrowser({ requireSelected: search });
        const query = search && typeof data === "string" ? data.trim() : "";
        if (search && (!query || data.length > 4096)) {
          throw new Error("Invalid search query");
        }
        const context = this.browsingContext;
        await lazy.SearchService.init();
        const engine = context.usePrivateBrowsing
          ? await lazy.SearchService.getDefaultPrivate()
          : await lazy.SearchService.getDefault();
        this.#activeBrowser({ requireSelected: search });
        if (!search) {
          return engine?.name ?? "";
        }
        const submission = engine?.getSubmission(query, null, "newtab");
        if (!submission || !["http", "https"].includes(submission.uri.scheme)) {
          throw new Error("Unsupported search provider URL");
        }
        context.loadURI(submission.uri, {
          triggeringPrincipal: Services.scriptSecurityManager.getSystemPrincipal(),
          postData: submission.postData,
        });
        return null;
      }
      default:
        throw new Error("Unknown Aelthoren message");
    }
  }
}
