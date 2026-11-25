# Testing

There are no tests yet. The app is easy to test in-process with FastAPI's `TestClient` (needs `httpx`):

```bash
pip install -r requirements.txt pytest httpx
pytest -q
```

Suggested `tests/test_generate.py` skeleton:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_index_served():
    assert client.get("/").status_code == 200

def test_ospf_renders_network_lines():
    r = client.post("/generate/ospf", json={
        "hostname": "R1", "router_id": "10.0.0.1",
        "networks": [{"network": "10.0.0.0", "wildcard": "0.0.0.255", "area": 0}],
    })
    assert r.status_code == 200
    assert " network 10.0.0.0 0.0.0.255 area 0" in r.text

def test_newline_injection_rejected():          # fails today: see docs/security.md
    r = client.post("/generate/ospf", json={"hostname": "R1\nusername x", "router_id": "1.1.1.1"})
    assert r.status_code == 422
```

Run from the repo root so `app` is importable and the `templates/`, `static/`, `web/` paths resolve.

## What to cover

- Each of the six endpoints with model defaults returns 200 and starts with `! ===`.
- Golden-file tests: store expected output for representative inputs under `tests/golden/` and compare exactly, so template whitespace changes are deliberate.
- Validation: invalid IPs, out-of-range ASN/VLAN/process IDs, `role` not hub/spoke, newline/control characters → 422.
- DMVPN hub vs spoke branches.

## Checking generated IOS

Paste output into a lab router (Cisco CML, GNS3, EVE-NG, or a DevNet sandbox) in config mode and watch for `% Invalid input`. `crypto profile DMVPN-PROFILE` currently fails that check.

## Lint

No config is committed; `ruff check app && ruff format --check app` works with defaults.
