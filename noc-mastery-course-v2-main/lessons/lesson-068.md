# Lesson 68: 10DLC Registration and Compliance

**Module 1 | Section 1.17 — Messaging**
**⏱ ~6min read | Prerequisites: Lesson 182 (Telnyx Messaging API)**

---

## Introduction

Since 2021, US carriers (T-Mobile, AT&T, and others) require **Application-to-Person (A2P)** messages sent from standard 10-digit long codes (10DLC) to be registered through **The Campaign Registry (TCR)**. Unregistered A2P traffic faces heavy filtering and throttling. As a NOC engineer, you'll troubleshoot registration failures, throughput limits, and compliance blocks daily.

---

## What Is A2P 10DLC?

**A2P (Application-to-Person)** = messages sent by a business application to end users. This is distinct from **P2P (Person-to-Person)** = messages between individuals.

Before 10DLC, businesses sent A2P traffic from regular long codes (designed for P2P), causing:
- Carrier spam filters blocking legitimate messages
- No sender identity verification
- No throughput guarantees
- Shared infrastructure congestion

10DLC solves this by creating a **registered identity → campaign → number** hierarchy:

```
Brand (Business Identity)
  └── Campaign (Use Case)
        └── Phone Numbers (Sending numbers)
              └── Messages (Actual traffic)
```

---

## The Campaign Registry (TCR)

TCR is the central database that carriers query to verify A2P senders.

### Registration Hierarchy

```
┌─────────────────────────────────────────┐
│  CSP (Campaign Service Provider)         │
│  = Telnyx (registered with TCR)          │
│                                          │
│  ┌───────────────────────────────────┐   │
│  │  Brand (Your Customer)            │   │
│  │  - Legal name, EIN, address       │   │
│  │  - Trust Score assigned by TCR    │   │
│  │                                   │   │
│  │  ┌─────────────────────────────┐  │   │
│  │  │  Campaign                   │  │   │
│  │  │  - Use case (2FA, marketing)│  │   │
│  │  │  - Sample messages          │  │   │
│  │  │  - Opt-in description       │  │   │
│  │  │  - Phone numbers attached   │  │   │
│  │  └─────────────────────────────┘  │   │
│  └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## Brand Registration

The brand represents the business entity sending messages.

### Required Brand Information

```json
{
  "entity_type": "PRIVATE_PROFIT",
  "legal_name": "Acme Health Inc.",
  "display_name": "Acme Health",
  "ein": "12-3456789",
  "phone": "+15551234567",
  "street": "123 Main St",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US",
  "email": "compliance@acmehealth.com",
  "website": "https://acmehealth.com",
  "vertical": "HEALTHCARE"
}
```

### Entity Types

| Type | Description | Trust Score Range |
|------|-------------|-------------------|
| PRIVATE_PROFIT | Standard corporation/LLC | 1-100 |
| PUBLIC_PROFIT | Publicly traded company | Usually 75+ |
| NON_PROFIT | 501(c)(3) organization | Varies |
| GOVERNMENT | Government entity | Usually 75+ |
| SOLE_PROPRIETOR | Individual (limited support) | Low (1-30) |

---

## Trust Scores and Throughput

TCR assigns a **Trust Score** (1-100) based on brand verification. This directly controls messaging throughput:

### Trust Score → Throughput Mapping

```
Trust Score    T-Mobile MPS    AT&T MPS    Daily Cap
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   1-24            0.2           1          2,000
  25-49            0.5           1         10,000
  50-74            2.0          10         50,000
  75-100          75.0          75        200,000+
```

🔧 **NOC Tip:** When a customer reports slow message delivery, check their trust score first. A score of 15 means they're limited to 0.2 MPS on T-Mobile — that's 1 message every 5 seconds. This isn't a Telnyx issue; it's carrier-enforced throttling based on TCR trust.

---

## Campaign Types

Each campaign declares a use case. The type affects approval likelihood and carrier treatment.

### Standard Campaign Types

| Type | Use Case | Example |
|------|----------|---------|
| **TRANSACTIONAL** | Account notifications | "Your order shipped" |
| **2FA** | Authentication codes | "Your code is 847293" |
| **MARKETING** | Promotions | "50% off this weekend!" |
| **CUSTOMER_CARE** | Support conversations | "Your ticket #123 is resolved" |
| **ACCOUNT_NOTIFICATION** | Alerts | "Payment received" |
| **CHARITY** | Donations | "Text GIVE to donate" |
| **EMERGENCY** | Public safety | "Evacuation notice" |
| **POLLING** | Surveys | "Rate 1-5" |
| **MIXED** | Multiple use cases | Combination of above |

### Campaign Registration via Telnyx API

```bash
curl -X POST https://api.telnyx.com/10dlc/campaign \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "brand_id": "brand_abc123",
    "use_case": "MARKETING",
    "description": "Weekly promotional offers to opted-in subscribers",
    "sample_message_1": "Hi {name}, 50% off all items this weekend! Reply STOP to unsubscribe.",
    "sample_message_2": "Flash sale! Use code SAVE20 for 20% off. Reply STOP to opt out.",
    "message_flow": "Users opt in via web form at example.com/subscribe",
    "opt_in_type": "WEB_FORM",
    "opt_in_keywords": "START, SUBSCRIBE",
    "opt_out_keywords": "STOP, UNSUBSCRIBE, CANCEL",
    "help_keywords": "HELP, INFO",
    "number_pool": false,
    "subscriber_optin": true,
    "subscriber_optout": true,
    "subscriber_help": true
  }'
