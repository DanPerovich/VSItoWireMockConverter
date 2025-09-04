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


def convert_to_wiremock_cloud_format(stubs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert WireMock stubs to WireMock Cloud format."""
    cloud_stubs = []
    
    for stub in stubs:
        # WireMock Cloud uses a slightly different format
        cloud_stub = {
            "request": stub["request"],
            "response": stub["response"],
        }
        
        # Add priority if present
        if "priority" in stub:
            cloud_stub["priority"] = stub["priority"]
        
        # Add metadata if present
        if "metadata" in stub:
            cloud_stub["metadata"] = stub["metadata"]
        
        # Add name based on transaction ID if available
        if "metadata" in stub and "devtest_transaction_id" in stub["metadata"]:
            cloud_stub["name"] = stub["metadata"]["devtest_transaction_id"]
        
        cloud_stubs.append(cloud_stub)
    
    return cloud_stubs


def create_wiremock_cloud_export(
    stubs: List[Dict[str, Any]], 
    output_dir: Path,
    cloud_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create WireMock Cloud export format."""
    # Convert stubs to Cloud format
    cloud_stubs = convert_to_wiremock_cloud_format(stubs)
    
    # Create export structure
    export_data = {
        "version": "1.0",
        "format": "wiremock-cloud",
        "stubs": cloud_stubs,
        "metadata": {
            "generated_by": "vsi2wm",
            "total_stubs": len(cloud_stubs),
        }
    }
    
    # Add WireMock Cloud configuration if provided
    if cloud_config:
        export_data["wiremock_cloud"] = cloud_config
    
    # Write export file
    export_file = output_dir / "wiremock-cloud-export.json"
    with open(export_file, "w") as f:
        json.dump(export_data, f, indent=2)
    
    logger.info(f"Created WireMock Cloud export: {export_file}")
    
    return {
        "export_file": str(export_file),
        "stubs_count": len(cloud_stubs),
        "cloud_format": True,
    }


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
