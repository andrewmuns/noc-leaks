# Lesson 67: Telnyx Messaging API — SMS, MMS, and Number Management

**Module 1 | Section 1.17 — Messaging**
**⏱ ~7min read | Prerequisites: Lesson 181 (SMS/MMS Fundamentals)**

---

## Introduction

Now that you understand carrier messaging protocols, let's look at how Telnyx exposes messaging capabilities through its API. The Telnyx Messaging API abstracts SMPP complexity into RESTful calls with webhook-based delivery notifications. As a NOC engineer, you'll troubleshoot API-level issues, webhook failures, and delivery problems daily.

---

## Messaging Profiles

Every Telnyx messaging configuration starts with a **Messaging Profile** — a container that groups settings, numbers, and webhook URLs.

```json
{
  "id": "4001170c-2b3f-4e5a-9b1d-xxxxxxxxxxxx",
  "name": "Production Alerts",
  "enabled": true,
  "webhook_url": "https://customer.example.com/webhooks/sms",
  "webhook_failover_url": "https://backup.example.com/webhooks/sms",
  "webhook_api_version": "2",
  "number_pool_settings": {
    "sticky_sender": true,
    "geomatch": true
  },
  "v1_secret": null,
  "whitelisted_destinations": ["US", "CA", "GB"]
}
```

Key settings:
- **webhook_url** — Where Telnyx POSTs delivery status and inbound messages
- **webhook_failover_url** — Backup if primary webhook fails (3 retries, then failover)
- **sticky_sender** — Same from-number for conversations with same recipient
- **geomatch** — Prefer sending from a number with matching area code
- **whitelisted_destinations** — Country restrictions to prevent fraud

🔧 **NOC Tip:** When a customer says "I'm not receiving webhooks," first verify the webhook URL returns HTTP 200 within 10 seconds. Telnyx retries up to 3 times with exponential backoff (1s, 5s, 25s), then hits the failover URL. Check the Messaging Logs in Mission Control for webhook response codes.

---

## Outbound SMS Flow

### Sending a Message

```bash
curl -X POST https://api.telnyx.com/v2/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "+15551234567",
    "to": "+15559876543",
    "text": "Your verification code is 847293",
    "messaging_profile_id": "4001170c-2b3f-4e5a-9b1d-xxxxxxxxxxxx",
    "webhook_url": "https://example.com/dlr",
    "webhook_failover_url": "https://backup.example.com/dlr"
  }'
```

### Response

```json
{
  "data": {
    "id": "msg_abc123def456",
    "record_type": "message",
    "direction": "outbound",
    "type": "SMS",
    "from": { "phone_number": "+15551234567", "carrier": "Telnyx" },
    "to": [{ "phone_number": "+15559876543", "status": "queued" }],
    "parts": 1,
    "encoding": "GSM-7",
    "cost": { "amount": "0.0040", "currency": "USD" },
    "messaging_profile_id": "4001170c-2b3f-4e5a-9b1d-xxxxxxxxxxxx"
  }
}
```

### Internal Processing Pipeline

```
API Request received
  → Validate API key + permissions
  → Check messaging profile settings
  → Validate 'from' number belongs to account
  → Check destination country whitelist
  → Number lookup (carrier, type)
  → Route selection (direct carrier vs aggregator)
  → SMPP submit_sm to carrier
  → Return message_id to caller
  → Async: DLR webhook when carrier responds
```

🔧 **NOC Tip:** The `parts` field in the response tells you how many SMS segments the message was split into. If a customer is confused about billing, check this — a 161-character GSM-7 message is 2 parts (2x the cost).

---

## Inbound SMS Flow

When someone sends a message to a Telnyx number:

```
Carrier SMSC → SMPP deliver_sm → Telnyx Platform
  → Match destination number to messaging profile
  → POST webhook to customer's URL
```

### Inbound Webhook Payload

```json
{
  "data": {
    "event_type": "message.received",
    "id": "evt_xyz789",
    "payload": {
      "id": "msg_inbound_001",
      "direction": "inbound",
      "type": "SMS",
      "from": { "phone_number": "+15559876543" },
      "to": [{ "phone_number": "+15551234567" }],
      "text": "Yes, confirm my appointment",
      "received_at": "2026-02-23T10:34:12.000Z",
      "messaging_profile_id": "4001170c-2b3f-4e5a-9b1d-xxxxxxxxxxxx"
    }
  }
}
```

🔧 **NOC Tip:** If inbound messages aren't reaching the customer, check: (1) Is the number assigned to a messaging profile? (2) Is the messaging profile enabled? (3) Is the webhook URL responding? Use `GET /v2/phone_numbers/{id}` to verify the number's messaging profile assignment.

---

## MMS — Media Handling

### Sending MMS

```bash
curl -X POST https://api.telnyx.com/v2/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "+15551234567",
    "to": "+15559876543",
    "text": "Check out this image!",
    "media_urls": [
      "https://example.com/images/photo.jpg"
    ],
    "messaging_profile_id": "4001170c-2b3f-4e5a-9b1d-xxxxxxxxxxxx"
  }'
```

### MMS Constraints

```
Max media size:    1 MB per attachment (carrier limit)
Supported types:   image/jpeg, image/png, image/gif, 
                   video/mp4, audio/mp3, text/vcard
Max attachments:   10 per message
Media URL:         Must be publicly accessible (Telnyx fetches it)
```

### Inbound MMS Media

When receiving MMS, Telnyx hosts the media temporarily:

