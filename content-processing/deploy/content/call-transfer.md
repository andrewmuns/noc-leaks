---
content_type: truncated
description: "Learn about call transfer \u2014 refer and replaces"
difficulty: Advanced
duration: 7 minutes
full_content_available: true
lesson: '48'
module: 'Module 1: Foundations'
objectives:
- "Understand Blind transfer uses REFER with a simple Refer-To target \u2014 the B2BUA\
  \ calls the target and bridges to the existing party"
- "Understand Attended transfer uses REFER with a Replaces parameter \u2014 connecting\
  \ an existing consultation call to the held party"
- "Understand NOTIFY messages report transfer progress using SIP fragments \u2014\
  \ check these to determine why transfers fail"
- "Understand Transfer is the most common SIP interoperability problem \u2014 vendor\
  \ implementations vary significantly"
- "Understand In B2BUA architectures, the B2BUA handles the transfer internally \u2014\
  \ media re-bridging is critical"
slug: call-transfer
title: "Call Transfer \u2014 REFER and Replaces"
word_limit: 300
---

## Why Transfers Are Complex

Call transfer seems simple: move a call from one person to another. But in SIP's distributed architecture, it's surprisingly complex. There's no central switch that can just "reconnect the wires." Instead, transfer involves coordinating multiple independent SIP dialogs, each with their own state, and getting them to stitch together seamlessly.

Transfer is also the SIP feature most likely to break across different vendor implementations. The spec is clear, but edge cases abound.

---

## Blind Transfer (Unattended Transfer)

Alice is talking to Bob. Alice wants to transfer Bob to Carol without talking to Carol first.

### The REFER Method

```
Alice                    Telnyx B2BUA                    Bob
  |<======== RTP ==========>|<======== RTP ============>|
  |                          |                            |
  |------- REFER ----------->|                            |
  | Refer-To: carol@...      |                            |
  |<------ 202 Accepted -----|                            |
  |                          |                            |
  |                          |------- INVITE ------------>| Carol
  |                          |<------ 200 OK -------------|
  |                          |------- ACK --------------->|
  |                          |                            |
  |<------ NOTIFY -----------|                            |
  | (sipfrag: SIP/2.0 200)   |                            |
  |------- 200 OK (NOTIFY)->|                            |
  |                          |                            |
  |------- BYE ------------->|  (Alice disconnects)       |
  |<------ 200 OK -----------|                            |
```

**Step by step:**
1. Alice sends **REFER** within the existing dialog to Telnyx, with `Refer-To: <sip:carol@example.com>` header
2. Telnyx responds **202 Accepted** — "I'll try to do what you asked"
3. Telnyx creates a **new INVITE** to Carol (this is a new call leg)
4. Telnyx bridges Bob's existing media to Carol's new media
5. Telnyx sends **NOTIFY** to Alice reporting the outcome (using SIP fragment — the response code from the INVITE to Carol)
6. Alice hangs up (BYE)

The **NOTIFY** messages use the "refer" event package — they carry SIP fragments that tell Alice whether the transfer succeeded or failed. The `sipfrag` body might contain `SIP/2.0 180 Ringing` (transfer in progress) or `SIP/2.0 200 OK` (transfer succeeded).

### B2BUA Transfer Handling


---

## 🔒 Full Course Content Available

This is a

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*