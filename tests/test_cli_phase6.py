"""Tests for Phase 6 CLI functionality - new arguments and features."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from vsi2wm.cli import CLIError, main, parse_args, validate_args
from vsi2wm.exceptions import ConversionError


pytestmark = [pytest.mark.phase6, pytest.mark.cli]


class TestPhase6CLIArguments:
    """Test new CLI arguments added in Phase 6."""

    def test_parse_args_auto_upload(self):
        """Test parsing --auto-upload flag."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--auto-upload"
        ]
        
        parsed = parse_args(args)
        assert parsed.auto_upload is True

    def test_parse_args_api_token(self):
        """Test parsing --api-token argument."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--api-token", "wm_test123"
        ]
        
        parsed = parse_args(args)
        assert parsed.api_token == "wm_test123"

    def test_parse_args_no_create_mockapi(self):
        """Test parsing --no-create-mockapi flag."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--no-create-mockapi"
        ]
        
        parsed = parse_args(args)
        assert parsed.no_create_mockapi is True

    def test_parse_args_oss_format_hidden(self):
        """Test parsing --oss-format flag (hidden feature)."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--oss-format"
        ]
        
        parsed = parse_args(args)
        assert parsed.oss_format is True

    def test_parse_args_legacy_flags(self):
        """Test parsing legacy flags for backward compatibility."""
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
        assert parsed.upload_to_cloud is True
        assert parsed.test_cloud_connection is True
        assert parsed.analyze_scenario is True
        assert parsed.optimize_scenario is True

    def test_parse_args_combinations(self):
        """Test parsing multiple new arguments together."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--auto-upload",
            "--api-token", "wm_test123",
            "--no-create-mockapi",
            "--log-level", "debug"
        ]
        
        parsed = parse_args(args)
        assert parsed.auto_upload is True
        assert parsed.api_token == "wm_test123"
        assert parsed.no_create_mockapi is True
        assert parsed.log_level == "debug"

    def test_parse_args_defaults(self):
        """Test that new arguments have correct defaults."""
        args = ["convert", "--in", "test.vsi", "--out", "output"]
        
        parsed = parse_args(args)
        assert parsed.auto_upload is False
        assert parsed.api_token is None
        assert parsed.no_create_mockapi is False
        assert parsed.oss_format is False


class TestPhase6FormatSelection:
    """Test format selection logic for Cloud vs OSS."""

    def test_format_selection_cloud_default(self):
        """Test that Cloud format is selected by default."""
        args = ["convert", "--in", "test.vsi", "--out", "output"]
        parsed = parse_args(args)
        
        # Cloud format should be default (no --oss-format flag)
        assert not parsed.oss_format

    def test_format_selection_oss_explicit(self):
        """Test that OSS format is selected when --oss-format is used."""
        args = ["convert", "--in", "test.vsi", "--out", "output", "--oss-format"]
        parsed = parse_args(args)
        
        assert parsed.oss_format is True

    def test_format_selection_help_text(self):
        """Test that --oss-format is hidden from help text."""
        import io
        import sys
        from contextlib import redirect_stdout
        
        # Capture help text output
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                parse_args(["--help"])
            except SystemExit:
                pass  # Expected behavior
        
        help_text = f.getvalue()
        
        # --oss-format should not appear in the argument list (it's hidden)
        # but it may appear in examples
        lines = help_text.split('\n')
        argument_section = False
        for line in lines:
            if line.strip().startswith('--oss-format'):
                # If we're in the argument section, this should not be here
                if argument_section:
                    assert False, "--oss-format should not appear in argument list"
                # If we're in examples section, this is OK
                break
            elif line.strip().startswith('positional arguments:') or line.strip().startswith('options:'):
                argument_section = True
            elif line.strip().startswith('Examples:'):
                argument_section = False

    def test_format_selection_examples(self):
        """Test that help examples show new Cloud-first workflow."""
        import io
        from contextlib import redirect_stdout
        
        # Capture help text output
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                parse_args(["--help"])
            except SystemExit:
                pass  # Expected behavior
        
        help_text = f.getvalue()
        
        # Should show auto-upload example
        assert "--auto-upload" in help_text
        assert "--api-token" in help_text
        assert "Auto-upload to WireMock Cloud" in help_text


