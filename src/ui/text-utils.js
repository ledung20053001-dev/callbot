(function exposeTextUtilities(root, factory) {
  "use strict";

  const utilities = factory();
  root.CallbotText = utilities;
  if (typeof module === "object" && module.exports) {
    module.exports = utilities;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function createTextUtilities() {
  "use strict";

  function normalizeTranscriptText(value) {
    let text = String(value ?? "")
      .normalize("NFC")
      .replace(/[\u200B-\u200D\uFEFF]/gu, "")
      .replace(/\\+([,.;:!?…])/gu, "$1")
      .replace(/\s+([,.;:!?…])/gu, "$1")
      .replace(/([,;:!?])(?=\S)/gu, "$1 ")
      .replace(/\.(?=[^\s.\d])/gu, ". ")
      .replace(/[ \t]{2,}/gu, " ")
      .trim()
      .normalize("NFC");

    if (text && !/[.!?…]["'”’)]?$/u.test(text)) text += ".";
    return text;
  }

  return Object.freeze({ normalizeTranscriptText });
});
