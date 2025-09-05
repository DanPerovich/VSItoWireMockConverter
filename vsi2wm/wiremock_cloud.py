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
            "Authorization": f"Bearer {api_key}",
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


def convert_to_wiremock_cloud_format(stubs: List[Dict[str, Any]], source_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Convert WireMock stubs to WireMock Cloud format with enhanced metadata."""
    cloud_stubs = []
    
    for i, stub in enumerate(stubs):
        # WireMock Cloud uses a slightly different format
        cloud_stub = {
            "request": stub["request"],
            "response": stub["response"],
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
        
        # Enhanced naming strategy for Cloud format
        cloud_stub["name"] = _generate_cloud_stub_name(stub, i)
        
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
    if not config["api_key"].startswith("wm_"):
        logger.warning("WireMock Cloud API key should start with 'wm_'")
    
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
        # Test by getting project info
        project_info = client.get_project_info()
        environments = client.list_environments()
        
        return {
            "connected": True,
            "project_info": project_info,
            "environments": environments,
            "tested_environment": cloud_config.get("environment", "default"),
        }
    except Exception as e:
        raise ConversionError(f"Failed to connect to WireMock Cloud: {e}", exit_code=1)
