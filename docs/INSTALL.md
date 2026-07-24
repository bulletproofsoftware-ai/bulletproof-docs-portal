# Install Guide — bulletproof-docs-portal

`bulletproof-docs-portal` is a single-file [FastAPI](https://fastapi.tiangolo.com)
application. Installation is: install the native PDF libraries, create a virtualenv,
install five Python packages, and run [Uvicorn](https://www.uvicorn.org). No database,
no container, no build step.

---

## Requirements

| Requirement | Notes |
|-------------|-------|
| **Python 3.10+** | The code uses `from __future__ import annotations` and modern type syntax; 3.10 or newer is expected. CI runs on 3.12. |
| **Cairo, Pango, GDK-PixBuf, libffi** | Native libraries [WeasyPrint](https://weasyprint.org) needs for PDF rendering. |
| A directory of projects to serve | Anything under `DOCS_ROOT` (default `~/Code`). |

---

## 1. Install native dependencies (for PDF export)

WeasyPrint renders PDFs using Cairo and Pango, which are **not** Python packages — you must
install them at the OS level first.

**macOS (Homebrew):**

```bash
brew install cairo pango gdk-pixbuf libffi
```

**Debian / Ubuntu:**

```bash
sudo apt-get update
sudo apt-get install -y libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0
```

If these are missing, the app will still start and browse/render HTML, but any request to
a `/pdf/` route will fail. For the definitive, per-platform list see the
[WeasyPrint installation docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

---

## 2. Get the code

```bash
git clone https://github.com/bulletproofsoftware-ai/bulletproof-docs-portal.git
cd bulletproof-docs-portal
```

---

## 3. Create a virtualenv and install Python dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

This installs the five direct dependencies (and their transitive tree):

| Package | Version | Role |
|---------|---------|------|
| `fastapi` | 0.115.0 | Web framework / routing |
| `uvicorn[standard]` | 0.32.0 | ASGI server that runs the app |
| `markdown` | 3.7 | Markdown → HTML rendering |
| `pygments` | 2.18.0 | Syntax highlighting for fenced code blocks |
| `weasyprint` | 68.0 | HTML → PDF conversion |

> WeasyPrint is pinned to **68.0** or newer: versions below 68.0 are affected by
> [CVE-2025-68616](https://github.com/advisories/GHSA-) (an SSRF protection bypass). See the
> [Scan Report](scan/scan-report.md) for details.

---

## 4. Run it

```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8090
```

Then open <http://localhost:8090>. By default the portal serves projects under `~/Code`.

To serve a different directory, set `DOCS_ROOT`:

```bash
DOCS_ROOT=/path/to/projects .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8090
```

---

## 5. Verify the install

```bash
# Liveness probe — should return JSON with a project count
curl -s http://127.0.0.1:8090/healthz
# → {"status":"ok","docs_root":"/…","projects":N}

# The index page should return HTTP 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/
# → 200
```

If `projects` is `0`, either `DOCS_ROOT` points at a directory with no matching docs, or
its subdirectories contain no `.md`/`.html` files matching the include patterns
(see [OVERVIEW.md](OVERVIEW.md)).

To confirm PDF export works end to end, browse to any doc in the UI and click
**Download PDF**, or:

```bash
curl -s -o out.pdf "http://127.0.0.1:8090/p/<project>/pdf/README.md"
file out.pdf   # → PDF document, version 1.x
```

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `cannot load library 'libgobject-2.0-0'` or similar on startup | Native WeasyPrint deps missing — re-run step 1. |
| `/pdf/` returns a 500 | Same as above; the HTML/browse paths work without Cairo/Pango, PDF does not. |
| Index shows "No projects with documentation found" | `DOCS_ROOT` is wrong, or projects contain no matching docs. Check with `/healthz`. |
| `address already in use` | Another process holds the port — pick a different `--port`. |
| A doc 404s | The path is outside `DOCS_ROOT` (traversal guard) or the file does not exist. |

---

Apache-2.0 © 2026 bulletproofsoftware-ai. See [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
