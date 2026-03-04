# Lesson 82: Number Provisioning — Ordering, Searching, and Assigning
**Module 2 | Section 2.7 — Numbers**
**⏱ ~7 min read | Prerequisites: Lesson 4**

---

## The Lifecycle of a Phone Number

Every phone call that traverses Telnyx's network begins with a phone number. But phone numbers aren't just random strings of digits — they're regulated resources with complex supply chains, geographic significance, and technical constraints that directly affect how calls are routed, billed, and delivered. Understanding number provisioning is essential for NOC engineers because misconfigured or improperly provisioned numbers are among the most common root causes of "calls not working."

## How Telnyx Sources Numbers

Phone numbers originate from national regulators — the FCC in the US, OFCOM in the UK, ARCEP in France, and so on. These regulators allocate blocks of numbers (typically in blocks of 1,000 or 10,000) to carriers. Telnyx obtains numbers through several channels:

**Direct allocation** — In markets where Telnyx holds a carrier license, numbers are allocated directly from the national numbering authority. This gives Telnyx the most control over inventory and the fastest provisioning times.

**Upstream carrier agreements** — In markets where Telnyx doesn't hold a direct license, numbers are sourced from local carriers through wholesale agreements. This adds a dependency: provisioning speed depends on the upstream carrier's systems and APIs.

**Number pooling** — In the US, the Number Pooling Administration System (NPAS) allows carriers to share thousand-blocks. Instead of allocating an entire 10,000-number block to one carrier, individual thousands-blocks can be assigned to different carriers, improving number utilization.

The sourcing method matters to NOC engineers because it affects provisioning latency. Direct-allocation numbers can be activated in seconds. Upstream-carrier numbers may take minutes to hours, depending on the carrier's API responsiveness.

## The Number Search API

When a customer needs a phone number, they query Telnyx's Number Search API. This API exposes the available inventory with powerful filtering:

- **Area code / NPA-NXX** — Find numbers in specific geographic areas
- **City and state** — Geographic search for local presence
- **Pattern matching** — Vanity numbers (e.g., numbers containing "TELNYX")
- **Features** — Filter by capabilities: voice, SMS, MMS, fax, emergency services
- **Number type** — Local, toll-free, national, mobile

Behind the scenes, the search queries Telnyx's number inventory database. This database is continuously updated as numbers are sourced, ordered, released, and recycled. The inventory system must handle race conditions — two customers searching simultaneously might see the same number, but only one can order it.

🔧 **NOC Tip:** When a customer reports "I can't find numbers in area code X," check the inventory database for that NPA. If inventory is genuinely depleted, it's a supply issue, not a platform bug. Some area codes (especially in major metros) have chronically low availability due to high demand.

## Ordering and Activation

When a customer orders a number, a multi-step process kicks off:

1. **Reservation** — The number is temporarily locked in inventory (typically 15–30 minutes) to prevent double-ordering.
2. **Validation** — The system verifies the customer's account is in good standing, has appropriate permissions, and meets regulatory requirements for that number type.
3. **Upstream provisioning** — For numbers sourced from upstream carriers, an API call provisions the number in the carrier's system. This is where delays and failures often occur.
4. **Internal provisioning** — The number is configured in Telnyx's routing tables, making it reachable for inbound calls.
5. **Activation** — The number is marked as active and available for use.

Each step can fail independently. Upstream provisioning failures are the most common — the carrier's system might be slow, return an error, or the specific number might no longer be available (the inventory was stale).

🔧 **NOC Tip:** If a customer reports a newly ordered number isn't receiving calls, check whether internal provisioning completed. The number might be in the customer's portal but not yet in the routing tables. Look for provisioning events in Graylog with the number as a search key.

## Number Assignment

Once ordered, a number must be assigned to a **connection** (for voice) or a **messaging profile** (for SMS/MMS). This assignment determines how the number behaves:

- **Connection assignment** — Links the number to a SIP trunk or Call Control application. Inbound calls to this number are routed to that connection's configured endpoints.
- **Messaging profile assignment** — Links the number to a messaging configuration. Inbound SMS/MMS messages are delivered to the profile's webhook URL.
- **Dual assignment** — A number can be assigned to both a connection (for voice) and a messaging profile (for messaging) simultaneously.

Unassigned numbers are a common support issue: the customer ordered the number but never assigned it, so inbound calls return a 404 or go to a default handler.

## Number Types and Their Implications

Different number types have different technical and regulatory characteristics:

**Local numbers** — Geographic numbers tied to a specific rate center. Callers in the same area may incur local rates. Local numbers typically support voice, SMS, and fax.

**Toll-free numbers** — 800, 888, 877, 866, 855, 844, 833 prefixes in the US. The called party pays for the call. Toll-free numbers are managed by RespOrgs (Responsible Organizations) and have their own porting process.

**National numbers** — Non-geographic numbers available in some countries. No specific area association.

**Mobile numbers** — In some markets, Telnyx provides mobile numbers through its wireless/IoT product. These have different regulatory requirements (e.g., identity verification in some countries).

**International numbers** — Numbers in countries outside the US/Canada. Each country has its own regulatory requirements — some require proof of local address, business registration, or specific documentation.

🔧 **NOC Tip:** When investigating routing failures for international numbers, check the country-specific regulatory requirements. Some countries deactivate numbers that don't meet ongoing compliance requirements (like address verification renewals).

## Number Release and Quarantine

When a customer releases (cancels) a number, it doesn't immediately return to the available pool. Instead, it enters a **quarantine period** — typically 30-90 days. During quarantine:

- The number is not available for new orders
- Inbound calls may receive a "disconnected" treatment
- The quarantine prevents the number from being immediately reassigned to another customer, which could cause confusion (callers reaching the wrong party)

After quarantine, the number returns to the available inventory pool. For numbers sourced from upstream carriers, the release must also be communicated upstream, and the quarantine policy may be dictated by the upstream carrier or regulator.

## Real-World Troubleshooting Scenario

**Scenario:** A customer orders 100 numbers via the API. 95 activate successfully, but 5 return errors.

**Investigation steps:**
1. Check the order API response for each failed number — the error code indicates the failure type
2. Common failures: number already taken (race condition), upstream carrier rejection, regulatory compliance check failed
3. For upstream carrier failures, check the carrier's provisioning queue — there may be a backlog
4. For compliance failures, verify the customer's account has the required documentation

**Resolution:** Retry the failed orders after a brief delay (race condition resolution), or guide the customer to provide required documentation (compliance issue). If the upstream carrier is consistently failing, escalate to the carrier management team.

---

**Key Takeaways:**
1. Phone numbers have a complex lifecycle: sourcing → search → order → provision → assign → use → release → quarantine
2. Provisioning failures often occur at the upstream carrier step — always check whether the number was successfully provisioned end-to-end
3. Unassigned numbers are a top support issue — a number must be assigned to a connection or messaging profile to function
4. Different number types (local, toll-free, international) have different regulatory requirements that affect provisioning
5. Quarantine periods prevent released numbers from immediate reuse, which can affect inventory availability

**Next: Lesson 73 — Number Porting — The Complete Lifecycle**
