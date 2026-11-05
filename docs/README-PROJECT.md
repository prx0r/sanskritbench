# SANSKRIT BENCHMARK SCIENCE LAB — README (the sanskritbenchy project)

> **⚠️ REPOSITORY:** This is the **`sanskritbenchy`** project (the Sanskrit-benchmark science lane). It is a
> **separate standalone repo** — do **NOT** push it to `smellycock` (which is the translation-focused
> patalaorg reference). Live at `/root/sanskritbench`.

*2026-08-16 · The clean, **all-inclusive and standalone** project for the **Sanskrit-benchmark science**
lane. Self-contained: full lab code (`pipeline/` + `tools/`), gold data (`data/`), adopted toolkits
(`repos/`), and research + vision docs. The truth is the code + the experiment registry; this doc is the
projection.*

---

## 0. THE GOAL + VISION (read this first)

> **Read `VISION.md` — it is the single north-star.** One sentence: build our own Sanskrit translation
> benchmark, powered by learned metrics (COMET/ML) and conditioned on **philosophical school and historical
> period**, that **provably beats** the existing Sanskrit benchmarks (Sāmayik/Itihāsa/IndicParam, which use
> BLEU/chrF).

**The one falsifiable claim:** our metric(s) rank Sanskrit translations more like a human judge than
BLEU/chrF do — per school and per period (the *vimarśa* test). Proven by a logged Kendall's-tau/Spearman
vs human gold, per school × per period, on the same fixed data.

- `VISION.md` — the goal + the three pillars + the proof (start here).
- `research/VISION-COMET-SCHOOL-PERIOD-BENCHMARK.md` — the verified research landscape + build path (B→C→A).
- `repos/README.md` — the adopted toolkits (COMET, MTME, MQM, span-meta-eval) and how they serve the vision.

---

## ⭐ THE DOC MAP + READ ORDER (how everything fits)

```
START HERE → VISION.md (the goal + checkpointed roadmap)
   │
   ├─ HOW-IT-WORKS.md   (the mechanisms: skills, goals, verification, why it's deterministic)
   ├─ INTEGRATION.md    (the hermes-native build + our lab additions, how they compose)
   ├─ CANONICAL-DATA-SPEC.md  (every schema the lab writes + the strict validator)
   ├─ RECIPES.md        (every agent command + how to expand the lab)
   ├─ AGENTS.md         (the ONE RULE + the anti-mess standard — timestamped·logged·content-addressed·registered)
   ├─ CODING-AGENT.md   (the strict how-to: no-timeout backgrounding, box budget, file lifecycle, review + test protocol)
   ├─ GOALS.md          (the concrete checkpoints, Phase 1–6, each a falsifiable gate)
   │
   ├─ AGENT-ORCHESTRATION.md  (how a hermes agent runs the lab: kanban + cron + skills)
   ├─ METASTRUCTURE.md        (the reusable agentic operating system — the pattern, packaged in /root/agentic-infra)
   ├─ HERMES-MCP-API.md       (the MCP/API machine interface)
   │
   ├─ repos/README.md         (the adopted toolkits: COMET, MTME, MQM, ezkl, risc0)
   │
   └─ research/               (the verified deep-dives)
       ├─ HOW-WE-BEAT-AND-IMPROVE-THE-BENCHMARK.md      (the meta-eval protocol + improvable axes)
       ├─ LEGITIMATE-SANSKRIT-BENCHMARK.md              (the 15-step recipe, status per step)
       ├─ HERMES-VERIFICATION-ARCHITECTURE.md           (every hermes feature → verification)
       ├─ AGENTIC-SCIENCE-MECHANISMS.md                 (the bulletproof patterns we steal)
       ├─ DEEP-DIVE-COMET-CRYPTO-VERIFICATION.md        (COMET/ML + crypto proofs)
       ├─ HF-SANSKRIT-LORA-PERSONA-SURVEY.md            (persona translation, LoRA, lemmatization)
       └─ ... (PROOF-OF-TRANSLATION, MITRASAMGRAHA, SANSKRIT-BENCHMARKS, SCIENCE-LAB-VISION)
```

**One-line read order:** VISION → HOW-IT-WORKS → RECIPES → AGENTS → GOALS → then dive into research/ as
needed. The code all runs through `agent/run.py` and every result is in `agent/trace.py`.

---

## 1. THE ONE-LINE STATE

**The lab is built and runs on real Sanskrit gold. The immediate next step is Phase B — run off-the-shelf
COMET on our gold and prove whether it beats chrF/bleu (a logged tau vs the judge). Then school/period
conditioning (Phase C) and the Sanskrit DA/MQM gold (Phase A).**

---

## 2. THE PROOF PROTOCOL (Kendall's tau — the WMT method, adopted from MTME)

