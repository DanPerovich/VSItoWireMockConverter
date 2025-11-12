# VSI to WireMock Converter

A powerful command-line tool to convert CA LISA / Broadcom DevTest `.vsi` files to WireMock stub mappings for HTTP/S services. This tool enables seamless migration from DevTest virtualization to WireMock-based API mocking.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd VSItoWireMockConverter

# Install with Poetry
poetry install

# Verify installation
poetry run vsi2wm --help
```

### Basic Usage

```bash
# Convert a VSI file to WireMock Cloud export (default behavior)
poetry run vsi2wm convert --in service.vsi

# Convert with custom output directory
poetry run vsi2wm convert --in service.vsi --out output

# With custom options
poetry run vsi2wm convert \
  --in service.vsi \
  --out output \
  --latency uniform \
  --soap-match both \
  --log-level info \
  --max-file-size 1048576

# Auto-upload to WireMock Cloud
poetry run vsi2wm convert \
  --in service.vsi \
  --auto-upload \
  --api-token wm_xxx

# Update existing MockAPI
poetry run vsi2wm convert \
  --in service.vsi \
  --auto-upload \
  --api-token wm_xxx \
  --update-mockapi \
  --mockapi-id abc123

# Use legacy OSS format (hidden feature)
poetry run vsi2wm convert --in service.vsi --oss-format

