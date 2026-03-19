# Parallel CV Orchestrator

## Purpose
Launch N subagents simultaneously to generate CVs and cover letters in parallel rather than sequentially. Reduces pipeline wall time from ~15 min/position to ~15 min total for a batch of 10.

---

## When to Use
- Called from `weekly_job_pipeline.md` at STEP 4 (CV generation) and STEP 5 (CL generation)
- Any time you have 2+ positions that need CV or cover letter generation
- Minimum batch size for parallelization: 2 positions (below that, just run inline)

---

## Constraints
- Max simultaneous subagents: 8 (split larger batches into waves of 8)
- Each subagent needs: company, role, folder path, archetype file name
- Subagents write their own output files -- do NOT write them from the orchestrator

---

## Archetype Selection Logic

```
title_lower = role.lower()

if any(x in title_lower for x in ["technical program", "tpm", "engineering program", "infrastructure program"]):
    archetype = "cv_archetype_tpm.txt"
elif any(x in title_lower for x in ["ai", "digital transformation", "innovation", "strategy", "transformation"]):
    archetype = "cv_archetype_ai_transformation.txt"
elif any(x in title_lower for x in ["product manager", "senior pm", "principal pm", "sr. pm", "vp product"]):
    archetype = "cv_archetype_pm.txt"
elif any(x in title_lower for x in ["consulting", "advisory", "client", "professional services", "engagement"]):
    archetype = "cv_archetype_consulting_pm.txt"
else:
    archetype = "cv_archetype_tpm.txt"  # default
```

---

## CV Generation Subagent Prompt

```
You are a CV optimization specialist. Your only job is to generate one optimized CV.

POSITION:
  Company: {company}
  Role: {role}
  Folder: applications/{folder}/

FILES TO READ (in order):
  1. Base CV archetype: applications/archetypes/{archetype_file}
  2. Job description: applications/{folder}/job_description.txt
  3. CV workflow prompt: CV_matching_Prompt.txt

EXECUTE the full CV matching workflow from CV_matching_Prompt.txt (Steps 1-5).

SAVE these files to applications/{folder}/:
  - keyword_map.txt
  - optimized_cv.txt
  - changes_summary.txt

RETURN exactly this format (one line):
"{company} | {role} | {match_pct}% | {keyword1}, {keyword2}, {keyword3}"
```

---

## Cover Letter Generation Subagent Prompt

```
You are a cover letter specialist. Your only job is to generate one cover letter.

POSITION:
  Company: {company}
  Role: {role}
  Folder: applications/{folder}/

FILES TO READ (in order):
  1. Optimized CV: applications/{folder}/optimized_cv.txt
  2. Job description: applications/{folder}/job_description.txt
  3. Keyword map: applications/{folder}/keyword_map.txt
  4. Cover letter workflow prompt: Cover_Letter_Prompt.txt

EXECUTE the full cover letter workflow from Cover_Letter_Prompt.txt.

SAVE to: applications/{folder}/cover_letter.txt

RETURN exactly this format (one line):
"{company} | {role} | {hook_sentence} | {anchor} | {word_count} words | {keyword_count} keywords"
```

---

## Orchestration Steps

### CV Generation Wave

1. Run archetype selection for all PROCEED positions
2. For each position, prepare subagent prompt with correct values filled in
3. Launch all subagents simultaneously (max 8 per wave)
4. Wait for all to complete
5. Collect one-line summaries from each subagent
6. Build Batch Checkpoint 1 table from summaries
7. Present table to user

### Cover Letter Generation Wave

1. Filter to CV-approved positions only
2. For each approved position, prepare CL subagent prompt
3. Launch all subagents simultaneously (max 8 per wave)
4. Wait for all to complete
5. Collect one-line summaries from each subagent
6. Build Batch Checkpoint 2 table from summaries
7. Present table to user

---

## Error Handling

| Error | Action |
|-------|--------|
| Subagent returns no output | Re-run that subagent individually |
| `optimized_cv.txt` not created | Check if `job_description.txt` exists -- if empty/missing, flag for manual JD paste |
| `cover_letter.txt` not created | Check if `optimized_cv.txt` exists and CV was approved |
| Match % below 65% | Flag in table with low-match indicator -- let user decide |
| Subagent timeout | Re-run individually |

---

## Performance Notes

- Each subagent CV run: ~2-4 minutes
- 8 parallel subagents: ~4 minutes total vs. ~32 minutes sequential
- Cover letter runs are faster (~1-2 min each)
- For 30-position batches: run 4 waves of ~8 = ~16-20 minutes total CV generation
