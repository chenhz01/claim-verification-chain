# claim-verification-chain

A structural claim-to-evidence chain checker. Extracts claims from text (citation markers or factual hint patterns), maps every citation to a declared evidence registry, and reports verified links, broken links, and unverified claims. Structure only — never judges truth. Pure stdlib, offline, deterministic.

**Status:** v0.1.1 · Confidence: high (structural checks), medium (claim detection heuristics) · as of 2026-10-11

## Problem

AI-generated reports state facts — "costs rose 3% [5]" — where citation [5] may not exist, or the claim carries no citation at all. Fact-checking models judge *truth*; nobody cheaply checks the *mechanics*: does every claim-bearing sentence carry evidence links, and do those links resolve to a declared evidence registry?

## How it works

1. **Extract**: text is split into sentences; sentences with `[citation]` markers or factual hints ("according to", "%", "study", "measured"…) become claims.
2. **Map**: each citation token (`[1]`, `[REF:abc]`, `[src:3]`) is normalized and looked up in the evidence registry (JSON: id → source/url).
3. **Classify**: verified (all citations resolve), broken links (some citation not in registry), unverified (claim with no citations). Exit `1` if any broken or unverified; `2` on bad input. This is a *structure* check — the tool never decides whether a claim is true.

## Quickstart

```bash
# ~0.6 s total [measured; reproduce: python self_test.py]
python self_test.py

cat > evidence.json <<'EOF'
{"1": {"source": "Annual Report 2025", "url": "https://example.com/ar"},
 "bench": {"source": "Benchmark Study", "url": "https://example.com/b"}}
EOF
python claim_verification_chain.py report.md --evidence evidence.json   # ~0.1 s
# BROKEN c2: citations 99 not in registry
# UNVERIFIED c3: Studies show improvements everywhere.
```

## Why not X

| Alternative | Stars | Why not this |
| --- | --- | --- |
| [dwadden/multivers](https://github.com/dwadden/multivers) | 54 ★ | A trained model + checkpoints for scientific claim verification — judges truth, needs GPUs and model weights. This checks chain structure deterministically with zero model calls. |
| [ASoleimaniB/BERT_FEVER](https://github.com/ASoleimaniB/BERT_FEVER) | 34 ★ | BERT-based evidence retrieval and verification for FEVER-style tasks: ML pipeline, training data, inference cost. Here the registry is explicit and the check is instant. |
| [Shabbyshambles/psyloblock](https://github.com/Shabbyshambles/psyloblock) | 0 ★ | A hallucination checking tool at the response level; this operates at the citation-chain level and is reproducible without any model. |

## Minimal Fallback

If you cannot run this: grep your document for `%`, "according to", and "study", then grep for `\[` citations, and diff the citation IDs against your bibliography list. That is the same check, done by hand.

## Design Trade-offs

- **Structure, not truth** — a claim citing a real but irrelevant source still passes. Catching relevance is a model-layer job; mixing the two makes checks flaky.
- **Hint-word claim detection** — English keyword list; false negatives for unusual phrasing, false positives for rhetorical sentences. Deliberately coarse and explainable.
- **Registry is explicit JSON** — no automatic source fetching; the curator owns the mapping. Less magic, fully auditable.
- **One bad citation fails the claim** — no partial credit; simplest policy to act on.

## Limits & Second-order Effects

- Non-English claims are detected only via citations (hint words are English-only) — documented, tested as a known limit.
- Sentence splitting is heuristic; heavy abbreviations ("Dr. Smith said 3%…") may merge or split sentences oddly.
- Second-order: writers may game the check by attaching a random-but-registered citation everywhere. The tool makes that visible (links are listed per claim) but not impossible — curation stays human.
- The registry itself is trusted input; a wrong source string is faithfully reported.

## FAQ

**When NOT to use this?**
When you need to know whether claims are *true* (use an evidence-retrieval model), when your documents have no citation convention at all, or when claims appear in structured data rather than prose.

**Does it fetch URLs?** Never — offline only; URLs in the registry are not contacted.

**Can one citation cover multiple claims?** Yes — registry entries are shared; each claim lists its own links.

**What counts as a citation?** `[token]` up to 60 chars of letters/digits/`;:, _-`, e.g. `[1]`, `[REF:abc]`, `[src:3,5]`.

## Core Assumptions

1. Documents carry explicit citation markers; if they don't, the tool can only flag hint-based claims as unverified.
2. An evidence registry exists or can be maintained by a human curator.
3. Chain completeness (every claim linked, every link resolvable) is a useful, testable property independent of truth.
4. Determinism and auditability matter more than coverage for this layer.

## LICENSE

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 zhengming contributors.
Contact: hcac4735@agent.qq.com

---

Part of the [zhengming-toolbox](https://github.com/chenhz01/zhengming-toolbox) — 55 purpose-built AI-engineering tools across neglected niches.

Related tools: [lock-contract-test](https://github.com/chenhz01/lock-contract-test) · [csv-dialect-fingerprint](https://github.com/chenhz01/csv-dialect-fingerprint) · [md-table-lint](https://github.com/chenhz01/md-table-lint)
