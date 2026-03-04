# Lesson 85: Number Lookup API — LRN, Carrier, and Caller ID
**Module 2 | Section 2.8 — Lookup/Verify**
**⏱ ~5 min read | Prerequisites: Lesson 72**

---

## Why Number Lookup Matters

Before routing a call, sending an SMS, or processing a transaction, you often need to know: Who owns this number? What kind of number is it? Is it still active? The Number Lookup API answers these questions with real-time database queries. For NOC engineers, understanding how these lookups work helps debug routing decisions, fraud investigations, and delivery failures.

## LRN Lookup: Who Serves This Number?

The **Location Routing Number (LRN)** lookup is the foundational query for call routing, and we first encountered it in Lesson 4. When Telnyx needs to route an outbound call, it performs an LRN dip to determine which carrier currently serves the destination number.

### How It Works Under the Hood

1. Telnyx queries the NPAC (Number Portability Administration Center) database with the destination number
2. If the number has been ported, the NPAC returns the LRN — a 10-digit routing number that identifies the serving switch
3. If the number hasn't been ported, the default routing is based on the NPA-NXX (area code + exchange), which maps to the original carrier
4. The LRN tells Telnyx's routing engine which carrier to send the call to

LRN dips happen on virtually every outbound call. They're fast (typically <50ms) but they have a cost — every dip is a paid database query. This creates an optimization tension: dip every call for accurate routing, or cache results and risk routing to the wrong carrier.

🔧 **NOC Tip:** If outbound calls to a specific number are failing with "no route" or reaching the wrong carrier, perform a manual LRN dip via the Number Lookup API. If the number was recently ported, the routing database might have stale data. Compare the LRN result with what Telnyx's routing engine used.

## Carrier Lookup: Who Operates This Number?

A carrier lookup goes beyond LRN to return the **current operating carrier** for a number. This is useful for:

- **Routing optimization** — Knowing the carrier helps select the best interconnect path
- **Fraud prevention** — Numbers recently ported to VoIP carriers are higher fraud risk
- **Billing** — Some pricing depends on the destination carrier or network type

The carrier lookup returns information like:
- Carrier name (e.g., "T-Mobile USA")
- Network type (mobile, landline, VoIP)
- Country and region

### Number Type Identification

One of the most valuable fields is **number type**: mobile, landline, or VoIP. This matters because:

- **SMS delivery** — SMS can only be delivered to mobile numbers (and some VoIP numbers). Sending to a landline fails silently or returns an error.
- **Pricing** — Mobile termination often costs more than landline
- **Fraud signals** — VoIP numbers are easier to obtain anonymously and are higher-risk for fraud

🔧 **NOC Tip:** When investigating SMS delivery failures, the first check should be the number type. If the destination is a landline, SMS will never work. Customers frequently submit landlines expecting SMS delivery. A quick lookup saves hours of debugging.

## Caller ID Lookup: CNAM Query

The Caller ID lookup queries CNAM databases (as described in Lesson 74) to retrieve the name associated with a phone number. This is the same query terminating carriers perform to display caller names.

Telnyx's API gives customers access to this data programmatically. Common use cases:

- **Inbound call screening** — Display the caller's name before answering
- **Lead validation** — Verify that a phone number belongs to an expected person/business
- **Contact enrichment** — Add names to phone number databases

The CNAM query returns up to 15 characters. Quality varies — some numbers have well-maintained CNAM records, while others return empty or outdated names.

## Lookup Architecture and Caching

Number lookups hit external databases, which introduces latency and cost considerations:

**Latency** — Real-time lookups add 20-100ms to the processing path. For call routing, this is acceptable. For high-volume batch processing, it can be a bottleneck.

**Caching** — Telnyx caches lookup results to reduce cost and latency. Cache TTLs must balance freshness against cost:
- LRN data changes infrequently (only when numbers port) — longer cache TTLs are safe
- Carrier data is similarly stable — moderate TTLs work
- CNAM data can change anytime — shorter TTLs or no caching may be appropriate

**Cost** — Each dip to an external database has a per-query cost from the database provider. High-volume customers performing millions of lookups need to be aware of these costs.

## Use Cases Beyond Routing

### Fraud Prevention

Number lookups are a powerful fraud detection tool:

- **Number freshness** — Recently ported numbers, especially to VoIP carriers, are higher fraud risk
- **Type mismatch** — A customer claims to be calling from a mobile but the number is a VoIP line
- **Carrier inconsistency** — The number's carrier doesn't match expected patterns for the geography

### Routing Optimization

Beyond basic routing, carrier data enables smart routing decisions:

- **Direct interconnect** — If Telnyx has a direct peering with the destination carrier, route the call through that interconnect for better quality and lower cost
- **Least-cost routing** — Different carriers have different termination rates; knowing the carrier in advance enables optimal route selection

## Real-World Troubleshooting Scenario

**Scenario:** A customer's application is experiencing high latency when processing inbound calls. Each call takes an extra 200ms before the webhook fires.

**Investigation:**
1. Check if the customer has enabled caller ID lookup on their connection — this adds a CNAM dip to every inbound call
2. Check CNAM database response times in monitoring — the external database might be slow
3. Check if caching is effective — cache hit rate should be high for repeat callers

**Resolution:** If CNAM dip latency is the cause, the customer can disable it if they don't need caller names, or Telnyx can investigate the database provider's performance. Caching configurations can be tuned to improve hit rates.

---

**Key Takeaways:**
1. LRN lookups determine which carrier serves a number — essential for call routing and performed on virtually every outbound call
2. Number type identification (mobile/landline/VoIP) is critical for SMS delivery — sending to a landline will always fail
3. CNAM lookups are terminating-side queries that return caller names — quality and freshness vary across databases
4. Caching is essential for performance and cost management, but cache staleness can cause routing issues for recently ported numbers
5. Number lookups serve double duty: routing optimization and fraud prevention

**Next: Lesson 76 — Verify API — Phone Number Verification**