```
1. N gold Sanskrit verses (Mitrasamgraha test + 49 IPVV scholarly passages)
2. M diverse candidate translations per verse (different configs → different quality)
3. The human/judge signal: expert DA/MQM (Phase A) or the pairwise-ranked LLM judge (now)
4. For each automatic metric (chrF, bleu1, semantic, combined, COMET):
     rank candidates by that metric, rank them by the judge, compute KENDALL'S TAU / SPEARMAN
5. Higher tau = the metric correlates with human judgment better.
   If our combined/quality/learned metric beats raw chrF → the benchmark is proven better.
```

**Key method notes:**
- V1→V2: absolute 0–1 judge scores SATURATE (all ~0.8) → tau = 0. WMT's fix is **pairwise relative
  ranking** → a strict total order → non-zero tau. `judge_rank_pairwise()` implements this.
- **Adopt `google-research/mt-metrics-eval`** (`mt_metrics_eval/stats.py` `Correlation`/`AverageCorrelation`)
  for the standard tau/Spearman meta-eval — don't hand-roll it.

---

## 3. THE MODULES (all bundled here — fully standalone)

| Module (path) | Role in the vision | Status |
|---|---|---|
| `VISION.md` | the goal + vision (the north star) | ✅ |
| `pipeline/sanskrit_gold.py` | the fixed gold control (IPVV + kramasadbhava + Mitrasamgraha → **5,601 exemplars**, tradition-tagged) | ✅ runs clean |
| **`pipeline/sanskrit_texts.py`** | **the progressive-difficulty source: 254 DCS/GRETIL texts tagged by school/tier/period + specialist-term density** | ✅ |
| **`pipeline/benchmark_registry.py`** | **the legitimate content-addressed, versioned benchmark registry (lineage + decontamination audit)** | ✅ |
| **`pipeline/benchmark_runner.py`** | **run the benchmark: dealradar picks model per tier → hermes translates → proof gate → content-addressed result** | ✅ |
| `pipeline/experiment_lab.py` | named experiments (`EXP-…`), registry, `--report`, auto-report, Optuna-style `--sweep` | ✅ 3 logged |
| `pipeline/translation_proof.py` | the deterministic Pāṭala proof gate (SOURCE_BINDING / COVERAGE / ABSTENTION / TERM_CONSISTENCY) + lineage | ✅ proven |
| `pipeline/hypothesis_lab.py` | open-ended observe→reason→hypothesize→test→keep loop | ✅ `--propose` |
| `pipeline/validate_benchmark.py` | **THE meta-eval: tau of each metric vs the judge** (adopt MTME stats) | ⚠️ v2 built, needs completion |
| `pipeline/comet_scorer.py` | the learned-metric (COMET) adapter — Phase B baseline | ✅ scaffold (needs torch) |
| `pipeline/model.py` | the hermes client (mimo-v2.5, 1M context) — the only external call | ✅ |
| `tools/sanskrit_benchmark.py` | the better-benchmark leaderboard: per-tradition × quality × proof × **cost** (413 prices) | ✅ works |
| `tools/eval_mitrasamgraha.py` | the Mitrasamgraha eval harness (chrF/bleu/semantic-judge + lineage) | ✅ works |

**Data bundled:** `data/published/ipvv/` (58) · `data/benchmarks/mitrasamgraha/{test,val}.jsonl` ·
`pipeline/gold_records/` (23 kramasadbhava) · `data/corpus/model-prices.json` (413) ·
`data/corpus/registries/experiments.jsonl` (the logged science).

---

## 4. THE MEASURED RESULTS (logged in the registry — `experiments.jsonl`)

**Mitrasamgraha baseline (mimo-v2.5):** avg chrF ~0.55, bleu ~0.35, **semantic-fidelity ~0.8–0.9**
(LLM-judge). **BLEU/chrF UNDERSTATE good Sanskrit** (meaning right, wording differs) → the semantic-judge
is the honest quality axis.

| EXP | n | chrF | bleu | semantic |
|---|---|---|---|---|
| 60816T020912 | 4 | 0.613 | 0.397 | 0.900 |
| 60816T022005 | 3 | 0.591 | 0.399 | 0.800 |
| 60816T022207 | 3 | 0.581 | 0.341 | 0.733 |

**Cost:** mimo-v2.5 = **$10.88 / 1000 verses** → ~0.08 quality/$. **Proof gate:** faithful→PASS,
hallucinated→BLOCKED(SOURCE_BINDING), source-repeat→BLOCKED(ABSTENTION).

---

## 5. THE ADOPTED TOOLKITS (`repos/README.md` — reuse, don't rebuild)

The cloned repos under `patalacheckpoints/source-evidence/repos/` we adopt:
- **`Unbabel__COMET`** — the learned MT metric (baseline + our training scaffold).
- **`google-research__mt-metrics-eval` (MTME)** — the standard tau/Spearman meta-eval (replaces hand-rolled tau).
- **`google__wmt-mqm-human-evaluation`** — the MQM human-gold FORMAT for our Phase A Sanskrit gold.
- **`amazon-science__span-mt-metaeval`** — the LLM-as-judge meta-eval pattern (school-instructed judge).
- **`langtech-bsc__mt-evaluation` (MT-Lens)** — optional leaderboard visualization later.

