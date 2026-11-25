# Architecture

```
browser (web/index.html + static/app.js)
   │  POST /generate/<type>  JSON
   ▼
FastAPI (app/main.py)
   └─ APIRouter prefix=/generate (app/routes/generator.py)
        ├─ Pydantic model validates (422 on failure)        app/models.py
        └─ render("ios/<type>.j2", data)  → text/plain response
```

`app/main.py` also mounts `static/` at `/static` and returns `web/index.html` for `GET /`. FastAPI's `/docs`, `/redoc` and `/openapi.json` are enabled.

## Validation layer (`app/models.py`)

All models inherit `Strict` (`extra="forbid"`, whitespace stripped). Reusable types:

| Type | Rule |
|---|---|
| `Hostname` | `^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$` |
| `InterfaceName` | `^[A-Za-z][A-Za-z0-9/.:-]{0,63}$` (Gi0/0, GigabitEthernet1/0/24, Vlan10, Port-channel1) |
| `Description` | one line, no control characters, ≤ 200 chars |
| `ObjectName` | ACL/VLAN names: `[A-Za-z0-9_-]{1,64}` |
| `Secret` | printable ASCII, no spaces |
| `Netmask` / `Wildcard` | dotted-decimal, contiguous (validated with `ipaddress`) |
| `AclAddress` | `any`, `host A.B.C.D`, or `A.B.C.D <wildcard>` |
| `Port` | number or IOS keyword (`www`, `ssh`, ...) |
| `Asn` 1-4294967295, `VlanId` 1-4094, `OspfArea` ≥ 0, `ProcessId` 1-65535 | integer ranges |

IP addresses use `ipaddress.IPv4Address`; BGP prefixes use `IPv4Network` (host bits must be zero).

## Endpoints, models, templates

| Endpoint | Model (nested) | Template | Notes |
|---|---|---|---|
| `/generate/interface` | `InterfaceConfig` (`Interface`) | `ios/interface.j2` | at least one interface |
| `/generate/ospf` | `OSPFConfig` (`OspfNetwork`) | `ios/ospf.j2` | network + wildcard + area; passive interfaces; `default-information originate always` |
| `/generate/bgp` | `BGPConfig` (`BgpNeighbor`) | `ios/bgp.j2` | prefixes rendered as `network <addr> mask <netmask>` |
| `/generate/vlan` | `VLANConfig` (`Vlan`) | `ios/vlan.j2` | VLANs, SVIs, dot1q trunks with native and allowed VLAN list |
| `/generate/dmvpn` | `DMVPNConfig` | `ios/dmvpn.j2` | route adds `tunnel_network`/`tunnel_wildcard` derived from `tunnel_ip`/`tunnel_mask`; spoke requires `hub_public_ip` + `hub_tunnel_ip` |
| `/generate/acl` | `ACLConfig` (`AclRemark` \| `AclEntry`) | `ios/acl.j2` | remark-only rules or entries (each may carry a remark); `dst_port` only with tcp/udp; `apply_to` = `<interface> in|out` |

## Rendering

- One module-level `jinja2.Environment(FileSystemLoader("templates"), trim_blocks=True, lstrip_blocks=True, autoescape=False, undefined=StrictUndefined)`. Autoescaping is off because output is CLI text; safety comes from validation. `StrictUndefined` makes template typos fail.
- Templates are chosen by fixed name in code; user input is never compiled as a template.
- Output is `.strip()`ped; each template starts with a `! ===` banner and `hostname`.

## DMVPN template (Phase 2)

ISAKMP policy 10 (AES-256, SHA-256, DH group 14, pre-shared key `ipsec_psk` for `0.0.0.0 0.0.0.0`), transform set `esp-aes 256 esp-sha256-hmac` in transport mode, `crypto ipsec profile DMVPN-PROFILE`, `Tunnel0` mGRE with MTU 1400 / MSS 1360, NHRP authentication `nhrp_key` and network ID, hub `map multicast dynamic`, spoke static map + NHS. OSPF uses `ip ospf network broadcast`; the hub has priority 255 and spokes priority 0 so the hub is always DR. `router ospf` advertises the tunnel subnet with the wildcard derived from `tunnel_mask`.

## Dependencies

`requirements.txt`: fastapi, uvicorn[standard], jinja2, pydantic (v2), minimum versions. `requirements-dev.txt` adds pytest, httpx, ruff.
