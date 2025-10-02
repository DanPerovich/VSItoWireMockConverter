"""
Tests for random data generation helper functions.
"""

import pytest
from vsi2wm.helper_converter import HelperConverter


class TestRandomHelpers:
    """Test the random helper conversion functions."""
    
    def test_convert_random_string(self):
        """Test conversion of doRandomString helper."""
        converter = HelperConverter()
        
        # Test basic conversion
        text = "Token: {{=doRandomString(10)}}"
        result = converter.convert_helpers(text)
        expected = "Token: {{randomValue type='ALPHANUMERIC' length='10'}}"
        assert result == expected
        
        # Test with different length
        text = "ID: {{=doRandomString(20)}}"
        result = converter.convert_helpers(text)
        expected = "ID: {{randomValue type='ALPHANUMERIC' length='20'}}"
        assert result == expected
    
    def test_convert_random_number(self):
        """Test conversion of doRandomNumber helper."""
        converter = HelperConverter()
        
        # Test basic conversion
        text = "Age: {{=doRandomNumber(18, 65)}}"
        result = converter.convert_helpers(text)
        expected = "Age: {{randomInt lower=18 upper=65}}"
        assert result == expected
        
        # Test with different range
        text = "Score: {{=doRandomNumber(1, 100)}}"
        result = converter.convert_helpers(text)
        expected = "Score: {{randomInt lower=1 upper=100}}"
        assert result == expected
    
    def test_convert_random_boolean(self):
        """Test conversion of doRandomBoolean helper."""
        converter = HelperConverter()
        
        text = "Active: {{=doRandomBoolean()}}"
        result = converter.convert_helpers(text)
        expected = "Active: {{pickRandom true false}}"
        assert result == expected
    
    def test_convert_random_email(self):
        """Test conversion of doRandomEmail helper."""
        converter = HelperConverter()
        
        text = "Email: {{=doRandomEmail()}}"
        result = converter.convert_helpers(text)
        expected = "Email: {{random 'Internet.safeEmailAddress'}}"
        assert result == expected
    
    def test_convert_random_ssn(self):
        """Test conversion of doRandomSSN helper."""
        converter = HelperConverter()
        
        text = "SSN: {{=doRandomSSN()}}"
        result = converter.convert_helpers(text)
        expected = "SSN: {{random 'IdNumber.ssnValid'}}"
        assert result == expected
    
    def test_convert_random_credit_card(self):
        """Test conversion of doRandomCreditCard helper."""
        converter = HelperConverter()
        
        text = "Card: {{=doRandomCreditCard()}}"
        result = converter.convert_helpers(text)
        expected = "Card: {{random 'Business.creditCardNumber'}}"
        assert result == expected
    
    def test_multiple_random_helpers(self):
        """Test conversion of multiple random helpers in one text."""
        converter = HelperConverter()
        
        text = "User: {{=doRandomString(8)}}, Age: {{=doRandomNumber(21, 80)}}, Active: {{=doRandomBoolean()}}, Email: {{=doRandomEmail()}}"
        result = converter.convert_helpers(text)
        expected = "User: {{randomValue type='ALPHANUMERIC' length='8'}}, Age: {{randomInt lower=21 upper=80}}, Active: {{pickRandom true false}}, Email: {{random 'Internet.safeEmailAddress'}}"
        assert result == expected
    
    def test_random_helpers_with_other_helpers(self):
        """Test random helpers mixed with other supported helpers."""
        converter = HelperConverter()
        
        text = "Date: {{=doDateDeltaFromCurrent(\"yyyy-MM-dd\",\"+1D\")}}, Token: {{=doRandomString(16)}}, User: {{=request_user_id}}"
        result = converter.convert_helpers(text)
        expected = "Date: {{now offset='+1 days' format='yyyy-MM-dd'}}, Token: {{randomValue type='ALPHANUMERIC' length='16'}}, User: {{xPath request.body '//user/id/text()'}}"
        assert result == expected
    
    def test_random_helpers_not_unsupported(self):
        """Test that random helpers are no longer detected as unsupported."""
        converter = HelperConverter()
        
        text = "Token: {{=doRandomString(10)}}, Age: {{=doRandomNumber(18, 65)}}, Active: {{=doRandomBoolean()}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        # Should not detect any of the random helpers as unsupported
        assert len(unsupported) == 0
    
    def test_random_helpers_with_unsupported_helpers(self):
        """Test random helpers mixed with truly unsupported helpers."""
        converter = HelperConverter()
        
        text = "Token: {{=doRandomString(10)}}, Unknown: {{=doUnknownHelper()}}"
        unsupported = converter.detect_unsupported_helpers(text)
        
        # Should only detect the unknown helper as unsupported
        assert len(unsupported) == 1
        assert "{{=doUnknownHelper()}}" in unsupported
    
    def test_random_helpers_in_headers(self):
        """Test random helpers in header values."""
        converter = HelperConverter()
        
        headers = {
            "X-Token": "{{=doRandomString(20)}}",
            "X-Request-ID": "{{=doRandomNumber(1000, 9999)}}",
            "X-Active": "{{=doRandomBoolean()}}"
        }
        
        result = converter.convert_headers(headers)
        
        assert result["X-Token"] == "{{randomValue type='ALPHANUMERIC' length='20'}}"
        assert result["X-Request-ID"] == "{{randomInt lower=1000 upper=9999}}"
        assert result["X-Active"] == "{{pickRandom true false}}"
    
    def test_random_helpers_in_json_body(self):
        """Test random helpers in JSON request/response bodies."""
        from vsi2wm.ir import RequestBody, ResponseBody
        
        converter = HelperConverter()
        
        # Test request body
        req_body = RequestBody(
            type="json", 
            content='{"name": "{{=doRandomString(10)}}", "age": {{=doRandomNumber(18, 65)}}, "active": {{=doRandomBoolean()}}}'
        )
        result = converter.convert_request_body(req_body)
        
        expected_content = '{"name": "{{randomValue type=\'ALPHANUMERIC\' length=\'10\'}}", "age": {{randomInt lower=18 upper=65}}, "active": {{pickRandom true false}}}'
        assert result.content == expected_content
        
        # Test response body
        resp_body = ResponseBody(
            type="json",
            content='{"id": {{=doRandomNumber(1, 1000)}}, "email": "{{=doRandomEmail()}}", "ssn": "{{=doRandomSSN()}}"}'
        )
        result = converter.convert_response_body(resp_body)
        
        expected_content = '{"id": {{randomInt lower=1 upper=1000}}, "email": "{{random \'Internet.safeEmailAddress\'}}", "ssn": "{{random \'IdNumber.ssnValid\'}}"}'
        assert result.content == expected_content


if __name__ == "__main__":
    pytest.main([__file__])
