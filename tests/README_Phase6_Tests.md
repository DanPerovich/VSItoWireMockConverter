# Phase 6 Testing Documentation

This document describes the comprehensive test suite implemented for Phase 6: Testing & Validation of the VSI to WireMock Converter project.

## Overview

Phase 6 testing covers all the new features and functionality added in Phases 1-5, including:
- WireMock Cloud export as default behavior
- OSS format as hidden feature
- Auto-upload functionality
- MockAPI creation and management
- New CLI arguments and workflows

## Test Structure

### Test Files

1. **`test_cli_phase6.py`** - CLI functionality tests
   - New CLI arguments (`--auto-upload`, `--api-token`, `--no-create-mockapi`, `--oss-format`)
   - Format selection logic (Cloud vs OSS)
   - Auto-upload workflow
   - MockAPI management
   - Error handling
   - Backward compatibility

2. **`test_cloud_export_phase6.py`** - Cloud export and OSS format tests
   - Cloud export format generation
   - OSS format generation (hidden feature)
   - Format selection integration
   - Content-Type header enhancement
   - Metadata preservation
   - File structure validation

3. **`test_integration_phase6.py`** - End-to-end integration tests
   - Complete Cloud export workflow
   - Complete auto-upload workflow
   - MockAPI lifecycle management
   - Error handling scenarios
   - Backward compatibility workflows

4. **`test_golden_files_phase6.py`** - Golden file tests
   - Cloud export format structure validation
   - OSS format structure validation
   - MockAPI metadata generation
   - Format consistency between Cloud and OSS
   - Large file splitting behavior

5. **`test_missing_cli_args_phase6.py`** - Missing CLI arguments documentation
   - Documents missing CLI arguments from TODO
   - Placeholder tests for future implementation
   - Validation requirements for missing arguments

6. **`test_phase6_runner.py`** - Test runner utility
   - Runs all Phase 6 tests
   - Provides test results summary
   - Supports running specific test categories

## Test Categories

### Unit Tests (Milestone 6.1)
- ✅ New CLI arguments parsing and validation
- ✅ Format selection logic (Cloud default, OSS hidden)
- ✅ Cloud export generation and validation
- ✅ OSS format generation and validation
- ✅ Auto-upload functionality
- ✅ MockAPI creation and management
- ✅ Error handling and validation

### Integration Tests (Milestone 6.2)
- ✅ End-to-end Cloud export workflow
- ✅ End-to-end auto-upload workflow
- ✅ MockAPI creation and management workflow
- ✅ Error handling and recovery scenarios
- ✅ Backward compatibility with existing functionality

### Golden File Tests (Milestone 6.3)
- ✅ Cloud export format structure validation
- ✅ OSS format structure validation
- ✅ MockAPI metadata generation validation
- ✅ Format consistency between Cloud and OSS
- ✅ Large file splitting behavior validation

## Test Markers

The test suite uses pytest markers for organization:

- `@pytest.mark.phase6` - All Phase 6 tests
- `@pytest.mark.cli` - CLI-related tests
- `@pytest.mark.cloud` - Cloud export tests
- `@pytest.mark.oss` - OSS format tests
- `@pytest.mark.mockapi` - MockAPI management tests
- `@pytest.mark.integration` - Integration tests

## Running Tests

### Run All Phase 6 Tests
```bash
python -m pytest tests/test_*_phase6.py -v
```

### Run Specific Test Categories
```bash
# CLI tests only
python -m pytest tests/test_cli_phase6.py -v

# Cloud export tests only
python -m pytest tests/test_cloud_export_phase6.py -v

# Integration tests only
python -m pytest tests/test_integration_phase6.py -v

# Golden file tests only
python -m pytest tests/test_golden_files_phase6.py -v
```

### Run by Marker
```bash
# All Phase 6 tests
python -m pytest -m phase6 -v

# Cloud export tests
python -m pytest -m cloud -v

# OSS format tests
python -m pytest -m oss -v

# MockAPI tests
python -m pytest -m mockapi -v

# Integration tests
python -m pytest -m integration -v
```

