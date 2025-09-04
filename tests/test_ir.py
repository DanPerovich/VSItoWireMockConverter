"""Tests for IR module."""

import json
import tempfile
from pathlib import Path

import pytest

from vsi2wm.ir import (
    IntermediateRepresentation,
    Latency,
    Request,
    RequestBody,
    ResponseBody,
    ResponseVariant,
    State,
    Transaction,
    detect_body_type,
    extract_headers,
    extract_query_params,
    parse_latency,
    parse_weight,
)


class TestRequestBody:
    """Test RequestBody class."""

    def test_init(self):
        """Test RequestBody initialization."""
        body = RequestBody(type="json", content='{"key": "value"}')
        assert body.type == "json"
        assert body.content == '{"key": "value"}'

    def test_to_dict(self):
        """Test RequestBody to_dict method."""
        body = RequestBody(type="xml", content="<root>data</root>")
        result = body.to_dict()
        assert result["type"] == "xml"
        assert result["content"] == "<root>data</root>"


class TestResponseBody:
    """Test ResponseBody class."""

    def test_init(self):
        """Test ResponseBody initialization."""
        body = ResponseBody(type="json", content='{"result": "success"}')
        assert body.type == "json"
        assert body.content == '{"result": "success"}'

    def test_to_dict(self):
        """Test ResponseBody to_dict method."""
        body = ResponseBody(type="text", content="Hello World")
        result = body.to_dict()
        assert result["type"] == "text"
        assert result["content"] == "Hello World"


class TestLatency:
    """Test Latency class."""

    def test_range_latency(self):
        """Test range latency initialization."""
        latency = Latency(mode="range", min_ms=50, max_ms=150)
        assert latency.mode == "range"
        assert latency.min_ms == 50
        assert latency.max_ms == 150
        assert latency.fixed_ms is None

    def test_fixed_latency(self):
        """Test fixed latency initialization."""
        latency = Latency(mode="fixed", fixed_ms=100)
        assert latency.mode == "fixed"
        assert latency.fixed_ms == 100
        assert latency.min_ms is None
        assert latency.max_ms is None

    def test_to_dict_range(self):
        """Test Latency to_dict method for range."""
        latency = Latency(mode="range", min_ms=50, max_ms=150)
        result = latency.to_dict()
        assert result["mode"] == "range"
        assert result["minMs"] == 50
        assert result["maxMs"] == 150
        assert "fixedMs" not in result

    def test_to_dict_fixed(self):
        """Test Latency to_dict method for fixed."""
        latency = Latency(mode="fixed", fixed_ms=100)
        result = latency.to_dict()
        assert result["mode"] == "fixed"
        assert result["fixedMs"] == 100
        assert "minMs" not in result
        assert "maxMs" not in result


class TestState:
    """Test State class."""

    def test_init(self):
        """Test State initialization."""
        state = State(
            requires={"scenario": "Started"},
            sets={"scenario": "Next"}
        )
        assert state.requires == {"scenario": "Started"}
        assert state.sets == {"scenario": "Next"}

    def test_to_dict_with_data(self):
        """Test State to_dict method with data."""
        state = State(
            requires={"scenario": "Started"},
            sets={"scenario": "Next"}
        )
        result = state.to_dict()
        assert result["requires"] == {"scenario": "Started"}
        assert result["sets"] == {"scenario": "Next"}

    def test_to_dict_empty(self):
        """Test State to_dict method with empty state."""
        state = State()
        result = state.to_dict()
        assert result == {}