---

## 6. THE HONEST GAPS (the immediate next work, in order)

1. **Phase B** — run off-the-shelf COMET (`wmt22-comet-da`) on our gold; log tau vs the judge. **Needs
   torch — run on a torch-enabled box/GPU, not this 8GB shared box.**
2. **Complete validation v2** — finish `validate_benchmark.py` on Mitrasamgraha (short verses) → the
   non-zero tau that proves semantic/combined beats raw chrF.
3. **IPVV candidates** — long passages fit 1M context fine; the "0 candidates" was a per-call **timeout**,
   not a context limit — pass a larger `timeout` to `chat()`.
4. **Phase C** — school + period conditioning (the *vimarśa* test).
5. **Phase A** — the Sanskrit DA/MQM gold (the long-term asset; format from wmt-mqm).
6. **Close the loop** — validate → hypothesis_lab → run → re-validate.

---

## 7. HOW TO RUN (the science method — all from this repo)

```bash
cd /root/sanskritbench

# the fixed gold control
PYTHONPATH=. python3 pipeline/sanskrit_gold.py
# the experiment lab
PYTHONPATH=. python3 pipeline/experiment_lab.py --report
PYTHONPATH=. python3 pipeline/experiment_lab.py --layer L2 --config l2-flash --test mitrasamgraha --n 5 --judge
# the scientific proof (Kendall's tau)
PYTHONPATH=. python3 pipeline/validate_benchmark.py --n 2 --m 3 --test mitrasamgraha --dry-run
PYTHONPATH=. python3 pipeline/validate_benchmark.py --n 2 --m 3 --test mitrasamgraha
# the hypothesis loop
PYTHONPATH=. python3 pipeline/hypothesis_lab.py --propose
# the benchmark leaderboard + cost router
PYTHONPATH=. python3 tools/sanskrit_benchmark.py --report
PYTHONPATH=. python3 tools/sanskrit_benchmark.py --cost --model mimo-v2.5
# the Mitrasamgraha eval
PYTHONPATH=. python3 tools/eval_mitrasamgraha.py --n 10 --judge
# the learned-metric adapter (Phase B — needs torch)
PYTHONPATH=. python3 pipeline/comet_scorer.py
```

---

## 8. THE KEY DOCS

| Doc (path) | What it is |
|---|---|
| **`HOW-IT-WORKS.md`** | **the master explanation: skills, goals, kanban review-gates, the crypto/provenance verification loop, why it's deterministic** |
| **`RECIPES.md`** | **every agent command/recipe + how to expand the lab properly** |
| **`AGENT-ORCHESTRATION.md`** | **how a hermes agent runs the lab autonomously (kanban + cron + skills + run.py/watchdog)** |
| **`HERMES-MCP-API.md`** | **the hermes MCP/API interface + recipes for driving the lab (the machine interface)** |
| **`skills/sanskrit-benchy/SKILL.md`** | **the hermes lab-driver skill** |
| **`VISION.md`** | **the goal + vision + checkpointed roadmap (Phase 1–6) + the Pāṭala proof architecture (north star — read first)** |
| **`GOALS.md`** | **the concrete checkpoints (Phase 1–6), each a falsifiable gate** |
| `repos/README.md` | the adopted toolkits + how they serve the vision |
| **`research/HOW-WE-BEAT-AND-IMPROVE-THE-BENCHMARK.md`** | **how we provably beat the frontier (WMT meta-eval tau) + the benchmark is improvable (metric/gold/split/data/proof) + the imported Sāmayik/Itihāsa datasets** |
| **`research/DEEP-DIVE-COMET-CRYPTO-VERIFICATION.md`** | **the citation-verified deep-dive: COMET/ML translation verification + cryptographic proofs/commitments (arXiv + GitHub)** |
| **`research/HF-SANSKRIT-LORA-PERSONA-SURVEY.md`** | **the verified HF + research survey: Sanskrit style/persona translation, LoRA adapters, lemmatization (ByT5/Vidyut/CDSL/DCS), licensing, multi-LoRA serving** |
| `research/VISION-COMET-SCHOOL-PERIOD-BENCHMARK.md` | the verified research landscape + the build path |
| `research/SCIENCE-LAB-VISION.md` | the earlier vision (drives hypothesis generation) |
| `research/PROOF-OF-TRANSLATION.md` | the proof architecture + verified arXiv literature |
| `research/MITRASAMGRAHA.md` | the gold + eval harness + first results |
| `research/SANSKRIT-BENCHMARKS.md` | the verified benchmark landscape |

---

## 9. THE RULE

> **No claim of "better" is made without a logged Kendall's-tau/Spearman vs human gold on the same fixed
> data. No "trained COMET" is claimed before the Sanskrit DA/MQM gold exists. Reuse the mature toolkits.
> If it isn't in the registry, it isn't decided.**
