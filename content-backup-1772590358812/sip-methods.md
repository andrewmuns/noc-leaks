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

BYE can only be sent after the dialog is confirmed (200 OK received and ACK sent). Before that, use CANCEL instead.

**Missing BYE = ghost call.** If a call ends on one side (caller hangs up) but BYE never reaches the other side (network failure, firewall drops it), the other side thinks the call is still active. It keeps sending RTP to nowhere and the CDR keeps accumulating duration.

### CANCEL — Abort a Pending Request

CANCEL tells the UAS to stop processing a pending INVITE. It can only be sent before a final response is received — once you get a 200 OK, it's too late to CANCEL (you must ACK then BYE).

**The CANCEL race condition:** CANCEL and 200 OK can cross in transit. If the callee answers while the CANCEL is in flight:
1. CANCEL arrives after 200 OK was sent → UAS responds 200 to CANCEL but the INVITE is already answered
2. Caller receives 200 OK to INVITE → must send ACK, then immediately BYE

This race condition is normal and expected. SIP implementations must handle it correctly.

### REGISTER — Bind an Address

As discussed in Lesson 37, REGISTER creates a binding between an Address of Record (AOR) and a Contact address. It doesn't establish a session — it's purely administrative.

```
REGISTER sip:sip.telnyx.com SIP/2.0
Contact: <sip:user@192.168.1.100:5060>;expires=3600
```

### OPTIONS — Query Capabilities

A lightweight "ping" for SIP. OPTIONS asks the remote UA what methods and codecs it supports. The response includes Allow (supported methods), Accept (content types), and optionally an SDP body with media capabilities.

**Practical use:** Telnyx and many SIP providers use OPTIONS as a keep-alive mechanism — periodic OPTIONS sent to check if an endpoint is still reachable. If OPTIONS gets no response, the endpoint is marked as down and traffic is routed elsewhere.

> **💡 NOC Tip:**  you see a trunk marked as "down" despite the customer claiming their system is running, check if OPTIONS packets are getting through. Firewalls that allow INVITE but block OPTIONS (because they don't recognize the method) will cause the health check to fail while calls still work.

## Extension Methods

These methods were added in subsequent RFCs to support features beyond basic call control.

### REFER (RFC 3515) — Transfer a Call

REFER asks the recipient to initiate a new request to a third party. Used for call transfer.

```
REFER sip:user@10.0.1.50 SIP/2.0
Refer-To: <sip:+15553334444@sip.telnyx.com>
```

This tells the recipient: "Please send an INVITE to +15553334444." The recipient sends back NOTIFY messages reporting the progress of the new INVITE.

### SUBSCRIBE / NOTIFY (RFC 6665) — Event Framework

SUBSCRIBE expresses interest in receiving updates about a state or event. NOTIFY delivers those updates.

**Use cases:**
- **Presence:** Subscribe to a user's online/offline status
- **Message Waiting Indicator (MWI):** Phone subscribes to voicemail events, gets NOTIFY when a new message arrives
- **REFER progress:** After REFER, the referrer subscribes to transfer progress and gets NOTIFY updates
- **Dialog state:** Monitor whether a user is on a call (busy lamp field)

### INFO (RFC 6086) — Mid-Dialog Information

Carries application-level information within an existing dialog without changing the session. Most commonly used for:
- DTMF relay (as discussed in Lesson 31)
- Call progress information
- Proprietary extensions

### UPDATE (RFC 3311) — Modify Session Before Establishment

Like re-INVITE, but can be sent before the initial INVITE transaction completes. Useful for changing codec or media parameters during early dialog (between 183 and 200).

### MESSAGE (RFC 3428) — Instant Messaging

Sends a text message via SIP. Creates no dialog — it's a single request/response, like HTTP GET.

### PRACK (RFC 3262) — Reliable Provisional Responses

Makes provisional responses (1xx) reliable by requiring acknowledgment. Without PRACK, provisional responses like 180 Ringing are sent unreliably over UDP — they might get lost. With PRACK, each provisional response is acknowledged, ensuring the caller knows the phone is ringing.

## Request Structure

Every SIP request follows this format:

```
Method Request-URI SIP/2.0     ← Request Line
Via: ...                        ← Headers
From: ...
To: ...
Call-ID: ...
CSeq: ...
Content-Type: ...
Content-Length: ...
                                ← Empty line
[Body - usually SDP]            ← Message Body
```

## Response Structure

```
SIP/2.0 200 OK                 ← Status Line
Via: ...                        ← Headers (echoed from request)
From: ...
To: ...;tag=responding-tag
Call-ID: ...
CSeq: ...
Contact: ...
Content-Type: ...

[Body - usually SDP for INVITE responses]
```

## Real Troubleshooting Scenario: Call Transfer Fails Silently

**Symptom:** Customer tries to transfer calls using their PBX, but the transfer fails — the call just drops.

**Investigation:**
1. SIP trace shows REFER being sent
2. Telnyx responds 202 Accepted
3. Telnyx sends INVITE to the transfer target (new INVITE on B-leg)
4. Transfer target responds 486 Busy
5. NOTIFY with 486 is sent back to the customer
6. Customer PBX doesn't handle the NOTIFY correctly — drops the original call

**Root cause:** The customer's PBX doesn't properly process failed-transfer NOTIFY messages. It interprets any NOTIFY as "transfer succeeded" and disconnects the original call.

**Resolution:** PBX firmware update to properly handle REFER NOTIFY status codes. In the interim, customer can use attended transfer (verify the target answers before completing) instead of blind transfer.

## Method Usage in Telnyx NOC Context

| Method | When You'll See It | What to Check |
|--------|--------------------|---------------|
| INVITE | Every call setup | SDP content, authentication, routing |
| ACK | After 200 OK | Missing ACK = ghost calls |
| BYE | Call teardown | Missing BYE = stuck calls |
| CANCEL | Caller hangs up before answer | Race with 200 OK |
| REGISTER | Endpoint registration | Credentials, NAT, expiry |
| OPTIONS | Health checks | Firewall blocking, timeout |
| REFER | Call transfer | NOTIFY handling, target reachability |
| INFO | DTMF via SIP INFO | Latency, method mismatch |

---

**Key Takeaways:**
1. Six core methods (INVITE, ACK, BYE, CANCEL, REGISTER, OPTIONS) form the foundation — extension methods add features
2. INVITE is unique: it uses a three-way handshake (INVITE → 200 → ACK) and can modify sessions via re-INVITE
3. CANCEL can only abort pending requests — once a 200 OK is sent, you must ACK then BYE
4. OPTIONS is used as a SIP-level health check — firewalls that block it cause false "trunk down" alarms
5. REFER enables call transfer with NOTIFY-based progress reporting — buggy NOTIFY handling causes transfer failures
6. Missing ACK causes 200 OK retransmission storms; missing BYE causes ghost calls — both are common NOC issues

**Next: Lesson 39 — SIP Headers: The Essential Ones and What They Tell You**
