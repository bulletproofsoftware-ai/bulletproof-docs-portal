"""
docs-portal — minimal HTML+PDF browser for project documentation.

Walks a configured root directory, lists markdown files per project, renders
them to HTML, and offers a PDF download for any document.

Run:
    pip install -r requirements.txt
    uvicorn app:app --host 127.0.0.1 --port 8090

Configure via env:
    DOCS_ROOT — directory to scan (default: ~/Code)
"""

from __future__ import annotations

import hmac
import html
import io
import os
import re
import zipfile
from pathlib import Path

import markdown as md_lib
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from weasyprint import HTML

DOCS_ROOT = Path(os.environ.get("DOCS_ROOT", str(Path.home() / "Code"))).resolve()
INCLUDE_PATTERNS = [
    "*.md",
    "docs/**/*.md",
    "docs/**/*.html",
    "docs-site/**/*.md",
    "docs/COMPLETE/*.md",
    "docs/specs/*.md",
    "**/README.md",
]
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build"}

app = FastAPI(title="Docs Portal", description="Browse and PDF-export project documentation")

# Shared-secret gate.
#
# Every route below serves file contents from DOCS_ROOT, which defaults to the
# operator's entire ~/Code directory. Without this the portal browsed, and let
# anyone download or zip, whatever happened to be under that root.
#
# Send the token as `Authorization: Bearer <token>` or `X-Docs-Token`.
# Unset token => the service refuses everything (fail closed) rather than
# serving the filesystem to anyone who can reach the port.
DOCS_PORTAL_TOKEN = os.environ.get("DOCS_PORTAL_TOKEN", "")
_PUBLIC_PATHS = {"/healthz"}


@app.middleware("http")
async def require_token(request: Request, call_next):
    if request.url.path in _PUBLIC_PATHS:
        return await call_next(request)

    if not DOCS_PORTAL_TOKEN:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "DOCS_PORTAL_TOKEN is not set; the portal refuses "
                          "requests until it is configured."
            },
        )

    header = request.headers.get("authorization", "")
    presented = (
        header[7:] if header.lower().startswith("bearer ") else ""
    ) or request.headers.get("x-docs-token", "")

    # Constant-time compare so the token cannot be recovered from timing.
    if not presented or not hmac.compare_digest(presented, DOCS_PORTAL_TOKEN):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    return await call_next(request)


_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _validate_segments(value: str, *, allow_slash: bool) -> str:
    """Reject anything that is not a plain relative path of safe segments.

    Containment checks alone are correct but invisible to dataflow analysis, and
    they are also the last line rather than the first. Rejecting the input shape
    up front means a traversal attempt never reaches a filesystem call at all
    (CodeQL py/path-injection).
    """
    if not value or "\x00" in value:
        raise HTTPException(status_code=400, detail="invalid path")
    if value.startswith("/") or value.startswith("\\"):
        raise HTTPException(status_code=400, detail="invalid path")
    parts = value.split("/") if allow_slash else [value]
    for part in parts:
        if not _SEGMENT_RE.match(part) or part == ".." or part == ".":
            raise HTTPException(status_code=400, detail="invalid path")
    return "/".join(parts)


def _safe_project_dir(project: str) -> Path:
    """Validated, contained project directory."""
    project = _validate_segments(project, allow_slash=False)
    project_dir = (DOCS_ROOT / project).resolve()
    if DOCS_ROOT not in project_dir.parents and project_dir != DOCS_ROOT:
        raise HTTPException(status_code=400, detail="invalid project")
    if not project_dir.is_dir():
        raise HTTPException(status_code=404, detail="project not found")
    return project_dir


def _safe_path(project: str, doc_path: str) -> Path:
    """Resolve project + doc_path under DOCS_ROOT, refusing traversal."""
    doc_path = _validate_segments(doc_path, allow_slash=True)
    project_dir = _safe_project_dir(project)
    full = (project_dir / doc_path).resolve()
    if project_dir not in full.parents and full != project_dir:
        raise HTTPException(status_code=400, detail="path traversal")
    if not full.is_file():
        raise HTTPException(status_code=404, detail="doc not found")
    return full


