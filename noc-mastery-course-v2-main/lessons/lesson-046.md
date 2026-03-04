# Lesson 46: Basic Call Setup — INVITE to 200 OK to BYE
**Module 1 | Section 1.11 — SIP Call Flows**
**⏱ ~8 min read | Prerequisites: Lesson 41**

---

## The Most Important Call Flow

If you learn only one SIP call flow, this is it. The basic INVITE → 200 OK → ACK → media → BYE → 200 OK sequence is the foundation of every voice call. Every other call flow — transfers, conferences, holds — is a variation on this theme.

---

## Step-by-Step: A Complete Call

Let's trace a call from Alice to Bob through Telnyx's B2BUA. There are two independent legs: Alice ↔ Telnyx (Leg A) and Telnyx ↔ Bob (Leg B).

### Phase 1: Call Initiation

```
Alice                    Telnyx B2BUA                    Bob
  |                          |                            |
  |------- INVITE ---------->|                            |
  |<------ 100 Trying -------|                            |
  |                          |------- INVITE ------------>|
  |                          |<------ 100 Trying ---------|
```

**Alice sends INVITE** containing:
- Request-URI: Bob's address (e.g., `sip:+15551234567@sip.telnyx.com`)
- SDP body: Alice's codec offer and media address (where she wants to receive RTP)
- From: Alice's identity
- To: Bob's identity
- Call-ID: Unique identifier for this call
- Via: Alice's address for responses

**Telnyx responds 100 Trying** immediately — this stops Alice's INVITE retransmission timer. The 100 is hop-by-hop; it just means "I got it."

