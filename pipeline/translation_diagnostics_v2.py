#!/usr/bin/env python3
"""pipeline/translation_diagnostics_v2.py — deterministic translation diagnostics.

PR #7 P0 repair for translation_proof.py's `result_id` bug (function object
interpolated instead of called; only the first 40 candidate chars hashed)
and its `proof: true` overclaim (heuristics passing is not semantic proof).

This module ADDS a versioned format; it does not edit the pinned v1 kernel
(translation-work lineage_audit pins translation_proof.py by SHA — that lane
re-pins on its own schedule). v1 result_ids stay valid as historical
records and are INVALID for new authorization.

A v2 record carries NO proof claim. `deterministic_gate` reports whether
deterministic checks pass; it is a diagnostic, not a verdict on fidelity.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import translation_proof as tp  # noqa: E402 (read-only; pinned bytes untouched)

FORMAT = "translation-diagnostics/2"


def canon(o) -> bytes:
    return json.dumps(o, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def diagnose(source: str, candidate: str, config: dict | None = None,
             glossary: dict | None = None) -> dict:
    """Run deterministic checks; return a diagnostic record (never a proof)."""
    cfg = dict(config or {})
    checks = {
        "SOURCE_BINDING": tp.check_source_binding(source, candidate),
        "COVERAGE": tp.check_coverage(source, candidate),
        "ABSTENTION": tp.check_abstention(candidate),
        "TERM_CONSISTENCY": tp.check_term_consistency(candidate),
        "CITATION_GROUNDING": tp.check_citation_grounding(source, candidate),
    }
    blocking = [name for name, c in checks.items() if not c["PASS"]]
    passed = not blocking
    src_sha = sha(source.encode())
    cand_sha = sha(candidate.encode())
    record_core = {
        "format": FORMAT,
        "source_sha": src_sha,
        "candidate_sha": cand_sha,
        "source_chars": len(source),
        "candidate_chars": len(candidate),
        "config": cfg,
        "checks": {k: bool(v["PASS"]) for k, v in checks.items()},
    }
    diagnostic_id = sha(canon(record_core))
    return {
        **record_core,
        "diagnostic_id": diagnostic_id,
        "deterministic_gate": "PASS" if passed else "BLOCKED",
        "gate_note": ("diagnostic only: deterministic checks passed/failed; "
                      "not a semantic proof, not an authorization"),
        "blocking": blocking,
        "check_details": {k: v for k, v in checks.items()},
        "supersedes": ("translation_proof.py result_id v1 "
                       "(historical only, invalid for new authorization)"),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True)
    ap.add_argument("--candidate", required=True)
    a = ap.parse_args()
    print(json.dumps(diagnose(a.source, a.candidate), indent=1,
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
