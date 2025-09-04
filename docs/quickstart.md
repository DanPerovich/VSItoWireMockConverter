# Quickstart Guide

Get up and running with the VSI to WireMock converter in minutes.

## Prerequisites

- **Python 3.11+** installed
- **Poetry** for dependency management
- **VSI files** exported from DevTest Studio

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd VSItoWireMockConverter
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Verify Installation

```bash
poetry run vsi2wm --help
```

You should see the help output with available commands.

## Your First Conversion

### 1. Prepare Your VSI File

Ensure your VSI file:
- Has `.vsi` extension
- Contains HTTP/HTTPS transactions
- Is exported from DevTest Studio

### 2. Run Basic Conversion

```bash
poetry run vsi2wm convert --in your-service.vsi --out output
```

### 3. Check Results

```bash
ls -la output/
```

You should see:
- `mappings/` - WireMock stub files
- `report.json` - Conversion statistics
- `stubs_index.json` - Stub index
- `summary.txt` - Human-readable summary

## Common Use Cases

### REST JSON Service

```bash
# Convert REST service with custom options
poetry run vsi2wm convert \
  --in rest-service.vsi \
  --out rest-output \
  --latency uniform \
  --log-level info
```

### SOAP XML Service

```bash
# Convert SOAP service with both header and body matching
poetry run vsi2wm convert \
  --in soap-service.vsi \
  --out soap-output \
  --soap-match both \
  --log-level debug
```

### Large Response Bodies

```bash
# Handle large responses with custom file size limit
poetry run vsi2wm convert \
  --in large-service.vsi \
  --out large-output \
  --max-file-size 2097152  # 2MB limit
```

## Integration with WireMock

### WireMock Cloud

1. **Convert VSI to WireMock format:**
   ```bash
   poetry run vsi2wm convert --in service.vsi --out wiremock-stubs
   ```

2. **Import stubs to WireMock Cloud:**
   - Use WireMock Cloud web interface
   - Upload `mappings/*.json` files
   - Or use WireMock Cloud API

### WireMock OSS

1. **Convert VSI to WireMock format:**
   ```bash
   poetry run vsi2wm convert --in service.vsi --out wiremock-stubs
   ```

2. **Copy stubs to WireMock:**
   ```bash
   cp wiremock-stubs/mappings/*.json /path/to/wiremock/mappings/
   ```

3. **Restart WireMock:**
   ```bash
   # If using Docker
   docker restart wiremock
   
   # If using standalone
   java -jar wiremock-standalone.jar
   ```

## Testing Your Conversion

### 1. Check Conversion Report

```bash
cat output/report.json | python -m json.tool
```

Look for:
- `stubs_generated` count
- `warnings` array (should be empty)
- `writer_info` statistics

### 2. Validate Generated Stubs

```bash
# Check first stub
python -m json.tool output/mappings/$(ls output/mappings/ | head -1)
```

### 3. Test with Sample Request

```bash
# Test GET request (adjust path as needed)
curl -X GET http://localhost:8080/api/users

# Test POST request with JSON body
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'
```

## Troubleshooting

### Common Issues

#### "Input file not found"
```bash
# Check if file exists
ls -la your-service.vsi

# Use absolute path if needed
poetry run vsi2wm convert --in /full/path/to/your-service.vsi --out output
```

#### "Wrong file extension"
```bash
# Rename file to .vsi extension
mv your-service.xml your-service.vsi
```

#### "No transactions found"
```bash
# Check VSI content
grep -i "<t " your-service.vsi

# Check for HTTP protocol
grep -i "protocol" your-service.vsi
```

### Debug Mode

Enable detailed logging:

```bash
poetry run vsi2wm convert \
  --in your-service.vsi \
  --out output \
  --log-level debug
```

## Next Steps

### Advanced Configuration

- **Custom latency strategies:** `--latency fixed:100`
- **SOAP matching options:** `--soap-match soapAction`
- **File size limits:** `--max-file-size 5242880`

### Batch Processing

```bash
# Convert multiple VSI files
for file in *.vsi; do
  poetry run vsi2wm convert --in "$file" --out "output-${file%.vsi}"
done
```

### Integration with CI/CD

```bash
# Example GitHub Actions step
- name: Convert VSI to WireMock
  run: |
    poetry install
    poetry run vsi2wm convert --in service.vsi --out wiremock-stubs
    # Upload stubs to WireMock Cloud or copy to WireMock OSS
```

## Getting Help

- **Documentation:** Check `docs/` directory
- **Examples:** Use `tests/data/` sample files
- **Issues:** Report on GitHub with logs and VSI samples
- **Debug:** Use `--log-level debug` for detailed information

## Example Workflow

### Complete Example

```bash
# 1. Install converter
git clone <repository-url>
cd VSItoWireMockConverter
poetry install

# 2. Convert VSI file
poetry run vsi2wm convert \
  --in my-service.vsi \
  --out wiremock-stubs \
  --latency uniform \
  --soap-match both \
  --log-level info

# 3. Check results
ls -la wiremock-stubs/
cat wiremock-stubs/report.json | python -m json.tool

# 4. Import to WireMock Cloud
# Upload wiremock-stubs/mappings/*.json files

# 5. Test
curl -X GET https://your-wiremock-cloud-url/api/users
```

This quickstart guide should get you converting VSI files to WireMock stubs in no time!
