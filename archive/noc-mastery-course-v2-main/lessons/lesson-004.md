# Lesson 4: Number Portability and the LNP Database
**Module 1 | Section 1.1 — The PSTN: History, Circuit Switching, and SS7**
**⏱ ~6 min read | Prerequisites: Lesson 3**

---

## Why Numbers Had to Become Portable

Before 1996, your phone number was permanently tied to your carrier. Switching from AT&T to MCI meant getting a new phone number — which meant reprinting business cards, updating every contact, and losing the number your customers knew. This was a massive barrier to competition, and carriers knew it.

The **Telecommunications Act of 1996** mandated Local Number Portability (LNP) in the United States, requiring carriers to allow customers to keep their phone numbers when switching providers. This fundamentally changed how phone calls are routed and created an entire infrastructure layer that Telnyx interacts with daily.

For NOC engineers, LNP isn't academic. Number porting issues cause real incidents: calls routing to the wrong carrier, porting delays blocking customer migrations, and stale LNP data causing call failures.

## How LNP Works — The Location Routing Number

Before LNP, routing was simple: the first 6 digits of a phone number (NPA-NXX, i.e., area code + exchange) told you which switch served that number. All numbers in 212-555-XXXX belonged to the same switch.

LNP broke this assumption. Now, 212-555-1234 might belong to AT&T while 212-555-1235 belongs to Telnyx. You can no longer route based on the NPA-NXX alone.

The solution is the **Location Routing Number (LRN)** — a 10-digit number that identifies the switch currently serving a ported number. Here's how it works:

1. **Before routing a call**, the originating carrier performs a **dip** — a real-time database query to the Number Portability Administration Center (NPAC)
2. The query asks: "Has this number been ported? If so, what's the LRN?"
3. If the number has been ported, the NPAC returns the LRN of the new serving switch
4. The originating carrier routes the call to the switch identified by the LRN instead of the switch implied by the dialed digits

**Example:**
- Customer ports 212-555-1234 from AT&T to Telnyx
- AT&T's switch for 212-555 has LRN 212-555-0000
- Telnyx's switch in New York has LRN 646-847-0000 (hypothetical)
- When anyone calls 212-555-1234, the dip returns LRN 646-847-0000
- The call routes to Telnyx's switch, which delivers it to the customer

The LRN looks like a regular phone number but is never dialed by humans — it's purely a routing construct.

## The NPAC — Number Portability Administration Center

The **NPAC** is the centralized database (operated by iconectiv in North America) that stores the mapping between ported numbers and their serving carrier's LRN. There are regional NPAC databases, and all carriers synchronize with them.

The porting process:
1. **Customer** requests a port from Old Carrier to New Carrier (Telnyx)
2. **New Carrier** submits a port request to the NPAC
3. **Old Carrier** receives notification and has a window to confirm or reject (typically for validation, not to block the port)
4. **FOC (Firm Order Confirmation)** is issued with a scheduled port date/time
5. At the scheduled time, the **NPAC updates the LRN** mapping
6. The old carrier **releases** the number; the new carrier **activates** it
7. All carriers' local databases synchronize with the NPAC update

🔧 **NOC Tip:** Porting-related call failures often occur in the window around the port activation time. If a customer reports "my number isn't working" right after a port, check: (1) Has the NPAC actually activated the port? (2) Has Telnyx's routing been configured for the number? (3) Has the old carrier released the number? A common issue is the port activating in NPAC but the old carrier not releasing the number promptly, causing a brief period where calls fail on both sides.

## Dip Queries — Real-Time Database Lookups

Every call to a ported number requires a **dip** — a real-time query to determine the current LRN. These dips happen billions of times per day across the North American network.

There are two approaches:

**All-Call Query (ACQ):** Dip every single call, regardless of whether the number might be ported. This ensures routing is always current but generates massive query volume.

**Query-on-Release (QoR):** Only dip when the call arrives at the original serving switch and that switch discovers the number has been ported. This is more efficient but adds an extra routing hop.