class TestPhase6AutoUpload:
    """Test auto-upload functionality."""

    @patch('vsi2wm.wiremock_cloud.AutoUploadManager')
    @patch('vsi2wm.wiremock_cloud.create_cloud_config_from_sources')
    @patch('vsi2wm.core.VSIConverter')
    def test_auto_upload_success(self, mock_converter, mock_cloud_config, mock_upload_manager):
        """Test successful auto-upload workflow."""
        # Setup mocks
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter_instance.report.source_version = "10.5.0"
        mock_converter_instance.report.build_number = "510"
        mock_converter.return_value = mock_converter_instance
        
        mock_cloud_config.return_value = {
            "api_key": "wm_test123",
            "project_id": "test-project",
            "environment": "default"
        }
        
        mock_upload_manager_instance = Mock()
        mock_upload_manager_instance.validate_upload_prerequisites.return_value = {"valid": True, "errors": []}
        mock_upload_manager_instance.upload_stubs_to_mockapi.return_value = {
            "success": True,
            "uploaded_stubs": 5,
            "mock_api_id": "mock123",
            "mock_api": {"name": "test-mockapi"}
        }
        mock_upload_manager.return_value = mock_upload_manager_instance
        
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
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123"
            ]
            
            exit_code = main(args)
            assert exit_code == 0
            
            # Verify auto-upload was called
            mock_upload_manager_instance.upload_stubs_to_mockapi.assert_called_once()

    @patch('vsi2wm.wiremock_cloud.create_cloud_config_from_sources')
    @patch('vsi2wm.core.VSIConverter')
    def test_auto_upload_no_token(self, mock_converter, mock_cloud_config):
        """Test auto-upload fails when no API token provided."""
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter.return_value = mock_converter_instance
        
        # No cloud config (no token)
        mock_cloud_config.return_value = None
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload"
            ]
            
            exit_code = main(args)
            assert exit_code == 1  # Should fail due to missing token

    @patch('vsi2wm.wiremock_cloud.AutoUploadManager')
    @patch('vsi2wm.wiremock_cloud.create_cloud_config_from_sources')
    @patch('vsi2wm.core.VSIConverter')
    def test_auto_upload_validation_failure(self, mock_converter, mock_cloud_config, mock_upload_manager):
        """Test auto-upload fails when validation fails."""
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter.return_value = mock_converter_instance
        
        mock_cloud_config.return_value = {
            "api_key": "wm_test123",
            "project_id": "test-project"
        }
        
        mock_upload_manager_instance = Mock()
        mock_upload_manager_instance.validate_upload_prerequisites.return_value = {
            "valid": False,
            "errors": ["Invalid API token"]
        }
        mock_upload_manager.return_value = mock_upload_manager_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123"
            ]
            
            exit_code = main(args)
            assert exit_code == 1  # Should fail due to validation

    @patch('vsi2wm.wiremock_cloud.AutoUploadManager')
    @patch('vsi2wm.wiremock_cloud.create_cloud_config_from_sources')
    @patch('vsi2wm.core.VSIConverter')
    def test_auto_upload_upload_failure(self, mock_converter, mock_cloud_config, mock_upload_manager):
        """Test auto-upload fails when upload fails."""
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter.return_value = mock_converter_instance
        
        mock_cloud_config.return_value = {
            "api_key": "wm_test123",
            "project_id": "test-project"
        }
        
        mock_upload_manager_instance = Mock()
        mock_upload_manager_instance.validate_upload_prerequisites.return_value = {"valid": True, "errors": []}
        mock_upload_manager_instance.upload_stubs_to_mockapi.return_value = {
            "success": False,
            "error": "Upload failed"
        }
        mock_upload_manager.return_value = mock_upload_manager_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123"
            ]
            
            exit_code = main(args)
            assert exit_code == 1  # Should fail due to upload failure


