# VSI to WireMock Mapping Rules

This document explains how CA LISA / Broadcom DevTest VSI elements are mapped to WireMock stub mappings.

## Overview

The VSI to WireMock converter transforms DevTest virtualization definitions into WireMock-compatible stub mappings. The conversion process involves:

1. **Parsing** VSI XML structure
2. **Building** an Intermediate Representation (IR)
3. **Mapping** IR elements to WireMock JSON format
4. **Writing** output files with proper organization

## VSI Structure Understanding

### VSI Layouts

DevTest VSI files can use two different layouts:

#### Model-Based Layout (`<bd>` elements)
```xml
<serviceImage>
  <transactions>
    <t id="transaction_id">
      <rq>
        <m>
          <method>GET</method>
          <path>/api/users</path>
        </m>
        <bd>request body</bd>
      </rq>
      <rs>
        <rp id="variant_id">
          <m>
            <status>200</status>
            <latency ms="100-200">range</latency>
            <weight>0.8</weight>
          </m>
          <bd>response body</bd>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>
```

#### RR-Pairs Layout (`<reqData>/<rspData>` elements)
```xml
<serviceImage>
  <transactions>
    <t id="transaction_id">
      <rq>
        <m>
          <method>POST</method>
          <path>/api/users</path>
        </m>
        <reqData>
          <bd>request body</bd>
        </reqData>
      </rq>
      <rs>
        <rp id="variant_id">
          <m>
            <status>201</status>
            <latency ms="150">fixed</latency>
            <weight>0.9</weight>
          </m>
          <rspData>
            <bd>response body</bd>
          </rspData>
        </rp>
      </rs>
    </t>
  </transactions>
</serviceImage>
```

## Request Mapping Rules

### HTTP Method
**VSI:** `<method>GET</method>`
**WireMock:** `"method": "GET"`

### URL Path
**VSI:** `<path>/api/users</path>`
**WireMock:** `"urlPath": "/api/users"`

### Headers
**VSI:**
```xml
<headers>
  <header name="Content-Type">application/json</header>
  <header name="Authorization">Bearer token123</header>
</headers>
```

**WireMock:**
```json
{
  "headers": {
    "Content-Type": {
      "equalTo": "application/json"
    },
    "Authorization": {
      "equalTo": "Bearer token123"
    }
  }
}
```

### Query Parameters
**VSI:**
```xml
<query>
  <param name="page">1</param>
  <param name="limit">10</param>
</query>
```

**WireMock:**
```json
{
  "queryParameters": {
    "page": {
      "equalTo": "1"
    },
    "limit": {
      "equalTo": "10"
    }
  }
}
```

### Request Body

#### JSON Body
**VSI:**
```xml
<bd><![CDATA[{"name": "John", "email": "john@example.com"}]]></bd>
```

**WireMock:**
```json
{
  "bodyPatterns": [
    {
      "equalToJson": "{\"name\": \"John\", \"email\": \"john@example.com\"}",
      "ignoreArrayOrder": true,
      "ignoreExtraElements": true
    }
  ]
}
```

#### XML Body
**VSI:**
```xml
<bd><![CDATA[<user><name>John</name><email>john@example.com</email></user>]]></bd>
```

**WireMock:**
```json
{
  "bodyPatterns": [
    {
      "equalToXml": "<user><name>John</name><email>john@example.com</email></user>"
    }
  ]
}
```

#### Plain Text Body
**VSI:**
```xml
<bd>Hello World</bd>
```

**WireMock:**
```json
{
  "bodyPatterns": [
    {
      "equalTo": "Hello World"
    }
  ]
}
```

### SOAP-Specific Mapping

#### SOAPAction Header
**VSI:**
```xml
<soapAction>urn:Service#Operation</soapAction>
```

**WireMock:**
```json
{
  "headers": {
    "SOAPAction": {
      "equalTo": "urn:Service#Operation"
    }
  }
}
```

#### SOAP Body
**VSI:**
```xml
<bd><![CDATA[<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <getUser>
      <id>123</id>
    </getUser>
  </soapenv:Body>
</soapenv:Envelope>]]></bd>
```

**WireMock:**
```json
{
  "bodyPatterns": [
    {
      "equalToXml": "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\"><soapenv:Body><getUser><id>123</id></getUser></soapenv:Body></soapenv:Envelope>"
    }
  ]
}
```

## Response Mapping Rules

