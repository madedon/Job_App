"""
Pre-Screening Filter Engine
Automatically evaluates job descriptions against known deal-breaker rules
before any CV generation work begins.

Usage:
    from tools.prescreening_filter import prescreen
    result = prescreen(jd_text, company, role, location)
    # result: {"decision": "PROCEED" | "AUTO_SKIP", "reason": str, "flags": list}
"""

import sys
import io
import re
from datetime import datetime, timedelta

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass


# ─────────────────────────────────────────────
# RULE DEFINITIONS
# Each rule: (label, check_fn, skip_reason)
# check_fn receives (jd_lower, location_lower, role_lower)
# Returns True if the rule is triggered (→ AUTO_SKIP)
# ─────────────────────────────────────────────

def _is_non_dfw_onsite(jd_lower, location_lower, role_lower):
    """Skip if on-site outside Dallas-Fort Worth metro."""
    onsite_signals = ["on-site", "onsite", "on site", "in-office", "in office", "not remote",
                      "must relocate", "relocation required", "no remote", "office-based",
                      "100% onsite", "fully on-site", "fully onsite"]
    relocation_cities = [
        "new york", "nyc", "jersey city", "san francisco", "seattle", "redmond",
        "chicago", "boston", "austin", "denver", "mountain view", "menlo park",
        "sunnyvale", "san jose", "los angeles", "atlanta", "washington dc",
        "phoenix", "miami", "charlotte", "minneapolis", "pittsburgh",
        "buenos aires", "sao paulo", "london", "toronto", "vancouver",
        "algiers", "athens", "cairo", "bellevue", "cupertino", "palo alto",
        "san diego", "portland", "detroit", "columbus", "indianapolis",
        "salt lake", "raleigh", "durham", "nashville", "tampa", "orlando",
    ]
    is_onsite = any(sig in jd_lower for sig in onsite_signals)
    dfw_terms = ["remote", "frisco", "plano", "dallas", "irving",
                 "fort worth", "dfw", "mckinney", "allen",
                 "richardson", "addison", "westlake", "tx"]
    location_is_remote_or_dfw = any(x in location_lower for x in dfw_terms)
    location_is_non_dfw = any(city in location_lower for city in relocation_cities)
    jd_mentions_non_dfw = any(city in jd_lower for city in relocation_cities)
    jd_mentions_dfw = any(x in jd_lower for x in dfw_terms)
    if is_onsite and location_is_non_dfw and not location_is_remote_or_dfw:
        return True
    if is_onsite and not location_is_remote_or_dfw and jd_mentions_non_dfw and not jd_mentions_dfw:
        return True
    no_relocation = "no relocation" in jd_lower or "relocation is not" in jd_lower or "relocation not provided" in jd_lower
    if no_relocation and location_is_non_dfw and not location_is_remote_or_dfw:
        return True
    intl_only_cities = ["bangalore", "bengaluru", "hyderabad", "mumbai", "pune",
                        "singapore", "dublin", "berlin", "tokyo", "shanghai",
                        "beijing", "hong kong", "sydney", "melbourne"]
    location_is_intl = any(city in location_lower for city in intl_only_cities)
    if location_is_intl and is_onsite:
        return True
    return False


def _requires_pmp_mandatory(jd_lower, location_lower, role_lower):
    """Skip if PMP is stated as required (not just preferred)."""
    mandatory_patterns = [
        r"pmp\s*(certification)?\s*(is\s*)?(required|mandatory|must\s*have|necessary)",
        r"(required|must\s*have|mandatory)[^.]{0,60}pmp",
        r"pmp\s*required",
        r"project management professional.*required",
        r"pmp\s*certification\s*is\s*a\s*must",
        r"must\s*hold\s*(a\s*)?pmp",
        r"pmp\s*certified\s*(is\s*)?(required|mandatory)",
    ]
    preferred_patterns = [
        r"pmp\s*(is\s*)?(preferred|a plus|desired|nice to have|strongly preferred)",
        r"(preferred|a plus|desired)[^.]{0,60}pmp",
    ]
    jd_lower_clean = re.sub(r'\s+', ' ', jd_lower)
    for pat in preferred_patterns:
        if re.search(pat, jd_lower_clean):
            return False
    for pat in mandatory_patterns:
        if re.search(pat, jd_lower_clean):
            return True
    return False


