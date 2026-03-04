# Lesson 132: Message Delivery Failures — Systematic Troubleshooting

**Module 4 | Section 4.3 — Messaging Debug**
**⏱ ~8 min read | Prerequisites: Lessons 68-70**

---

SMS and MMS delivery failures are fundamentally different from voice call failures. Where voice signaling happens in real-time with immediate feedback (SIP response codes), messages are asynchronous, batched, and queued. A message might be accepted now, sent in 5 seconds, and fail 30 seconds later with a carrier error. Understanding the message lifecycle and tracking its path through the pipeline is essential for effective troubleshooting.

## The Message Lifecycle

Every message flows through distinct stages:

```
1. RECEIVED
   ↓
2. QUEUED (in Telnyx queue)
   ↓
3. SUBMITTED (to carrier)
   ↓
4. DELIVERED / FAILED / UNDELIVERED (carrier acknowledgment)
```

Each state transition is logged. Understanding where a message got stuck tells you what to investigate.

### State Definitions

| State | Meaning | Investigation Focus |
|-------|---------|---------------------|
| **RECEIVED** | Message accepted into Telnyx | Check validation, queue insertion |
| **QUEUED** | Waiting in queue for sending | Check queue depth, rate limiting |
| **SUBMITTED** | Sent to carrier, awaiting response | Check carrier connectivity |
| **DELIVERED** | Carrier acknowledged delivery | Success |
| **FAILED** | Carrier rejected | Check error code, content, number validity |
| **UNDELIVERABLE** | Carrier couldn't deliver | Check number status, routing |

## Finding Messages in Graylog

Graylog is the primary tool for message debugging:

```
# By message ID (MDR ID)
type:SMS AND message_id:msg-abc123-def456

# By phone number
type:SMS AND (from:+15551234567 OR to:+15559876543)

# By timestamp and status
type:SMS AND status:FAILED AND timestamp:["2026-02-22 14:00" TO "2026-02-22 14:10"]

# By customer
type:SMS AND customer_id:cust-abc123 AND status:FAILED

# By carrier
type:SMS AND carrier:CarrierX AND status:FAILED
```

**Message Detail Record (MDR) view:**
```json
{
  "message_id": "msg-abc123-def456",
  "from": "+15551234567",
  "to": "+15559876543",
  "body": "Hello world",
  "status": "FAILED",
  "error_code": 30003,
  "error_message": "Unreachable destination number",
  "carrier": "CarrierX",
  "submitted_at": "2026-02-22T14:05:23Z",
  "failed_at": "2026-02-22T14:05:35Z",
  "latency_ms": 12000
}
```

🔧 **NOC Tip:** The MDR is your single source of truth. It contains all state transitions and error information. When a customer asks "what happened to message X," the MDR gives you the authoritative answer. Bookmark the MDR query in Graylog or build a simple dashboard for message lookup by ID or number.

## Systematic Debugging Flow

### Step 1: Find the Message

Locate the specific message in question:

```
type:SMS AND message_id:msg-abc123-def456
```

If you don't have the message ID:
```
type:SMS AND from:+15551234567 AND timestamp:["2026-02-22 14:00" TO now]
```

### Step 2: Check Current State

What state is the message in?

**RECEIVED but never QUEUED:**
- Message validation failed
- Customer quota exceeded
- Content blocked (spam filter)

**QUEUED but never SUBMITTED:**
- Queue backlog (high volume)
- Rate limiting (customer exceeded rate)
- There was a delay but later submitted

**SUBMITTED but no final state:**
- Carrier hasn't responded yet (check carrier latency)
- Carrier DLACK never received
- DLACK lost in transit

**FAILED or UNDELIVERABLE:**
- Carrier rejected (check error code)
- Number invalid or unreachable
- Content filtered by carrier

### Step 3: Read Error Codes

Common Telnyx SMS error codes:

| Code | Meaning | Common Causes |
|------|---------|---------------|
| **30001** | Queue overflow | Too many messages, system capacity |
| **30002** | Account suspended | Billing, TOS violation |
| **30003** | Unreachable | Invalid number, landline, unreachable |
| **30004** | Message blocked | Carrier filtering, spam detected |
| **30005** | Unknown destination | Number doesn't exist |
| **30006** | Landline | Can't deliver SMS to landline |
| **30007** | Carrier violation | Content filtered by carrier |
| **30008** | Unknown error | Generic catch-all |

**Carrier-specific errors** (varies by carrier):
- 102: Network congestion
- 103: Destination not reachable
- 202: Message expired
- 460-499: Various routing errors

### Step 4: Check for Patterns

Is this affecting one message or many?

```
# Same destination number in last hour
type:SMS AND to:+15559876543 AND timestamp:[now-1h TO now]

# Same customer, same error code
type:SMS AND customer_id:cust-abc123 AND error_code:30004
                      AND timestamp:[now-1h TO now]

# Same carrier, same time window
type:SMS AND carrier:CarrierX AND status:FAILED
                      AND timestamp:["2026-02-22 14:00" TO "2026-02-22 14:30"]
```

**Pattern analysis:**
- 1 message → likely number-specific or content-specific
- Many messages to same number → recipient issue (full mailbox, blocked)
- Many messages same customer → customer account or configuration issue
- Many messages same carrier → carrier outage or filtering
- All messages many customers → widespread issue

🔧 **NOC Tip:** For high-volume SMS issues, group by carrier and error code. A query like `type:SMS AND status:FAILED | stats count by carrier, error_code` immediately shows if one carrier is driving failures. If 90% of failures are to CarrierX with error 102 (congestion), that's a carrier issue requiring escalation to them, not a Telnyx issue.

## Common Failure Scenarios

