"""Golden file tests for Phase 6 Cloud export and OSS format."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from vsi2wm.cli import main
from vsi2wm.core import VSIConverter
from vsi2wm.wiremock_cloud import create_wiremock_cloud_export
from vsi2wm.writer import write_wiremock_output


pytestmark = [pytest.mark.phase6, pytest.mark.cloud, pytest.mark.oss]


class TestCloudExportGoldenFiles:
    """Test Cloud export format against golden files."""

    def test_cloud_export_golden_file_structure(self):
        """Test Cloud export file structure matches expected format."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            },
            {
                "priority": 1,
                "request": {"method": "POST", "urlPath": "/users"},
                "response": {"status": 201, "jsonBody": {"id": 123, "name": "John"}},
                "metadata": {"devtest_transaction_id": "POST#/users"}
            }
        ]
        
        source_metadata = {
            "source_file": "test.vsi",
            "source_version": "10.5.0",
            "build_number": "510",
            "transactions_count": 2,
            "variants_count": 4
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            # Create Cloud export
            result = create_wiremock_cloud_export(stubs, output_dir, source_metadata=source_metadata)
            
            # Check result structure
            assert result["stubs_count"] == 2
            assert result["cloud_format"] is True
            assert result["enhanced_version"] == "2.0"
            assert result["metadata_included"] is True
            
            # Check export file structure
            export_file = output_dir / "wiremock-cloud-export.json"
            assert export_file.exists()
            
            with open(export_file, "r") as f:
                export_data = json.load(f)
            
            # Check top-level structure
            assert "version" in export_data
            assert "format" in export_data
            assert "metadata" in export_data
            assert "stubs" in export_data
            assert "cloud_features" in export_data
            
            # Check version and format
            assert export_data["version"] == "2.0"
            assert export_data["format"] == "wiremock-cloud"
            
            # Check metadata structure
            metadata = export_data["metadata"]
            assert metadata["generated_by"] == "vsi2wm"
            assert metadata["generated_version"] == "2.0"
            assert metadata["total_stubs"] == 2
            assert "generated_timestamp" in metadata
            assert metadata["source_file"] == "test.vsi"
            assert metadata["source_version"] == "10.5.0"
            assert metadata["source_build"] == "510"
            assert metadata["transactions_count"] == 2
            assert metadata["variants_count"] == 4
            
            # Check cloud features
            cloud_features = export_data["cloud_features"]
            assert cloud_features["enhanced_naming"] is True
            assert cloud_features["automatic_content_type"] is True
            assert cloud_features["metadata_preservation"] is True
            assert cloud_features["timestamp_tracking"] is True
            
            # Check stubs structure
            assert len(export_data["stubs"]) == 2
            
            for i, stub in enumerate(export_data["stubs"]):
                # Required Cloud fields
                assert "id" in stub
                assert "name" in stub
                assert "request" in stub
                assert "response" in stub
                assert "persistent" in stub
                assert stub["persistent"] is True
                
                # Check metadata
                assert "metadata" in stub
                assert stub["metadata"]["cloud_format"] is True
                assert stub["metadata"]["stub_index"] == i
                assert "generated_timestamp" in stub["metadata"]
                
                # Check source metadata
                assert stub["metadata"]["source_version"] == "10.5.0"
                assert stub["metadata"]["source_build"] == "510"

    def test_cloud_export_stub_naming(self):
        """Test Cloud export stub naming convention."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            },
            {
                "priority": 1,
                "request": {"method": "POST", "urlPathPattern": "/users/{id}"},
                "response": {"status": 200},
                "metadata": {"devtest_transaction_id": "POST#/users/{id}"}
            },
            {
                "priority": 2,
                "request": {"method": "DELETE", "urlPath": "/users"},
                "response": {"status": 204}
                # No metadata - should use fallback naming
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            create_wiremock_cloud_export(stubs, output_dir)
            
            export_file = output_dir / "wiremock-cloud-export.json"
            with open(export_file, "r") as f:
                export_data = json.load(f)
            
            stubs_data = export_data["stubs"]
            
            # Check naming convention
            assert stubs_data[0]["name"] == "GET__users"
            assert stubs_data[1]["name"] == "POST__users_{id}"  # Uses metadata transaction ID
            assert stubs_data[2]["name"] == "DELETE__users_2"  # Uses fallback naming with index

    def test_cloud_export_content_type_headers(self):
        """Test Cloud export automatic Content-Type headers."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/json"},
                "response": {"status": 200, "jsonBody": {"data": "test"}},
                "metadata": {"devtest_transaction_id": "GET#/json"}
            },
            {
                "priority": 1,
                "request": {"method": "GET", "urlPath": "/xml"},
                "response": {"status": 200, "body": "<data>test</data>"},
                "metadata": {"devtest_transaction_id": "GET#/xml"}
            },
            {
                "priority": 2,
                "request": {"method": "GET", "urlPath": "/text"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/text"}
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            create_wiremock_cloud_export(stubs, output_dir)
            
            export_file = output_dir / "wiremock-cloud-export.json"
            with open(export_file, "r") as f:
                export_data = json.load(f)
            
            stubs_data = export_data["stubs"]
            
            # Check Content-Type headers
            assert stubs_data[0]["response"]["headers"]["Content-Type"] == "application/json"
            assert stubs_data[1]["response"]["headers"]["Content-Type"] == "application/xml"
            assert stubs_data[2]["response"]["headers"]["Content-Type"] == "text/plain"

    def test_cloud_export_with_cloud_config(self):
        """Test Cloud export with WireMock Cloud configuration."""
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
            
            create_wiremock_cloud_export(stubs, output_dir, cloud_config=cloud_config)
            
            export_file = output_dir / "wiremock-cloud-export.json"
            with open(export_file, "r") as f:
                export_data = json.load(f)
            
            # Check cloud configuration is included
            assert "wiremock_cloud" in export_data
            assert export_data["wiremock_cloud"] == cloud_config


class TestOSSFormatGoldenFiles:
    """Test OSS format against golden files."""

    def test_oss_format_golden_file_structure(self):
        """Test OSS format file structure matches expected format."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            },
            {
                "priority": 1,
                "request": {"method": "POST", "urlPath": "/users"},
                "response": {"status": 201, "jsonBody": {"id": 123, "name": "John"}},
                "metadata": {"devtest_transaction_id": "POST#/users"}
            }
        ]
        
        report_data = {
            "source_file": "test.vsi",
            "source_version": "10.5.0",
            "build_number": "510",
            "counts": {
                "transactions": 2,
                "variants": 4,
                "stubs_generated": 2
            }
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            # Create OSS format output
            stats = write_wiremock_output(stubs, report_data, output_dir, output_format="oss")
            
            # Check stats
            assert stats["total_stubs"] == 2
            assert stats["files_written"] == 2
            assert len(stats["errors"]) == 0
            
            # Check directory structure
            assert (output_dir / "mappings").exists()
            assert (output_dir / "__files").exists()
            assert (output_dir / "report.json").exists()
            assert (output_dir / "stubs_index.json").exists()
            assert (output_dir / "summary.txt").exists()
            
            # Check stub files
            stub_files = list((output_dir / "mappings").glob("*.json"))
            assert len(stub_files) == 2
            
            # Check stub file naming
            stub_names = [f.name for f in stub_files]
            assert "GET__users_0.json" in stub_names
            assert "POST__users_1.json" in stub_names
            
            # Check report file structure
            with open(output_dir / "report.json", "r") as f:
                report = json.load(f)
            
            assert report["source_file"] == "test.vsi"
            assert report["source_version"] == "10.5.0"
            assert report["build_number"] == "510"
            assert report["counts"]["transactions"] == 2
            assert report["counts"]["variants"] == 4
            assert report["counts"]["stubs_generated"] == 2
            assert "writer_info" in report
            assert report["writer_info"]["output_format"] == "wiremock"
            
            # Check stub index structure
            with open(output_dir / "stubs_index.json", "r") as f:
                index = json.load(f)
            
            assert index["total_stubs"] == 2
            assert len(index["stubs"]) == 2
            
            # Check individual stub info
            for stub_info in index["stubs"]:
                assert "index" in stub_info
                assert "transaction_id" in stub_info
                assert "method" in stub_info
                assert "url" in stub_info
                assert "status" in stub_info
                assert "priority" in stub_info
                assert "filename" in stub_info

    def test_oss_format_large_file_splitting(self):
        """Test OSS format large file splitting golden file structure."""
        large_body = "x" * 2000  # Large body to trigger splitting
        stubs = [
            {
                "priority": 0,
                "request": {"method": "POST", "urlPath": "/large"},
                "response": {"status": 200, "body": large_body},
                "metadata": {"devtest_transaction_id": "POST#/large"}
            }
        ]
        
        report_data = {
            "source_file": "test.vsi",
            "counts": {"stubs_generated": 1}
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            # Use small max file size to trigger splitting
            stats = write_wiremock_output(
                stubs, report_data, output_dir, 
                output_format="oss", max_file_size=100
            )
            
            # Check splitting occurred
            assert stats["large_files_split"] == 1
            
            # Check stub file (should reference body file)
            stub_file = output_dir / "mappings" / "POST__large_0.json"
            assert stub_file.exists()
            
            with open(stub_file, "r") as f:
                stub_content = json.load(f)
            
            # Should have bodyFileName instead of body
            assert "body" not in stub_content["response"]
            assert "bodyFileName" in stub_content["response"]
            assert stub_content["response"]["bodyFileName"] == "__files/POST__large_0_body.bin"
            
            # Check body file was created
            body_file = output_dir / "__files" / "POST__large_0_body.bin"
            assert body_file.exists()
            
            with open(body_file, "r") as f:
                assert f.read() == large_body

    def test_oss_format_json_body_splitting(self):
        """Test OSS format JSON body splitting."""
        large_json = {"data": "x" * 2000}  # Large JSON
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/json"},
                "response": {"status": 200, "jsonBody": large_json},
                "metadata": {"devtest_transaction_id": "GET#/json"}
            }
        ]
        
        report_data = {"source_file": "test.vsi", "counts": {"stubs_generated": 1}}
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            stats = write_wiremock_output(
                stubs, report_data, output_dir,
                output_format="oss", max_file_size=100
            )
            
            assert stats["large_files_split"] == 1
            
            # Check JSON body file extension
            body_file = output_dir / "__files" / "GET__json_0_body.json"
            assert body_file.exists()
            
            with open(body_file, "r") as f:
                body_content = json.load(f)
                assert body_content == large_json

    def test_oss_format_xml_body_splitting(self):
        """Test OSS format XML body splitting."""
        large_xml = "<data>" + "x" * 2000 + "</data>"  # Large XML
        stubs = [
            {
                "priority": 0,
                "request": {"method": "POST", "urlPath": "/xml"},
                "response": {"status": 200, "body": large_xml},
                "metadata": {"devtest_transaction_id": "POST#/xml"}
            }
        ]
        
        report_data = {"source_file": "test.vsi", "counts": {"stubs_generated": 1}}
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            
            stats = write_wiremock_output(
                stubs, report_data, output_dir,
                output_format="oss", max_file_size=100
            )
            
            assert stats["large_files_split"] == 1
            
            # Check XML body file extension
            body_file = output_dir / "__files" / "POST__xml_0_body.xml"
            assert body_file.exists()
            
            with open(body_file, "r") as f:
                assert f.read() == large_xml


class TestMockAPIMetadataGoldenFiles:
    """Test MockAPI metadata generation against golden files."""

    def test_mockapi_metadata_extraction(self):
        """Test MockAPI metadata extraction from VSI source."""
        from vsi2wm.wiremock_cloud import extract_mockapi_metadata
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "test-service.vsi"
            vsi_file.write_text("test content")
            
            source_metadata = {
                "source_version": "10.5.0",
                "build_number": "510",
                "transactions_count": 5,
                "variants_count": 10
            }
            
            metadata = extract_mockapi_metadata(vsi_file, source_metadata)
            
            # Check metadata structure
            assert "name" in metadata
            assert "description" in metadata
            assert "tags" in metadata
            
            # Check name generation
            assert metadata["name"] == "test-service"
            
            # Check description generation
            description = metadata["description"]
            assert "test-service.vsi" in description
            assert "10.5.0" in description
            assert "510" in description
            assert "Generated:" in description
            
            # Check tags generation
            tags = metadata["tags"]
            assert "vsi-generated" in tags
            assert "automated" in tags
            assert "service" in tags
            assert "v10" in tags  # Major version tag

    def test_mockapi_metadata_with_rest_api(self):
        """Test MockAPI metadata for REST API VSI file."""
        from vsi2wm.wiremock_cloud import extract_mockapi_metadata
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "rest-api.vsi"
            vsi_file.write_text("test content")
            
            metadata = extract_mockapi_metadata(vsi_file)
            
            # Check tags include REST API tag
            assert "rest-api" in metadata["tags"]

    def test_mockapi_metadata_with_soap_service(self):
        """Test MockAPI metadata for SOAP service VSI file."""
        from vsi2wm.wiremock_cloud import extract_mockapi_metadata
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            vsi_file = Path(tmp_dir) / "soap-service.vsi"
            vsi_file.write_text("test content")
            
            metadata = extract_mockapi_metadata(vsi_file)
            
            # Check tags include SOAP service tag
            assert "soap-service" in metadata["tags"]

    def test_mockapi_metadata_name_sanitization(self):
        """Test MockAPI name sanitization."""
        from vsi2wm.wiremock_cloud import _generate_mockapi_name
        
        # Test various filename patterns
        test_cases = [
            ("test_service.vsi", "test-service"),
            ("My API Service.vsi", "my-api-service"),
            ("test@#$%service.vsi", "testservice"),
            ("__test__service__.vsi", "test-service"),
            ("123-test-456.vsi", "123-test-456"),
            ("", "vsi-mockapi"),  # Fallback
        ]
        
        for filename, expected_name in test_cases:
            vsi_file = Path(filename)
            name = _generate_mockapi_name(vsi_file)
            assert name == expected_name


class TestGoldenFileConsistency:
    """Test consistency between Cloud and OSS formats."""

    def test_format_consistency_same_stubs(self):
        """Test that same stubs produce consistent results in both formats."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/users"},
                "response": {"status": 200, "body": "Hello World"},
                "metadata": {"devtest_transaction_id": "GET#/users"}
            },
            {
                "priority": 1,
                "request": {"method": "POST", "urlPath": "/users"},
                "response": {"status": 201, "jsonBody": {"id": 123}},
                "metadata": {"devtest_transaction_id": "POST#/users"}
            }
        ]
        
        report_data = {
            "source_file": "test.vsi",
            "counts": {"stubs_generated": 2}
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create Cloud format
            cloud_dir = Path(tmp_dir) / "cloud"
            cloud_dir.mkdir()
            create_wiremock_cloud_export(stubs, cloud_dir, source_metadata=report_data)
            
            # Create OSS format
            oss_dir = Path(tmp_dir) / "oss"
            oss_dir.mkdir()
            write_wiremock_output(stubs, report_data, oss_dir, output_format="oss")
            
            # Both should have same number of stubs
            with open(cloud_dir / "wiremock-cloud-export.json", "r") as f:
                cloud_data = json.load(f)
            
            oss_stub_files = list((oss_dir / "mappings").glob("*.json"))
            
            assert len(cloud_data["stubs"]) == 2
            assert len(oss_stub_files) == 2
            
            # Check that request/response data is consistent
            for i, cloud_stub in enumerate(cloud_data["stubs"]):
                oss_stub_file = oss_dir / "mappings" / f"GET__users_{i}.json" if i == 0 else oss_dir / "mappings" / f"POST__users_{i}.json"
                
                with open(oss_stub_file, "r") as f:
                    oss_stub = json.load(f)
                
                # Request should be the same
                assert cloud_stub["request"] == oss_stub["request"]
                
                # Response status should be the same
                assert cloud_stub["response"]["status"] == oss_stub["response"]["status"]

    def test_metadata_preservation_consistency(self):
        """Test that metadata is preserved consistently in both formats."""
        stubs = [
            {
                "priority": 0,
                "request": {"method": "GET", "urlPath": "/test"},
                "response": {"status": 200, "body": "Hello"},
                "metadata": {
                    "devtest_transaction_id": "GET#/test",
                    "custom_field": "custom_value"
                }
            }
        ]
        
        source_metadata = {
            "source_file": "test.vsi",
            "source_version": "10.5.0",
            "build_number": "510"
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create Cloud format
            cloud_dir = Path(tmp_dir) / "cloud"
            cloud_dir.mkdir()
            create_wiremock_cloud_export(stubs, cloud_dir, source_metadata=source_metadata)
            
            # Create OSS format
            oss_dir = Path(tmp_dir) / "oss"
            oss_dir.mkdir()
            write_wiremock_output(stubs, source_metadata, oss_dir, output_format="oss")
            
            # Check Cloud format metadata
            with open(cloud_dir / "wiremock-cloud-export.json", "r") as f:
                cloud_data = json.load(f)
            
            cloud_stub = cloud_data["stubs"][0]
            assert cloud_stub["metadata"]["devtest_transaction_id"] == "GET#/test"
            assert cloud_stub["metadata"]["custom_field"] == "custom_value"
            assert cloud_stub["metadata"]["source_version"] == "10.5.0"
            assert cloud_stub["metadata"]["source_build"] == "510"
            
            # Check OSS format metadata
            oss_stub_file = oss_dir / "mappings" / "GET__test_0.json"
            with open(oss_stub_file, "r") as f:
                oss_stub = json.load(f)
            
            assert oss_stub["metadata"]["devtest_transaction_id"] == "GET#/test"
            assert oss_stub["metadata"]["custom_field"] == "custom_value"
