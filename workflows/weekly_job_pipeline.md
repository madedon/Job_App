# Weekly Job Application Pipeline v2 (Batch Mode)

## Objective
Process 10-60 job positions per daily run. Pre-screening eliminates non-starters automatically. Human review is batched into two compact checkpoints per session -- one for all CVs, one for all cover letters. Parallel subagent generation replaces sequential wait time.

---

## Pipeline Flow

```
STEP 1: Scan Gmail / Load positions
           |
STEP 2: Pre-screen (auto-skip rules)
           |
    AUTO_SKIP ────────────► Log to tracker (Skipped) → Done
           |
        PROCEED
           |
STEP 3: Scrape JDs (parallel, Firecrawl)
           |
STEP 4: Launch subagents in parallel
        (CV + keyword map per position)
           |
    ◆ BATCH CHECKPOINT 1: User reviews all CVs in one table
           |
    APPROVED positions only
           |
STEP 5: Launch subagents in parallel
        (Cover letter per approved position)
           |
    ◆ BATCH CHECKPOINT 2: User reviews all CLs in one table
           |
STEP 6: Update master (applications/job_pipeline_master.xlsx)
        Upload outputs to Google Drive
```

---

## Pre-Screening Rules (STEP 2)

**Tool:** `tools/prescreening_filter.py`
**Function:** `prescreen_batch(positions)`

Auto-skip rules (in priority order):

| Rule | Skip Condition |
|------|---------------|
| Non-DFW on-site | On-site signal + non-DFW city in location |
| PMP mandatory | "PMP required/mandatory" (not just preferred) |
| CPA/CFA mandatory | CPA/CFA certification required |
| Finance systems domain | 2+ finance system terms (AP/AR, ERP, close & consolidation, etc.) |
| Contract-only | Contract signals without conversion path |
| Posting closed | "position has been filled", "no longer accepting", etc. |
| Security clearance | Active/current clearance required |
| Junior role | 0-4 years experience patterns, entry-level, recent grad |
| Fashion/retail industry | Apparel/footwear industry experience required |
| Part-time only | Part-time without full-time option |
| K-12/education | Teaching credentials or education domain required |
| Wrong function | Non-PM roles (SWE, accountant, HR, etc.) |
| Niche industry | Restaurant/food service, actuarial, real estate license |

All AUTO_SKIP positions are logged to tracker immediately with reason in Notes.
PROCEED positions continue to JD scraping.

---

## JD Scraping (STEP 3)

**Tool:** Firecrawl MCP -- `mcp__firecrawl__firecrawl_scrape`

For each PROCEED position:
1. Create folder: `applications/{YYYY-MM-DD}_{Company}_{Role_Slug}/`
2. Scrape with: `formats: ["markdown"]`, `onlyMainContent: true`, `waitFor: 3000`
3. Save to `job_description.txt`

**Fallback chain (if scrape fails):**
Use `tools/scrape_jd.py` for domain-specific strategy. If all attempts fail, write placeholder for manual paste.

---

## Role Archetype Auto-Selection (STEP 4)

Before launching subagents, map each position to a base CV archetype:

| Archetype File | Use When Title Contains |
|---------------|------------------------|
| `applications/archetypes/cv_archetype_tpm.txt` | "Technical Program Manager", "TPM", "Engineering Program" |
| `applications/archetypes/cv_archetype_ai_transformation.txt` | "AI", "Digital Transformation", "Innovation", "Strategy" |
| `applications/archetypes/cv_archetype_pm.txt` | "Product Manager", "Senior PM", "Principal PM" |
| `applications/archetypes/cv_archetype_consulting_pm.txt` | "Consulting", "Advisory", "Client", "Professional Services" |

Default: `cv_archetype_tpm.txt` if no clear match.

---

## Parallel Subagent CV Generation (STEP 4)

Launch one subagent per PROCEED position simultaneously.

**Subagent prompt template:**

```
You are a CV optimization specialist. Generate an optimized CV for the following position.

POSITION: {company} -- {role}
ARCHETYPE: {archetype_file}

FILES TO READ:
1. Base CV: applications/archetypes/{archetype_file}
2. JD: applications/{folder}/job_description.txt
3. CV Prompt: CV_matching_Prompt.txt

EXECUTE the CV matching workflow (Steps 1-5 in CV_matching_Prompt.txt).

SAVE these files to applications/{folder}/:
- keyword_map.txt
- optimized_cv.txt
- changes_summary.txt

RETURN a one-line summary: "Company | Role | Match % | 3 top keywords"
```

