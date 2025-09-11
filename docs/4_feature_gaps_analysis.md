# Feature Gaps Analysis: CA LISA DevTest Helper Functions

**Document Version:** 1.0  
**Created:** 2024  
**Status:** Analysis Complete - Implementation Pending

## Overview

This document captures the comprehensive analysis of CA LISA / Broadcom DevTest helper functions and VSI elements that are not currently supported by the VSI to WireMock converter. The analysis reveals significant gaps in helper function coverage that should be systematically addressed to improve conversion accuracy and completeness.

## Current Implementation Status

### ✅ Currently Supported Helpers
The application currently handles only a minimal set of CA LISA helpers:

1. **Date Delta Helpers**
   - `doDateDeltaFromCurrent("format","offsetD")` → `{{now offset='X days' format='Y'}}`
   - Supports both HTML-encoded and plain formats

2. **Request Field Access**
   - `request_field` patterns → `{{xPath request.body '//field/text()'}}`
   - Basic XPath extraction from request bodies

### ❌ Missing Helper Functions (High Priority)

#### 1. Random Data Generation Helpers
These are commonly used in VSI files for generating dynamic test data:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doRandomString(length)` | `{{randomValue type='ALPHANUMERIC' length='X'}}` | HIGH | Generate random strings |
| `doRandomNumber(min, max)` | `{{randomValue type='NUMBER' min='X' max='Y'}}` | HIGH | Generate random numbers |
| `doRandomDate(startDate, endDate)` | `{{randomValue type='DATE' min='X' max='Y'}}` | HIGH | Generate random dates |
| `doRandomTime()` | `{{randomValue type='TIME'}}` | HIGH | Generate random times |
| `doRandomBoolean()` | `{{randomValue type='BOOLEAN'}}` | HIGH | Generate random boolean values |
| `doRandomEmail()` | `{{randomValue type='EMAIL'}}` | MEDIUM | Generate random email addresses |
| `doRandomSSN()` | `{{randomValue type='SSN'}}` | MEDIUM | Generate random SSNs |
| `doRandomCreditCard()` | `{{randomValue type='CREDIT_CARD'}}` | MEDIUM | Generate random credit card numbers |

#### 2. Current Date/Time Helpers
Essential for dynamic timestamp generation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doGetCurrentDate()` | `{{now format='yyyy-MM-dd'}}` | HIGH | Get current date |
| `doGetCurrentTime()` | `{{now format='HH:mm:ss'}}` | HIGH | Get current time |
| `doGetCurrentDateTime()` | `{{now format='yyyy-MM-dd HH:mm:ss'}}` | HIGH | Get current date and time |
| `doGetTimestamp()` | `{{now format='yyyy-MM-dd HH:mm:ss.SSS'}}` | HIGH | Get current timestamp |
| `doGetCurrentYear()` | `{{now format='yyyy'}}` | MEDIUM | Get current year |
| `doGetCurrentMonth()` | `{{now format='MM'}}` | MEDIUM | Get current month |
| `doGetCurrentDay()` | `{{now format='dd'}}` | MEDIUM | Get current day |

#### 3. Mathematical Calculation Helpers
For dynamic calculations in responses:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doCalculate(expression)` | `{{math expression}}` | HIGH | Evaluate mathematical expressions |
| `doAdd(a, b)` | `{{math 'a + b'}}` | MEDIUM | Addition |
| `doSubtract(a, b)` | `{{math 'a - b'}}` | MEDIUM | Subtraction |
| `doMultiply(a, b)` | `{{math 'a * b'}}` | MEDIUM | Multiplication |
| `doDivide(a, b)` | `{{math 'a / b'}}` | MEDIUM | Division |
| `doModulo(a, b)` | `{{math 'a % b'}}` | LOW | Modulo operation |
| `doRound(number, decimals)` | `{{math 'round(number, decimals)'}}` | LOW | Round numbers |

### ❌ Missing Helper Functions (Medium Priority)

#### 4. String Manipulation Helpers
For dynamic string processing:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doConcat(string1, string2)` | `{{concat string1 string2}}` | MEDIUM | String concatenation |
| `doSubstring(string, start, length)` | `{{substring string start length}}` | MEDIUM | Extract substring |
| `doToUpperCase(string)` | `{{upper string}}` | MEDIUM | Convert to uppercase |
| `doToLowerCase(string)` | `{{lower string}}` | MEDIUM | Convert to lowercase |
| `doTrim(string)` | `{{trim string}}` | MEDIUM | Remove whitespace |
| `doReplace(string, old, new)` | `{{replace string old new}}` | MEDIUM | Replace text |
| `doLength(string)` | `{{length string}}` | LOW | Get string length |

