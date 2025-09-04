# Troubleshooting Guide

This guide helps you resolve common issues when using the VSI to WireMock converter.

## Common Error Messages

### File and Path Issues

#### "Input file not found"
```bash
Error: Input file not found: service.vsi
```

**Causes:**
- File doesn't exist at the specified path
- Incorrect file path
- File permissions issue

**Solutions:**
1. Verify the file exists: `ls -la service.vsi`
2. Use absolute path: `--in /full/path/to/service.vsi`
3. Check file permissions: `chmod 644 service.vsi`

#### "Input file must have .vsi extension"
```bash
Error: Input file must have .vsi extension: service.xml
```

**Causes:**
- File has wrong extension
- File is not a VSI file

**Solutions:**
1. Rename file: `mv service.xml service.vsi`
2. Verify it's a valid VSI file (should contain `<serviceImage>` root element)

#### "Output path exists but is not a directory"
```bash
Error: Output path exists but is not a directory: /path/to/output
```

**Causes:**
- Output path is a file, not a directory
- Path conflict

**Solutions:**
1. Remove existing file: `rm /path/to/output`
2. Use different output directory: `--out /path/to/new/output`

#### "Permission denied creating output directory"
```bash
Error: Permission denied creating output directory: /protected/output
```

**Causes:**
- Insufficient permissions
- Directory owned by different user

**Solutions:**
1. Use different location: `--out ~/output`
2. Fix permissions: `sudo chmod 755 /protected/output`
3. Change ownership: `sudo chown $USER /protected/output`

### Validation Errors

#### "Max file size must be positive"
```bash
Error: Max file size must be positive: 0
```

**Causes:**
- Invalid `--max-file-size` value
- Zero or negative value

**Solutions:**
1. Use positive value: `--max-file-size 1048576`
2. Use default: omit the parameter

### Conversion Issues

#### "No transactions found"
```bash
WARNING: No transactions found in VSI file
```

**Causes:**
- Empty VSI file
- Malformed VSI structure
- Non-HTTP protocol (skipped)

**Solutions:**
1. Check VSI file content: `grep -i "<t " service.vsi`
2. Verify VSI structure is valid
3. Check for HTTP protocol in VSI

#### "Non-HTTP protocol detected"
```bash
WARNING: Skipping non-HTTP protocol: MQ
```

**Causes:**
- VSI contains MQ, JMS, or other non-HTTP protocols
- Protocol detection issue

**Solutions:**
1. Filter for HTTP-only VSIs
2. Check protocol in VSI: `grep -i "protocol" service.vsi`
3. This is expected behavior for non-HTTP services

#### "Large response body exceeds max file size"
```bash
WARNING: Response body exceeds max file size (1048576 bytes), splitting to __files/
```

**Causes:**
- Response body is larger than threshold
- Large JSON/XML responses

**Solutions:**
1. This is normal behavior
2. Increase threshold: `--max-file-size 2097152`
3. Check generated `__files/` directory

## Debugging Techniques

### Enable Debug Logging

```bash
poetry run vsi2wm convert --in service.vsi --out output --log-level debug
```

**Debug output includes:**
- VSI parsing details
- Layout detection
- Transaction processing
- IR building steps
- Mapping decisions
- File writing operations

### Check Conversion Report

Examine `output/report.json` for detailed statistics:

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
  "warnings": [
    "Non-HTTP protocol detected: MQ"
  ],
  "writer_info": {
    "output_format": "wiremock",
    "files_written": 6,
    "large_files_split": 1
  }
}
```

### Validate VSI Structure

Check if VSI file has correct structure:

```bash
# Check for serviceImage root
grep -i "serviceImage" service.vsi

# Check for transactions
grep -i "<t " service.vsi

# Check for HTTP protocol
grep -i "protocol" service.vsi
```

### Test with Sample Files

Use the provided test VSI files to verify functionality:

```bash
# Test simple REST conversion
poetry run vsi2wm convert --in tests/data/simple_rest.vsi --out test_output

