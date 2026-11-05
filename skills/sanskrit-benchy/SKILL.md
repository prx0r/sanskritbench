---
name: sanskrit-benchy
description: "Drive the Sanskrit benchmark science lab: run experiments, hypotheses, Kendall's-tau validation, Pāṭala proofs, re-render + fine-tune, and the watchdog — all kanban-aware, all verified. Use this skill whenever working in /root/sanskritbench."
version: 2.0.0
date: 2026-08-16
author: sanskritbenchy
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Sanskrit, Benchmark, MT, COMET, Science, ML, Verification]
    related_skills: [research, arxiv]
---

# Sanskrit Benchmark Science Lab (sanskritbenchy)

You are driving the lab at `/root/sanskritbench`. **The ONE RULE: nothing is real unless it is a logged,
content-addressed number on fixed gold, passed by a deterministic gate.** Your job is not to be clever — it
is to run the right step, read the logged result, and never claim more than the gate proves.

---

## 0. READ FIRST (60 seconds of orientation)

| Doc | Why |
|---|---|
| `AGENTS.md` | the ONE RULE + the anti-mess standard (timestamped·logged·content-addressed·registered) |
| `VISION.md` | the goal + the checkpointed roadmap (what we're building toward) |
| `HOW-IT-WORKS.md` | how skills/goals/verification make it deterministic |
| `INTEGRATION.md` | hermes-native vs our lab additions — how they compose |
| `RECIPES.md` | the full recipe book (every sequence) |
| `check.py --status` | the gate — MUST PASS before/after any change |

---

## 1. THE COMMAND MAP — what each command does AND WHEN to use it

> **Golden rule for every command:** run `python3 agent/ramwatch.py` first — if it says CAUTION/CRITICAL,
> do light work or wait. Never start a heavy job into a near-OOM box.

### 1.1 First — check the box can take it
| Command | When | What |
|---|---|---|
| `python3 agent/ramwatch.py` | BEFORE any heavy job | gives a SAFE/CAUTION/CRITICAL verdict on RAM+load |

### 1.2 The gate (always)
| Command | When | What |
|---|---|---|
| `python3 check.py --status` | before + after ANY change | PASS = every doc/script registered + resolves |
| `python3 agent/trace.py --all` | any time | see every run/experiment/log in one place |

### 1.3 The core science steps
| Command | When you want to... | What it does |
|---|---|---|
| `python3 agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha` | **prove the metric beats chrF** (the first falsifiable number) | Kendall's-tau of each metric vs the judge |
| `--test frontier:saamayik` | **validate on EXTERNAL gold** (honest cross-check) | same meta-eval on Sāmayik |
| `python3 agent/run.py --step eval --n 5 --judge` | **measure translation quality** on Mitrasamgraha | chrF/bleu/semantic-judge per verse |
| `python3 agent/run.py --step hypothesis --rounds 1 --n 3` | **improve the translation** (self-improvement loop) | observe→hypothesize→test→keep |
| `python3 agent/run.py --step tree_search` | **let the lab choose a better strategy autonomously** | AIDE metric-grounded search (every node scored by a real number) |
| `python3 agent/run.py --step benchmark --n 1` | **run the progressive-difficulty benchmark** | dealradar picks model per tier → translate → proof gate |
| `python3 agent/run.py --step report` | **see the leaderboard** | the logged experiments |

### 1.4 The proof + verification (the anti-hallucination spine)
| Command | When you want to... | What it does |
|---|---|---|
| `python3 agent/run.py --step proof --source "…" --candidate "…"` | **check one translation's deterministic gate** | Pāṭala proof (SOURCE_BINDING/COVERAGE/ABSTENTION/TERM/CITATION_GROUNDING) |
| `python3 agent/run.py --step verify --source "…" --candidate "…" --gold "…"` | **prove a translation is faithful** (the full check) | proof gate + gold anti-hallucination + content-address → VERIFIED kind |
| `python3 agent/audit.py --list` | **see all content-addressed runs** | the provenance ledger |
| `python3 agent/audit.py --bench suite` | **recompute on fixed gold, fail on mismatch** | the executable ONE RULE |
| `python3 agent/verify.py --registry` | **audit the whole registry** | every run has a valid signature + nanopublication |

### 1.5 The product vision (re-render + fine-tune)
| Command | When you want to... | What it does |
|---|---|---|
| `python3 agent/run.py --step render --n 4` | **re-render a passage into equally-valid translations** | N register-candidates; keep the gate-PASS + semantic-valid set |
| `python3 agent/run.py --step finetune --n 5` | **build fine-tuning data** (plain/precise registers) | LoRA-ready register-pair data from gold + re-renders |

### 1.6 The autonomous + memory layer
| Command | When you want to... | What it does |
|---|---|---|
| `python3 agent/run.py --step checkpoints` | **see the vision→checkpoint DAG + what's next** | the autonomous goal-hitting mechanism |
| `python3 agent/run.py --step memory --search <q>` | **remember/query past lab decisions** | the deterministic temporal memory (anti-regression) |
| `python3 agent/run.py --step challenge --n 200` | **build the SaQE training data** | controlled bad translations across all 14 MQM error families |
| `python3 agent/challenge_verify.py --n 20` | **prove the SaQE data is usable** | verify each `bad` < `good` on semantic fidelity (the N1 gate) |

### 1.7 The watchdog (scheduled, autonomous)
| Command | When | What |
|---|---|---|
| `python3 agent/watchdog.py --test mitrasamgraha` | **let the lab self-validate on a cycle** | validate→hypothesize→report, logged (also runs daily via hermes cron) |

---

## 2. THE DECISION FLOW — how to decide WHAT to do next

```
1. python3 agent/run.py --step checkpoints     → what's the NEXT checkpoint (prereqs done, not done)?
2. python3 agent/ramwatch.py                    → can the box take a heavy job?
3. Do the next checkpoint:
   - P1 first proof → validate + audit
   - P2 COMET (needs torch/GPU box)            → SKIP on this box
   - P3 school/period (needs the lemma map)     → roadmap
   - P7 re-render/fine-tune                     → render + finetune (verified working)
4. python3 agent/verify.py / audit.py           → prove the result is real
5. hermes kanban claim → request-review --summary → promote --reason   → record it
6. python3 agent/trace.py --recent              → confirm it's logged
```

**If you're unsure what to run:** run `--step checkpoints` first. It tells you the ONE next thing.

---

## 3. THE STANDARD WORKFLOW (every session)

```bash
cd /root/sanskritbench
python3 check.py --status                 # 1. gate
python3 agent/ramwatch.py                 # 2. box safety
python3 agent/run.py --step checkpoints   # 3. what's next
# ... run the next checkpoint's step (see the map above) ...
python3 agent/trace.py --recent           # 4. confirm it's logged
python3 check.py --status                 # 5. gate still green
```

---

## 4. THE HONEST RULES (never violate)

1. **No claim of "better" without a logged Kendall's-tau vs human gold on the same fixed data.** Log to
   the registry via `agent/run.py` — never a bare assertion.
2. **No "trained COMET" before the Phase 4 DA/MQM gold exists** (needs torch/GPU + human gold).
3. **The crypto layer proves integrity, never quality.**
4. **Box rules:** 8GB/4-core, ~2GB free. Run SMALL samples (n=2–3), one job at a time, background long runs.
   Run `ramwatch.py` before + during. Kill by PID if available < 400MiB.
5. **Never fabricate a result.** A failed step is logged as failed.
6. **Anti-circularity:** the verifier ≠ the generator. Use the deterministic gates (verify/audit), not your
   own judgment, to accept a result.

---

## 5. HOW TO READ THE RESULTS

- `data/corpus/registries/experiments.jsonl` — the logged translation experiments (chrF/bleu/semantic).
- `data/corpus/registries/agent-runs.jsonl` — every `agent/run.py` step (the orchestration ledger).
- `data/corpus/registries/watchdog.jsonl` — every watchdog cycle.
- `data/checkpoints.json` — the vision→checkpoint DAG (what's done / what's next).
- `data/lab-memory.db` — the DML deterministic decision memory.
- `research/HOW-WE-BEAT-AND-IMPROVE-THE-BENCHMARK.md` — what the tau number means.

---

## 6. WHEN TO STOP AND ASK (the honest limits)

- **If a step needs torch/GPU** (COMET, LoRA fine-tune) and this is the 8GB CPU box → report it as blocked
  on hardware; do the CPU-runnable work instead.
- **If the box is CAUTION/CRITICAL** → don't start a heavy job; do light work or wait.
- **If a gate FAILS** → don't paper over it; log it, fix the real issue, re-run.
- **If you don't know the next step** → run `--step checkpoints`.
