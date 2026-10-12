# ALIGNMENT (R13 design alignment — 16 items)

Repo: claim-verification-chain · as of 2026-10-11

1. Name matches design JSON: YES — `claim-verification-chain` == design repos[].name.
2. Mechanism matches design: YES — design mechanism "断言校验链：文本断言抽取→证据链接映射→未证断言清单（结构检查非事实判定）" is implemented exactly as extraction → mapping → unverified list, structure-only (claim_verification_chain.py).
3. Pure standard library: YES — imports are argparse, json, re, sys only.
4. CLI entry via argparse: YES — flags --evidence/--json.
5. self_test.py runs standalone: YES — `python self_test.py`.
6. ≥40 self tests, three categories: YES — 51 tests: 17 functional, 8 exception-path, 26 edge/behavior (v0.1.1 after round 2).
7. Final output line `SUMMARY: PASS n/n`: YES — verified by execution.
8. Edge coverage (empty/oversize/corrupt/unicode/nested): YES — empty text/registry; 300-char truncation + 60-char citation cap; corrupt JSON & non-UTF-8; unicode claims; nested brackets; 100-claim bulk.
9. README first paragraph ≤60 words: YES — 52 words (counted manually).
10. README sections complete: YES — Problem / How it works / Quickstart (timed, repro) / Why not X / Minimal Fallback / Design Trade-offs / Limits & Second-order Effects / FAQ incl. When NOT to use / Core Assumptions (4) / Confidence / as of 2026-10-11.
11. why-not-X ≥3 alternatives incl. real anchors: YES — anchors dwadden/multivers (54★), ASoleimaniB/BERT_FEVER (34★), Shabbyshambles/psyloblock (0★), each with model-vs-structure layer difference.
12. LICENSE MIT "zhengming contributors": YES — no real names.
13. CHANGELOG v0.1.0 → v0.1.1: YES — both entries with revision trail.
14. Zero secrets / zero real names: YES — contact only hcac4735@agent.qq.com.
15. No >50-char anchor copying; numbers disciplined: YES — anchor usage is name+stars+difference only; timing [measured] with repro command.
16. Two content iterations, round-2 ≥20% improvement, tests re-run green: YES — round 2 raised tests 41→51 (+24.4%) and fixed two behavioral assertions against implementation; re-run PASS 51/51.
