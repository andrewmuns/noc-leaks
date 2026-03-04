# Lesson 47: Call Failures — CANCEL, Timeouts, and Error Responses
**Module 1 | Section 1.11 — SIP Call Flows**
**⏱ ~7 min read | Prerequisites: Lesson 44**

---

## Calls Fail More Often Than They Succeed

In a typical telecom environment, 30-40% of call attempts don't result in a completed conversation. That's not a bug — it's reality. People don't answer, lines are busy, numbers are wrong, networks hiccup. Understanding *how* calls fail in SIP is just as important as understanding how they succeed.

---

## CANCEL: Aborting a Pending Call

CANCEL is how a caller says "never mind" after sending an INVITE but before receiving a final response. The most common scenario: the caller hangs up while the phone is ringing.

### The CANCEL Flow

```
Alice                    Telnyx B2BUA                    Bob
  |------- INVITE ---------->|------- INVITE ------------>|
  |<------ 100 Trying -------|<------ 180 Ringing --------|
  |<------ 180 Ringing ------|                            |
  |                          |                            |
  |  (Alice hangs up)        |                            |
  |------- CANCEL ---------->|------- CANCEL ------------>|
  |<------ 200 OK (CANCEL) --|<------ 200 OK (CANCEL) ---|
  |                          |<------ 487 Terminated -----|
  |                          |------- ACK (487) --------->|
  |<------ 487 Terminated ---|                            |
  |------- ACK (487) ------->|                            |
```

**Key points:**
- CANCEL has the **same Call-ID, From-tag, and To-tag** as the INVITE — it targets a specific transaction
- The 200 OK to CANCEL just means "I received your CANCEL" — it does *not* mean the call was successfully cancelled
- The actual result is the **487 Request Terminated** response to the original INVITE
- You must still ACK the 487 (as with all final responses to INVITE)

### The Critical Rule: CANCEL Timing

CANCEL can only be sent *after* a provisional response is received and *before* a final response arrives. Why?

- **Before any response:** The INVITE might not have arrived yet. Sending CANCEL to something that doesn't exist is meaningless. The UAC should wait for at least a 100 Trying before sending CANCEL.
- **After final response:** It's too late — the transaction is complete. If a 200 OK arrives, the call is answered. You must send ACK then BYE to end it (you can't un-answer a call with CANCEL).

🔧 **NOC Tip:** If you see high 487 rates on a trunk, don't panic — 487 is a *normal* response. It means callers are hanging up during ringing. Investigate only if the rate is unusually high (e.g., >50% of call attempts), which might indicate long Post-Dial Delay causing callers to give up.

---

## The Race Condition: CANCEL Crosses with 200 OK

This is one of the trickiest scenarios in SIP:

```
Alice                    Telnyx B2BUA                    Bob
  |------- INVITE ---------->|------- INVITE ------------>|
  |<------ 180 Ringing ------|<------ 180 Ringing --------|
  |                          |                            |
  |------- CANCEL ---------->|      (Bob answers)         |
  |                          |<------ 200 OK (INVITE) ----|
```

Alice cancels, but Bob has *already answered*. The CANCEL and 200 OK cross in flight. What happens?

1. Telnyx receives CANCEL from Alice — tries to cancel Leg B
2. But Leg B already received 200 OK from Bob — it's too late to CANCEL
3. Telnyx must **ACK** Bob's 200 OK (to complete the INVITE transaction)
4. Then immediately send **BYE** to Bob (to tear down the now-unwanted call)
5. Telnyx sends 487 to Alice (or handles internally depending on implementation)

This race condition is a common source of brief "phantom calls" — calls that appear in CDRs with 0-1 second duration. They're technically valid calls that were established then immediately torn down.

---

## Timeouts: When Nobody Responds

### Timer B — INVITE Transaction Timeout (32 seconds)

If no response at all arrives to an INVITE within 32 seconds, the client transaction generates a **408 Request Timeout** locally. Common causes:

- Destination is completely unreachable (firewall blocking, wrong IP)
- DNS resolved to a non-existent host
- The far-end server crashed

### Timer F — Non-INVITE Transaction Timeout (32 seconds)

