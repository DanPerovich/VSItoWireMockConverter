# Technical Specification: MockAPI Creation & Upload

## Overview
This document specifies the technical implementation for automatic MockAPI creation and upload to WireMock Cloud, including metadata extraction from VSI files and intelligent naming strategies.

## MockAPI Creation Workflow

### 1. Metadata Extraction

#### VSI Source Metadata
```python
class VSIMetadata:
    """Extracted metadata from VSI file for MockAPI creation."""
    
    def __init__(self, vsi_file: Path):
        self.filename = vsi_file.stem
        self.source_version = None
        self.build_number = None
        self.protocol = None
        self.service_name = None
        self.description = None
        self.tags = []
        self.transactions_count = 0
        self.api_type = None  # REST, SOAP, etc.
```

#### Extraction Strategy
1. **Filename Analysis**: Extract meaningful name from VSI filename
   - Remove common suffixes: `_vsi`, `_service`, `_api`
   - Convert to title case: `my-api.vsi` → `My Api`
   - Handle special characters: `user-service_v2.vsi` → `User Service V2`

2. **VSI Content Analysis**: Extract metadata from XML content
   ```xml
   <!-- Extract from VSI root element -->
   <serviceImage version="1.0" buildNumber="1.0.0">
   ```

3. **Protocol Detection**: Determine API type
   - HTTP/HTTPS → REST API
   - SOAP actions → SOAP API
   - Mixed protocols → Hybrid API

4. **Description Generation**: Create meaningful description
   ```python
   def generate_description(metadata: VSIMetadata) -> str:
       return f"{metadata.api_type} API with {metadata.transactions_count} endpoints"
   ```

### 2. MockAPI Naming Strategy

#### Default Naming Rules
1. **Primary**: Use VSI filename (sanitized)
   - `user-service.vsi` → `User Service`
   - `payment-api_v2.vsi` → `Payment Api V2`

2. **Fallback**: Use service name from VSI content
   - Extract from `<serviceImage>` attributes
   - Extract from transaction descriptions

3. **Conflict Resolution**: Handle naming conflicts
   ```python
   def resolve_naming_conflict(name: str, existing_apis: List[str]) -> str:
       if name not in existing_apis:
           return name
       
       # Try with version suffix
       for i in range(1, 10):
           candidate = f"{name} v{i}"
           if candidate not in existing_apis:
               return candidate
       
       # Try with timestamp
       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       return f"{name}_{timestamp}"
   ```

#### Custom Naming
- **`--project-name`**: Override default naming
- **Environment variables**: `WIREMOCK_CLOUD_PROJECT_NAME`
- **Configuration file**: `project_name` in `wiremock_cloud_api` section

### 3. MockAPI Configuration

#### Default Settings
```python
DEFAULT_MOCKAPI_CONFIG = {
    "name": "Auto-generated from VSI",
    "description": "API converted from VSI file",
    "type": "openapi",  # or "graphql"
    "environment": "default",
    "settings": {
        "timeout": 30000,  # 30 seconds
        "rate_limiting": {
            "enabled": False
        },
        "cors": {
            "enabled": True,
            "origins": ["*"]
        }
    }
}
```

#### Type Detection
```python
def detect_api_type(transactions: List[Transaction]) -> str:
    """Detect API type from transactions."""
    
    soap_count = sum(1 for t in transactions if t.has_soap_action)
    rest_count = sum(1 for t in transactions if t.is_rest)
    
    if soap_count > rest_count:
        return "soap"
    elif rest_count > 0:
        return "openapi"
    else:
        return "custom"
```

## Upload Pipeline

### 1. Pre-upload Validation

#### Token Validation
```python
def validate_api_token(token: str) -> bool:
    """Validate WireMock Cloud API token."""
    try:
        response = requests.get(
            "https://api.wiremock.cloud/v1/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except Exception:
        return False
```

#### Project Validation
```python
def validate_project_access(token: str, project_id: str) -> bool:
    """Validate access to WireMock Cloud project."""
    try:
        response = requests.get(
            f"https://api.wiremock.cloud/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200
    except Exception:
        return False
```

### 2. MockAPI Creation/Retrieval

#### Create New MockAPI
```python
def create_mock_api(client: WireMockCloudClient, metadata: VSIMetadata) -> Dict:
    """Create new MockAPI in WireMock Cloud."""
    
    mockapi_data = {
        "name": metadata.service_name,
        "description": metadata.description,
        "type": metadata.api_type,
        "settings": DEFAULT_MOCKAPI_CONFIG["settings"]
    }
    
    response = client.session.post(
        f"{client.base_url}/v1/projects/{client.project_id}/mockapis",
        json=mockapi_data
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        raise ConversionError(f"Failed to create MockAPI: {response.text}")
```

