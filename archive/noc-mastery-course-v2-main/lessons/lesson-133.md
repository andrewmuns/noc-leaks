# Lesson 133: Carrier Filtering and Compliance Issues

**Module 4 | Section 4.3 — Messaging Debug**
**⏱ ~6 min read | Prerequisites: Lesson 116**

---

Message delivery failures often trace back to carrier-side filtering — the carrier accepts the message but silently drops it, or actively rejects it with specific error codes. Understanding why carriers filter messages and how to work with (not against) their filtering systems is essential for maintaining deliverability and resolving customer complaints.

## Why Carriers Filter Messages

Carriers filter for three primary reasons:

### 1. Spam Prevention

Carriers have a financial and regulatory obligation to protect their subscribers from unwanted messages. A single spam complaint can cost carriers customer trust and regulatory scrutiny. Their filters are aggressive by design — they'd rather block some legitimate messages than let spam through.

**Spam filter triggers:**
- High-volume unsolicited messages
- Sender not in recipient's contacts
- Content matching known spam patterns
- Links to suspicious or blacklisted domains
- Shortened URLs (obscured destinations)
- Financial offers, "free" claims, urgent language

### 2. Network Protection

Carriers protect their networks from:
- **Traffic floods**: Sudden spikes that could overwhelm SMSC capacity
- **Invalid destination attempts**: Repeated messages to invalid numbers waste resources
- **Protocol violations**: Malformed messages or invalid encoding

### 3. Regulatory Compliance

Carriers must comply with:
- **TCPA (Telephone Consumer Protection Act)**: Prior express consent required
- **CTIA guidelines**: Best practices for A2P messaging
- **10DLC rules**: Campaign registration requirements
- **International regulations**: Varies by country (GDPR, local telecom laws)

## Types of Carrier Filtering

### Content-Based Filtering

The message body triggers the filter:

**Red flags:**
- "FREE", "WINNER", "CONGRATULATIONS"
- "Click here", "Act now", "Limited time"
- Shortened URLs (bit.ly, tinyurl, etc.)
- Excessive capitalization
- Special characters in unusual patterns

**What carriers don't tell you:** Each carrier has proprietary algorithms. What passes Verizon's filter might be blocked by T-Mobile. The rules change frequently without public notice.

🔧 **NOC Tip:** When customers report messages being filtered, check if the issue is carrier-specific. If messages to T-Mobile are blocked but Verizon works, the problem is T-Mobile's content filter. Try having the customer send a simplified message (no links, plain text) to the same recipient. If that works, it confirms content filtering.

### Volume-Based Filtering

Sending too many messages in a short period triggers throttling:

**Symptoms:**
- Initial messages deliver, then delivery rate drops
- Messages queue but don't submit
- Error codes indicating rate limiting

**Carrier thresholds (example, varies by carrier):**
- Local number: 1 message per second
- Short code: 100 messages per second
- Toll-free: 5 messages per second (varies by registration tier)

**What happens:**
- Carrier accepts first N messages at configured rate
- Above threshold, carrier queues or rejects
- Some carriers apply "leaky bucket" — messages above rate are delayed, not rejected
- Others reject outright

### Sender Reputation Filtering

Each sender builds a reputation score based on:

| Factor | Positive Impact | Negative Impact |
|--------|-----------------|-----------------|
| **Opt-out rate** | <1% | >2% |
| **Complaint rate** | <0.1% | >0.5% |
| **Invalid number rate** | <3% | >10% |
| **Consent documentation** | Complete, auditable | Missing or incomplete |

Low reputation → Stricter filtering, lower throughput
High reputation → Better deliverability, higher throughput

## 10DLC Compliance Deep Dive

10DLC (10-Digit Long Code) is the primary A2P messaging channel in the US. It requires registration:

### The Registration Chain

```
Brand (the business)
    ↓ registers with
TCR (The Campaign Registry)
    ↓ assigns
Campaign (the messaging use case)
    ↓ links to
Number (10DLC assigned to campaign)
```

### Brand Registration

**What carriers check:**
- Business legitimacy (EIN, registered entity)
- Industry type (some industries face stricter rules)
- Previous violations (TCPA fines, carrier blocks)

**Trust score (0-100):**
- 75-100: High trust → higher throughput, lower filtering
- 50-74: Medium trust → moderate throughput
- <50: Low trust → aggressive filtering, possible rejection

### Campaign Registration

**Required information:**
- Use case description (marketing, alerts, 2FA, etc.)
- Opt-in method (web form, keyword, etc.)
- Sample messages
- Expected volume

**Campaign types and scrutiny:**
- **2FA/OTP**: Low scrutiny, high deliverability
- **App alerts**: Low scrutiny
- **Marketing**: Medium scrutiny
- **Lead generation**: High scrutiny
- **Debt collection**: Very high scrutiny

### Common 10DLC Rejection Reasons

