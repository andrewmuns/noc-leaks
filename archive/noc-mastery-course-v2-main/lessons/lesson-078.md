# Lesson 78: SMS/MMS Architecture — How Messages Flow

**Module 2 | Section 2.6 — Messaging**
**⏱ ~8 min read | Prerequisites: Lesson 18**

---

## From API Call to Handset: The Journey of a Text Message

When a developer calls `POST /v2/messages` to send an SMS, it looks instant. But beneath that API call is a complex chain of systems, protocols, and carrier relationships that transport the message from Telnyx's infrastructure to a cell phone potentially on the other side of the world.

Understanding this chain is essential for NOC operations because messaging failures can occur at any link, and each requires different diagnostic approaches.

## The SMS Delivery Path

```
Customer App                   Telnyx                        Carrier
┌──────────┐    ┌─────────────────────────────┐    ┌──────────────────┐
│ REST API  │──▶│ Messaging API Gateway       │    │                  │
│ call      │   │       │                     │    │  Aggregator      │
│           │   │       ▼                     │──▶│  or Direct       │
│           │   │ Message Router              │   │  Interconnect    │
│           │   │ (number lookup, carrier     │   │       │          │
│           │   │  selection, compliance)     │   │       ▼          │
│           │   │       │                     │   │  Carrier SMSC    │
│           │   │       ▼                     │   │  (Short Message  │
│           │   │ Upstream Delivery           │   │   Service Center)│
│           │   │ (SMPP/HTTP to carrier)      │   │       │          │
│           │   └─────────────────────────────┘   │       ▼          │
│           │                                      │  Cell Tower      │
│           │                                      │       │          │
│           │                                      │       ▼          │
│           │                                      │  Handset         │
└──────────┘                                      └──────────────────┘
```

### Step 1: API Ingestion

The Messaging API Gateway receives the request, validates it (authentication, parameter validation, rate limits), and enqueues the message for processing. The API returns `202 Accepted` — the message is queued, not delivered. This is an important distinction that customers often misunderstand.

### Step 2: Message Routing

The Message Router determines how to deliver the message:
1. **Number lookup**: What carrier serves the destination number? (LRN/carrier database — Lesson 75)
2. **Route selection**: Which upstream path should we use? (Direct carrier interconnect vs. aggregator)
3. **Compliance check**: Is this message allowed? (10DLC campaign verification, opt-out checking, content screening)
4. **Number formatting**: Normalize the destination to E.164 format

### Step 3: Upstream Delivery

Telnyx delivers the message to the carrier using one of two protocols:

**SMPP (Short Message Peer-to-Peer):** The traditional SMS interconnection protocol. Binary, efficient, connection-oriented. Most carrier interconnects use SMPP. Telnyx maintains persistent SMPP connections (binds) to carriers and aggregators.

**HTTP/HTTPS:** Some modern carriers accept messages via REST APIs. Simpler to implement but less established for high-volume traffic.

### Step 4: Carrier SMSC

The receiving carrier's Short Message Service Center (SMSC) accepts the message and handles delivery to the handset. If the phone is off or out of coverage, the SMSC stores the message and retries (store-and-forward). Messages are typically stored for 24-72 hours before being discarded.

### Step 5: Last-Mile Delivery

The SMSC delivers the message to the handset via the carrier's radio network. The handset acknowledges receipt, and the carrier generates a Delivery Receipt (DLR).

## MMS: Adding Multimedia

MMS (Multimedia Messaging Service) adds images, videos, and longer text to messaging. The architecture is more complex:

1. **Media storage**: The image/video is uploaded to a media server
2. **MM4/MM7 protocol**: MMS uses different carrier interconnection protocols than SMS
3. **Content adaptation**: carriers may resize images for the recipient's device
4. **Interoperability challenges**: different carriers handle MMS differently (image size limits, supported formats)

MMS messages travel through **MMSC** (Multimedia Messaging Service Centers) rather than SMSCs. The media content itself is typically delivered as a URL — the recipient's phone downloads the content from the MMSC.

