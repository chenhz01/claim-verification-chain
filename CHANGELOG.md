# Changelog

## v0.1.2 (2026-10-12)

Round-13 fix pass (self_test rc=1, 3 failures; <40 cases):

- fix: evidence registry keys may themselves carry prefixes ("REF:bench");
  build_chain now normalizes registry keys the same way as citations, so
  [REF:bench] and [ref:bench] both resolve and links report the normalized
  evidence key
- fix: hint words missed plural "studies" ("study" is not a substring of
  "studies"); added to CLAIM_HINT_WORDS
- test correction (test was wrong): many_claims_bulk cited evidence id "2"
  which the shared EVIDENCE registry never declared (adding it would break
  nested_brackets_inner_token_captured); citations now all point at "1"
- tests added: studies-plural hint, prefixed-registry resolution, mixed
  resolved+broken claim, evidence_count, empty text, citation-only claim,
  array-registry rejection, missing-source rejection
- self tests: 42/42 PASS (34 -> 42)


## v0.1.1 (2026-10-11)

Round-2 content iteration (self-review driven):

- test coverage: 41 -> 51 self tests (+24.4%), correcting nested-bracket
  capture semantics, overlong-bracket handling, bulk 100-claim scans,
  English-only hint-word limit documentation and JSON CLI output checks
- documentation: README states the gaming second-order effect (citations
  attached without reading sources)

## v0.1.0 (2026-10-11)

Initial release:

- claim extraction: citation markers + factual hint words
- citation normalization: bare / REF: / src: / source: prefixes
- chain classification: verified / broken_links / unverified
- evidence registry JSON with source validation
- CLI: --evidence --json; exit 0/1/2 discipline
- self_test.py: 41 tests across functional / exception-path / extreme-edge
