# Lesson 60: Fax API — Programmable Fax

**Module 1 | Section 1.18 — Identity**
**⏱ ~5min read | Prerequisites: Lesson 57 (T.38 Fax over IP)**

---

## Introduction

Fax refuses to die. Healthcare (HIPAA), legal, government, and finance industries still rely heavily on fax. Lesson 57 covered T.38 fax relay at the protocol level. This lesson covers the **Telnyx Fax API** — a programmable layer that abstracts T.38 complexity into simple REST calls with webhook-based status updates. As a NOC engineer, you'll troubleshoot fax failures that span both API-level and protocol-level issues.

---

## Telnyx Fax API vs Raw T.38

```
                    Raw T.38              Telnyx Fax API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Setup:              SIP + T.38 config     REST API call
Document format:    TIFF (Group 3/4)      PDF, TIFF, PNG, DOC
Error correction:   ECM in T.38           Handled by platform
Receiving:          SIP endpoint needed   Webhook notification
Status:             SIP BYE/error codes   Webhook events
Resolution:         Negotiate per call    API parameter
Retry:              Manual                Configurable auto-retry
```

---

## Sending a Fax

### API Call

```bash
curl -X POST https://api.telnyx.com/v2/faxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "connection_id": "conn_abc123",
    "from": "+15551234567",
    "to": "+15559876543",
    "media_url": "https://example.com/documents/invoice.pdf",
    "quality": "high",
    "store_media": true,
    "monochrome": true,
    "t38_enabled": true,
    "webhook_url": "https://example.com/webhooks/fax"
  }'
```

### Response

```json
{
  "data": {
    "id": "fax_def456",
    "status": "queued",
    "direction": "outbound",
    "from": "+15551234567",
    "to": "+15559876543",
    "quality": "high",
    "page_count": null,
    "created_at": "2026-02-23T10:00:00Z"
  }
}
```

### Internal Processing

```
API request received
  → Fetch document from media_url
  → Convert to TIFF (G3/G4 compression)
  → Establish SIP call to destination
  → Negotiate T.38 (or fall back to G.711 passthrough)
  → Transmit pages via T.38 UDPTL
  → Confirm page delivery (ECM)
  → Hang up and send webhook with results
```

🔧 **NOC Tip:** The most common fax send failure is a bad `media_url` — the document URL must be publicly accessible. If a customer says "fax queued but never sent," check if Telnyx can reach their media URL. Firewalled URLs are the #1 cause.

---

## Receiving a Fax

### Configuration

Assign a Telnyx number to receive faxes:

```bash
curl -X PATCH https://api.telnyx.com/v2/phone_numbers/+15551234567 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "connection_id": "conn_fax_inbound",
    "fax": {
      "enabled": true,
      "media_type": "application/pdf",
      "webhook_url": "https://example.com/webhooks/fax-receive"
    }
  }'
```

### Inbound Fax Webhook

```json
{
  "data": {
    "event_type": "fax.received",
    "payload": {
      "fax_id": "fax_inbound_789",
      "direction": "inbound",
      "from": "+15559876543",
      "to": "+15551234567",
      "status": "received",
      "page_count": 3,
      "media_url": "https://media.telnyx.com/faxes/fax_inbound_789/document.pdf",
      "quality": "normal",
      "received_at": "2026-02-23T10:05:30Z"
    }
  }
}
```

🔧 **NOC Tip:** Received fax media URLs expire after **7 days**. If a customer reports missing fax documents, check the receive timestamp. They should download and store faxes immediately upon webhook receipt.

---

## Quality Settings

```
Quality    Resolution      Speed          Use Case
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
normal     204×98 DPI      Fast           Text documents
fine       204×196 DPI     Medium         Detailed text
high       204×392 DPI     Slow           Images, fine print
```

Higher quality = slower transmission = higher chance of timeout/failure on poor connections.

🔧 **NOC Tip:** If a customer reports fax timeouts, try reducing quality from "high" to "normal." High-resolution faxes take 3-4x longer to transmit, and many legacy fax machines timeout at 60 seconds per page.

---

## Webhook Events

The Fax API sends events through the fax lifecycle:

