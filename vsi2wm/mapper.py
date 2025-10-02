"""Mapper for converting Intermediate Representation to WireMock stub mappings."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from vsi2wm.ir import (
    IntermediateRepresentation,
    Request,
    ResponseVariant,
    Transaction,
)

logger = logging.getLogger(__name__)


class WireMockMapper:
    """Maps Intermediate Representation to WireMock stub mappings."""

    def __init__(
        self,
        latency_strategy: str = "uniform",
        soap_match_strategy: str = "both",
    ):
        self.latency_strategy = latency_strategy
        self.soap_match_strategy = soap_match_strategy

    def map_ir_to_stubs(self, ir: IntermediateRepresentation) -> List[Dict[str, Any]]:
        """Convert Intermediate Representation to WireMock stub mappings."""
        logger.info(f"Mapping IR with {len(ir.transactions)} transactions to WireMock stubs")
        
        stubs = []
        
        for transaction in ir.transactions:
            # Sort response variants by weight (descending) to set priority
            sorted_variants = sorted(
                transaction.response_variants,
                key=lambda v: v.weight,
                reverse=True
            )
            
            for i, variant in enumerate(sorted_variants):
                stub = self._create_stub(transaction, variant, priority=i)
                stubs.append(stub)
        
        logger.info(f"Generated {len(stubs)} WireMock stubs")
        return stubs

    def _create_stub(
        self, 
        transaction: Transaction, 
        variant: ResponseVariant, 
        priority: int
    ) -> Dict[str, Any]:
        """Create a single WireMock stub from transaction and variant."""
        request = transaction.request
        
        # Build request matching
        request_match = self._build_request_match(request)
        
        # Build response
        response = self._build_response(variant)
        
        # Build stub
        stub = {
            "priority": priority,
            "request": request_match,
            "response": response,
        }
        
        # Add metadata
        stub["metadata"] = {
            "devtest_transaction_id": transaction.id,
            "devtest_variant_weight": variant.weight,
        }
        if transaction.selection_logic:
            stub["metadata"]["devtest_selection_logic"] = transaction.selection_logic
        
        return stub

    def _build_request_match(self, request: Request) -> Dict[str, Any]:
        """Build WireMock request matching criteria."""
        request_match = {
            "method": request.method,
        }
        
        # Add URL matching
        if request.path_template:
            request_match["urlPathPattern"] = request.path_template
        else:
            request_match["urlPath"] = request.path
        
        # Add headers
        if request.headers:
            request_match["headers"] = {}
            for name, value in request.headers.items():
                request_match["headers"][name] = {
                    "equalTo": value
                }
        
        # Add query parameters
        if request.query:
            request_match["queryParameters"] = {}
            for name, value in request.query.items():
                request_match["queryParameters"][name] = {
                    "equalTo": value
                }
        
        # Add body matching
        if request.body:
            if request.body.type == "json":
                request_match["bodyPatterns"] = [
                    {
                        "equalToJson": request.body.content,
                        "ignoreArrayOrder": True,
                        "ignoreExtraElements": True,
                    }
                ]
            elif request.body.type == "xml":
                request_match["bodyPatterns"] = [
                    {
                        "equalToXml": request.body.content,
                    }
                ]
            else:
                request_match["bodyPatterns"] = [
                    {
                        "equalTo": request.body.content,
                    }
                ]
        
        # Add SOAP-specific matching
        if request.soap_action:
            if self.soap_match_strategy in ["soapAction", "both"]:
                if "headers" not in request_match:
                    request_match["headers"] = {}
                request_match["headers"]["SOAPAction"] = {
                    "equalTo": request.soap_action
                }
        
        return request_match

    def _build_response(self, variant: ResponseVariant) -> Dict[str, Any]:
        """Build WireMock response."""
        response = {
            "status": variant.status,
        }
        
        # Add headers
        if variant.headers:
            response["headers"] = variant.headers
        else:
            response["headers"] = {}
        
        # Add body
        if variant.body:
            if variant.body.type == "json":
                # Check if content contains Handlebars helpers
                if "{{" in variant.body.content and "}}" in variant.body.content:
                    # Use body instead of jsonBody for templates
                    response["body"] = variant.body.content
                    response["headers"]["Content-Type"] = "application/json"
                else:
                    # Parse as JSON for static content
                    response["jsonBody"] = json.loads(variant.body.content)
            elif variant.body.type == "xml":
                response["body"] = variant.body.content
            else:
                response["body"] = variant.body.content
        
        # Add latency
        if variant.latency:
            if variant.latency.mode == "range":
                response["delayDistribution"] = {
                    "type": "uniform",
                    "lower": variant.latency.min_ms,
                    "upper": variant.latency.max_ms,
                }
            elif variant.latency.mode == "fixed":
                response["fixedDelayMilliseconds"] = variant.latency.fixed_ms
        
        # Add transformers
        response["transformers"] = ["response-template"]
        
        return response


def map_ir_to_wiremock(
    ir: IntermediateRepresentation,
    latency_strategy: str = "uniform",
    soap_match_strategy: str = "both",
) -> List[Dict[str, Any]]:
    """Convenience function to map IR to WireMock stubs."""
    mapper = WireMockMapper(latency_strategy, soap_match_strategy)
    return mapper.map_ir_to_stubs(ir)