Wait for all subagents to complete before proceeding to Checkpoint 1.

---

## BATCH CHECKPOINT 1: CV Review

Present a single review table covering all generated CVs:

```
CV REVIEW -- {N} positions ready

Num | Company          | Role                  | Match | Headline (first line)        | Top Keywords
----|------------------|-----------------------|-------|------------------------------|----------------
 1  | JPMorgan Chase   | Lead TPM              |  87%  | Lead Technical Program...    | infrastructure, governance, Agile
 2  | phData           | Sr PM AI & Data       |  86%  | Senior Program Manager...    | consulting, Snowflake, delivery
...

Reply options:
  "approve all"           → proceed all to cover letter
  "1 approve, 2 skip"     → mixed decisions
  "show 2"                → display full CV for position 2
  "changes to 1: [note]"  → revise specific CV
```

---

## Parallel Subagent Cover Letter Generation (STEP 5)

Launch one subagent per CV-approved position simultaneously.

**Subagent prompt template:**

```
You are a cover letter specialist. Generate a cover letter for the following position.

POSITION: {company} -- {role}

FILES TO READ:
1. CV: applications/{folder}/optimized_cv.txt
2. JD: applications/{folder}/job_description.txt
3. Keyword map: applications/{folder}/keyword_map.txt
4. CL Prompt: Cover_Letter_Prompt.txt

EXECUTE the cover letter workflow (Cover_Letter_Prompt.txt).

SAVE to: applications/{folder}/cover_letter.txt

RETURN: "Company | Role | Hook (first sentence) | Anchor | Word count | Keyword count"
```

---

## BATCH CHECKPOINT 2: Cover Letter Review

```
COVER LETTER REVIEW -- {N} positions ready

Num | Company        | Hook (first sentence)                                      | Anchor     | Words | KW
----|----------------|------------------------------------------------------------|------------|-------|----
 1  | JPMorgan Chase | "The most reliable evidence of TPM capability..."          | Ericsson   |  512  | 14
...

Reply options:
  "approve all"
  "1 approve, 3 skip"
  "show 2"
  "changes to 1: [note]"
```

---

## Output & Storage

- **Application folders saved locally:** `applications/{date}_{company}_{role}/`
- **Pipeline master updated:** `applications/job_pipeline_master.xlsx`
- **Upload to Google Drive:** Use MCP connector to save outputs to the configured Drive folder
- **Update master row** at each pipeline event using `tools/build_pipeline_master.py`

Status color codes:
- Applied: `C6EFCE` (green)
- Deferred: `FFEB9C` (yellow)
- Skipped / Auto-Skipped: `D9D9D9` (grey)
- Expired: `F4CCCC` (pink)
- Ready to Apply: `BDD7EE` (light blue)
- Interviewing: `9FC5E8` (blue)

---

## Execution Commands

Start full pipeline:
```
"Start the daily job application pipeline for [date]"
"Run the pipeline on these [N] positions: [list]"
```

Individual steps:
```
"Run pre-screening on these positions"
"Scrape JDs for the approved positions"
"Generate CVs for all PROCEED positions in parallel"
"Show me the batch CV checkpoint"
"Generate cover letters for the approved CVs"
```

---

## Inputs

- Gmail access: via MCP connector (Claude Code built-in)
- Base CVs: `applications/archetypes/cv_archetype_*.txt`
- CV prompt: `CV_matching_Prompt.txt`
- Cover letter prompt: `Cover_Letter_Prompt.txt`
- Pre-screening engine: `tools/prescreening_filter.py`
- JD scraping: Firecrawl MCP + `tools/scrape_jd.py`

## Outputs

- **Master tracker:** `applications/job_pipeline_master.xlsx`
- **Google Drive:** Outputs uploaded via MCP connector
- Application folders: `applications/{date}_{company}_{role}/`

---

## Known Constraints

| Constraint | Workaround |
|-----------|-----------|
| LinkedIn JDs behind login wall | Try direct URL → if blocked, flag for manual paste |
| Firecrawl credits (paid) | Prioritize T1/T2 roles; use `onlyMainContent: true` |
| Gmail token expiry | MCP connector handles auth automatically |
| Subagent context limits | Max ~8 subagents simultaneously; split large batches |
