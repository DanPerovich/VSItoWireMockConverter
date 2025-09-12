"""WireMock Cloud integration for VSI to WireMock converter."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from vsi2wm.exceptions import ConversionError

logger = logging.getLogger(__name__)


class WireMockCloudClient:
    """Client for WireMock Cloud API operations."""
    
    def __init__(self, api_key: str, project_id: str, environment: str = "default"):
        """Initialize WireMock Cloud client."""
        self.api_key = api_key
        self.project_id = project_id
        self.environment = environment
        self.base_url = "https://api.wiremock.cloud"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        })
    
    def upload_stubs(self, stubs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload stubs to WireMock Cloud."""
        url = f"{self.base_url}/v1/projects/{self.project_id}/environments/{self.environment}/stubs"
        
        try:
            response = self.session.post(url, json={"stubs": stubs})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to upload stubs to WireMock Cloud: {e}", exit_code=1)
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information from WireMock Cloud."""
        url = f"{self.base_url}/v1/projects/{self.project_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to get project info from WireMock Cloud: {e}", exit_code=1)
    
    def list_environments(self) -> List[Dict[str, Any]]:
        """List environments for the project."""
        url = f"{self.base_url}/v1/projects/{self.project_id}/environments"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json().get("environments", [])
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to list environments from WireMock Cloud: {e}", exit_code=1)
    
    def create_mock_api(self, name: str, description: str = "", tags: List[str] = None) -> Dict[str, Any]:
        """Create a new MockAPI in WireMock Cloud."""
        url = f"{self.base_url}/v1/mock-apis"
        
        payload = {
            "mockApi": {
                "name": name,
                "description": description,
                "tags": tags or [],
            }
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to create MockAPI in WireMock Cloud: {e}", exit_code=1)
    
    def get_mock_api(self, mock_api_id: str) -> Dict[str, Any]:
        """Get an existing MockAPI by ID."""
        url = f"{self.base_url}/v1/mock-apis/{mock_api_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to get MockAPI from WireMock Cloud: {e}", exit_code=1)
    
    def list_mock_apis(self) -> List[Dict[str, Any]]:
        """List all MockAPIs accessible to the user."""
        url = f"{self.base_url}/v1/mock-apis"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json().get("mockApis", [])
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to list MockAPIs from WireMock Cloud: {e}", exit_code=1)
    
    def update_mock_api(self, mock_api_id: str, name: str = None, description: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """Update an existing MockAPI."""
        url = f"{self.base_url}/v1/mock-apis/{mock_api_id}"
        
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if tags is not None:
            payload["tags"] = tags
        
        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to update MockAPI in WireMock Cloud: {e}", exit_code=1)
    
    def delete_mock_api(self, mock_api_id: str) -> Dict[str, Any]:
        """Delete a MockAPI."""
        url = f"{self.base_url}/v1/mock-apis/{mock_api_id}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to delete MockAPI from WireMock Cloud: {e}", exit_code=1)


def convert_to_wiremock_cloud_format(stubs: List[Dict[str, Any]], source_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Convert WireMock stubs to WireMock Cloud import format."""
    import uuid
    
    cloud_stubs = []
    
    for i, stub in enumerate(stubs):
        # WireMock Cloud import format requires specific fields
        cloud_stub = {
            "id": str(uuid.uuid4()),  # Required: unique ID for each mapping
            "name": _generate_cloud_stub_name(stub, i),
            "request": stub["request"],
            "response": stub["response"],
            "persistent": True,  # Required: makes the mapping persistent
        }
        
        # Add priority if present
        if "priority" in stub:
            cloud_stub["priority"] = stub["priority"]
        
        # Enhanced metadata for Cloud format
        cloud_metadata = {}
        if "metadata" in stub:
            cloud_metadata.update(stub["metadata"])
        
        # Add Cloud-specific metadata
        cloud_metadata["cloud_format"] = True
        cloud_metadata["stub_index"] = i
        cloud_metadata["generated_timestamp"] = _get_current_timestamp()
        
        # Add source metadata if available
        if source_metadata:
            cloud_metadata["source_version"] = source_metadata.get("source_version")
            cloud_metadata["source_build"] = source_metadata.get("build_number")
        
        cloud_stub["metadata"] = cloud_metadata
        
        # Add Cloud-specific formatting
        cloud_stub = _enhance_cloud_stub_formatting(cloud_stub)
        
        cloud_stubs.append(cloud_stub)
    
    return cloud_stubs


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def _generate_cloud_stub_name(stub: Dict[str, Any], index: int) -> str:
    """Generate a meaningful name for Cloud stub."""
    # Try to extract meaningful name from metadata
    if "metadata" in stub and "devtest_transaction_id" in stub["metadata"]:
        transaction_id = stub["metadata"]["devtest_transaction_id"]
        # Clean up transaction ID for Cloud naming
        name = transaction_id.replace("#", "_").replace("/", "_").replace(" ", "_")
        return name
    
    # Fallback to method + path
    request = stub.get("request", {})
    method = request.get("method", "UNKNOWN")
    url_path = request.get("urlPath") or request.get("urlPathPattern", "")
    
    if url_path:
        # Clean up URL path for naming
        clean_path = url_path.replace("/", "_").replace("{", "").replace("}", "").replace("*", "wildcard")
        return f"{method}_{clean_path}_{index}"
    
    return f"stub_{index}"


