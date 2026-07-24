# Comprehensive Overview — bulletproof-docs-portal

A minimal, single-process web app that turns a directory of projects into a browsable,
PDF-exportable documentation portal. Point it at a folder, and it walks every project
inside, lists the Markdown and HTML docs it finds, renders them as clean HTML in your
browser, and offers a one-click **PDF download** (or a **ZIP** of all of a project's docs).

- **New here?** → [Install Guide](INSTALL.md) then [How To Use](HOW-TO-USE.md)
- **Running it for a team?** → [Administrator Guide](ADMINISTRATOR.md)
- **Security posture?** → [Scan Report](scan/scan-report.md) · [SBOM](SBOM.md)

---

## The problem it solves

Documentation lives scattered across dozens of repositories — a `README.md` here, a
`docs/` folder there, an odd `.html` design note somewhere else. Reading it usually means
either cloning each repo and opening files in an editor, or standing up a heavyweight docs
site generator per project. Neither is convenient for a quick browse, and neither gives
you a portable PDF to hand to someone.

`bulletproof-docs-portal` is the smallest thing that solves this: a single Python file
(`app.py`) that serves a live index of every project under a configured root, renders any
doc on demand, and exports it to PDF. **No auth, no database, no build step, one process.**
It is intended to run locally (bound to `127.0.0.1`) against your own project tree.

---

## What's in the repository

| Path | What it is |
|------|------------|
| [`app.py`](../app.py) | The entire application: a [FastAPI](https://fastapi.tiangolo.com) app with 7 routes, Markdown→HTML rendering, and WeasyPrint PDF export |
| [`requirements.txt`](../requirements.txt) | Five direct Python dependencies (FastAPI, Uvicorn, Markdown, Pygments, WeasyPrint) |
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | CI: compile-check every `.py` file and run tests if any exist |
| `LICENSE`, `NOTICE` | Apache-2.0 license text and attribution notice |
| [`docs/`](.) | This documentation set, SBOM, and the security scan artifacts |

There is no Dockerfile, no compose file, no frontend build, and no persistent storage —
by design. The app holds no state; it reads from the filesystem on every request.

---

## How it works

```
                    ┌──────────────────────────────────────────────┐
   Browser  ───────▶│  FastAPI app (app.py) on 127.0.0.1:8090      │
                    │                                              │
                    │   /            list projects under DOCS_ROOT  │
                    │   /p/{proj}    tree of a project's docs       │
                    │   /p/…/d/{doc} render doc as HTML             │
                    │   /p/…/pdf/{doc} WeasyPrint → PDF             │
                    │   /p/…/raw/{doc} raw file bytes               │
                    │   /p/…/zip     all project docs as a ZIP      │
                    │   /healthz     liveness + project count       │
                    └───────────────────────┬──────────────────────┘
                                             │ reads (never writes)
                                             ▼
                       DOCS_ROOT   e.g. ~/Code
                        ├── project-a/  README.md, docs/**.md …
                        ├── project-b/  docs/**.html …
                        └── …
```

1. **Discovery.** On each request to `/`, the app iterates the immediate subdirectories of
   `DOCS_ROOT`, skipping dotfiles and build/vendor directories
   (`.git`, `node_modules`, `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `dist`,
   `build`). A project is listed only if it contains at least one matching doc.
2. **Doc listing.** Within a project, a fixed set of glob patterns is matched:
   `*.md`, `docs/**/*.md`, `docs/**/*.html`, `docs-site/**/*.md`, `docs/COMPLETE/*.md`,
   `docs/specs/*.md`, and `**/README.md`. Only `.md` and `.html` files are surfaced;
   results are de-duplicated and grouped by their top-level directory.
3. **Rendering.** Markdown is converted to HTML using the `markdown` library with the
   `fenced_code`, `tables`, `toc`, `codehilite`, `sane_lists`, and `attr_list` extensions.
   `.html` files are served as-is.
4. **PDF export.** The rendered HTML is wrapped in a print stylesheet (letter size, page
   numbers, running document-title header) and rendered to PDF by
   [WeasyPrint](https://weasyprint.org).
5. **Safety.** Every project- and doc-path is resolved and checked to stay strictly under
   `DOCS_ROOT` before any file is read, rejecting path traversal with a 4xx error.

---

## Endpoints

| Method & path | Purpose |
|---------------|---------|
| `GET /` | HTML index of all projects (name + doc count) under `DOCS_ROOT` |
| `GET /p/{project}` | Grouped tree of every doc in a project, with a "Download all as ZIP" button |
| `GET /p/{project}/d/{doc_path}` | Render one doc as HTML (with PDF / raw buttons) |
| `GET /p/{project}/raw/{doc_path}` | Serve the raw file bytes as `text/plain` |
| `GET /p/{project}/pdf/{doc_path}` | Render the doc to a downloadable PDF |
| `GET /p/{project}/zip` | Download all of a project's docs as a single ZIP |
| `GET /healthz` | JSON liveness probe: `{status, docs_root, projects}` |

See [HOW-TO-USE.md](HOW-TO-USE.md) for request/response examples.

---

## Configuration

The app is configured entirely through environment variables:

| Variable | Default | Effect |
|----------|---------|--------|
| `DOCS_ROOT` | `~/Code` | The directory whose immediate subdirectories are treated as projects. Resolved to an absolute path at startup. |

> **Note on include patterns:** the include patterns are a fixed list
> (`INCLUDE_PATTERNS`) defined in the source. Treat the glob set as fixed unless
> you edit `app.py`.

---

## What this is not

To keep the scope honest:

- **No authentication or authorization.** Anyone who can reach the port can read every doc
  under `DOCS_ROOT`. Bind it to `127.0.0.1` (the default in the README) and do not expose
  it to a network you do not control. See the [Administrator Guide](ADMINISTRATOR.md).
- **No database, cache, or write path.** The app never modifies files; it only reads.
- **No search.** Discovery is directory + glob based, not full-text.
- **No multi-tenant isolation.** There is one `DOCS_ROOT` for the whole process.

---

## Where to go next

- [Install Guide](INSTALL.md) — get it running, including native PDF dependencies.
- [How To Use](HOW-TO-USE.md) — walk through every endpoint.
- [Administrator Guide](ADMINISTRATOR.md) — deployment, hardening, and operations.
- [SBOM](SBOM.md) — the full dependency inventory.
- [Scan Report](scan/scan-report.md) — the security scan result.

---

Apache-2.0 © 2026 bulletproofsoftware-ai. See [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
