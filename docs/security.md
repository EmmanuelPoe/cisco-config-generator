# Security

Generated output is meant to be pasted into network devices, so the main risks are **injected or wrong configuration**, then the usual web-app concerns.

## 1. Config injection (handled — keep it that way)

Templates insert values verbatim (no escaping makes sense for CLI text). Protection is entirely in `app/models.py`:

- every string field has a constrained type; `Description` and every pattern exclude `\r`, `\n` and other control characters
- addresses, masks, wildcards, ports, ASNs and VLAN IDs are parsed, not just pattern-matched
- `extra="forbid"` rejects unknown fields; nested objects are Pydantic models, not dicts
- `tests/test_generate.py::test_newlines_are_rejected_everywhere` covers each generator

Rules: never add a `str`/`dict` field without a constrained type; never build a template path or template source from input; add an injection test for any new string field.

## 2. Secrets in generated config

- `DMVPNConfig.nhrp_key` (≤ 8 chars, IOS limit) and `ipsec_psk` (16-128 chars) are required and have no defaults. The UI fields are empty with `autocomplete="off"`, and the PSK field is a password input.
- The PSK is used for `crypto isakmp key ... address 0.0.0.0 0.0.0.0` (a wildcard key shared by all DMVPN peers, standard for DMVPN). Use a long random value and rotate it per deployment; certificate-based IKEv2 is the stronger option if the template is extended.
- Generated configs are shown in the browser and returned in HTTP responses; nothing is stored server-side. Do not log request bodies.

## 3. Web app exposure

- No authentication. `uvicorn app.main:app --reload` listens on 127.0.0.1 by default; do not document `--host 0.0.0.0` without adding authentication or a reverse proxy.
- `/docs` and `/openapi.json` are public; acceptable for a local tool, disable them (`docs_url=None`, `redoc_url=None`, `openapi_url=None`) if hosted.
- `static/app.js` writes responses with `textContent`; keep using it for all output.
- Requests are same-origin; no CORS is configured or needed.

## 4. Supply chain

`requirements.txt` uses minimum versions. Pin versions for deployment and run `pip-audit -r requirements.txt` periodically.
