"""Tests for WireMock mapper."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from vsi2wm.ir import (
    IntermediateRepresentation,
    Latency,
    Request,
    RequestBody,
    ResponseBody,
    ResponseVariant,
    Transaction,
)
from vsi2wm.mapper import WireMockMapper, map_ir_to_wiremock


class TestWireMockMapper:
    """Test WireMock mapper functionality."""

    def test_init(self):
        """Test mapper initialization."""
        mapper = WireMockMapper()
        assert mapper.latency_strategy == "uniform"
        assert mapper.soap_match_strategy == "both"

        mapper = WireMockMapper(latency_strategy="fixed", soap_match_strategy="soapAction")
        assert mapper.latency_strategy == "fixed"
        assert mapper.soap_match_strategy == "soapAction"

    def test_map_ir_to_stubs_empty(self):
        """Test mapping empty IR."""
        ir = IntermediateRepresentation()
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        assert stubs == []

    def test_map_ir_to_stubs_simple_rest(self):
        """Test mapping simple REST transaction."""
        # Create test IR
        request = Request(
            method="GET",
            path="/api/users",
            headers={"Content-Type": "application/json"},
        )
        
        response_variant = ResponseVariant(
            status=200,
            headers={"Content-Type": "application/json"},
            body=ResponseBody(type="json", content='{"users": []}'),
        )
        
        transaction = Transaction(
            id="GET#/api/users",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        # Map to stubs
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check request
        assert stub["request"]["method"] == "GET"
        assert stub["request"]["urlPath"] == "/api/users"
        assert stub["request"]["headers"]["Content-Type"]["equalTo"] == "application/json"
        
        # Check response
        assert stub["response"]["status"] == 200
        assert stub["response"]["headers"]["Content-Type"] == "application/json"
        assert stub["response"]["jsonBody"] == {"users": []}
        assert stub["response"]["transformers"] == ["response-template"]
        
        # Check priority
        assert stub["priority"] == 0

    def test_map_ir_to_stubs_with_body_matching(self):
        """Test mapping with request body matching."""
        request = Request(
            method="POST",
            path="/api/users",
            body=RequestBody(type="json", content='{"name": "John", "email": "john@example.com"}'),
        )
        
        response_variant = ResponseVariant(
            status=201,
            body=ResponseBody(type="json", content='{"id": 123, "name": "John"}'),
        )
        
        transaction = Transaction(
            id="POST#/api/users",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check body pattern
        body_pattern = stub["request"]["bodyPatterns"][0]
        assert body_pattern["equalToJson"] == '{"name": "John", "email": "john@example.com"}'
        assert body_pattern["ignoreArrayOrder"] is True
        assert body_pattern["ignoreExtraElements"] is True

    def test_map_ir_to_stubs_with_xml_body(self):
        """Test mapping with XML body."""
        request = Request(
            method="POST",
            path="/api/data",
            body=RequestBody(type="xml", content='<data><name>John</name></data>'),
        )
        
        response_variant = ResponseVariant(
            status=200,
            body=ResponseBody(type="xml", content='<response><status>ok</status></response>'),
        )
        
        transaction = Transaction(
            id="POST#/api/data",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check XML body pattern
        body_pattern = stub["request"]["bodyPatterns"][0]
        assert body_pattern["equalToXml"] == '<data><name>John</name></data>'
        
        # Check XML response body
        assert stub["response"]["body"] == '<response><status>ok</status></response>'

    def test_map_ir_to_stubs_with_latency_range(self):
        """Test mapping with range latency."""
        request = Request(method="GET", path="/api/data")
        
        response_variant = ResponseVariant(
            status=200,
            latency=Latency(mode="range", min_ms=100, max_ms=500),
        )
        
        transaction = Transaction(
            id="GET#/api/data",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check delay distribution
        delay_dist = stub["response"]["delayDistribution"]
        assert delay_dist["type"] == "uniform"
        assert delay_dist["lower"] == 100
        assert delay_dist["upper"] == 500

    def test_map_ir_to_stubs_with_fixed_latency(self):
        """Test mapping with fixed latency."""
        request = Request(method="GET", path="/api/data")
        
        response_variant = ResponseVariant(
            status=200,
            latency=Latency(mode="fixed", fixed_ms=250),
        )
        
        transaction = Transaction(
            id="GET#/api/data",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check fixed delay
        assert stub["response"]["fixedDelayMilliseconds"] == 250

    def test_map_ir_to_stubs_with_soap_action(self):
        """Test mapping with SOAP action."""
        request = Request(
            method="POST",
            path="/soap/service",
            soap_action="http://example.com/GetUser",
        )
        
        response_variant = ResponseVariant(status=200)
        
        transaction = Transaction(
            id="POST#/soap/service",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check SOAP action header
        assert stub["request"]["headers"]["SOAPAction"]["equalTo"] == "http://example.com/GetUser"

    def test_map_ir_to_stubs_with_selection_logic(self):
        """Test mapping with selection logic."""
        request = Request(method="POST", path="/api/payment")
        
        response_variant = ResponseVariant(
            status=200,
            weight=0.8,
        )
        
        transaction = Transaction(
            id="POST#/api/payment",
            request=request,
            response_variants=[response_variant],
            selection_logic="amount > 100",
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check metadata
        assert stub["metadata"]["devtest_selection_logic"] == "amount > 100"
        assert stub["metadata"]["devtest_transaction_id"] == "POST#/api/payment"
        assert stub["metadata"]["devtest_variant_weight"] == 0.8

    def test_map_ir_to_stubs_multiple_variants_priority(self):
        """Test mapping with multiple variants and priority ordering."""
        request = Request(method="GET", path="/api/data")
        
        variant1 = ResponseVariant(status=200, weight=0.3)
        variant2 = ResponseVariant(status=404, weight=0.7)
        
        transaction = Transaction(
            id="GET#/api/data",
            request=request,
            response_variants=[variant1, variant2],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 2
        
        # Higher weight should have lower priority (higher priority number)
        assert stubs[0]["priority"] == 0  # weight 0.7
        assert stubs[1]["priority"] == 1  # weight 0.3
        assert stubs[0]["response"]["status"] == 404
        assert stubs[1]["response"]["status"] == 200

    def test_map_ir_to_stubs_with_query_params(self):
        """Test mapping with query parameters."""
        request = Request(
            method="GET",
            path="/api/users",
            query={"page": "1", "limit": "10"},
        )
        
        response_variant = ResponseVariant(status=200)
        
        transaction = Transaction(
            id="GET#/api/users",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check query parameters
        query_params = stub["request"]["queryParameters"]
        assert query_params["page"]["equalTo"] == "1"
        assert query_params["limit"]["equalTo"] == "10"

    def test_map_ir_to_stubs_with_path_template(self):
        """Test mapping with path template."""
        request = Request(
            method="GET",
            path="/api/users/123",
            path_template="/api/users/{id}",
        )
        
        response_variant = ResponseVariant(status=200)
        
        transaction = Transaction(
            id="GET#/api/users/{id}",
            request=request,
            response_variants=[response_variant],
        )
        
        ir = IntermediateRepresentation(transactions=[transaction])
        
        mapper = WireMockMapper()
        stubs = mapper.map_ir_to_stubs(ir)
        
        assert len(stubs) == 1
        stub = stubs[0]
        
        # Check path template
        assert stub["request"]["urlPathPattern"] == "/api/users/{id}"


class TestMapIRToWireMock:
    """Test convenience function."""

    def test_map_ir_to_wiremock(self):
        """Test convenience function."""
        request = Request(method="GET", path="/test")
        response_variant = ResponseVariant(status=200)
        transaction = Transaction(
            id="GET#/test",
            request=request,
            response_variants=[response_variant],
        )
        ir = IntermediateRepresentation(transactions=[transaction])
        
        stubs = map_ir_to_wiremock(ir)
        assert len(stubs) == 1
        assert stubs[0]["request"]["method"] == "GET"
        assert stubs[0]["response"]["status"] == 200