class TestRequest:
    """Test Request class."""

    def test_init_minimal(self):
        """Test Request initialization with minimal data."""
        request = Request(method="GET", path="/api/test")
        assert request.method == "GET"
        assert request.path == "/api/test"
        assert request.path_template is None
        assert request.soap_action is None
        assert request.operation is None
        assert request.headers == {}
        assert request.query == {}
        assert request.body is None

    def test_init_full(self):
        """Test Request initialization with full data."""
        body = RequestBody(type="json", content='{"key": "value"}')
        request = Request(
            method="POST",
            path="/api/users",
            path_template="/api/users/{id}",
            soap_action="urn:Service#Operation",
            operation="createUser",
            headers={"Content-Type": "application/json"},
            query={"page": "1"},
            body=body
        )
        assert request.method == "POST"
        assert request.path == "/api/users"
        assert request.path_template == "/api/users/{id}"
        assert request.soap_action == "urn:Service#Operation"
        assert request.operation == "createUser"
        assert request.headers == {"Content-Type": "application/json"}
        assert request.query == {"page": "1"}
        assert request.body == body

    def test_to_dict_minimal(self):
        """Test Request to_dict method with minimal data."""
        request = Request(method="GET", path="/api/test")
        result = request.to_dict()
        assert result["method"] == "GET"
        assert result["path"] == "/api/test"
        assert result["headers"] == {}
        assert result["query"] == {}
        assert "pathTemplate" not in result
        assert "soapAction" not in result
        assert "operation" not in result
        assert "body" not in result

    def test_to_dict_full(self):
        """Test Request to_dict method with full data."""
        body = RequestBody(type="json", content='{"key": "value"}')
        request = Request(
            method="POST",
            path="/api/users",
            path_template="/api/users/{id}",
            soap_action="urn:Service#Operation",
            operation="createUser",
            headers={"Content-Type": "application/json"},
            query={"page": "1"},
            body=body
        )
        result = request.to_dict()
        assert result["method"] == "POST"
        assert result["path"] == "/api/users"
        assert result["pathTemplate"] == "/api/users/{id}"
        assert result["soapAction"] == "urn:Service#Operation"
        assert result["operation"] == "createUser"
        assert result["headers"] == {"Content-Type": "application/json"}
        assert result["query"] == {"page": "1"}
        assert result["body"]["type"] == "json"
        assert result["body"]["content"] == '{"key": "value"}'


class TestResponseVariant:
    """Test ResponseVariant class."""

    def test_init_minimal(self):
        """Test ResponseVariant initialization with minimal data."""
        variant = ResponseVariant(status=200)
        assert variant.status == 200
        assert variant.headers == {}
        assert variant.body is None
        assert variant.latency is None
        assert variant.weight == 1.0
        assert variant.notes is None

    def test_init_full(self):
        """Test ResponseVariant initialization with full data."""
        body = ResponseBody(type="json", content='{"result": "success"}')
        latency = Latency(mode="range", min_ms=50, max_ms=150)
        variant = ResponseVariant(
            status=201,
            headers={"Content-Type": "application/json"},
            body=body,
            latency=latency,
            weight=0.8,
            notes="Created successfully"
        )
        assert variant.status == 201
        assert variant.headers == {"Content-Type": "application/json"}
        assert variant.body == body
        assert variant.latency == latency
        assert variant.weight == 0.8
        assert variant.notes == "Created successfully"

    def test_to_dict_minimal(self):
        """Test ResponseVariant to_dict method with minimal data."""
        variant = ResponseVariant(status=200)
        result = variant.to_dict()
        assert result["status"] == 200
        assert result["headers"] == {}
        assert result["weight"] == 1.0
        assert "body" not in result
        assert "latency" not in result
        assert "notes" not in result

    def test_to_dict_full(self):
        """Test ResponseVariant to_dict method with full data."""
        body = ResponseBody(type="json", content='{"result": "success"}')
        latency = Latency(mode="range", min_ms=50, max_ms=150)
        variant = ResponseVariant(
            status=201,
            headers={"Content-Type": "application/json"},
            body=body,
            latency=latency,
            weight=0.8,
            notes="Created successfully"
        )
        result = variant.to_dict()
        assert result["status"] == 201
        assert result["headers"] == {"Content-Type": "application/json"}
        assert result["weight"] == 0.8
        assert result["body"]["type"] == "json"
        assert result["body"]["content"] == '{"result": "success"}'
        assert result["latency"]["mode"] == "range"
        assert result["latency"]["minMs"] == 50
        assert result["latency"]["maxMs"] == 150
        assert result["notes"] == "Created successfully"