#### 5. Data Formatting Helpers
For consistent data presentation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doFormatDate(date, format)` | `{{formatDate date format}}` | MEDIUM | Format dates |
| `doFormatNumber(number, format)` | `{{formatNumber number format}}` | MEDIUM | Format numbers |
| `doFormatCurrency(amount, currency)` | `{{formatCurrency amount currency}}` | LOW | Format currency |
| `doPadLeft(string, length, char)` | `{{padLeft string length char}}` | LOW | Left pad strings |
| `doPadRight(string, length, char)` | `{{padRight string length char}}` | LOW | Right pad strings |

#### 6. Data Validation Helpers
For input validation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doIsValidEmail(email)` | `{{isValidEmail email}}` | LOW | Validate email format |
| `doIsValidSSN(ssn)` | `{{isValidSSN ssn}}` | LOW | Validate SSN format |
| `doIsValidCreditCard(card)` | `{{isValidCreditCard card}}` | LOW | Validate credit card format |
| `doIsValidDate(date)` | `{{isValidDate date}}` | LOW | Validate date format |
| `doIsValidNumber(number)` | `{{isValidNumber number}}` | LOW | Validate number format |

### ❌ Missing Helper Functions (Low Priority)

#### 7. Data Transformation Helpers
For data encoding/decoding:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doBase64Encode(string)` | `{{base64Encode string}}` | LOW | Base64 encoding |
| `doBase64Decode(string)` | `{{base64Decode string}}` | LOW | Base64 decoding |
| `doMD5Hash(string)` | `{{md5Hash string}}` | LOW | MD5 hashing |
| `doSHA1Hash(string)` | `{{sha1Hash string}}` | LOW | SHA1 hashing |
| `doSHA256Hash(string)` | `{{sha256Hash string}}` | LOW | SHA256 hashing |
| `doURLEncode(string)` | `{{urlEncode string}}` | LOW | URL encoding |
| `doURLDecode(string)` | `{{urlDecode string}}` | LOW | URL decoding |

#### 8. Data Extraction Helpers
For extracting data from various formats:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doExtractFromXML(xml, xpath)` | `{{xPath xml xpath}}` | MEDIUM | Extract data from XML |
| `doExtractFromJSON(json, jsonpath)` | `{{jsonPath json jsonpath}}` | MEDIUM | Extract data from JSON |
| `doExtractFromCSV(csv, column)` | `{{csvExtract csv column}}` | LOW | Extract data from CSV |
| `doExtractFromRegex(text, pattern)` | `{{regexExtract text pattern}}` | LOW | Extract data using regex |

#### 9. Data Generation Helpers
For generating unique identifiers:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doGenerateUUID()` | `{{uuid}}` | MEDIUM | Generate UUIDs |
| `doGenerateGUID()` | `{{uuid}}` | MEDIUM | Generate GUIDs |
| `doGenerateSequence(start, step)` | `{{sequence start step}}` | LOW | Generate sequences |
| `doGenerateCounter()` | `{{counter}}` | LOW | Generate counters |
| `doGenerateRandomString(length, charset)` | `{{randomValue type='ALPHANUMERIC' length='X' charset='Y'}}` | LOW | Generate random strings with custom charset |

### ❌ Missing VSI-Specific Elements

#### 10. State Management Helpers
For maintaining state across requests:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doSetProperty(name, value)` | `{{setProperty name value}}` | HIGH | Set properties |
| `doGetProperty(name)` | `{{getProperty name}}` | HIGH | Get properties |
| `doClearProperty(name)` | `{{clearProperty name}}` | MEDIUM | Clear properties |
| `doIncrementProperty(name)` | `{{incrementProperty name}}` | MEDIUM | Increment properties |
| `doDecrementProperty(name)` | `{{decrementProperty name}}` | MEDIUM | Decrement properties |

