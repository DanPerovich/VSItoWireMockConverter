"""Tests for Phase 6 Cloud export and OSS format generation."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from vsi2wm.wiremock_cloud import (
    convert_to_wiremock_cloud_format,
    create_wiremock_cloud_export,
    _generate_cloud_stub_name,
    _enhance_cloud_stub_formatting,
    _validate_cloud_export_data,
    WireMockCloudClient
)
from vsi2wm.writer import WireMockWriter, write_wiremock_output
from vsi2wm.core import VSIConverter


pytestmark = [pytest.mark.phase6, pytest.mark.cloud, pytest.mark.oss]


class TestCloudExportGeneration:
    """Test Cloud export format generation."""

    def test_convert_to_wiremock_cloud_format_basic(self):
        """Test basic conversion to Cloud format."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            }
        ]
        
        cloud_stubs = convert_to_wiremock_cloud_format(stubs)
        
        assert len(cloud_stubs) == 1
        cloud_stub = cloud_stubs[0]
        
        # Check required Cloud fields
        assert "id" in cloud_stub
        assert "name" in cloud_stub
        assert "request" in cloud_stub
        assert "response" in cloud_stub
        assert "persistent" in cloud_stub
        assert cloud_stub["persistent"] is True
        
        # Check metadata
        assert "metadata" in cloud_stub
        assert cloud_stub["metadata"]["cloud_format"] is True
        assert "stub_index" in cloud_stub["metadata"]
        assert "generated_timestamp" in cloud_stub["metadata"]

    def test_convert_to_wiremock_cloud_format_with_source_metadata(self):
        """Test conversion with source metadata."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "POST", "urlPath": "/users"},
                "response": {"status": 201, "body": "Created"},
                "metadata": {"devtest_transaction_id": "POST#/users"}
            }
        ]
        
        source_metadata = {
            "source_version": "10.5.0",
            "build_number": "510",
            "source_file": "test.vsi"
        }
        
        cloud_stubs = convert_to_wiremock_cloud_format(stubs, source_metadata)
        
        assert len(cloud_stubs) == 1
        cloud_stub = cloud_stubs[0]
        
        # Check source metadata is included
        assert cloud_stub["metadata"]["source_version"] == "10.5.0"
        assert cloud_stub["metadata"]["source_build"] == "510"

    def test_generate_cloud_stub_name_from_metadata(self):
        """Test generating Cloud stub name from metadata."""
        stub = {
            "metadata": {"devtest_transaction_id": "GET#/users"},
            "request": {"method": "GET", "urlPath": "/users"}
        }
        
        name = _generate_cloud_stub_name(stub, 0)
        assert name == "GET__users"

    def test_generate_cloud_stub_name_from_request(self):
        """Test generating Cloud stub name from request when no metadata."""
        stub = {
            "request": {"method": "POST", "urlPathPattern": "/users/{id}"}
        }
        
        name = _generate_cloud_stub_name(stub, 1)
        assert name == "POST__users_{id}_1"

    def test_generate_cloud_stub_name_fallback(self):
        """Test generating Cloud stub name fallback."""
        stub = {
            "request": {}
        }
        
        name = _generate_cloud_stub_name(stub, 2)
        assert name == "stub_2"

    def test_enhance_cloud_stub_formatting_json(self):
        """Test enhancing Cloud stub formatting for JSON responses."""
        stub = {
            "response": {
                "status": 200,
                "jsonBody": {"data": "test"}
            }
        }
        
        enhanced = _enhance_cloud_stub_formatting(stub)
        
        assert "headers" in enhanced["response"]
        assert enhanced["response"]["headers"]["Content-Type"] == "application/json"

    def test_enhance_cloud_stub_formatting_xml(self):
        """Test enhancing Cloud stub formatting for XML responses."""
        stub = {
            "response": {
                "status": 200,
                "body": "<data>test</data>"
            }
        }
        
        enhanced = _enhance_cloud_stub_formatting(stub)
        
        assert "headers" in enhanced["response"]
        assert enhanced["response"]["headers"]["Content-Type"] == "application/xml"

    def test_enhance_cloud_stub_formatting_text(self):
        """Test enhancing Cloud stub formatting for text responses."""
        stub = {
            "response": {
                "status": 200,
                "body": "Hello World"
            }
        }
        
        enhanced = _enhance_cloud_stub_formatting(stub)
        
        assert "headers" in enhanced["response"]
        assert enhanced["response"]["headers"]["Content-Type"] == "text/plain"

    def test_create_wiremock_cloud_export(self):
        """Test creating complete Cloud export file."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/test"},
                "response": {"status": 200, "body": "Hello"},
                "metadata": {"devtest_transaction_id": "GET#/test"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            result = create_wiremock_cloud_export(stubs, output_dir)
            
            # Check return value
            assert result["stubs_count"] == 1
            assert result["cloud_format"] is True
            assert result["enhanced_version"] == "2.0"
            
            # Check export file was created
            export_file = output_dir / "wiremock-cloud-export.json"
            assert export_file.exists()
            
            # Check export file content
            with open(export_file, "r") as f:
                export_data = json.load(f)
            
            assert export_data["version"] == "2.0"
            assert export_data["format"] == "wiremock-cloud"
            assert "metadata" in export_data
            assert "stubs" in export_data
            assert len(export_data["stubs"]) == 1
            assert "cloud_features" in export_data

    def test_create_wiremock_cloud_export_with_cloud_config(self):
        """Test creating Cloud export with cloud configuration."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/test"},
                "response": {"status": 200, "body": "Hello"},
                "metadata": {"devtest_transaction_id": "GET#/test"}
            }
        ]
        
        cloud_config = {
            "api_key": "wm_test123",
            "project_id": "test-project",
            "environment": "default"
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            result = create_wiremock_cloud_export(stubs, output_dir, cloud_config)
            
            # Check export file content
            export_file = output_dir / "wiremock-cloud-export.json"
            with open(export_file, "r") as f:
                export_data = json.load(f)
            
            assert "wiremock_cloud" in export_data
            assert export_data["wiremock_cloud"] == cloud_config

    def test_validate_cloud_export_data_valid(self):
        """Test validation of valid Cloud export data."""
        export_data = {
            "version": "2.0",
            "format": "wiremock-cloud",
            "metadata": {"total_stubs": 1},
            "stubs": [
                {
                    "id": "test-id",
                    "name": "test-stub",
                    "request": {"method": "GET"},
                    "response": {"status": 200}
                }
            ]
        }
        
        # Should not raise exception
        _validate_cloud_export_data(export_data)

    def test_validate_cloud_export_data_missing_fields(self):
        """Test validation of Cloud export data with missing fields."""
        export_data = {
            "version": "2.0",
            "format": "wiremock-cloud"
            # Missing metadata and stubs
        }
        
        with pytest.raises(Exception):  # Should raise ConversionError
            _validate_cloud_export_data(export_data)

    def test_validate_cloud_export_data_invalid_stubs(self):
        """Test validation of Cloud export data with invalid stubs."""
        export_data = {
            "version": "2.0",
            "format": "wiremock-cloud",
            "metadata": {"total_stubs": 1},
            "stubs": [
                {
                    "id": "test-id",
                    "name": "test-stub"
                    # Missing request and response
                }
            ]
        }
        
        with pytest.raises(Exception):  # Should raise ConversionError
            _validate_cloud_export_data(export_data)


class TestOSSFormatGeneration:
    """Test OSS format generation (hidden feature)."""

    def test_oss_format_writer_initialization(self):
        """Test WireMockWriter initialization for OSS format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = WireMockWriter(Path(tmp_dir))
            
            assert writer.output_dir == Path(tmp_dir)
            assert writer.mappings_dir == Path(tmp_dir) / "mappings"
            assert writer.files_dir == Path(tmp_dir) / "__files"
            
            # Check directories were created
            assert writer.mappings_dir.exists()
            assert writer.files_dir.exists()

    def test_oss_format_stub_writing(self):
        """Test writing stubs in OSS format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = WireMockWriter(Path(tmp_dir))
            
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/users"},
                    "response": {"status": 200, "body": "Hello World"},
                    "metadata": {"devtest_transaction_id": "GET#/users"}
                }
            ]
            
            stats = writer.write_stubs(stubs)
            
            assert stats["total_stubs"] == 1
            assert stats["files_written"] == 1
            assert len(stats["errors"]) == 0
            
            # Check stub file was created
            stub_file = writer.mappings_dir / "GET__users_0.json"
            assert stub_file.exists()
            
            # Check content
            with open(stub_file, "r") as f:
                content = json.load(f)
                assert content["request"]["method"] == "GET"
                assert content["response"]["status"] == 200

    def test_oss_format_large_file_splitting(self):
        """Test OSS format large file splitting."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Use small max file size to trigger splitting
            writer = WireMockWriter(Path(tmp_dir), max_file_size=100)
            
            large_body = "x" * 200  # Larger than 100 byte limit
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "POST", "urlPath": "/large"},
                    "response": {"status": 200, "body": large_body},
                    "metadata": {"devtest_transaction_id": "POST#/large"}
                }
            ]
            
            stats = writer.write_stubs(stubs)
            
            assert stats["large_files_split"] == 1
            
            # Check body file was created
            body_file = writer.files_dir / "POST__large_0_body.bin"
            assert body_file.exists()

    def test_oss_format_report_generation(self):
        """Test OSS format report generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = WireMockWriter(Path(tmp_dir))
            
            report_data = {
                "source_file": "test.vsi",
                "counts": {"stubs_generated": 5}
            }
            
            writer.write_report(report_data)
            
            report_file = writer.output_dir / "report.json"
            assert report_file.exists()
            
            with open(report_file, "r") as f:
                content = json.load(f)
                assert content["source_file"] == "test.vsi"
                assert content["counts"]["stubs_generated"] == 5
                assert content["writer_info"]["output_format"] == "wiremock"

    def test_oss_format_index_generation(self):
        """Test OSS format stub index generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = WireMockWriter(Path(tmp_dir))
            
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/users"},
                    "response": {"status": 200},
                    "metadata": {"devtest_transaction_id": "GET#/users"}
                }
            ]
            
            writer.write_index_file(stubs)
            
            index_file = writer.output_dir / "stubs_index.json"
            assert index_file.exists()
            
            with open(index_file, "r") as f:
                content = json.load(f)
                assert content["total_stubs"] == 1
                assert len(content["stubs"]) == 1

    def test_oss_format_summary_generation(self):
        """Test OSS format summary generation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            writer = WireMockWriter(Path(tmp_dir))
            
            stats = {
                "total_stubs": 10,
                "files_written": 8,
                "large_files_split": 2,
                "errors": ["Failed to write stub 5: Permission denied"]
            }
            
            writer.write_summary(stats)
            
            summary_file = writer.output_dir / "summary.txt"
            assert summary_file.exists()
            
            with open(summary_file, "r") as f:
                content = f.read()
                assert "Total stubs generated: 10" in content
                assert "Files written: 8" in content
                assert "Large files split: 2" in content


class TestFormatSelectionIntegration:
    """Test format selection integration in VSIConverter."""

    @patch('vsi2wm.parser.parse_vsi_file')
    @patch('vsi2wm.ir_builder.build_ir_from_vsi')
    @patch('vsi2wm.mapper.map_ir_to_wiremock')
    def test_cloud_format_default(self, mock_mapper, mock_ir_builder, mock_parse_vsi):
        """Test that Cloud format is used by default."""
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
        mock_ir.transactions = []
        mock_ir_builder.return_value = mock_ir
        
        mock_mapper.return_value = []
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            converter = VSIConverter(
                input_file=vsi_file,
                output_dir=Path(tmp_dir) / "output",
                output_format="cloud"
            )
            
            result = converter.convert()
            assert result == 0
            
            # Check that Cloud export file was created
            cloud_export = Path(tmp_dir) / "output" / "wiremock-cloud-export.json"
            assert cloud_export.exists()

    @patch('vsi2wm.parser.parse_vsi_file')
    @patch('vsi2wm.ir_builder.build_ir_from_vsi')
    @patch('vsi2wm.mapper.map_ir_to_wiremock')
    def test_oss_format_explicit(self, mock_mapper, mock_ir_builder, mock_parse_vsi):
        """Test that OSS format is used when explicitly specified."""
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
        mock_ir.transactions = []
        mock_ir_builder.return_value = mock_ir
        
        mock_mapper.return_value = []
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test.vsi"
            vsi_file.write_text("test content")
            
            converter = VSIConverter(
                input_file=vsi_file,
                output_dir=Path(tmp_dir) / "output",
                output_format="oss"
            )
            
            result = converter.convert()
            assert result == 0
            
            # Check that OSS format files were created
            mappings_dir = Path(tmp_dir) / "output" / "mappings"
            assert mappings_dir.exists()
            
            # Cloud export should not exist
            cloud_export = Path(tmp_dir) / "output" / "wiremock-cloud-export.json"
            assert not cloud_export.exists()

    def test_write_wiremock_output_cloud_format(self):
        """Test write_wiremock_output with Cloud format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/test"},
                    "response": {"status": 200, "body": "Hello"},
                    "metadata": {"devtest_transaction_id": "GET#/test"}
                }
            ]
            
            report_data = {
                "source_file": "test.vsi",
                "counts": {"stubs_generated": 1}
            }
            
            stats = write_wiremock_output(stubs, report_data, Path(tmp_dir), output_format="cloud")
            
            assert stats["total_stubs"] == 1
            
            # Check Cloud export file was created
            cloud_export = Path(tmp_dir) / "wiremock-cloud-export.json"
            assert cloud_export.exists()
            
            # OSS format files should not exist
            assert not (Path(tmp_dir) / "mappings").exists()
            assert not (Path(tmp_dir) / "__files").exists()

    def test_write_wiremock_output_oss_format(self):
        """Test write_wiremock_output with OSS format."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/test"},
                    "response": {"status": 200, "body": "Hello"},
                    "metadata": {"devtest_transaction_id": "GET#/test"}
                }
            ]
            
            report_data = {
                "source_file": "test.vsi",
                "counts": {"stubs_generated": 1}
            }
            
            stats = write_wiremock_output(stubs, report_data, Path(tmp_dir), output_format="oss")
            
            assert stats["total_stubs"] == 1
            
            # Check OSS format files were created
            assert (Path(tmp_dir) / "mappings").exists()
            assert (Path(tmp_dir) / "__files").exists()
            assert (Path(tmp_dir) / "report.json").exists()
            assert (Path(tmp_dir) / "stubs_index.json").exists()
            assert (Path(tmp_dir) / "summary.txt").exists()
            
            # Cloud export should not exist
            assert not (Path(tmp_dir) / "wiremock-cloud-export.json").exists()