def _requires_finance_cert_mandatory(jd_lower, location_lower, role_lower):
    """Skip if CPA/CFA certification is mandatory."""
    jd_clean = re.sub(r'\s+', ' ', jd_lower)
    mandatory = [
        r"(cpa|cfa)\s*(certification)?\s*(is\s*)?(required|mandatory|must\s*have)",
        r"(required|must\s*have|mandatory)[^.]{0,40}(cpa|cfa)\b",
    ]
    preferred = [
        r"(cpa|cfa)\s*(is\s*)?(preferred|a plus|desired|nice to have)",
    ]
    for pat in preferred:
        if re.search(pat, jd_clean):
            return False
    for pat in mandatory:
        if re.search(pat, jd_clean):
            return True
    return False


def _is_finance_domain(jd_lower, location_lower, role_lower):
    """Skip if the role's primary domain is financial systems (not finance industry generally)."""
    finance_system_terms = [
        "accounts payable", "accounts receivable", "ap/ar", " ar ", " ap ",
        "close and consolidation", "close & consolidation", "financial close",
        "general ledger", "erp implementation", "erp migration", "sap implementation",
        "workday financials", "oracle financials", "netsuite", "epicor",
        "revenue recognition", "financial systems modernization",
        "finance systems", "financial processes", "procurement systems",
        "order to cash", "procure to pay", "record to report",
        "treasury management", "tax compliance", "audit management",
        "financial reporting system", "chart of accounts", "subledger",
    ]
    hits = [term for term in finance_system_terms if term in jd_lower]
    return len(hits) >= 2


def _is_contract_only(jd_lower, location_lower, role_lower):
    """Skip pure contract roles (not contract-to-hire)."""
    contract_signals = ["contract position", "contract role", "contractor only",
                        "this is a contract", "w2 contract", "1099", "corp to corp",
                        "c2c", "contract only", "temporary position", "temp position",
                        "short-term assignment", "freelance position", "freelance role"]
    hire_signals = ["contract to hire", "contract-to-hire", "contract to perm",
                    "potential for full-time", "possible conversion"]
    is_contract = any(sig in jd_lower for sig in contract_signals)
    is_c2h = any(sig in jd_lower for sig in hire_signals)
    return is_contract and not is_c2h


def _is_posting_too_old(jd_lower, location_lower, role_lower, posted_text=""):
    """Flag if posting is explicitly closed, expired, or has a past end date."""
    closed_signals = ["this position has been filled", "position closed", "no longer accepting",
                      "posting expired", "job closed", "closed:", "no longer available",
                      "application period has ended", "applications are closed",
                      "this role has been filled", "this job has been filled"]
    if any(sig in jd_lower for sig in closed_signals):
        return True
    if "expired" in jd_lower:
        expired_patterns = [
            r'(posting|end|closing)\s*(date|deadline)?[^.]{0,40}expired',
            r'expired\s*(posting|position|listing|job)',
            r'[—–]\s*expired',
        ]
        for ep in expired_patterns:
            if re.search(ep, jd_lower):
                return True
    end_date_patterns = [
        r'posting\s*end\s*date',
        r'closing\s*date',
        r'application\s*deadline',
        r'apply\s*by',
        r'expires?\s*on',
        r'deadline',
        r'applications?\s*(close|end)\s*on',
    ]
    today = datetime.now()
    for pat in end_date_patterns:
        match = re.search(pat + r'[:\s]*([a-z]+\s+\d{1,2},?\s*\d{4})', jd_lower)
        if match:
            date_str = match.group(1).strip()
            try:
                for fmt in ["%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"]:
                    try:
                        end_date = datetime.strptime(date_str, fmt)
                        if end_date < today - timedelta(days=1):
                            return True
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        match_numeric = re.search(pat + r'[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-]\d{4})', jd_lower)
        if match_numeric:
            date_str = match_numeric.group(1).strip()
            try:
                for fmt in ["%m/%d/%Y", "%m-%d-%Y"]:
                    try:
                        end_date = datetime.strptime(date_str, fmt)
                        if end_date < today - timedelta(days=1):
                            return True
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
    return False


