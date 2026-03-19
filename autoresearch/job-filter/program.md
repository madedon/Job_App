# Job Prescreening Filter Auto Research

Autonomous optimization of the job prescreening filter that decides which positions are worth pursuing (PROCEED) vs which to skip (AUTO_SKIP) based on job description text analysis.

## Setup

1. **Create a branch**: `git checkout -b autoresearch/job-filter-v1` from current state.
2. **Read the in-scope files**:
   - `tools/prescreening_filter.py` -- the file you modify. 13 filter rules with pattern matching and heuristics.
   - `tools/job_filter_benchmark.py` -- the benchmark script. **Do not modify.**
   - `.tmp/job_filter_labeled_dataset.json` -- labeled positions with JD text and outcomes. **Do not modify.**
3. **Initialize results.tsv**: Create `autoresearch/job-filter/results.tsv` with the header row.
4. **Run baseline**: Execute the benchmark.
5. **Confirm and go**: Begin the loop.

## Experimentation

Each experiment takes <1 second (pure regex, no API calls). Run as:

```bash
python tools/job_filter_benchmark.py
```

**What you CAN modify:**
- `tools/prescreening_filter.py` -- everything is fair game:
  - Rule functions, pattern lists, threshold values
  - Add entirely new rules
  - Rule ordering and interaction logic

**What you CANNOT modify:**
- `tools/job_filter_benchmark.py` -- the benchmark evaluator
- `.tmp/job_filter_labeled_dataset.json` -- the ground truth data
- Do not add pip dependencies

**The goal: maximize weighted_f1 (F2 score) while improving filter_rate.**

**CRITICAL CONSTRAINT: Recall must stay at 100%.** Never introduce a rule that would AUTO_SKIP a position that was actually Applied/Deferred.

## Output format

```
---
accuracy:         0.918919
precision:        0.906250
recall:           1.000000
f1:               0.950820
weighted_f1:      0.979730
filter_rate:      0.625000
```

## Logging results

Log to `autoresearch/job-filter/results.tsv` (tab-separated):

```
commit	weighted_f1	filter_rate	recall	status	description
```

## The experiment loop

LOOP FOREVER:

1. Modify `tools/prescreening_filter.py`
2. git commit
3. Run: `python tools/job_filter_benchmark.py > autoresearch/job-filter/run.log 2>&1`
4. Read key metrics from run.log
5. **REJECT if recall < 1.0**
6. If weighted_f1 improved AND recall == 1.0: keep
7. If not: git reset
8. Log to results.tsv
9. Repeat