class TestPhase6MockAPIManagement:
    """Test MockAPI creation and management functionality."""

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_creation(self, mock_client_class):
        """Test MockAPI creation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful creation
        mock_client.create_mock_api.return_value = {
            "mockApi": {
                "id": "mock123",
                "name": "test-mockapi",
                "description": "Test MockAPI"
            }
        }
        
        from vsi2wm.wiremock_cloud import WireMockCloudClient
        
        client = WireMockCloudClient("wm_test123", "test-project")
        result = client.create_mock_api("test-mockapi", "Test description")
        
        assert result["mockApi"]["id"] == "mock123"
        assert result["mockApi"]["name"] == "test-mockapi"

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_retrieval(self, mock_client_class):
        """Test MockAPI retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful retrieval
        mock_client.get_mock_api.return_value = {
            "id": "mock123",
            "name": "test-mockapi"
        }
        
        from vsi2wm.wiremock_cloud import WireMockCloudClient
        
        client = WireMockCloudClient("wm_test123", "test-project")
        result = client.get_mock_api("mock123")
        
        assert result["id"] == "mock123"
        assert result["name"] == "test-mockapi"

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_listing(self, mock_client_class):
        """Test MockAPI listing."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful listing
        mock_client.list_mock_apis.return_value = [
            {"id": "mock1", "name": "mockapi1"},
            {"id": "mock2", "name": "mockapi2"}
        ]
        
        from vsi2wm.wiremock_cloud import WireMockCloudClient
        
        client = WireMockCloudClient("wm_test123", "test-project")
        result = client.list_mock_apis()
        
        assert len(result) == 2
        assert result[0]["name"] == "mockapi1"

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_update(self, mock_client_class):
        """Test MockAPI update."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful update
        mock_client.update_mock_api.return_value = {
            "id": "mock123",
            "name": "updated-mockapi",
            "description": "Updated description"
        }
        
        from vsi2wm.wiremock_cloud import WireMockCloudClient
        
        client = WireMockCloudClient("wm_test123", "test-project")
        result = client.update_mock_api("mock123", name="updated-mockapi")
        
        assert result["name"] == "updated-mockapi"

    @patch('vsi2wm.wiremock_cloud.WireMockCloudClient')
    def test_mockapi_deletion(self, mock_client_class):
        """Test MockAPI deletion."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful deletion
        mock_client.delete_mock_api.return_value = {"success": True}
        
        from vsi2wm.wiremock_cloud import WireMockCloudClient
        
        client = WireMockCloudClient("wm_test123", "test-project")
        result = client.delete_mock_api("mock123")
        
        assert result["success"] is True


class TestPhase6ErrorHandling:
    """Test error handling for new Phase 6 features."""

    def test_invalid_api_token_format(self):
        """Test handling of invalid API token format."""
        from vsi2wm.wiremock_cloud import validate_api_token
        
        # Test empty token
        result = validate_api_token("")
        assert result["valid"] is False
        assert "empty" in result["errors"][0]
        
        # Test too short token
        result = validate_api_token("short")
        assert result["valid"] is False
        assert "too short" in result["errors"][0]
        
        # Test token with spaces
        result = validate_api_token("wm test 123")
        assert result["valid"] is True  # Should be valid but with warning
        assert len(result["warnings"]) > 0

    def test_missing_cloud_config(self):
        """Test handling of missing cloud configuration."""
        from vsi2wm.wiremock_cloud import validate_wiremock_cloud_config
        
        # Test missing api_key
        result = validate_wiremock_cloud_config({"project_id": "test"})
        assert result is False
        
        # Test missing project_id
        result = validate_wiremock_cloud_config({"api_key": "wm_test123"})
        assert result is False
        
        # Test empty values
        result = validate_wiremock_cloud_config({"api_key": "", "project_id": "test"})
        assert result is False

    def test_cloud_connection_failure(self):
        """Test handling of cloud connection failures."""
        from vsi2wm.wiremock_cloud import test_wiremock_cloud_connection
        
        # Test with invalid config
        with pytest.raises(ConversionError):
            test_wiremock_cloud_connection({"api_key": "invalid", "project_id": "test"})

    def test_upload_validation_failure(self):
        """Test upload validation failure handling."""
        from vsi2wm.wiremock_cloud import AutoUploadManager
        
        # Test with invalid config
        manager = AutoUploadManager({"api_key": "invalid", "project_id": "test"})
        result = manager.validate_upload_prerequisites()
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0


class TestPhase6BackwardCompatibility:
    """Test backward compatibility with existing functionality."""

    def test_legacy_upload_to_cloud_flag(self):
        """Test that --upload-to-cloud flag still works."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--upload-to-cloud"
        ]
        
        parsed = parse_args(args)
        assert parsed.upload_to_cloud is True

    def test_legacy_test_cloud_connection_flag(self):
        """Test that --test-cloud-connection flag still works."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--test-cloud-connection"
        ]
        
        parsed = parse_args(args)
        assert parsed.test_cloud_connection is True

    def test_legacy_analyze_scenario_flag(self):
        """Test that --analyze-scenario flag still works."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--analyze-scenario"
        ]
        
        parsed = parse_args(args)
        assert parsed.analyze_scenario is True

    def test_legacy_optimize_scenario_flag(self):
        """Test that --optimize-scenario flag still works."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--optimize-scenario"
        ]
        
        parsed = parse_args(args)
        assert parsed.optimize_scenario is True

    def test_existing_cli_arguments_still_work(self):
        """Test that existing CLI arguments still work with new ones."""
        args = [
            "convert",
            "--in", "test.vsi",
            "--out", "output",
            "--latency", "uniform",
            "--soap-match", "both",
            "--log-level", "debug",
            "--max-file-size", "2048576",
            "--auto-upload",
            "--api-token", "wm_test123"
        ]
        
        parsed = parse_args(args)
        
        # Existing arguments
        assert parsed.latency == "uniform"
        assert parsed.soap_match == "both"
        assert parsed.log_level == "debug"
        assert parsed.max_file_size == 2048576
        
        # New arguments
        assert parsed.auto_upload is True
        assert parsed.api_token == "wm_test123"


class TestPhase6NewCLIArguments:
    """Test the newly implemented --update-mockapi and --mockapi-id arguments."""

    def test_update_mockapi_argument_parsing(self):
        """Test that --update-mockapi argument is parsed correctly."""
        from vsi2wm.cli import parse_args
        
        args = [
            "convert",
            "--in", "test.vsi",
            "--update-mockapi"
        ]
        
        parsed = parse_args(args)
        assert parsed.update_mockapi is True

    def test_mockapi_id_argument_parsing(self):
        """Test that --mockapi-id argument is parsed correctly."""
        from vsi2wm.cli import parse_args
        
        args = [
            "convert",
            "--in", "test.vsi",
            "--mockapi-id", "abc123"
        ]
        
        parsed = parse_args(args)
        assert parsed.mockapi_id == "abc123"

    def test_update_mockapi_with_id_parsing(self):
        """Test that both --update-mockapi and --mockapi-id work together."""
        from vsi2wm.cli import parse_args
        
        args = [
            "convert",
            "--in", "test.vsi",
            "--update-mockapi",
            "--mockapi-id", "abc123"
        ]
        
        parsed = parse_args(args)
        assert parsed.update_mockapi is True
        assert parsed.mockapi_id == "abc123"

    def test_update_mockapi_requires_mockapi_id(self):
        """Test that --update-mockapi requires --mockapi-id."""
        import tempfile
        from pathlib import Path
        from vsi2wm.cli import parse_args, CLIError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--update-mockapi"
            ]
            
            parsed = parse_args(args)
            
            # This should raise CLIError during validation
            from vsi2wm.cli import validate_args
            with pytest.raises(CLIError) as exc_info:
                validate_args(parsed)
            
            assert "--update-mockapi requires --mockapi-id" in str(exc_info.value)

    def test_mockapi_id_requires_update_mockapi(self):
        """Test that --mockapi-id requires --update-mockapi."""
        import tempfile
        from pathlib import Path
        from vsi2wm.cli import parse_args, CLIError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--mockapi-id", "abc123"
            ]
            
            parsed = parse_args(args)
            
            # This should raise CLIError during validation
            from vsi2wm.cli import validate_args
            with pytest.raises(CLIError) as exc_info:
                validate_args(parsed)
            
            assert "--mockapi-id requires --update-mockapi" in str(exc_info.value)

    def test_update_mockapi_mutually_exclusive_with_no_create_mockapi(self):
        """Test that --update-mockapi and --no-create-mockapi are mutually exclusive."""
        import tempfile
        from pathlib import Path
        from vsi2wm.cli import parse_args, CLIError
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--update-mockapi",
                "--mockapi-id", "abc123",
                "--no-create-mockapi"
            ]
            
            parsed = parse_args(args)
            
            # This should raise CLIError during validation
            from vsi2wm.cli import validate_args
            with pytest.raises(CLIError) as exc_info:
                validate_args(parsed)
            
            assert "mutually exclusive" in str(exc_info.value)

    def test_help_text_includes_new_arguments(self):
        """Test that help text includes the new arguments."""
        from vsi2wm.cli import parse_args
        import io
        import contextlib
        
        # Capture help output for convert command specifically
        help_output = io.StringIO()
        with contextlib.redirect_stdout(help_output):
            try:
                parse_args(["convert", "--help"])
            except SystemExit:
                pass
        
        help_text = help_output.getvalue()
        
        # Check that new arguments are in help text
        assert "--update-mockapi" in help_text
        assert "--mockapi-id" in help_text
        assert "Update existing MockAPI" in help_text
        assert "Specific MockAPI ID" in help_text

    def test_examples_include_new_arguments(self):
        """Test that examples include the new arguments."""
        from vsi2wm.cli import parse_args
        import io
        import contextlib
        
        # Capture help output
        help_output = io.StringIO()
        with contextlib.redirect_stdout(help_output):
            try:
                parse_args(["--help"])
            except SystemExit:
                pass
        
        help_text = help_output.getvalue()
        
        # Check that examples include new arguments
        assert "--update-mockapi --mockapi-id" in help_text
        assert "Update existing MockAPI" in help_text


class TestPhase6NewUploadWorkflow:
    """Test the new upload workflow with --update-mockapi and --mockapi-id."""

    @patch('vsi2wm.wiremock_cloud.AutoUploadManager')
    @patch('vsi2wm.core.VSIConverter')
    def test_upload_to_existing_mockapi_workflow(self, mock_converter_class, mock_upload_manager_class):
        """Test the complete workflow for uploading to existing MockAPI."""
        import tempfile
        from pathlib import Path
        from vsi2wm.cli import main
        
        # Setup mocks
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter_instance.report.source_version = "1.0"
        mock_converter_instance.report.build_number = "123"
        mock_converter_class.return_value = mock_converter_instance
        
        mock_upload_manager_instance = Mock()
        mock_upload_manager_instance.validate_upload_prerequisites.return_value = {"valid": True, "errors": []}
        mock_upload_manager_instance.upload_stubs_to_existing_mockapi.return_value = {
            "success": True,
            "mock_api": {"id": "abc123", "name": "test-mockapi"},
            "mock_api_id": "abc123",
            "uploaded_stubs": 5,
            "metadata_updated": True
        }
        mock_upload_manager_class.return_value = mock_upload_manager_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123",
                "--update-mockapi",
                "--mockapi-id", "abc123"
            ]
            
            exit_code = main(args)
            
            # Verify the workflow
            assert exit_code == 0
            mock_upload_manager_instance.upload_stubs_to_existing_mockapi.assert_called_once()
            
            # Check the call arguments
            call_args = mock_upload_manager_instance.upload_stubs_to_existing_mockapi.call_args
            assert call_args[1]["mockapi_id"] == "abc123"

    @patch('vsi2wm.wiremock_cloud.AutoUploadManager')
    @patch('vsi2wm.core.VSIConverter')
    def test_upload_to_existing_mockapi_with_metadata_update(self, mock_converter_class, mock_upload_manager_class):
        """Test uploading to existing MockAPI with metadata update."""
        import tempfile
        from pathlib import Path
        from vsi2wm.cli import main
        
        # Setup mocks
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter_instance.report.source_version = "2.0"
        mock_converter_instance.report.build_number = "456"
        mock_converter_class.return_value = mock_converter_instance
        
        mock_upload_manager_instance = Mock()
        mock_upload_manager_instance.validate_upload_prerequisites.return_value = {"valid": True, "errors": []}
        mock_upload_manager_instance.upload_stubs_to_existing_mockapi.return_value = {
            "success": True,
            "mock_api": {"id": "abc123", "name": "updated-mockapi", "description": "Updated description"},
            "mock_api_id": "abc123",
            "uploaded_stubs": 3,
            "metadata_updated": True
        }
        mock_upload_manager_class.return_value = mock_upload_manager_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123",
                "--update-mockapi",
                "--mockapi-id", "abc123"
            ]
            
            exit_code = main(args)
            
            # Verify the workflow
            assert exit_code == 0
            mock_upload_manager_instance.upload_stubs_to_existing_mockapi.assert_called_once()

    @patch('vsi2wm.wiremock_cloud.AutoUploadManager')
    @patch('vsi2wm.core.VSIConverter')
    def test_upload_to_existing_mockapi_failure(self, mock_converter_class, mock_upload_manager_class):
        """Test handling of upload failure to existing MockAPI."""
        import tempfile
        from pathlib import Path
        from vsi2wm.cli import main
        
        # Setup mocks
        mock_converter_instance = Mock()
        mock_converter_instance.convert.return_value = 0
        mock_converter_instance.report.source_version = "1.0"
        mock_converter_instance.report.build_number = "123"
        mock_converter_class.return_value = mock_converter_instance
        
        mock_upload_manager_instance = Mock()
        mock_upload_manager_instance.validate_upload_prerequisites.return_value = {"valid": True, "errors": []}
        mock_upload_manager_instance.upload_stubs_to_existing_mockapi.return_value = {
            "success": False,
            "error": "MockAPI not found",
            "mock_api": None,
            "mock_api_id": "abc123",
            "uploaded_stubs": 0
        }
        mock_upload_manager_class.return_value = mock_upload_manager_instance
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            args = [
                "convert",
                "--in", str(vsi_file),
                "--out", str(Path(tmp_dir) / "output"),
                "--auto-upload",
                "--api-token", "wm_test123",
                "--update-mockapi",
                "--mockapi-id", "abc123"
            ]
            
            exit_code = main(args)
            
            # Verify the workflow failed
            assert exit_code == 1
            mock_upload_manager_instance.upload_stubs_to_existing_mockapi.assert_called_once()
