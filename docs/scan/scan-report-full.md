# Security Scan Report: bulletproof-docs-portal

**Scan ID:** `7a064463-7be2-4bbc-97de-494ef51c7c5c`
**Date:** 2026-07-24T21:05:11.724Z
**Score:** 1000/1000 (excellent)
**Branch:** main | **Commit:** `N/A`
**Profile:** standard

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Medium | 3 |
| Low | 10 |
| Info | 0 |
| **Total (open)** | **13** |

> **Note:** The counts above reflect _open_ findings only.
> 1 scanner(s) were skipped — see "Skipped Scanners" below.

## Scanners Executed

| Scanner | Status | Findings | Duration | Notes |
|---------|--------|----------|----------|-------|
| trivy | pass | 3 | 2.5s |  |
| gitleaks | pass | 0 | 0.5s |  |
| opengrep | pass | 0 | 6.2s |  |
| checkov | pass | 0 | 3.6s |  |
| grype | pass | 2 | 3.4s |  |
| syft | pass | 7 | 1.6s |  |
| package-validator | pass | 0 | 0.1s |  |
| oxlint | skipped | 0 | 0.0s | _skipped: no_matching_files_ |
| ruff | pass | 1 | 0.0s |  |
| actionlint | pass | 0 | 0.0s |  |
| jscpd | pass | 0 | 0.0s |  |
| typos | pass | 0 | 0.0s |  |
| _file_inventory | pass | 0 | 0.0s |  |

## Medium Findings (3)

### [MEDIUM] \`fastapi.responses.RedirectResponse\` imported but unused

- **File:** `app.py:26`
- **Scanner:** ruff
- **Rule:** `RUFF-F401`

**What's wrong:** `fastapi.responses.RedirectResponse` imported but unused

**How to fix:** Auto-fix available: Remove unused import: `fastapi.responses.RedirectResponse` (applicability: safe)

**Action:** Plan to fix this issue in your next sprint or release.

---

### [MEDIUM] Using outdated libraries with known security issues.

- **File:** `/requirements.txt`
- **Scanner:** grype
- **Rule:** `CVE-2026-49452`
- **OWASP:** A06:2021-Vulnerable and Outdated Components

**What's wrong:** WeasyPrint has CSS Injection via Presentational Hints

**Code:**
```
Package: weasyprint
Version: 68.0
Type: python
Language: python
```

**How to fix:** Review this finding and apply the appropriate fix based on the description: WeasyPrint has CSS Injection via Presentational Hints

**Action:** Plan to fix this issue in your next sprint or release.

---

### [MEDIUM] Using outdated libraries with known security issues.

- **File:** `requirements.txt`
- **Scanner:** trivy
- **Rule:** `CVE-2026-49452`
- **OWASP:** A06:2021-Vulnerable and Outdated Components

**What's wrong:** ### Summary
A CSS injection issue exists in WeasyPrint when HTML presentational hints are enabled. Unescaped attribute values are embedded into CSS, allowing injection of arbitrary CSS declarations. This affects applications processing untrusted HTML input.

### Details
File: weasyprint/css/__init__.py

The `background` attribute is used to construct CSS:

background-image:url({element.get("background")})

This string is parsed by `tinycss2.parse_blocks_contents()`.

Because the value is not escaped, additional CSS declarations can be injected.

### PoC
<body background="x);background-image:url(http://169.254.169.254/latest/meta-data/)">

### Impact
- CSS injection
- Server-side requests via injected `url()`
- Limited to cases where `presentational_hints=True`

### Suggested Fix
- Escape attribute values before embedding into CSS
- Restrict allowed values for presentational hints
[VULN-05_css_injection_presentational_hints.md](https://github.com/user-attachments/files/26370718/VULN-05_css_injection_presentational_hints.md)

**Code:**
```
Package: weasyprint
Installed: 68.0
Fixed: N/A
```

**How to fix:** Review this finding and apply the appropriate fix based on the description: ### Summary
A CSS injection issue exists in WeasyPrint when HTML presentational hints are enabled. Unescaped attribute values are embedded into CSS, allowing injection of arbitrary CSS declarations. T

**Action:** Plan to fix this issue in your next sprint or release.

---

## Low Findings (10)

- **SBOM-LICENSE-UNKNOWN**: Unknown License: weasyprint@68.0 (`/requirements.txt`)
- **SBOM-LICENSE-UNKNOWN**: Unknown License: uvicorn@0.32.0 (`/requirements.txt`)
- **SBOM-LICENSE-UNKNOWN**: Unknown License: pygments@2.18.0 (`/requirements.txt`)
- **SBOM-LICENSE-UNKNOWN**: Unknown License: markdown@3.8.1 (`/requirements.txt`)
- **SBOM-LICENSE-UNKNOWN**: Unknown License: fastapi@0.115.0 (`/requirements.txt`)
- **SBOM-LICENSE-UNKNOWN**: Unknown License: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 (`/.github/workflows/ci.yml`)
- **SBOM-LICENSE-UNKNOWN**: Unknown License: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 (`/.github/workflows/ci.yml`)
- **CVE-2026-4539**: CVE-2026-4539: Vulnerability in pygments@2.18.0 (`/requirements.txt`)
- **LICENSE-Apache-2.0**: License Compliance: Apache-2.0 in  (`LICENSE`)
- **CVE-2026-4539**: CVE-2026-4539: pygments: Pygments: Denial of Service via inefficient regular expression processing in AdlLexer (`requirements.txt`)

## Skipped Scanners (1)

Scanners that did not run on this scan, with the reason why and how to enable them.

| Scanner | Reason | How to enable |
|---------|--------|---------------|
| `oxlint` | no_matching_files | No .js/.ts files found — Oxlint requires a JavaScript/TypeScript project |

## Recommendations

1. Update 5 vulnerable dependency/dependencies -- run `npm audit fix` or equivalent

---
*Generated by Code Hardener v0.1.0 | 2026-07-24T21:06:31.345Z*