#### Retrieve Existing MockAPI
```python
def get_mock_api(client: WireMockCloudClient, mockapi_id: str) -> Dict:
    """Retrieve existing MockAPI from WireMock Cloud."""
    
    response = client.session.get(
        f"{client.base_url}/v1/projects/{client.project_id}/mockapis/{mockapi_id}"
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise ConversionError(f"Failed to retrieve MockAPI: {response.text}")
```

### 3. Stub Import

#### Convert Stubs for Import
```python
def convert_stubs_for_import(stubs: List[Dict]) -> List[Dict]:
    """Convert WireMock stubs to WireMock Cloud import format."""
    
    cloud_stubs = []
    for stub in stubs:
        cloud_stub = {
            "request": stub["request"],
            "response": stub["response"]
        }
        
        # Add priority if present
        if "priority" in stub:
            cloud_stub["priority"] = stub["priority"]
        
        # Add metadata if present
        if "metadata" in stub:
            cloud_stub["metadata"] = stub["metadata"]
        
        # Add name based on transaction ID
        if "metadata" in stub and "devtest_transaction_id" in stub["metadata"]:
            cloud_stub["name"] = stub["metadata"]["devtest_transaction_id"]
        
        cloud_stubs.append(cloud_stub)
    
    return cloud_stubs
```

#### Import Stubs to MockAPI
```python
def import_stubs_to_mockapi(
    client: WireMockCloudClient, 
    mockapi_id: str, 
    stubs: List[Dict]
) -> Dict:
    """Import stubs to existing MockAPI."""
    
    import_data = {
        "stubs": stubs,
        "strategy": "replace"  # or "merge", "append"
    }
    
    response = client.session.post(
        f"{client.base_url}/v1/projects/{client.project_id}/mockapis/{mockapi_id}/stubs/import",
        json=import_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise ConversionError(f"Failed to import stubs: {response.text}")
```

## Error Handling & Recovery

### 1. Upload Errors

#### Common Error Scenarios
1. **Invalid API Token**: Token expired or incorrect
2. **Network Issues**: Connection timeout or DNS failure
3. **Permission Denied**: Insufficient permissions for project
4. **MockAPI Creation Failed**: Name conflict or validation error
5. **Stub Import Failed**: Invalid stub format or size limit

#### Error Recovery Strategies
```python
class UploadErrorHandler:
    """Handle upload errors and provide recovery options."""
    
    def handle_token_error(self, error: Exception) -> str:
        """Handle API token errors."""
        return "Please check your API token and try again."
    
    def handle_network_error(self, error: Exception) -> str:
        """Handle network connectivity errors."""
        return "Please check your internet connection and try again."
    
    def handle_permission_error(self, error: Exception) -> str:
        """Handle permission errors."""
        return "Please check your WireMock Cloud permissions."
    
    def handle_naming_conflict(self, error: Exception) -> str:
        """Handle MockAPI naming conflicts."""
        return "Please specify a different project name using --project-name."
```

### 2. Retry Logic

#### Exponential Backoff
```python
def upload_with_retry(
    upload_func: Callable, 
    max_retries: int = 3, 
    base_delay: float = 1.0
) -> Any:
    """Upload with exponential backoff retry logic."""
    
    for attempt in range(max_retries):
        try:
            return upload_func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

## Progress Reporting

### 1. Upload Progress

#### Progress Indicators
```python
class UploadProgress:
    """Track and report upload progress."""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
    
    def update(self, step_name: str):
        """Update progress and log current step."""
        self.current_step += 1
        elapsed = time.time() - self.start_time
        
        logger.info(f"Upload progress: {self.current_step}/{self.total_steps} - {step_name}")
        
        if self.current_step == self.total_steps:
            logger.info(f"Upload completed in {elapsed:.2f} seconds")
```

### 2. Result Reporting

#### Success Report
```python
def generate_upload_report(
    mockapi_id: str, 
    stubs_count: int, 
    metadata: VSIMetadata
) -> Dict:
    """Generate upload success report."""
    
    return {
        "status": "success",
        "mockapi_id": mockapi_id,
        "mockapi_name": metadata.service_name,
        "stubs_imported": stubs_count,
        "upload_time": datetime.now().isoformat(),
        "metadata": {
            "source_file": metadata.filename,
            "source_version": metadata.source_version,
            "api_type": metadata.api_type
        }
    }
```

## Security Considerations

### 1. Token Security

#### Secure Token Handling
```python
class SecureTokenManager:
    """Manage API tokens securely."""
    
    def __init__(self):
        self.token = None
    
    def set_token(self, token: str):
        """Set token without logging."""
        self.token = token
    
    def get_token(self) -> str:
        """Get token without exposing in logs."""
        return self.token
    
    def validate_token(self) -> bool:
        """Validate token without exposing it."""
        # Implementation that doesn't log the token
        pass