**Telnyx creates a new INVITE** on Leg B toward Bob. This is a *different* INVITE with a different Call-ID, different Via, and potentially different SDP (Telnyx's own media address, possibly different codec list). This is the B2BUA in action — two independent SIP dialogs.

### Phase 2: Ringing and Early Media

```
Alice                    Telnyx B2BUA                    Bob
  |                          |                            |
  |                          |<------ 180 Ringing --------|
  |<------ 180 Ringing ------|                            |
  |                          |                            |
```

**Bob's phone rings** and sends 180 Ringing. Telnyx relays this to Alice (generating its own 180). Alice's phone now plays a local ringback tone.

Alternatively, Bob's side might send **183 Session Progress** with SDP, establishing early media. In that case, the ringback tone comes from the network (through the RTP path) instead of being generated locally. This is how you hear carrier announcements or custom ringback tones.

🔧 **NOC Tip:** If a customer hears double ringback (one local, one from the network), the 183 with early media is arriving but the phone isn't suppressing its local ringback. Check the phone's configuration for "early media" or "180/183 handling" settings.

### Phase 3: Answer — The Three-Way Handshake

```
Alice                    Telnyx B2BUA                    Bob
  |                          |                            |
  |                          |<------ 200 OK (SDP) ------|
  |                          |------- ACK --------------->|
  |<------ 200 OK (SDP) ----|                            |
  |------- ACK ------------->|                            |
  |                          |                            |
```

**Bob answers** — his phone sends 200 OK with SDP (the answer to the codec offer). This is the most critical message in the call flow:
- It establishes the dialog (To-tag is now set)
- It completes codec negotiation (the SDP answer selects codecs)
- It starts billing

**Telnyx ACKs** Bob's 200 OK on Leg B, then generates its own 200 OK to Alice on Leg A. Alice ACKs Telnyx's 200 OK.

**Why ACK exists:** The INVITE/200/ACK is a three-way handshake specifically because a lost 200 OK would mean the callee thinks the call is active but the caller doesn't. Without ACK, there's no confirmation that the caller received the 200 OK. The UAS retransmits the 200 OK until it receives ACK.

### Phase 4: Media Flows

```
Alice                    Telnyx B2BUA                    Bob
  |                          |                            |
  |========= RTP ==========>|========= RTP ============>|
  |<======== RTP ============|<======== RTP =============|
  |                          |                            |
```

RTP media flows bidirectionally. In Telnyx's B2BUA architecture, media typically flows through Telnyx (media anchoring) — Alice sends RTP to Telnyx, Telnyx forwards (possibly transcoded) RTP to Bob, and vice versa.

The media addresses were established by the SDP offer/answer in the INVITE/200 exchange. Alice sends to the IP:port in Telnyx's SDP; Bob sends to the IP:port in Telnyx's SDP on the other leg.

### Phase 5: Teardown

```
Alice                    Telnyx B2BUA                    Bob
  |                          |                            |
  |------- BYE ------------->|                            |
  |                          |------- BYE --------------->|
  |                          |<------ 200 OK -------------|
  |<------ 200 OK -----------|                            |
  |                          |                            |
```

**Alice hangs up** — her phone sends BYE within the established dialog (using the route set and remote target from the dialog state). Telnyx acknowledges with 200 OK and sends its own BYE to Bob on Leg B. Bob confirms with 200 OK.

BYE can come from either side. If Bob hangs up first, the flow is mirrored.

---

## Timing Matters: What Happens When

Understanding the timing of each phase helps with troubleshooting:

| Phase | Typical Duration | Alarm If |
|-------|-----------------|----------|
| INVITE → 100 Trying | < 100ms | > 1s (network/routing delay) |
| 100 Trying → 180 Ringing | 1-5s | > 10s (destination processing delay) |
| 180 Ringing → 200 OK | User-dependent (5-30s) | > 60s (check ring timeout settings) |
| 200 OK → ACK | < 100ms | > 1s (routing/NAT issue) |
| BYE → 200 OK | < 500ms | > 5s (endpoint unresponsive) |

### Post-Dial Delay (PDD)

PDD is the time from INVITE to the first ringback indication (180 or 183). It's one of the most important quality metrics — callers expect to hear ringing within 3-5 seconds. High PDD makes the service feel broken.

Common causes of high PDD:
- DNS resolution delays
- Slow carrier routing
- Overloaded SIP proxies
- LNP dip latency
- Complex IVR processing before ringing indication

🔧 **NOC Tip:** If customers complain about "long silence before ringing," measure PDD in your SIP traces. Check the time between the outbound INVITE and the first 180/183. If it's consistently > 5 seconds, investigate the routing path and carrier response times.

---

## The B2BUA Difference

In a simple proxy model, the INVITE flows through the proxy and dialog is established end-to-end. In Telnyx's B2BUA model:

- **Two separate dialogs** with different Call-IDs, tags, and Via headers
- **Independent SDP negotiation** on each leg — Telnyx can offer different codecs to each side
- **Media anchoring** — RTP flows through Telnyx, enabling recording, transcoding, and monitoring
- **Independent timers** — each leg can have different timeout settings
- **Topology hiding** — neither Alice nor Bob sees the other's real IP address

This architecture gives Telnyx full control over the call but means every call consumes resources on the B2BUA — SIP state, media ports, and potentially transcoding CPU.

---

## Real-World Troubleshooting Scenario

**Problem:** Customer reports calls connect (they hear the other party answer) but audio drops after exactly 30 seconds.

**Investigation:**
1. SIP trace shows: INVITE → 200 OK → ACK → (30 seconds) → BYE from Telnyx
2. The BYE reason header says "RTP timeout"
3. Check the RTP stream — packets from the customer's PBX have a source IP that's different from what was in the SDP (NAT issue)
4. The B2BUA received the 200 OK, started waiting for RTP from the customer, but RTP never arrived at the expected address
5. The RTP timeout fired after 30 seconds, tearing down the call

**Root cause:** Customer's PBX is behind NAT. The SDP contains the private IP (192.168.x.x) but RTP arrives from the public NAT IP. If the B2BUA doesn't support RTP latching (learning the real source from incoming packets), it never processes the media.

**Fix:** Enable media latching / comedia on the trunk, or fix the customer's NAT configuration (STUN, or configure the PBX with its external IP).

---

**Key Takeaways:**
1. The basic call flow is: INVITE → 100 → 180/183 → 200 OK → ACK → RTP → BYE → 200 OK
2. The INVITE/200/ACK three-way handshake ensures both sides agree the call is established
3. 183 Session Progress with SDP enables early media (network-provided ringback tones)
4. Telnyx's B2BUA creates two independent dialogs — different Call-IDs, independent codec negotiation
5. Post-Dial Delay (INVITE to first ring indication) is a critical quality metric — target < 5 seconds
6. Media starts flowing after 200 OK/ACK — audio issues in the first seconds often indicate SDP/NAT problems
7. RTP timeout (no media received) is a common cause of calls dropping shortly after answer

**Next: Lesson 45 — Call Failures — CANCEL, Timeouts, and Error Responses**