def _list_projects() -> list[dict]:
    items: list[dict] = []
    for entry in sorted(DOCS_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith(".") or entry.name in EXCLUDE_DIRS:
            continue
        doc_count = sum(1 for _ in _list_docs_in(entry))
        if doc_count == 0:
            continue
        items.append({"name": entry.name, "doc_count": doc_count})
    return items


def _list_docs_in(project_dir: Path):
    """Yield (relative_path, abs_path) for every markdown/html doc."""
    seen: set[Path] = set()
    for pattern in INCLUDE_PATTERNS:
        for f in project_dir.glob(pattern):
            if not f.is_file():
                continue
            if any(part in EXCLUDE_DIRS for part in f.parts):
                continue
            if f.suffix.lower() not in (".md", ".html"):
                continue
            if f in seen:
                continue
            seen.add(f)
            yield (f.relative_to(project_dir), f)


def _render_markdown(text: str) -> str:
    return md_lib.markdown(
        text,
        extensions=["fenced_code", "tables", "toc", "codehilite", "sane_lists", "attr_list"],
    )


PAGE_CSS = """
* { box-sizing: border-box; }
body { font: 15px/1.6 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       margin: 0; background: #f7f8fa; color: #1f2937; }
header { background: #1f2937; color: #fff; padding: 1rem 1.5rem; display: flex;
         align-items: center; justify-content: space-between; }
header a { color: #fff; text-decoration: none; }
header h1 { margin: 0; font-size: 1.1rem; }
.container { max-width: 1100px; margin: 0 auto; padding: 1.5rem; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 6px;
        padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
ul { padding-left: 1.25rem; }
li { margin: .25rem 0; }
.proj-link { display: block; padding: .75rem 1rem; border: 1px solid #e5e7eb;
             border-radius: 4px; margin-bottom: .5rem; background: #fff; text-decoration: none;
             color: #1f2937; }
.proj-link:hover { background: #f3f4f6; }
.proj-name { font-weight: 600; }
.proj-meta { color: #6b7280; font-size: .85em; margin-left: .5rem; }
.btn { display: inline-block; padding: .4rem .9rem; border-radius: 4px;
       background: #2563eb; color: #fff; text-decoration: none; font-size: .9em;
       border: none; cursor: pointer; }
.btn:hover { background: #1d4ed8; }
.btn-secondary { background: #6b7280; }
.btn-secondary:hover { background: #4b5563; }
.toolbar { display: flex; gap: .5rem; margin-bottom: 1rem; align-items: center; flex-wrap: wrap; }
.crumbs { color: #6b7280; font-size: .9em; margin-bottom: 1rem; }
.crumbs a { color: #2563eb; text-decoration: none; }
pre { background: #1f2937; color: #f9fafb; padding: 1rem; border-radius: 4px;
      overflow-x: auto; font-size: .9em; }
code { background: #f3f4f6; padding: .1em .35em; border-radius: 3px;
       font-family: 'SF Mono', Menlo, monospace; font-size: .9em; }
pre code { background: transparent; padding: 0; color: inherit; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
th, td { border: 1px solid #e5e7eb; padding: .5em .75em; text-align: left; }
th { background: #f3f4f6; }
blockquote { border-left: 4px solid #d1d5db; padding-left: 1em;
             color: #4b5563; margin: 1em 0; }
h1, h2, h3, h4 { line-height: 1.3; }
.tree { list-style: none; padding-left: 0; }
.tree details { margin: .25em 0; }
.tree summary { cursor: pointer; padding: .25em .5em; border-radius: 3px; }
.tree summary:hover { background: #f3f4f6; }
.tree a { color: #2563eb; text-decoration: none; padding: .15em .5em; display: block;
          border-radius: 3px; }
.tree a:hover { background: #eff6ff; }
"""

PRINT_CSS = """
@page { size: letter; margin: 1in; @bottom-right { content: counter(page) " / " counter(pages); }
       @top-left { content: string(doc-title); font-size: 9pt; color: #6b7280; } }
body { font: 11pt/1.5 'Helvetica', sans-serif; color: #111; }
h1 { string-set: doc-title content(); border-bottom: 2px solid #333; padding-bottom: .3em; }
h1, h2, h3 { color: #1f2937; }
pre { background: #f3f4f6; padding: .8em; border-radius: 3px; font-size: 9pt;
      white-space: pre-wrap; word-wrap: break-word; border: 1px solid #d1d5db; }
code { font-family: 'Courier New', monospace; font-size: 9pt; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #999; padding: .4em; }
th { background: #e5e7eb; }
blockquote { border-left: 3px solid #999; padding-left: 1em; color: #555; }
"""


def _page(title: str, body: str, crumbs: str = "") -> str:
    # `title` is caller-supplied text (usually a project name straight off the
    # URL) and lands inside an element, so it must be escaped. `body` and
    # `crumbs` are deliberately HTML and are escaped by their callers.
    safe_title = html.escape(title, quote=True)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title} — Docs Portal</title>
