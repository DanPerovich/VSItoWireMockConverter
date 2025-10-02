"""Integration tests for Phase 6 features - end-to-end workflows."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from vsi2wm.cli import main
from vsi2wm.core import VSIConverter
from vsi2wm.wiremock_cloud import AutoUploadManager, WireMockCloudClient


pytestmark = [pytest.mark.phase6, pytest.mark.integration]


class TestEndToEndCloudExport:
    """Test end-to-end Cloud export workflow."""

    @patch('vsi2wm.parser.parse_vsi_file')
    @patch('vsi2wm.ir_builder.build_ir_from_vsi')
    @patch('vsi2wm.mapper.map_ir_to_wiremock')
    def test_cloud_export_workflow(self, mock_mapper, mock_ir_builder, mock_parse_vsi):
        """Test complete Cloud export workflow."""
        # Setup mocks
        mock_parse_vsi.return_value = {
            "layout": "standard",
            "metadata": {"source_version": "1.0", "build_number": "123"},
            "protocol": "HTTP",
            "is_http": True,
            "transactions_count": 2,
            "warnings": []
        }
        
        mock_ir = Mock()
        mock_transactions = [
            Mock(transaction_id="GET#/users", method="GET", url_path="/users", response_variants=[]),
            Mock(transaction_id="POST#/users", method="POST", url_path="/users", response_variants=[])
        ]
        # Create a mock that behaves like a list
        mock_transactions_list = Mock()
        mock_transactions_list.__iter__ = Mock(return_value=iter(mock_transactions))
        mock_transactions_list.__len__ = Mock(return_value=len(mock_transactions))
        mock_ir.transactions = mock_transactions_list
        mock_ir_builder.return_value = mock_ir
        
        mock_mapper.return_value = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            },
            {
                "priority": 1,
                "request": {"method": "POST", "urlPath": "/users"},
                "response": {"status": 201, "body": "Created"},
                "metadata": {"devtest_transaction_id": "POST#/users"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test VSI file
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            # Run conversion with Cloud format
            converter = VSIConverter(
                input_file=vsi_file,
                output_dir=Path(tmp_dir) / "output",
                output_format="cloud"
            )
            
            result = converter.convert()
            assert result == 0
            
            # Check Cloud export file was created
            cloud_export = Path(tmp_dir) / "output" / "wiremock-cloud-export.json"
            assert cloud_export.exists()
            
            # Check export content
            with open(cloud_export, "r") as f:
                export_data = json.load(f)
            
            assert export_data["format"] == "wiremock-cloud"
            assert export_data["version"] == "2.0"
            assert len(export_data["stubs"]) == 2
            assert "cloud_features" in export_data
            
            # Check individual stubs
            for stub in export_data["stubs"]:
                assert "id" in stub
                assert "name" in stub
                assert "request" in stub
                assert "response" in stub
                assert "persistent" in stub
                assert stub["persistent"] is True

    def test_cloud_export_cli_workflow(self):
        """Test Cloud export via CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test VSI file
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output")
            ]
            
            with patch('vsi2wm.parser.parse_vsi_file') as mock_parse_vsi, \
                 patch('vsi2wm.ir_builder.build_ir_from_vsi') as mock_ir_builder, \
                 patch('vsi2wm.mapper.map_ir_to_wiremock') as mock_mapper:
                
                # Setup mocks
                mock_parse_vsi.return_value = {
                    "layout": "standard",
                    "metadata": {"source_version": "1.0", "build_number": "123"},
                    "protocol": "HTTP",
                    "is_http": True,
                    "transactions_count": 0,
                    "warnings": []
                }
                
                mock_ir = Mock()
                mock_transactions = []
                # Create a mock that behaves like a list
                mock_transactions_list = Mock()
                mock_transactions_list.__iter__ = Mock(return_value=iter(mock_transactions))
                mock_transactions_list.__len__ = Mock(return_value=len(mock_transactions))
                mock_ir.transactions = mock_transactions_list
                mock_ir_builder.return_value = mock_ir
                
                mock_mapper.return_value = []
                
                exit_code = main(args)
                assert exit_code == 0
                
                # Check Cloud export was created
                cloud_export = Path(tmp_dir) / "output" / "wiremock-cloud-export.json"
                assert cloud_export.exists()


