import xml.etree.ElementTree as ET
import json
import os
import sys
from typing import Dict, Optional, Tuple
import re
from pathlib import Path

class VSIConverter:
    """Handle conversion of VSI files to WireMock mappings."""
    
    def __init__(self, vsi_file_path: str):
        self.vsi_file_path = Path(vsi_file_path)
        self.output_dir = self.vsi_file_path.with_suffix('')/'mappings'
        self.date_delta_pattern = re.compile(
            r"\{\{=doDateDeltaFromCurrent\(&quot;(.*?)&quot;,&quot;([-+]?\d+)D&quot;\);.*?\}\}"
        )
        self.xpath_pattern = re.compile(
            r"\{\{=request_(.*?);/\*.*?\*/\}\}"
        )
    
    def convert_date_delta(self, text: str) -> str:
        """Convert date delta format to WireMock format."""
        return self.date_delta_pattern.sub(
            r"{{now offset='\2 days' format='\1'}}", 
            text
        )
    
    def convert_xpath(self, match: re.Match) -> str:
        """Convert xpath format to WireMock format."""
        xpath_value = match.group(1).replace('_', '/')
        return f"{{{{xPath request.body '//{xpath_value}/text()'}}}}"
    
    def convert_helpers(self, text: str) -> str:
        """Convert all helpers in the text."""
        text = self.convert_date_delta(text)
        return self.xpath_pattern.sub(self.convert_xpath, text)
    
    def create_wiremock_mapping(self, request_data: str, response_data: str) -> Dict:
        """Create WireMock mapping dictionary."""
        return {
            "request": {
                "method": "POST",
                "urlPath": "/api/service",
                "bodyPatterns": [{"equalToXml": request_data}]
            },
            "response": {
                "status": 200,
                "body": response_data,
                "headers": {"Content-Type": "application/xml"},
                "transformers": ["response-template"]
            }
        }
    
    def extract_request_response(self, sp_element: ET.Element) -> Optional[Dict]:
        """Extract request and response data from SP element."""
        request_data = None
        response_data = None
        
        # Find request data
        request_elem = sp_element.find(".//rq/bd")
        if request_elem is not None and request_elem.text:
            request_data = self.convert_helpers(request_elem.text)
        
        # Find response data
        response_elem = sp_element.find(".//rs/rp/bd")
        if response_elem is not None and response_elem.text:
            response_data = self.convert_helpers(response_elem.text)
        
        if request_data and response_data:
            return self.create_wiremock_mapping(request_data, response_data)
        return None
    
    def process(self) -> None:
        """Process the VSI file and create WireMock mappings."""
        try:
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Parse XML
            tree = ET.parse(self.vsi_file_path)
            root = tree.getroot()
            
            # Process each 't' element
            for i, sp in enumerate(root.iter('t')):
                mapping = self.extract_request_response(sp)
                if mapping:
                    output_file = self.output_dir/f"namespace-mapping-{i}.json"
                    with output_file.open('w') as f:
                        json.dump(mapping, f, indent=4)
            
            print(f"\nMapping files created: {list(self.output_dir.glob('*.json'))}")
            
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python vsiConverter.py <vsi_file_path>")
        sys.exit(1)
    
    converter = VSIConverter(sys.argv[1])
    converter.process()

if __name__ == "__main__":
    main()