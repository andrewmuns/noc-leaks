---
title: "SIP Methods — INVITE, REGISTER, BYE, and Beyond"
description: "Learn about sip methods — invite, register, bye, and beyond"
module: "Module 1: Foundations"
lesson: "40"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand Six core methods (INVITE, ACK, BYE, CANCEL, REGISTER, OPTIONS) form the foundation — extension methods add features
  - Understand INVITE is unique: it uses a three-way handshake (INVITE → 200 → ACK) and can modify sessions via re-INVITE
  - Understand CANCEL can only abort pending requests — once a 200 OK is sent, you must ACK then BYE
  - Understand OPTIONS is used as a SIP-level health check — firewalls that block it cause false "trunk down" alarms
  - Understand REFER enables call transfer with NOTIFY-based progress reporting — buggy NOTIFY handling causes transfer failures
slug: "sip-methods"
---


SIP methods are the verbs of the protocol — they tell the receiving entity what you want it to do. Mastering these methods is like learning the vocabulary of a language. You need to know what each one means, when it's used, and what to expect in response.

## Core Methods (RFC 3261)

These six methods are defined in the base SIP specification. Every SIP implementation must support them.

### INVITE — Initiate a Session

The most important SIP method. INVITE establishes a new session (call) or modifies an existing one (re-INVITE).

```
INVITE sip:+15551234567@sip.telnyx.com SIP/2.0
Via: SIP/2.0/UDP 10.0.1.50:5060;branch=z9hG4bK776
From: <sip:+15559876543@customer.com>;tag=1928301774
To: <sip:+15551234567@sip.telnyx.com>
Call-ID: a84b4c76e66710@10.0.1.50
CSeq: 314159 INVITE
Contact: <sip:+15559876543@10.0.1.50:5060>
Content-Type: application/sdp

[SDP body with media offer]
```

**Key characteristics:**
- Contains an SDP body with the media offer (codecs, IP, port)
- Creates an INVITE transaction that uses a **three-way handshake**: INVITE → 200 OK → ACK
- The only method where the final response is acknowledged with ACK
- Can create early dialogs via provisional responses with To-tags (183 Session Progress)

A re-INVITE is the same method sent within an existing dialog to modify session parameters (hold, codec change, media addition).

### ACK — Acknowledge Final Response to INVITE

ACK confirms receipt of the final response to an INVITE. This exists because INVITE transactions may take a long time (the phone rings for 30 seconds), and reliability of the final response must be ensured.

**For 2xx responses (success):** ACK is sent by the UAC directly to the UAS. It's an end-to-end acknowledgment.
**For non-2xx responses (failure):** ACK is sent hop-by-hop through the same proxies. It's part of the transaction, not the dialog.

If ACK is never sent after a 200 OK, the UAS retransmits the 200 OK repeatedly and eventually tears down the call — a common source of "ghost calls" in poorly implemented systems.

> **💡 NOC Tip:**  you see repeated 200 OK retransmissions in SIP traces, the ACK isn't getting through. Check for firewall issues, NAT problems, or routing errors that prevent the ACK from reaching the UAS.

### BYE — Terminate a Session

Sent by either party to end an established call. BYE terminates the dialog — both sides stop sending media and release resources.

```
BYE sip:+15559876543@10.0.1.50:5060 SIP/2.0
```

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios
- ✅ Practice quizzes and assessments

[**🚀 Unlock Full Course Access**](https://teleponymastery.com/enroll)

---

*Preview shows approximately 25% of the full lesson content.*