"""
Tests for unsupported CA LISA helper detection and warning system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from vsi2wm.helper_converter import HelperConverter, detect_unsupported_helpers, get_unsupported_helpers, clear_unsupported_helpers
from vsi2wm.core import VSIConverter
from vsi2wm.ir import RequestBody, ResponseBody


class TestHelperConverter:
    """Test the HelperConverter class for unsupported helper detection."""
    
    def test_detect_unsupported_helpers_basic(self):
        """Test basic detection of unsupported helpers."""
        converter = HelperConverter()
        
        # Test with unsupported helpers (random helpers are now supported)
        text = "Hello {{=doUnknownHelper()}} and {{=doAnotherUnknown()}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        assert len(unsupported) == 2
        assert "{{=doUnknownHelper()}}" in unsupported
        assert "{{=doAnotherUnknown()}}" in unsupported
    
    def test_detect_unsupported_helpers_mixed(self):
        """Test detection with mix of supported and unsupported helpers."""
        converter = HelperConverter()
        
        text = "Date: {{=doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\")}} Random: {{=doRandomString(5)}} Unknown: {{=doUnknownHelper()}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        # Should only detect the unsupported one (random helpers are now supported)
        assert len(unsupported) == 1
        assert "{{=doUnknownHelper()}}" in unsupported
    
    def test_detect_unsupported_helpers_none(self):
        """Test detection when no unsupported helpers are present."""
        converter = HelperConverter()
        
        text = "Date: {{=doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\")}} Field: {{=request_user_id}} Random: {{=doRandomString(10)}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        assert len(unsupported) == 0
    
    def test_detect_unsupported_helpers_empty(self):
        """Test detection with empty or None text."""
        converter = HelperConverter()
        
        assert converter.detect_unsupported_helpers("") == []
        assert converter.detect_unsupported_helpers(None) == []
    
    def test_replace_unsupported_helpers(self):
        """Test replacement of unsupported helpers with fallback text."""
        converter = HelperConverter()
        
        text = "Hello {{=doUnknownHelper()}} and {{=doAnotherUnknown()}}"
        result = converter.replace_unsupported_helpers(text)
        
        expected = "Hello [UNSUPPORTED: doUnknownHelper()] and [UNSUPPORTED: doAnotherUnknown()]"
        assert result == expected
    
    def test_replace_unsupported_helpers_mixed(self):
        """Test replacement with mix of supported and unsupported helpers."""
        converter = HelperConverter()
        
        text = "Date: {{=doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\")}} Random: {{=doRandomString(5)}} Unknown: {{=doUnknownHelper()}}"
        result = converter.replace_unsupported_helpers(text)
        
        # Supported helpers should remain unchanged, unsupported should be replaced
        assert "{{=doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\")}}" in result
        assert "{{=doRandomString(5)}}" in result  # Now supported
        assert "[UNSUPPORTED: doUnknownHelper()]" in result
    
    def test_convert_helpers_with_unsupported(self):
        """Test full conversion process with unsupported helpers."""
        converter = HelperConverter()
        
        text = "Date: {{=doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\")}} Random: {{=doRandomString(5)}} Unknown: {{=doUnknownHelper()}}"
        result = converter.convert_helpers(text)
        
        # Should convert supported helpers and replace unsupported ones
        assert "{{now offset='+1 days' format='yyyy-MM-dd'}}" in result
        assert "{{randomValue type='ALPHANUMERIC' length='5'}}" in result  # Now supported
        assert "[UNSUPPORTED: doUnknownHelper()]" in result
    
    def test_get_unsupported_helpers(self):
        """Test getting list of unsupported helpers."""
        converter = HelperConverter()
        
        # Clear any previous state
        converter.clear_unsupported_helpers()
        
        # Process text with unsupported helpers (random helpers are now supported)
        converter.detect_unsupported_helpers("{{=doUnknownHelper()}} and {{=doAnotherUnknown()}}")
        
        unsupported = converter.get_unsupported_helpers()
        assert len(unsupported) == 2
        assert "{{=doUnknownHelper()}}" in unsupported
        assert "{{=doAnotherUnknown()}}" in unsupported
    
    def test_clear_unsupported_helpers(self):
        """Test clearing unsupported helpers list."""
        converter = HelperConverter()
        
        # Add some unsupported helpers
        converter.detect_unsupported_helpers("{{=doUnknownHelper()}}")
        assert len(converter.get_unsupported_helpers()) == 1
        
        # Clear and verify
        converter.clear_unsupported_helpers()
        assert len(converter.get_unsupported_helpers()) == 0
    
    def test_convert_headers(self):
        """Test conversion of headers with unsupported helpers."""
        converter = HelperConverter()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {{=doRandomString(20)}}",
            "X-Custom": "{{=doRandomNumber(1,100)}}",
            "X-Unknown": "{{=doUnknownHelper()}}"
        }
        
        result = converter.convert_headers(headers)
        
        assert result["Content-Type"] == "application/json"  # No helpers, unchanged
        assert result["Authorization"] == "Bearer {{randomValue type='ALPHANUMERIC' length='20'}}"  # Now supported
        assert result["X-Custom"] == "{{randomInt lower=1 upper=100}}"  # Now supported
        assert result["X-Unknown"] == "[UNSUPPORTED: doUnknownHelper()]"
    
    def test_convert_request_body(self):
        """Test conversion of request body with unsupported helpers."""
        converter = HelperConverter()
        
        body = RequestBody(type="json", content='{"id": {{=doRandomNumber(1,100)}}, "name": "{{=doRandomString(10)}}", "unknown": "{{=doUnknownHelper()}}"}')
        result = converter.convert_request_body(body)
        
        assert "{{randomInt lower=1 upper=100}}" in result.content  # Now supported
        assert "{{randomValue type='ALPHANUMERIC' length='10'}}" in result.content  # Now supported
        assert "[UNSUPPORTED: doUnknownHelper()]" in result.content
    
    def test_convert_response_body(self):
        """Test conversion of response body with unsupported helpers."""
        converter = HelperConverter()
        
        body = ResponseBody(type="json", content='{"result": "{{=doRandomString(5)}}", "unknown": "{{=doUnknownHelper()}}"}')
        result = converter.convert_response_body(body)
        
        assert "{{randomValue type='ALPHANUMERIC' length='5'}}" in result.content  # Now supported
        assert "[UNSUPPORTED: doUnknownHelper()]" in result.content


class TestConvenienceFunctions:
    """Test the convenience functions for unsupported helper detection."""
    
    def test_detect_unsupported_helpers_function(self):
        """Test the detect_unsupported_helpers convenience function."""
        text = "Hello {{=doUnknownHelper()}}"
        unsupported = detect_unsupported_helpers(text)
        
        assert len(unsupported) == 1
        assert "{{=doUnknownHelper()}}" in unsupported
    
    def test_get_unsupported_helpers_function(self):
        """Test the get_unsupported_helpers convenience function."""
        # Clear any previous state
        clear_unsupported_helpers()
        
        # Process some text
        detect_unsupported_helpers("{{=doUnknownHelper()}}")
        
        unsupported = get_unsupported_helpers()
        assert len(unsupported) == 1
        assert "{{=doUnknownHelper()}}" in unsupported
    
    def test_clear_unsupported_helpers_function(self):
        """Test the clear_unsupported_helpers convenience function."""
        # Add some helpers
        detect_unsupported_helpers("{{=doUnknownHelper()}}")
        assert len(get_unsupported_helpers()) == 1
        
        # Clear and verify
        clear_unsupported_helpers()
        assert len(get_unsupported_helpers()) == 0


class TestVSIConverterStrictMode:
    """Test the VSIConverter with strict mode enabled."""
    
    def test_strict_mode_without_unsupported_helpers(self):
        """Test strict mode when no unsupported helpers are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple VSI file without unsupported helpers
            vsi_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <serviceImage>
                <t id="1">
                    <rq>
                        <method>GET</method>
                        <url>/test</url>
                    </rq>
                    <rs>
                        <rp id="1">
                            <status>200</status>
                            <bd>{"message": "Hello World"}</bd>
                        </rp>
                    </rs>
                </t>
            </serviceImage>'''
            
            vsi_file = temp_path / "test.vsi"
            vsi_file.write_text(vsi_content)
            
            converter = VSIConverter(
                input_file=vsi_file,
                output_dir=temp_path / "output",
                strict_mode=True
            )
            
            # Should succeed without errors
            exit_code = converter.convert()
            assert exit_code == 0
    
    def test_strict_mode_with_unsupported_helpers(self):
        """Test strict mode when unsupported helpers are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a VSI file with unsupported helpers
            vsi_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <serviceImage>
                <t id="1">
                    <rq>
                        <method>GET</method>
                        <url>/test</url>
                    </rq>
                    <rs>
                        <rp id="1">
                            <status>200</status>
                            <bd>{"message": "{{=doUnknownHelper()}}"}</bd>
                        </rp>
                    </rs>
                </t>
            </serviceImage>'''
            
            vsi_file = temp_path / "test.vsi"
            vsi_file.write_text(vsi_content)
            
            converter = VSIConverter(
                input_file=vsi_file,
                output_dir=temp_path / "output",
                strict_mode=True
            )
            
            # Should fail with exit code 1
            exit_code = converter.convert()
            assert exit_code == 1
    
    def test_normal_mode_with_unsupported_helpers(self):
        """Test normal mode when unsupported helpers are found (should succeed with warnings)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a VSI file with unsupported helpers
            vsi_content = '''<?xml version="1.0" encoding="UTF-8"?>
            <serviceImage>
                <t id="1">
                    <rq>
                        <method>GET</method>
                        <url>/test</url>
                    </rq>
                    <rs>
                        <rp id="1">
                            <status>200</status>
                            <bd>{"message": "{{=doUnknownHelper()}}"}</bd>
                        </rp>
                    </rs>
                </t>
            </serviceImage>'''
            
            vsi_file = temp_path / "test.vsi"
            vsi_file.write_text(vsi_content)
            
            converter = VSIConverter(
                input_file=vsi_file,
                output_dir=temp_path / "output",
                strict_mode=False  # Normal mode
            )
            
            # Should succeed with warnings
            exit_code = converter.convert()
            assert exit_code == 0
            
            # Check that warnings were generated
            assert len(converter.report.warnings) > 0
            unsupported_warnings = [w for w in converter.report.warnings if "Unsupported CA LISA helper" in w]
            assert len(unsupported_warnings) > 0


class TestComplexScenarios:
    """Test complex scenarios with multiple unsupported helpers."""
    
    def test_multiple_unsupported_helpers_in_different_locations(self):
        """Test detection of unsupported helpers in headers, request body, and response body."""
        converter = HelperConverter()
        
        # Test headers
        headers = {"X-Token": "{{=doUnknownHelper()}}"}
        converter.convert_headers(headers)
        
        # Test request body
        req_body = RequestBody(type="json", content='{"id": {{=doAnotherUnknown()}}}')
        converter.convert_request_body(req_body)
        
        # Test response body
        resp_body = ResponseBody(type="json", content='{"result": "{{=doThirdUnknown()}}"}')
        converter.convert_response_body(resp_body)
        
        unsupported = converter.get_unsupported_helpers()
        assert len(unsupported) == 3
        assert "{{=doUnknownHelper()}}" in unsupported
        assert "{{=doAnotherUnknown()}}" in unsupported
        assert "{{=doThirdUnknown()}}" in unsupported
    
    def test_nested_helpers(self):
        """Test detection of nested or complex helper expressions."""
        converter = HelperConverter()
        
        text = "Complex: {{=doFormatDate(doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\"),\"MM/dd/yyyy\")}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        # Should detect the entire complex expression as unsupported
        assert len(unsupported) == 1
        assert "{{=doFormatDate(doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\"),\"MM/dd/yyyy\")}}" in unsupported
    
    def test_html_encoded_helpers(self):
        """Test detection of HTML-encoded helper expressions."""
        converter = HelperConverter()
        
        text = "Encoded: {{=doUnknownHelper()}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        assert len(unsupported) == 1
        assert "{{=doUnknownHelper()}}" in unsupported


if __name__ == "__main__":
    pytest.main([__file__])
