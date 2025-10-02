# Feature Gaps Analysis: CA LISA DevTest Helper Functions

**Document Version:** 1.0  
**Created:** 2025  
**Status:** 7 of 85 helpers implemented

## Overview

This document captures the comprehensive analysis of CA LISA / Broadcom DevTest helper functions and VSI elements that are not currently supported by the VSI to WireMock converter. The analysis reveals significant gaps in helper function coverage that should be systematically addressed to improve conversion accuracy and completeness.

## Current Implementation Status

### ✅ Currently Supported Helpers
The application currently handles the following CA LISA helpers:

1. **Date Delta Helpers**
   - `doDateDeltaFromCurrent("format","offsetD")` → `{{now offset='X days' format='Y'}}`
   - Supports both HTML-encoded and plain formats

2. **Request Field Access**
   - `request_field` patterns → `{{xPath request.body '//field/text()'}}`
   - Basic XPath extraction from request bodies

3. **Random Data Generation Helpers**
   - `doRandomString(length)` → `{{randomValue type='ALPHANUMERIC' length='X'}}`
   - `doRandomNumber(min, max)` → `{{randomInt lower=X upper=Y}}`
   - `doRandomBoolean()` → `{{pickRandom true false}}`
   - `doRandomEmail()` → `{{random 'Internet.safeEmailAddress'}}`
   - `doRandomSSN()` → `{{random 'IdNumber.ssnValid'}}`
   - `doRandomCreditCard()` → `{{random 'Business.creditCardNumber'}}`

### ❌ Missing Helper Functions (High Priority)

#### 1. Random Data Generation Helpers 
These are commonly used in VSI files for generating dynamic test data:

| CA LISA Helper | WireMock Equivalent | Priority | Status |
|---|---|---|---|
| `doRandomDate(startDate, endDate)` | `{{randomValue type='DATE' min='X' max='Y'}}` | HIGH | ❌ **PENDING** |
| `doRandomTime()` | `{{randomValue type='TIME'}}` | HIGH | ❌ **PENDING** |

#### 2. Date and Time Helpers
For dynamic date/time generation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doCurrentDate()` | `{{now format='yyyy-MM-dd'}}` | HIGH | Current date |
| `doCurrentTime()` | `{{now format='HH:mm:ss'}}` | HIGH | Current time |
| `doCurrentDateTime()` | `{{now format='yyyy-MM-dd HH:mm:ss'}}` | HIGH | Current date and time |
| `doDateAdd(date, days)` | `{{dateOffset date days}}` | MEDIUM | Add days to date |
| `doDateSubtract(date, days)` | `{{dateOffset date -days}}` | MEDIUM | Subtract days from date |
| `doDateDiff(date1, date2)` | `{{dateDiff date1 date2}}` | LOW | Calculate date difference |

#### 3. Mathematical Operations
For calculations and data manipulation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doAdd(a, b)` | `{{add a b}}` | HIGH | Addition |
| `doSubtract(a, b)` | `{{subtract a b}}` | HIGH | Subtraction |
| `doMultiply(a, b)` | `{{multiply a b}}` | HIGH | Multiplication |
| `doDivide(a, b)` | `{{divide a b}}` | HIGH | Division |
| `doModulo(a, b)` | `{{modulo a b}}` | MEDIUM | Modulo operation |
| `doRound(number, decimals)` | `{{round number decimals}}` | MEDIUM | Round numbers |
| `doCeiling(number)` | `{{ceiling number}}` | LOW | Ceiling function |
| `doFloor(number)` | `{{floor number}}` | LOW | Floor function |

#### 4. String Manipulation Helpers
For text processing:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doConcat(string1, string2)` | `{{concat string1 string2}}` | HIGH | Concatenate strings |
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
For parsing and extracting data:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doExtractJSON(json, path)` | `{{jsonPath json path}}` | MEDIUM | Extract from JSON |
| `doExtractXML(xml, xpath)` | `{{xPath xml xpath}}` | MEDIUM | Extract from XML |
| `doExtractRegex(text, pattern)` | `{{regexExtract text pattern}}` | LOW | Extract with regex |
| `doExtractCSV(csv, column)` | `{{csvExtract csv column}}` | LOW | Extract CSV column |

#### 9. Data Generation Helpers
For creating test data:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doGenerateUUID()` | `{{uuid}}` | MEDIUM | Generate UUID |
| `doGenerateGUID()` | `{{guid}}` | MEDIUM | Generate GUID |
| `doGenerateSequence(start, step)` | `{{sequence start step}}` | LOW | Generate sequence |
| `doGenerateCounter()` | `{{counter}}` | LOW | Generate counter |

#### 10. Data Comparison Helpers
For conditional logic:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doEquals(a, b)` | `{{equals a b}}` | MEDIUM | Equality check |
| `doNotEquals(a, b)` | `{{notEquals a b}}` | MEDIUM | Inequality check |
| `doGreaterThan(a, b)` | `{{greaterThan a b}}` | MEDIUM | Greater than |
| `doLessThan(a, b)` | `{{lessThan a b}}` | MEDIUM | Less than |
| `doContains(string, substring)` | `{{contains string substring}}` | MEDIUM | String contains |
| `doStartsWith(string, prefix)` | `{{startsWith string prefix}}` | LOW | String starts with |
| `doEndsWith(string, suffix)` | `{{endsWith string suffix}}` | LOW | String ends with |

