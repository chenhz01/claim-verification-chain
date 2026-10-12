#!/usr/bin/env python3
"""claim-verification-chain: structural claim-to-evidence chain checker.

Extracts candidate claims from text (sentences with citation markers or
factual hint patterns), maps each citation to a declared evidence registry,
and reports the chain: verified (linked + resolvable), broken links (citation
points to unknown evidence), and unverified claims (no citation at all).
This is a STRUCTURE check, not a fact check: it never judges whether a claim
is true, only whether every claim carries evidence links that resolve.
Pure standard library, deterministic, offline.
"""
import argparse
import json
import re
import sys

CITATION_RE = re.compile(r"\[([A-Za-z0-9_\-:;, ]{1,60})\]")
CLAIM_HINT_WORDS = ("according to", "proven", "shown", "study", "studies", "survey",
                    "report", "research", "percent", "%", "increase", "decrease",
                    "measured", "benchmark", "statistics", "data show", "found that")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\u4e00-\u9fff\"'])")


class ChainError(Exception):
    """Raised for unreadable or malformed inputs."""


def load_evidence(path):
    """Evidence registry: {"id": {"source": str, "url": str, ...}}."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise ChainError("cannot read evidence file: %s" % exc)
    except json.JSONDecodeError as exc:
        raise ChainError("evidence file is not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise ChainError("evidence registry must be a JSON object")
    for eid, spec in data.items():
        if not isinstance(spec, dict):
            raise ChainError("evidence %r must be an object" % eid)
        if not spec.get("source"):
            raise ChainError("evidence %r is missing 'source'" % eid)
    return data


def split_sentences(text):
    if not isinstance(text, str):
        raise ChainError("text must be a string")
    parts = SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def extract_citations(sentence):
    """Return unique citation tokens like '1', 'REF:abc', 'src:3'."""
    seen, tokens = set(), []
    for match in CITATION_RE.finditer(sentence):
        token = match.group(1).strip()
        if token and token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens


def looks_like_claim(sentence):
    low = sentence.lower()
    return any(w in low for w in CLAIM_HINT_WORDS)


def extract_claims(text):
    """Return claim dicts: {"id", "text", "citations", "hint"} in order."""
    claims = []
    for idx, sentence in enumerate(split_sentences(text), 1):
        citations = extract_citations(sentence)
        hinted = looks_like_claim(sentence)
        if citations or hinted:
            claims.append({"id": "c%d" % idx, "text": sentence[:300],
                           "citations": citations, "hint": hinted})
    return claims


def build_chain(claims, evidence):
    """Map claims to evidence; classify verified / broken / unverified."""
    verified, broken, unverified = [], [], []
    # registry keys may carry prefixes too ("REF:bench"); index them normalized
    norm_map = {}
    for k in evidence:
        norm_map.setdefault(normalize_evidence_key(k), k)
    for claim in claims:
        if not claim["citations"]:
            unverified.append({"id": claim["id"], "text": claim["text"],
                               "reason": "no citation marker"})
            continue
        resolved, missing = [], []
        for token in claim["citations"]:
            key = normalize_evidence_key(token)
            if key in norm_map:
                resolved.append({"citation": token, "evidence": key,
                                 "source": evidence[norm_map[key]]["source"]})
            else:
                missing.append(token)
        if missing:
            broken.append({"id": claim["id"], "text": claim["text"],
                           "missing_citations": missing})
        elif resolved:
            verified.append({"id": claim["id"], "text": claim["text"],
                             "links": resolved})
    return {"verified": verified, "broken_links": broken, "unverified": unverified}


def normalize_evidence_key(token):
    """Citations may be '1', 'REF:1', 'src:1' — try the bare suffix too."""
    token = token.strip()
    if token in ("REF:%s", "src:%s"):
        pass
    for prefix in ("REF:", "ref:", "src:", "source:"):
        if token.lower().startswith(prefix.lower()):
            return token[len(prefix):]
    return token


def analyze(text, evidence):
    claims = extract_claims(text)
    report = build_chain(claims, evidence)
    report["claims_total"] = len(claims)
    report["evidence_count"] = len(evidence)
    return report


def format_report(report):
    lines = ["claims: %d, verified: %d, broken links: %d, unverified: %d" % (
        report["claims_total"], len(report["verified"]),
        len(report["broken_links"]), len(report["unverified"]))]
    for item in report["broken_links"]:
        lines.append("BROKEN %s: citations %s not in registry" % (
            item["id"], ", ".join(item["missing_citations"])))
    for item in report["unverified"]:
        lines.append("UNVERIFIED %s: %s" % (item["id"], item["text"][:80]))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="claim-verification-chain", description=__doc__)
    parser.add_argument("text", help="text/markdown file with claims")
    parser.add_argument("--evidence", required=True, help="evidence registry JSON")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)
    try:
        evidence = load_evidence(args.evidence)
        try:
            with open(args.text, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            raise ChainError("cannot read text file: %s" % exc)
        except UnicodeDecodeError:
            raise ChainError("%s is not valid UTF-8" % args.text)
        report = analyze(text, evidence)
    except ChainError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else format_report(report))
    return 0 if not (report["broken_links"] or report["unverified"]) else 1


if __name__ == "__main__":
    sys.exit(main())