1. **Brand not registered**: Customer skipped brand registration
2. **Campaign missing**: Messages sent without campaign association
3. **Use case mismatch**: Registered as "alerts" but sending marketing
4. **Sample messages don't match**: Registered samples differ from actual content
5. **Invalid opt-in**: No documented consent

🔧 **NOC Tip:** When a customer's deliverability drops, check their 10DLC trust score trend. A score drop from 80 to 60 explains why messages that previously worked are now being filtered. Trust score changes happen monthly based on rolling metrics — opt-out rate spikes, complaint spikes, and high invalid number rates all degrade score. Work with the customer to improve their messaging practices.

## Toll-Free Verification

Toll-free messaging has its own verification process:

**Unverified toll-free:**
- Low throughput (limited messages per day)
- Aggressive content filtering
- May be blocked entirely for A2P

**Verified toll-free:**
- Higher throughput
- Better deliverability
- Still subject to content filtering

**Verification process:**
1. Submit business information
2. Describe use case
3. Provide opt-in documentation
4. Carrier reviews (days to weeks)
5. Approved or rejected

**Common rejection reasons:**
- Incomplete business documentation
- Use case not supported for toll-free
- Previous violations on same number

## Working With Carriers During Filtering Events

When filtering impacts legitimate traffic:

### Step 1: Confirm It's Filtering

```
# Graylog query to identify pattern
type:SMS AND status:DELIVERED AND carrier:Verizon
| stats count by hour(timestamp)

# Compare delivered vs failed rates
type:SMS AND (status:DELIVERED OR status:FAILED)
| stats count by status, carrier
```

If delivery rate to one carrier dropped significantly, filtering is likely.

### Step 2: Identify the Trigger

- Did the customer change message content?
- Did volume increase suddenly?
- Was there a campaign or marketing push?
- Did 10DLC trust score change?

### Step 3: Open a Carrier Ticket

Most carriers have support channels for legitimate businesses:

**Information needed:**
- Message IDs affected
- Sender number(s)
- Recipient examples
- Sample message content
- Business justification
- 10DLC/toll-free registration status

**What carriers can do:**
- Whitelist specific senders (rare, requires strong justification)
- Provide specific filter feedback ("your message triggered X rule")
- Expedite verification processes
- Adjust throughput limits

**What carriers won't do:**
- Reveal exact filter rules
- Guarantee no future filtering
- Whitelist content patterns

### Step 4: Customer Remediation

Help customers improve their practices:

1. **Clean lists**: Remove invalid numbers, opt-outs
2. **Improve consent**: Document opt-in clearly
3. **Simplify content**: Remove links, reduce marketing language
4. **Register properly**: Complete 10DLC/toll-free registration
5. **Monitor metrics**: Track opt-out rate, complaint rate

## Real-World Scenario

**Customer report:** "Our messages stopped being delivered to Verizon recipients 3 days ago."

**Investigation:**

1. Query failed messages to Verizon:
```
type:SMS AND carrier:Verizon AND status:FAILED
| stats count by day(timestamp), error_code
```

2. Results:
- Day 1: 5% failure rate (normal)
- Day 2: 40% failure rate (spike)
- Day 3: 70% failure rate (severe)
- Error code: 30004 (Message blocked)

3. Check customer's 10DLC status:
- Trust score: 55 (dropped from 78)
- Campaign: Marketing
- Recent changes: None

4. Check opt-out rate trend:
```
type:SMS AND event:opt_out AND customer_id:CUST-ABC
| stats count by week
```
- Opt-outs increased from 0.5% to 3% in the past week

5. Check message content:
```
type:SMS AND customer_id:CUST-ABC
| sample body
```
- Message contains: "Click here for your FREE gift!"
- Link to shortened URL
- Marketing language

**Root cause:** 
- Customer's opt-out rate spiked
- Trust score dropped from 78 to 55
- Verizon's filter became more aggressive
- Content triggers ("FREE", shortened URL) combined with low trust score

**Resolution:**
1. Immediate: Customer removes "FREE", removes shortened URLs
2. Short-term: Customer improves opt-in process, reduces opt-outs
3. Long-term: Trust score improves over 30-60 days, filtering reduces

---

**Key Takeaways:**

1. Carriers filter for spam prevention, network protection, and regulatory compliance — their defaults favor blocking over risking spam
2. Content filtering triggers: marketing language, shortened URLs, excessive capitalization, suspicious links
3. Volume filtering: each sender has throughput limits; exceeding them causes throttling or rejection
4. Sender reputation (trust score for 10DLC) affects filtering — lower score = more aggressive filtering
5. 10DLC registration requires brand, campaign, and number association — unregistered traffic is filtered heavily
6. When investigating filtering: identify pattern, check trust score, review content, open carrier ticket if legitimate
7. Long-term deliverability requires clean lists, documented consent, and maintaining low opt-out/complaint rates

**Next: Lesson 118 — Traceroute and MTR — Deep Dive**
