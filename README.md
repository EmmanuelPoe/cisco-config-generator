# Cisco Config Generator

A web tool that generates Cisco IOS configuration snippets from structured input. Fill out a form (or call the API), get config you can review and paste into a device.

## Generators

| Generator | Endpoint | Produces |
|---|---|---|
| Interfaces | `POST /generate/interface` | routed interfaces with IP, mask, description |
| OSPF | `POST /generate/ospf` | `router ospf` with networks/areas, passive interfaces, default route origination |
| BGP | `POST /generate/bgp` | `router bgp` with neighbors and advertised prefixes (CIDR in, `network … mask …` out) |
| VLAN / SVI | `POST /generate/vlan` | VLANs, SVIs, 802.1Q trunks with native and allowed VLANs |
| DMVPN Phase 2 | `POST /generate/dmvpn` | hub or spoke: IKEv1/IPsec transport profile, mGRE tunnel, NHRP, OSPF (hub as DR) |
| ACL | `POST /generate/acl` | standard or extended named ACLs with remarks, optional interface binding |

Every input is validated before rendering (IP addresses, masks, wildcards, ASNs, VLAN IDs, interface names, ports), and no field may contain a newline or control character, so one field cannot inject extra configuration lines. Invalid input returns HTTP 422 with the reason.

## Tech stack

Python 3.10+, FastAPI, Pydantic v2, Jinja2; HTML/CSS/vanilla JavaScript frontend.

## Project structure

```
cisco-config-generator/
├── app/
│   ├── main.py               # FastAPI app; serves the UI and static files
│   ├── models.py             # Pydantic request models and validation
│   └── routes/generator.py   # /generate/* endpoints
├── templates/ios/            # acl, bgp, dmvpn, interface, ospf, vlan (.j2)
├── static/                   # app.js, style.css
├── web/index.html            # the form UI
├── tests/test_generate.py
├── requirements.txt / requirements-dev.txt
└── pytest.ini, ruff.toml
```

## Quick start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# UI:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

## API example

```bash
curl -X POST http://localhost:8000/generate/ospf \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "CORE-RTR-01",
    "router_id": "10.0.0.1",
    "process_id": 1,
    "networks": [{"network": "10.0.0.0", "wildcard": "0.0.0.255", "area": 0}],
    "passive_interfaces": ["GigabitEthernet0/1"]
  }'
```

DMVPN requires two secrets with no defaults: `nhrp_key` (NHRP authentication, up to 8 characters) and `ipsec_psk` (IKE pre-shared key, 16+ characters). ACL addresses are `any`, `host A.B.C.D`, or `A.B.C.D <wildcard>`.

## Development

```bash
pip install -r requirements-dev.txt
ruff check app tests && ruff format --check app tests
pytest -q
```

CI runs the same checks on every pull request.

## Roadmap

EIGRP, STP/port-security, NX-OS and ASA templates.

Always review generated configuration before applying it to a device.

Agent and contributor docs: [CLAUDE.md](CLAUDE.md) and [docs/](docs/).