```json
{
  "media": [
    {
      "url": "https://media.telnyx.com/msg_abc123/image.jpg",
      "content_type": "image/jpeg",
      "size": 245830
    }
  ]
}
```

🔧 **NOC Tip:** MMS media URLs from Telnyx expire after **72 hours**. If a customer says they can't access received media, check the timestamp. They need to download and store media promptly. This is a common support question.

---

## Alphanumeric Sender ID

For markets that support it (UK, EU, Australia — **not** US/Canada), you can send from a text string instead of a phone number:

```json
{
  "from": "MyBrand",
  "to": "+447700900123",
  "text": "Your order has shipped!",
  "messaging_profile_id": "..."
}
```

Constraints:
- Max 11 characters
- Alphanumeric only (letters, digits, spaces)
- **One-way only** — recipients cannot reply
- Must be pre-registered in some countries (e.g., India, Saudi Arabia)
- Not supported in US, Canada, or China

---

## Toll-Free Messaging

US toll-free numbers (8XX) are an important messaging channel:

- **No 10DLC registration required** (toll-free has its own verification)
- **Higher throughput** than standard long codes (~10 MPS after verification)
- **Toll-free verification** required by carriers since 2023
- Verification reviews business identity and use case

```
Toll-free verification statuses:
  PENDING     — Submitted, awaiting carrier review
  VERIFIED    — Approved, full throughput enabled
  REJECTED    — Failed verification (resubmit with corrections)
  UNVERIFIED  — Not yet submitted (limited to ~0.25 MPS)
```

🔧 **NOC Tip:** Unverified toll-free numbers are severely rate-limited and may have messages filtered. If a customer reports slow delivery from an 8XX number, check verification status in Mission Control → Messaging → Toll-Free Verification.

---

## Delivery Status Webhooks

Telnyx sends status updates as messages progress through the delivery pipeline:

```
message.queued      → Accepted by Telnyx, queued for delivery
message.sent        → Submitted to carrier via SMPP
message.delivered   → Carrier confirmed delivery to handset
message.failed      → Permanent failure
message.sending_failed → Failed before reaching carrier
```

### Webhook Payload for Delivery Status

```json
{
  "data": {
    "event_type": "message.delivered",
    "payload": {
      "id": "msg_abc123def456",
      "to": [{ 
        "phone_number": "+15559876543",
        "status": "delivered"
      }],
      "completed_at": "2026-02-23T10:34:15.123Z"
    }
  }
}
```

---

## Common Error Codes

| Code | Meaning | NOC Action |
|------|---------|------------|
| 40001 | Invalid 'from' number | Number not on account or not messaging-enabled |
| 40002 | Invalid 'to' number | Failed number validation |
| 40003 | Messaging profile disabled | Re-enable in Mission Control |
| 40008 | Country not whitelisted | Add country to profile's whitelist |
| 40300 | Rate limit exceeded | Customer hitting API rate limits |
| 50001 | Carrier rejected | Check carrier error detail |
| 50002 | Carrier timeout | Carrier SMPP issue — check route health |
| 50003 | Undeliverable | Invalid/unreachable number |

🔧 **NOC Tip:** Error 50002 (carrier timeout) often indicates an upstream carrier issue. Check the Telnyx status page and SMPP bind health for that carrier's route. If multiple customers see 50002 to the same carrier, escalate to the carrier team.

---

## Number Management for Messaging

### Assigning Numbers to Messaging Profiles

```bash
# List numbers on account
curl https://api.telnyx.com/v2/phone_numbers?filter[status]=active

# Update number to use messaging profile
curl -X PATCH https://api.telnyx.com/v2/phone_numbers/+15551234567 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "messaging_profile_id": "4001170c-2b3f-4e5a-9b1d-xxxxxxxxxxxx"
  }'
```

### Number Pool Settings

When a messaging profile has multiple numbers, the **number pool** handles selection:

- **Sticky sender** — Maintains same from-number per conversation
- **Geomatch** — Selects number with matching area code to recipient
- **Round-robin** — Distributes across numbers to avoid per-number rate limits

---

## Real-World NOC Scenario

**Scenario:** Customer reports "Messages show as 'sent' but recipients aren't receiving them."

**Investigation:**

1. Check webhook logs — are DLRs coming back as `delivered` or `sent` (no final DLR)?
2. If stuck at `sent`: carrier accepted but no DLR returned — this may be normal for some international routes
3. If `delivered` but not received: possible handset-level spam filter (Google Messages, iOS)
4. Check if messages are going to landlines (can't receive SMS without special handling)
5. Verify the 'from' number isn't flagged for spam by carriers

```bash
# Check message detail
curl https://api.telnyx.com/v2/messages/msg_abc123def456
```

---

## Key Takeaways

1. **Messaging profiles** are the central configuration unit — they bind numbers, webhooks, and routing rules together
2. **Outbound flow**: API call → validation → route selection → SMPP submit → async DLR webhook
3. **Inbound flow**: Carrier SMPP deliver → number-to-profile match → webhook POST to customer
4. **MMS media URLs expire in 72 hours** — customers must download promptly
5. **Toll-free messaging requires verification** — unverified numbers get throttled heavily
6. **Webhook reliability matters** — always configure a failover URL; monitor for non-200 responses
7. **Error codes 40xxx are client errors, 50xxx are carrier/network errors** — know the difference for triage

---

**Next: Lesson 183 — 10DLC Registration and Compliance**
