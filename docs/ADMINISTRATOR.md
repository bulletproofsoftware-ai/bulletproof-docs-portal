# Administrator Guide — bulletproof-docs-portal

This guide covers running `bulletproof-docs-portal` beyond a single local session:
configuration, process management, hardening, and operations. The app is deliberately
tiny — one FastAPI file, no database, no writes — so "administration" is mostly about
**where you point it** and **who can reach it**.

---

## Configuration surface

| Variable | Default | Effect |
|----------|---------|--------|
| `DOCS_ROOT` | `~/Code` | Absolute directory whose immediate subdirectories are the "projects". Resolved once at startup. |

Everything else — the include glob patterns (`INCLUDE_PATTERNS`), the excluded directory
set (`EXCLUDE_DIRS`), the on-screen and print CSS — is defined in `app.py`. There is no
config file. To change discovery behavior you edit the source.

---

## Running as a managed process

Run it under any ASGI-capable supervisor. Uvicorn is the reference server.

**systemd (Linux):**

```ini
# /etc/systemd/system/docs-portal.service
[Unit]
Description=bulletproof-docs-portal
After=network.target

[Service]
Type=simple
User=docs
WorkingDirectory=/opt/bulletproof-docs-portal
Environment=DOCS_ROOT=/srv/projects
ExecStart=/opt/bulletproof-docs-portal/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8090
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now docs-portal
curl -s http://127.0.0.1:8090/healthz
```

**launchd (macOS):** wrap the same `uvicorn` invocation in a user LaunchAgent plist with
`KeepAlive` set.

For more than a handful of concurrent readers, run several workers behind Uvicorn
(`--workers N`) — the app is stateless, so workers need no coordination.

---

## Hardening — read before exposing it

The app has **no authentication, authorization, or rate limiting**. Its threat model is
"a trusted local user browsing their own docs." Treat these as required controls before it
is reachable by anyone else:

1. **Keep the bind address local.** The README and all examples use `--host 127.0.0.1`.
   Do not bind `0.0.0.0` on an untrusted network.
2. **Front it with a reverse proxy that adds auth.** If remote access is needed, put nginx
   / Caddy / an identity-aware proxy in front and enforce authentication there. The app
   itself will authenticate no one.
3. **Constrain `DOCS_ROOT` to exactly what should be shared.** Every `.md`/`.html` under
   the root that matches the include patterns is world-readable to anyone who reaches the
   port. Point it at a curated docs tree, not your entire home directory, if the audience
   is broader than yourself. Note the default is `~/Code`.
4. **Run as an unprivileged user** with read-only access to `DOCS_ROOT`. The app never
   writes, so it needs no write permission anywhere.
5. **Path traversal is already handled** in code: both the project name and the doc path
   are resolved with `Path.resolve()` and rejected unless they remain strictly under
   `DOCS_ROOT` (`_safe_path` and the project-view guard). This blocks `../` escapes; it
   does **not** implement per-doc access control.

### PDF export and SSRF

WeasyPrint fetches resources referenced by the HTML it renders. Historically this enabled
SSRF; **`weasyprint` is pinned to 68.0+**, which includes the fix for
[CVE-2025-68616](https://nvd.nist.gov/vuln/detail/CVE-2025-68616) (SSRF protection bypass via HTTP
redirect). Keep the pin at 68.0 or newer. If you render docs from untrusted sources, be
aware that PDF generation dereferences their `img`/`link` URLs; render only docs you trust,
or run the process without outbound network access.

---

## Operations

### Health checks

```bash
curl -s http://127.0.0.1:8090/healthz
# {"status":"ok","docs_root":"/srv/projects","projects":9}
```

Use this as your liveness/readiness probe. A non-200 or a connection error means the
process is down; `projects: 0` usually means `DOCS_ROOT` is misconfigured or empty.

### Logs

Uvicorn logs to stdout/stderr — capture them via your supervisor (`journalctl -u
docs-portal` under systemd). There is no application log file.

### Resource profile

- **CPU/RAM:** negligible at idle. PDF rendering is the only meaningful cost — WeasyPrint
  parses HTML and lays out pages per request. Large docs or bursts of PDF requests are the
  scaling concern; add workers or a small queue in front if you see contention.
- **Disk:** none written by the app. Doc size is bounded by whatever is under `DOCS_ROOT`.
- **State:** none. Restarting the process loses nothing; discovery re-runs on each request.

### Upgrades

```bash
git pull
.venv/bin/pip install -r requirements.txt   # re-installs pinned versions
sudo systemctl restart docs-portal
```

Review [requirements.txt](../requirements.txt) and the [SBOM](SBOM.md) after any dependency
bump, and re-run a scan (see [scan/scan-report.md](scan/scan-report.md)) if you change deps.

---

## Backup / disaster recovery

There is nothing to back up inside the app — it is stateless. Your source of truth is the
`DOCS_ROOT` tree (back that up with your normal file backups) and this repository. Recovery
is: reinstall (see [INSTALL.md](INSTALL.md)) and re-point `DOCS_ROOT`.

---

Apache-2.0 © 2026 bulletproofsoftware-ai. See [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
