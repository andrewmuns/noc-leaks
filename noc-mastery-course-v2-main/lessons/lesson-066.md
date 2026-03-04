# Lesson 66: SMS and MMS Messaging — How Carrier Messaging Works

**Module 1 | Section 1.17 — Messaging**
**⏱ ~8min read | Prerequisites: Lesson 40 (SS7 Fundamentals)**

---

## Introduction

Before diving into Telnyx messaging products, you need to understand how carrier messaging actually works at the protocol level. SMS and MMS are deceptively complex — they traverse SS7 signaling networks, SMPP aggregator links, and multi-stage MMS relay architectures. As a NOC engineer, understanding these layers lets you pinpoint exactly where a message failed.

---

## SMS over SS7 — The MAP Layer

Short Message Service was bolted onto GSM's signaling infrastructure. SMS messages travel over **SS7's MAP (Mobile Application Part)** protocol, not the voice bearer path.

### The SMS Delivery Flow

```
Mobile Device (MO-SMS)
    → BSC/RNC → MSC
        → SMSC (Short Message Service Center)
            → MAP: SRI-for-SM (query HLR for routing)
                → HLR returns MSC address
            → MAP: MT-Forward-SM (deliver to terminating MSC)
        → Terminating MSC → BSC → Mobile Device
```

Key components:

| Component | Role |
|-----------|------|
| **SMSC** | Store-and-forward hub; queues messages if handset unreachable |
| **HLR** | Home Location Register; knows which MSC currently serves the subscriber |
| **MAP SRI-for-SM** | Send Routing Info for Short Message — queries HLR |
| **MAP MT-Forward-SM** | Mobile Terminated Forward — delivers the message payload |

### MAP Message Structure

```
MAP MT-Forward-SM {
  SM-RP-DA: IMSI (destination subscriber)
  SM-RP-OA: SMSC address
  SM-RP-UI: {
    TP-MTI: SMS-DELIVER
    TP-OA: +15551234567 (originating address)
    TP-PID: 0x00
    TP-DCS: 0x00 (GSM-7 encoding)
    TP-SCTS: 2026-02-23T10:30:00Z
    TP-UDL: 140 (user data length in septets)
    TP-UD: <message payload>
  }
}
```

🔧 **NOC Tip:** When debugging SMS failures on carrier interconnects, check if the HLR lookup (SRI-for-SM) is returning a valid MSC address. A "subscriber absent" MAP error means the handset isn't registered — not a Telnyx issue.

---

## SMPP — The Aggregator Protocol

Most modern SMS routing between carriers and platforms like Telnyx uses **SMPP (Short Message Peer-to-Peer)** protocol, not raw SS7.

### SMPP Connection Lifecycle

```
Telnyx SMPP Client                    Carrier SMSC
       |                                    |
       |--- bind_transceiver -------------->|
       |<-- bind_transceiver_resp (0x00) ---|
       |                                    |
       |--- submit_sm (outbound SMS) ------>|
       |<-- submit_sm_resp (message_id) ----|
       |                                    |
       |<-- deliver_sm (DLR or MO-SMS) -----|
       |--- deliver_sm_resp --------------->|
       |                                    |
       |--- unbind ------------------------>|
       |<-- unbind_resp --------------------|
```

### Key SMPP PDUs

- **bind_transmitter / bind_receiver / bind_transceiver** — Session establishment
- **submit_sm** — Send a message (MO direction from platform to carrier)
- **deliver_sm** — Receive a message or delivery receipt
- **enquire_link** — Keepalive heartbeat (typically every 30-60s)

### SMPP Error Codes NOC Engineers See

```
0x00000000  ESME_ROK           — Success
0x00000001  ESME_RINVMSGLEN    — Invalid message length
0x00000045  ESME_RSUBMITFAIL   — Submit failed
0x00000058  ESME_RTHROTTLED    — Throughput exceeded
0x00000400  ESME_RDELIVERYFAILURE — Delivery failed
```

🔧 **NOC Tip:** If you see a spike in `ESME_RTHROTTLED` (0x58) errors, the carrier is rate-limiting your SMPP bind. Check if a specific customer is sending a burst. Telnyx SMPP connections have per-bind TPS limits — monitor `smpp.submit_sm.throttled` metrics.

---

## Character Encoding — GSM-7 vs UCS-2

SMS message capacity depends on encoding:

| Encoding | Characters per segment | Used for |
|----------|----------------------|----------|
| **GSM-7** | 160 chars | Latin alphabet, basic symbols |
| **UCS-2** | 70 chars | Unicode (emoji, CJK, Arabic, etc.) |

### The GSM-7 Default Alphabet

GSM-7 uses 7-bit encoding. Most ASCII characters map directly, but some don't exist in GSM-7:

```
Missing from GSM-7 (triggers UCS-2 fallback):
  [ ] { } | ^ ~ \ €  ← These use GSM-7 extension table (2 septets each)
  Any emoji             ← Forces UCS-2
  Chinese/Arabic/Hindi  ← Forces UCS-2
```

🔧 **NOC Tip:** A customer complains "my 80-character message was billed as 2 segments." Check for emoji or special characters — a single emoji forces UCS-2, dropping capacity to 70 chars. This is a common NOC support escalation.

---

## Long Message Concatenation (UDH)

Messages exceeding one segment use **User Data Header (UDH)** for concatenation:

```
UDH for concatenated SMS:
  UDHL: 0x05 (header length)
  IEI:  0x00 (concatenation IE)
  IEDL: 0x03 (IE data length)
  Ref:  0xA3 (reference number — links segments)
  Total: 0x03 (total segments)
  Seq:  0x01 (this segment number)
```

