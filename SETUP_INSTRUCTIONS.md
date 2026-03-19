# Job_App — Setup & Run Instructions

## Quick Start (Any Machine — Mac or PC)

### 1. Clone the Repo
```bash
git clone https://github.com/madedon/Job_App.git
cd Job_App
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Credentials

**Option A: Claude Code with MCP connectors (Recommended)**
If you're running inside Claude Code with Google connectors already configured, you don't need local credentials. The agent will use:
- `mcp__claude_ai_Gmail__*` for email scanning
- Google Drive MCP for file uploads
- Firecrawl MCP for JD scraping

**Option B: Standalone Python scripts**
For running tools outside of Claude Code:
```bash
cp .env.example .env
# Edit .env and add your FIRECRAWL_API_KEY
```
Then copy these files from your Google Cloud Console (project: claudecodeautomations):
- `credentials.json` → repo root
- `token.json` → repo root (auto-generated on first Gmail scan)
- `token_drive.json` → repo root (auto-generated on first Drive upload)

### 4. Launch Claude Code
```bash
cd Job_App
claude
```

---

## How to Run the Pipeline

### Full Pipeline (Most Common)
```
Start the daily job application pipeline
```
This runs all 7 steps: Gmail scan → Pre-screen → Scrape JDs → Generate CVs → Review → Generate Cover Letters → Review → Update tracker

### Individual Steps

| Command | What It Does |
|---------|-------------|
| `Scan Gmail for job alerts from the last 3 days` | Runs Gmail scanner, exports Excel to .tmp/ |
| `Run pre-screening on these positions` | Filters positions through 13 auto-skip rules |
| `Scrape JD for [URL]` | Scrapes job description using Firecrawl |
| `Generate CV for [Company] - [Role]` | Creates optimized CV using archetype + prompt |
| `Generate cover letter for [Company] - [Role]` | Creates cover letter from optimized CV |
| `Convert [folder] to PDF` | Generates PDF from .txt CV and cover letter |
| `Upload [file] to Google Drive` | Uploads to Job Search Tracker folder |

### Batch Mode (Parallel Processing)
```
Generate CVs for all PROCEED positions in parallel
```
Launches up to 8 subagents simultaneously. See `workflows/parallel_cv_orchestrator.md`.

### Resume from Checkpoint
```
Resume pipeline from Checkpoint 2 — CVs approved
Re-run CV for position 3 with changes: [your note]
```

---

## Project Structure

```
Job_App/
├── CLAUDE.md                          # Agent instructions (auto-loaded)
├── SETUP_INSTRUCTIONS.md              # This file
├── CV_matching_Prompt.txt             # 5-step CV optimization prompt
├── Cover_Letter_Prompt.txt            # Cover letter generation prompt
├── ORIGINAL_CV.txt                    # Master CV baseline
├── requirements.txt                   # Python dependencies
├── .env.example                       # API key template
├── .gitignore                         # Excludes secrets & temp files
│
├── tools/                             # Deterministic Python scripts
│   ├── prescreening_filter.py         # 13-rule auto-skip engine
│   ├── gmail_job_scanner.py           # Gmail alert scanner → Excel
│   ├── scrape_jd.py                   # Domain-aware JD scraper
│   ├── build_pipeline_master.py       # Pipeline master tracker
│   ├── txt_to_pdf.py                  # CV/CL text → PDF converter
│   ├── gdrive_upload.py               # Google Drive file uploader
│   └── job_filter_benchmark.py        # Filter accuracy benchmark
│
├── workflows/                         # Markdown SOPs
│   ├── weekly_job_pipeline.md         # Full 7-step pipeline
│   └── parallel_cv_orchestrator.md    # Parallel CV/CL generation
│
├── applications/                      # Generated application folders
│   └── archetypes/                    # Base CV templates
│       ├── cv_archetype_tpm.txt       # Technical Program Manager
│       ├── cv_archetype_ai_transformation.txt  # AI/Digital Transformation
│       ├── cv_archetype_pm.txt        # Product Manager
│       └── cv_archetype_consulting_pm.txt      # Consulting/Professional Services
│
├── autoresearch/                      # Filter optimization
│   └── job-filter/
│       ├── program.md                 # Experiment specification
│       └── results.tsv                # 25 experiments (F1=1.0)
│
├── tasks/                             # Task tracking
│   └── todo.md                        # Current session plan
│
└── .tmp/                              # Temporary files (gitignored)
    └── Job_Alerts_YYYYMMDD.xlsx       # Gmail scan output
