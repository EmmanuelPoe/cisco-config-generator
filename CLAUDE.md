# CLAUDE.md

Guidance for AI agents working in this repository. Read this first, then the matching file in `docs/`.

## What this is

A FastAPI app that renders Cisco IOS configuration snippets from JSON input using Jinja2 templates, plus a single-page form UI. Six generators, each a `POST /generate/<type>` endpoint returning `text/plain`: `interface`, `ospf`, `bgp`, `vlan`, `dmvpn`, `acl`. All templates are IOS (`templates/ios/`).

The core safety property: **every input is validated in `app/models.py` before it reaches a template**, and no string may contain a newline or control character. Output is pasted into devices line by line, so an unvalidated newline would let a field inject arbitrary commands.

## Commands

```bash
pip install -r requirements-dev.txt     # runtime + pytest, httpx, ruff
uvicorn app.main:app --reload           # http://localhost:8000 (UI), /docs (OpenAPI)
pytest -q                               # 36 tests
ruff check app tests && ruff format --check app tests
```

CI (`.github/workflows/ci.yml`) runs ruff and pytest on every pull request.

## Layout

```
app/main.py              FastAPI app: mounts /static, includes router, serves web/index.html at /
app/routes/generator.py  Jinja2 Environment (trim/lstrip blocks, StrictUndefined, no autoescape) + six endpoints
app/models.py            Pydantic v2 models; constrained types (Hostname, InterfaceName, Description, Netmask, Wildcard, AclAddress, ...)
templates/ios/*.j2       acl, bgp, dmvpn, interface, ospf, vlan
web/index.html           the form UI
static/app.js            builds JSON payloads from form fields, calls /generate/<type>, shows/copies output
tests/test_generate.py   rendering, validation and injection tests
pytest.ini, ruff.toml    test path and lint settings
```

## Rules for agents

- Any new field gets a constrained type from `app/models.py` (or a new one there). Never use bare `str`, `dict` or `List[dict]`. Models use `extra="forbid"`.
- One endpoint, one model, one template per config type.
- Templates only format; computed values (e.g. DMVPN tunnel network/wildcard) are derived in Python and passed in.
- Secrets (`nhrp_key`, `ipsec_psk`) have no defaults and must not get example values in the UI or docs.
- Add tests for rendering, validation failures (422) and newline injection with every change.
- Keep the README generator table and `static/app.js` payload builders in sync with the models.

## Docs

- [docs/architecture.md](docs/architecture.md)
- [docs/security.md](docs/security.md)
- [docs/ui.md](docs/ui.md)
- [docs/testing.md](docs/testing.md)
- [docs/agent-guide.md](docs/agent-guide.md)
