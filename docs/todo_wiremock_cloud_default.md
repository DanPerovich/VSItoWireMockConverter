# TODO: WireMock Cloud Default & Auto-Upload Implementation

## Overview
This document outlines the implementation stages for:
1. Making WireMock Cloud export the default behavior
2. Hiding WireMock OSS project folder generation as an undocumented feature
3. Adding automatic MockAPI creation and upload to WireMock Cloud

## Phase 1: Core Architecture Changes

### Milestone 1.1 — CLI Restructuring
- [ ] **Remove `--wiremock-cloud` flag** (will be default behavior)
- [ ] **Add `--oss-format` flag** (hidden/undocumented feature)
  - Use `argparse.SUPPRESS` to hide from help output
  - Add to `--help` output only when explicitly requested
- [ ] **Update argument validation** to handle new flag structure
- [ ] **Add `--auto-upload` flag** for automatic MockAPI upload
- [ ] **Add `--api-token` argument** for WireMock Cloud authentication
- [ ] **Add `--project-name` argument** (optional, auto-derived from filename)
- [ ] **Update help text and examples** to reflect new defaults

### Milestone 1.2 — Configuration Updates
- [ ] **Add `output_format` setting** to `ConversionConfig` (default: "cloud")
- [ ] **Add `oss_format` setting** for hidden OSS format feature
- [ ] **Add `auto_upload` setting** for automatic upload behavior
- [ ] **Add `wiremock_cloud_api` section** with token and project settings
- [ ] **Update config file template** (`vsi2wm.yaml`) with new defaults
- [ ] **Add config validation** for new settings

### Milestone 1.3 — Core Converter Modifications
- [ ] **Modify `VSIConverter` class** to support format selection
- [ ] **Add `output_format` parameter** to constructor
- [ ] **Update conversion flow** to use Cloud format by default
- [ ] **Add conditional OSS format generation** when `--oss-format` is specified
- [ ] **Integrate auto-upload logic** into main conversion flow

## Phase 2: Output Format Implementation

### Milestone 2.1 — WireMock Cloud Export (Default)
- [ ] **Make Cloud export the primary output method**
- [ ] **Generate `wiremock-cloud-export.json`** by default
- [ ] **Include all stub metadata** in Cloud format
- [ ] **Add Cloud-specific formatting** (names, priorities, metadata)
- [ ] **Update report structure** for Cloud format
- [ ] **Add Cloud format validation** and error handling

### Milestone 2.2 — WireMock OSS Format (Hidden Feature)
- [ ] **Create conditional OSS format generation**
- [ ] **Maintain existing `mappings/` directory structure** when `--oss-format` is used
- [ ] **Preserve all existing OSS functionality** (large file splitting, etc.)
- [ ] **Add OSS format validation** and error handling
- [ ] **Ensure backward compatibility** for existing scripts

### Milestone 2.3 — Writer Module Updates
- [ ] **Refactor `WireMockWriter` class** to support multiple formats
- [ ] **Add `write_cloud_output()` method** for Cloud format
- [ ] **Add `write_oss_output()` method** for OSS format
- [ ] **Update `write_wiremock_output()` function** with format parameter
- [ ] **Add format-specific error handling** and logging
- [ ] **Update file organization** for different formats

## Phase 3: WireMock Cloud Integration

### Milestone 3.1 — MockAPI Creation
- [ ] **Extend `WireMockCloudClient` class** with MockAPI creation methods
- [ ] **Add `create_mock_api()` method** for creating new MockAPIs
- [ ] **Add `get_mock_api()` method** for retrieving existing MockAPIs
- [ ] **Add `update_mock_api()` method** for updating existing MockAPIs
- [ ] **Add MockAPI metadata extraction** from VSI source file
- [ ] **Add MockAPI naming strategy** (derived from filename + metadata)

### Milestone 3.2 — Automatic Upload Pipeline
- [ ] **Create `AutoUploadManager` class** to handle upload workflow
- [ ] **Add MockAPI creation/retrieval logic**
- [ ] **Add stub import/update logic**
- [ ] **Add error handling and retry logic**
- [ ] **Add upload progress reporting**
- [ ] **Add upload validation and verification**

