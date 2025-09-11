"""
Helper conversion utilities for transforming CA LISA (Broadcom DevTest) helpers 
to WireMock Handlebars helpers.
"""

import re
from typing import Dict, Any


class HelperConverter:
    """Converts CA LISA helpers to WireMock Handlebars helpers."""
    
    def __init__(self):
        # Pattern for date delta helpers with HTML entities: {{=doDateDeltaFromCurrent("format","offsetD");}}
        self.date_delta_pattern_encoded = re.compile(
            r"\{\{=doDateDeltaFromCurrent\(&quot;(.*?)&quot;,&quot;([-+]?\d+)D&quot;\);.*?\}\}"
        )
        # Pattern for date delta helpers without HTML entities: {{=doDateDeltaFromCurrent("format","offsetD")}}
        self.date_delta_pattern_plain = re.compile(
            r"\{\{=doDateDeltaFromCurrent\(\"(.*?)\",\"([-+]?\d+)D?\"\)\}\}"
        )
        
        # Pattern for xpath helpers: {{=request_field;/*comment*/}}
        self.xpath_pattern = re.compile(
            r"\{\{=request_(.*?);/\*.*?\*/\}\}"
        )
        
        # Pattern for simple request field access: {{=request_field}}
        self.simple_request_pattern = re.compile(
            r"\{\{=request_(.*?)\}\}"
        )
    
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
        text = self.date_delta_pattern_plain.sub(
            r"{{now offset='\2 days' format='\1'}}", 
            text
        )
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
    
    def convert_helpers(self, text: str) -> str:
        """Convert all CA LISA helpers in the text to WireMock Handlebars helpers.
        
        Args:
            text: The text containing CA LISA helpers
            
        Returns:
            Text with CA LISA helpers converted to WireMock Handlebars helpers
        """
        if not text:
            return text
            
        # Apply conversions in order
        text = self.convert_date_delta(text)
        text = self.xpath_pattern.sub(self.convert_xpath, text)
        text = self.simple_request_pattern.sub(self.convert_simple_request, text)
        
        return text
    
    def convert_request_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Convert helpers in request body content.
        
        Args:
            body: RequestBody or ResponseBody object
            
        Returns:
            Body object with converted content
        """
        if body and hasattr(body, 'content') and body.content:
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
