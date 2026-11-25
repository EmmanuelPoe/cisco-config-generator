# Testing

```bash
pip install -r requirements-dev.txt
pytest -q                                          # 36 tests, < 1 s
ruff check app tests && ruff format --check app tests
```

`pytest.ini` sets `pythonpath = .` and `testpaths = tests`. CI (`.github/workflows/ci.yml`, Python 3.11) runs ruff and pytest on every pull request and push to `main`.

## `tests/test_generate.py`

| Test | Covers |
|---|---|
| `test_index_served` | UI page |
| `test_every_generator_renders_with_defaults` | all six endpoints with minimal input |
| `test_newlines_are_rejected_everywhere` | newline/CRLF injection through hostname, descriptions, VLAN names, remarks, `apply_to`, interface lists → 422 |
| `test_invalid_values_are_rejected` | bad IPs, non-contiguous masks/wildcards, ASN 0, BGP prefixes with host bits, VLAN 4095, short PSK, long NHRP key, spoke without hub, bad ACL action/address/port/direction/name, unknown fields |
| `test_dmvpn_has_no_default_key` | secrets are required |
| `test_ospf_output`, `test_bgp_networks_use_real_masks`, `test_dmvpn_hub_and_spoke`, `test_acl_remarks_and_entries`, `test_standard_acl`, `test_vlan_trunk_allowed_list` | exact rendered lines |

## UI payloads

The browser builds payloads in `static/app.js`. When you change a model, check that the form's default values still produce valid payloads: load the page, click Generate on every tab, and confirm no `! Error` output. (During the validation rework this was also checked by running `buildPayload()` in Node against the form defaults and posting the results to the API.)

## Checking generated IOS

Paste output into a lab router (Cisco CML, GNS3, EVE-NG, or a DevNet sandbox) in config mode and watch for `% Invalid input`.