# Strict mode - fail if unsupported CA LISA helpers are found
poetry run vsi2wm convert --in service.vsi --strict-mode
```

### Example Output

**WireMock Cloud Export (Default):**
```
output/
├── wiremock-cloud-export.json  # WireMock Cloud import format
├── report.json                 # Conversion report with statistics
└── summary.txt                 # Human-readable summary
```

**WireMock OSS Format (Legacy):**
```
output/
├── mappings/                   # WireMock stub mappings (*.json)
│   ├── GET__accounts_0.json
│   ├── POST__users_1.json
│   └── ...
├── __files/                    # Large response bodies (if split)
│   └── GET__accounts_0_body.json
├── report.json                 # Conversion report with statistics
├── stubs_index.json           # Index of all generated stubs
└── summary.txt                # Human-readable summary
```

## 📋 Features

### ✅ Supported VSI Formats
- **DevTest 9.x+ VSI files** (HTTP/S only)
- **Model-based layout** (`<bd>` elements)
- **RR-pairs layout** (`<reqData>/<rspData>` elements)
- **REST JSON services** with query parameters
- **SOAP XML services** with SOAPAction headers
- **Multiple response variants** with weights
- **Latency ranges** and fixed delays
- **Selection logic** (matchScript)

### ✅ WireMock Compatibility
- **WireMock Cloud** export format (default)
- **WireMock OSS** compatibility (legacy format)
- **Auto-upload to WireMock Cloud** with API token authentication
- **MockAPI management** (create, update, find existing)
- **Response templates** for dynamic responses
- **Priority-based stub ordering**
- **Metadata preservation** from DevTest

## 🛠️ Command Line Options

### Required Arguments
- `--in <file>`: Input VSI file path

### Optional Arguments
- `--out <dir>`: Output directory for WireMock mappings (default: input filename without extension)
- `--latency <strategy>`: Latency strategy
  - `uniform` (default): Convert ranges to uniform distribution
  - `fixed:<ms>`: Use fixed delay for all stubs
- `--soap-match <strategy>`: SOAP matching strategy
  - `soapAction`: Match only SOAPAction header
  - `xpath`: Match only XPath body patterns
  - `both` (default): Match both header and body
- `--max-file-size <bytes>`: Maximum file size before splitting (default: 1048576)
- `--log-level <level>`: Logging level (debug, info, warn, error)
- `--strict-mode`: Fail conversion if unsupported CA LISA helpers are found

### WireMock Cloud Arguments
- `--auto-upload`: Automatically upload stubs to WireMock Cloud after conversion
- `--api-token <token>`: WireMock Cloud API token for authentication
- `--no-create-mockapi`: Only use existing MockAPI with same name, fail if not found
- `--update-mockapi`: Update existing MockAPI instead of creating new one (requires --mockapi-id)
- `--mockapi-id <id>`: Specific MockAPI ID to use for upload (required with --update-mockapi)

### Hidden Arguments
- `--oss-format`: Generate WireMock OSS project folder (legacy format)

### Exit Codes
- `0`: Success
- `1`: General errors
- `2`: Validation errors (file not found, wrong extension, etc.)
- `3`: Permission errors

## 📖 Mapping Rules

### Request Mapping

#### HTTP Method & URL
```json
{
  "request": {
    "method": "GET",
    "urlPath": "/accounts"
  }
}
```

#### Headers
```json
{
  "request": {
    "headers": {
      "Content-Type": {
        "equalTo": "application/json"
      },
      "Authorization": {
        "equalTo": "Bearer token123"
      }
    }
  }
}
```

#### Query Parameters
```json
{
  "request": {
    "queryParameters": {
      "page": {
        "equalTo": "1"
      },
      "limit": {
        "equalTo": "10"
      }
    }
  }
}
```

#### Body Matching
**JSON Bodies:**
```json
{
  "request": {
    "bodyPatterns": [
      {
        "equalToJson": "{\"name\": \"John\", \"email\": \"john@example.com\"}",
        "ignoreArrayOrder": true,
        "ignoreExtraElements": true
      }
    ]
  }
}
```

**XML Bodies:**
```json
{
  "request": {
    "bodyPatterns": [
      {
        "equalToXml": "<user><name>John</name></user>"
      }
    ]
  }
}
```

**SOAP Services:**
```json
{
  "request": {
    "headers": {
      "SOAPAction": {
        "equalTo": "http://example.com/GetUser"
      }
    },
    "bodyPatterns": [
      {
        "equalToXml": "<soapenv:Envelope>...</soapenv:Envelope>"
      }
    ]
  }
}
```

### Response Mapping

#### Status & Headers
```json
{
  "response": {
    "status": 200,
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

#### Body Content
**JSON Responses:**
```json
{
  "response": {
    "jsonBody": {
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

**XML Responses:**
```json
{
  "response": {
    "body": "<user><id>123</id><name>John Doe</name></user>"
  }
}
```

#### Latency
**Range Latency:**
```json
{
  "response": {
    "delayDistribution": {
      "type": "uniform",
      "lower": 100,
      "upper": 200
    }
  }
}
```

**Fixed Latency:**
```json
{
  "response": {
    "fixedDelayMilliseconds": 150
  }
}
```

#### Priority & Metadata
```json
{
  "priority": 0,
  "response": {
    "transformers": ["response-template"]
  },
  "metadata": {
    "devtest_transaction_id": "GET#/accounts",
    "devtest_variant_weight": 0.8,
    "devtest_selection_logic": "request.page == '1'"
  }
}
```

## ☁️ WireMock Cloud Integration

### Auto-Upload to WireMock Cloud

The tool now supports direct integration with WireMock Cloud, making it easy to convert VSI files and immediately deploy them as MockAPIs.

#### Setup
1. **Get your API token** from WireMock Cloud
2. **Set environment variable** (optional):
   ```bash
   export WIREMOCK_CLOUD_API_TOKEN=wm_xxx
   ```

#### Usage Examples

**Create new MockAPI:**
```bash
poetry run vsi2wm convert --in service.vsi --auto-upload --api-token wm_xxx
```

**Update existing MockAPI:**
```bash
poetry run vsi2wm convert --in service.vsi --auto-upload --api-token wm_xxx --update-mockapi --mockapi-id abc123
```

**Use existing MockAPI by name:**
```bash
poetry run vsi2wm convert --in service.vsi --auto-upload --api-token wm_xxx --no-create-mockapi
```

#### MockAPI Management

- **Automatic naming**: MockAPI names are derived from VSI filename
- **Metadata extraction**: Description and tags are extracted from VSI content
- **Conflict resolution**: Handles naming conflicts automatically
- **Metadata updates**: Updates MockAPI metadata when uploading to existing MockAPIs

## 🔧 Examples

### Basic Conversion

**Auto-generated output directory:**
```bash
# Input: service.vsi → Output: service/
poetry run vsi2wm convert --in service.vsi

# Input: my-api.vsi → Output: my-api/
poetry run vsi2wm convert --in my-api.vsi
```

**Custom output directory:**
```bash
# Specify custom output directory
poetry run vsi2wm convert --in service.vsi --out wiremock-stubs
```

### Build Standalone Binaries

Create one-file executables with PyInstaller. This uses the helper script shared with CI so local builds match release artifacts.

```bash
# Install dev dependencies (first time only)
poetry install --with dev

# Build binaries into dist/pyinstaller/
poetry run python scripts/build_pyinstaller.py

# Run the binary
./dist/pyinstaller/vsi2wm --help
```

GitHub Actions builds the same binaries for Linux, macOS, and Windows. Trigger the workflow by pushing a tag like `v0.1.0` or run it manually from the Actions tab. Artifacts are uploaded as `vsi2wm-linux-x64`, `vsi2wm-darwin-x64`, and `vsi2wm-windows-x64.exe`.

Publishing a tag automatically creates a GitHub Release named after the tag and attaches the three binaries as release assets.

#### Running the macOS Binary

macOS Gatekeeper will block unsigned binaries downloaded from the internet. To run the macOS binary, remove the quarantine flag:

```bash
# Remove quarantine flag and make executable
xattr -d com.apple.quarantine vsi2wm-darwin-x64
chmod +x vsi2wm-darwin-x64

# Run the binary
./vsi2wm-darwin-x64 --help
```

Alternatively, you can right-click the binary in Finder, select **Open**, and click **Open** in the security dialog that appears.

### REST JSON Service

**Input VSI:**
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
            <param name="page">1</param>
            <param name="limit">10</param>
          </query>
        </m>
      </rq>
      <rs>
        <rp id="success">
          <m>
            <status>200</status>
            <latency ms="100-200">range</latency>
            <weight>0.8</weight>
          </m>
          <bd><![CDATA[{"accounts": [{"id": 1, "name": "ACME Corp"}]}]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>
```

**Generated WireMock Stub:**
```json
{
  "priority": 0,
  "request": {
    "method": "GET",
    "urlPath": "/accounts",
    "queryParameters": {
      "page": {"equalTo": "1"},
      "limit": {"equalTo": "10"}
    }
  },
  "response": {
    "status": 200,
    "jsonBody": {
      "accounts": [{"id": 1, "name": "ACME Corp"}]
    },
    "delayDistribution": {
      "type": "uniform",
      "lower": 100,
      "upper": 200
    },
    "transformers": ["response-template"]
  },
  "metadata": {
    "devtest_transaction_id": "GET#/accounts",
    "devtest_variant_weight": 0.8
  }
}
```

### SOAP XML Service

**Input VSI:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<serviceImage name="supplier_service" version="1.0">
  <transactions>
    <t id="POST#/supplier">
      <rq>
        <m>
          <method>POST</method>
          <path>/supplier</path>
          <headers>
            <header name="SOAPAction">urn:SupplierService#getSupplier</header>
          </headers>
        </m>
        <bd><![CDATA[<soapenv:Envelope><soapenv:Body><getSupplier><id>123</id></getSupplier></soapenv:Body></soapenv:Envelope>]]></bd>
      </rq>
      <rs>
        <rp id="success">
          <m>
            <status>200</status>
            <latency ms="150">fixed</latency>
            <weight>0.9</weight>
            <matchScript language="js"><![CDATA[request.getSupplier.id == "123"]]></matchScript>
          </m>
          <bd><![CDATA[<soapenv:Envelope><soapenv:Body><getSupplierResponse><supplier><id>123</id><name>ACME Corp</name></supplier></getSupplierResponse></soapenv:Body></soapenv:Envelope>]]></bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>
```

**Generated WireMock Stub:**
```json
{
  "priority": 0,
  "request": {
    "method": "POST",
    "urlPath": "/supplier",
    "headers": {
      "SOAPAction": {
        "equalTo": "urn:SupplierService#getSupplier"
      }
    },
    "bodyPatterns": [
      {
        "equalToXml": "<soapenv:Envelope><soapenv:Body><getSupplier><id>123</id></getSupplier></soapenv:Body></soapenv:Envelope>"
      }
    ]
  },
  "response": {
    "status": 200,
    "body": "<soapenv:Envelope><soapenv:Body><getSupplierResponse><supplier><id>123</id><name>ACME Corp</name></supplier></getSupplierResponse></soapenv:Body></soapenv:Envelope>",
    "fixedDelayMilliseconds": 150,
    "transformers": ["response-template"]
  },
  "metadata": {
    "devtest_transaction_id": "POST#/supplier",
    "devtest_variant_weight": 0.9,
    "devtest_selection_logic": "request.getSupplier.id == \"123\""
  }
}
```

## 🚨 Troubleshooting

### Common Issues

#### File Not Found
```bash
Error: Input file not found: service.vsi
```
**Solution:** Ensure the VSI file exists and the path is correct.

#### Wrong File Extension
```bash
Error: Input file must have .vsi extension: service.xml
```
**Solution:** Ensure the input file has a `.vsi` extension.

#### Permission Errors
```bash
Error: Permission denied creating output directory: /protected/output
```
**Solution:** Check directory permissions or use a different output location.

#### Large File Splitting
```bash
Warning: Response body exceeds max file size (1048576 bytes), splitting to __files/
```
**Solution:** This is normal behavior. Large responses are automatically split to separate files.

#### Non-HTTP Protocol
```bash
Warning: Skipping non-HTTP protocol: MQ
```
**Solution:** Only HTTP/HTTPS protocols are supported. MQ and other protocols are skipped.

#### Unsupported CA LISA Helpers
```bash
Warning: Unsupported CA LISA helper in response body: {{=doRandomString(10)}}
```
**Solution:** The converter detects unsupported CA LISA helper functions and replaces them with `[UNSUPPORTED: helper]` format. Use `--strict-mode` to fail conversion when unsupported helpers are found.

### Debug Mode

Enable debug logging to see detailed conversion information:

```bash
poetry run vsi2wm convert --in service.vsi --out output --log-level debug
```

### Conversion Report

Check the `report.json` file for detailed conversion statistics:

```json
{
  "source_file": "service.vsi",
  "source_version": "1.0",
  "build_number": "1.0.0",
  "counts": {
    "transactions": 3,
    "variants": 6,
    "stubs_generated": 6
  },
  "warnings": [],
  "writer_info": {
    "output_format": "wiremock",
    "files_written": 6,
    "large_files_split": 1
  }
}
```

## 🧪 Testing

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Test Categories
```bash
# Golden file tests
poetry run pytest tests/test_golden_files.py

# CLI tests
poetry run pytest tests/test_cli.py

# Core functionality tests
poetry run pytest tests/test_core.py
```

### Test Coverage
```bash
poetry run pytest --cov=vsi2wm --cov-report=html
```

## 🔄 Migration Guide

### From DevTest to WireMock Cloud

1. **Export VSI files** from DevTest Studio
2. **Get WireMock Cloud API token** from your account
3. **Convert and auto-upload** using this tool:
   ```bash
   poetry run vsi2wm convert --in service.vsi --auto-upload --api-token wm_xxx
   ```
4. **Verify functionality** with your test suite

### From DevTest to WireMock OSS

1. **Export VSI files** from DevTest Studio
2. **Convert to OSS format** using this tool:
   ```bash
   poetry run vsi2wm convert --in service.vsi --oss-format
   ```
3. **Import stubs** into WireMock OSS
4. **Verify functionality** with your test suite

### Best Practices

- **Test thoroughly** after conversion
- **Review generated stubs** for accuracy
- **Adjust priorities** if needed
- **Monitor performance** with new latency settings
- **Backup original VSI files**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`poetry run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- **CA LISA / Broadcom DevTest** for the VSI format
- **WireMock** for the excellent mocking framework
- **Python community** for the amazing ecosystem

## 📞 Support

For issues and questions:
- Check the [troubleshooting section](#-troubleshooting)
- Review the [examples](#-examples)
- Open an issue on GitHub
- Check the [conversion report](#conversion-report) for details