class TestTransaction:
    """Test Transaction class."""

    def test_init_minimal(self):
        """Test Transaction initialization with minimal data."""
        request = Request(method="GET", path="/api/test")
        transaction = Transaction(id="test-1", request=request)
        assert transaction.id == "test-1"
        assert transaction.request == request
        assert transaction.response_variants == []
        assert transaction.selection_logic is None
        assert transaction.state is None

    def test_init_full(self):
        """Test Transaction initialization with full data."""
        request = Request(method="POST", path="/api/users")
        variant = ResponseVariant(status=201)
        state = State(requires={"scenario": "Started"})
        transaction = Transaction(
            id="create-user",
            request=request,
            response_variants=[variant],
            selection_logic="if (condition) return true;",
            state=state
        )
        assert transaction.id == "create-user"
        assert transaction.request == request
        assert len(transaction.response_variants) == 1
        assert transaction.response_variants[0] == variant
        assert transaction.selection_logic == "if (condition) return true;"
        assert transaction.state == state

    def test_to_dict_minimal(self):
        """Test Transaction to_dict method with minimal data."""
        request = Request(method="GET", path="/api/test")
        transaction = Transaction(id="test-1", request=request)
        result = transaction.to_dict()
        assert result["id"] == "test-1"
        assert result["request"]["method"] == "GET"
        assert result["request"]["path"] == "/api/test"
        assert result["responseVariants"] == []
        assert "selectionLogic" not in result
        assert "state" not in result

    def test_to_dict_full(self):
        """Test Transaction to_dict method with full data."""
        request = Request(method="POST", path="/api/users")
        variant = ResponseVariant(status=201)
        state = State(requires={"scenario": "Started"})
        transaction = Transaction(
            id="create-user",
            request=request,
            response_variants=[variant],
            selection_logic="if (condition) return true;",
            state=state
        )
        result = transaction.to_dict()
        assert result["id"] == "create-user"
        assert result["request"]["method"] == "POST"
        assert result["request"]["path"] == "/api/users"
        assert len(result["responseVariants"]) == 1
        assert result["responseVariants"][0]["status"] == 201
        assert result["selectionLogic"]["js"] == "if (condition) return true;"
        assert result["state"]["requires"] == {"scenario": "Started"}


class TestIntermediateRepresentation:
    """Test IntermediateRepresentation class."""

    def test_init(self):
        """Test IntermediateRepresentation initialization."""
        ir = IntermediateRepresentation()
        assert ir.protocol == "HTTP"
        assert ir.transactions == []
        assert ir.meta == {}

    def test_init_with_data(self):
        """Test IntermediateRepresentation initialization with data."""
        request = Request(method="GET", path="/api/test")
        transaction = Transaction(id="test-1", request=request)
        ir = IntermediateRepresentation(
            protocol="HTTPS",
            transactions=[transaction],
            meta={"version": "1.0"}
        )
        assert ir.protocol == "HTTPS"
        assert len(ir.transactions) == 1
        assert ir.transactions[0] == transaction
        assert ir.meta["version"] == "1.0"

    def test_to_dict(self):
        """Test IntermediateRepresentation to_dict method."""
        request = Request(method="GET", path="/api/test")
        transaction = Transaction(id="test-1", request=request)
        ir = IntermediateRepresentation(
            protocol="HTTPS",
            transactions=[transaction],
            meta={"version": "1.0"}
        )
        result = ir.to_dict()
        assert result["protocol"] == "HTTPS"
        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["id"] == "test-1"
        assert result["meta"]["version"] == "1.0"

    def test_to_json(self):
        """Test IntermediateRepresentation to_json method."""
        request = Request(method="GET", path="/api/test")
        transaction = Transaction(id="test-1", request=request)
        ir = IntermediateRepresentation(
            protocol="HTTPS",
            transactions=[transaction],
            meta={"version": "1.0"}
        )
        json_str = ir.to_json()
        data = json.loads(json_str)
        assert data["protocol"] == "HTTPS"
        assert len(data["transactions"]) == 1
        assert data["transactions"][0]["id"] == "test-1"
        assert data["meta"]["version"] == "1.0"

    def test_save(self):
        """Test IntermediateRepresentation save method."""
        request = Request(method="GET", path="/api/test")
        transaction = Transaction(id="test-1", request=request)
        ir = IntermediateRepresentation(
            protocol="HTTPS",
            transactions=[transaction],
            meta={"version": "1.0"}
        )
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name
        
        try:
            ir.save(temp_file)
            
            with open(temp_file, "r") as f:
                data = json.load(f)
            
            assert data["protocol"] == "HTTPS"
            assert len(data["transactions"]) == 1
            assert data["transactions"][0]["id"] == "test-1"
            assert data["meta"]["version"] == "1.0"
        finally:
            Path(temp_file).unlink()


