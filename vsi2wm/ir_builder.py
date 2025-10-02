"""IR Builder for constructing Intermediate Representation from VSI files."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree.ElementTree import Element, iterparse

from vsi2wm.ir import (
    IntermediateRepresentation,
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
from vsi2wm.helper_converter import HelperConverter

logger = logging.getLogger(__name__)


class IRBuilder:
    """Builds Intermediate Representation from VSI files."""
    
    def __init__(self, vsi_file_path: Path):
        self.vsi_file_path = vsi_file_path
        self.ir = IntermediateRepresentation()
        self.warnings: List[str] = []
        self.helper_converter = HelperConverter()
        
    def build(self) -> IntermediateRepresentation:
        """Build the complete Intermediate Representation."""
        logger.info(f"Building IR from {self.vsi_file_path}")
        
        try:
            # Read file content as string first, then parse
            with open(self.vsi_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            logger.debug(f"XML content length: {len(xml_content)}")
            logger.debug(f"XML content preview: {xml_content[:200]}...")
            
            from xml.etree.ElementTree import fromstring
            root = fromstring(xml_content)
            logger.debug(f"Root element: {root}")
            logger.debug(f"Root tag: {root.tag}")
            
            # Find all transaction elements
            transactions = root.findall('.//t')
            logger.debug(f"Found {len(transactions)} transaction elements")
            
            for transaction_elem in transactions:
                transaction_id = transaction_elem.get('id', 'unknown')
                logger.debug(f"Processing transaction: {transaction_id}")
                
                # Extract all data from the transaction before any processing
                request_elem = transaction_elem.find('.//rq')
                response_variants = transaction_elem.findall('.//rp')
                logger.debug(f"Found {len(response_variants)} response variants")
                
                # Process the transaction
                self._process_transaction_start(transaction_elem)
                
                # Process all response variants for this transaction
                for rp_elem in response_variants:
                    logger.debug(f"Processing response variant: {rp_elem.get('id', 'unknown')}")
                    self._process_response_variant(rp_elem, transaction_id)
            
            logger.info(f"Built IR with {len(self.ir.transactions)} transactions")
            return self.ir
            
        except Exception as e:
            logger.error(f"Error building IR: {e}")
            self.warnings.append(f"IR building failed: {e}")
            return self.ir
    
    def _process_transaction_start(self, transaction_elem: Element) -> None:
        """Process the start of a transaction element."""
        transaction_id = transaction_elem.get('id', 'unknown')
        
        # Find request element
        request_elem = transaction_elem.find('.//rq')
        if not request_elem:
            logger.warning(f"No request found in transaction {transaction_id}")
            return
        
        logger.debug(f"Request element: {request_elem}")
        logger.debug(f"Request element children: {[child.tag for child in request_elem]}")
        
        # Check the 'm' element
        m_elem = request_elem.find('.//m')
        if m_elem:
            logger.debug(f"M element children: {[child.tag for child in m_elem]}")
            # Try to find path by iterating through children
            for child in m_elem:
                logger.debug(f"Child: {child.tag} = '{child.text}'")
        
        # Build request
        request = self._build_request(request_elem, transaction_id)
        
        # Create transaction
        transaction = Transaction(id=transaction_id, request=request)
        
        # Add to IR
        self.ir.transactions.append(transaction)
    
    def _build_request(self, request_elem: Element, transaction_id: str) -> Request:
        """Build a Request object from VSI request element."""
        # Extract all data from the request element before any processing
        method = "GET"  # default
        path = "/"  # default
        path_template = None
        soap_action = None
        operation = None
        headers = {}
        query = {}
        body = None
        
        # Find the 'm' element and extract method and path
        m_elem = request_elem.find('.//m')
        if m_elem:
            for child in m_elem:
                if child.tag == 'method':
                    method = child.text or "GET"
                elif child.tag == 'path':
                    path = child.text or "/"
                elif child.tag == 'pathTemplate':
                    path_template = child.text
                elif child.tag == 'soapAction':
                    soap_action = child.text
                elif child.tag == 'operation':
                    operation = child.text
        
        # Extract headers
        headers_elem = request_elem.find('.//headers')
        if headers_elem:
            headers = extract_headers(headers_elem)
            # Detect unsupported helpers in request headers and convert
            self.helper_converter.clear_unsupported_helpers()  # Clear previous helpers
            headers = self.helper_converter.convert_headers(headers)
            # Collect warnings from helper converter
            for helper in self.helper_converter.get_unsupported_helpers():
                self.warnings.append(f"Unsupported CA LISA helper in request header: {helper}")
        
        # Extract query parameters
        query_elem = request_elem.find('.//query')
        if query_elem:
            query = extract_query_params(query_elem)
        
        # Extract body - iterate through children instead of using find
        body = None
        for child in request_elem:
            if child.tag == 'bd':
                if child.text:
                    body_content = child.text.strip()
                    if body_content:
                        body_type = detect_body_type(body_content)
                        body = RequestBody(type=body_type, content=body_content)
                        
                        # Convert CA LISA helpers to WireMock Handlebars helpers
                        self.helper_converter.clear_unsupported_helpers()  # Clear previous helpers
                        body = self.helper_converter.convert_request_body(body)
                        
                        # Collect warnings from helper converter
                        for helper in self.helper_converter.get_unsupported_helpers():
                            self.warnings.append(f"Unsupported CA LISA helper in request body: {helper}")
                        
                        # Detect SOAP services and default to POST
                        if body_type == "xml" and "soapenv:Envelope" in body.content:
                            if method == "GET":  # Only change if still default
                                method = "POST"
                                logger.debug(f"Detected SOAP service, changed method to POST")
                break
        
        logger.debug(f"Built request: {method} {path}")
        
        return Request(
            method=method,
            path=path,
            path_template=path_template,
            soap_action=soap_action,
            operation=operation,
            headers=headers,
            query=query,
            body=body,
        )
    
    def _process_response_variant(self, response_elem: Element, transaction_id: str) -> None:
        """Process a response variant element."""
        # Find the corresponding transaction in IR
        transaction = None
        for t in self.ir.transactions:
            if t.id == transaction_id:
                transaction = t
                break
        
        if not transaction:
            logger.warning(f"Transaction {transaction_id} not found for response variant")
            return
        
        # Build response variant
        variant = self._build_response_variant(response_elem, transaction_id)
        transaction.response_variants.append(variant)
        
        # Extract selection logic if present - look inside m element
        m_elem = response_elem.find('.//m')
        if m_elem:
            for child in m_elem:
                if child.tag == 'matchScript':
                    if child.text:
                        transaction.selection_logic = child.text.strip()
                    break
    
    def _build_response_variant(self, response_elem: Element, transaction_id: str) -> ResponseVariant:
        """Build a ResponseVariant object from VSI response element."""
        # Extract status by iterating through m element children
        status = 200  # default
        m_elem = response_elem.find('.//m')
        logger.debug(f"Response element children: {[child.tag for child in response_elem]}")
        logger.debug(f"M element found: {m_elem}")
        if m_elem:
            for child in m_elem:
                if child.tag == 'status':
                    try:
                        status = int(child.text) if child.text else 200
                        logger.debug(f"Found status: {status}")
                    except ValueError:
                        status = 200
                    break
        
        # Extract headers
        headers_elem = response_elem.find('.//headers')
        headers = extract_headers(headers_elem)
        # Detect unsupported helpers in response headers and convert
        self.helper_converter.clear_unsupported_helpers()  # Clear previous helpers
        headers = self.helper_converter.convert_headers(headers)
        # Collect warnings from helper converter
        for helper in self.helper_converter.get_unsupported_helpers():
            self.warnings.append(f"Unsupported CA LISA helper in response header: {helper}")
        
        # Extract body - iterate through children instead of using find
        body = None
        for child in response_elem:
            if child.tag == 'bd':
                if child.text:
                    body_content = child.text.strip()
                    if body_content:
                        body_type = detect_body_type(body_content)
                        body = ResponseBody(type=body_type, content=body_content)
                        
                        # Convert CA LISA helpers to WireMock Handlebars helpers
                        self.helper_converter.clear_unsupported_helpers()  # Clear previous helpers
                        body = self.helper_converter.convert_response_body(body)
                        
                        # Collect warnings from helper converter
                        for helper in self.helper_converter.get_unsupported_helpers():
                            self.warnings.append(f"Unsupported CA LISA helper in response body: {helper}")
                        
                        logger.debug(f"Found response body: type={body_type}, content length={len(body_content)}")
                break
        
        # Extract latency by iterating through m element children
        latency = None
        if m_elem:
            logger.debug(f"M element children: {[child.tag for child in m_elem]}")
            for child in m_elem:
                if child.tag == 'latency':
                    latency = parse_latency(child)
                    break
        
        # Extract weight by iterating through m element children
        weight = 1.0  # default
        if m_elem:
            for child in m_elem:
                if child.tag in ['selectionWeight', 'weight']:
                    weight = parse_weight(child)
                    logger.debug(f"Found weight: {weight}")
                    break
        
        # Extract notes (from comments or other metadata)
        notes = None
        notes_elem = response_elem.find('.//notes')
        if notes_elem and notes_elem.text:
            notes = notes_elem.text.strip()
        
        logger.debug(f"Built response variant: status={status}, weight={weight}, latency={latency}")
        
        return ResponseVariant(
            status=status,
            headers=headers,
            body=body,
            latency=latency,
            weight=weight,
            notes=notes,
        )
    
    def _extract_state_info(self, transaction_elem: Element) -> Optional[State]:
        """Extract state/correlation information from transaction."""
        # This is a placeholder for future state extraction
        # Will be implemented when we need to handle scenarios and correlation
        return None


def build_ir_from_vsi(vsi_file_path: Path) -> Tuple[IntermediateRepresentation, List[str]]:
    """Convenience function to build IR from VSI file.
    
    Returns:
        Tuple of (IntermediateRepresentation, warnings)
    """
    builder = IRBuilder(vsi_file_path)
    ir = builder.build()
    return ir, builder.warnings