🔧 **NOC Tip:** MMS failures are often media-related. If text SMS works but MMS fails: check if the media URL is accessible from the carrier's MMSC, check file size limits (typically 1-3MB depending on carrier), and check supported formats (JPEG, PNG, GIF are safest).

## Long Code vs. Short Code vs. Toll-Free

**Long codes (10-digit numbers):** Standard phone numbers. Used for person-to-person (P2P) and application-to-person (A2P) messaging. Subject to 10DLC regulations for A2P (Lesson 69). Throughput: 1-100+ messages/second depending on trust score.

**Short codes (5-6 digit numbers):** Dedicated high-throughput numbers. Expensive to lease and provision ($500-1000/month). Throughput: 100+ messages/second. Used for high-volume campaigns.

**Toll-free numbers:** 1-800/888/etc. Can be enabled for SMS. Moderate throughput. Must go through a verification process for A2P.

## Delivery Receipts (DLRs)

DLRs are status updates from the carrier indicating what happened to the message. Common statuses:
- **delivered**: message reached the handset
- **undelivered**: delivery failed (invalid number, phone off too long, carrier rejection)
- **sent**: accepted by the carrier but no delivery confirmation (common with some carriers)

**The reliability problem:** Not all carriers send DLRs reliably. Some carriers:
- Never send DLRs for certain message types
- Send DLRs with significant delay (minutes to hours)
- Report "delivered" when the message only reached the SMSC, not the handset
- Don't differentiate between "delivered" and "read"

🔧 **NOC Tip:** When a customer says "messages aren't being delivered," check if they mean "no DLR received" or "the recipient didn't get the message." These are different problems. Missing DLRs might be a carrier DLR reliability issue, not a delivery issue.

## Message Queuing and Rate Limiting

Messages are queued at multiple levels:
1. **Telnyx internal queue**: after API acceptance, before carrier delivery
2. **Carrier queue**: carriers impose rate limits per sending number
3. **SMSC queue**: the carrier's message center queues for handset delivery

Rate limits vary by number type and registration status:
- Unregistered long code: ~1 msg/sec (T-Mobile), higher on other carriers
- Registered 10DLC: 3-75+ msg/sec depending on trust score
- Short code: 100+ msg/sec
- Toll-free: 3-25+ msg/sec after verification

Exceeding rate limits causes carrier throttling or rejection. Messages are queued on Telnyx's side and delivered at the allowed rate.

## Inbound Message Flow

Inbound messages (handset → customer application) follow the reverse path:

1. Carrier delivers the message to Telnyx via SMPP/HTTP
2. Telnyx routes it based on the destination number's configuration
3. Message is delivered to the customer via webhook (HTTP POST) or stored for API polling

The webhook delivery for inbound messages has the same reliability considerations as Call Control webhooks (Lesson 62).

## Troubleshooting Scenario: "Messages to T-Mobile Numbers Are Failing"

A customer reports that messages to T-Mobile numbers started failing while AT&T and Verizon work fine.

**Investigation:**
1. Graylog: Search for the customer's sending number + T-Mobile destination numbers
2. Found: upstream delivery returns error code 30007 — "carrier violation"
3. Check 10DLC registration: customer's campaign is approved, but...
4. The sending number wasn't properly assigned to the 10DLC campaign in TCR
5. T-Mobile enforces 10DLC strictly; AT&T and Verizon were more lenient at the time

**Resolution:** Customer assigned the sending number to their registered campaign. T-Mobile deliveries resumed.

---

**Key Takeaways:**
1. SMS delivery is a multi-hop chain: Telnyx API → Message Router → Upstream (SMPP/HTTP) → Carrier SMSC → Handset
2. `202 Accepted` from the API means "queued," not "delivered" — delivery is asynchronous
3. DLRs are not 100% reliable — some carriers don't send them consistently
4. MMS uses different protocols (MM4/MM7) and has media size/format constraints
5. Rate limits vary dramatically by number type and 10DLC registration status
6. Different carriers enforce compliance (10DLC) with varying strictness — T-Mobile being the most aggressive

**Next: Lesson 69 — 10DLC: A2P Messaging Registration and Compliance**
