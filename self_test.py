#!/usr/bin/env python3
"""Self-test for claim-verification-chain. Pure stdlib. Run: python self_test.py"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_verification_chain as cvc  # noqa: E402

TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


EVIDENCE = {
    "1": {"source": "Annual Report 2025", "url": "https://example.com/ar"},
    "REF:bench": {"source": "Benchmark Study", "url": "https://example.com/bench"},
}


def expect_chain_error(fn, *a, **kw):
    try:
        fn(*a, **kw)
    except cvc.ChainError:
        return
    raise AssertionError("expected ChainError")


def wf(text, name="f"):
    d = tempfile.mkdtemp()
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return d, p


def cleanup(d):
    shutil.rmtree(d)


# ---------------- functional unit tests ----------------

@test("split_basic_sentences")
def _():
    assert cvc.split_sentences("One. Two. Three.") == ["One.", "Two.", "Three."]


@test("split_keeps_abbrev_robust_enough")
def _():
    s = cvc.split_sentences("Value rose 5%. Costs fell. Done.")
    assert len(s) == 3


@test("citations_extracted_simple")
def _():
    assert cvc.extract_citations("costs rose [1] sharply.") == ["1"]


@test("citations_multiple_unique")
def _():
    assert cvc.extract_citations("x [1] and y [1] and z [REF:bench]") == ["1", "REF:bench"]


@test("claim_by_citation_only")
def _():
    claims = cvc.extract_claims("Anything at all [1].")
    assert len(claims) == 1 and claims[0]["citations"] == ["1"]


@test("claim_by_hint_word")
def _():
    claims = cvc.extract_claims("According to the study, birds fly.")
    assert len(claims) == 1 and claims[0]["hint"] is True


@test("plain_opinion_not_claim")
def _():
    assert cvc.extract_claims("I like turtles. The sky is blue today, honestly.") == []


@test("verified_chain_built")
def _():
    r = cvc.analyze("Costs rose 3% [1].", EVIDENCE)
    assert len(r["verified"]) == 1 and r["verified"][0]["links"][0]["evidence"] == "1"


@test("ref_prefix_normalized")
def _():
    r = cvc.analyze("Benchmark improved [REF:bench].", EVIDENCE)
    assert len(r["verified"]) == 1 and r["verified"][0]["links"][0]["evidence"] == "bench"


@test("broken_link_reported")
def _():
    r = cvc.analyze("Data show growth [99].", EVIDENCE)
    assert len(r["broken_links"]) == 1 and r["broken_links"][0]["missing_citations"] == ["99"]


@test("unverified_claim_reported")
def _():
    r = cvc.analyze("Studies show improvements everywhere.", EVIDENCE)
    assert len(r["unverified"]) == 1


@test("mixed_report_counts")
def _():
    text = "A rose 5% [1]. B fell according to study. C grew 2% [77]."
    r = cvc.analyze(text, EVIDENCE)
    assert r["claims_total"] == 3
    assert len(r["verified"]) == 1 and len(r["unverified"]) == 1 and len(r["broken_links"]) == 1


@test("format_report_lines")
def _():
    r = cvc.analyze("Data show growth [99].", EVIDENCE)
    text = cvc.format_report(r)
    assert "BROKEN" in text


@test("cli_end_to_end_exit_1")
def _():
    d1, tp = wf("Data show growth [99].")
    d2, ep = wf(json.dumps(EVIDENCE))
    try:
        assert cvc.main([tp, "--evidence", ep]) == 1
    finally:
        cleanup(d1), cleanup(d2)


@test("cli_clean_exit_0")
def _():
    d1, tp = wf("Growth was 5% [1].")
    d2, ep = wf(json.dumps(EVIDENCE))
    try:
        assert cvc.main([tp, "--evidence", ep]) == 0
    finally:
        cleanup(d1), cleanup(d2)


@test("source_field_carried_into_links")
def _():
    r = cvc.analyze("Rose 5% [1].", EVIDENCE)
    assert r["verified"][0]["links"][0]["source"] == "Annual Report 2025"


# ---------------- exception-path tests ----------------

@test("missing_evidence_file_raises")
def _():
    expect_chain_error(cvc.load_evidence, os.path.join(tempfile.mkdtemp(), "no.json"))


@test("evidence_corrupt_json_raises")
def _():
    d, p = wf("{broken", "e.json")
    try:
        expect_chain_error(cvc.load_evidence, p)
    finally:
        cleanup(d)


@test("evidence_array_rejected")
def _():
    d, p = wf("[1,2]", "e.json")
    try:
        expect_chain_error(cvc.load_evidence, p)
    finally:
        cleanup(d)


@test("evidence_entry_missing_source_raises")
def _():
    d, p = wf(json.dumps({"1": {"url": "x"}}), "e.json")
    try:
        expect_chain_error(cvc.load_evidence, p)
    finally:
        cleanup(d)


@test("evidence_entry_not_object_raises")
def _():
    d, p = wf(json.dumps({"1": "a string"}), "e.json")
    try:
        expect_chain_error(cvc.load_evidence, p)
    finally:
        cleanup(d)


@test("non_string_text_raises")
def _():
    expect_chain_error(cvc.split_sentences, 42)


@test("missing_text_file_exit_2")
def _():
    d, ep = wf(json.dumps(EVIDENCE))
    try:
        assert cvc.main([os.path.join(d, "ghost.txt"), "--evidence", ep]) == 2
    finally:
        cleanup(d)


@test("invalid_utf8_text_exit_2")
def _():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "bin.txt")
    with open(p, "wb") as f:
        f.write(b"\xff\xfe")
    d2, ep = wf(json.dumps(EVIDENCE))
    try:
        assert cvc.main([p, "--evidence", ep]) == 2
    finally:
        cleanup(d), cleanup(d2)


# ---------------- extreme-edge tests ----------------

@test("empty_text_no_claims")
def _():
    r = cvc.analyze("", EVIDENCE)
    assert r["claims_total"] == 0 and r["unverified"] == []


@test("empty_evidence_registry")
def _():
    r = cvc.analyze("Data show growth [1].", {})
    assert len(r["broken_links"]) == 1


@test("unicode_claims_and_citations")
def _():
    text = "据研究，成本上升了 5% [1]。"
    r = cvc.analyze(text, EVIDENCE)
    assert len(r["verified"]) == 1


@test("long_sentence_truncated_in_claim_text")
def _():
    long = "Data show " + "word " * 200 + "[1]."
    r = cvc.analyze(long, EVIDENCE)
    assert len(r["verified"][0]["text"]) <= 301


@test("overlong_citation_bracket_ignored")
def _():
    long_token = "x" * 100
    text = "Data show growth [%s]." % long_token
    r = cvc.analyze(text, EVIDENCE)
    # bracket too long to be a citation -> claim detected by hint, left unverified
    assert len(r["unverified"]) == 1 and r["broken_links"] == []


@test("many_claims_bulk")
def _():
    # all citations point at evidence id "1" (the only bare id in the registry)
    text = " ".join("Fact %d rose 3%% [1]." % i for i in range(100))
    r = cvc.analyze(text, EVIDENCE)
    assert r["claims_total"] == 100 and len(r["verified"]) == 100


@test("nested_brackets_inner_token_captured")
def _():
    text = "Data show [see [2] inner] growth [1]."
    r = cvc.analyze(text, EVIDENCE)
    # inner [2] is captured and unresolved -> the chain is broken even though [1] resolves
    assert len(r["broken_links"]) == 1 and r["broken_links"][0]["missing_citations"] == ["2"]


@test("claim_text_stored_trimmed")
def _():
    r = cvc.analyze("  Data show growth [1].  ", EVIDENCE)
    assert r["verified"][0]["text"].startswith("Data")


@test("json_report_parseable")
def _():
    d1, tp = wf("Growth was 5% [1].")
    d2, ep = wf(json.dumps(EVIDENCE))
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cvc.main([tp, "--evidence", ep, "--json"])
        data = json.loads(buf.getvalue())
        assert data["claims_total"] == 1
    finally:
        cleanup(d1), cleanup(d2)


@test("hint_words_multilingual_english_only_limit")
def _():
    claims = cvc.extract_claims("研究发现增长率很高。")
    assert claims == []  # known limit: hint words are English-only


@test("studies_plural_hint_triggers_claim")
def _():
    r = cvc.analyze("Studies show a 10% lift.", EVIDENCE)
    assert r["claims_total"] == 1 and len(r["unverified"]) == 1


@test("registry_key_with_prefix_resolves")
def _():
    r = cvc.analyze("Benchmark improved [REF:bench] and again [ref:bench].", EVIDENCE)
    assert len(r["verified"]) == 1 and len(r["verified"][0]["links"]) == 2


@test("mixed_prefix_and_broken_in_one_claim")
def _():
    r = cvc.analyze("Data show growth [1] [ghost].", EVIDENCE)
    assert len(r["broken_links"]) == 1 and r["broken_links"][0]["missing_citations"] == ["ghost"]


@test("evidence_count_reported")
def _():
    r = cvc.analyze("Data show growth [1].", EVIDENCE)
    assert r["evidence_count"] == 2


@test("empty_text_no_claims")
def _():
    r = cvc.analyze("", EVIDENCE)
    assert r["claims_total"] == 0 and r["verified"] == []


@test("citation_without_hint_is_claim")
def _():
    r = cvc.analyze("The sky is clear [1].", EVIDENCE)
    assert r["claims_total"] == 1 and len(r["verified"]) == 1


@test("load_evidence_rejects_array")
def _():
    d, p = wf(json.dumps([1, 2]))
    try:
        expect_chain_error(cvc.load_evidence, p)
    finally:
        cleanup(d)


@test("load_evidence_missing_source_rejected")
def _():
    d, p = wf(json.dumps({"x": {"url": "https://example.com"}}))
    try:
        expect_chain_error(cvc.load_evidence, p)
    finally:
        cleanup(d)


def main():
    passed = failed = 0
    for name, fn in TESTS:
        try:
            fn()
            passed += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL %s: %r" % (name, exc))
    print("passed=%d failed=%d total=%d" % (passed, failed, passed + failed))
    print("SUMMARY: PASS %d/%d" % (passed, passed + failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
