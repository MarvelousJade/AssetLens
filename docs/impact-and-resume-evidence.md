# AssetLens: impact and resume evidence

Reviewed October 25, 2026. [Source-review fingerprints](evidence/resume-review-2026-10-25.json).

## Existing evidence and candidate claim

**Status: preliminary. Category: engineering.** The eight-holding seeded portfolio has a historical absolute local baseline, not an optimized before/after result. The API uses Python/FastAPI, SQLite and a deterministic copilot; network and external models are excluded.

- Problem/change: establish the latency of holdings, analytics, deterministic copilot and report generation before attempting optimization.
- Measured result: July 29, 2026, 15:10 UTC; holdings p50 23.612 ms / p95 70.528 ms; performance analytics p95 81.544 ms; exposure p95 70.527 ms; deterministic copilot p95 75.988 ms; report creation p95 158.745 ms.
- Conditions: Windows 11, Python 3.12.10, AMD64 Family 23 Model 113; temporary SQLite, eight holdings; five warm-up requests per operation; 100 samples for each API operation, ten reports. See [original record](performance.md).
- Baseline/improved source revisions: no comparative code revisions recorded. Historical exact measured SHA, RAM and complete dependency lock identity are not established by this report. Current review revision and source hashes are in the manifest; they are not retroactive run provenance.
- Raw per-request samples: not retained in the inspected record; no confidence interval or new timing run is claimed. Reciprocal mean latency is not concurrent throughput. Current-version applicability needs a matched rerun.
- Personal contribution: not established by this evidence audit; historical checks must not be presented as personally executed.
- Safe capability bullet now: “Provides a portfolio analytics API with holdings, exposure analysis and deterministic copilot workflows.” Use an implementation verb only when contribution is confirmed.
- Conditional quantified draft after current-version validation: “Benchmarked holdings retrieval at 70.5 ms p95 over 100 warmed local FastAPI/SQLite requests on an eight-holding fixture.”

## Next measurement and acceptance criteria

Use the existing benchmark on a disposable local database. From apps/api run:

```powershell
python scripts/benchmark_api.py --iterations 100 --report-iterations 10 --warmup-iterations 5 --output .tmp/evidence-trial-1.json
```

Repeat with distinct output names for five trials; fingerprint source and fixture and retain every JSON. The existing script fixes its temporary database path, so run serially. Check successful HTTP responses plus expected portfolio totals and valid generated report content; successful status alone does not establish semantic equivalence. For a later optimization run the same five-trial protocol on both revisions, alternate order, compare medians/ranges and keep all outputs. No runtime rerun was attempted in this documentation increment.

Strongest candidates: current-version holdings/report latency after rerun; protected cross-owner behavior after a separately labeled correctness experiment. No measured workflow or real-world impact is available.

## Measurement policy for future changes

Choose one or two useful metrics during planning and record acceptance criteria before implementation. Measure the old version first; for new functionality use an initial implementation or a defined manual workflow. Compare equivalent inputs, environments and required outputs. Without a defensible comparator, report an absolute result. Test totals, lines of code and commits are verification/scope evidence, not user impact.

For every experiment record metric/value, rationale, baseline and delivered source commits (or explicitly unknown/not applicable), date, OS, CPU/RAM, tool versions, dataset origin/hash/size and whether synthetic/demo/real, exact commands, repetitions, warm-up and cache state, all raw results, summary statistics and correctness checks. Record limitations, confounders and unfavorable runs. Repeat timings enough to distinguish variation; normally start with at least five paired trials and increase if variation warrants it. Keep cold and warm cache comparisons labeled and separate from code improvements.

Reduction = (baseline - improved) / baseline * 100. Speedup = baseline time / improved time. Use percentage points for differences between rates. Do not average incompatible workloads, mix source revisions, select only favorable samples or turn a reciprocal of latency into sustained throughput.

Separate engineering results (performance/correctness/recovery), workflow results (observed task time/manual steps) and real-world impact (observed adoption/user/business outcomes). Synthetic experiments support engineering claims only. Do not invent hours saved, customers, revenue or production capacity.

Each candidate claim must record problem/baseline, change, measured result, supporting commits/artifacts, conditions/limitations, verified personal contribution, proposed bullet and status **verified**, **preliminary** or **unverified**. Project results do not establish who personally implemented or executed the work. Use first-person implementation verbs only when contribution is independently known; otherwise use the capability wording below. Record confirmed personal work separately.

Before handoff trace every number to evidence, check applicability to the delivered tree, identify the strongest two or three results and mark remaining validation. Prepare draft bullets here; change an actual resume only when requested under the current resume instructions.

### Record template

| Field | Required record |
| --- | --- |
| Problem / value / category | Why this metric matters; engineering, workflow or real-world |
| Baseline / improved revision | Full SHAs; dirty state and source hashes; use N/A if no comparator |
| Environment / date | OS, CPU/RAM, runtime/compiler/dependency versions |
| Dataset | Origin, hash, size, characteristics; synthetic/demo/real |
| Procedure | Exact commands/steps; repetitions; warm-up/cache; condition order |
| Raw evidence / summary | Every sample/artifact; median/range/p95 as appropriate |
| Arithmetic / correctness | Explicit calculation; equivalent required outputs |
| Limitations | Noise, missing metadata, uncontrolled factors, negative results |
| Contribution / bullet / status | Actual personal work, supported wording, validation still needed |
