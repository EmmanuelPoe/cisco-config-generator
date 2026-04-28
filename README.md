# Cisco Config Generator

A web-based tool for generating valid Cisco IOS and NX-OS configurations from structured input. Fill out a form, get production-ready config output instantly.

## Features

- **Router Config** — generate IOS configs for interfaces, OSPF, EIGRP, BGP, ACLs
- **Switch Config** — VLAN, trunk, access port, STP, and port-security templates
- **Firewall Rules** — ASA and NX-OS ACL generation from plain-language rules
- **DMVPN Hub/Spoke** — full DMVPN Phase 2/3 config generation
- **Validation** — input validation with error highlighting before generation

## Tech Stack

- Python 3.10+
- FastAPI — REST API backend
- Jinja2 — config templating engine
- HTML/CSS/JavaScript — frontend form interface

## Project Structure

```
cisco-config-generator/
├── app/
│   ├── main.py               # FastAPI app
│   ├── routes/
│   │   └── generator.py      # Config generation endpoints
│   └── models.py             # Pydantic input models
├── templates/
│   ├── ios/
│   │   ├── router_base.j2
│   │   ├── ospf.j2
│   │   ├── bgp.j2
│   │   └── dmvpn_hub.j2
│   └── nxos/
│       ├── vlan.j2
│       └── vpc.j2
├── static/
│   ├── style.css
│   └── app.js
├── web/
│   └── index.html
└── requirements.txt
```

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# Open http://localhost:8000
```

## API Example

```bash
curl -X POST http://localhost:8000/generate/ospf \
  -H "Content-Type: application/json" \
  -d '{
    "router_id": "10.0.0.1",
    "process_id": 1,
    "networks": ["10.0.0.0/24", "192.168.1.0/24"],
    "area": 0
  }'
```