With UDH overhead:
- GSM-7: **153** chars per segment (not 160)
- UCS-2: **67** chars per segment (not 70)

The receiving handset reassembles segments using the reference number. If one segment fails delivery, the handset shows a partial or garbled message.

🔧 **NOC Tip:** If users report "missing parts of long messages," check DLR status per segment. One segment failing (e.g., carrier timeout) breaks concatenation. Look for mismatched reference numbers in logs.

---

## MMS Architecture — MM1 through MM4

MMS (Multimedia Messaging Service) uses a completely different architecture from SMS:

```
                    MM1                MM3
Mobile Device ←----------→ MMSC ←----------→ HLR/HSS
                            |
                    MM4     |     MM7
Carrier B MMSC ←-----------→←----------→ Value-Added Service
                            |
                    MM1     |
                  ←----------→ Recipient Device
```

### MMS Interface Reference Points

| Interface | Between | Protocol |
|-----------|---------|----------|
| **MM1** | Device ↔ MMSC | HTTP/WAP |
| **MM3** | MMSC ↔ HLR | MAP/Diameter |
| **MM4** | MMSC ↔ MMSC (inter-carrier) | SMTP-based |
| **MM7** | MMSC ↔ Application (like Telnyx) | SOAP/HTTP |

### MMS Send Flow

```
1. Device sends MM1 POST with MIME multipart (image + text)
2. Originating MMSC stores content, generates message-id
3. MMSC queries HLR for recipient's serving MMSC
4. MM4 forward to terminating MMSC (SMTP envelope)
5. Terminating MMSC sends MM1 notification to recipient
6. Recipient device fetches content via MM1 GET
7. Delivery report sent back via MM4
```

🔧 **NOC Tip:** MMS failures between carriers are almost always on the MM4 interface. If a customer reports "MMS works to AT&T but not Verizon," check the MM4 peering status with that specific carrier. Telnyx has direct MM4 connections with major US carriers.

---

## Delivery Receipts (DLR) and Status Codes

Delivery receipts confirm whether the carrier accepted and delivered the message.

### Common DLR Status Values

```
DELIVRD   — Message delivered to handset
ACCEPTD   — Accepted by carrier (not yet delivered)
UNDELIV   — Undeliverable (invalid number, phone off for days)
EXPIRED   — TTL expired before delivery
REJECTD   — Carrier rejected (spam filter, blocklist)
UNKNOWN   — Carrier doesn't support DLR for this route
```

### DLR Error Code Ranges

```
000-099   — No error / delivered
100-199   — Temporary carrier error (retry possible)
200-299   — Permanent carrier error (don't retry)
300-399   — Content/encoding error
400-499   — Handset error (incompatible, memory full)
500-599   — Network error (SS7 failure, SMSC down)
```

🔧 **NOC Tip:** A high rate of `UNDELIV` to a specific carrier? Check if their SMSC is having issues — look at the Telnyx carrier status page and recent incident reports. If `REJECTD` is spiking, the carrier may have flagged the sending number for spam.

---

## Message Routing at Telnyx

Telnyx routes messages through a **Least Cost Routing (LCR)** engine with quality weighting:

```
Inbound message → Number Lookup (carrier/type) 
  → Route Selection:
      1. Direct carrier route (preferred)
      2. Tier-1 aggregator route
      3. Tier-2 aggregator fallback
  → SMPP submit to selected route
  → DLR monitoring and webhook delivery
```

Routing decisions factor in:
- **Destination carrier** (direct routes preferred)
- **Number type** (mobile, landline, toll-free)
- **Country** (international routes have different aggregator chains)
- **Historical delivery rate** per route
- **Cost** (weighted against quality)

---

## Real-World NOC Scenario

**Scenario:** Customer reports 30% SMS delivery failure to T-Mobile numbers in the US.

**Investigation steps:**

1. Pull DLR stats filtered by destination carrier = T-Mobile
2. Check DLR error codes — are they `REJECTD` (spam) or `UNDELIV` (routing)?
3. If `REJECTD`: Check if T-Mobile's content filter is blocking. Look at message content for spam triggers.
4. If `UNDELIV`: Check SMPP bind health to the T-Mobile direct route. Is `enquire_link` succeeding?
5. Check if traffic shifted to a backup aggregator route (lower quality)
6. Verify the sending numbers are properly provisioned for A2P messaging

```bash
# Check SMPP bind status for T-Mobile route
telnyx-cli smpp binds --carrier tmobile --status

# Pull DLR stats for last hour
telnyx-cli messaging dlr-stats --carrier tmobile --period 1h
```

---

## Key Takeaways

1. **SMS travels over SS7 MAP** — SRI-for-SM queries the HLR, MT-Forward-SM delivers the payload to the serving MSC
2. **SMPP is the standard interconnect** between Telnyx and carriers — monitor bind health, throttle errors, and enquire_link keepalives
3. **GSM-7 gives 160 chars; UCS-2 gives 70** — a single emoji forces the entire message to UCS-2
4. **Concatenated messages use UDH** — each segment is independently routed, so partial delivery is possible
5. **MMS uses HTTP-based MM1-MM7 interfaces** — inter-carrier MMS goes over MM4 (SMTP-based)
6. **DLR codes tell the story** — learn to read DELIVRD/UNDELIV/REJECTD and the numeric error ranges
7. **Message routing is quality-weighted LCR** — direct carrier routes are preferred over aggregator fallbacks

---

**Next: Lesson 182 — Telnyx Messaging API: SMS, MMS, and Number Management**
