# Lesson 80: Message Delivery Troubleshooting

**Module 2 | Section 2.6 — Messaging**
**⏱ ~7 min read | Prerequisites: Lesson 68, 69**

---

## The Messaging Debugging Mindset

Message delivery troubleshooting is different from voice troubleshooting. Voice calls fail immediately and obviously — the call doesn't connect, you hear silence, audio is choppy. Messages fail silently. The sender hits "send," gets a 202, and may never know the message didn't arrive unless they check for a DLR or the recipient tells them.

This means message debugging is often delayed — hours or days after the failure — and requires systematic log investigation.

## Error Code Categories

Telnyx messaging error codes map to specific failure points:

### Telnyx-Level Errors (Before Upstream Delivery)

| Code | Meaning | Common Cause |
|------|---------|-------------|
| 10001 | Invalid number | Destination isn't a valid E.164 number |
| 10002 | Number not in service | Number has been disconnected |
| 10003 | Forbidden | Account suspended, number not authorized |
| 10004 | Rate limited | Exceeded per-number or per-account rate limit |
| 10005 | Insufficient funds | Prepaid account out of balance |

These failures are caught before the message leaves Telnyx. They return quickly and have clear resolutions.

### Carrier-Level Errors (Upstream Rejection)

| Code | Meaning | Common Cause |
|------|---------|-------------|
| 30003 | Unreachable destination | Number is temporarily unreachable (phone off, roaming) |
| 30004 | Message blocked | Carrier filtered the message (content or compliance) |
| 30005 | Unknown number | Number doesn't exist in carrier's database |
| 30006 | Landline | Sent SMS to a landline that doesn't support SMS |
| 30007 | Carrier violation | 10DLC compliance issue (Lesson 69) |
| 30008 | Unknown error | Generic carrier rejection — requires investigation |

Carrier errors are harder to debug because carrier error messages are often vague.

🔧 **NOC Tip:** Error 30008 (unknown) is the most frustrating — it means the carrier rejected the message without a specific reason. Check: (1) message content for spam-trigger keywords, (2) sending volume patterns (sudden spikes trigger filtering), (3) whether other customers are experiencing similar rejections to the same carrier.

## Carrier Filtering: The Black Box

Carriers run content filtering on all messages. These filters are proprietary and not documented. They look for:

**Content patterns:**
- Known spam phrases ("Act now!", "Free gift", "You've won")
- URL shorteners (bit.ly, tinyurl.com) — heavily penalized
- Phone numbers in messages (recruiting for alternative numbers)
- Excessive capitalization or special characters

**Behavioral patterns:**
- Same message sent to many different numbers (bulk blast)
- High volume from a single number in a short period
- Messages sent outside normal business hours (late night volumes)
- High opt-out rate (many recipients texting STOP)

**Reputation signals:**
- Spam reports from recipients
- Previous violations from the same number or brand
- Numbers flagged by third-party spam databases

🔧 **NOC Tip:** When messages are being filtered, ask the customer for their exact message content. Compare with recent changes — did they add a URL shortener? Did they change the message template? Often a small content change triggers filtering. Try sending a simple "Test message" from the same number — if that goes through, it's content-based filtering, not number/campaign blocking.

## Number Deactivation and Recycling

Phone numbers are recycled. A number that belonged to one person may be reassigned to another after a period of deactivation. This causes:

1. **Messages to wrong person**: customer's database has a number that now belongs to someone else
2. **Spam reports**: the new owner reports messages they didn't sign up for
3. **Opt-out issues**: the new owner opts out, blocking legitimate messages if the old owner contacts the business

Number Lookup (Lesson 75) can help detect deactivated or reassigned numbers before sending.

## Debugging with Message Detail Records (MDRs)

MDRs are the messaging equivalent of CDRs (Call Detail Records). Each message generates an MDR containing:

- **Message ID**: unique identifier
- **From/To numbers**: sender and recipient
- **Direction**: outbound or inbound
- **Status**: sent, delivered, undelivered, failed
- **Error code**: if failed, the specific error
- **Carrier**: which carrier was used for delivery
- **Timestamps**: API received, sent to carrier, DLR received
- **Cost**: per-message billing

The Telnyx portal and API provide MDR access. For NOC investigation, MDRs are the starting point.

## Graylog Investigation Workflow

For deeper investigation beyond MDRs:

```
1. Start with the message ID or phone number
   Graylog: message_id:"<id>" OR from_number:"+15551234567"

2. Trace the message through the pipeline
   - API ingestion log: was the message accepted?
   - Routing log: which carrier was selected?
   - SMPP delivery log: what was the carrier response?
   - DLR log: did a delivery receipt arrive?

3. Check for patterns
   - Same error for multiple messages to same carrier?
   - Same error for all messages from same number?
   - Error started at a specific time? (carrier change, deployment)
```

## MMS-Specific Issues

MMS debugging has additional dimensions:

**Media fetch failure**: Telnyx needs to fetch the media from the provided URL. If the URL is inaccessible, returns an error, or is too slow, MMS fails.

**File size exceeded**: Carriers impose MMS file size limits (typically 1-3MB). A 5MB image will be rejected.

**Unsupported format**: Not all carriers support all media types. JPEG and PNG are safest. HEIC (iPhone default) may not be supported by all carriers.

**Transcoding**: Telnyx may transcode images to meet carrier requirements. If the original is a 10MB PNG, it needs to be compressed before delivery.

🔧 **NOC Tip:** For MMS failures, check the media URL first — `curl -I <url>` to verify it's accessible, check Content-Type and Content-Length headers. Many MMS failures are simply "media URL returned 404 or 403."

## Throughput Issues

"Messages are slow" is different from "messages are failing." Slow delivery usually means:

1. **Queue buildup**: sending faster than the rate limit allows → messages queue internally
2. **Carrier throttling**: carrier is accepting messages slowly → upstream queue
3. **SMSC congestion**: carrier's message center is overloaded (rare, usually during high-traffic events like New Year's)

Check the internal queue depth in Grafana. If messages are queuing on Telnyx's side, it's a rate limit or upstream issue. If they're being sent promptly but delivery is slow, it's carrier-side.

## Troubleshooting Scenario: "Half Our Messages Aren't Being Delivered"

A customer reports approximately 50% delivery failure rate. No specific error code — messages just show "undelivered."

**Investigation:**
1. Pull MDRs for the last 24 hours. Filter by status=undelivered
2. Pattern: failures are all to mobile numbers that have been ported to a different carrier
3. The number lookup data is stale — routing to the original carrier, which rejects messages for ported numbers
4. The rejection happens at the old carrier's SMSC with a generic error

**Resolution:** Enabled fresh carrier lookup (dip) before each message send. The updated routing sent messages to the correct carrier. Delivery rate returned to normal.

This demonstrates why LRN/carrier lookups (Lesson 75) matter for messaging, not just voice routing.

---

**Key Takeaways:**
1. Message failures are silent — customers may not know messages failed unless they monitor DLRs
2. Error codes fall into Telnyx-level (quick, clear) and carrier-level (delayed, often vague) categories
3. Carrier content filtering is a black box — avoid spam trigger words, URL shorteners, and bulk-blast patterns
4. MDRs are your starting point; Graylog pipeline tracing for deeper investigation
5. MMS failures often trace to media URL issues: inaccessible, too large, or unsupported format
6. Stale carrier routing data causes delivery failures to ported numbers — fresh lookups are essential

**Next: Lesson 71 — RCS: Rich Communication Services**
