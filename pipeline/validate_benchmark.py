#!/usr/bin/env python3
"""pipeline/validate_benchmark.py — SMOKE-TEST the benchmark plumbing (Kendall's tau-b).

NOT a proof of human correlation: 3×3 with a same-model LLM proxy judge is a
wiring check only. Human validation needs blinded human ratings on a consented,
held-out set (see TECHNICAL-SPEC §4). MODEL_PROXY labels below are deliberate.

Protocol (WMT-shaped, proxy only):
  1. Take N verses from the gold loader.
  2. Produce M candidate translations per verse (diverse configs).
  3. Have the MODEL_PROXY judge rank candidates pairwise (reference + candidates,
     no Sanskrit shown — limitation, not human judgment).
  4. Rank M candidates by each automatic metric and by the proxy; tau-b per verse.
  5. Higher proxy-tau = ranks more like the proxy — nothing about humans.

A positive, higher tau for our combined/quality metric vs raw chrF/bleu = the PROOF.

Usage:
  python3 pipeline/validate_benchmark.py --n 3 --m 3 --dry-run     # no model calls
  python3 pipeline/validate_benchmark.py --n 3 --m 3               # real: Kendall's tau per metric
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

from experiment_lab import translate, chrF, bleu1, semantic_fidelity, TEST_SOURCES  # noqa: E402


def judge_rank_pairwise(model: str, gold: str, candidates: list[str]) -> list[float]:
    """Have the judge RANK the candidates relative to each other (WMT-standard).

    Absolute 0-1 scores SATURATE (all 0.8) → Kendall's tau can't discriminate. Pairwise relative
    ranking forces a total order: the judge picks the best of each pair, we tally wins → a strict
    ranking (as a 0..1 normalized score per candidate). This produces a real ranking tau can measure.
    """
    from model import chat
    scores = [0.0] * len(candidates)
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            system = ("You are a strict Sanskrit translation judge. Given the GOLD reference and two "
                      "CANDIDATE translations, which candidate better preserves the MEANING? "
                      "Reply with exactly: 1 or 2")
            user = (f"GOLD: {gold}\n\nCANDIDATE 1: {candidates[i]}\n\nCANDIDATE 2: {candidates[j]}\n"
                    f"Better candidate (1 or 2):")
            try:
                raw = (chat(system, user, model=model, timeout=60) or "").strip()
                m = re.search(r"[12]", raw)
                winner = int(m.group(0)) if m else None
            except Exception:
                winner = None
            if winner == 1:
                scores[i] += 1
            elif winner == 2:
                scores[j] += 1
            else:
                scores[i] += 0.5; scores[j] += 0.5  # tie
    # normalize to 0..1
    mx = max(scores) or 1
    return [round(s / mx, 3) for s in scores]


def kendall_tau(rank_a: list[float], rank_b: list[float]) -> float:
    """Kendall's tau-b rank correlation (WMT meta-eval standard, SciPy definition).

    Ties in either ranking shrink the denominator; they are NOT dropped.
    Returns nan when undefined (n<2, all pairs tied, or one side constant) —
    callers must skip nan, never treat it as 0 = "no correlation".
    Verified: kendall_tau([1,1,2],[1,2,3]) ≈ 0.8165 (tau-b); all-tied → nan.
    """
    import math
    if len(rank_a) != len(rank_b) or len(rank_a) < 2:
        return float("nan")
    n = len(rank_a)
    concordant = discordant = ties_a_only = ties_b_only = ties_both = 0
    for i in range(n):
        for j in range(i + 1, n):
            da = rank_a[i] - rank_a[j]
            db = rank_b[i] - rank_b[j]
            if da == 0 and db == 0:
                ties_both += 1
            elif da == 0:
                ties_a_only += 1
            elif db == 0:
                ties_b_only += 1
            elif da * db > 0:
                concordant += 1
            else:
                discordant += 1
    denom = math.sqrt((concordant + discordant + ties_a_only) *
                      (concordant + discordant + ties_b_only))
    if denom == 0:
        return float("nan")
    return (concordant - discordant) / denom


def _combo(chrf_val, bleu_val, sem_val):
    """A combined quality signal: semantic-judge dominates, surface as tiebreak. Returns 0-1."""
    if sem_val is not None:
        return sem_val
    return (chrf_val + bleu_val) / 2


def produce_candidates(source: str, n: int, model: str, max_chars: int = 400) -> list[str]:
    """Produce n diverse candidate translations (different configs) for one verse.

    max_chars truncates long sources (IPVV passages are 8K-64K chars — too long for context); a
    truncated leading window is the usable, comparable unit. Mitrasamgraha's short verses are unaffected.
    """
    src = source[:max_chars]
    styles = [
        "Translate literally, preserving word order.",
        "Translate naturally and fluently into modern English.",
        "Translate faithfully, keeping philosophical terms transliterated.",
    ]
    cands = []
    for i in range(n):
        style = styles[i % len(styles)]
        from model import chat
        system = ("You are a Sanskrit scholar-translator. " + style + " Output only the translation.")
        try:
            raw = chat(system, f"Translate:\n{src}", model=model, timeout=90)
            cands.append((raw or "").strip().strip('"').strip())
        except Exception:
            cands.append("")
    return cands


def validate(n_verses: int, m_cands: int, test: str, model: str, dry_run: bool) -> int:
    rows = TEST_SOURCES[test]["load"]()[:n_verses]
    print(f"=== VALIDATE benchmark plumbing (tau-b vs MODEL_PROXY judge) ===")
    print(f"  {n_verses} verses × {m_cands} candidate translations each, model={model}")
    print(f"  smoke-test only: which metric ranks most like the proxy judge?")

    # collect per-verse: {gold, candidates, judge_scores, metric_scores}
    tau_scores = {m: [] for m in ["chrF", "bleu1", "semantic", "combined"]}
    for vi, v in enumerate(rows):
        if dry_run:
            print(f"  [verse {vi+1}] dry-run (would produce {m_cands} candidates)")
            continue
        cands = produce_candidates(v["source"], m_cands, model)
        cands = [c for c in cands if c]  # drop failures
        if len(cands) < 2:
            print(f"  [verse {vi+1}] only {len(cands)} candidate(s) — skipping"); continue
        # the MODEL_PROXY judge RANKS the candidates pairwise (forces a total order).
    # Limitation (do not relabel as human): judge sees reference + candidates,
    # never the Sanskrit; same model family may generate, judge, and score.
        judge = judge_rank_pairwise(model, v["gold"], cands)
        chrf_s = []; bleu_s = []; sem_s = []; combo_s = []
        for c in cands:
            fid, _ = semantic_fidelity(model, v["gold"], c)
            chrf_s.append(chrF(v["gold"], c))
            bleu_s.append(bleu1(v["gold"], c))
            sem_s.append(fid)
            combo_s.append(_combo(chrf_s[-1], bleu_s[-1], fid))
        # tau of each metric vs the proxy ranking (nan = undefined, skipped)
        import math
        for name, scores in [("chrF", chrf_s), ("bleu1", bleu_s),
                             ("semantic", sem_s), ("combined", combo_s)]:
            tau = kendall_tau(scores, judge)
            if isinstance(tau, float) and math.isnan(tau):
                print(f"  [verse {vi+1}] {name}: tau=undefined (tied/constant)")
                continue
            tau_scores[name].append(tau)
            print(f"  [verse {vi+1}] {name}: tau={tau:+.3f} (proxy={judge})")

    if dry_run:
        return 0

    print("\n=== TAU-B SUMMARY vs MODEL_PROXY (plumbing only, not human proof) ===")
    print(f"{'metric':10} {'avg tau':>9}  (nan skipped; undefined = tied/constant)")
    print("-" * 55)
    results = {}
    for name, taus in tau_scores.items():
        import math
        scored = [t for t in taus if not (isinstance(t, float) and math.isnan(t))]
        avg = (sum(scored) / len(scored)) if scored else float("nan")
        results[name] = avg
        tag = f"{avg:+.3f} (n={len(scored)})" if scored else "undefined"
        print(f"{name:10} {tag}")

    # the plumbing claim (never "scientifically better" without human gold)
    import math
    def _val(x):
        return x if isinstance(x, float) and not math.isnan(x) else float("-inf")
    best = max(results, key=lambda k: _val(results[k]))
    baseline = results.get("chrF", float("nan"))
    claim = (not math.isnan(results[best]) and not math.isnan(baseline)
             and results[best] > baseline)
    if claim:
        print(f"\n  ✓ {best} ranks more like the MODEL_PROXY than raw chrF "
              f"({results[best]:+.3f} vs {baseline:+.3f}) — plumbing signal only")
    else:
        print(f"\n  ✗ no proxy win — plumbing only, no human conclusion")

    # THE ONE RULE: numbers are real only as content-addressed run records.
    # Gold here = actual loaded rows (source+gold), never a test descriptor.
    from run_recorder import RunRecorder
    gold = [{"source": v.get("source", ""), "gold": v.get("gold", "")} for v in rows]
    rr = RunRecorder()
    rec = rr.record(
        step="validate_benchmark", gold=gold,
        config={"test": test, "n": n_verses, "m": m_cands, "model": model,
                "judge": "MODEL_PROXY(pairwise,same-model,reference-only)"},
        metrics={"tau_proxy": {k: (None if isinstance(v, float) and math.isnan(v) else v)
                               for k, v in results.items()},
                 "best_metric": best, "beats_chrF_proxy": claim},
        raw=[{"metric": k, "tau_proxy": (None if isinstance(v, float) and math.isnan(v) else v),
              "n_scored": len(tau_scores[k])}
             for k, v in results.items()],
        assertion=f"SMOKE ONLY: proxy-tau best='{best}' beats_chrF_proxy={claim} "
                  f"on {len(gold)} rows (no human claim)",
    )
    print(f"\n  content-addressed run: {rec['run_signature']} (kind={rec['kind']})")
    print(f"  => {'proxy smoke PASSED' if claim else 'proxy smoke: no win'} (not a human gate)")
    return 0 if claim else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3, help="number of gold verses")
    ap.add_argument("--m", type=int, default=3, help="candidate translations per verse")
    ap.add_argument("--test", default="mitrasamgraha",
                    help="gold source: mitrasamgraha | ipvv | kramasadbhava | frontier:saamayik | frontier:itihasa")
    ap.add_argument("--model", default="mimo-v2.5")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return validate(args.n, args.m, args.test, args.model, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
