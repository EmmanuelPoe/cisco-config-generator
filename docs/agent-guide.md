# Agent guide

## Recipes

**Add a generator (e.g. EIGRP)**
1. `app/models.py`: `class EIGRPConfig(BaseModel)` with validated fields (see security.md) — no bare `str` or `dict` for network values.
2. `templates/ios/eigrp.j2`: start with the `! ===` banner and `hostname {{ hostname }}`; end sections with `!`.
3. `app/routes/generator.py`: `@router.post("/eigrp", response_class=PlainTextResponse)` returning `render("ios/eigrp.j2", cfg.model_dump())`.
4. `web/index.html`: a `.tab-btn` (in order) and a `#tab-eigrp` `.tab-content` with `eigrp-*` field IDs and a `generate('eigrp')` button.
5. `static/app.js`: add `'eigrp'` to the `names` array in `switchTab` at the matching position, and a `case 'eigrp'` in `buildPayload`.
6. Tests for the endpoint, plus README and docs.

**Add NX-OS support**: create `templates/nxos/`, and either separate endpoints (`/generate/nxos/vlan`) or a `platform: Literal["ios","nxos"]` field that chooses the template path from a fixed mapping — never build the path from raw input.

**Harden inputs** (highest-value change): introduce shared constrained types (`SafeStr`, `IPv4Address`, `Wildcard`, `ASN`, `VlanId`) and nested models replacing `List[dict]`, then update `app.js` payload builders if field shapes change.

## Pitfalls

- `trim_blocks`/`lstrip_blocks` are on: `{% ... %}` lines leave no blank lines or indentation, so put the indentation IOS needs (leading space for sub-commands) on the text lines.
- `model_dump()` passes nested dicts through unchanged; templates access them as `net.network` etc., which Jinja resolves for dict keys and attributes alike.
- Pydantic v2 `Field(example=...)` is deprecated (use `examples=[...]` or `json_schema_extra`); it produces warnings, not errors.
- Changing template whitespace changes output byte-for-byte; update golden files on purpose.

## Done means

All endpoints return 200 for valid input and 422 for invalid input, tests pass, generated IOS pastes cleanly into a lab device, README matches the code.