### HTTP Status
**VSI:** `<status>200</status>`
**WireMock:** `"status": 200`

### Response Headers
**VSI:**
```xml
<rspData>
  <h>
    <n>Content-Type</n>
    <v>application/json</v>
  </h>
</rspData>
```

**WireMock:**
```json
{
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Response Body

#### JSON Response
**VSI:**
```xml
<bd><![CDATA[{"id": 123, "name": "John Doe", "email": "john@example.com"}]]></bd>
```

**WireMock:**
```json
{
  "jsonBody": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### XML Response
**VSI:**
```xml
<bd><![CDATA[<user><id>123</id><name>John Doe</name><email>john@example.com</email></user>]]></bd>
```

**WireMock:**
```json
{
  "body": "<user><id>123</id><name>John Doe</name><email>john@example.com</email></user>"
}
```

#### Plain Text Response
**VSI:**
```xml
<bd>Success</bd>
```

**WireMock:**
```json
{
  "body": "Success"
}
```

### Latency Mapping

#### Range Latency
**VSI:**
```xml
<latency ms="100-200">range</latency>
```

**WireMock:**
```json
{
  "delayDistribution": {
    "type": "uniform",
    "lower": 100,
    "upper": 200
  }
}
```

#### Fixed Latency
**VSI:**
```xml
<latency ms="150">fixed</latency>
```

**WireMock:**
```json
{
  "fixedDelayMilliseconds": 150
}
```

## Priority and Metadata

### Priority Assignment
**VSI:** `<weight>0.8</weight>`
**WireMock:** `"priority": 0` (higher weights get lower priority numbers)

The converter assigns priorities in descending order of weight:
- Weight 1.0 → Priority 0
- Weight 0.8 → Priority 1
- Weight 0.5 → Priority 2
- etc.

### DevTest Metadata
**VSI:**
```xml
<t id="GET#/users">
  <rp id="success">
    <m>
      <matchScript language="js"><![CDATA[request.page == "1"]]></matchScript>
    </m>
  </rp>
</t>
```

**WireMock:**
```json
{
  "metadata": {
    "devtest_transaction_id": "GET#/users",
    "devtest_variant_weight": 0.8,
    "devtest_selection_logic": "request.page == \"1\""
  }
}
```

## Response Templates

All WireMock stubs include the `response-template` transformer:

```json
{
  "response": {
    "transformers": ["response-template"]
  }
}
```

This enables dynamic response generation and template processing in WireMock.

## Large File Handling

When response bodies exceed the `--max-file-size` threshold (default: 1MB), they are split into separate files:

**Original stub:**
```json
{
  "response": {
    "body": "very large response content..."
  }
}
```

**Split stub:**
```json
{
  "response": {
    "bodyFileName": "stub_0_0_body.json"
  }
}
```

**File content (`__files/stub_0_0_body.json`):**
```
very large response content...
```

## Tradeoffs and Limitations

### Supported Protocols
- **HTTP/HTTPS only**: MQ and other protocols are skipped
- **HTTP methods**: GET, POST, PUT, DELETE, PATCH, etc.
- **Content types**: JSON, XML, plain text

### Latency Mapping
- **Range latency**: Converted to uniform distribution (not normal or exponential)
- **Fixed latency**: Preserved as-is
- **No latency**: No delay added

### Body Matching
- **JSON**: Uses `equalToJson` with array order and extra element ignoring
- **XML**: Uses `equalToXml` (exact matching)
- **Text**: Uses `equalTo` (exact matching)

### Selection Logic
- **JavaScript**: Embedded in metadata (not executed by WireMock)
- **Complex logic**: May need manual adjustment for WireMock compatibility

### File Size Limits
- **Large bodies**: Automatically split to `__files/` directory
- **Configurable threshold**: Set via `--max-file-size` parameter
- **Performance**: Large files may impact conversion speed

## Best Practices

### Before Conversion
1. **Validate VSI files** in DevTest Studio
2. **Review selection logic** for compatibility
3. **Check for non-HTTP protocols** (will be skipped)
4. **Backup original files**

### After Conversion
1. **Review generated stubs** for accuracy
2. **Test stub functionality** in WireMock
3. **Adjust priorities** if needed
4. **Monitor performance** with new latency settings
5. **Verify large file handling** for big responses

### Optimization
1. **Use appropriate file size limits** for your environment
2. **Consider stub organization** for complex services
3. **Review metadata** for debugging purposes
4. **Test with real traffic** to validate behavior
