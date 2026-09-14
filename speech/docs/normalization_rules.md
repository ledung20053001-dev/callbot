# Vietnamese identity normalization rules

## Principle

Normalization changes representation, never identity meaning. Always retain the
raw transcript and attach normalization status. A database candidate must never
be used to "correct" recognized speech silently.

Recommended result shape:

```json
{
  "raw_text": "NGUYỄN  VĂN AN.",
  "normalized_text": "nguyễn văn an",
  "status": "normalized",
  "warnings": [],
  "normalizer_version": "vi-identity-v1"
}
```

## Safe, context-independent transforms

Applied to a comparison key, not to `raw_text`:

1. Unicode-normalize to NFC. Do not strip Vietnamese diacritics.
2. Trim outer whitespace and collapse internal Unicode whitespace to one space.
3. Apply Unicode-aware lowercase/case-fold for comparison.
4. Remove only surrounding sentence punctuation when the field is already known
   to be a full name or DOB utterance.
5. Preserve token order, accents, `đ`, and all alphanumeric characters.

Examples:

| Input | Comparison form | Safe? |
|---|---|---:|
| `NGUYỄN VĂN AN` | `nguyễn văn an` | Yes |
| `Nguyễn   Văn   An` | `nguyễn văn an` | Yes |
| `Nguyễn Văn An.` | `nguyễn văn an` | Yes, in a name field |
| `Nguyễn Văn Anh` | `nguyễn văn an` | **No** |
| `Ân` | `An` | **No** |

## Full names

- Preserve every recognized token and diacritic. Do not fuzzy-correct
  `An/Anh/Ân`, `Hà/Hạ`, `Minh/Mình`, or similar names.
- Honorifics such as `anh`, `chị`, `cô`, `chú` may be removed only when captured
  separately by a grammar and never based on a patient database match.
- Do not reorder Vietnamese names into given-name-first form.
- Fuzzy or accent-insensitive matching may generate candidates for explicit user
  confirmation; it must not select or mutate an identity.

## Digits and dates

Text-to-number conversion is contextual parsing, not generic replacement.

- Parse a complete DOB only when a date grammar identifies day, month, and year.
- Canonical output is ISO `YYYY-MM-DD`; retain the spoken/raw form alongside it.
- Validate calendar reality, including leap years. Reject `31/04` and similar
  impossible dates.
- Accept lexical variants such as `mùng một`, `ngày một`, `tháng tư`, `tháng bốn`,
  and `lẻ/linh` only when the resulting value is unambiguous.
- Preserve leading-zero semantics only in the formatted canonical value.
- A two-digit year such as `bảy tám` has no century without an explicit policy or
  confirmation. Return `ambiguous`, not `1978`.
- Digit-by-digit speech (`một chín bảy tám`) and cardinal speech
  (`một nghìn chín trăm bảy mươi tám`) are different grammars. Convert only after
  the grammar is identified with high confidence.

Suggested parse result:

```json
{
  "raw_text": "Mười bốn tháng ba năm bảy tám",
  "normalized_date": null,
  "status": "ambiguous",
  "warnings": ["TWO_DIGIT_YEAR_REQUIRES_CONFIRMATION"]
}
```

## Punctuation and fillers

- Punctuation may be ignored for field comparison but remains in `raw_text`.
- Fillers (`à`, `ừm`) may be removed only by a field-specific parser and must not
  join or split identity tokens.
- Never remove a word merely because it is absent from the patient database.

## Decision outcomes

Every identity normalizer returns one of:

- `normalized`: safe canonical form produced.
- `unchanged`: no safe transformation needed.
- `ambiguous`: multiple semantic values remain; ask the caller to repeat/confirm.
- `invalid`: the utterance cannot represent a valid value.

No low-confidence or ambiguous result may be promoted to `normalized` silently.

## Required tests for Day 2

- NFC versus decomposed Vietnamese diacritics.
- Multiple spaces and surrounding punctuation.
- `An/Anh/Ân`, `Hà/Hạ`, `Minh/Mình` non-equivalence.
- Leap day, invalid calendar date, and day/month boundaries.
- Full four-digit year, digit-by-digit year, and ambiguous two-digit year.
- Idempotence: `normalize(normalize(x)) == normalize(x)` for canonical values.
