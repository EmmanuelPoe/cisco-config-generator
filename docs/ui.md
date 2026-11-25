# UI

## Layout (`web/index.html` + `static/style.css`)

Full-height, three-column grid under a header:

| Column | Width | Content |
|---|---|---|
| `.sidebar` | 160px | "Generators" label + `.tab-btn` buttons: OSPF, BGP, VLAN, DMVPN, ACL, Interface |
| `.editor-pane` | 1fr | one `.tab-content` per generator (`#tab-ospf` ... `#tab-interface`), each a `.form-grid` of `.field`s, textareas for list input, and a green `.generate-btn` |
| `.output-pane` | 1fr | header with a Copy button (`#copy-btn`) and `<pre id="output">` |

Theme: GitHub-dark palette — background `#0d1117`, panels `#161b22`, borders `#30363d`, text `#c9d1d9`, accent `#58a6ff`, generate button `#238636`. Monospace textareas and output.

## Behavior (`static/app.js`)

- `switchTab(name)` relies on the **order** of `.tab-btn` elements matching `['ospf','bgp','vlan','dmvpn','acl','interface']`. Adding a tab means adding to that array in the same position.
- `toggleDMVPNRole()` shows `#dmvpn-spoke-fields` only for role `spoke`.
- `buildPayload(type)` reads fields by ID and parses textareas line by line (`parseLines`):
  - OSPF networks: `network wildcard area`
  - BGP neighbors: `ip remote_asn description...`; BGP networks: one CIDR per line
  - VLANs: `id name ip mask`
  - ACL rules: `remark <text>`, or `action protocol src dst [port]` (extended) / `action src` (standard), where an address is `any`, `host A.B.C.D` or `A.B.C.D <wildcard>`
  - Interfaces: `name ip mask description...`
- `generate(type)` POSTs JSON and shows the text response, or `! Error: <detail>` (the Pydantic validation details) for 4xx/5xx, via `textContent`.
- `copyOutput()` uses `navigator.clipboard` (needs `localhost` or HTTPS).

## Element IDs

Per tab: `<type>-hostname` plus `ospf-rid|pid|default|networks|passive`, `bgp-asn|rid|neighbors|networks`, `vlan-native|vlans|trunks`, `dmvpn-role|tip|tmask|tsrc|nid|key|psk|ospf|hub-pub|hub-tun`, `acl-name|type|apply|rules`, `iface-ifaces`; shared `output`, `copy-btn`.

## Conventions

- No framework or build step; plain DOM APIs and inline `onclick` handlers.
- Secret fields (`dmvpn-key`, `dmvpn-psk`) start empty with `autocomplete="off"`; never pre-fill them.
- Server-side validation is the source of truth; client-side hints (`maxlength`, `minlength`, placeholders) are conveniences only.
- The grid layout does not collapse on narrow screens; add a media query if mobile matters.
