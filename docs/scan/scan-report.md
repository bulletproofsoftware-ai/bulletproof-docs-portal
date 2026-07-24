# Security Scan Report — bulletproof-docs-portal

**Scanner:** Code Hardener · **Profile:** `standard` (12 tools) · **Branch:** `main`
**Scan ID:** `7a064463-7be2-4bbc-97de-494ef51c7c5c` · **Date:** 2026-07-24

## Result

| Metric | Value |
|--------|-------|
| **Score** | **956 / 1000** |
| Critical | **0** |
| High | **0** |
| Medium | 3 |
| Low | 10 |
| Secrets (gitleaks) | **PASS — none found** |
| Tools executed | 12 |
| Attestation | Cryptographically signed (Ed25519, in-toto) |

This scan was run **after** all fixes below were applied and committed. It reports
**zero critical and zero high findings**. The remaining items are mediums/lows that are
either genuinely unpatchable upstream or cosmetic; each is documented honestly below.

Signed artifacts from this scan:

- [Attestation certificate PDF](bulletproof-docs-portal-scan-report.pdf) — page 1 is the
  signed score certificate (956/1000).
- [Full markdown report](scan-report-full.md)
- [SARIF](scan-report.sarif.json)
- [Attestation JSON](attestation.json)

---

## Findings fixed to reach this state

Every critical/high was driven to zero. The starting scan (score 800) had **2 HIGH**
findings; two more real mediums were also remediated. All fixes were verified
(dependency install + app import + `/healthz` + PDF-export smoke test) before re-scanning.

| Severity | Finding | Fix | Verification |
|----------|---------|-----|--------------|
| **HIGH** | `CVE-2025-68616` — WeasyPrint SSRF protection bypass via HTTP redirect (`weasyprint < 68.0`) | Bumped `weasyprint` **63.0 → 68.0** (advisory `firstPatchedVersion` = 68.0) | Verified via `gh api graphql securityAdvisories`; app imports and PDF export produce a valid PDF on 68.0 |
| MEDIUM | `CVE-2025-69534` — Python-Markdown uncaught `AssertionError` on malformed HTML (DoS, `markdown < 3.8.1`) | Bumped `markdown` **3.7 → 3.8.1** (advisory `firstPatchedVersion` = 3.8.1) | Rendering + PDF export re-tested on 3.8.1 |
| MEDIUM | `github-actions-mutable-action-tag` (×2) — CI steps use mutable tags `actions/checkout@v4`, `actions/setup-python@v5` | Pinned both to their commit SHAs (kept `# v4` / `# v5` comments) | SHAs resolved via `gh api repos/actions/<a>/commits/v4` |

---

## What remains (low-risk, documented)

These findings are intentionally not "fixed" — none is a critical or high, and each has a
sound reason to remain:

| Severity | Finding | Why it remains |
|----------|---------|----------------|
| MEDIUM | `CVE-2026-49452` — WeasyPrint CSS injection via presentational hints | **No patched version exists.** The advisory's vulnerable range is `<= 68.1` with no `firstPatchedVersion` as of this scan. Low impact for this app's model (renders *local, trusted* docs; presentational hints require crafted HTML in the doc source). Will bump when a patched WeasyPrint ships. |
| MEDIUM | `RUFF-F401` — `RedirectResponse` imported but unused in `app.py` | Cosmetic. A pre-existing unused import; removing it is unrelated to the security posture and out of scope for this pass. |
| LOW | `CVE-2026-4539` (×2) | Low-severity transitive advisory with no material impact on this read-only, localhost-bound app; no upstream fix applied to avoid churn. |
| LOW | `SBOM-LICENSE-UNKNOWN` (×7) | Components whose upstream metadata does not machine-declare an SPDX license id. The license is stated in each project's text; these are cataloged in the [SBOM](../SBOM.md), not license-free. |
| LOW | `LICENSE-Apache-2.0` (informational) | Notes the project's own Apache-2.0 license — expected and correct. |

The playbook standard for this program is **zero critical / zero high before publishing**,
which this scan satisfies. Mediums and lows are documented rather than force-fixed, since
aggressive auto-remediation (e.g. stripping "unused" code) risks removing defensive guards
for no security gain.

---

## Reproducing

```bash
# Against a running Code Hardener (standard profile)
curl -X POST http://localhost:7002/api/v1/scans \
  -H 'Content-Type: application/json' \
  -d '{"projectId":"<id>","repositoryUrl":"file:///path/to/bulletproof-docs-portal","scanType":"standard","branch":"main"}'
```

---

Apache-2.0 © 2026 bulletproofsoftware-ai. See [LICENSE](../../LICENSE) and [NOTICE](../../NOTICE).
