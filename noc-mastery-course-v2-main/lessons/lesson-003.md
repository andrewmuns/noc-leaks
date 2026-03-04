# Lesson 3: SS7 Signaling — The Brain of the PSTN
**Module 1 | Section 1.1 — The PSTN: History, Circuit Switching, and SS7**
**⏱ ~9 min read | Prerequisites: Lesson 2**

---

## Why Signaling Matters

In Lesson 1, we saw that the earliest telephone networks used **in-band signaling** — the same circuit that carried voice also carried control information (dial pulses, busy tones). This worked, but it had a fatal flaw: since signaling and voice shared the same channel, anyone who could generate the right tones could manipulate the network.

In the 1960s and 70s, "phone phreaks" famously exploited Multi-Frequency (MF) in-band signaling by blowing precise tones into the handset. A 2600 Hz tone could seize a trunk; specific MF tone sequences could route calls for free. The most famous tool was the "blue box" — a device that generated MF signaling tones.

This vulnerability, combined with the need for more sophisticated call control features, drove the development of **Signaling System 7 (SS7)** — a completely separate signaling network that runs **out-of-band**, on dedicated data links that subscribers never touch.

Understanding SS7 is essential for NOC engineers because **SIP is SS7's spiritual successor**. The call flows are remarkably similar. If you understand how an SS7 ISUP call setup works, SIP call flows (Lesson 44) become immediately intuitive.

## In-Band vs. Out-of-Band Signaling

**In-band signaling** means control information travels on the same path as the conversation:
- Dial pulses (rotary phone) — electrical interruptions on the voice circuit
- DTMF tones (touch-tone) — audio-frequency tones in the voice path
- MF signaling — special frequency pairs used between switches

**Out-of-band signaling** means control information travels on a completely separate network:
- SS7 uses dedicated 64 kbps data links (DS0 channels) exclusively for signaling
- Voice circuits carry only voice — no control information
- The signaling network is physically separate from the bearer (voice) network

This separation provides three critical benefits:
1. **Security**: Subscribers can't inject signaling commands
2. **Speed**: Call setup can begin before a voice circuit is allocated
3. **Intelligence**: Complex routing decisions, database queries, and feature control happen on the signaling network without affecting voice quality

🔧 **NOC Tip:** The in-band vs. out-of-band distinction survives in SIP. SIP signaling (INVITE, BYE, etc.) travels separately from RTP media. When you're troubleshooting, always analyze signaling and media independently — a call can have perfect signaling but broken media, or vice versa.

## The SS7 Protocol Stack

SS7 is a layered protocol stack, and while you don't need to memorize every layer, understanding the architecture helps you see the parallels with SIP:

### Message Transfer Part (MTP) — Layers 1-3

**MTP1** — Physical layer. Typically a DS0 (64 kbps) channel on a T1/E1.

**MTP2** — Data link layer. Provides reliable, sequenced delivery of signaling messages between directly connected nodes. Error detection, retransmission, flow control. Think of it as the SS7 equivalent of TCP's reliability.

**MTP3** — Network layer. Routes signaling messages through the network based on point codes (the SS7 equivalent of IP addresses). Every switch and signaling node has a unique **point code** — a numeric address used to route messages.

### Upper Layers

**SCCP (Signaling Connection Control Part)** — Adds connection-oriented and connectionless services on top of MTP3. Enables communication between applications, not just nodes.

**TCAP (Transaction Capabilities Application Part)** — Provides database query/response functionality. Used for number portability lookups (Lesson 4), toll-free routing, caller ID name (CNAM) queries, and more.

**ISUP (ISDN User Part)** — The call control protocol. Manages circuit-switched call setup, teardown, and maintenance. This is the layer most directly comparable to SIP.

**MAP (Mobile Application Part)** — Manages mobile network functions: roaming, handovers, SMS routing. Relevant when understanding how mobile calls interact with Telnyx's network.

## The Signaling Network Topology

SS7 uses a dedicated mesh of signaling nodes:

**SSP (Service Switching Point)** — The telephone switch itself. Originates and terminates calls. Generates ISUP messages to request call connections.

**STP (Signal Transfer Point)** — A signaling router. Routes SS7 messages between nodes based on point codes. STPs operate in mated pairs for redundancy — if one fails, its mate handles all traffic.

**SCP (Service Control Point)** — A database server. Responds to queries from SSPs (via TCAP) for intelligent routing decisions: toll-free number translation, number portability lookups, calling name delivery.

The topology is always redundant: every SSP connects to at least two STPs, and every STP pair cross-connects to other STP pairs. This creates a highly reliable signaling network that can survive individual node or link failures.

## ISUP Call Flow — The SS7 Equivalent of SIP

Here's how a circuit-switched call sets up via ISUP. Compare this to the SIP INVITE flow (Lesson 44) — the parallels are striking:

### The ISUP Message Sequence