### Use Test Runner
```bash
# Run all Phase 6 tests
python tests/test_phase6_runner.py

# Run specific test category
python tests/test_phase6_runner.py cli
python tests/test_phase6_runner.py cloud
python tests/test_phase6_runner.py integration
```

## Test Coverage

### CLI Functionality
- ✅ New argument parsing (`--auto-upload`, `--api-token`, `--no-create-mockapi`, `--oss-format`)
- ✅ Format selection logic (Cloud default, OSS hidden)
- ✅ Auto-upload workflow integration
- ✅ Error handling and validation
- ✅ Backward compatibility with legacy flags

### Cloud Export Format
- ✅ Export file structure validation
- ✅ Stub naming convention
- ✅ Content-Type header enhancement
- ✅ Metadata preservation
- ✅ Cloud-specific formatting
- ✅ Validation and error handling

### OSS Format (Hidden Feature)
- ✅ File structure preservation
- ✅ Large file splitting
- ✅ Report generation
- ✅ Index file generation
- ✅ Summary generation
- ✅ Backward compatibility

### MockAPI Management
- ✅ MockAPI creation
- ✅ MockAPI retrieval
- ✅ MockAPI listing
- ✅ MockAPI update
- ✅ MockAPI deletion
- ✅ Name conflict resolution
- ✅ Metadata extraction

### Auto-Upload Functionality
- ✅ Upload workflow
- ✅ Validation and prerequisites
- ✅ Error handling and recovery
- ✅ Progress reporting
- ✅ MockAPI integration

### Integration Workflows
- ✅ End-to-end Cloud export
- ✅ End-to-end auto-upload
- ✅ MockAPI lifecycle
- ✅ Error scenarios
- ✅ Backward compatibility

## Test Data

### Sample VSI Files
Tests use sample VSI files from `tests/data/`:
- `simple_rest.vsi` - Basic REST API
- `soap_service.vsi` - SOAP service
- `multiple_transactions.vsi` - Multiple transactions
- `query_params.vsi` - Query parameters
- `rr_pairs.vsi` - Request-response pairs

### Mock Data
Tests use comprehensive mock data for:
- WireMock Cloud API responses
- MockAPI metadata
- Stub mappings
- Error scenarios
- Network failures

## Test Results

### Expected Results
- All Phase 6 tests should pass
- No linting errors
- Comprehensive coverage of new functionality
- Backward compatibility maintained

### Test Metrics
- **Total Test Files**: 6
- **Total Test Classes**: 25+
- **Total Test Methods**: 100+
- **Coverage Areas**: CLI, Cloud Export, OSS Format, MockAPI, Integration, Golden Files

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Mock Failures**: Check mock setup and return values
3. **File Path Issues**: Verify test data files exist
4. **Network Errors**: Tests use mocks, no real network calls

### Debug Mode
```bash
# Run with debug output
python -m pytest tests/test_*_phase6.py -v -s --tb=long

# Run specific test with debug
python -m pytest tests/test_cli_phase6.py::TestPhase6CLIArguments::test_parse_args_auto_upload -v -s
```

## Future Enhancements

### Missing CLI Arguments (Documented)
The following CLI arguments are documented as missing and need implementation:
- `--project-name` - Custom project name for WireMock Cloud
- `--update-mockapi` - Update existing MockAPI instead of creating new one
- `--mockapi-id` - Specific MockAPI ID to use for upload

### Additional Test Coverage
- Performance testing for large VSI files
- Stress testing for auto-upload functionality
- Security testing for API token handling
- Load testing for MockAPI management

## Conclusion

The Phase 6 test suite provides comprehensive coverage of all new functionality while maintaining backward compatibility. The tests are well-organized, documented, and ready for continuous integration.

For questions or issues with the test suite, refer to the individual test files or the main project documentation.
