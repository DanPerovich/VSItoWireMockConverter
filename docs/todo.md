# TODO: VSI to WireMock converter

## Milestone 0 — Project scaffold ✅
- [x] Repo init (Python 3.11+)
- [x] Packaging: `poetry` with console script `vsi2wm`
- [x] Logger with `--log-level`

## Milestone 1 — Parser & detector ✅
- [x] Streaming XML parse of `.vsi`
- [x] Detect layout: meta props vs inline, `<bd>` vs `<reqData>/<rspData>`
- [x] Extract source version/buildNumber if present
- [x] HTTP-only gate (skip others with report entry)

## Milestone 2 — IR builder ✅
- [x] Build IR for requests (method, path/pathTemplate, headers, query, body)
- [x] Build IR for responses (status, headers, body, latency, weight)
- [x] Capture scripts in `selectionLogic.js`
- [x] Capture simple state/correlation hints (setProperty, tokens)

## Milestone 3 — Mapper (IR → WireMock) ✅
- [x] REST JSON: default `equalToJson`; optional JSONPath
- [x] SOAP: default **both** header (SOAPAction) and XPath operation
- [x] XML bodies: default `equalToXml`; optional XPath
- [x] Latency: map ranges to `delayDistribution: {type: "uniform", lower, upper}`
- [x] Fixed: `fixedDelayMilliseconds`
- [x] One stub per variant; set `priority` by descending weight
- [x] Always add `transformers: ["response-template"]`
- [x] Embed DevTest metadata in `metadata`

## Milestone 4 — Writers ✅
- [x] Write `mappings/` files (pretty JSON)
- [x] Write `report.json`

## Milestone 5 — CLI ✅
- [x] `vsi2wm convert --in file.vsi --out outdir --latency uniform --soap-match both --log-level info`
- [x] Validate args; helpful error messages
- [x] Exit codes: 0 success, non-zero on fatal parse/mapping errors

## Milestone 6 — Test data & unit tests ✅
- [x] Build tiny synthetic VSIs for: SOAP, REST, RR-pairs, model-based, weights, ranges
- [x] Golden-file tests: compare produced mappings to expected JSON
- [x] Snapshot tests for `report.json`

## Milestone 7 — Docs ✅
- [x] `README.md` with quickstart and examples
- [x] Explain mapping rules and any tradeoffs
- [x] Troubleshooting section

## Milestone 8 — Future enhancements ✅
- [x] WireMock Cloud export format + API upload
- [x] Optional config file (YAML) for strategy knobs
- [x] Large-body splitting to `__files/`
- [x] Advanced scenario modeling helpers
