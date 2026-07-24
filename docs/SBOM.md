# Software Bill of Materials — bulletproof-docs-portal

This document summarizes the dependency inventory for `bulletproof-docs-portal`. The
machine-readable SBOM is committed alongside it in **CycloneDX 1.x** format:

- [`bulletproof-docs-portal.cyclonedx.json`](bulletproof-docs-portal.cyclonedx.json)

It was generated from a clean virtualenv install of [`requirements.txt`](../requirements.txt)
using `cyclonedx-py`, so it captures the full transitive dependency tree — not just the
five direct packages.

---

## Direct dependencies

These are the packages the application declares in `requirements.txt`:

| Package | Version | License | Role |
|---------|---------|---------|------|
| [fastapi](https://pypi.org/project/fastapi/) | 0.115.0 | MIT | Web framework, routing, responses |
| [uvicorn[standard]](https://pypi.org/project/uvicorn/) | 0.32.0 | BSD-3-Clause | ASGI server |
| [markdown](https://pypi.org/project/Markdown/) | 3.8.1 | BSD | Markdown → HTML rendering |
| [pygments](https://pypi.org/project/Pygments/) | 2.18.0 | BSD-2-Clause | Code syntax highlighting |
| [weasyprint](https://pypi.org/project/weasyprint/) | 68.0 | BSD | HTML → PDF conversion |

> **Security-relevant pins.** `weasyprint` is held at **68.0+** (fixes
> [CVE-2025-68616](https://github.com/advisories/), SSRF protection bypass) and `markdown`
> at **3.8.1+** (fixes [CVE-2025-69534](https://github.com/advisories/), an uncaught
> parser exception). See the [Scan Report](scan/scan-report.md).

---

## Transitive inventory

The full graph resolves to **65 components** (direct + transitive). The
[CycloneDX JSON](bulletproof-docs-portal.cyclonedx.json) is the authoritative list; the
notable transitive libraries include:

| Component | Provides | Pulled in by |
|-----------|----------|--------------|
| `starlette` | ASGI toolkit underlying FastAPI | fastapi |
| `pydantic`, `pydantic-core` | Request/response data modeling | fastapi |
| `anyio`, `sniffio` | Async I/O abstraction | starlette / fastapi |
| `httptools`, `websockets`, `uvloop`, `watchfiles`, `python-dotenv` | Uvicorn "standard" extras | uvicorn[standard] |
| `pydyf`, `tinycss2`, `cssselect2`, `pyphen`, `Pillow`, `fonttools`, `tinyhtml5` | PDF rasterization / CSS / fonts / images | weasyprint |
| `cffi`, `pycparser` | Native binding layer (Cairo/Pango via CFFI) | weasyprint |

---

## License distribution

Across all 65 components (licenses as declared by upstream package metadata, normalized):

| License | Components |
|---------|-----------|
| MIT | 29 |
| BSD-3-Clause | 9 |
| Apache-2.0 | 8 |
| BSD (unspecified variant) | 6 |
| BSD-2-Clause | 1 |
| BSD / BSD-2-Clause | 1 |
| LGPL-2.0-or-later | 1 |
| Python-2.0 | 1 |
| MPL-2.0 | 1 |
| ISC | 1 |
| Apache-2.0 OR BSD-2-Clause | 1 |
| HPND | 1 |
| GPL-2.0-or-later / LGPL-2.0+ / MPL-1.1 (multi-licensed) | 1 |
| Apache-2.0 / BSD | 1 |
| PSF-2.0 | 1 |
| Apache-2.0 / MIT | 1 |
| BSD / BSD-3-Clause | 1 |

All are permissive or weak-copyleft licenses compatible with distributing this Apache-2.0
project. The single component with a `GPL-2.0-or-later` option (`Pyphen`) is **multi-licensed**
and also offered under LGPL-2.0+ and MPL-1.1, which are compatible; no dependency imposes a
strong-copyleft obligation on the portal itself. The seven "license unknown" low findings in
the scan reflect components whose upstream metadata does not machine-declare a SPDX id (the
license is stated in their project text); they are cataloged, not license-free.

---

## Base images and runtime

There is **no container image** in this repository — no Dockerfile, no compose file. The app
runs directly on a host Python 3.10+ interpreter (CI uses 3.12) plus the system-level native
libraries WeasyPrint requires (Cairo, Pango, GDK-PixBuf, libffi), which are installed via the
OS package manager rather than pip. Those native libraries are outside the Python SBOM; see
[INSTALL.md](INSTALL.md) for the platform packages.

---

## Regenerating the SBOM

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pip install cyclonedx-bom
.venv/bin/cyclonedx-py environment .venv --output-format json \
  > docs/bulletproof-docs-portal.cyclonedx.json
```

---

Apache-2.0 © 2026 bulletproofsoftware-ai. See [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
