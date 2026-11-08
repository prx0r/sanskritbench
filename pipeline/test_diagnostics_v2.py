#!/usr/bin/env python3
"""test_diagnostics_v2.py — the v1 failure modes must be impossible in v2.

- v1 interpolated the source_sha FUNCTION (repr with memory address) into
  result_id: same input in two processes gave different IDs.
- v1 hashed only the first 40 candidate chars: different sources with a
  shared 40-char prefix collided.
- v1 set proof:true when heuristics passed, including for a negated
  sentence: the gate cannot distinguish meaning.

Each test below fails on v1 semantics and passes on v2.
Run: python3 -m unittest pipeline.test_diagnostics_v2 -v (from repo root:
python3 pipeline/test_diagnostics_v2.py discovers itself too).
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from translation_diagnostics_v2 import diagnose  # noqa: E402


def run_diagnose(source: str, candidate: str) -> dict:
    r = subprocess.run(
        [sys.executable, str(HERE / "translation_diagnostics_v2.py"),
         "--source", source, "--candidate", candidate],
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


class TestDiagnosticsV2(unittest.TestCase):
    def test_deterministic_in_process(self):
        a = diagnose("src alpha", "The child goes to the village")
        b = diagnose("src alpha", "The child goes to the village")
        self.assertEqual(a["diagnostic_id"], b["diagnostic_id"])

    def test_deterministic_across_processes(self):
        # v1 failed here: function repr carries a memory address.
        a = run_diagnose("src alpha", "The child goes to the village")
        b = run_diagnose("src alpha", "The child goes to the village")
        self.assertEqual(a["diagnostic_id"], b["diagnostic_id"])
        self.assertNotIn("function", a["diagnostic_id"])
        self.assertEqual(len(a["diagnostic_id"]), 64)

    def test_changed_source_changes_id(self):
        a = diagnose("source ALPHA", "The child goes to the village")
        b = diagnose("source BETA completely different",
                     "The child goes to the village")
        self.assertNotEqual(a["diagnostic_id"], b["diagnostic_id"])

    def test_changed_suffix_changes_id(self):
        # v1 hashed candidate[:40]: shared prefixes collided.
        stem = "x" * 40
        a = diagnose("src", stem + " ending one")
        b = diagnose("src", stem + " ending two")
        self.assertNotEqual(a["diagnostic_id"], b["diagnostic_id"])

    def test_no_proof_claim(self):
        d = diagnose("src alpha", "The child goes to the village")
        self.assertNotIn("proof", d)
        self.assertIn("diagnostic", d["gate_note"])

    def test_negation_documents_heuristic_blindness(self):
        # Both pass the deterministic gate (heuristics cannot tell meaning
        # apart) — recorded as a documented limitation, never as proof.
        pos = diagnose("src alpha", "The child goes to the village")
        neg = diagnose("src alpha", "The child does not go to the village")
        self.assertEqual(pos["deterministic_gate"], "PASS")
        self.assertEqual(neg["deterministic_gate"], "PASS")
        self.assertNotEqual(pos["diagnostic_id"], neg["diagnostic_id"])

    def test_full_hashes_recorded(self):
        d = diagnose("src alpha", "The child goes to the village")
        self.assertEqual(len(d["source_sha"]), 64)
        self.assertEqual(len(d["candidate_sha"]), 64)
        self.assertEqual(d["format"], "translation-diagnostics/2")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