Most carriers, including Telnyx, use ACQ or subscribe to LNP database feeds that maintain a local copy of porting data, reducing real-time query latency.

**Dip costs matter.** Each LNP dip has a cost (fractions of a cent), and at scale (millions of calls per day), these costs are significant. This is one reason carriers maintain local copies of the LNP database rather than querying the NPAC for every call.

## Impact on Telnyx Operations

LNP touches multiple aspects of Telnyx's business:

**Inbound Call Routing:** When a call arrives for a Telnyx customer's ported number, the originating carrier's dip must return Telnyx's LRN. If the NPAC data is stale or incorrect, calls won't reach Telnyx.

**Outbound Call Routing:** When Telnyx originates a call, it performs its own LNP dip to determine the serving carrier of the destination number. This dip informs routing decisions — which carrier to send the call to and via which interconnection point.

**Number Porting Lifecycle:** Telnyx regularly ports numbers in (from other carriers to Telnyx) and out (from Telnyx to other carriers). Each port involves NPAC coordination, FOC scheduling, and activation — all of which can encounter issues.

**Number Lookup API:** Telnyx offers a Number Lookup API that performs LNP/LRN queries. This API is essentially a dip-as-a-service product, allowing customers to determine the serving carrier of any number before routing.

## A Real Troubleshooting Scenario

**Scenario:** A Telnyx customer ported their number three days ago. Calls from most carriers work fine, but calls from one specific carrier consistently get "number not in service" treatment.

**Analysis:**
- The NPAC has the correct LRN (verified because most carriers route correctly)
- The failing carrier likely has a **stale local LNP database** that hasn't synced the update
- Some smaller carriers or resellers update their local LNP caches less frequently

**What to investigate:**
1. Confirm the NPAC record is correct (Telnyx porting team can verify)
2. Have the customer provide the failing carrier's name
3. Check if the failing carrier is known for slow LNP updates
4. If needed, contact the failing carrier and request they refresh their LNP data for the affected number

**Resolution:** This usually resolves itself within 24-48 hours as caches refresh. For urgent cases, a direct request to the failing carrier to refresh their cache can accelerate resolution.

🔧 **NOC Tip:** When investigating porting-related call failures, always determine the directionality. "Inbound calls failing" vs. "outbound calls failing" have completely different root causes. Inbound failures point to LRN/NPAC issues (other carriers can't find Telnyx). Outbound failures point to Telnyx's own routing or the destination carrier's issues. Also check if the problem is universal or carrier-specific — a universal failure suggests an NPAC issue; a carrier-specific failure suggests a local database sync problem.

## The Broader Picture

LNP is one example of how the PSTN's intelligence layer (SS7 databases, SCPs) was essential infrastructure. In the SIP world, equivalent functionality is handled through:
- **ENUM (E.164 Number Mapping)**: DNS-based lookup that maps phone numbers to SIP URIs
- **LNP dip services**: Third-party databases queried via API before routing
- **Carrier routing tables**: Maintained by interconnection agreements

Understanding LNP helps you understand a significant portion of Telnyx's routing infrastructure and why number porting — something that seems like a simple administrative task — is actually a complex distributed database synchronization problem.

---

**Key Takeaways:**
1. LNP allows phone numbers to move between carriers; the LRN (Location Routing Number) tells the network which switch currently serves a ported number
2. Every call to a ported number requires a dip — a real-time database query that returns the LRN, adding latency and cost to call routing
3. Porting failures often stem from NPAC synchronization delays — stale LRN data in a carrier's local database causes misrouted or failed calls
4. The porting lifecycle (request → FOC → activation → release) involves multiple carriers and NPAC coordination — failures at any stage cause incidents
5. Telnyx interacts with LNP as both a porting participant (porting numbers in/out) and a dip consumer (querying LRN for outbound routing)

**Next: Lesson 5 — Analog to Digital — The Nyquist Theorem and PCM**