#### 11. Data Conversion Helpers
For type conversion:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doToString(value)` | `{{toString value}}` | MEDIUM | Convert to string |
| `doToNumber(string)` | `{{toNumber string}}` | MEDIUM | Convert to number |
| `doToBoolean(value)` | `{{toBoolean value}}` | LOW | Convert to boolean |
| `doToDate(string)` | `{{toDate string}}` | LOW | Convert to date |

#### 12. Data Aggregation Helpers
For data processing:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doSum(array)` | `{{sum array}}` | LOW | Sum array values |
| `doAverage(array)` | `{{average array}}` | LOW | Average array values |
| `doMin(array)` | `{{min array}}` | LOW | Minimum value |
| `doMax(array)` | `{{max array}}` | LOW | Maximum value |
| `doCount(array)` | `{{count array}}` | LOW | Count elements |

#### 13. Data Selection Helpers
For conditional data selection:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doIf(condition, trueValue, falseValue)` | `{{if condition trueValue falseValue}}` | MEDIUM | Conditional selection |
| `doChoose(index, values...)` | `{{choose index values}}` | LOW | Choose from values |
| `doSwitch(value, cases...)` | `{{switch value cases}}` | LOW | Switch statement |

#### 14. Data State Helpers
For maintaining state across requests:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doSetVariable(name, value)` | `{{setVariable name value}}` | LOW | Set variable |
| `doGetVariable(name)` | `{{getVariable name}}` | LOW | Get variable |
| `doIncrementVariable(name)` | `{{incrementVariable name}}` | LOW | Increment variable |
| `doDecrementVariable(name)` | `{{decrementVariable name}}` | LOW | Decrement variable |

#### 15. Data Correlation Helpers
For request/response correlation:

| CA LISA Helper | WireMock Equivalent | Priority | Notes |
|---|---|---|---|
| `doExtractFromRequest(path)` | `{{xPath request.body path}}` | MEDIUM | Extract from request |
| `doExtractFromResponse(path)` | `{{xPath response.body path}}` | MEDIUM | Extract from response |
| `doCorrelateValue(name, value)` | `{{correlate name value}}` | LOW | Correlate values |

### ❌ Missing VSI Elements (Future)

#### 16. Advanced Selection Logic
- Complex conditional statements
- Nested if-then-else logic
- Loop constructs
- Time-based latency variations

#### 17. Advanced Header Handling
- Dynamic header generation
- Header validation
- Header transformation
- Conditional headers
- Header correlation

#### 18. Advanced Body Handling
- Dynamic body generation
- Body validation
- Body transformation
- Conditional body content
- Body correlation

## Implementation Roadmap

### Phase 1: Core Random Data Generation (High Priority) ✅ **COMPLETED**
- ✅ Implement random string, number, and boolean generators
- ✅ Add random email, SSN, and credit card generators
- ❌ Implement random date and time generators (pending)
- ❌ Add current date/time helpers (pending)
- ❌ Implement basic mathematical calculations (pending)

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

The current implementation has been significantly enhanced with the addition of 6 random data generation helper functions. This represents a major step forward in improving conversion accuracy and completeness. The comprehensive analysis provides a clear roadmap for systematically addressing the remaining gaps, with the next priority being date/time helpers and mathematical operations.

**Recent Progress:**
- ✅ **6 random data generation helpers implemented** (doRandomString, doRandomNumber, doRandomBoolean, doRandomEmail, doRandomSSN, doRandomCreditCard)
- ✅ **Enhanced JSON body handling** for Handlebars templates
- ✅ **Comprehensive test coverage** for new helper functions

Implementing the remaining features will further improve the conversion accuracy and completeness of the VSI to WireMock converter, making it a more robust and reliable tool for migrating from DevTest to WireMock.

---

**Next Steps:**
1. ✅ ~~Review and prioritize helper functions based on actual VSI file analysis~~ **COMPLETED**
2. ✅ ~~Design implementation approach for Phase 1 helpers~~ **COMPLETED**
3. ✅ ~~Create test cases for each helper function~~ **COMPLETED**
4. ✅ ~~Implement helper conversion logic in `HelperConverter` class~~ **COMPLETED**
5. ✅ ~~Update documentation and examples~~ **COMPLETED**
6. **NEW:** Implement remaining random data helpers (doRandomDate, doRandomTime)
7. **NEW:** Implement current date/time helpers (doCurrentDate, doCurrentTime, doCurrentDateTime)
8. **NEW:** Implement mathematical operations (doAdd, doSubtract, doMultiply, doDivide)



