"""Intermediate Representation (IR) for VSI to WireMock conversion."""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RequestBody:
    """Represents a request body with type and content."""
    
    type: str  # "xml", "json", "text"
    content: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "content": self.content,
        }


@dataclass
class ResponseBody:
    """Represents a response body with type and content."""
    
    type: str  # "xml", "json", "text"
    content: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "content": self.content,
        }


@dataclass
class Latency:
    """Represents latency configuration."""
    
    mode: str  # "range" or "fixed"
    min_ms: Optional[int] = None
    max_ms: Optional[int] = None
    fixed_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"mode": self.mode}
        if self.min_ms is not None:
            result["minMs"] = self.min_ms
        if self.max_ms is not None:
            result["maxMs"] = self.max_ms
        if self.fixed_ms is not None:
            result["fixedMs"] = self.fixed_ms
        return result


@dataclass
class State:
    """Represents state/correlation information."""
    
    requires: Optional[Dict[str, str]] = None
    sets: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        if self.requires:
            result["requires"] = self.requires
        if self.sets:
            result["sets"] = self.sets
        return result


@dataclass
class Request:
    """Represents a VSI request."""
    
    method: str
    path: str
    path_template: Optional[str] = None
    soap_action: Optional[str] = None
    operation: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    query: Dict[str, str] = field(default_factory=dict)
    body: Optional[RequestBody] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "method": self.method,
            "path": self.path,
            "headers": self.headers,
            "query": self.query,
        }
        
        if self.path_template:
            result["pathTemplate"] = self.path_template
        if self.soap_action:
            result["soapAction"] = self.soap_action
        if self.operation:
            result["operation"] = self.operation
        if self.body:
            result["body"] = self.body.to_dict()
            
        return result


@dataclass
class ResponseVariant:
    """Represents a response variant."""
    
    status: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[ResponseBody] = None
    latency: Optional[Latency] = None
    weight: float = 1.0
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "status": self.status,
            "headers": self.headers,
            "weight": self.weight,
        }
        
        if self.body:
            result["body"] = self.body.to_dict()
        if self.latency:
            result["latency"] = self.latency.to_dict()
        if self.notes:
            result["notes"] = self.notes
            
        return result


@dataclass
class Transaction:
    """Represents a VSI transaction."""
    
    id: str
    request: Request
    response_variants: List[ResponseVariant] = field(default_factory=list)
    selection_logic: Optional[str] = None
    state: Optional[State] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "request": self.request.to_dict(),
            "responseVariants": [v.to_dict() for v in self.response_variants],
        }
        
        if self.selection_logic:
            result["selectionLogic"] = {"js": self.selection_logic}
        if self.state:
            result["state"] = self.state.to_dict()
            
        return result


@dataclass
class IntermediateRepresentation:
    """Main Intermediate Representation container."""
    
    protocol: str = "HTTP"
    transactions: List[Transaction] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "protocol": self.protocol,
            "transactions": [t.to_dict() for t in self.transactions],
            "meta": self.meta,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, file_path: str) -> None:
        """Save IR to JSON file."""
        with open(file_path, "w") as f:
            f.write(self.to_json())
        logger.info(f"Saved IR to {file_path}")


def detect_body_type(content: str) -> str:
    """Detect the type of body content."""
    content = content.strip()
    
    if content.startswith("{") and content.endswith("}"):
        return "json"
    elif content.startswith("<") and content.endswith(">"):
        return "xml"
    else:
        return "text"


def parse_latency(latency_elem) -> Optional[Latency]:
    """Parse latency information from VSI element."""
    if latency_elem is None:
        return None
    
    # Check for range format: <latency ms="40-120">range</latency>
    ms_attr = latency_elem.get("ms")
    if ms_attr and "-" in ms_attr:
        try:
            min_ms, max_ms = map(int, ms_attr.split("-"))
            return Latency(mode="range", min_ms=min_ms, max_ms=max_ms)
        except ValueError:
            logger.warning(f"Invalid latency range format: {ms_attr}")
    
    # Check for fixed format: <latency ms="100">fixed</latency>
    if ms_attr:
        try:
            fixed_ms = int(ms_attr)
            return Latency(mode="fixed", fixed_ms=fixed_ms)
        except ValueError:
            logger.warning(f"Invalid latency fixed format: {ms_attr}")
    
    return None


def parse_weight(weight_elem) -> float:
    """Parse weight information from VSI element."""
    if weight_elem is None:
        return 1.0
    
    try:
        weight_text = weight_elem.text or weight_elem.get("value", "1.0")
        return float(weight_text)
    except (ValueError, TypeError):
        logger.warning(f"Invalid weight value: {weight_elem}")
        return 1.0


def extract_headers(headers_elem) -> Dict[str, str]:
    """Extract headers from VSI element."""
    headers = {}
    
    if not headers_elem:
        return headers
    
    for header_elem in headers_elem.findall(".//header"):
        name = header_elem.get("name")
        value = header_elem.text or "*"
        if name:
            headers[name] = value
    
    return headers


def extract_query_params(query_elem) -> Dict[str, str]:
    """Extract query parameters from VSI element."""
    params = {}
    
    if not query_elem:
        return params
    
    for param_elem in query_elem.findall(".//param"):
        name = param_elem.get("name")
        value = param_elem.text or "*"
        if name:
            params[name] = value
    
    return params