Same concept for non-INVITE transactions (BYE, REGISTER, etc.). If the BYE gets no response, Timer F fires.

### What NOC Engineers See

Timeouts appear as 408 responses in SIP traces, but remember: **408 is usually generated locally**, not sent by the remote party. If you see 408, it means the request went into a black hole.

```
Alice → INVITE → Telnyx → INVITE → [nothing]
                          (32 seconds pass)
                 Telnyx generates 408 internally
Alice ← 408 ← Telnyx
```

🔧 **NOC Tip:** When investigating 408 timeouts, don't look for a response from the far end — there isn't one. Instead, investigate why the far end didn't respond:
1. Is the destination IP reachable? (`ping`, `traceroute`)
2. Is the SIP port open? (`nc -zv host 5060`)
3. Did DNS resolve correctly? (`dig SRV _sip._udp.carrier.com`)
4. Is there a firewall rule blocking SIP?

---

## Error Responses: The Call Was Rejected

When the far end *does* respond but rejects the call:

### 4xx — The Request Is Wrong

- **403 Forbidden:** "I know who you are but you're not allowed." Often: blocked destination, disabled account, or policy violation.
- **404 Not Found:** "This number doesn't exist in my system."
- **480 Temporarily Unavailable:** "The user exists but isn't reachable right now."
- **486 Busy Here:** "The line is busy."
- **488 Not Acceptable Here:** "I can't handle your SDP offer." (Codec mismatch — see Lesson 49)

### 5xx — The Server Is Broken

- **500 Internal Server Error:** Generic server failure. Check carrier/platform logs.
- **503 Service Unavailable:** "I'm overloaded or in maintenance." This triggers failover routing at Telnyx — the routing engine tries the next available carrier.

### Failover Behavior

Telnyx's routing engine doesn't give up after one failure. When a carrier returns certain error codes (408, 500, 502, 503, 504), the call is automatically retried on the next carrier in the routing table. This is transparent to the customer — they just experience slightly higher Post-Dial Delay.

Codes that do NOT trigger failover (because they're definitive):
- 403 (Forbidden — retrying won't help)
- 404 (Number doesn't exist — it won't exist on another carrier either)
- 486 (Busy — the callee is busy regardless of carrier)
- 487 (Cancelled — the caller chose to hang up)

---

## Diagnosing Call Failures: A Framework

When investigating why calls fail:

1. **Get the response code** — this is your starting point
2. **Determine who generated it** — the far-end carrier? Telnyx? The customer's PBX?
3. **Check the context:**
   - Single call failure or pattern?
   - Specific destination or all destinations?
   - Specific time of day or constant?
4. **Map to common causes** (see Lesson 40 reference table)
5. **Gather evidence:** SIP traces, PCAP, Grafana metrics, carrier status

### Real-World Scenario

**Problem:** A customer reports 30% of outbound calls to mobile numbers failing with "fast busy" tone.

**Investigation:**
1. Grafana shows a spike in 404 responses, but only for one specific carrier route
2. SIP traces show the 404 comes from the downstream carrier, not Telnyx
3. The affected numbers are all recently ported mobile numbers
4. The carrier's LNP database hasn't updated — it's routing to the old carrier, which returns 404

**Resolution:** Report to the carrier that their LNP data is stale. As a temporary fix, adjust routing to prefer a different carrier for the affected number range. Monitor until the carrier confirms their LNP database is updated.

---

**Key Takeaways:**
1. CANCEL aborts pending INVITEs — it can only be sent after provisional and before final response
2. 487 Request Terminated is the normal result of a CANCEL — high 487 rates indicate user abandonment, not technical issues
3. The CANCEL/200 race condition creates brief "phantom calls" — CANCEL crosses with answer, requiring ACK then BYE
4. 408 timeout is generated *locally* when no response arrives — investigate reachability, not the far end's response
5. Telnyx's routing engine automatically fails over on 408, 500, 502, 503, 504 — but not on definitive rejections like 403, 404, 486
6. Always determine *who* generated the error response — Telnyx, the carrier, or the customer's equipment
7. Patterns matter more than individual failures — cluster analysis (by carrier, destination, time) reveals root causes

**Next: Lesson 46 — Call Transfer — REFER and Replaces**
