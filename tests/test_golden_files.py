"""Golden file tests for VSI to WireMock conversion."""

import json
import tempfile
from pathlib import Path

import pytest

from vsi2wm.core import VSIConverter


class TestGoldenFiles:
    """Test conversion against expected golden files."""

    def test_simple_rest_golden_file(self):
        """Test simple REST VSI conversion against golden file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/simple_rest.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read generated stubs
            stubs = []
            mappings_dir = output_dir / "mappings"
            for stub_file in mappings_dir.glob("*.json"):
                with open(stub_file, "r") as f:
                    stubs.append(json.load(f))
            
            # Sort stubs by priority for consistent comparison
            stubs.sort(key=lambda x: x["priority"])
            
            # Expected golden file structure
            expected_stubs = [
                {
                    "priority": 0,
                    "request": {
                        "method": "GET",
                        "urlPath": "/users",
                        "headers": {
                            "Content-Type": {
                                "equalTo": "application/json"
                            }
                        }
                    },
                    "response": {
                        "status": 200,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "jsonBody": {
                            "users": [
                                {"id": 1, "name": "John"},
                                {"id": 2, "name": "Jane"}
                            ]
                        },
                        "delayDistribution": {
                            "type": "uniform",
                            "lower": 100,
                            "upper": 200
                        },
                        "transformers": ["response-template"]
                    },
                    "metadata": {
                        "devtest_transaction_id": "GET#/users",
                        "devtest_variant_weight": 1.0
                    }
                },
                {
                    "priority": 1,
                    "request": {
                        "method": "GET",
                        "urlPath": "/users",
                        "headers": {
                            "Content-Type": {
                                "equalTo": "application/json"
                            }
                        }
                    },
                    "response": {
                        "status": 404,
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "jsonBody": {
                            "error": "Users not found"
                        },
                        "fixedDelayMilliseconds": 50,
                        "transformers": ["response-template"]
                    },
                    "metadata": {
                        "devtest_transaction_id": "GET#/users",
                        "devtest_variant_weight": 0.1
                    }
                }
            ]
            
            # Compare stubs
            assert len(stubs) == len(expected_stubs)
            
            for i, (actual, expected) in enumerate(zip(stubs, expected_stubs)):
                # Compare key fields
                assert actual["priority"] == expected["priority"]
                assert actual["request"]["method"] == expected["request"]["method"]
                assert actual["request"]["urlPath"] == expected["request"]["urlPath"]
                assert actual["response"]["status"] == expected["response"]["status"]
                assert actual["response"]["jsonBody"] == expected["response"]["jsonBody"]
                
                # Check metadata
                assert "devtest_transaction_id" in actual["metadata"]
                assert "devtest_variant_weight" in actual["metadata"]

    def test_soap_service_golden_file(self):
        """Test SOAP VSI conversion against golden file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/soap_service.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read generated stubs
            stubs = []
            mappings_dir = output_dir / "mappings"
            for stub_file in mappings_dir.glob("*.json"):
                with open(stub_file, "r") as f:
                    stubs.append(json.load(f))
            
            # Sort stubs by priority
            stubs.sort(key=lambda x: x["priority"])
            
            # Verify SOAP-specific features
            assert len(stubs) == 2
            
            # First stub (priority 0) should be the 200 response
            first_stub = stubs[0]
            assert first_stub["priority"] == 0
            assert first_stub["request"]["method"] == "POST"
            assert first_stub["request"]["urlPath"] == "/soap/service"
            assert first_stub["request"]["headers"]["SOAPAction"]["equalTo"] == "http://example.com/GetUser"
            assert first_stub["response"]["status"] == 200
            assert "body" in first_stub["response"]  # XML body
            assert "delayDistribution" in first_stub["response"]
            assert first_stub["metadata"]["devtest_selection_logic"] == "request.GetUserRequest.userId == \"123\""
            
            # Second stub (priority 1) should be the 500 response
            second_stub = stubs[1]
            assert second_stub["priority"] == 1
            assert second_stub["response"]["status"] == 500
            assert "fixedDelayMilliseconds" in second_stub["response"]

    def test_query_params_golden_file(self):
        """Test VSI with query parameters against golden file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/query_params.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read generated stubs
            stubs = []
            mappings_dir = output_dir / "mappings"
            for stub_file in mappings_dir.glob("*.json"):
                with open(stub_file, "r") as f:
                    stubs.append(json.load(f))
            
            assert len(stubs) == 1
            
            stub = stubs[0]
            assert stub["request"]["method"] == "GET"
            assert stub["request"]["urlPath"] == "/products"
            
            # Check query parameters
            query_params = stub["request"]["queryParameters"]
            assert query_params["category"]["equalTo"] == "electronics"
            assert query_params["limit"]["equalTo"] == "10"
            assert query_params["page"]["equalTo"] == "1"
            
            # Check response
            assert stub["response"]["status"] == 200
            assert "delayDistribution" in stub["response"]

    def test_multiple_transactions_golden_file(self):
        """Test VSI with multiple transactions against golden file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/multiple_transactions.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read generated stubs
            stubs = []
            mappings_dir = output_dir / "mappings"
            for stub_file in mappings_dir.glob("*.json"):
                with open(stub_file, "r") as f:
                    stubs.append(json.load(f))
            
            # Should have 6 stubs (3 transactions × 2 variants each)
            assert len(stubs) == 6
            
            # Check that we have stubs for all three transactions
            transaction_ids = set()
            for stub in stubs:
                transaction_ids.add(stub["metadata"]["devtest_transaction_id"])
            
            expected_transactions = {"GET#/users", "POST#/users", "DELETE#/users/{id}"}
            assert transaction_ids == expected_transactions

    def test_rr_pairs_golden_file(self):
        """Test RR-pairs VSI conversion against golden file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/rr_pairs.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read generated stubs
            stubs = []
            mappings_dir = output_dir / "mappings"
            for stub_file in mappings_dir.glob("*.json"):
                with open(stub_file, "r") as f:
                    stubs.append(json.load(f))
            
            # Should have 2 stubs (1 transaction × 2 variants)
            assert len(stubs) == 2
            
            # Sort by priority
            stubs.sort(key=lambda x: x["priority"])
            
            # Check first stub (201 response)
            first_stub = stubs[0]
            assert first_stub["priority"] == 0
            assert first_stub["request"]["method"] == "POST"
            assert first_stub["request"]["urlPath"] == "/orders"
            assert first_stub["request"]["headers"]["Authorization"]["equalTo"] == "Bearer token123"
            assert first_stub["response"]["status"] == 201
            assert "delayDistribution" in first_stub["response"]
            
            # Check second stub (400 response)
            second_stub = stubs[1]
            assert second_stub["priority"] == 1
            assert second_stub["response"]["status"] == 400
            assert "fixedDelayMilliseconds" in second_stub["response"]


class TestReportSnapshots:
    """Test report.json snapshots."""

    def test_simple_rest_report_snapshot(self):
        """Test report.json snapshot for simple REST VSI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/simple_rest.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read report
            report_file = output_dir / "report.json"
            with open(report_file, "r") as f:
                report = json.load(f)
            
            # Check expected report structure
            assert report["source_file"] == str(input_file)
            assert report["source_version"] == "1.0"
            assert report["build_number"] == "1.0.0"
            assert report["counts"]["transactions"] == 1
            assert report["counts"]["variants"] == 2
            assert report["counts"]["stubs_generated"] == 2
            assert len(report["warnings"]) == 0
            assert "writer_info" in report
            assert report["writer_info"]["output_format"] == "wiremock"

    def test_multiple_transactions_report_snapshot(self):
        """Test report.json snapshot for multiple transactions VSI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert the test VSI
            input_file = Path("tests/data/multiple_transactions.vsi")
            output_dir = Path(temp_dir)
            
            converter = VSIConverter(
                input_file=input_file,
                output_dir=output_dir,
                latency_strategy="uniform",
                soap_match_strategy="both",
            )
            
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Read report
            report_file = output_dir / "report.json"
            with open(report_file, "r") as f:
                report = json.load(f)
            
            # Check expected report structure
            assert report["source_file"] == str(input_file)
            assert report["source_version"] == "2.0"
            assert report["build_number"] == "2.0.0"
            assert report["counts"]["transactions"] == 3
            assert report["counts"]["variants"] == 6
            assert report["counts"]["stubs_generated"] == 6
            assert len(report["warnings"]) == 0