def _requires_security_clearance(jd_lower, location_lower, role_lower):
    """Skip if active security clearance is required."""
    clearance_patterns = [
        r"(active|current|must\s*hold|require[sd]?)[^.]{0,40}(secret|top secret|ts/sci|clearance)",
        r"security\s*clearance\s*(is\s*)?(required|mandatory)",
        r"must\s*(have|hold|possess)[^.]{0,30}clearance",
        r"(sci|ts/sci|top\s*secret)\s*(clearance\s*)?(required|mandatory)",
        r"public\s*trust\s*(clearance\s*)?(required|mandatory)",
        r"eligib(le|ility)\s*(for\s*)?secret\s*clearance",
    ]
    for pat in clearance_patterns:
        if re.search(pat, jd_lower):
            return True
    return False


def _is_wrong_function(jd_lower, location_lower, role_lower):
    """Skip if role title indicates a non-PM function entirely."""
    wrong_function_titles = [
        r"\b(software|staff|principal)\s*engineer\b",
        r"\baccountant\b",
        r"\b(hr|human\s*resources)\s*(manager|director|generalist)\b",
        r"\bnurse\b",
        r"\bteacher\b",
        r"\bsales\s*(representative|rep|executive)\b",
        r"\b(executive|administrative)\s*assistant\b",
        r"\bdata\s*entry\b",
        r"\bcustomer\s*service\s*(representative|agent)\b",
        r"\brecruiter\b",
        r"\bparalegal\b",
    ]
    for pat in wrong_function_titles:
        if re.search(pat, role_lower):
            return True
    return False


def _is_education_k12_domain(jd_lower, location_lower, role_lower):
    """Skip if role requires K-12/education-specific credentials."""
    education_signals = [
        r"teaching\s*(certificate|certification|license)\s*(required|mandatory)",
        r"(edd|ed\.d\.|doctor\s*of\s*education)\s*(required|preferred)",
        r"superintendent",
        r"school\s*(district|board|principal)",
        r"k-?12\s*(experience|background)\s*(required|mandatory)",
    ]
    for pat in education_signals:
        if re.search(pat, jd_lower):
            return True
    return False


def _is_niche_industry_mismatch(jd_lower, location_lower, role_lower):
    """Skip if role requires niche industry background that doesn't match user profile."""
    niche_patterns = [
        (["restaurant", "food service", "hospitality"],
         [r"(experience\s+in|background\s+in|industry)[^.]{0,40}(restaurant|food\s*service|hospitality)"]),
        (["actuarial", "underwriting", "claims processing"],
         [r"(actuarial|underwriting)\s*(experience|background)\s*(required|mandatory)"]),
        (["real estate license", "broker license", "mls"],
         [r"(real\s*estate|broker)\s*(license|certification)\s*(required|mandatory)"]),
    ]
    for terms, patterns in niche_patterns:
        term_hits = sum(1 for t in terms if t in jd_lower)
        if term_hits >= 1:
            for pat in patterns:
                if re.search(pat, jd_lower):
                    return True
    return False


def _is_part_time_only(jd_lower, location_lower, role_lower):
    """Skip if explicitly part-time only (not full-time)."""
    part_time_signals = ["part-time", "part time", "20 hours per week", "20 hrs/week",
                         "half-time", "10-20 hours"]
    full_time_signals = ["full-time", "full time", "40 hours"]
    is_part_time = any(sig in jd_lower for sig in part_time_signals)
    is_full_time = any(sig in jd_lower for sig in full_time_signals)
    return is_part_time and not is_full_time


def _is_fashion_retail_domain(jd_lower, location_lower, role_lower):
    """Skip if role explicitly requires fashion/retail/apparel industry experience."""
    industry_terms = ["apparel", "footwear", "fashion"]
    desirable_patterns = [
        r"(experience\s+in|industry\s+experience)[^.]{0,60}(apparel|retail|footwear|fashion)",
        r"(apparel|footwear|fashion)[^.]{0,40}(desirable|preferred|required|industry)",
    ]
    hits = sum(1 for term in industry_terms if term in jd_lower)
    if hits >= 1:
        for pat in desirable_patterns:
            if re.search(pat, jd_lower):
                return True
    return False