```

#### Token Sources (Priority Order)
1. **Command line**: `--api-token`
2. **Environment variable**: `WIREMOCK_CLOUD_API_TOKEN`
3. **Configuration file**: `wiremock_cloud_api.api_key`
4. **Interactive prompt**: Ask user for token

### 2. Data Privacy

#### Sensitive Data Handling
- **Never log tokens**: Tokens are never logged or displayed
- **Mask sensitive data**: Replace tokens with `***` in error messages
- **Secure storage**: Use secure configuration management
- **Access control**: Respect WireMock Cloud permissions

## Performance Optimization

### 1. Upload Efficiency

#### Batch Upload
```python
def upload_stubs_in_batches(
    stubs: List[Dict], 
    batch_size: int = 100
) -> List[Dict]:
    """Upload stubs in batches for better performance."""
    
    results = []
    for i in range(0, len(stubs), batch_size):
        batch = stubs[i:i + batch_size]
        result = import_stubs_to_mockapi(client, mockapi_id, batch)
        results.append(result)
    
    return results
```

#### Compression
```python
def compress_stubs_for_upload(stubs: List[Dict]) -> bytes:
    """Compress stubs for efficient upload."""
    import gzip
    import json
    
    data = json.dumps(stubs).encode('utf-8')
    return gzip.compress(data)
```

### 2. Memory Management

#### Streaming Upload
```python
def stream_upload_large_stubs(
    stubs: List[Dict], 
    chunk_size: int = 1024
) -> None:
    """Stream upload for large stub collections."""
    
    for i in range(0, len(stubs), chunk_size):
        chunk = stubs[i:i + chunk_size]
        upload_chunk(chunk)
        # Clear chunk from memory
        del chunk
```

## Configuration Management

### 1. Upload Configuration

#### Default Settings
```yaml
# vsi2wm.yaml
wiremock_cloud_api:
  auto_upload: false
  api_key: null
  project_id: null
  environment: default
  upload_settings:
    batch_size: 100
    retry_attempts: 3
    timeout: 30
    compression: true
  naming:
    strategy: "filename"  # filename, custom, auto
    conflict_resolution: "version"  # version, timestamp, error
```

### 2. Environment-Specific Configs

#### Development
```yaml
# dev.yaml
wiremock_cloud_api:
  auto_upload: true
  environment: development
  upload_settings:
    batch_size: 50
    retry_attempts: 1
```

#### Production
```yaml
# prod.yaml
wiremock_cloud_api:
  auto_upload: true
  environment: production
  upload_settings:
    batch_size: 200
    retry_attempts: 5
    timeout: 60
```

## Testing Strategy

### 1. Unit Tests

#### MockAPI Creation Tests
```python
def test_create_mock_api_success():
    """Test successful MockAPI creation."""
    metadata = VSIMetadata(Path("test.vsi"))
    metadata.service_name = "Test API"
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": "mock_123"}
        
        result = create_mock_api(client, metadata)
        assert result["id"] == "mock_123"
```

#### Upload Error Tests
```python
def test_upload_with_retry():
    """Test upload retry logic."""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = [
            requests.exceptions.ConnectionError(),
            requests.exceptions.ConnectionError(),
            Mock(status_code=200, json=lambda: {"success": True})
        ]
        
        result = upload_with_retry(upload_func, max_retries=3)
        assert result["success"] is True
```

### 2. Integration Tests

#### End-to-End Upload Tests
```python
def test_end_to_end_upload():
    """Test complete upload workflow."""
    # Test with real WireMock Cloud API (using test tokens)
    # Test MockAPI creation, stub import, and validation
    pass
```

#### Error Recovery Tests
```python
def test_error_recovery():
    """Test error handling and recovery."""
    # Test various error scenarios and recovery strategies
    pass
```

## Future Enhancements

### 1. Advanced Features

#### MockAPI Versioning
- **Version management**: Track MockAPI versions
- **Rollback capability**: Revert to previous versions
- **Change tracking**: Monitor stub changes over time

#### Collaboration Features
- **Team sharing**: Share MockAPIs with team members
- **Access control**: Granular permission management
- **Activity logging**: Track who made changes

#### Advanced Analytics
- **Usage tracking**: Monitor MockAPI usage
- **Performance metrics**: Track response times
- **Error reporting**: Monitor stub failures

### 2. Performance Improvements

#### Parallel Uploads
- **Concurrent uploads**: Upload multiple MockAPIs simultaneously
- **Background processing**: Non-blocking upload operations
- **Progress tracking**: Real-time upload progress

#### Caching
- **Token caching**: Cache validated tokens
- **Metadata caching**: Cache extracted metadata
- **Upload caching**: Cache successful uploads
