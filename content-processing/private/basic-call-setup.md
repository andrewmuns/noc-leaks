---
content_type: complete
description: "Learn about basic call setup \u2014 invite to 200 ok to bye"
difficulty: Advanced
duration: 8 minutes
lesson: '46'
module: 'Module 1: Foundations'
objectives:
- Understand The basic call flow is: "INVITE \u2192 100 \u2192 180/183 \u2192 200\
    \ OK \u2192 ACK \u2192 RTP \u2192 BYE \u2192 200 OK"
- Understand The INVITE/200/ACK three-way handshake ensures both sides agree the call
  is established
- Understand 183 Session Progress with SDP enables early media (network-provided ringback
  tones)
- "Understand Telnyx's B2BUA creates two independent dialogs \u2014 different Call-IDs,\
  \ independent codec negotiation"
- "Understand Post-Dial Delay (INVITE to first ring indication) is a critical quality\
  \ metric \u2014 target < 5 seconds"
public_word_count: 251
slug: basic-call-setup
title: "Basic Call Setup \u2014 INVITE to 200 OK to BYE"
total_word_count: 335
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