def _is_wrong_seniority(jd_lower, location_lower, role_lower):
    """Skip if role is clearly junior/mid-level (under 5 years experience)."""
    junior_patterns = [
        r"(0-2|1-3|2-4|0-3|3-5|2-5)\s*years",
        r"(entry[\s-]level|junior|associate)[^.]{0,30}(required|preferred|position)",
        r"recent\s*graduate",
        r"new\s*grad",
        r"\binternship\b",
        r"\bintern\b",
        r"co-?op\s*(position|role|program)",
    ]
    senior_titles = ["director", "principal", "vp ", "vice president", "head of", "senior director"]
    is_senior_title = any(t in role_lower for t in senior_titles)
    if is_senior_title:
        return False
    for pat in junior_patterns:
        if re.search(pat, jd_lower):
            return True
    return False


# ─────────────────────────────────────────────
# MAIN PRESCREEN FUNCTION
# ─────────────────────────────────────────────

RULES = [
    ("Non-DFW on-site role (relocation required)",   _is_non_dfw_onsite),
    ("PMP certification mandatory",                  _requires_pmp_mandatory),
    ("CPA/CFA certification mandatory",              _requires_finance_cert_mandatory),
    ("Finance systems domain (ERP/AP/AR/close)",     _is_finance_domain),
    ("Contract-only (no conversion path)",           _is_contract_only),
    ("Posting explicitly closed",                    _is_posting_too_old),
    ("Active security clearance required",           _requires_security_clearance),
    ("Junior/entry-level role (under 5 yrs)",        _is_wrong_seniority),
    ("Fashion/retail/apparel industry required",      _is_fashion_retail_domain),
    ("Part-time only (no full-time)",                 _is_part_time_only),
    ("K-12/education domain credentials required",    _is_education_k12_domain),
    ("Wrong function (non-PM role)",                  _is_wrong_function),
    ("Niche industry mismatch",                       _is_niche_industry_mismatch),
]


def prescreen(jd_text: str, company: str = "", role: str = "", location: str = "") -> dict:
    """Run all pre-screening rules against a job description."""
    jd_lower = jd_text.lower()
    loc_lower = location.lower()
    role_lower = role.lower()

    triggered = []
    for label, check_fn in RULES:
        try:
            if check_fn(jd_lower, loc_lower, role_lower):
                triggered.append(label)
        except Exception:
            pass

    if triggered:
        return {
            "decision": "AUTO_SKIP",
            "reason": triggered[0],
            "flags": triggered,
            "company": company,
            "role": role,
        }
    return {
        "decision": "PROCEED",
        "reason": "",
        "flags": [],
        "company": company,
        "role": role,
    }


def prescreen_batch(positions: list) -> dict:
    """Run prescreening on a list of positions."""
    proceed = []
    auto_skip = []

    for pos in positions:
        result = prescreen(
            jd_text=pos.get("jd_text", ""),
            company=pos.get("company", ""),
            role=pos.get("role", ""),
            location=pos.get("location", ""),
        )
        if result["decision"] == "PROCEED":
            proceed.append({**pos, **result})
        else:
            auto_skip.append({**pos, **result})

    summary_lines = [
        f"Pre-screening complete: {len(proceed)} PROCEED | {len(auto_skip)} AUTO_SKIP",
        "",
        "AUTO-SKIPPED:",
    ]
    for s in auto_skip:
        summary_lines.append(f"  x {s['company']} -- {s['role']}: {s['reason']}")
    summary_lines.append("")
    summary_lines.append("PROCEEDING TO CV GENERATION:")
    for p in proceed:
        summary_lines.append(f"  v {p['company']} -- {p['role']}")

    return {
        "proceed": proceed,
        "auto_skip": auto_skip,
        "summary": "\n".join(summary_lines),
    }


# ─────────────────────────────────────────────
# CLI TEST MODE
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        {
            "company": "Waymo",
            "role": "Finance Digital Engineering Program Lead",
            "location": "Mountain View, CA",
            "jd_text": """Lead digital engineering programs to modernize financial systems.
            Experience delivering technology programs within Finance, FinTech, Accounting systems, ERP domains.
            Strong understanding of financial processes close and consolidation, revenue, accounts payable,
            accounts receivable, procurement, budgeting, controls. On-site Mountain View CA required."""
        },
        {
            "company": "JPMorgan Chase",
            "role": "Lead Technical Program Manager",
            "location": "Plano, TX",
            "jd_text": """Lead complex technology programs. 5+ years TPM experience. Cross-functional collaboration.
            Risk management. Agile methodologies. PMP preferred but not required. Full-time role."""
        },
    ]

    results = prescreen_batch(test_cases)
    print(results["summary"])
