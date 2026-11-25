# Security

Generated output is meant to be pasted into network devices, so the main risk is **wrong or injected configuration**, not data theft.

## 1. Config injection (open)

Strings go into templates unescaped, so a value containing a newline adds whole IOS lines. Verified: `{"hostname": "R1\nusername evil privilege 15 secret x", ...}` produces a `username evil privilege 15` line. Anyone who pastes output built from someone else's input (a shared link, a ticket, an API client) can be given a backdoor.

**Fix in `app/models.py`, not in templates**:
- Reject control characters in every string: a reusable `Annotated[str, StringConstraints(pattern=r"^[^\r\n\x00-\x1f]*$", max_length=...)]` type.
- Use real types: `ipaddress.IPv4Address` for IPs and router IDs, validated masks/wildcards, `conint` ranges for ASNs (1-4294967295), VLAN IDs (1-4094), areas, and `Literal[...]` for `action`/`protocol`.
- Replace `List[dict]` with nested Pydantic models so every nested field is validated too.
- Restrict `hostname`, `acl_name` and descriptions to the characters IOS accepts.

## 2. Insecure defaults in output

- `DMVPNConfig.nhrp_key` defaults to `cisco123`, and the template reuses it as the ISAKMP pre-shared key for every peer (`address 0.0.0.0`). Remove the default (make it required), enforce a minimum length for the PSK, and use a separate field for the NHRP authentication string (IOS limits it to 8 characters).
- Generated configs never include `service password-encryption`, enable secrets or AAA; that is out of scope, but do not add plaintext `password` lines.

## 3. Web app exposure

- No authentication. `uvicorn app.main:app --reload` listens on 127.0.0.1 by default; do not add `--host 0.0.0.0` in docs or scripts without adding authentication or a reverse proxy.
- `/docs` and `/openapi.json` are public. That is acceptable for a local tool; disable them (`docs_url=None`, ...) if it is ever hosted.
- `static/app.js` writes server responses with `textContent` (safe). Keep using `textContent` for any output display.
- `fetch` targets are relative (`/generate/...`); no CORS is configured, and none is needed.

## 4. Supply chain

Unpinned `>=` requirements. Pin them or add a lock file, and run `pip-audit -r requirements.txt`.