### Milestone 3.3 — API Token Management
- [ ] **Add secure token handling** (environment variables, config files)
- [ ] **Add token validation** and authentication testing
- [ ] **Add token refresh logic** if needed
- [ ] **Add token security best practices** documentation
- [ ] **Add token error handling** and user guidance

## Phase 4: Metadata Extraction & Naming

### Milestone 4.1 — VSI Metadata Extraction
- [ ] **Extract MockAPI name** from VSI filename and metadata
- [ ] **Extract MockAPI description** from VSI content
- [ ] **Extract MockAPI tags** from VSI metadata
- [ ] **Extract MockAPI version** from VSI version/build info
- [ ] **Add metadata fallback strategies** for missing information

### Milestone 4.2 — Naming Strategy
- [ ] **Implement smart naming** based on VSI filename
- [ ] **Add naming conflict resolution** for existing MockAPIs
- [ ] **Add naming validation** (WireMock Cloud requirements)
- [ ] **Add naming customization** options
- [ ] **Add naming documentation** and examples

### Milestone 4.3 — MockAPI Configuration
- [ ] **Add MockAPI type detection** (REST, SOAP, etc.)
- [ ] **Add MockAPI settings** (timeout, rate limiting, etc.)
- [ ] **Add MockAPI environment** configuration
- [ ] **Add MockAPI sharing** and access control
- [ ] **Add MockAPI lifecycle** management

## Phase 5: CLI Integration

### Milestone 5.1 — New CLI Arguments
- [ ] **Add `--auto-upload` flag** for automatic upload
- [ ] **Add `--api-token` argument** for authentication
- [ ] **Add `--project-name` argument** for custom naming
- [ ] **Add `--create-mockapi` flag** for new MockAPI creation
- [ ] **Add `--update-mockapi` flag** for existing MockAPI updates
- [ ] **Add `--mockapi-id` argument** for existing MockAPI ID

### Milestone 5.2 — CLI Workflow
- [ ] **Update main conversion flow** to include auto-upload
- [ ] **Add upload progress reporting** to CLI output
- [ ] **Add upload result reporting** (success/failure)
- [ ] **Add upload error handling** and user guidance
- [ ] **Add upload validation** before starting

### Milestone 5.3 — CLI Examples
- [ ] **Update help text** with new examples
- [ ] **Add auto-upload examples** to documentation
- [ ] **Add token configuration examples**
- [ ] **Add MockAPI creation examples**
- [ ] **Add error handling examples**

## Phase 6: Testing & Validation

### Milestone 6.1 — Unit Tests
- [ ] **Add tests for new CLI arguments**
- [ ] **Add tests for format selection logic**
- [ ] **Add tests for Cloud export generation**
- [ ] **Add tests for OSS format generation**
- [ ] **Add tests for auto-upload functionality**
- [ ] **Add tests for MockAPI creation/management**

### Milestone 6.2 — Integration Tests
- [ ] **Add end-to-end Cloud export tests**
- [ ] **Add end-to-end auto-upload tests**
- [ ] **Add MockAPI creation tests**
- [ ] **Add error handling tests**
- [ ] **Add backward compatibility tests**

### Milestone 6.3 — Golden File Tests
- [ ] **Update existing golden file tests** for new defaults
- [ ] **Add Cloud export golden file tests**
- [ ] **Add OSS format golden file tests**
- [ ] **Add MockAPI metadata golden file tests**

## Phase 7: Documentation Updates

### Milestone 7.1 — README Updates
- [ ] **Update README** to reflect Cloud export as default
- [ ] **Add auto-upload documentation**
- [ ] **Add API token configuration guide**
- [ ] **Add MockAPI creation examples**
- [ ] **Update CLI examples** for new behavior

### Milestone 7.2 — Help Text Updates
- [ ] **Update CLI help text** for new arguments
- [ ] **Add hidden feature documentation** for OSS format
- [ ] **Add auto-upload help text**
- [ ] **Add token configuration help**