```

🔧 **NOC Tip:** Campaign rejections are usually due to: (1) vague use case descriptions, (2) sample messages not matching declared use case, (3) missing opt-out language. Coach customers to be specific and include "Reply STOP to unsubscribe" in samples.

---

## The Vetting Process

### Standard Vetting (Free, Automatic)

TCR automatically scores brands based on:
- Business registry match (EIN verification)
- Web presence
- Business age
- Industry vertical

### Enhanced Vetting (Paid, Manual)

For higher trust scores, brands can request enhanced vetting:

```
Standard vetting:  Score 1-75 (automated)
Enhanced vetting:  Score up to 100 (manual review, ~$40)
Appeal:            Re-review if score seems wrong
```

🔧 **NOC Tip:** If a legitimate large enterprise gets a low trust score (< 50), recommend enhanced vetting. The $40 fee is worth it for the 10-50x throughput increase. Check brand details for common issues: misspelled legal name, wrong EIN, or website domain mismatch.

---

## Telnyx 10DLC Registration Flow

```
Step 1: Customer creates Brand via Telnyx API/Portal
          → Telnyx submits to TCR
          → TCR returns Trust Score (usually within minutes)

Step 2: Customer creates Campaign
          → Telnyx submits to TCR
          → TCR returns campaign_id
          → Carrier review begins (T-Mobile: auto, AT&T: manual)
          → AT&T review takes 2-7 business days

Step 3: Customer assigns phone numbers to campaign
          → Numbers registered with carriers
          → A2P routing activated

Step 4: Customer sends messages
          → Carrier checks registration
          → Throughput limits enforced per trust score
```

### Registration Statuses

```
BRAND:
  PENDING    → Submitted to TCR
  VERIFIED   → TCR accepted, score assigned
  FAILED     → TCR rejected (bad data)

CAMPAIGN:
  PENDING    → Submitted to carriers
  APPROVED   → All carriers approved
  REJECTED   → One or more carriers rejected
  SUSPENDED  → Carrier suspended for violations
  EXPIRED    → Annual renewal missed
```

---

## Compliance Monitoring

### What Gets You Suspended

```
❌ Sending without opt-in consent
❌ Not honoring STOP/opt-out requests
❌ Content doesn't match declared campaign type
❌ Sharing/selling phone numbers between campaigns
❌ Sending prohibited content (SHAFT: Sex, Hate, Alcohol, Firearms, Tobacco)
❌ Exceeding throughput limits (carrier blocks excess)
```

### Carrier Enforcement Actions

```
Level 1: Throttling      — Messages queued/delayed
Level 2: Filtering       — Messages silently dropped
Level 3: Number blocking — Sending number blacklisted
Level 4: Campaign suspend — All numbers in campaign blocked
Level 5: Brand ban       — All campaigns for brand blocked
```

🔧 **NOC Tip:** If messages suddenly stop delivering and DLRs show `REJECTD`, check if the campaign was suspended. In Mission Control → Messaging → 10DLC, look for status changes. Carrier suspensions require a compliance review and remediation plan before reinstatement.

---

## Real-World NOC Scenario

**Scenario:** Customer migrated to Telnyx and is sending marketing SMS, but only 20% are delivering to T-Mobile.

**Investigation:**

1. Check if 10DLC registration exists — `GET /v2/10dlc/campaigns`
2. Brand trust score = 18 (low!) → throughput = 0.2 MPS on T-Mobile
3. Customer is trying to send 500 messages/minute → 99.6% are being throttled
4. Remaining deliveries are trickling through at carrier-enforced rate
5. **Resolution:** Recommend enhanced vetting to improve trust score, or use toll-free/short code for higher throughput

```bash
# Check brand trust score
curl https://api.telnyx.com/v2/10dlc/brands/brand_abc123
# Look for: "trust_score": 18
```

---

## Key Takeaways

1. **10DLC is mandatory** for A2P messaging on US long codes — unregistered traffic gets filtered
2. **Brand → Campaign → Numbers** is the registration hierarchy managed through TCR
3. **Trust scores directly control throughput** — a score of 20 means ~0.2 MPS on T-Mobile
4. **Campaign approval takes time** — T-Mobile auto-approves; AT&T manually reviews (2-7 days)
5. **Enhanced vetting** ($40) can dramatically improve trust scores for legitimate businesses
6. **Compliance violations lead to suspension** — monitor campaign statuses proactively
7. **NOC engineers should check 10DLC status first** when troubleshooting US messaging delivery

---

**Next: Lesson 184 — Short Codes and High-Throughput Messaging**
