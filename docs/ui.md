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
- `buildPayload(type)` reads fields by ID and parses textareas line by line (`parseLines`), splitting on whitespace:
  - OSPF networks: `network wildcard area`
  - BGP neighbors: `ip remote_asn description...`
  - VLANs: `id name ip mask`
  - ACL rules: `action protocol src dst [dst_port]`, or `remark <text>`
  - Interfaces: `name ip mask description...`
- `generate(type)` POSTs JSON, shows the text response, or `! Error: <detail>` for 4xx/5xx, all via `textContent`.
- `copyOutput()` uses `navigator.clipboard` (needs `localhost` or HTTPS).

## Element IDs

Per tab: `<type>-hostname` plus `ospf-rid|pid|default|networks|passive`, `bgp-asn|rid|neighbors|networks`, `vlan-native|vlans|trunks`, `dmvpn-role|tip|tmask|tsrc|nid|key|ospf|hub-pub|hub-tun`, `acl-name|type|apply|rules`, `iface-ifaces`; shared `output`, `copy-btn`.

## Conventions

- No framework or build step; plain DOM APIs and inline `onclick` handlers.
- Validation errors from Pydantic come back as JSON in `detail`; the UI prints them raw. If you add client-side checks, mirror (never replace) server-side validation.
- The grid layout does not collapse on narrow screens; add a media query if mobile matters.