### Milestone 7.3 — Migration Guide
- [ ] **Create migration guide** for existing users
- [ ] **Document breaking changes** (removed `--wiremock-cloud`)
- [ ] **Add backward compatibility notes**
- [ ] **Add troubleshooting section** for new features

## Phase 8: Advanced Features

### Milestone 8.1 — Enhanced MockAPI Management
- [ ] **Add MockAPI versioning** support
- [ ] **Add MockAPI backup/restore** functionality
- [ ] **Add MockAPI sharing** and collaboration features
- [ ] **Add MockAPI analytics** and usage tracking
- [ ] **Add MockAPI monitoring** and alerting

### Milestone 8.2 — Advanced Upload Options
- [ ] **Add batch upload** support for multiple VSI files
- [ ] **Add incremental upload** for large MockAPIs
- [ ] **Add upload scheduling** and automation
- [ ] **Add upload rollback** and recovery
- [ ] **Add upload performance** optimization

### Milestone 8.3 — Configuration Management
- [ ] **Add environment-specific** configurations
- [ ] **Add team/shared** configurations
- [ ] **Add configuration templates** for common use cases
- [ ] **Add configuration validation** and linting
- [ ] **Add configuration migration** tools

## Implementation Notes

### Breaking Changes
- **Removal of `--wiremock-cloud` flag**: Users will need to remove this flag from existing scripts
- **Default output format change**: Users expecting OSS format will need to add `--oss-format`
- **Output file structure change**: Default output will be `wiremock-cloud-export.json` instead of `mappings/` directory

### Backward Compatibility
- **OSS format preservation**: All existing OSS functionality will be preserved with `--oss-format`
- **Existing scripts**: Will continue to work with minimal changes
- **Configuration files**: Will be automatically migrated where possible

### Security Considerations
- **API token handling**: Tokens will be stored securely and not logged
- **Authentication**: Proper error handling for invalid tokens
- **Access control**: Respect WireMock Cloud permissions and access levels

### Performance Considerations
- **Upload optimization**: Large MockAPIs will be uploaded efficiently
- **Error recovery**: Robust error handling and retry logic
- **Progress reporting**: Clear feedback during long operations

## Success Criteria

### Phase 1-2: Core Implementation
- [ ] WireMock Cloud export is the default behavior
- [ ] WireMock OSS format is available as hidden feature
- [ ] All existing functionality is preserved
- [ ] No breaking changes to core conversion logic

### Phase 3-4: Cloud Integration
- [ ] Automatic MockAPI creation works correctly
- [ ] Stub upload to WireMock Cloud is reliable
- [ ] API token management is secure
- [ ] Metadata extraction is accurate

### Phase 5-6: CLI & Testing
- [ ] New CLI arguments work correctly
- [ ] Auto-upload workflow is user-friendly
- [ ] All tests pass with new defaults
- [ ] Error handling is robust

### Phase 7-8: Documentation & Polish
- [ ] Documentation is complete and accurate
- [ ] Migration guide helps existing users
- [ ] Advanced features work as expected
- [ ] Performance is acceptable

## Timeline Estimate

- **Phase 1-2**: 2-3 weeks (Core architecture and output formats)
- **Phase 3-4**: 2-3 weeks (Cloud integration and metadata)
- **Phase 5-6**: 1-2 weeks (CLI integration and testing)
- **Phase 7-8**: 1-2 weeks (Documentation and polish)

**Total Estimated Time**: 6-10 weeks

## Risk Mitigation

### Technical Risks
- **WireMock Cloud API changes**: Monitor API documentation and version compatibility
- **Performance issues**: Implement efficient upload strategies and progress reporting
- **Error handling**: Comprehensive error handling and user guidance

### User Experience Risks
- **Breaking changes**: Clear migration guide and backward compatibility
- **Complexity**: Intuitive CLI design and helpful error messages
- **Security**: Secure token handling and clear security documentation

### Project Risks
- **Scope creep**: Focus on core functionality first, advanced features later
- **Testing complexity**: Comprehensive test coverage for all new features
- **Documentation**: Keep documentation updated throughout development
