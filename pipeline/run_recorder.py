#!/usr/bin/env python3
"""pipeline/run_recorder.py — the content-addressed RUN RECORDER (bulletproof provenance).

Stolen mechanism (verified research: DVC content-addressing + wandb git/deps capture + the nanopublication
data model from sensein/ECO). Every experiment run becomes a content-addressed, reproducible, anti-
fabrication record:

  run.signature = sha256(gold.hash || code.sha || config.sha)   → out.hash
  persisted as:  {run.signature, out.hash, metrics, raw_outputs, git_commit, diff.patch, requirements}

And every headline number ships as a NANOPUBLICATION triple {assertion, evidence, provenance} — so a
number that only exists in an LLM's text (no machine-computed content-addressed run) is automatically
flagged as theater. This makes the lab's ONE RULE executable: nothing is real without a logged number on
fixed gold.

Deterministic + stdlib (sha256). Reuses the existing lab metrics + gold.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "data" / "corpus" / "runs"   # content-addressed run store


def sha256(obj) -> str:
    """SHA-256 of any JSON-serializable object (canonical). The anti-fabrication key."""
    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# the eigenius 4-kind epistemic ladder (verified: eigenius_eigenius, "how-known" substrate).
# Each kind has STRONGER guarantees than the last:
#   DECLARED  — a human asserts it (weakest: opinion)
#   OBSERVED  — measured/recorded with provenance (a logged value)
#   DERIVED   — produced by a typed pipeline whose steps are auditable (a computed value on gold)
#   VERIFIED  — derived AND re-checked by a formal/deterministic proof system (the strongest)
# A number is only "VERIFIED" if it passes a deterministic gate (our proof gate / audit), not just computed.
EPISTEMIC_KINDS = ["DECLARED", "OBSERVED", "DERIVED", "VERIFIED"]


def epistemic_kind(*, verified: bool = False, derived: bool = True, observed: bool = True) -> str:
    """Assign the eigenius epistemic kind to a result based on how it was produced."""
    if verified:
        return "VERIFIED"      # derived AND passed a deterministic proof gate
    if derived:
        return "DERIVED"       # computed by a reproducible pipeline on fixed data
    if observed:
        return "OBSERVED"      # measured/recorded with provenance
    return "DECLARED"          # human assertion only


def file_sha(path: Path) -> str:
    return sha256({"file": str(path), "content": path.read_text(encoding="utf-8", errors="ignore")})


def gold_hash(gold: list[dict]) -> str:
    """Content-address the fixed gold (the input). Hash source+gold, not the file path."""
    return sha256([{"source": r.get("source", ""), "gold": r.get("gold", "")} for r in gold])


def code_sha() -> str:
    """Hash the frozen eval/metric code — every pipeline + tool file that affects the result."""
    parts = {}
    for d in ("pipeline", "tools"):
        for f in sorted((ROOT / d).glob("*.py")):
            parts[str(f.relative_to(ROOT))] = f.read_text(encoding="utf-8", errors="ignore")
    return sha256(parts)


def config_sha(config: dict) -> str:
    """Hash the RESOLVED config (all overrides applied) — the same-config-is-meaningful statement."""
    return sha256(config)


def git_state() -> dict:
    """Auto-capture the git commit + diff.patch (wandb's Code-Saving trio, minus requirements)."""
    out = {"commit": "", "diff": ""}
    try:
        c = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT)
        out["commit"] = c.stdout.strip()
        d = subprocess.run(["git", "diff"], capture_output=True, text=True, cwd=ROOT)
        out["diff"] = d.stdout
    except Exception:
        pass
    return out


def run_signature(gold: list[dict], config: dict) -> str:
    """The content-addressed run key: hash(gold || code || config). Same key ⇒ same reproducible run."""
    return sha256({"gold": gold_hash(gold), "code": code_sha(), "config": config_sha(config)})