class TestHelperFunctions:
    """Test helper functions."""

    def test_detect_body_type_json(self):
        """Test detect_body_type for JSON."""
        assert detect_body_type('{"key": "value"}') == "json"
        assert detect_body_type('  {"key": "value"}  ') == "json"

    def test_detect_body_type_xml(self):
        """Test detect_body_type for XML."""
        assert detect_body_type("<root>data</root>") == "xml"
        assert detect_body_type('  <root>data</root>  ') == "xml"

    def test_detect_body_type_text(self):
        """Test detect_body_type for text."""
        assert detect_body_type("Hello World") == "text"
        assert detect_body_type("") == "text"
        assert detect_body_type("  ") == "text"

    def test_parse_latency_range(self):
        """Test parse_latency for range format."""
        # Mock element with range latency
        class MockElement:
            def __init__(self, ms_attr):
                self.ms_attr = ms_attr
            
            def get(self, attr):
                return self.ms_attr if attr == "ms" else None
        
        elem = MockElement("50-150")
        latency = parse_latency(elem)
        assert latency.mode == "range"
        assert latency.min_ms == 50
        assert latency.max_ms == 150
        assert latency.fixed_ms is None

    def test_parse_latency_fixed(self):
        """Test parse_latency for fixed format."""
        # Mock element with fixed latency
        class MockElement:
            def __init__(self, ms_attr):
                self.ms_attr = ms_attr
            
            def get(self, attr):
                return self.ms_attr if attr == "ms" else None
        
        elem = MockElement("100")
        latency = parse_latency(elem)
        assert latency.mode == "fixed"
        assert latency.fixed_ms == 100
        assert latency.min_ms is None
        assert latency.max_ms is None

    def test_parse_latency_invalid(self):
        """Test parse_latency with invalid format."""
        # Mock element with invalid latency
        class MockElement:
            def __init__(self, ms_attr):
                self.ms_attr = ms_attr
            
            def get(self, attr):
                return self.ms_attr if attr == "ms" else None
        
        elem = MockElement("invalid")
        latency = parse_latency(elem)
        assert latency is None

    def test_parse_weight_valid(self):
        """Test parse_weight with valid weight."""
        # Mock element with valid weight
        class MockElement:
            def __init__(self, text):
                self.text = text
        
        elem = MockElement("0.8")
        weight = parse_weight(elem)
        assert weight == 0.8

    def test_parse_weight_invalid(self):
        """Test parse_weight with invalid weight."""
        # Mock element with invalid weight
        class MockElement:
            def __init__(self, text):
                self.text = text
        
        elem = MockElement("invalid")
        weight = parse_weight(elem)
        assert weight == 1.0  # Default value

    def test_parse_weight_none(self):
        """Test parse_weight with None element."""
        weight = parse_weight(None)
        assert weight == 1.0  # Default value

    def test_extract_headers(self):
        """Test extract_headers function."""
        # Mock headers element
        class MockHeaderElement:
            def __init__(self, name, text):
                self.name = name
                self.text = text
            
            def get(self, attr):
                return self.name if attr == "name" else None
        
        class MockHeadersElement:
            def __init__(self, headers):
                self.headers = headers
            
            def findall(self, path):
                return self.headers
        
        headers_elem = MockHeadersElement([
            MockHeaderElement("Content-Type", "application/json"),
            MockHeaderElement("Authorization", "Bearer token")
        ])
        
        headers = extract_headers(headers_elem)
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer token"

    def test_extract_headers_none(self):
        """Test extract_headers with None element."""
        headers = extract_headers(None)
        assert headers == {}

    def test_extract_query_params(self):
        """Test extract_query_params function."""
        # Mock query element
        class MockParamElement:
            def __init__(self, name, text):
                self.name = name
                self.text = text
            
            def get(self, attr):
                return self.name if attr == "name" else None
        
        class MockQueryElement:
            def __init__(self, params):
                self.params = params
            
            def findall(self, path):
                return self.params
        
        query_elem = MockQueryElement([
            MockParamElement("page", "1"),
            MockParamElement("size", "10")
        ])
        
        params = extract_query_params(query_elem)
        assert params["page"] == "1"
        assert params["size"] == "10"

    def test_extract_query_params_none(self):
        """Test extract_query_params with None element."""
        params = extract_query_params(None)
        assert params == {}