```

---

## Key Workflows

### Weekly Job Application Pipeline
**File:** `workflows/weekly_job_pipeline.md`

```
STEP 1: Scan Gmail for job alerts
STEP 2: Pre-screen (auto-skip 13 rules)
STEP 3: Scrape job descriptions (Firecrawl)
STEP 4: Generate CVs in parallel (subagents)
  → CHECKPOINT 1: Review all CVs in batch table
STEP 5: Generate cover letters in parallel
  → CHECKPOINT 2: Review all CLs in batch table
STEP 6: Update pipeline master tracker
STEP 7: Upload to Google Drive
```

### Pre-Screening Filter (13 Rules)
**File:** `tools/prescreening_filter.py`

| # | Rule | Auto-Skip When |
|---|------|---------------|
| 1 | Non-DFW on-site | On-site + non-Dallas location |
| 2 | PMP mandatory | PMP certification required |
| 3 | CPA/CFA mandatory | Finance cert required |
| 4 | Finance systems | 2+ finance system terms |
| 5 | Contract-only | No conversion to full-time |
| 6 | Posting closed | Position filled/expired |
| 7 | Security clearance | Active clearance required |
| 8 | Junior role | Under 5 years experience |
| 9 | Fashion/retail | Industry experience required |
| 10 | Part-time only | No full-time option |
| 11 | K-12/education | Teaching credentials needed |
| 12 | Wrong function | Non-PM role (SWE, HR, etc.) |
| 13 | Niche industry | Restaurant, actuarial, real estate |

### CV Archetypes
The system auto-selects the best base CV based on role title:

| Role Keywords | Archetype Used |
|--------------|----------------|
| TPM, Technical Program, Engineering Program | `cv_archetype_tpm.txt` |
| AI, Digital Transformation, Innovation | `cv_archetype_ai_transformation.txt` |
| Product Manager, Senior PM, Principal PM | `cv_archetype_pm.txt` |
| Consulting, Advisory, Professional Services | `cv_archetype_consulting_pm.txt` |

---

## Google Drive Integration

**Output folder:** https://drive.google.com/drive/u/0/folders/1vsV9V-vYevsq1xu5H4FAHcZNE3xvVrJU

When running inside Claude Code with MCP connectors, outputs are automatically saved to this Drive folder. The pipeline saves:
- `job_pipeline_master.xlsx` — single source of truth tracker
- `{Company}_{Role}/` folders with CV, cover letter, keyword map
- PDF versions of CV and cover letter

---

## Updating the Filter

To improve the prescreening filter:
```
Run the filter benchmark
```
This tests all 13 rules against labeled data. Current performance: **100% accuracy, 100% recall, 100% filter rate**.

To add new rules, modify `tools/prescreening_filter.py` and run:
```bash
python tools/job_filter_benchmark.py --verbose
```

See `autoresearch/job-filter/program.md` for the full experimentation framework.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `credentials.json not found` | Download from Google Cloud Console (project: claudecodeautomations) |
| `Token refresh failed` | Delete `token.json` and re-run — browser auth will trigger |
| `fpdf2 not found` | Run `pip install fpdf2` |
| `Firecrawl scrape fails` | Check FIRECRAWL_API_KEY in .env; some sites block scrapers |
| `Excel encoding errors` | Scripts include cross-platform UTF-8 fix automatically |

---

## Version History

- **v1.0** (2026-03-19): Initial portable release
  - 7 tools, 2 workflows, 4 archetypes
  - 13 prescreening rules (25 experiments, F1=1.0)
  - Cross-platform (Windows + Mac)
  - MCP-native (Gmail, Drive, Firecrawl)
