# VSI to WireMock Converter

A command-line tool to convert CA LISA / Broadcom DevTest `.vsi` files to WireMock stub mappings for HTTP/S services.

## Features

- Parse DevTest 9.x+ VSI files (HTTP/S only)
- Support both VSI layouts: model-based (`<bd>`) and RR-pairs (`<reqData>/<rspData>`)
- Generate WireMock stub mappings compatible with both WireMock Cloud and WireMock OSS
- Map DevTest latency ranges to WireMock random uniform delay
- Support for REST JSON and SOAP XML services
- Generate conversion reports with warnings and statistics

## Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (for development)

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd VSItoWireMockConverter

# Install with Poetry
poetry install

# Install the console script
poetry install --with dev
```

## Usage

### Basic conversion

```bash
# Convert a VSI file to WireMock mappings
vsi2wm convert --in service.vsi --out output

# With custom options
vsi2wm convert \
  --in service.vsi \
  --out output \
  --latency uniform \
  --soap-match both \
  --log-level debug
```

### Command line options

- `--in`: Input VSI file path (required)
- `--out`: Output directory for WireMock mappings (required)
- `--latency`: Latency strategy - `uniform` (default) or `fixed:<ms>`
- `--soap-match`: SOAP matching strategy - `soapAction`, `xpath`, or `both` (default: `both`)
- `--log-level`: Logging level - `debug`, `info`, `warn`, `error` (default: `info`)
- `--version`: Show version information

### Output structure

```
output/
├── mappings/          # WireMock stub mappings (*.json)
├── __files/          # Large response bodies (if split enabled)
└── report.json       # Conversion report with statistics
```

## Development

### Setup development environment

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run black vsi2wm tests
poetry run isort vsi2wm tests
poetry run mypy vsi2wm
```

### Project structure

```
vsi2wm/
├── __init__.py       # Package initialization
├── cli.py           # Command-line interface
└── core.py          # Core conversion logic

tests/
├── __init__.py
├── test_cli.py      # CLI tests
└── test_core.py     # Core logic tests
```

## Supported VSI formats

### REST JSON example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<serviceImage name="crm_accounts" version="1.0">
  <transactions>
    <t id="GET#/accounts">
      <rq>
        <m>
          <method>GET</method>
          <path>/accounts</path>
          <query>
            <param name="name">*</param>
            <param name="page">*</param>
          </query>
        </m>
      </rq>
      <rs>
        <rp id="page_1">
          <m><status>200</status><latency ms="40-120">range</latency></m>
          <bd><![CDATA[{"page": 1, "items": [...]}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>
```

### SOAP XML example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<serviceImage name="supplier_service" version="1.0">
  <transactions>
    <t id="SOAP#SupplierService#getSupplier">
      <rq>
        <m>
          <operation>getSupplier</operation>
          <soapAction>urn:SupplierService#getSupplier</soapAction>
          <endpoint>/soa-infra/services/erp/SupplierService</endpoint>
        </m>
        <bd><![CDATA[<soapenv:Envelope>...</soapenv:Envelope>]]></bd>
      </rq>
      <rs>
        <rp id="200_ok">
          <m><status>200</status><latency ms="50-150">range</latency></m>
          <bd><![CDATA[<soapenv:Envelope>...</soapenv:Envelope>]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>
```

## Roadmap

### Milestone 0 - Project scaffold ✅
- [x] Repo init (Python 3.11+)
- [x] Packaging: `poetry` with console script `vsi2wm`
- [x] Logger with `--log-level`

### Milestone 1 - Parser & detector
- [ ] Streaming XML parse of `.vsi`
- [ ] Detect layout: meta props vs inline, `<bd>` vs `<reqData>/<rspData>`
- [ ] Extract source version/buildNumber if present
- [ ] HTTP-only gate (skip others with report entry)

### Milestone 2 - IR builder
- [ ] Build IR for requests (method, path/pathTemplate, headers, query, body)
- [ ] Build IR for responses (status, headers, body, latency, weight)
- [ ] Capture scripts in `selectionLogic.js`
- [ ] Capture simple state/correlation hints (setProperty, tokens)

### Milestone 3 - Mapper (IR → WireMock)
- [ ] REST JSON: default `equalToJson`; optional JSONPath
- [ ] SOAP: default **both** header (SOAPAction) and XPath operation
- [ ] XML bodies: default `equalToXml`; optional XPath
- [ ] Latency: map ranges to `delayDistribution: {type: "uniform", lower, upper}`
- [ ] Fixed: `fixedDelayMilliseconds`
- [ ] One stub per variant; set `priority` by descending weight
- [ ] Always add `transformers: ["response-template"]`
- [ ] Embed DevTest metadata in `metadata`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

[Add your license information here]

## Acknowledgments

- CA LISA / Broadcom DevTest for the VSI format
- WireMock for the excellent mocking framework