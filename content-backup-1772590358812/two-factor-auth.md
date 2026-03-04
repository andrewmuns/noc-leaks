---
title: "Verify API — Two-Factor Authentication"
description: "Learn about verify api — two-factor authentication"
module: "Module 1: Foundations"
lesson: "6"
difficulty: "Beginner"
duration: "5 minutes"
objectives:
  - Understand verify api — two-factor authentication
slug: "two-factor-auth"
---

## Introduction

Two-factor authentication (2FA) via SMS or voice is one of the highest-volume messaging use cases. The Telnyx Verify API provides a managed OTP (One-Time Password) service that handles code generation, delivery, rate limiting, and fraud prevention. For NOC engineers, Verify is a critical path — when it breaks, customers' users can't log in.

---

## How OTP Verification Works

### The Verification Lifecycle

```
1. INITIATE  — App requests verification for +15559876543
2. GENERATE  — Telnyx generates OTP (e.g., 847293)
3. DELIVER   — OTP sent via SMS, voice call, or WhatsApp
4. SUBMIT    — User enters code in the app
5. VERIFY    — App sends code to Telnyx for validation
6. RESULT    — Telnyx returns: verified ✓ or failed ✗
```

```
   Customer App              Telnyx Verify             User
       │                          │                      │
       │── POST /verifications ──>│                      │
       │<── verification_id ──────│                      │
       │                          │── SMS: "847293" ────>│
       │                          │                      │
       │                          │      (user enters)   │
       │── POST /verify_code ────>│                      │
       │<── status: verified ─────│                      │
```
slug: "two-factor-auth"
---

## Using the Verify API

### Step 1: Create a Verify Profile

```bash
curl -X POST https://api.telnyx.com/v2/verify_profiles \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "Acme Login Verification",
    "default_timeout_secs": 300,
    "messaging_enabled": true,
    "rcs_enabled": false,
    "call_enabled": true,
    "whatsapp_enabled": false,
    "messaging_template": "Your Acme verification code is {code}. Valid for 5 minutes.",
    "code_length": 6,
    "app_id": null
  }'
```

### Step 2: Initiate Verification

```bash
curl -X POST https://api.telnyx.com/v2/verifications \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "verify_profile_id": "vp_abc123",
    "phone_number": "+15559876543",
    "type": "sms",
    "timeout_secs": 300
  }'
```

```json
{
  "data": {
    "id": "ver_xyz789",
    "status": "pending",
    "phone_number": "+15559876543",
    "type": "sms",
    "created_at": "2026-02-23T10:00:00Z",
    "timeout_secs": 300
  }
}
```

### Step 3: Verify the Code

```bash
curl -X POST https://api.telnyx.com/v2/verifications/ver_xyz789/actions/verify \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{ "code": "847293" }'
```

```json
{
  "data": {
    "id": "ver_xyz789",
    "status": "verified",
    "phone_number": "+15559876543",
    "response_code": "accepted"
  }
}
```

---

## Delivery Channels

### SMS (Primary)

```
Pros:  Universal reach, fast delivery (<5 seconds typical)
Cons:  Vulnerable to SIM swap, SS7 interception
Cost:  Standard SMS rate + verify fee
```

### Voice Call (Fallback)

```
Pros:  Works on landlines, higher trust perception
Cons:  Slower (user must listen), requires attention
Flow:  Telnyx calls the number and reads the code via TTS
       "Your verification code is: 8. 4. 7. 2. 9. 3."
```

### WhatsApp (Where Available)

```
Pros:  Delivered via data (works without SMS signal), rich formatting
Cons:  Requires WhatsApp installed, regional availability
Flow:  OTP delivered as WhatsApp Business message
```

### Fallback Chain

```
Attempt 1: SMS delivery
  → If fails after 30s: retry SMS
  → If fails again: 
Attempt 2: Voice call
  → If no answer:
Attempt 3: Return failure to customer app
```

> **💡 NOC Tip:**  a customer reports low verification success rates, check the delivery channel breakdown. If SMS delivery rate drops for a specific carrier, the voice fallback should compensate. If both channels fail, the issue is likely the destination number (landline, VOIP, or invalid).
slug: "two-factor-auth"
---

