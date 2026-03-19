# Job Application Pipeline — Agent Instructions

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution.

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed

**Layer 3: Tools (The Execution)**
- Python scripts in `tools/` that do the actual work
- API calls, data transformations, file operations
- Credentials and API keys are stored in `.env`

## How to Operate

**1. Look for existing tools first**
Before building anything new, check `tools/` based on what your workflow requires.

**2. Learn and adapt when things fail**
Read the full error message and trace, fix the script and retest, document what you learned in the workflow.

**3. Keep workflows current**
Don't create or overwrite workflows without asking unless explicitly told to.

## Workflow Orchestration

- **Plan first** for any task with 3+ steps or architectural decisions
- **Use subagents** to keep the main context window clean
- **Verify before done** — run tests, check logs, demonstrate correctness
- **Autonomous bug fixing** — just fix it, zero context switching required

## File Structure

```
tools/                  # Python scripts for deterministic execution
workflows/              # Markdown SOPs defining what to do and how
applications/           # Job application output: {date}_{company}_{role}/
applications/archetypes/  # Base CV archetypes for different role types
tasks/                  # Task plans (todo.md) and agent lessons (lessons.md)
autoresearch/           # Filter optimization experiments and results
.tmp/                   # Temporary files (scraped data, intermediate exports)
.env                    # API keys and environment variables (NEVER commit)
credentials.json        # Google OAuth client credentials (NEVER commit)
token.json              # Gmail access token (NEVER commit)
token_drive.json        # Drive + Gmail combined token (NEVER commit)
```

## Quick Reference: Tools

| Tool | Purpose |
|------|---------|
| `gmail_job_scanner.py` | Scans Gmail for job alerts → raw output to `.tmp/Job_Alerts_{date}.xlsx` |
| `build_pipeline_master.py` | **Single source of truth** — merges/updates `applications/job_pipeline_master.xlsx` |
| `prescreening_filter.py` | Auto-skip rules engine (13 rules) — call before CV generation |
| `job_filter_benchmark.py` | Benchmarks filter against labeled dataset |
| `scrape_jd.py` | Domain-aware JD scrape instructions + fallback chain |
| `gdrive_upload.py` | Uploads files to Google Drive folders |
| `txt_to_pdf.py` | Converts .txt CV files to PDF |

## Quick Reference: Workflows

| Workflow | When to Use |
|----------|------------|
| `weekly_job_pipeline.md` | Full 7-step job application pipeline |
| `parallel_cv_orchestrator.md` | Parallel CV/CL generation with subagents |

## Project Context

**Python interpreter:** Use the system default `python` or `python3` command. If a specific interpreter is needed, set `PYTHON_PATH` in `.env`.

**Google OAuth files:**
- `credentials.json` — OAuth client credentials (from Google Cloud Console)
- `token.json` — Gmail access token (auto-generated on first run)
- `token_drive.json` — Drive + Gmail combined token (auto-generated on first run)

**Job applications:**
- Output folder: `applications/{date}_{company}_{role}/`
- Files per application: `job_description.txt`, `keyword_map.txt`, `optimized_cv.txt`, `cover_letter.txt`
- CV file naming: `Dimitrios_Tselios_{Short_Role_Title}.txt`

## Known Issues

- **Windows encoding**: All Python scripts include a cross-platform encoding fix (UTF-8 stdout wrapper)
- **Gmail token**: May expire between sessions — `authenticate()` in scripts handles refresh gracefully
- **Firecrawl credits**: Prioritize T1/T2 roles; use `onlyMainContent: true` to minimize tokens

## Task Decision Tree

```
User wants to...
├─ Scan for new job opportunities   → gmail_job_scanner.py → exports Excel
├─ Pre-screen positions             → prescreening_filter.py (auto-skip rules)
├─ Apply for a job                  → CV_matching_Prompt.txt → Cover_Letter_Prompt.txt
│                                     → save to applications/{date}_{company}_{role}/
├─ Upload files to Drive            → gdrive_upload.py
├─ Convert CV .txt to PDF           → txt_to_pdf.py
├─ Scrape a job description         → Firecrawl MCP or scrape_jd.py
└─ Benchmark filter rules           → job_filter_benchmark.py
```

## Named Workflow Patterns

**Job pipeline (per opening):** Gmail scan → extract JD → `CV_matching_Prompt.txt` (5-step) → `Cover_Letter_Prompt.txt` → save `applications/{date}_{company}_{role}/` → upload PDF to Drive → submit portal

**Google Drive upload:** `gdrive_upload.py` with target folder name → confirm upload success

## Task Management

1. Write plan to `tasks/todo.md` with checkable items
2. Confirm the plan before starting implementation
3. Mark items complete as you go
4. Log corrections to `tasks/lessons.md`

## Core Principles

- **Simplicity first**: Make every change as simple as possible
- **No laziness**: Find root causes. No temporary fixes
- **Minimal impact**: Only touch what's necessary

## Bottom Line

You sit between what I want (workflows) and what actually gets done (tools). Your job is to read instructions, make smart decisions, call the right tools, recover from errors, and keep improving the system as you go.

First read the research outcome completely before responding. DO NOT start executing if something is not clear — ask clarifying questions so we can refine the approach step by step.

Stay pragmatic. Stay reliable. Keep learning.
