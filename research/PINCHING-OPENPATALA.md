# PINCHING OPENPATALA — how the openpatala corpus engine feeds the sanskritbenchy benchmark

*2026-08-16 · An objective brainstorm: `/root/openpatala` is a SEPARATE autonomous Sanskrit corpus
engine (the huge ingestor + normalizer of Devanagari works). It is NOT the benchmark — but it produces
exactly the input the benchmark's school/period moat needs. This doc maps what openpatala already has,
what we can adopt verbatim (tools/processes), and how it unblocks `DEV-PLAN-WITH-GPU` G6 (the *vimarśa*
school/period conditioning) and the benchmark's school/period strata.*

---

## 1. WHAT OPENPATALA IS (verified)

**openpatalaproject = an autonomous Sanskrit corpus engine.** It discovers niche sources (archive.org/DLI,
sanskritdocuments, GRETIL, Muktabodha), fetches the bytes, OCRs scanned Devanagari pages, normalizes them
into a **unified verse-object** format, labels every verse, and serves it via a FastAPI. Everything is
logged + content-addressed + schema-gated — the same anti-theatre discipline as ours.

### The concrete assets (verified live, not aspirational)

| Asset | What it has | Relevance to us |
|---|---|---|
| **The WORKS metadata map** | 12 curated works, each with `author`, `period`, `school[]`, `genre` | **THE school/period conditioning data** (our G6 moat + benchmark school/period strata) |
| **The verse JSONL** | real Sanskrit verses per work, e.g. Īśvarapratyabhijñāvimarśinī 533 verses, content-addressed (`source_sha256`), layer/version/status | fresh, source-bound Sanskrit source text for the benchmark (beyond Mitrasamgraha) |
| **The OCR engine** | MorphBG (VedOCR) + tesseract `-l san` on CPU; TrOCR + pe-ocr-sanskrit on GPU | a corpus-expansion channel: OCR niche editions we can't get clean elsewhere |
| **The translation-availability index** | 260 works, per-work translation editions, tier A/B/C, download-proof | the benchmark's *multi-reference* source (independent published translations) |
| **traditions.ts** | per-tradition `period`, `concepts`, doctrinal core (Trika/Krama/Śaiva…) | the lemma→sense→(school,period) spine's scholarly ground truth |
| **The unified data spec** | `object_id=work:verse` + version + layer + source provenance + inherited parent metadata | the data contract we should consume |

---

## 2. THE FOUR WAYS TO USE IT (brainstorm, in value order)

### Way 1 — **the school/period conditioning data (the biggest prize, unblocks G6)**
Our `*vimarśa*` moat (`DEV-PLAN-WITH-GPU` G6) needs lemma→sense→(school,period) disambiguation. openpatala
already stores exactly that on the parent work:
```
tantraloka               → period "10th-11th c."  → school ["Trika", "Pratyabhijñā (Kashmir Śaivism)"]
isvarapratyabhijnavimarsini → period "10th-11th c." → school ["Trika", "Pratyabhijñā (Utpaladeva's IPK, …)"]
stavacintamani           → period "9th-10th c."   → school ["Śaiva Siddhānta", "Kashmir Śaivism (bhakti)"]
```
**Action:** import the WORKS map + the verse JSONL into our benchmark so passages carry a real
`school` + `period` (our PASSAGE schema already has those fields but they're sparse). This turns the
*vimarśa* test from "spec'd" into "data-ready": fixed passages where the correct rendering depends on
school/period, ranked correctly by a conditioned metric.

### Way 2 — **multi-reference benchmark source (fixes our N4 gap)**
Our benchmark has 0 passages with ≥2 references. openpatala's `translation-availability.json` (260 works)
holds independent published English translations (tier A = scholarly). These are exactly the PaliBench
multi-references the blueprint wants — independent human translations, not re-rendered variants of one gold.
**Action:** wire `attach_references` (our `benchmark_registry.py` already has it) to pull independent
published translations from the availability index where a passage's work matches.

### Way 3 — **fresh source-bound Sanskrit text for the gold (decontamination + domain coverage)**
Our gold is Mitrasamgraha + DCS/GRETIL. openpatala's OCR'd verses (e.g. Īśvarapratyabhijñāvimarśinī 533,
meghamala 672, naishadhacharitam 1725) are real, source-bound Sanskrit from niche editions — a
decontamination-advantaged test split (these post-date the model cutoffs) and a school/period-tagged
extension to the progressive-difficulty source.
**Action:** import a labeled verse subset as a held-out test set with full school/period provenance.

### Way 4 — **the OCR engine as a corpus-expansion channel (the long play)**
The blueprint wants Sanskrit text in more scripts/editions. openpatala's OCR stack (MorphBG + tesseract +
GPU TrOCR/ByT5) can convert scanned niche editions into our verse format. Not immediately needed, but it's
the difference between "benchmark on what exists" and "benchmark on the whole traditio."