def _enhance_cloud_stub_formatting(stub: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance stub formatting for Cloud format."""
    # Ensure response has proper Content-Type headers for Cloud
    response = stub.get("response", {})
    if "headers" not in response:
        response["headers"] = {}
    
    # Add Content-Type based on response body type
    if "jsonBody" in response and "Content-Type" not in response["headers"]:
        response["headers"]["Content-Type"] = "application/json"
    elif "body" in response and "Content-Type" not in response["headers"]:
        body = response["body"]
        if isinstance(body, str):
            if body.strip().startswith("{") or body.strip().startswith("["):
                response["headers"]["Content-Type"] = "application/json"
            elif body.strip().startswith("<"):
                response["headers"]["Content-Type"] = "application/xml"
            else:
                response["headers"]["Content-Type"] = "text/plain"
    
    stub["response"] = response
    return stub


def create_wiremock_cloud_export(
    stubs: List[Dict[str, Any]], 
    output_dir: Path,
    cloud_config: Optional[Dict[str, Any]] = None,
    source_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create enhanced WireMock Cloud export format."""
    # Convert stubs to Cloud format with enhanced metadata
    cloud_stubs = convert_to_wiremock_cloud_format(stubs, source_metadata)
    
    # Enhanced export metadata
    export_metadata = {
        "generated_by": "vsi2wm",
        "generated_version": "2.0",  # Phase 2 enhanced version
        "total_stubs": len(cloud_stubs),
        "generated_timestamp": _get_current_timestamp(),
        "format_version": "1.0",
    }
    
    # Add source metadata if available
    if source_metadata:
        export_metadata.update({
            "source_file": source_metadata.get("source_file"),
            "source_version": source_metadata.get("source_version"),
            "source_build": source_metadata.get("build_number"),
            "transactions_count": source_metadata.get("transactions_count"),
            "variants_count": source_metadata.get("variants_count"),
        })
    
    # Create enhanced export structure
    export_data = {
        "version": "2.0",
        "format": "wiremock-cloud",
        "metadata": export_metadata,
        "stubs": cloud_stubs,
    }
    
    # Add WireMock Cloud configuration if provided
    if cloud_config:
        export_data["wiremock_cloud"] = cloud_config
    
    # Add Cloud-specific enhancements
    export_data["cloud_features"] = {
        "enhanced_naming": True,
        "automatic_content_type": True,
        "metadata_preservation": True,
        "timestamp_tracking": True,
    }
    
    # Validate export data
    _validate_cloud_export_data(export_data)
    
    # Write export file with enhanced formatting
    export_file = output_dir / "wiremock-cloud-export.json"
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created enhanced WireMock Cloud export: {export_file}")
    logger.info(f"Export contains {len(cloud_stubs)} stubs with enhanced metadata")
    
    return {
        "export_file": str(export_file),
        "stubs_count": len(cloud_stubs),
        "cloud_format": True,
        "enhanced_version": "2.0",
        "metadata_included": bool(source_metadata),
    }


def _validate_cloud_export_data(export_data: Dict[str, Any]) -> None:
    """Validate Cloud export data structure."""
    required_fields = ["version", "format", "metadata", "stubs"]
    for field in required_fields:
        if field not in export_data:
            raise ConversionError(f"Missing required Cloud export field: {field}", exit_code=1)
    
    # Validate stubs structure
    stubs = export_data["stubs"]
    if not isinstance(stubs, list):
        raise ConversionError("Cloud export stubs must be a list", exit_code=1)
    
    for i, stub in enumerate(stubs):
        if not isinstance(stub, dict):
            raise ConversionError(f"Stub {i} must be a dictionary", exit_code=1)
        
        if "request" not in stub or "response" not in stub:
            raise ConversionError(f"Stub {i} missing required request/response fields", exit_code=1)
        
        if "name" not in stub:
            logger.warning(f"Stub {i} missing name field")
    
    logger.debug(f"Cloud export validation passed for {len(stubs)} stubs")


def upload_to_wiremock_cloud(
    stubs: List[Dict[str, Any]],
    cloud_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Upload stubs directly to WireMock Cloud."""
    # Validate cloud configuration
    required_fields = ["api_key", "project_id"]
    for field in required_fields:
        if field not in cloud_config:
            raise ConversionError(f"Missing required WireMock Cloud field: {field}", exit_code=1)
    
    # Initialize client
    client = WireMockCloudClient(
        api_key=cloud_config["api_key"],
        project_id=cloud_config["project_id"],
        environment=cloud_config.get("environment", "default"),
    )
    
    # Convert stubs to Cloud format
    cloud_stubs = convert_to_wiremock_cloud_format(stubs)
    
    # Upload to WireMock Cloud
    logger.info(f"Uploading {len(cloud_stubs)} stubs to WireMock Cloud...")
    result = client.upload_stubs(cloud_stubs)
    
    logger.info("Successfully uploaded stubs to WireMock Cloud")
    
    return {
        "uploaded_stubs": len(cloud_stubs),
        "wiremock_cloud_response": result,
        "project_id": cloud_config["project_id"],
        "environment": cloud_config.get("environment", "default"),
    }


def validate_wiremock_cloud_config(config: Dict[str, Any]) -> bool:
    """Validate WireMock Cloud configuration."""
    required_fields = ["api_key", "project_id"]
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required WireMock Cloud field: {field}")
            return False
        
        if not config[field]:
            logger.error(f"WireMock Cloud field {field} cannot be empty")
            return False
    
    # Validate API key format (basic check)
    # Check for WireMock Cloud format (should start with 'wm' prefix)
    if not config["api_key"].startswith("wm"):
        logger.warning("WireMock Cloud API key should start with 'wm' (e.g., 'wm_', 'wmcp_', etc.)")
    
    return True


def test_wiremock_cloud_connection(cloud_config: Dict[str, Any]) -> Dict[str, Any]:
    """Test WireMock Cloud connection and credentials."""
    if not validate_wiremock_cloud_config(cloud_config):
        raise ConversionError("Invalid WireMock Cloud configuration", exit_code=1)
    
    client = WireMockCloudClient(
        api_key=cloud_config["api_key"],
        project_id=cloud_config["project_id"],
        environment=cloud_config.get("environment", "default"),
    )
    
    try:
        # Test by listing MockAPIs (user-scoped endpoint)
        mock_apis = client.list_mock_apis()
        
        return {
            "connected": True,
            "mock_apis_count": len(mock_apis),
            "tested_endpoint": "mock-apis",
        }
    except Exception as e:
        raise ConversionError(f"Failed to connect to WireMock Cloud: {e}", exit_code=1)


def extract_mockapi_metadata(source_file: Path, source_metadata: Optional[Dict[str, Any]] = None, client: Optional[WireMockCloudClient] = None) -> Dict[str, Any]:
    """Extract MockAPI metadata from VSI source file and metadata."""
    base_name = _generate_mockapi_name(source_file)
    
    # Generate unique name if client is provided and create_mockapi is True
    if client is not None:
        unique_name = _generate_unique_mockapi_name(client, base_name)
    else:
        unique_name = base_name
    
    metadata = {
        "name": unique_name,
        "description": _generate_mockapi_description(source_file, source_metadata),
        "tags": _generate_mockapi_tags(source_file, source_metadata),
    }
    
    # Add source information
    if source_metadata:
        metadata["source_version"] = source_metadata.get("source_version")
        metadata["source_build"] = source_metadata.get("build_number")
        metadata["source_file"] = str(source_file)
    
    return metadata


def _generate_mockapi_name(source_file: Path) -> str:
    """Generate base MockAPI name from VSI filename."""
    # Clean up filename for MockAPI naming
    name = source_file.stem.lower()
    
    # Replace common separators with hyphens
    name = name.replace("_", "-").replace(" ", "-").replace(".", "-")
    
    # Remove any non-alphanumeric characters except hyphens
    import re
    name = re.sub(r'[^a-z0-9\-]', '', name)
    
    # Ensure it starts and ends with alphanumeric
    name = re.sub(r'^\-+|\-+$', '', name)
    
    # Fallback if name becomes empty
    if not name:
        name = "vsi-mockapi"
    
    return name


def _generate_unique_mockapi_name(client: WireMockCloudClient, base_name: str) -> str:
    """Generate a unique MockAPI name by checking for conflicts and adding suffix if needed."""
    # First try the base name
    if not _mockapi_name_exists(client, base_name):
        return base_name
    
    # If base name exists, try with timestamp suffix
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    timestamped_name = f"{base_name}-{timestamp}"
    
    if not _mockapi_name_exists(client, timestamped_name):
        return timestamped_name
    
    # If timestamped name also exists (unlikely), try with random suffix
    import random
    import string
    while True:
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        unique_name = f"{base_name}-{random_suffix}"
        if not _mockapi_name_exists(client, unique_name):
            return unique_name


def _mockapi_name_exists(client: WireMockCloudClient, name: str) -> bool:
    """Check if a MockAPI with the given name already exists."""
    try:
        mock_apis = client.list_mock_apis()
        for mock_api in mock_apis:
            if mock_api.get("name") == name:
                return True
        return False
    except Exception:
        # If we can't check, assume it doesn't exist to avoid blocking
        return False


def _generate_mockapi_description(source_file: Path, source_metadata: Optional[Dict[str, Any]] = None) -> str:
    """Generate MockAPI description from source file and metadata."""
    description_parts = []
    
    # Add source file info
    description_parts.append(f"Generated from VSI file: {source_file.name}")
    
    # Add version info if available
    if source_metadata:
        version = source_metadata.get("source_version")
        build = source_metadata.get("build_number")
        if version:
            description_parts.append(f"Source version: {version}")
        if build and build != version:
            description_parts.append(f"Build: {build}")
    
    # Add generation timestamp
    from datetime import datetime
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    description_parts.append(f"Generated: {timestamp}")
    
    return " | ".join(description_parts)


def _generate_mockapi_tags(source_file: Path, source_metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """Generate MockAPI tags from source file and metadata."""
    tags = ["vsi-generated", "automated"]
    
    # Add file-based tags
    filename = source_file.stem.lower()
    if "rest" in filename or "api" in filename:
        tags.append("rest-api")
    elif "soap" in filename:
        tags.append("soap-service")
    elif "service" in filename:
        tags.append("service")
    
    # Add version-based tags
    if source_metadata:
        version = source_metadata.get("source_version")
        if version:
            # Add major version as tag
            try:
                major_version = version.split(".")[0]
                tags.append(f"v{major_version}")
            except (IndexError, ValueError):
                pass
    
    return tags


def find_or_create_mockapi(
    client: WireMockCloudClient,
    mockapi_name: str,
    mockapi_metadata: Dict[str, Any],
    create_if_not_found: bool = True
) -> Dict[str, Any]:
    """Find existing MockAPI by name or create new one based on create_if_not_found flag."""
    try:
        if create_if_not_found:
            # Always create a new MockAPI (ignore existing ones)
            logger.info(f"Creating new MockAPI: {mockapi_name}")
            new_mock_api = client.create_mock_api(
                name=mockapi_metadata["name"],
                description=mockapi_metadata["description"],
                tags=mockapi_metadata["tags"]
            )
            # Extract ID from nested response structure
            mock_api_id = new_mock_api.get('mockApi', {}).get('id')
            logger.info(f"Created MockAPI: {mockapi_name} (ID: {mock_api_id})")
            return new_mock_api
        else:
            # Only use existing MockAPI, fail if not found
            mock_apis = client.list_mock_apis()
            
            # Look for existing MockAPI with same name
            for mock_api in mock_apis:
                if mock_api.get("name") == mockapi_name:
                    logger.info(f"Found existing MockAPI: {mockapi_name} (ID: {mock_api.get('id')})")
                    return mock_api
            
            # MockAPI not found and creation is disabled
            raise ConversionError(f"MockAPI '{mockapi_name}' not found and creation disabled", exit_code=1)
            
    except Exception as e:
        raise ConversionError(f"Failed to find or create MockAPI '{mockapi_name}': {e}", exit_code=1)


class AutoUploadManager:
    """Manages automatic upload workflow to WireMock Cloud."""
    
    def __init__(self, cloud_config: Dict[str, Any]):
        """Initialize AutoUploadManager with cloud configuration."""
        self.cloud_config = cloud_config
        self.client = WireMockCloudClient(
            api_key=cloud_config["api_key"],
            project_id=cloud_config["project_id"],
            environment=cloud_config.get("environment", "default"),
        )
    
    def upload_stubs_to_mockapi(
        self,
        stubs: List[Dict[str, Any]],
        source_file: Path,
        source_metadata: Optional[Dict[str, Any]] = None,
        mockapi_name: Optional[str] = None,
        create_mockapi: bool = True
    ) -> Dict[str, Any]:
        """Upload stubs to MockAPI with automatic MockAPI management."""
        try:
            # Extract MockAPI metadata
            if mockapi_name:
                # Use provided name
                mockapi_metadata = extract_mockapi_metadata(source_file, source_metadata, self.client if create_mockapi else None)
                mockapi_metadata["name"] = mockapi_name
            else:
                # Auto-generate name from source file
                mockapi_metadata = extract_mockapi_metadata(source_file, source_metadata, self.client if create_mockapi else None)
            
            logger.info(f"Uploading stubs to MockAPI: {mockapi_metadata['name']}")
            
            # Find or create MockAPI
            mock_api = find_or_create_mockapi(
                self.client,
                mockapi_metadata["name"],
                mockapi_metadata,
                create_if_not_found=create_mockapi
            )
            
            # Extract ID from nested response structure
            mock_api_id = mock_api.get("mockApi", {}).get("id") or mock_api.get("id")
            if not mock_api_id:
                raise ConversionError("MockAPI ID not found in response", exit_code=1)
            
            # Convert stubs to Cloud format
            cloud_stubs = convert_to_wiremock_cloud_format(stubs, source_metadata)
            
            # Upload stubs to MockAPI
            logger.info(f"Uploading {len(cloud_stubs)} stubs to MockAPI {mock_api_id}")
            upload_result = self._upload_stubs_to_mockapi(mock_api_id, cloud_stubs)
            
            return {
                "success": True,
                "mock_api": mock_api,
                "mock_api_id": mock_api_id,
                "uploaded_stubs": len(cloud_stubs),
                "upload_result": upload_result,
                "mockapi_metadata": mockapi_metadata,
            }
            
        except Exception as e:
            logger.error(f"Auto-upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "mock_api": None,
                "mock_api_id": None,
                "uploaded_stubs": 0,
            }
    
    def upload_stubs_to_existing_mockapi(
        self,
        stubs: List[Dict[str, Any]],
        source_file: Path,
        source_metadata: Optional[Dict[str, Any]] = None,
        mockapi_id: str = None
    ) -> Dict[str, Any]:
        """Upload stubs to existing MockAPI by ID and optionally update MockAPI metadata."""
        try:
            logger.info(f"Uploading stubs to existing MockAPI: {mockapi_id}")
            
            # Get existing MockAPI to verify it exists
            try:
                existing_mockapi = self.client.get_mock_api(mockapi_id)
                logger.info(f"Found existing MockAPI: {existing_mockapi.get('name', 'Unknown')}")
            except Exception as e:
                raise ConversionError(f"MockAPI {mockapi_id} not found or inaccessible: {e}", exit_code=1)
            
            # Extract MockAPI metadata for potential update
            mockapi_metadata = extract_mockapi_metadata(source_file, source_metadata, self.client)
            
            # Update MockAPI metadata if it has changed
            should_update_metadata = False
            update_payload = {}
            
            if mockapi_metadata.get("name") != existing_mockapi.get("name"):
                update_payload["name"] = mockapi_metadata["name"]
                should_update_metadata = True
                
            if mockapi_metadata.get("description") != existing_mockapi.get("description"):
                update_payload["description"] = mockapi_metadata["description"]
                should_update_metadata = True
                
            if mockapi_metadata.get("tags") != existing_mockapi.get("tags"):
                update_payload["tags"] = mockapi_metadata["tags"]
                should_update_metadata = True
            
            if should_update_metadata:
                logger.info(f"Updating MockAPI metadata: {update_payload}")
                updated_mockapi = self.client.update_mock_api(
                    mockapi_id,
                    name=update_payload.get("name"),
                    description=update_payload.get("description"),
                    tags=update_payload.get("tags")
                )
                logger.info("MockAPI metadata updated successfully")
            else:
                updated_mockapi = existing_mockapi
                logger.info("MockAPI metadata unchanged, skipping update")
            
            # Convert stubs to Cloud format
            cloud_stubs = convert_to_wiremock_cloud_format(stubs, source_metadata)
            
            # Upload stubs to MockAPI
            logger.info(f"Uploading {len(cloud_stubs)} stubs to MockAPI {mockapi_id}")
            upload_result = self._upload_stubs_to_mockapi(mockapi_id, cloud_stubs)
            
            return {
                "success": True,
                "mock_api": updated_mockapi,
                "mock_api_id": mockapi_id,
                "uploaded_stubs": len(cloud_stubs),
                "upload_result": upload_result,
                "mockapi_metadata": mockapi_metadata,
                "metadata_updated": should_update_metadata,
            }
            
        except Exception as e:
            logger.error(f"Auto-upload to existing MockAPI failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "mock_api": None,
                "mock_api_id": mockapi_id,
                "uploaded_stubs": 0,
            }
    
    def _upload_stubs_to_mockapi(self, mock_api_id: str, cloud_stubs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload stubs to specific MockAPI."""
        url = f"{self.client.base_url}/v1/mock-apis/{mock_api_id}/mappings/import"
        
        try:
            response = self.client.session.post(url, json={"mappings": cloud_stubs})
            response.raise_for_status()
            
            # Handle empty response (common for successful imports)
            if response.content:
                return response.json()
            else:
                # Return success indicator for empty response
                return {"success": True, "message": "Stubs imported successfully"}
                
        except requests.exceptions.RequestException as e:
            raise ConversionError(f"Failed to upload stubs to MockAPI {mock_api_id}: {e}", exit_code=1)
    
    def validate_upload_prerequisites(self) -> Dict[str, Any]:
        """Validate that all prerequisites for upload are met."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        
        # Validate cloud configuration
        if not validate_wiremock_cloud_config(self.cloud_config):
            validation_result["valid"] = False
            validation_result["errors"].append("Invalid WireMock Cloud configuration")
        
        # Test connection
        try:
            connection_test = test_wiremock_cloud_connection(self.cloud_config)
            if not connection_test.get("connected"):
                validation_result["valid"] = False
                validation_result["errors"].append("Failed to connect to WireMock Cloud")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Connection test failed: {e}")
        
        return validation_result


def get_api_token_from_sources(
    cli_token: Optional[str] = None,
    config_token: Optional[str] = None,
    env_var: str = "WIREMOCK_CLOUD_API_TOKEN"
) -> Optional[str]:
    """Get API token from various sources in order of priority."""
    import os
    
    # Priority order: CLI argument > config file > environment variable
    if cli_token:
        logger.debug("Using API token from CLI argument")
        return cli_token
    
    if config_token:
        logger.debug("Using API token from config file")
        return config_token
    
    env_token = os.getenv(env_var)
    if env_token:
        logger.debug(f"Using API token from environment variable {env_var}")
        return env_token
    
    return None


def validate_api_token(api_token: str) -> Dict[str, Any]:
    """Validate API token format and basic structure."""
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }
    
    if not api_token:
        validation_result["valid"] = False
        validation_result["errors"].append("API token is empty")
        return validation_result
    
    if not isinstance(api_token, str):
        validation_result["valid"] = False
        validation_result["errors"].append("API token must be a string")
        return validation_result
    
    # Check minimum length
    if len(api_token) < 10:
        validation_result["valid"] = False
        validation_result["errors"].append("API token appears too short")
        return validation_result
    
    # Check for WireMock Cloud format (should start with 'wm' prefix)
    if not api_token.startswith("wm"):
        validation_result["warnings"].append("API token should start with 'wm' (e.g., 'wm_', 'wmcp_', etc.) for WireMock Cloud")
    
    # Check for common issues
    if " " in api_token:
        validation_result["warnings"].append("API token contains spaces - this may cause issues")
    
    return validation_result


def test_api_token_authentication(api_token: str, project_id: str, environment: str = "default") -> Dict[str, Any]:
    """Test API token authentication with WireMock Cloud."""
    test_config = {
        "api_key": api_token,
        "project_id": project_id,
        "environment": environment,
    }
    
    try:
        result = test_wiremock_cloud_connection(test_config)
        return {
            "authenticated": result.get("connected", False),
            "project_info": result.get("project_info"),
            "environments": result.get("environments"),
            "error": None,
        }
    except Exception as e:
        return {
            "authenticated": False,
            "project_info": None,
            "environments": None,
            "error": str(e),
        }


def create_cloud_config_from_sources(
    cli_args: Optional[Dict[str, Any]] = None,
    config_data: Optional[Dict[str, Any]] = None,
    source_file: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """Create cloud configuration from various sources."""
    cloud_config = {}
    
    cli_token = cli_args.get("api_token") if cli_args else None
    wiremock_cloud_config = config_data.get("wiremock_cloud") if config_data is not None else None
    config_token = wiremock_cloud_config.get("api_key") if wiremock_cloud_config is not None else None
    api_token = get_api_token_from_sources(cli_token, config_token)
    
    if not api_token:
        logger.debug("No API token found in any source")
        return None
    
    cloud_config["api_key"] = api_token
    
    # Get project ID (auto-derive from source file)
    project_id = None
    if source_file:
        # Auto-derive from source filename
        project_id = source_file.stem.lower().replace("_", "-").replace(" ", "-")
    
    if not project_id:
        logger.debug("No project ID found - using default")
        project_id = "default"
    
    cloud_config["project_id"] = project_id
    
    # Get environment
    environment = "default"
    if config_data is not None and wiremock_cloud_config is not None and wiremock_cloud_config.get("environment"):
        environment = wiremock_cloud_config["environment"]
    
    cloud_config["environment"] = environment
    
    return cloud_config
