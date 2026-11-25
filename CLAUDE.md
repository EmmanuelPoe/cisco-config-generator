# CLAUDE.md

Guidance for AI agents working in this repository. Read this first, then the matching file in `docs/`.

## What this is

A FastAPI app that renders Cisco IOS configuration snippets from JSON input using Jinja2 templates, plus a single-page form UI. Six generators, each a `POST /generate/<type>` endpoint returning `text/plain`: `interface`, `ospf`, `bgp`, `vlan`, `dmvpn`, `acl`. All templates are IOS (`templates/ios/`); there are no NX-OS or ASA templates.

**The README overstates the repo**: EIGRP, STP/port-security, ASA/NX-OS firewall rules, `router_base.j2`, `dmvpn_hub.j2`, `templates/nxos/` and "input validation with error highlighting" do not exist. Output is not "production-ready" — see the known issues below.

## Commands

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload            # http://localhost:8000 (UI), /docs (OpenAPI)
curl -X POST localhost:8000/generate/ospf -H 'Content-Type: application/json' \
  -d '{"hostname":"R1","router_id":"10.0.0.1","networks":[{"network":"10.0.0.0","wildcard":"0.0.0.255","area":0}]}'
```

Note: the README's curl example sends `networks` as CIDR strings and `area` at the top level; the real `OSPFConfig` model wants a list of `{network, wildcard, area}` objects.

No tests, linter config or CI exist yet.

## Layout

```
app/main.py              FastAPI app: mounts /static, includes router, serves web/index.html at /
app/routes/generator.py  Jinja2 Environment (trim_blocks, lstrip_blocks) + the six POST endpoints
app/models.py            Pydantic v2 request models (one per generator)
templates/ios/*.j2       acl, bgp, dmvpn, interface, ospf, vlan
web/index.html           the form UI (sidebar tabs, editor pane, output pane)
static/app.js            builds JSON payloads from form fields, calls /generate/<type>, shows/copies output
static/style.css         dark GitHub-style theme
```

## Known issues — read before changing templates or models

1. **Config injection**: string fields are inserted into templates raw. A newline in any field (e.g. `hostname`) adds arbitrary IOS lines to the output — verified with `"hostname": "R1\nusername evil privilege 15 secret x"`. See [docs/security.md](docs/security.md).
2. **No semantic validation**: IPs, masks, wildcards, interface names and ACL fields are plain `str`/`dict`; `"router_id": "not-an-ip"` returns 200.
3. **DMVPN template**: `crypto profile DMVPN-PROFILE` is not a valid IOS command (should be `crypto ipsec profile`); the header says IKEv2 but it configures ISAKMP (IKEv1); the NHRP key doubles as the IPsec pre-shared key, defaults to `cisco123`, and is applied with `address 0.0.0.0`.

## Rules for agents

- Every new or changed input field must be validated in `app/models.py` (types, regex, `ipaddress`) so nothing with newlines or control characters reaches a template.
- One endpoint, one model, one template per config type; keep that 1:1 mapping.
- Never put real credentials, keys or customer configs in templates, model defaults or examples.
- Keep the README in sync with what is actually implemented.

## Docs

- [docs/architecture.md](docs/architecture.md)
- [docs/security.md](docs/security.md)
- [docs/ui.md](docs/ui.md)
- [docs/testing.md](docs/testing.md)
- [docs/agent-guide.md](docs/agent-guide.md)
