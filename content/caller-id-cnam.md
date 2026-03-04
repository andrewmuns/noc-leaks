---
title: "Number Lookup and Caller Identity (CNAM)"
description: "Learn about number lookup and caller identity (cnam)"
module: "Module 1: Foundations"
lesson: "5"
difficulty: "Beginner"
duration: "5 minutes"
objectives:
  - Understand number lookup and caller identity (cnam)
slug: "caller-id-cnam"
---


## Introduction

Number Lookup and CNAM are identity services that answer the questions: "Who owns this number?", "What carrier serves it?", and "What name should display on caller ID?" For NOC engineers, these tools are indispensable for debugging routing issues, verifying number ownership, and understanding why calls show incorrect caller names.

---

## Number Lookup — What It Reveals

A number lookup query returns rich metadata about a phone number:

```bash
curl -X GET "https://api.telnyx.com/v2/number_lookup/+15551234567" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```json
{
  "data": {
    "phone_number": "+15551234567",
    "country_code": "US",
    "national_format": "(555) 123-4567",
    "carrier": {
      "name": "T-Mobile USA",
      "type": "mobile",
      "mobile_country_code": "310",
      "mobile_network_code": "260"
    },
    "portability": {
      "ported": true,
      "original_carrier": "AT&T",
      "ported_date": "2024-06-15"
    },
    "caller_name": {
      "caller_name": "JOHN SMITH",
      "error_code": null
    },
    "line_type": "mobile",
    "valid": true,
    "fraud_score": 12
  }
}
```

### Key Fields for NOC Use

| Field | NOC Use Case |
|-------|-------------|
| **carrier.name** | Identify which carrier to troubleshoot with |
| **carrier.type** | mobile/landline/voip — affects routing decisions |

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios
- ✅ Practice quizzes and assessments

[**🚀 Unlock Full Course Access**](https://teleponymastery.com/enroll)

---

*Preview shows approximately 25% of the full lesson content.*