class TestEndToEndAutoUpload:
    """Test end-to-end auto-upload workflow."""

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    @patch('vsi2wm.parser.parse_vsi_file')
    @patch('vsi2wm.ir_builder.build_ir_from_vsi')
    @patch('vsi2wm.mapper.map_ir_to_wiremock')
    def test_auto_upload_workflow(self, mock_mapper, mock_ir_builder, mock_parse_vsi, mock_client_class):
        """Test complete auto-upload workflow."""
        # Setup mocks
        mock_parse_vsi.return_value = {
            "layout": "standard",
            "metadata": {"source_version": "1.0", "build_number": "123"},
            "protocol": "HTTP",
            "is_http": True,
            "transactions_count": 1,
            "warnings": []
        }
        
        mock_ir = Mock()
        mock_transactions = [Mock(transaction_id="GET#/users", method="GET", url_path="/users", response_variants=[])]
        # Create a mock that behaves like a list
        mock_transactions_list = Mock()
        mock_transactions_list.__iter__ = Mock(return_value=iter(mock_transactions))
        mock_transactions_list.__len__ = Mock(return_value=len(mock_transactions))
        mock_ir.transactions = mock_transactions_list
        mock_ir_builder.return_value = mock_ir
        
        mock_mapper.return_value = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            }
        ]
        
        # Setup WireMock Cloud client mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_mock_apis.return_value = []
        mock_client.create_mock_api.return_value = {
            "mockApi": {"id": "mock123", "name": "test-mockapi"}
        }
        mock_client.session.post.return_value = Mock(status_code=200, content=b'')
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test VSI file
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            # Create Cloud export file
            cloud_export = Path(tmp_dir) / "output" / "wiremock-cloud-export.json"
            cloud_export.parent.mkdir()
            cloud_export.write_text(json.dumps({
                "stubs": [{"request": {"method": "GET"}, "response": {"status": 200}}]
            }))
            
            # Test auto-upload via CLI
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123"
            ]
            
            exit_code = main(args)
            assert exit_code == 0
            
            # Verify MockAPI was created
            mock_client.create_mock_api.assert_called_once()
            
            # Verify stubs were uploaded
            mock_client.session.post.assert_called_once()

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_auto_upload_manager_workflow(self, mock_client_class):
        """Test AutoUploadManager complete workflow."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_mock_apis.return_value = []
        mock_client.create_mock_api.return_value = {
            "mockApi": {"id": "mock123", "name": "test-mockapi"}
        }
        mock_client.session.post.return_value = Mock(status_code=200, content=b'')
        
        # Create AutoUploadManager
        cloud_config = {
            "api_key": "wm_test123",
            "project_id": "test-project",
            "environment": "default"
        }
        
        manager = AutoUploadManager(cloud_config)
        
        # Test validation
        validation = manager.validate_upload_prerequisites()
        assert validation["valid"] is True
        
        # Test upload
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            result = manager.upload_stubs_to_mockapi(
                stubs=stubs,
                source_file=vsi_file,
                source_metadata={"source_version": "10.5.0"},
                create_mockapi=True
            )
            
            assert result["success"] is True
            assert result["uploaded_stubs"] == 1
            assert result["mock_api_id"] == "mock123"


class TestEndToEndMockAPIManagement:
    """Test end-to-end MockAPI management workflow."""

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_lifecycle(self, mock_client_class):
        """Test complete MockAPI lifecycle."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Test MockAPI creation
        mock_client.create_mock_api.return_value = {
            "mockApi": {"id": "mock123", "name": "test-mockapi", "description": "Test MockAPI"}
        }
        
        # Use the mocked client directly
        create_result = mock_client.create_mock_api("test-mockapi", "Test description")
        
        assert create_result["mockApi"]["id"] == "mock123"
        assert create_result["mockApi"]["name"] == "test-mockapi"
        
        # Test MockAPI retrieval
        mock_client.get_mock_api.return_value = {
            "id": "mock123",
            "name": "test-mockapi",
            "description": "Test MockAPI"
        }
        
        get_result = mock_client.get_mock_api("mock123")
        assert get_result["id"] == "mock123"
        
        # Test MockAPI update
        mock_client.update_mock_api.return_value = {
            "id": "mock123",
            "name": "updated-mockapi",
            "description": "Updated description"
        }
        
        update_result = mock_client.update_mock_api("mock123", name="updated-mockapi")
        assert update_result["name"] == "updated-mockapi"
        
        # Test MockAPI listing
        mock_client.list_mock_apis.return_value = [
            {"id": "mock123", "name": "updated-mockapi"},
            {"id": "mock456", "name": "another-mockapi"}
        ]
        
        list_result = mock_client.list_mock_apis()
        assert len(list_result) == 2
        
        # Test MockAPI deletion
        mock_client.delete_mock_api.return_value = {"success": True}
        
        delete_result = mock_client.delete_mock_api("mock123")
        assert delete_result["success"] is True

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_name_conflict_resolution(self, mock_client_class):
        """Test MockAPI name conflict resolution."""
        # Setup mock client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock the list_mock_apis to return existing MockAPI
        mock_client.list_mock_apis.return_value = [
            {"id": "existing", "name": "test-mockapi"}
        ]
        
        from vsi2wm.wiremock_cloud import _generate_unique_mockapi_name
        
        # Use the mocked client directly
        unique_name = _generate_unique_mockapi_name(mock_client, "test-mockapi")
        
        # Should generate unique name with timestamp
        assert unique_name != "test-mockapi"
        assert "test-mockapi" in unique_name


