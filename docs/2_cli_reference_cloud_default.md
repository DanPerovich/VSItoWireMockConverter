# CLI Reference: WireMock Cloud Default

## Overview
This document describes the new CLI behavior where WireMock Cloud export is the default output format, and WireMock OSS project folder generation is available as a hidden feature.

## Basic Usage

### Default Behavior (WireMock Cloud Export)
```bash
# Generate WireMock Cloud export (default)
poetry run vsi2wm convert --in service.vsi

# With auto-upload to WireMock Cloud
poetry run vsi2wm convert --in service.vsi --auto-upload --api-token YOUR_TOKEN

# With custom project name
poetry run vsi2wm convert --in service.vsi --auto-upload --api-token YOUR_TOKEN --project-name "My API"
```

### Hidden OSS Format (Legacy Behavior)
```bash
# Generate WireMock OSS project folder (hidden feature)
poetry run vsi2wm convert --in service.vsi --oss-format

# OSS format with all options
poetry run vsi2wm convert \
  --in service.vsi \
  --oss-format \
  --latency uniform \
  --soap-match both \
  --log-level info
```

## CLI Arguments

### Required Arguments
- `--in <file>`: Input VSI file path

### Optional Arguments (Default: Cloud Export)
- `--out <dir>`: Output directory (default: input filename without extension)
- `--config <file>`: Configuration file (YAML)
- `--latency <strategy>`: Latency strategy (overrides config)
- `--soap-match <strategy>`: SOAP matching strategy (overrides config)
- `--log-level <level>`: Logging level (overrides config)
- `--max-file-size <bytes>`: Maximum file size before splitting (overrides config)

### WireMock Cloud Arguments
- `--auto-upload`: Automatically upload to WireMock Cloud after conversion
- `--api-token <token>`: WireMock Cloud API token for authentication
- `--project-name <name>`: Custom project name (default: derived from filename)
- `--create-mockapi`: Create new MockAPI (default behavior)
- `--update-mockapi`: Update existing MockAPI
- `--mockapi-id <id>`: Existing MockAPI ID for updates

### Hidden Arguments (OSS Format)
- `--oss-format`: Generate WireMock OSS project folder (hidden feature)

## Output Formats

### WireMock Cloud Export (Default)
```
output/
  wiremock-cloud-export.json    # Main export file
  report.json                    # Conversion report
  summary.txt                    # Human-readable summary
```

### WireMock OSS Project Folder (Hidden Feature)
```
output/
  mappings/                      # Individual stub files
  __files/                       # Large response bodies
  report.json                    # Conversion report
  stubs_index.json              # Stub index
  summary.txt                   # Human-readable summary
```

## Configuration

### Default Configuration (vsi2wm.yaml)
```yaml
# Output format (default: cloud)
output_format: cloud

# Auto-upload settings
auto_upload: false
wiremock_cloud_api:
  api_key: null
  project_id: null
  environment: default

# Hidden OSS format settings
oss_format: false

# Other settings remain the same...
latency_strategy: uniform
soap_match_strategy: both
max_file_size: 1048576
log_level: info
```

### Environment Variables
```bash
# WireMock Cloud API token
export WIREMOCK_CLOUD_API_TOKEN="your_token_here"

# WireMock Cloud project ID
export WIREMOCK_CLOUD_PROJECT_ID="your_project_id"
```

## Examples

### Basic Cloud Export
```bash
# Simple conversion to WireMock Cloud format
poetry run vsi2wm convert --in my-api.vsi
# Output: my-api/wiremock-cloud-export.json
```

### Auto-Upload to WireMock Cloud
```bash
# Convert and upload automatically
poetry run vsi2wm convert \
  --in my-api.vsi \
  --auto-upload \
  --api-token wm_1234567890abcdef \
  --project-name "My REST API"
```

### Custom Configuration
```bash
# Use custom config file
poetry run vsi2wm convert \
  --in my-api.vsi \
  --config production.yaml \
  --auto-upload
```

### Hidden OSS Format
```bash
# Generate WireMock OSS project folder
poetry run vsi2wm convert \
  --in my-api.vsi \
  --oss-format \
  --out wiremock-stubs
```

## Migration Guide

### From Previous Version
If you were using the previous version with `--wiremock-cloud`:

**Before:**
```bash
poetry run vsi2wm convert --in service.vsi --out output --wiremock-cloud
```

**After:**
```bash
# Cloud export (default)
poetry run vsi2wm convert --in service.vsi --out output

# OSS format (if you need it)
poetry run vsi2wm convert --in service.vsi --out output --oss-format
```

### Breaking Changes
1. **`--wiremock-cloud` flag removed**: Cloud export is now default
2. **Default output structure changed**: `wiremock-cloud-export.json` instead of `mappings/` directory
3. **OSS format requires `--oss-format`**: Previously default, now hidden feature

### Backward Compatibility
- **OSS format preserved**: All existing OSS functionality available with `--oss-format`
- **Configuration files**: Will be automatically migrated where possible
- **Existing scripts**: Will work with minimal changes (remove `--wiremock-cloud`)

## Error Handling

### Common Errors
```bash
# Missing API token for auto-upload
Error: API token required for auto-upload. Use --api-token or set WIREMOCK_CLOUD_API_TOKEN

# Invalid API token
Error: Invalid API token. Please check your token and try again.

# MockAPI creation failed
Error: Failed to create MockAPI: Project name already exists

# OSS format not found (hidden feature)
Error: --oss-format is a hidden feature. Use --help for available options.
```

### Troubleshooting
1. **API Token Issues**: Check token validity and permissions
2. **Network Issues**: Verify internet connection and WireMock Cloud availability
3. **Permission Issues**: Ensure proper access to WireMock Cloud project
4. **Naming Conflicts**: Use `--project-name` to specify custom name

## Security Considerations

### API Token Security
- **Never log tokens**: Tokens are never logged or displayed
- **Environment variables**: Use `WIREMOCK_CLOUD_API_TOKEN` for automation
- **Config files**: Store tokens securely in configuration files
- **Token rotation**: Regularly rotate API tokens

### Best Practices
1. **Use environment variables** for CI/CD pipelines
2. **Store tokens securely** in configuration management systems
3. **Limit token permissions** to minimum required access
4. **Monitor token usage** and rotate regularly

## Advanced Usage

### Batch Processing
```bash
# Process multiple VSI files
for file in *.vsi; do
  poetry run vsi2wm convert --in "$file" --auto-upload --api-token "$TOKEN"
done
```

### CI/CD Integration
```bash
# GitHub Actions example
- name: Convert VSI to WireMock Cloud
  run: |
    poetry run vsi2wm convert \
      --in service.vsi \
      --auto-upload \
      --api-token ${{ secrets.WIREMOCK_CLOUD_TOKEN }}
```

### Custom Naming Strategy
```bash
# Use custom project naming
poetry run vsi2wm convert \
  --in service.vsi \
  --auto-upload \
  --api-token "$TOKEN" \
  --project-name "service-$(date +%Y%m%d)"
```
