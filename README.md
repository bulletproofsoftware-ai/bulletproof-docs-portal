# Docs Portal

Minimal local web app to browse and PDF-export project documentation
across all your projects in `your projects directory (set DOCS_ROOT)`.

## What it does

- Walks `your projects directory (set DOCS_ROOT)` (configurable) and lists every project that has docs
- For each project, shows a tree of all `.md` and `.html` files
- Click a doc → renders as HTML in your browser
- "Download PDF" button on every page
- "Download all as ZIP" per project
- No auth, no database, no compliance service. One process.

## Run

```bash
cd bulletproof-docs-portal
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8090
```

Open http://localhost:8090

## Configure

```bash
DOCS_ROOT=/path/to/projects .venv/bin/uvicorn app:app --port 8090
```

## Native deps for PDF export

WeasyPrint needs Cairo + Pango. On macOS:

```bash
brew install cairo pango gdk-pixbuf libffi
```

On Debian/Ubuntu:

```bash
sudo apt-get install libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf-2.0-0
```

## License

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE).
