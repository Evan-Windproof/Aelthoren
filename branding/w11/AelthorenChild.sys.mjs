/* SPDX-License-Identifier: MIT */

import {
  createLocalization,
  localizeDocument,
  resolveLocale,
} from "resource://aelthoren-w11/AelthorenL10n.sys.mjs";

export class AelthorenChild extends JSWindowActorChild {
  #engine = "";

  async handleEvent(event) {
    const document = this.document;
    if (event.target !== document) {
      return;
    }
    const main = document.querySelector("main.newtab, main.about");
    if (!main) {
      return;
    }

    const form = document.getElementById("search");
    if (event.type === "DOMContentLoaded" && form) {
      const input = document.getElementById("query");
      const status = document.getElementById("action-status");
      const send = async (name, data) => {
        status.textContent = "";
        try {
          await this.sendQuery(name, data);
        } catch (error) {
          if (this.manager?.isCurrentGlobal) {
            const locale = resolveLocale(Services.locale.appLocaleAsBCP47);
            status.textContent =
              await createLocalization(locale).formatValue("action-failed");
            console.error(error);
          }
        }
      };

      form.addEventListener("submit", event => {
        event.preventDefault();
        const query = input.value.trim();
        if (
          event.isTrusted && document.hasValidTransientUserGestureActivation && query
        ) {
          send("Aelthoren:Search", query);
        }
      });

      for (const button of document.querySelectorAll("#shortcuts button")) {
        const action = button.getAttribute("data-action");
        button.addEventListener("click", event => {
          if (event.isTrusted && document.hasValidTransientUserGestureActivation) {
            send("Aelthoren:Open", action);
          }
        });
      }

      this.sendQuery("Aelthoren:GetSearchEngine").then(
        async engine => {
          this.#engine = engine;
          await this.#localize(document, main);
        },
        () => {} // Keep the generic placeholder if the search service is unavailable.
      ).catch(console.error);
    }

    await this.#localize(document, main);
  }

  async #localize(document, main) {
    const locale = resolveLocale(Services.locale.appLocaleAsBCP47);
    const l10n = createLocalization(locale);
    await localizeDocument(document, l10n);
    document.documentElement.lang = locale;
    const input = document.getElementById("query");
    if (input && this.#engine) {
      const placeholder = await l10n.formatValue("search-engine", {
        engine: this.#engine,
      });
      if (placeholder) {
        input.placeholder = placeholder;
      }
    }
    main.hidden = false;
  }
}