#### 11. Correlation Helpers
For request correlation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doSetCorrelationId(id)` | `{{setCorrelationId id}}` | MEDIUM | Set correlation IDs |
| `doGetCorrelationId()` | `{{getCorrelationId}}` | MEDIUM | Get correlation IDs |
| `doGenerateCorrelationId()` | `{{generateCorrelationId}}` | MEDIUM | Generate correlation IDs |

#### 12. Session Management Helpers
For session handling:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doSetSessionValue(key, value)` | `{{setSessionValue key value}}` | LOW | Set session values |
| `doGetSessionValue(key)` | `{{getSessionValue key}}` | LOW | Get session values |
| `doClearSession()` | `{{clearSession}}` | LOW | Clear session |

#### 13. File System Helpers
For file operations:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doReadFile(filename)` | `{{readFile filename}}` | LOW | Read file contents |
| `doWriteFile(filename, content)` | `{{writeFile filename content}}` | LOW | Write file contents |
| `doFileExists(filename)` | `{{fileExists filename}}` | LOW | Check if file exists |
| `doGetFileSize(filename)` | `{{getFileSize filename}}` | LOW | Get file size |

### ❌ Missing VSI Structure Elements

#### 14. Advanced Selection Logic Support
Currently captures `selectionLogic.js` but may not handle:
- Complex conditional logic
- Weighted random selection
- State-based selection
- Time-based selection
- Custom selection algorithms

#### 15. Advanced Latency Patterns
Currently supports uniform and fixed latency, but missing:
- Exponential distribution
- Normal distribution
- Custom distribution functions
- Conditional latency based on request content
- Time-based latency variations

#### 16. Advanced Header Handling
- Dynamic header generation
- Header validation
- Header transformation
- Conditional headers
- Header correlation

#### 17. Advanced Body Handling
- Dynamic body generation
- Body validation
- Body transformation
- Conditional body content
- Body correlation

## Implementation Roadmap

### Phase 1: Core Random Data Generation (High Priority)
- Implement random string, number, date, time, and boolean generators
- Add current date/time helpers
- Implement basic mathematical calculations

### Phase 2: String and Data Manipulation (Medium Priority)
- Add string manipulation helpers
- Implement data formatting functions
- Add data validation helpers

### Phase 3: Advanced Features (Low Priority)
- Implement data transformation helpers
- Add data extraction functions
- Implement state management helpers

### Phase 4: VSI-Specific Elements (Future)
- Enhance selection logic support
- Add advanced latency patterns
- Implement advanced header/body handling

## Technical Considerations

### 1. WireMock Handlebars Compatibility
- Ensure all helper functions map to valid WireMock Handlebars helpers
- Some functions may require custom Handlebars helpers
- Consider fallback strategies for unsupported functions

### 2. Pattern Matching
- Update regex patterns in `HelperConverter` class
- Handle both HTML-encoded and plain formats
- Support nested function calls

### 3. Error Handling
- Graceful degradation for unsupported functions
- Warning messages for missing helpers
- Fallback to original text when conversion fails

### 4. Testing Strategy
- Create test VSI files with each helper function
- Verify correct WireMock output
- Test edge cases and error conditions

## Success Metrics

- **Coverage**: Support for 80%+ of common CA LISA helper functions
- **Accuracy**: 95%+ correct conversion rate
- **Performance**: No significant impact on conversion speed
- **Compatibility**: Works with both WireMock Cloud and OSS

## Conclusion

The current implementation covers only a small fraction of the helper functions available in CA LISA/DevTest VSI files. This comprehensive analysis provides a clear roadmap for systematically addressing these gaps, starting with the most commonly used random data generation and date/time helpers.

Implementing these features will significantly improve the conversion accuracy and completeness of the VSI to WireMock converter, making it a more robust and reliable tool for migrating from DevTest to WireMock.

---

**Next Steps:**
1. Review and prioritize helper functions based on actual VSI file analysis
2. Design implementation approach for Phase 1 helpers
3. Create test cases for each helper function
4. Implement helper conversion logic in `HelperConverter` class
5. Update documentation and examples