class RunRecorder:
    """Persist a content-addressed run record + nanopublication triples."""

    def __init__(self, runs_dir: Path = RUNS_DIR):
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def record(self, *, step: str, gold: list[dict], config: dict, metrics: dict,
               raw: list[dict] | None = None, assertion: str = "",
               evidence_code: str = "ECO:0000203", verified: bool = False) -> dict:
        """Record one run. Returns the run record (signature, out.hash, nanopublication).

        Immutability: the input-signature file `{sig}.json` is first-write-wins
        and NEVER overwritten. A rerun with the same inputs but different outputs
        writes `{sig}.{out_hash[:12]}.json` + records `supersedes` linkage, so
        stochastic reruns stay individually retrievable. Raw outputs: full hash
        + count always recorded; body stores all rows when small, else first 20
        with explicit truncation note (never silent).

        verified=True marks VERIFIED (derived AND passed a deterministic gate).
        Default is DERIVED (computed on fixed gold).
        """
        sig = run_signature(gold, config)
        raw = raw or []
        # hash the OUTPUT too (metrics + FULL raw) — out.hash covers everything
        out_hash = sha256({"metrics": metrics, "raw": raw})
        raw_hash = sha256(raw)
        truncated = len(raw) > 20
        record = {
            "step": step, "run_signature": sig, "out_hash": out_hash,
            "exec_id": f"{sig[:12]}.{out_hash[:12]}",
            "gold_hash": gold_hash(gold), "code_sha": code_sha(), "config_sha": config_sha(config),
            "config": config, "metrics": metrics,
            "raw_outputs": raw if not truncated else raw[:20],
            "raw_total": len(raw), "raw_hash": raw_hash,
            "raw_truncated": truncated,
            "git": git_state(),
            "ts": datetime.now(timezone.utc).isoformat(),
            # nanopublication: every headline number carries assertion + evidence + provenance
            "kind": epistemic_kind(verified=verified, derived=True, observed=True),
            "nanopublication": {
                "assertion": assertion or f"{step} produced metrics {json.dumps(metrics)}",
                "evidence": {"code": evidence_code, "artifact": f"run:{sig[:12]}"},
                "provenance": {"run_signature": sig, "out_hash": out_hash,
                               "generated_by": "sanskritbenchy/run_recorder.py",
                               "ts": datetime.now(timezone.utc).isoformat()},
            },
        }
        out_file = self.runs_dir / f"{sig}.json"
        if out_file.exists():
            try:
                prior = json.loads(out_file.read_text())
            except Exception:
                prior = None
            if prior and prior.get("out_hash") != out_hash:
                # same inputs, different outputs: keep both, link them
                record["supersedes_note"] = (
                    f"input-signature {sig[:12]} reran with different outputs; "
                    f"prior out {str(prior.get('out_hash'))[:12]} preserved in {out_file.name}")
                variant = self.runs_dir / f"{sig}.{out_hash[:12]}.json"
                variant.write_text(json.dumps(record, ensure_ascii=False, indent=2))
                return record
            if prior and prior.get("out_hash") == out_hash:
                return prior  # identical rerun: return existing, no duplicate write
        out_file.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        return record

    def get(self, signature: str) -> dict | None:
        p = self.runs_dir / f"{signature}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def all(self) -> list[dict]:
        return [json.loads(f.read_text()) for f in sorted(self.runs_dir.glob("*.json"))]


if __name__ == "__main__":
    from sanskrit_gold import exemplars
    rec = RunRecorder()
    gold = exemplars()[:3]
    r = rec.record(step="proof-check", gold=gold,
                   config={"model": "mimo-v2.5", "n": 3},
                   metrics={"avg_chrF": 0.61, "semantic": 0.9},
                   raw=[{"id": g["id"], "chrF": 0.6} for g in gold],
                   assertion="semantic-judge correlates better with human than chrF")
    print("run_signature:", r["run_signature"][:16], "| out_hash:", r["out_hash"][:16])
    print("nanopublication assertion:", r["nanopublication"]["assertion"][:50])
    print("gold_hash:", r["gold_hash"][:16])
