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
| **portability.ported** | Was number ported? Original carrier still in NPAC? |
| **line_type** | Can this number receive SMS? (landline = usually no) |
| **valid** | Is this a real, dialable number? |
| **fraud_score** | Risk indicator (0-100) for fraud detection |

> **💡 NOC Tip:** en a customer says "calls to +1555XXXXXXX aren't connecting," your first move should be a number lookup. If the number was recently ported, routing databases may not have updated yet. Check `portability.ported` and `ported_date` — if ported within the last 24-48 hours, LNP propagation delay is likely the cause.
slug: "caller-id-cnam"
---

## How Number Lookup Works Internally

```
Telnyx Number Lookup API
  → Query NPAC (Number Portability Administration Center)
      → Returns: LRN (Location Routing Number), ported status
  → Query carrier databases (MCC/MNC for mobile)
  → Query LIDB (Line Information Database) for CNAM
  → Aggregate and return results
```

### Data Sources

```
NPAC          — Porting status, LRN, original/current carrier
HLR/HSS       — Mobile subscriber status (active, roaming)
LIDB           — Caller name (CNAM) database
Carrier DBs    — Line type, MCC/MNC
Third-party    — Fraud scoring, spam databases
```

---

## CNAM — Caller Name Delivery

### How CNAM Works

When a call arrives, the terminating carrier performs a **CNAM dip** to look up the caller's name:

```
Incoming call: FROM +15551234567
  → Terminating switch queries CNAM database (LIDB)
  → LIDB returns: "JOHN SMITH"
  → Caller ID displays: "JOHN SMITH  555-123-4567"
```

### CNAM Database Architecture

```
Originating carrier                Terminating carrier
      │                                   │
      │  (does NOT send name)             │
      │  ── INVITE (From: +15551234567) ──>│
      │                                   │
      │                          CNAM dip │──→ LIDB
      │                                   │←── "JOHN SMITH"
      │                                   │
      │                          Display to│
      │                          called party
```

**Important:** The originating carrier does NOT send the caller's name in the SIP INVITE. The terminating carrier looks it up independently. This is why the same number can show different names on different carriers — they may query different CNAM databases.

> **💡 NOC Tip:** stomer says "my caller ID shows the wrong name." This is a CNAM database issue, not a Telnyx issue. The name is stored in LIDB by whichever carrier owns the number. To update CNAM: (1) For Telnyx numbers, update via the portal/API. (2) For ported numbers, ensure the CNAM record was updated post-port. CNAM propagation takes 24-72 hours.
slug: "caller-id-cnam"
---

## Updating CNAM for Telnyx Numbers

```bash
# Update caller ID name for a Telnyx number
curl -X PATCH "https://api.telnyx.com/v2/phone_numbers/+15551234567" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "cnam_listing": {
      "enabled": true,
      "name": "ACME CORP"
    }
  }'
```

### CNAM Constraints

```
Max length:     15 characters
Allowed chars:  A-Z, 0-9, spaces, hyphens, periods
Case:           Stored uppercase
Propagation:    24-72 hours to reach all carrier databases
Cost:           Typically included with number or small monthly fee
```

---

## Line Type Detection

Line type is critical for messaging and routing decisions:

```
MOBILE     — Can receive SMS, supports MMS, cellular voice
LANDLINE   — Voice only (no SMS without text-enabling)
VOIP       — Internet-based, may have limited SMS support
TOLL_FREE  — 8XX numbers, special routing
PAGER      — Legacy (rare)
UNKNOWN    — Carrier didn't return type information
```

### Why Line Type Matters for NOC

```
Scenario: Customer sends SMS to +15551234567, gets error

Number Lookup → line_type: "landline"

Root cause: Landlines can't receive SMS by default.
Solution: Customer needs to use a text-enabled landline 
          service, or switch to voice-based delivery.
```

> **💡 NOC Tip:** fore troubleshooting SMS delivery failures, always check line type. About 15% of "SMS not delivered" tickets are simply messages sent to landlines. A quick number lookup saves 20 minutes of investigation.
slug: "caller-id-cnam"
---

## Fraud Scoring

Telnyx Number Lookup includes a fraud risk score:

```
Score 0-20:   Low risk — Normal consumer/business number
Score 21-50:  Moderate — Some risk indicators
Score 51-80:  High — Multiple fraud signals
Score 81-100: Very high — Known fraud association
```

### Fraud Indicators

```
- Number recently activated (< 30 days)
- Number associated with known fraud campaigns
- High volume of short-duration calls (robocall pattern)
- Number on carrier spam/fraud blocklists
- Unusual porting activity (frequent port-in/port-out)
```

---

## Batch Lookups

For high-volume use cases, Telnyx supports batch number lookups:

```bash
curl -X POST "https://api.telnyx.com/v2/number_lookup/batch" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "phone_numbers": [
      "+15551234567",
      "+15559876543",
      "+447700900123"
    ]
  }'
```

> **💡 NOC Tip:** en investigating widespread routing issues to a specific carrier, batch lookup a sample of affected numbers. If they all show the same carrier and porting status, the issue is likely on that carrier's side.
slug: "caller-id-cnam"
---

## Real-World NOC Scenario

**Scenario:** Customer reports outbound calls display "UNKNOWN" on recipient caller ID instead of their business name.

**Investigation:**

1. Check CNAM listing for the customer's Telnyx number:
   ```bash
   curl https://api.telnyx.com/v2/phone_numbers/+15551234567
   ```
2. Is `cnam_listing.enabled` = true? If false, CNAM was never set up.
3. If enabled, when was it last updated? CNAM takes 24-72 hours to propagate.
4. If set up correctly and propagated, the issue may be carrier-specific. Some carriers (especially mobile) don't always display CNAM.
5. For ported numbers: verify CNAM was re-registered after porting to Telnyx.

**Resolution:** Enable CNAM listing, set the business name, wait 48 hours, then test by calling a landline (landlines display CNAM most reliably).

---

## Key Takeaways

1. **Number Lookup reveals carrier, line type, port status, and fraud score** — your first debugging tool
2. **CNAM is a terminating-side lookup** — the called party's carrier queries LIDB independently
3. **CNAM propagation takes 24-72 hours** — set expectations with customers
4. **Line type detection prevents wasted effort** — SMS to landlines will always fail
5. **Fraud scores help flag suspicious numbers** before they cause damage
6. **Ported numbers may have stale data** — always check `portability.ported_date`
7. **Batch lookups** are efficient for investigating carrier-wide issues
slug: "caller-id-cnam"
---

**Next: Lesson 187 — Verify API: Two-Factor Authentication**
