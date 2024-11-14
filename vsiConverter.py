import xml.etree.ElementTree as ET
import json
import os
import sys
import re

# Replacement function to convert each match to the required XPath format
def replace_with_xpath(match):
    # Replace underscores with slashes and add "/text()" at the end
    xpath_value = match.group(1).replace('_', '/')
    return f"{{{{xPath request.body '//{xpath_value}/text()'}}}}"

# Function to convert Dev/Test CA LISA helpers to WMC helpers
def convertHelpers(inputText, caller):
    outputText = None
    workingText = inputText

    ###Replace doDateDeltaFromCurrent
    # Pattern to match the specific format
    pattern = r"\{\{=doDateDeltaFromCurrent\(&quot;(.*?)&quot;,&quot;([-+]?\d+)D&quot;\);.*?\}\}"
    # Replacement format string
    replacement = r"{{now offset='\2 days' format='\1'}}"
    # Replace all matches in the input string
    workingText = re.sub(pattern, replacement, workingText)
    
    ###Replace XPath helpers
    # Regular expression to capture the relevant part between "{{=request_" and ";/*"
    pattern = r"\{\{=request_(.*?);/\*.*?\*/\}\}"

    # Substitute matches in the text using the pattern and replacement function
    workingText = re.sub(pattern, replace_with_xpath, workingText)

    outputText = workingText
    return outputText

# Function to create WireMock mapping files without the "id" field
def create_wiremock_mapping_without_id(request_data, response_data):
    mapping = {
        "request": {
            "method": "POST",
            "urlPath": "/api/service",  # Placeholder URL
            "bodyPatterns": [{"equalToXml": request_data}]
        },
        "response": {
            "status": 200,
            "body": response_data,
            "headers": {"Content-Type": "application/xml"},
            "transformers": ["response-template"]
        },
    }
    return mapping

# Function to handle the extraction of <p> and the response body from <bd> inside <rp> under <rs>
def extract_request_response_with_namespace(sp_element):
    request_data = None
    response_data = None

    # Handle namespaces by searching for the correct elements using a wildcard for the namespace
    ns = {'ns': 'http://some-namespace-url'}  # Placeholder for the actual namespace URI

    # Search for <p> element with n="recorded_raw_request"
    for p in sp_element.findall(".//rq/bd", ns):
        request_data = p.text

        # Search for Dev/Test specific items and convert them to WireMock format
        request_data = convertHelpers(request_data, 'req')

    # Search for the response body inside <rs>/<rp>/<bd>
    bd_element = sp_element.find('.//rs/rp/bd', ns)
    if bd_element is not None:
        response_data = bd_element.text

        # Search for Dev/Test specific helpers and convert them to WireMock handlebar format
        response_data = convertHelpers(response_data, 'rsp')

    # Create a WireMock mapping if both request and response are found
    if request_data and response_data:
        return create_wiremock_mapping_without_id(request_data, response_data)
    return None

# total arguments
n = len(sys.argv)
print("Total arguments passed:", n)

# Arguments passed
print("\nName of Python script:", sys.argv[0])
print("\nArguments passed:", end = " ")
for i in range(1, n):
    print(sys.argv[i], end = " ")

# Path to the .vsi file
#vsi_file_path = 'ZelleFIS.vsi'
vsi_file_path = sys.argv[1]

# Parse the XML file
tree = ET.parse(vsi_file_path)
root = tree.getroot()

# Directory to store the WireMock mapping files
output_dir = vsi_file_path.split('.')[0] + "/mappings"
os.makedirs(output_dir, exist_ok=True)

# Create WireMock mappings for each <sp> element
mappings_with_namespace = []
for i, sp in enumerate(root.iter('t')):
    mapping = extract_request_response_with_namespace(sp)
    if mapping:
        mappings_with_namespace.append(mapping)
        # Save the mapping to a file without "id"
        mapping_file_path = os.path.join(output_dir, f"namespace-mapping-{i}.json")
        with open(mapping_file_path, 'w') as mapping_file:
            json.dump(mapping, mapping_file, indent=4)

# List the created mapping files
print("\n\nMapping files created:", os.listdir(output_dir))