import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { normalizeTranscriptText } = require("../../src/ui/text-utils.js");


test("keeps Vietnamese text in NFC form", () => {
  const decomposed = "Nguye\u0302\u0303n Va\u0306n A";
  const result = normalizeTranscriptText(decomposed);

  assert.equal(result, "Nguyễn Văn A.");
  assert.equal(result, result.normalize("NFC"));
});

test("removes an escaped punctuation backslash", () => {
  assert.equal(normalizeTranscriptText("Lê Công Dũng \\."), "Lê Công Dũng.");
});

test("removes spaces before punctuation and restores spaces after it", () => {
  assert.equal(
    normalizeTranscriptText("Xin chào ,tôi muốn xác nhận lịch !"),
    "Xin chào, tôi muốn xác nhận lịch!",
  );
});

test("does not duplicate existing sentence punctuation", () => {
  assert.equal(normalizeTranscriptText("Anh/chị có đồng ý không?"), "Anh/chị có đồng ý không?");
});

test("removes zero-width characters introduced by copied text", () => {
  assert.equal(normalizeTranscriptText("xin\u200B chào"), "xin chào.");
});
