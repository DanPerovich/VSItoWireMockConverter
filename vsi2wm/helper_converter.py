"""
Helper conversion utilities for transforming CA LISA (Broadcom DevTest) helpers 
to WireMock Handlebars helpers.
"""

import re
import logging
from typing import Dict, Any, List, Set, Tuple

logger = logging.getLogger(__name__)


class HelperConverter:
    """Converts CA LISA helpers to WireMock Handlebars helpers."""
    
    def __init__(self):
        # Pattern for date delta helpers with HTML entities: {{=doDateDeltaFromCurrent("format","offsetD");}}
        self.date_delta_pattern_encoded = re.compile(
            r"\{\{=doDateDeltaFromCurrent\(&quot;(.*?)&quot;,&quot;([-+]?\d+)D&quot;\);.*?\}\}"
        )
        # Pattern for date delta helpers without HTML entities: {{=doDateDeltaFromCurrent("format","offsetD")}}
        self.date_delta_pattern_plain = re.compile(
            r"\{\{=doDateDeltaFromCurrent\(\"(.*?)\",\"([-+]?\d+D?)\"\)\}\}"
        )
        
        # Pattern for xpath helpers: {{=request_field;/*comment*/}}
        self.xpath_pattern = re.compile(
            r"\{\{=request_(.*?);/\*.*?\*/\}\}"
        )
        
        # Pattern for simple request field access: {{=request_field}}
        self.simple_request_pattern = re.compile(
            r"\{\{=request_(.*?)\}\}"
        )
        
        # Pattern for random string helper: {{=doRandomString(length)}}
        self.random_string_pattern = re.compile(
            r"\{\{=doRandomString\((\d+)\)\}\}"
        )
        
        # Pattern for random number helper: {{=doRandomNumber(min, max)}}
        self.random_number_pattern = re.compile(
            r"\{\{=doRandomNumber\(\s*(\d+)\s*,\s*(\d+)\s*\)\}\}"
        )
        
        # Pattern for random boolean helper: {{=doRandomBoolean()}}
        self.random_boolean_pattern = re.compile(
            r"\{\{=doRandomBoolean\(\)\}\}"
        )
        
        # Pattern for random email helper: {{=doRandomEmail()}}
        self.random_email_pattern = re.compile(
            r"\{\{=doRandomEmail\(\)\}\}"
        )
        
        # Pattern for random SSN helper: {{=doRandomSSN()}}
        self.random_ssn_pattern = re.compile(
            r"\{\{=doRandomSSN\(\)\}\}"
        )
        
        # Pattern for random credit card helper: {{=doRandomCreditCard()}}
        self.random_credit_card_pattern = re.compile(
            r"\{\{=doRandomCreditCard\(\)\}\}"
        )
        
        # Pattern to detect any CA LISA helper: {{=helperName(...)}}
        self.ca_lisa_helper_pattern = re.compile(
            r"\{\{=([^}]+)\}\}"
        )
        
        # Track unsupported helpers found during conversion
        self.unsupported_helpers: Set[str] = set()
    
    def convert_date_delta(self, text: str) -> str:
        """Convert date delta format to WireMock format.
        
        Converts: {{=doDateDeltaFromCurrent("yyyy-MM-dd","+1D");}}
        To: {{now offset='+1 days' format='yyyy-MM-dd'}}
        """
        # Handle both encoded and plain formats
        text = self.date_delta_pattern_encoded.sub(
            r"{{now offset='\2 days' format='\1'}}", 
            text
        )
        
        def replace_date_delta(match):
            format_str = match.group(1)
            offset_str = match.group(2)
            # Remove 'D' suffix if present
            if offset_str.endswith('D'):
                offset_str = offset_str[:-1]
            return f"{{{{now offset='{offset_str} days' format='{format_str}'}}}}"
        
        text = self.date_delta_pattern_plain.sub(replace_date_delta, text)
        return text
    
    def convert_xpath(self, match: re.Match) -> str:
        """Convert xpath format to WireMock format.
        
        Converts: {{=request_field;/*comment*/}}
        To: {{xPath request.body '//field/text()'}}
        """
        xpath_value = match.group(1).replace('_', '/')
        return f"{{{{xPath request.body '//{xpath_value}/text()'}}}}"
    
    def convert_simple_request(self, match: re.Match) -> str:
        """Convert simple request field access to WireMock format.
        
        Converts: {{=request_field}}
        To: {{xPath request.body '//field/text()'}}
        """
        field_name = match.group(1).replace('_', '/')
        return f"{{{{xPath request.body '//{field_name}/text()'}}}}"
    
    def convert_random_string(self, match: re.Match) -> str:
        """Convert random string helper to WireMock format.
        
        Converts: {{=doRandomString(10)}}
        To: {{randomValue type='ALPHANUMERIC' length='10'}}
        """
        length = match.group(1)
        return f"{{{{randomValue type='ALPHANUMERIC' length='{length}'}}}}"
    
    def convert_random_number(self, match: re.Match) -> str:
        """Convert random number helper to WireMock format.
        
        Converts: {{=doRandomNumber(1, 100)}}
        To: {{randomInt lower=1 upper=100}}
        """
        min_val = match.group(1)
        max_val = match.group(2)
        return f"{{{{randomInt lower={min_val} upper={max_val}}}}}"
    
    def convert_random_boolean(self, match: re.Match) -> str:
        """Convert random boolean helper to WireMock format.
        
        Converts: {{=doRandomBoolean()}}
        To: {{pickRandom true false}}
        """
        return "{{pickRandom true false}}"
    
    def convert_random_email(self, match: re.Match) -> str:
        """Convert random email helper to WireMock format.
        
        Converts: {{=doRandomEmail()}}
        To: {{random 'Internet.safeEmailAddress'}}
        """
        return "{{random 'Internet.safeEmailAddress'}}"
    
    def convert_random_ssn(self, match: re.Match) -> str:
        """Convert random SSN helper to WireMock format.
        
        Converts: {{=doRandomSSN()}}
        To: {{random 'IdNumber.ssnValid'}}
        """
        return "{{random 'IdNumber.ssnValid'}}"
    
    def convert_random_credit_card(self, match: re.Match) -> str:
        """Convert random credit card helper to WireMock format.
        
        Converts: {{=doRandomCreditCard()}}
        To: {{random 'Business.creditCardNumber'}}
        """
        return "{{random 'Business.creditCardNumber'}}"
    
    def detect_unsupported_helpers(self, text: str) -> List[str]:
        """Detect all CA LISA helpers in the text and identify unsupported ones.
        
        Args:
            text: The text containing CA LISA helpers
            
        Returns:
            List of unsupported helper expressions found
        """
        if not text:
            return []
            
        unsupported = []
        
        # Find all CA LISA helpers
        for match in self.ca_lisa_helper_pattern.finditer(text):
            helper_expr = match.group(0)  # Full expression like {{=doRandomString(10)}}
            helper_content = match.group(1)  # Content inside {{=...}}
            
            # Check if this helper is supported by our patterns
            is_supported = (
                self.date_delta_pattern_encoded.search(helper_expr) or
                self.date_delta_pattern_plain.search(helper_expr) or
                self.xpath_pattern.search(helper_expr) or
                self.simple_request_pattern.search(helper_expr) or
                self.random_string_pattern.search(helper_expr) or
                self.random_number_pattern.search(helper_expr) or
                self.random_boolean_pattern.search(helper_expr) or
                self.random_email_pattern.search(helper_expr) or
                self.random_ssn_pattern.search(helper_expr) or
                self.random_credit_card_pattern.search(helper_expr)
            )
            
            if not is_supported:
                unsupported.append(helper_expr)
                self.unsupported_helpers.add(helper_expr)
        
        return unsupported
    
    def replace_unsupported_helpers(self, text: str) -> str:
        """Replace unsupported CA LISA helpers with fallback text.
        
        Args:
            text: The text containing CA LISA helpers
            
        Returns:
            Text with unsupported helpers replaced with [UNSUPPORTED: helper] format
        """
        if not text:
            return text
            
        def replace_helper(match):
            helper_expr = match.group(0)  # Full expression like {{=doRandomString(10)}}
            helper_content = match.group(1)  # Content inside {{=...}}
            
            # Check if this helper is supported
            is_supported = (
                self.date_delta_pattern_encoded.search(helper_expr) or
                self.date_delta_pattern_plain.search(helper_expr) or
                self.xpath_pattern.search(helper_expr) or
                self.simple_request_pattern.search(helper_expr) or
                self.random_string_pattern.search(helper_expr) or
                self.random_number_pattern.search(helper_expr) or
                self.random_boolean_pattern.search(helper_expr) or
                self.random_email_pattern.search(helper_expr) or
                self.random_ssn_pattern.search(helper_expr) or
                self.random_credit_card_pattern.search(helper_expr)
            )
            
            if not is_supported:
                return f"[UNSUPPORTED: {helper_content}]"
            else:
                return helper_expr  # Keep supported helpers unchanged
        
        return self.ca_lisa_helper_pattern.sub(replace_helper, text)
    
    def convert_helpers(self, text: str) -> str:
        """Convert all CA LISA helpers in the text to WireMock Handlebars helpers.
        
        Args:
            text: The text containing CA LISA helpers
            
        Returns:
            Text with CA LISA helpers converted to WireMock Handlebars helpers
        """
        if not text:
            return text
            
        # First, replace unsupported helpers with fallback text
        text = self.replace_unsupported_helpers(text)
        
        # Then apply conversions for supported helpers
        text = self.convert_date_delta(text)
        text = self.xpath_pattern.sub(self.convert_xpath, text)
        text = self.simple_request_pattern.sub(self.convert_simple_request, text)
        text = self.random_string_pattern.sub(self.convert_random_string, text)
        text = self.random_number_pattern.sub(self.convert_random_number, text)
        text = self.random_boolean_pattern.sub(self.convert_random_boolean, text)
        text = self.random_email_pattern.sub(self.convert_random_email, text)
        text = self.random_ssn_pattern.sub(self.convert_random_ssn, text)
        text = self.random_credit_card_pattern.sub(self.convert_random_credit_card, text)
        
        return text
    
    def get_unsupported_helpers(self) -> List[str]:
        """Get list of all unsupported helpers found during conversion.
        
        Returns:
            List of unsupported helper expressions
        """
        return list(self.unsupported_helpers)
    
    def clear_unsupported_helpers(self) -> None:
        """Clear the list of unsupported helpers."""
        self.unsupported_helpers.clear()
    
    def convert_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Convert helpers in request body content.
        
        Args:
            body: RequestBody or ResponseBody object
            
        Returns:
            Body object with converted content
        """
        if body and hasattr(body, 'content') and body.content:
            # Detect unsupported helpers before conversion
            self.detect_unsupported_helpers(body.content)
            converted_content = self.convert_helpers(body.content)
            # Create new body object with converted content
            body_type = type(body)
            return body_type(type=body.type, content=converted_content)
        return body
    
    def convert_response_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Convert helpers in response body content.
        
        Args:
            body: ResponseBody object
            
        Returns:
            Body object with converted content
        """
        return self.convert_request_body(body)
    
    def convert_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Convert helpers in header values.
        
        Args:
            headers: Dictionary of header name -> value mappings
            
        Returns:
            Dictionary with converted header values
        """
        if not headers:
            return headers
            
        converted_headers = {}
        for name, value in headers.items():
            if value:
                # Detect unsupported helpers in header values
                self.detect_unsupported_helpers(value)
                converted_headers[name] = self.convert_helpers(value)
            else:
                converted_headers[name] = value
                
        return converted_headers


# Global converter instance
_converter = HelperConverter()


def convert_helpers(text: str) -> str:
    """Convert CA LISA helpers to WireMock Handlebars helpers.
    
    This is a convenience function that uses the global converter instance.
    
    Args:
        text: The text containing CA LISA helpers
        
    Returns:
        Text with CA LISA helpers converted to WireMock Handlebars helpers
    """
    return _converter.convert_helpers(text)


def convert_body_helpers(body: Dict[str, Any]) -> Dict[str, Any]:
    """Convert helpers in body content.
    
    Args:
        body: RequestBody or ResponseBody object
        
    Returns:
        Body object with converted content
    """
    return _converter.convert_request_body(body)


def convert_header_helpers(headers: Dict[str, str]) -> Dict[str, str]:
    """Convert helpers in header values.
    
    Args:
        headers: Dictionary of header name -> value mappings
        
    Returns:
        Dictionary with converted header values
    """
    return _converter.convert_headers(headers)


def detect_unsupported_helpers(text: str) -> List[str]:
    """Detect unsupported CA LISA helpers in text.
    
    Args:
        text: The text containing CA LISA helpers
        
    Returns:
        List of unsupported helper expressions found
    """
    return _converter.detect_unsupported_helpers(text)


def get_unsupported_helpers() -> List[str]:
    """Get list of all unsupported helpers found during conversion.
    
    Returns:
        List of unsupported helper expressions
    """
    return _converter.get_unsupported_helpers()


def clear_unsupported_helpers() -> None:
    """Clear the list of unsupported helpers."""
    _converter.clear_unsupported_helpers()