---

## 3. WHAT TO PINCH VERBATIM (reuse, don't rebuild — per AGENTS.md)

The two projects already share the benchmark-lab DNA (experiment_lab, translation_proof, model-via-hermes,
run_recorder, trace/audit/verify). openpatala has these ADDITIONAL reusable pieces:

| Piece (openpatala) | Path | Why we'd adopt it |
|---|---|---|
| **The unified data spec** | `docs/DATA-SPEC-UNIFIED.md` | the object spine (`object_id=work:verse` + version + layer + provenance + inherited metadata). Our benchmark should CONSUME this format, not reinvent it |
| **The work-meta JSON Schema** | `schemas/work-meta.json` | the canonical `{work_id, school[], period, genre, author}` — a schema our PASSAGE/metadata layer can align to |
| **OCR quality metric** | `agent/ocr_quality.py` | verse-recovery + CER, logged + content-addressed — the honest OCR gate |
| **Devanagari verse extractor** | `harvest_to_factory._extract_devanagari_text` | `॥N॥` verse extraction from OCR text |
| **aksharamukha transliteration** | (pip) | Devanagari→IAST |
| **MorphBG + tesseract `-l san`** | `source-evidence/repos/Suyashkb__VedOCR` | the CPU OCR stack |

### The process to pinch (not just tools)
openpatala's **ingest → normalize → label → schema-gate → persist → serve → verify** loop is the same
closed loop we use for benchmark gold. The specific process worth copying: **parent-inherited metadata**
(school/period/author stored once on the work, inherited by every verse — never denormalized). Our
benchmark PASSAGE schema stores school/period per passage; adopting the work-parent inheritance keeps it
consistent and streamable.

---

## 4. THE CONCRETE INTEGRATION PLAN (how it actually lands in sanskritbenchy)

1. **A small importer** `pipeline/import_openpatala.py`: read openpatala's `WORKS` map + verse JSONL →
   emit benchmark PASSAGE rows with real `school` + `period` + `source_id` + `source_sha256`. Gate:
   validate against PASSAGE schema; count school/period coverage.
2. **Wire the *vimarśa* test data**: pick fixed passages per school (Trika vs Śaiva Siddhānta vs …) where a
   technical term's correct rendering depends on school. Gate: a fixed `data/vimarsa/*.json` gold set.
3. **Attach multi-references** from `translation-availability.json` via the existing `attach_references`.
   Gate: ≥2 independent published references on the passages where a work matches.
4. **Add a school/period-tagged held-out split** from the OCR'd verses (decontamination-advantaged).
5. **Register every importer + its schema in MANIFEST; wire into `agent/run.py`** (the N6 rule).

### The dependency / order
- Do **Way 1 + Way 2** now (CPU-runnable, no torch): import WORKS metadata + verse JSONL + references →
  real school/period-tagged passages + multi-refs. This is pure CPU data-wiring — exactly the
  `DEV-PLAN-NO-GPU` mandate (prepare the data so the GPU phase runs immediately).
- **Way 3** (fresh test split) when we have a clean labeled subset.
- **Way 4** (OCR expansion) when the GPU box arrives or a specific niche work is wanted.

---

## 5. THE HONEST BOUNDARY (what's NOT in openpatala)

- openpatala has **no translations for most works** (`translation` field is often empty) — it's an
  ingestor/normalizer, not a translator or an evaluator. We do the translating + evaluating.
- Only **12 works** have full curated school/period metadata; the other ~248 are just bibliography rows.
  So the *vimarśa* test starts with those 12 (still a real, non-trivial conditioning set across Trika /
  Pratyabhijñā / Śaiva Siddhānta / Spanda / Bhairava / Kaula).
- The verse JSONL `translation` is empty (SOURCE layer only) — these are source verses, not gold pairs.

---

## 6. THE ONE-LINE SUMMARY

> **openpatala is the school/period-conditioned SOURCE-BOUND CORPUS ENGINE our benchmark was missing. Pinch
> its WORKS metadata map + verse JSONL (Way 1) to make our passages carry real school/period (the G6
> *vimarśa* moat), its translation-availability index (Way 2) to give us real multi-references (the N4 fix),
> and adopt its unified data spec + OCR engine as the expansion channel. It's CPU-runnable, reuses our
> existing schemas/`attach_references`, and turns the school/period conditioning from spec to data-ready.**