## Rate Limiting and Fraud Prevention

### Built-in Protections

```
Per-number limits:
  - Max 5 verification attempts per phone number per 10 minutes
  - Max 10 per hour
  - Max 20 per 24 hours

Per-IP limits (if customer passes IP):
  - Max 10 verifications per IP per hour

Cooldown:
  - After failed verification, 30-second cooldown before retry
```

### Fraud Patterns to Watch

```
🚨 Verification pumping / SMS toll fraud:
   - Attacker triggers thousands of verifications to premium numbers
   - Each SMS delivery generates revenue for the attacker
   - Pattern: Burst of verifications to international numbers

🚨 Enumeration attacks:
   - Attacker verifies which phone numbers are registered
   - Pattern: Sequential number verifications, all different numbers

🚨 Brute force:
   - Attacker tries all 6-digit codes (1,000,000 combinations)
   - Mitigated by: max 5 attempts per verification
```

> **💡 NOC Tip:** tch for sudden spikes in Verify API calls, especially to international destinations. **SMS pumping fraud** can cost customers thousands of dollars in minutes. If you see a burst of verifications to unusual country codes (e.g., +882, +888 satellite numbers), alert the customer immediately and suggest geo-restrictions.

---

## Monitoring Verification Success Rates

### Key Metrics

```
Verification Success Rate = Verified / Initiated × 100%

Healthy:   > 70% success rate
Warning:   50-70% (investigate delivery issues)
Critical:  < 50% (significant delivery or UX problem)
```

### Breakdown by Stage

```
Initiated:    100%  (all verification requests)
Delivered:     92%  (SMS/voice reached the device)  
Submitted:     78%  (user entered a code)
Verified:      75%  (correct code entered)

Drop-off analysis:
  8% failed delivery  → Check carrier routes
  14% never submitted → UX issue (user didn't receive or gave up)
  3% wrong code       → Normal human error
```

```bash
# Pull Verify metrics
curl "https://api.telnyx.com/v2/verifications?filter[status]=expired&filter[created_at][gte]=2026-02-22" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

> **💡 NOC Tip:**  expired verification (code never submitted) doesn't necessarily mean delivery failure — the user might have abandoned the login flow. Compare delivery webhooks with verification outcomes to separate delivery issues from UX issues.
slug: "two-factor-auth"
---

## Real-World NOC Scenario

**Scenario:** Customer reports verification codes are arriving 2-3 minutes late, causing users to get "code expired" errors.

**Investigation:**

1. Check the verification timeout — is it too short (e.g., 60 seconds)?
2. Check SMS delivery latency for the affected carrier routes
3. Pull DLR timestamps: `message.sent` vs `message.delivered` — what's the delta?
4. If latency is carrier-specific, check SMPP bind health for that route
5. If global, check Telnyx platform queuing metrics

```bash
# Check message delivery timing
curl "https://api.telnyx.com/v2/messages?filter[messaging_profile_id]=vp_abc123&filter[direction]=outbound" \
  -H "Authorization: Bearer YOUR_API_KEY"
# Compare sent_at vs delivered_at timestamps
```

**Resolution options:**
- Increase verification timeout (300s recommended)
- Add voice fallback for time-critical verifications
- Escalate carrier latency to routing team

---

## Key Takeaways

1. **Verify API manages the full OTP lifecycle** — generation, delivery, validation, and expiry
2. **SMS is primary, voice is fallback** — configure both for maximum reach
3. **Rate limiting is built in** — 5 attempts per number per 10 minutes prevents brute force
4. **SMS pumping fraud** is the #1 threat — monitor for bursts to international numbers
5. **Healthy success rate is >70%** — below 50% indicates delivery or UX problems
6. **Expired ≠ undelivered** — distinguish delivery failures from user abandonment
7. **Timeout should be 300 seconds** — shorter timeouts cause false failures on slow carrier routes
slug: "two-factor-auth"
---

**Next: Lesson 188 — Fax API: Programmable Fax**
