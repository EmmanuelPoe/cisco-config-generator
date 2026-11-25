# Architecture

```
browser (web/index.html + static/app.js)
   │  POST /generate/<type>  JSON
   ▼
FastAPI (app/main.py)
   └─ APIRouter prefix=/generate (app/routes/generator.py)
        ├─ Pydantic model validates/fills defaults   (app/models.py)
        └─ render("ios/<type>.j2", model.model_dump())  → text/plain response
```

`app/main.py` also mounts `static/` at `/static` and returns `web/index.html` for `GET /`. FastAPI's `/docs`, `/redoc` and `/openapi.json` are enabled (default).

## Endpoints, models, templates

| Endpoint | Model | Template | Key inputs |
|---|---|---|---|
| `/generate/interface` | `InterfaceConfig` | `ios/interface.j2` | `hostname`, `interfaces: [ {name, ip, mask, description} ]` |
| `/generate/ospf` | `OSPFConfig` | `ios/ospf.j2` | `router_id`, `process_id` (1-65535), `networks: [ {network, wildcard, area} ]`, `passive_interfaces`, `default_route` |
| `/generate/bgp` | `BGPConfig` | `ios/bgp.j2` | `local_asn`, `router_id`, `neighbors: [ {ip, remote_asn, description} ]`, `networks` |
| `/generate/vlan` | `VLANConfig` | `ios/vlan.j2` | `vlans: [ {id, name, ip, mask} ]`, `trunk_ports`, `native_vlan` |
| `/generate/dmvpn` | `DMVPNConfig` | `ios/dmvpn.j2` | `role` (`hub`/`spoke`), `tunnel_ip`, `tunnel_mask`, `tunnel_source`, `nhrp_network_id`, `nhrp_key`, `hub_public_ip`/`hub_tunnel_ip` (spoke), `ospf_process` |
| `/generate/acl` | `ACLConfig` | `ios/acl.j2` | `acl_name`, `acl_type` (`standard`/`extended`), `rules: [ {action, protocol, src, dst, dst_port, remark} ]`, `apply_to` |

Every model has `hostname: str`, and most list fields are `List[dict]` with example defaults, so the nested objects are not validated at all.

## Rendering

- One module-level `jinja2.Environment(FileSystemLoader("templates"), trim_blocks=True, lstrip_blocks=True)`. Autoescaping is off (correct for CLI text, but see security.md).
- Templates are loaded by fixed name from code; user input never chooses a template or is compiled as a template, so there is no server-side template injection.
- Output is `.strip()`ped and returned as `PlainTextResponse`.
- Each template starts with a `! ===` banner and `hostname {{ hostname }}`.

## Template notes

- `dmvpn.j2`: ISAKMP policy (AES-256, SHA-256, group 14), PSK = `nhrp_key` for `0.0.0.0`, transform set in transport mode, mGRE `Tunnel0`, OSPF over the tunnel. Hub advertises `tunnel_ip 0.0.0.255 area 0` (hard-coded /24 wildcard). See known issues in CLAUDE.md.

## Dependencies

`requirements.txt`: fastapi, uvicorn[standard], jinja2, pydantic (v2 — models use `pattern=` and `model_dump()`), all unpinned minimums.
