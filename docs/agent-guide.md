# Agent guide

## Recipes

**Add a generator (e.g. EIGRP)**
1. `app/models.py`: `class EIGRPConfig(Strict)` using the constrained types (`Hostname`, `IPv4Address`, `Wildcard`, ...). Nested lists get their own `Strict` model.
2. `templates/ios/eigrp.j2`: start with the `! ===` banner and `hostname {{ hostname }}`; end sections with `!`.
3. `app/routes/generator.py`: `@router.post("/eigrp", response_class=PlainTextResponse)` returning `render("ios/eigrp.j2", cfg.model_dump())`; derive any computed values in Python and add them to the dict.
4. `web/index.html`: a `.tab-btn` (in order) and a `#tab-eigrp` `.tab-content` with `eigrp-*` field IDs and a `generate('eigrp')` button.
5. `static/app.js`: add `'eigrp'` to the `names` array in `switchTab` at the matching position, and a `case 'eigrp'` in `buildPayload`.
6. Tests: default render, exact lines, invalid values, newline injection. Update the README generator table.

**Add a field to an existing generator**: constrained type in the model, use it in the template, add it to the form and `buildPayload`, add a render test and a 422 test.

**Add NX-OS support**: create `templates/nxos/` and either separate endpoints (`/generate/nxos/vlan`) or a `platform: Literal["ios", "nxos"]` field that selects the template from a fixed mapping — never build the path from raw input.

## Pitfalls

- `trim_blocks`/`lstrip_blocks` are on: `{% ... %}` lines leave no blank lines or indentation, so put the indentation IOS needs (leading space for sub-commands) on the text lines.
- `StrictUndefined` is on: every variable a template uses must be in the data dict (optional fields need a default in the model).
- `model_dump()` keeps `IPv4Address`/`IPv4Network` objects, so templates can use `.network_address`, `.netmask`, `.hostmask`.
- ACL rules are a union: `AclRemark` (`action: "remark"`) is tried before `AclEntry`. Keep remark-only rules free of address fields.
- Changing template whitespace changes output; update the exact-line assertions on purpose.

## Done means

All endpoints return 200 for valid input and 422 for invalid or injected input, `pytest -q` and ruff pass, every form tab generates without errors, README matches the code.
