"""Tests for WireMock writer."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from vsi2wm.writer import WireMockWriter, write_wiremock_output


class TestWireMockWriter:
    """Test WireMock writer functionality."""

    def test_init(self):
        """Test writer initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            assert writer.output_dir == Path(temp_dir)
            assert writer.mappings_dir == Path(temp_dir) / "mappings"
            assert writer.files_dir == Path(temp_dir) / "__files"
            assert writer.max_file_size == 1024 * 1024  # 1MB default

            # Check directories created
            assert writer.mappings_dir.exists()
            assert writer.files_dir.exists()

    def test_init_custom_max_file_size(self):
        """Test writer initialization with custom max file size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir), max_file_size=512 * 1024)  # 512KB
            assert writer.max_file_size == 512 * 1024

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
            # Test invalid characters
            assert writer._sanitize_filename("GET#/accounts") == "GET__accounts"
            assert writer._sanitize_filename("POST/soap/service") == "POST_soap_service"
            assert writer._sanitize_filename("file:with:colons") == "file_with_colons"
            
            # Test length limit
            long_name = "a" * 150
            sanitized = writer._sanitize_filename(long_name)
            assert len(sanitized) == 100
            assert sanitized == "a" * 100

    def test_write_stubs_simple(self):
        """Test writing simple stubs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/test"},
                    "response": {"status": 200, "body": "Hello World"},
                    "metadata": {"devtest_transaction_id": "GET#/test"}
                }
            ]
            
            stats = writer.write_stubs(stubs)
            
            assert stats["total_stubs"] == 1
            assert stats["files_written"] == 1
            assert stats["large_files_split"] == 0
            assert len(stats["errors"]) == 0
            
            # Check file was written
            stub_file = writer.mappings_dir / "GET__test_0.json"
            assert stub_file.exists()
            
            # Check content
            with open(stub_file, "r") as f:
                content = json.load(f)
                assert content["request"]["method"] == "GET"
                assert content["response"]["status"] == 200

    def test_write_stubs_with_large_body(self):
        """Test writing stubs with large response bodies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set small max file size to trigger splitting
            writer = WireMockWriter(Path(temp_dir), max_file_size=100)
            
            # Create stub with large body
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
            
            assert stats["total_stubs"] == 1
            assert stats["files_written"] == 1
            assert stats["large_files_split"] == 1
            assert len(stats["errors"]) == 0
            
            # Check stub file
            stub_file = writer.mappings_dir / "POST__large_0.json"
            assert stub_file.exists()
            
            with open(stub_file, "r") as f:
                content = json.load(f)
                assert "body" not in content["response"]
                assert "bodyFileName" in content["response"]
                assert content["response"]["bodyFileName"] == "__files/POST__large_0_body.bin"
            
            # Check body file
            body_file = writer.files_dir / "POST__large_0_body.bin"
            assert body_file.exists()
            
            with open(body_file, "r") as f:
                assert f.read() == large_body

    def test_write_stubs_with_json_body(self):
        """Test writing stubs with JSON response bodies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir), max_file_size=100)
            
            json_body = {"data": "x" * 200}  # Large JSON
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/json"},
                    "response": {"status": 200, "jsonBody": json_body},
                    "metadata": {"devtest_transaction_id": "GET#/json"}
                }
            ]
            
            stats = writer.write_stubs(stubs)
            
            assert stats["large_files_split"] == 1
            
            # Check body file extension
            body_file = writer.files_dir / "GET__json_0_body.json"
            assert body_file.exists()
            
            with open(body_file, "r") as f:
                content = json.load(f)
                assert content == json_body

    def test_write_stubs_with_xml_body(self):
        """Test writing stubs with XML response bodies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir), max_file_size=100)
            
            xml_body = "<data>" + "x" * 200 + "</data>"  # Large XML
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "POST", "urlPath": "/xml"},
                    "response": {"status": 200, "body": xml_body},
                    "metadata": {"devtest_transaction_id": "POST#/xml"}
                }
            ]
            
            stats = writer.write_stubs(stubs)
            
            assert stats["large_files_split"] == 1
            
            # Check body file extension
            body_file = writer.files_dir / "POST__xml_0_body.xml"
            assert body_file.exists()
            
            with open(body_file, "r") as f:
                assert f.read() == xml_body

    def test_write_stubs_error_handling(self):
        """Test error handling during stub writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
            # Create stub that will cause an error (invalid JSON)
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "GET", "urlPath": "/test"},
                    "response": {"status": 200, "body": "Hello World"},
                    "metadata": {"devtest_transaction_id": "GET#/test"}
                },
                {
                    "priority": 1,
                    "request": {"method": "POST", "urlPath": "/error"},
                    "response": {"status": 500, "body": Mock()},  # This will cause an error
                    "metadata": {"devtest_transaction_id": "POST#/error"}
                }
            ]
            
            stats = writer.write_stubs(stubs)
            
            assert stats["total_stubs"] == 2
            assert stats["files_written"] == 1  # Only first stub written
            assert len(stats["errors"]) == 1  # One error

    def test_write_report(self):
        """Test writing enhanced report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
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
                assert "writer_info" in content
                assert content["writer_info"]["max_file_size"] == 1024 * 1024
                assert content["writer_info"]["output_format"] == "wiremock"

    def test_write_index_file(self):
        """Test writing stub index file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
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
                    "response": {"status": 201},
                    "metadata": {"devtest_transaction_id": "POST#/users/{id}"}
                }
            ]
            
            writer.write_index_file(stubs)
            
            index_file = writer.output_dir / "stubs_index.json"
            assert index_file.exists()
            
            with open(index_file, "r") as f:
                content = json.load(f)
                assert content["total_stubs"] == 2
                assert len(content["stubs"]) == 2
                
                # Check first stub info
                stub1 = content["stubs"][0]
                assert stub1["index"] == 0
                assert stub1["transaction_id"] == "GET#/users"
                assert stub1["method"] == "GET"
                assert stub1["url"] == "/users"
                assert stub1["status"] == 200
                assert stub1["priority"] == 0
                assert stub1["filename"] == "GET__users_0.json"
                
                # Check second stub info
                stub2 = content["stubs"][1]
                assert stub2["url"] == "/users/{id}"  # urlPathPattern
                assert stub2["filename"] == "POST__users_{id}_1.json"

    def test_write_summary(self):
        """Test writing human-readable summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
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
                assert "Errors encountered: 1" in content
                assert "Failed to write stub 5: Permission denied" in content

    def test_write_summary_no_errors(self):
        """Test writing summary with no errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            writer = WireMockWriter(Path(temp_dir))
            
            stats = {
                "total_stubs": 5,
                "files_written": 5,
                "large_files_split": 0,
                "errors": []
            }
            
            writer.write_summary(stats)
            
            summary_file = writer.output_dir / "summary.txt"
            with open(summary_file, "r") as f:
                content = f.read()
                assert "No errors encountered." in content