### Scenario 1: Spam/Carrier Filtering

**Symptom:** Messages show DELIVERED in Telnyx but customer says recipients never received them.

**Investigation:**
1. Check carrier DLACK (delivery acknowledgment):
   - Some carriers accept messages (200 OK submit) but filter silently
   - No DLACK or DLACK says "delivered" but user never gets it
   - This is "message accepted but eaten by carrier"

2. Check message content:
   - URLs in message?
   - Keywords triggering filters (certain business categories)
   - High volume to same recipients?

3. Check 10DLC registration:
   - Is sender properly registered?
   - Trust score affects deliverability
   - Unregistered high-volume traffic gets filtered

🔧 **NOC Tip:** "Delivered" in Telnyx means "carrier acknowledged delivery." It does NOT mean "human received it." Carriers can and do drop messages after acknowledging. If customers complain about missing "delivered" messages, check: Is this affecting one carrier specifically? Does the pattern correlate with message content (URLs, certain keywords)? This is a filtering issue, not a delivery issue.

### Scenario 2: Invalid or Inactive Numbers

**Symptom:** High rate of 30003 (unreachable) or 30005 (unknown)

**Investigation:**
```
type:SMS AND (error_code:30003 OR error_code:30005)
| stats count by to
```

Are these real numbers?
- Use Number Lookup API (Lesson 75) to verify
- Check if recently ported (might have stale routing)
- Check if recently deactivated (number recycling)

**Customer education:**
- Not all numbers can receive SMS (some landlines, some VoIP)
- Ported numbers may have routing delays (hours to days)

### Scenario 3: Rate Limiting

**Symptom:** Messages queued but submission delayed. Error 30001.

**Investigation:**
1. Check customer's configured rate limit:
   - What's their messages-per-second cap?
   - Are they bursting above it?

2. Check queue depth:
   ```promql
   sms_queue_depth{customer_id="cust-abc123"}
   ```
   - Growing queue = throttling in effect

3. Check if rate limit is shared or per-number

**Resolution:**
- Increase customer rate limit (if appropriate)
- Implement client-side pacing
- Use burst capacity (if available)

### Scenario 4: 10DLC Compliance Failures

**Symptom:** Messages blocked with error code indicating "campaign not approved" or "content not registered."

**Investigation:**
1. Check customer's 10DLC status:
   - Brand registered?
   - Campaign registered?
   - Numbers assigned to campaign?

2. Check trust score:
   - Low trust score = stricter filtering
   - High trust score = better deliverability

**Common compliance issues:**
- Missing Opt-in documentation
- Campaign purpose doesn't match traffic
- Unregistered brand
- Using shared short code for A2P traffic

## Delivery Receipt (DLR) Tracking

For messages to show as DELIVERED, we need carrier DLRs:

```
Message lifecycle with DLR:
SUBMITTED → Carrier
WAITING (for DLR)
DELIVERED (DLR received from carrier)
```

DLR timeout varies:
- Domestic carriers: typically 10-30 seconds
- International: up to 5-10 minutes
- Some carriers: unreliable or missing DLRs

If DLR never arrives:
- Message status stays SUBMITTED or times out to UNKNOWN
- Check carrier DLR reliability stats
- Some carriers always provide DLR, others don't

**What "submitted" actually means:**
- Message reached carrier
- Carrier accepted responsibility
- Delivery may or may not happen
- DLR (if supported) confirms actual delivery

🔧 **NOC Tip:** When customers ask "why isn't my message showing delivered," check the DLR timeline. If it's been <30 seconds, it might still be in flight. If it's been >5 minutes and still SUBMITTED, the DLR was lost or carrier doesn't reliably provide them — this is expected for certain international routes. Set expectations accordingly.

## Real-World Troubleshooting Scenario

**Customer report:** "30% of our messages aren't being delivered."

**Investigation:**

1. Pull MDRs for last 4 hours:
```
type:SMS AND customer_id:CUST-BIGCORP AND timestamp:[now-4h TO now]
| stats count by status
```

Result:
- DELIVERED: 7,000
- FAILED: 3,000

2. Group failures by error code:
| stats count by error_code
- 30004 (Message blocked): 2,500
- 30003 (Unreachable): 400
- Others: 100

3. 30004 is 83% of failures → Content filtering

4. Check 30004 messages:
```
type:SMS AND error_code:30004 | stats count by to
```

5. All 30004s are to Verizon recipients → Verizon-specific filtering

6. Check message content of blocked messages:
- Contains shortened URLs (bit.ly)
- Contains certain keywords (financial offers)
- High volume over short period

7. Check 10DLC status:
- Customer has brand registered
- Campaign registered as "marketing"
- But trust score is low
- Verizon is filtering aggressively due to low trust + marketing content

**Root cause:** Verizon filtering due to low 10DLC trust score + marketing content patterns

**Resolution:** Educate customer on 10DLC trust score improvement (reduce opt-out rate, maintain low complaint rate)

---

**Key Takeaways:**

1. Messages have a lifecycle: RECEIVED → QUEUED → SUBMITTED → DELIVERED/FAILED
2. Finding the current state identifies investigation focus — SUBMITTED but no DLR means waiting on carrier
3. Error codes tell the story: 30003=invalid number, 30004=filtered, 30001=rate limited
4. Always check for patterns — single message vs many, specific customer vs all, specific carrier vs all
5. "Delivered" means carrier acknowledged — carriers can still filter silently
6. 10DLC compliance affects deliverability — low trust score = more filtering
7. DLR timeouts vary — domestic is seconds, international can be minutes, some carriers never provide DLR

**Next: Lesson 117 — Carrier Filtering and Compliance Issues**
