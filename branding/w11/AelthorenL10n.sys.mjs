/* SPDX-License-Identifier: MIT */

const LOCALES = ["en-US", "zh-CN", "zh-TW"];
const RESOURCE = "aelthoren.ftl";
const SELECTOR = "[data-aelthoren-l10n]";
let registry;

export function resolveLocale(appLocale) {
  try {
    const { language, script, region } = new Intl.Locale(appLocale);
    if (language === "zh") {
      if (script === "Hant" || (!script && ["TW", "HK", "MO"].includes(region))) {
        return "zh-TW";
      }
      return "zh-CN";
    }
  } catch (error) {
    if (!(error instanceof RangeError)) {
      throw error;
    }
  }
  return "en-US";
}

export function createLocalization(locale) {
  if (!registry) {
    registry = new L10nRegistry();
    registry.registerSources([
      new L10nFileSource(
        "aelthoren",
        "app",
        LOCALES,
        "resource://aelthoren-w11/l10n/{locale}/"
      ),
    ]);
  }
  return new Localization(
    [RESOURCE],
    false,
    registry,
    locale === "en-US" ? ["en-US"] : [locale, "en-US"]
  );
}

export async function localizeDocument(document, l10n) {
  const nodes = [...document.querySelectorAll(SELECTOR)];
  const values = await l10n.formatValues(
    nodes.map(node => node.getAttribute("data-aelthoren-l10n"))
  );
  for (let index = 0; index < nodes.length; index++) {
    const value = values[index];
    if (value === null) {
      continue;
    }
    const node = nodes[index];
    const attribute = node.getAttribute("data-aelthoren-attr");
    if (["aria-label", "placeholder", "value"].includes(attribute)) {
      node.setAttribute(attribute, value);
    } else {
      node.textContent = value;
    }
  }
}
