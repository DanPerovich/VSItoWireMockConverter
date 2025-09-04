# Spec: VSI to WireMock converter

**Focus keyword:** VSI to WireMock converter

You want a CLI-only **VSI to WireMock converter** that reads a single CA LISA / Broadcom DevTest `.vsi` (9.x+) and writes WireMock stub mappings for **HTTP/S** services. Output targets both **WireMock Cloud** (import via UI/API) and **WireMock OSS** (Docker/JAR).

---

## Goals
- Parse `.vsi` files from DevTest 9.x+ (HTTP/S only).
- Support **both** VSI shapes: model-based (`<bd>`) and RR-pairs (`<reqData>/<rspData>`).
- Normalize to a small Intermediate Representation (IR) then emit WireMock stubs.
- Create **one stub per response variant**, plus any files under `__files/` when body size is large.
- Always enable **Response Templating** in each stub.
- Map DevTest latency ranges to **WireMock random uniform delay**.
- Avoid custom extensions (works in WireMock Cloud and OSS out of the box).

## Non-goals (MVP)
- No MQ/JMS/TCP protocols.
- No directory input; **one VSI** per run.
- No upload to WireMock Cloud (future enhancement).
- No randomness for **weighted** variants (record weight in metadata only).

---

## Inputs and outputs
### Input
- Single file: `path/to/service.vsi` (XML)

### Output
```
output/
  mappings/        # *.json stub mappings
  __files/         # optional: large response bodies (if split is on later)
  report.json      # conversion report (summary + warnings)
```
> For MVP, bodies may be inlined; splitting to `__files/` can be a follow-up.

---

## CLI
```
vsi2wm convert --in service.vsi --out output   --latency uniform   --soap-match both   --log-level info
```
- `--in`: input `.vsi` file (required)
- `--out`: output directory (required)
- `--latency`: `uniform` (default) or `fixed:<ms>` (fallback)
- `--soap-match`: `soapAction|xpath|both` (default: `both`)
- `--log-level`: `debug|info|warn|error` (default: `info`)

> Future flags (not in MVP): `--wmc-export`, `--wmc-upload`

---

## Intermediate Representation (IR)

A small, version-agnostic model:

```json
{
  "protocol": "HTTP",
  "transactions": [
    {
      "id": "string",
      "request": {
        "method": "GET|POST|...",
        "path": "/...",
        "pathTemplate": "/inventory/{{id}}",
        "soapAction": "urn:Service#Operation",
        "operation": "OperationName",
        "headers": { "Header": "value or *" },
        "query": { "k": "v or *" },
        "body": { "type": "xml|json|text", "content": "..." }
      },
      "responseVariants": [
        {
          "status": 200,
          "headers": { "Content-Type": "application/json" },
          "body": { "type": "xml|json|text", "content": "..." },
          "latency": { "mode": "range|fixed", "minMs": 50, "maxMs": 150, "fixedMs": null },
          "weight": 0.9,
          "notes": "optional"
        }
      ],
      "selectionLogic": { "js": "optional raw matchScript if present" },
      "state": {
        "requires": { "scenario": "name", "state": "Started" },
        "sets": { "scenario": "name", "newState": "Next" }
      }
    }
  ],
  "meta": {
    "sourceVersion": "10.5.0",
    "buildNumber": "510"
  }
}
```

---

## VSI → IR normalization

- **Detect layout**
  - If `<meta><p name="...">` exists, read properties there; else read from `<m>` blocks.
  - If `<bd>` found → model-based bodies.
  - If `<reqData>/<rspData>` found → RR-pairs style bodies.
- **HTTP-only gate**: if protocol prop is not HTTP/S, skip with a report entry.
- **Request extraction**
  - REST: `<method>`, `<path>` or `<pathTemplate>`, `<headers>`, `<query>`, `<bd>`.
  - SOAP: `<endpoint>` as path, plus `<soapAction>` and `<operation>` when present; body from `<bd>`.
- **Response extraction**
  - Status from `<m><status>` (default 200). Headers if present. Body from `<bd>` or `<rspData>`.
  - Latency: read `<latency ms="a-b">range</latency>` or meta think time (`RANGE:a-b`, `FIXED:n`).
  - Weight: `<selectionWeight>` or `<weight>`; keep numeric value for metadata.
- **State/correlation**
  - Record simple `setProperty`, echoed tokens, or comments into `state` for later mapping to scenarios and templates.
- **Scripts**
  - Keep raw `<matchScript language="js">` in `selectionLogic.js` for reporting and possible hints.

---

## IR → WireMock mapping

| VSI | WireMock |
|---|---|
| Method | `request.method` |
| Path | `request.urlPath` (or `urlPathPattern` / `urlPathTemplate` if variables present) |
| Query params | `request.queryParameters` with `equalTo` by default |
| Headers | `request.headers` with `equalTo` by default |
| SOAPAction | `request.headers.SOAPAction.contains` and/or XPath on body |
| Operation (SOAP) | `matchesXPath` on Body (operation element) |
| Body JSON | default `equalToJson` (tolerant option on/off later), optional `matchesJsonPath` |
| Body XML | default `equalToXml`, optional `matchesXPath` |
| Response status | `response.status` |
| Response headers | `response.headers` |
| Response body | inline `response.body` (MVP); later `bodyFileName` |
| Latency range | `response.delayDistribution` → `{"type":"uniform","lower":minMs,"upper":maxMs}` |
| Fixed latency | `response.fixedDelayMilliseconds` |
| Weighted variants | Multiple stubs (one per variant); record weight in `metadata.weight`; set `priority` by weight (1 = highest) |
| Templating | `transformers: ["response-template"]` always on |

**SOAP default match mode:** **both** (`SOAPAction` header and XPath on operation).

---

## Handling `matchScript`
- Try to convert basic predicates to matchers:
  - JSON: translate comparisons to `matchesJsonPath` (e.g., `$.amount[?(@ > 500)]`).
  - XML: translate to `matchesXPath` with predicates.
- If not convertible, tag the variant with `"metadata": { "manualReview": true, "matchScript": "…" }` and add a report note.

---

## Scenarios and correlation
- For simple flows (login → authorized), use `scenarioName`, `requiredScenarioState`, `newScenarioState`.
- Use response templating to echo request parts:
  - JSON: `{{jsonPath request.body '$.amount'}}`
  - XML: `{{xPath request.body '/*[local-name()=\'Envelope\']'}}`
  - Headers: `{{request.headers.X-Session-Id}}`

---

## WireMock Cloud specifics
- Stubs must include `transformers: ["response-template"]` (Cloud supports Handlebars helpers).
- Random delay uses **Uniform** where a VSI exposes a range.
- Keep DevTest metadata under `metadata` (match tolerance, version, ids).

---

## Error handling & report
- Produce `report.json` with:
  - source file info (name, version attrs if present)
  - counts: transactions, variants, stubs generated
  - warnings: skipped protocols, unparsed pieces, unconverted scripts
  - notes: default match modes applied, latency strategy used

---

## Constraints & assumptions
- Response templating is available in both Cloud and OSS; for OSS we set per-stub transformers in output JSON.
- No custom extensions.
- Weighted randomness is out of scope; deterministic selection via `priority` only.

---

## Open items / TBD
- Heuristics for mapping DevTest **match tolerance** to WireMock matchers (fine-tune after first runs).
- Large body handling policy can be added later.
- Performance targets once typical VSI sizes are known.