<style>{PAGE_CSS}</style>
</head><body>
<header><h1><a href="/">📚 Docs Portal</a></h1>
<small style="opacity:.7">root: {DOCS_ROOT}</small></header>
<div class="container">
{crumbs}
{body}
</div></body></html>"""


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    projects = _list_projects()
    items = "\n".join(
        f'<a class="proj-link" href="/p/{p["name"]}">'
        f'<span class="proj-name">{p["name"]}</span>'
        f'<span class="proj-meta">{p["doc_count"]} docs</span></a>'
        for p in projects
    ) or '<p style="color:#6b7280">No projects with documentation found.</p>'
    body = f'<div class="card"><h2>Projects ({len(projects)})</h2>{items}</div>'
    return _page("Projects", body)


@app.get("/p/{project}", response_class=HTMLResponse)
async def project_view(project: str) -> str:
    project_dir = _safe_project_dir(project)
    docs = sorted(_list_docs_in(project_dir), key=lambda x: str(x[0]))
    if not docs:
        body = '<div class="card"><p>No documentation files in this project.</p></div>'
        return _page(project, body, f'<div class="crumbs"><a href="/">📚 Projects</a> / {html.escape(project, quote=True)}</div>')

    # Group by top-level directory
    grouped: dict[str, list[Path]] = {}
    for rel, _abs in docs:
        rel_str = str(rel)
        top = rel_str.split("/")[0] if "/" in rel_str else "(root)"
        grouped.setdefault(top, []).append(rel)

    items_html: list[str] = []
    for group in sorted(grouped.keys()):
        entries = sorted(grouped[group], key=str)
        links = "\n".join(
            f'<a href="/p/{project}/d/{rel}">{rel.name}</a>' for rel in entries
        )
        items_html.append(
            f'<details open><summary><strong>{group}/</strong> ({len(entries)})</summary>'
            f'<div style="margin-left:1em">{links}</div></details>'
        )
    tree = '<ul class="tree">' + "".join(items_html) + "</ul>"

    toolbar = (
        f'<div class="toolbar">'
        f'<a class="btn btn-secondary" href="/p/{project}/zip">⬇ Download All as ZIP</a>'
        f'<span style="color:#6b7280">{len(docs)} document(s)</span></div>'
    )
    body = f'<div class="card">{toolbar}{tree}</div>'
    crumbs = f'<div class="crumbs"><a href="/">📚 Projects</a> / {html.escape(project, quote=True)}</div>'
    return _page(project, body, crumbs)


@app.get("/p/{project}/d/{doc_path:path}", response_class=HTMLResponse)
async def doc_view(project: str, doc_path: str) -> str:
    full = _safe_path(project, doc_path)
    text = full.read_text(encoding="utf-8", errors="replace")
    if full.suffix.lower() == ".md":
        rendered = _render_markdown(text)
    else:  # .html
        rendered = text
    # project and doc_path come from the URL and are interpolated into HTML,
    # so they must be escaped: a path containing a quote or angle bracket
    # otherwise breaks out of the attribute and injects markup into the page.
    e_project = html.escape(project, quote=True)
    e_doc_path = html.escape(doc_path, quote=True)
    toolbar = (
        f'<div class="toolbar">'
        f'<a class="btn" href="/p/{e_project}/pdf/{e_doc_path}">⬇ Download PDF</a>'
        f'<a class="btn btn-secondary" href="/p/{e_project}/raw/{e_doc_path}">View Raw</a>'
        f'</div>'
    )
    body = f'<div class="card">{toolbar}<div class="content">{rendered}</div></div>'
    crumbs = (
        f'<div class="crumbs"><a href="/">📚 Projects</a> / '
        f'<a href="/p/{e_project}">{e_project}</a> / {e_doc_path}</div>'
    )
    return _page(full.name, body, crumbs)


@app.get("/p/{project}/raw/{doc_path:path}")
async def doc_raw(project: str, doc_path: str) -> Response:
    full = _safe_path(project, doc_path)
    return Response(content=full.read_bytes(), media_type="text/plain; charset=utf-8")


@app.get("/p/{project}/pdf/{doc_path:path}")
async def doc_pdf(project: str, doc_path: str) -> Response:
    full = _safe_path(project, doc_path)
    text = full.read_text(encoding="utf-8", errors="replace")
    if full.suffix.lower() == ".md":
        rendered = _render_markdown(text)
    else:
        rendered = text
    pdf_html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>{full.name}</title>
<style>{PRINT_CSS}</style></head>
<body><h1>{full.name}</h1>
<p style="color:#6b7280;font-size:9pt;border-bottom:1px solid #ccc;padding-bottom:.5em;">
Project: {project} · Path: {doc_path} · Generated by docs-portal
</p>
{rendered}
</body></html>"""
    pdf_bytes = HTML(string=pdf_html).write_pdf()
    safe_name = re.sub(r"[^\w.-]+", "_", full.stem) + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@app.get("/p/{project}/zip")
async def project_zip(project: str) -> Response:
    project_dir = _safe_project_dir(project)
    docs = list(_list_docs_in(project_dir))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        resolved_project = project_dir.resolve()
        for rel, abs_path in docs:
            # Skip anything that resolves outside the project: a symlinked doc
            # would otherwise be followed and its target packaged into the zip.
            try:
                if resolved_project not in Path(abs_path).resolve().parents:
                    continue
            except OSError:
                continue
            zf.write(abs_path, arcname=f"{project}/{rel}")
    buf.seek(0)
    safe_name = re.sub(r"[^\w.-]+", "_", project) + "-docs.zip"
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "docs_root": str(DOCS_ROOT), "projects": len(_list_projects())}