class TestWriteWireMockOutput:
    """Test convenience function."""

    def test_write_wiremock_output(self):
        """Test complete WireMock output writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
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
            
            stats = write_wiremock_output(stubs, report_data, Path(temp_dir))
            
            assert stats["total_stubs"] == 1
            assert stats["files_written"] == 1
            
            # Check all files were created
            output_dir = Path(temp_dir)
            assert (output_dir / "mappings" / "GET__test_0.json").exists()
            assert (output_dir / "report.json").exists()
            assert (output_dir / "stubs_index.json").exists()
            assert (output_dir / "summary.txt").exists()

    def test_write_wiremock_output_custom_max_size(self):
        """Test WireMock output with custom max file size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            stubs = [
                {
                    "priority": 0,
                    "request": {"method": "POST", "urlPath": "/large"},
                    "response": {"status": 200, "body": "x" * 200},
                    "metadata": {"devtest_transaction_id": "POST#/large"}
                }
            ]
            
            report_data = {"source_file": "test.vsi", "counts": {"stubs_generated": 1}}
            
            # Use small max file size to trigger splitting
            stats = write_wiremock_output(stubs, report_data, Path(temp_dir), max_file_size=100)
            
            assert stats["large_files_split"] == 1
            assert (Path(temp_dir) / "__files" / "POST__large_0_body.bin").exists()