```
Caller's Switch (SSP-A)              Callee's Switch (SSP-B)
       |                                      |
       |--- IAM (Initial Address Message) --->|
       |    [Called number, calling number,    |
       |     trunk circuit ID, codec info]    |
       |                                      |
       |<-- ACM (Address Complete Message) ---|
       |    [Call is being presented to       |
       |     the subscriber, ringing]         |
       |                                      |
       |<-- ANM (Answer Message) -------------|
       |    [Subscriber answered, start       |
       |     billing, connect voice path]     |
       |                                      |
       |====== Voice conversation ============|
       |                                      |
       |--- REL (Release) ------------------>|
       |    [Caller hung up, reason code]     |
       |                                      |
       |<-- RLC (Release Complete) -----------|
       |    [Circuit freed]                   |
       |                                      |
```

Now compare to SIP:

| ISUP Message | SIP Equivalent | Purpose |
|-------------|---------------|---------|
| IAM | INVITE | Initiate call, carry addressing and media info |
| ACM | 180 Ringing | Destination is alerting the user |
| ANM | 200 OK | Call answered, start billing |
| — | ACK | (No ISUP equivalent — circuit was pre-allocated) |
| REL | BYE | Release the call |
| RLC | 200 OK (to BYE) | Confirm release |

The mapping isn't perfect, but the conceptual flow is nearly identical. SIP's INVITE carries SDP (codec and media info) just as IAM carries bearer capability parameters. ACM and 180 Ringing both mean "the phone is ringing." ANM and 200 OK both mean "answered, start billing."

🔧 **NOC Tip:** When reading SIP call flows in Graylog or packet captures, mentally map them to this ISUP flow. It makes the sequence intuitive: INVITE = "I want to call someone," 180 = "it's ringing," 200 OK = "they answered," BYE = "we're done." The SIP response codes (Lesson 40) map to ISUP cause codes — for example, ISUP Cause 17 (User Busy) maps to SIP 486 Busy Here.

## How SS7 Enables Advanced Features

SS7's real power isn't just call setup — it's the **database queries** that happen before or during call routing:

**Toll-Free Routing:** When you dial 1-800-XXX-XXXX, the originating switch sends a TCAP query to an SCP: "Where should I route this 800 number?" The SCP responds with the actual destination number (an ordinary PSTN number), and the switch routes the call there. The subscriber never sees the real number.

**Caller ID (CNAM):** When a call arrives, the terminating switch queries a CNAM database: "What name is associated with this calling number?" The response populates the caller ID display.

**Local Number Portability (LNP):** Before routing a call, the originating switch queries the NPAC database: "Has this number been ported to another carrier?" If so, the response includes a Location Routing Number (LRN) that redirects the call. This is covered in depth in Lesson 4.

These database dips happen in real-time during call setup, adding milliseconds of delay but enabling features that would be impossible with simple digit-based routing.

## A Real Troubleshooting Scenario

**Scenario:** Calls from Telnyx to a specific PSTN destination range are failing with SIP 404 Not Found, but the numbers are valid and were working last week.

**Analysis:** This pattern often indicates a number portability issue. The called numbers may have ported to a new carrier, and the LNP database dip is either returning incorrect routing information or the new carrier hasn't completed their side of the porting process.

**What to investigate:**
1. Run an LRN lookup on the affected numbers — has the LRN changed recently?
2. Check if the new LRN routes to a valid carrier
3. If the numbers ported to a new carrier, verify the porting was completed on both sides
4. Check Telnyx's routing tables for the destination number range

**Resolution:** If the LRN data is correct but routing fails, the issue may be with the interconnection to the new serving carrier. If LRN data is stale, the NPAC may not have propagated the update yet.

## The Legacy Lives On

SS7 is gradually being replaced by SIP-based signaling (particularly for carrier-to-carrier interconnection via SIP trunks), but it remains the backbone of the PSTN. Every time a Telnyx SIP call terminates to a traditional PSTN destination, the call crosses from SIP to SS7 at a gateway — and understanding both protocols makes you effective at diagnosing problems on either side of that boundary.

More importantly, SS7's design philosophy — separate signaling from bearer, use databases for intelligent routing, maintain redundant signaling paths — directly influenced SIP's architecture. The concepts are the same; only the encoding changed (binary TLV in SS7 → text-based headers in SIP).

---

**Key Takeaways:**
1. SS7 replaced in-band signaling with a separate, secure signaling network — eliminating the vulnerability that phone phreaks exploited
2. The SS7 stack (MTP/SCCP/TCAP/ISUP) maps conceptually to the IP stack (Ethernet/IP/TCP/SIP)
3. ISUP call flow (IAM→ACM→ANM→REL→RLC) directly parallels SIP call flow (INVITE→180→200→BYE→200)
4. SS7 databases (SCPs) enable intelligent features like toll-free routing, CNAM, and LNP — concepts that persist in modern routing
5. ISUP cause codes map to SIP response codes — knowing this mapping is essential for debugging PSTN-terminated calls

**Next: Lesson 4 — Number Portability and the LNP Database**