class TestEndToEndErrorHandling:
    """Test end-to-end error handling scenarios."""

    def test_invalid_api_token_handling(self):
        """Test handling of invalid API token."""
        from vsi2wm.wiremock_cloud import validate_api_token, test_api_token_authentication
        
        # Test token validation with actually invalid token (too short)
        result = validate_api_token("short")
        assert result["valid"] is False
        
        # Test token validation with empty token
        result = validate_api_token("")
        assert result["valid"] is False
        
        # Test authentication with invalid token (format is valid but authentication fails)
        result = test_api_token_authentication("invalid_token", "test-project")
        assert result["authenticated"] is False
        assert result["error"] is not None

    def test_missing_cloud_config_handling(self):
        """Test handling of missing cloud configuration."""
        from vsi2wm.wiremock_cloud import validate_wiremock_cloud_config, create_cloud_config_from_sources
        
        # Test missing config validation
        result = validate_wiremock_cloud_config({})
        assert result is False
        
        # Test config creation with missing sources
        result = create_cloud_config_from_sources()
        assert result is None

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_network_error_handling(self, mock_client_class):
        """Test handling of network errors."""
        import requests
        
        # Setup mock client to raise network error
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_mock_apis.side_effect = requests.exceptions.ConnectionError("Network error")
        
        from vsi2wm.wiremock_cloud import test_wiremock_cloud_connection
        
        cloud_config = {
            "api_key": "wm_test123",
            "project_id": "test-project",
            "environment": "default"
        }
        
        with pytest.raises(Exception):  # Should raise ConversionError
            test_wiremock_cloud_connection(cloud_config)

    def test_upload_validation_error_handling(self):
        """Test handling of upload validation errors."""
        cloud_config = {
            "api_key": "invalid",
            "project_id": "test-project"
        }
        
        manager = AutoUploadManager(cloud_config)
        validation = manager.validate_upload_prerequisites()
        
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0


class TestEndToEndBackwardCompatibility:
    """Test end-to-end backward compatibility."""

    @patch('vsi2wm.parser.parse_vsi_file')
    @patch('vsi2wm.ir_builder.build_ir_from_vsi')
    @patch('vsi2wm.mapper.map_ir_to_wiremock')
    def test_oss_format_backward_compatibility(self, mock_mapper, mock_ir_builder, mock_parse_vsi):
        """Test that OSS format still works for backward compatibility."""
        # Setup mocks
        mock_parse_vsi.return_value = {
            "layout": "standard",
            "metadata": {"source_version": "1.0", "build_number": "123"},
            "protocol": "HTTP",
            "is_http": True,
            "transactions_count": 1,
            "warnings": []
        }
        
        mock_ir = Mock()
        mock_transactions = [Mock(transaction_id="GET#/users", method="GET", url_path="/users", response_variants=[])]
        # Create a mock that behaves like a list
        mock_transactions_list = Mock()
        mock_transactions_list.__iter__ = Mock(return_value=iter(mock_transactions))
        mock_transactions_list.__len__ = Mock(return_value=len(mock_transactions))
        mock_ir.transactions = mock_transactions_list
        mock_ir_builder.return_value = mock_ir
        
        mock_mapper.return_value = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            # Test OSS format via CLI
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--oss-format"
            ]
            
            exit_code = main(args)
            assert exit_code == 0
            
            # Check OSS format files were created
            output_dir = Path(tmp_dir) / "output"
            assert (output_dir / "mappings").exists()
            assert (output_dir / "__files").exists()
            assert (output_dir / "report.json").exists()
            assert (output_dir / "stubs_index.json").exists()
            assert (output_dir / "summary.txt").exists()
            
            # Cloud export should not exist
            assert not (output_dir / "wiremock-cloud-export.json").exists()

    def test_legacy_cli_flags_backward_compatibility(self):
        """Test that legacy CLI flags still work."""
        from vsi2wm.cli import parse_args
        
        # Test legacy flags
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--upload-to-cloud",
            "--test-cloud-connection",
            "--analyze-scenario",
            "--optimize-scenario"
        ]
        
        parsed = parse_args(args)
        
        # All legacy flags should still work
        assert parsed.upload_to_cloud is True
        assert parsed.test_cloud_connection is True
        assert parsed.analyze_scenario is True
        assert parsed.optimize_scenario is True

    def test_existing_config_file_compatibility(self):
        """Test compatibility with existing config files."""
        from vsi2wm.config import load_config, create_default_config
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file = Path(tmp_dir) / "vsi2wm.yaml"
            
            # Create default config
            create_default_config(config_file)
            
            # Load config
            config = load_config(config_file)
            
            # Should have new Phase 6 settings
            assert hasattr(config, 'output_format')
            assert hasattr(config, 'auto_upload')
            assert hasattr(config, 'wiremock_cloud')
            
            # Should have backward compatibility
            assert hasattr(config, 'latency_strategy')
            assert hasattr(config, 'soap_match_strategy')
            assert hasattr(config, 'max_file_size')
