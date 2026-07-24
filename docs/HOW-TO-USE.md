# How To Use — bulletproof-docs-portal

This guide walks through every endpoint the portal exposes, both from the browser and with
`curl`. It assumes the app is running per the [Install Guide](INSTALL.md), e.g.:

```bash
DOCS_ROOT=~/Code .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8090
```

Throughout, replace `<project>` with a directory name under `DOCS_ROOT` and `<doc_path>`
with a doc's path relative to that project (e.g. `README.md` or `docs/OVERVIEW.md`).

---

## Browsing (the UI)

Open <http://localhost:8090>. You land on the **Projects index** — a card listing every
subdirectory of `DOCS_ROOT` that contains at least one matching doc, with its doc count.

1. **Click a project** → you see a tree of its docs, grouped by their top-level directory
   (for example `(root)`, `docs`, `docs-site`). Each group can be expanded/collapsed.
2. **Click a doc** → it renders as HTML, with a toolbar offering **Download PDF** and
   **View Raw**.
3. **Download all as ZIP** (button on the project view) → bundles every doc in that project
   into a single ZIP.

The header shows the active `DOCS_ROOT` so you always know what tree you are browsing.

---

## The endpoints

### `GET /` — project index

Returns an HTML page listing all projects and their doc counts.

```bash
curl -s http://localhost:8090/ | grep proj-name
```

### `GET /p/{project}` — project doc tree

Returns the grouped tree of a project's docs plus the ZIP button.

```bash
curl -s http://localhost:8090/p/bulletproof-docs-portal
```

Returns `404` if the project directory does not exist or resolves outside `DOCS_ROOT`.

### `GET /p/{project}/d/{doc_path}` — render a doc as HTML

Renders one Markdown or HTML document. Markdown is converted with fenced-code, tables,
table-of-contents, code highlighting, sane-lists, and attribute-list extensions. HTML files
are served as-is.

```bash
curl -s "http://localhost:8090/p/bulletproof-docs-portal/d/README.md"
```

### `GET /p/{project}/raw/{doc_path}` — raw file

Returns the untouched file bytes as `text/plain; charset=utf-8` — useful for copying source
Markdown.

```bash
curl -s "http://localhost:8090/p/bulletproof-docs-portal/raw/README.md"
```

### `GET /p/{project}/pdf/{doc_path}` — export a doc as PDF

Renders the doc through a print stylesheet (letter page size, page numbers in the footer,
the document title as a running header) and returns a PDF as an attachment. The download
filename is derived from the doc's stem, sanitized to `[\w.-]`.

```bash
curl -s -o overview.pdf "http://localhost:8090/p/bulletproof-docs-portal/pdf/docs/OVERVIEW.md"
file overview.pdf   # → PDF document, version 1.x
```

> Requires the native WeasyPrint libraries (Cairo/Pango) from the [Install Guide](INSTALL.md).

### `GET /p/{project}/zip` — download all project docs

Bundles every matching doc in the project into a ZIP, with each entry namespaced under the
project name.

```bash
curl -s -o project-docs.zip "http://localhost:8090/p/bulletproof-docs-portal/zip"
unzip -l project-docs.zip
```

### `GET /healthz` — liveness

Returns a small JSON object — handy for a container/process health check.

```bash
curl -s http://localhost:8090/healthz
# → {"status":"ok","docs_root":"/Users/you/Code","projects":12}
```

---

## Which files show up?

A file is listed only if **all** of the following hold:

- It is under a project (an immediate subdirectory of `DOCS_ROOT`).
- Its path matches one of the fixed include patterns: `*.md`, `docs/**/*.md`,
  `docs/**/*.html`, `docs-site/**/*.md`, `docs/COMPLETE/*.md`, `docs/specs/*.md`,
  `**/README.md`.
- Its extension is `.md` or `.html`.
- No path component is an excluded directory (`.git`, `node_modules`, `.venv`, `venv`,
  `__pycache__`, `.pytest_cache`, `dist`, `build`).

If a doc you expect is missing, check it against these rules first. Nested Markdown that
does not live under `docs/`, `docs-site/`, or match `**/README.md` will not appear.

---

## Security note when using it

There is **no authentication**. Every doc under `DOCS_ROOT` is readable by anyone who can
reach the port. The path-traversal guard prevents escaping `DOCS_ROOT`, but it does not
restrict *which* docs inside the root a caller may read. Keep the bind address on
`127.0.0.1` for personal use; see the [Administrator Guide](ADMINISTRATOR.md) before
exposing it to anyone else.

---

Apache-2.0 © 2026 bulletproofsoftware-ai. See [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