# Test SOAP conversion
poetry run vsi2wm convert --in tests/data/soap_service.vsi --out test_output

# Test query parameters
poetry run vsi2wm convert --in tests/data/query_params.vsi --out test_output
```

## Performance Issues

### Slow Conversion

**Causes:**
- Large VSI files
- Many transactions
- Complex XML structure

**Solutions:**
1. Use debug logging to identify bottlenecks
2. Check file size: `ls -lh service.vsi`
3. Consider splitting large VSIs
4. Monitor system resources during conversion

### Memory Issues

**Causes:**
- Very large response bodies
- Too many transactions in single VSI

**Solutions:**
1. Increase `--max-file-size` to reduce file splitting
2. Split large VSIs into smaller files
3. Process VSIs individually instead of batch

## WireMock Integration Issues

### Stub Import Problems

**Common Issues:**
- Invalid JSON format
- Missing required fields
- File path issues

**Solutions:**
1. Validate generated JSON: `python -m json.tool output/mappings/stub_0_0.json`
2. Check WireMock logs for specific errors
3. Verify stub structure matches WireMock requirements

### Priority Conflicts

**Issue:** Stubs with same priority
**Solution:** Check weight values in VSI and adjust if needed

### Response Template Issues

**Issue:** Response templates not working
**Solution:** Verify `transformers: ["response-template"]` is present in stubs

## VSI-Specific Issues

### Layout Detection Problems

**Issue:** Wrong layout detected
**Symptoms:** Missing request/response data

**Solutions:**
1. Check VSI structure for `<bd>` vs `<reqData>/<rspData>`
2. Verify XML is well-formed
3. Use debug logging to see layout detection

### Selection Logic Issues

**Issue:** Complex JavaScript not working in WireMock
**Symptoms:** Stubs not matching expected requests

**Solutions:**
1. Review `matchScript` content in VSI
2. Convert to WireMock-compatible matching
3. Use metadata for debugging: check `devtest_selection_logic`

### Latency Mapping Issues

**Issue:** Unexpected response delays
**Symptoms:** Different latency behavior than DevTest

**Solutions:**
1. Check latency values in VSI: `grep -i "latency" service.vsi`
2. Verify uniform distribution vs fixed delays
3. Adjust WireMock delay settings if needed

## Environment Issues

### Python Version

**Issue:** Python version compatibility
**Solution:** Ensure Python 3.11+ is installed

```bash
python3 --version
```

### Poetry Installation

**Issue:** Poetry not found
**Solution:** Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### Dependencies

**Issue:** Missing dependencies
**Solution:** Reinstall dependencies

```bash
poetry install
poetry install --with dev
```

## Getting Help

### Check Logs

Always check the conversion logs first:

```bash
poetry run vsi2wm convert --in service.vsi --out output --log-level debug 2>&1 | tee conversion.log
```

### Report Issues

When reporting issues, include:

1. **VSI file sample** (sanitized)
2. **Command used**
3. **Error messages**
4. **Conversion report** (`report.json`)
5. **Environment details** (OS, Python version)

### Common Debugging Commands

```bash
# Check VSI structure
grep -i "serviceImage\|transaction\|protocol" service.vsi

# Validate JSON output
find output/mappings -name "*.json" -exec python -m json.tool {} \;

# Check file sizes
ls -lh output/mappings/
ls -lh output/__files/ 2>/dev/null || echo "No large files"

# Count generated stubs
find output/mappings -name "*.json" | wc -l

# Verify report
python -m json.tool output/report.json
```

## Best Practices

### Before Conversion
1. **Backup original VSI files**
2. **Validate VSI in DevTest Studio**
3. **Check for non-HTTP protocols**
4. **Review complex selection logic**

### During Conversion
1. **Use debug logging for first run**
2. **Check conversion report**
3. **Verify output structure**
4. **Test with sample requests**

### After Conversion
1. **Validate generated stubs**
2. **Test in WireMock environment**
3. **Verify latency behavior**
4. **Check metadata preservation**
5. **Monitor performance**