```
fax.queued       → Fax accepted, waiting to dial
fax.media.processed → Document converted, ready to send
fax.sending      → Call connected, pages transmitting
fax.delivered    → All pages sent successfully
fax.received     → Inbound fax received
fax.failed       → Fax transmission failed
```

### Failure Event Detail

```json
{
  "data": {
    "event_type": "fax.failed",
    "payload": {
      "fax_id": "fax_def456",
      "status": "failed",
      "failure_reason": "remote_did_not_answer",
      "sip_response_code": 480,
      "page_count": 0,
      "attempted_at": "2026-02-23T10:01:15Z"
    }
  }
}
```

### Common Failure Reasons

| Reason | Description | NOC Action |
|--------|-------------|------------|
| `remote_did_not_answer` | No answer after 60s | Verify destination number; may be a voice line |
| `remote_busy` | Destination busy | Retry later; may be receiving another fax |
| `t38_negotiation_failed` | T.38 handshake failed | Try with `t38_enabled: false` (G.711 fallback) |
| `fax_protocol_error` | Page transmission error | Check for line quality issues |
| `media_download_failed` | Can't fetch document URL | Customer's media URL unreachable |
| `invalid_media` | Document can't be converted | Bad file format or corrupted document |
| `timeout` | Transmission exceeded time limit | Reduce quality or page count |

🔧 **NOC Tip:** `t38_negotiation_failed` is common when the remote fax machine or its carrier doesn't support T.38. Setting `t38_enabled: false` forces G.711 passthrough mode, which is slower but more compatible. This is your go-to fix for "works to some numbers but not others."

---

## Monitoring Fax Success Rates

### Key Metrics

```
Fax Success Rate = Delivered / Attempted × 100%

Healthy:   > 85% (fax is inherently less reliable than voice/SMS)
Warning:   70-85%
Critical:  < 70%

Industry average: ~80-90% for well-configured systems
```

### Common Causes of Low Success Rates

```
1. T.38 incompatibility    → 30% of failures
   Fix: Enable G.711 fallback

2. Remote busy             → 20% of failures
   Fix: Auto-retry with backoff

3. No answer               → 15% of failures
   Fix: Verify fax number (might be voice-only)

4. Line quality            → 15% of failures
   Fix: Reduce quality setting

5. Media/document issues   → 10% of failures
   Fix: Validate documents before sending

6. Timeout                 → 10% of failures
   Fix: Split large documents, reduce quality
```

---

## Auto-Retry Configuration

```bash
curl -X POST https://api.telnyx.com/v2/faxes \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "from": "+15551234567",
    "to": "+15559876543",
    "media_url": "https://example.com/doc.pdf",
    "max_retries": 3,
    "retry_delay_secs": 120,
    "retry_on": ["remote_busy", "remote_did_not_answer", "t38_negotiation_failed"]
  }'
```

---

## Real-World NOC Scenario

**Scenario:** Healthcare customer reports 40% fax failure rate to a specific hospital fax number.

**Investigation:**

1. Pull fax logs for the destination number:
   ```bash
   curl "https://api.telnyx.com/v2/faxes?filter[to]=+15559876543&filter[status]=failed"
   ```
2. Check failure reasons — mostly `t38_negotiation_failed`
3. The hospital likely uses a legacy fax machine behind an analog gateway that doesn't support T.38
4. Test with `t38_enabled: false` — forces G.711 passthrough
5. Success rate jumps to 90%

**Resolution:** Configure the customer's fax profile to disable T.38 for that destination, or set up a routing rule that uses G.711 for known-incompatible destinations.

---

## Key Takeaways

1. **Fax API abstracts T.38 into REST calls** — send with a URL, receive via webhook
2. **Media URL must be publicly accessible** — #1 cause of "fax never sent" issues
3. **T.38 negotiation failures** are the most common protocol error — G.711 fallback is the fix
4. **Quality vs reliability trade-off** — higher resolution = slower = more timeouts
5. **Fax success rates of 85%+ are healthy** — fax is inherently less reliable than digital messaging
6. **Auto-retry with backoff** handles transient failures (busy, no answer)
7. **Media URLs expire** — 7 days for received faxes; customers must download promptly

---

**Next: Lesson 189 — TeXML: XML-Based Call Control**
