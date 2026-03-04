---
title: "SDP Structure — Offer/Answer Model"
description: "Learn about sdp structure — offer/answer model"
module: "Module 1: Foundations"
lesson: "50"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand SDP's `c=` line (connection address) and `m=` line (media port) define where to send RTP — these are the first things to check for audio issues
  - Understand The offer/answer model: offerer proposes, answerer selects a subset — the answer must only include codecs from the offer
  - Understand Private IPs in the `c=` line indicate NAT — this is the #1 cause of one-way or no audio
  - Understand Payload types 0-95 are static (well-known), 96-127 are dynamic (must be declared with `a=rtpmap`)
  - Understand `a=sendrecv/sendonly/recvonly/inactive` controls media direction — essential for hold/resume
slug: "sdp-basics"
---

## SDP: The Blueprint for Media

While SIP handles signaling (call setup, teardown, transfer), it says nothing about media. That's SDP's job. The **Session Description Protocol** (RFC 4566) describes *what* media to send, *where* to send it, and *how* to encode it. SDP rides inside SIP messages as the body — the Content-Type is `application/sdp`.

Every audio issue you'll ever debug eventually comes down to what's in the SDP. Learning to read SDP fluently is a core NOC skill.

---

## Anatomy of an SDP

Here's a real-world SDP from an INVITE:

```
v=0
o=- 12345 67890 IN IP4 10.0.1.50
s=-
c=IN IP4 10.0.1.50
t=0 0
m=audio 10000 RTP/AVP 0 8 101
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16
a=sendrecv
a=ptime:20
```

### Line by Line

**`v=0`** — Protocol version. Always 0. Not negotiated, not interesting.

**`o=- 12345 67890 IN IP4 10.0.1.50`** — Origin. The session identifier (`12345`) and version (`67890`) are important for re-INVITEs. When the session version increments, it signals a change. The IP here is informational — it's *not* necessarily where media goes.

**`s=-`** — Session name. Almost always a hyphen (meaningless). Legacy field.

**`c=IN IP4 10.0.1.50`** — **Connection address. This is where media goes.** This is the most operationally critical line in the SDP. If this contains a private IP (10.x, 192.168.x, 172.16-31.x) but the endpoint is behind NAT, you've found the source of one-way audio.

**`t=0 0`** — Timing. Start time 0, stop time 0 = permanent session. Not relevant for calls.

**`m=audio 10000 RTP/AVP 0 8 101`** — **Media line. The second most important line.** Breaks down as:
- `audio` — media type
- `10000` — port number (where to send RTP)
- `RTP/AVP` — transport (RTP Audio Video Profile)
- `0 8 101` — payload type numbers (codec identifiers)

**`a=rtpmap:0 PCMU/8000`** — Maps payload type 0 to G.711 μ-law at 8000 Hz. Payload types 0-95 are static (well-known), but rtpmap still explicitly declares them.

**`a=rtpmap:8 PCMA/8000`** — Payload type 8 = G.711 A-law.

**`a=rtpmap:101 telephone-event/8000`** — Payload type 101 = RFC 2833 DTMF. This is how DTMF digits are sent as RTP events rather than audio tones (see Lesson 31).

**`a=fmtp:101 0-16`** — Format parameters for telephone-event: supports DTMF digits 0-9, *, #, and events A-D.

**`a=sendrecv`** — Direction attribute: both send and receive. Changes during hold (Lesson 47).

**`a=ptime:20`** — Packetization time: 20ms per RTP packet. This affects bandwidth and latency calculations (Lesson 6).

> **💡 NOC Tip:** en debugging audio issues, always check the `c=` line and the port in the `m=` line first. These tell you where media *should* go. If they contain private IPs but the endpoint is behind NAT, you've found your problem.
slug: "sdp-basics"
---

## The Offer/Answer Model (RFC 3264)

SDP alone is just a description. The **offer/answer model** defines how two parties negotiate media parameters:

1. **Offerer** sends an SDP describing what it supports (codecs, ports, addresses)
2. **Answerer** responds with an SDP selecting from the offer

### Where Offer and Answer Live

The most common pattern:
- **INVITE** carries the SDP offer
- **200 OK** carries the SDP answer

But there are variations:
- **INVITE without SDP** (delayed offer): The 200 OK carries the offer, ACK carries the answer
- **183 Session Progress** can carry an SDP answer for early media

### Offer/Answer Rules

The answerer must follow specific rules:
- For each media line in the offer, the answer must have a corresponding media line
- The answer's payload types must be a *subset* of the offer's (you can only select codecs that were offered)
- To reject a media line, set its port to 0 (`m=audio 0 RTP/AVP 0`)
- The answer's `c=` line is the answerer's media address (where *they* receive RTP)

### Example Negotiation

**Offer (INVITE):**
```
m=audio 10000 RTP/AVP 0 8 18 101
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:18 G729/8000
a=rtpmap:101 telephone-event/8000
```

The offerer supports G.711 μ-law, G.711 A-law, G.729, and DTMF events.

**Answer (200 OK):**
```
m=audio 20000 RTP/AVP 8 101
a=rtpmap:8 PCMA/8000
a=rtpmap:101 telephone-event/8000
```

The answerer selected G.711 A-law and DTMF events. G.711 μ-law and G.729 were offered but not selected. Media should be sent to port 20000.

---

## NAT and SDP: The Core Problem

The `c=` connection address and `m=` port tell the remote party where to send RTP. When the endpoint is behind NAT:

```
Private Network          NAT           Public Internet
10.0.1.50:10000  →  203.0.113.5:54321  →  Telnyx
```

The SDP says `c=IN IP4 10.0.1.50` and `m=audio 10000` — a private address that's unreachable from the internet. The remote party tries to send RTP to 10.0.1.50:10000, which goes nowhere.

**Solutions** (revisiting Lesson 27):
- **STUN:** Endpoint discovers its public IP and puts *that* in the SDP
- **SIP ALG:** NAT device rewrites SDP (often badly)
- **B2BUA/SBC:** Telnyx puts its own media address in the SDP and bridges
- **RTP latching:** Telnyx ignores the SDP address and uses the actual source of incoming RTP packets

Telnyx's B2BUA naturally solves this for the carrier side — the SDP toward the carrier always contains Telnyx's own public media address. For the customer side, features like `comedia` (connection-oriented media) enable RTP latching.
slug: "sdp-basics"
---

## Special SDP Scenarios

### Multiple Media Lines
An SDP can contain multiple `m=` lines for different media types:
```
m=audio 10000 RTP/AVP 0
m=video 20000 RTP/AVP 96
m=image 30000 udptl t38
```
Audio, video, and T.38 fax — each with its own port and parameters.

### Port Zero = Rejected
Setting the port to 0 in an answer rejects that media:
```
m=video 0 RTP/AVP 96
```
"I don't support video."

### Hold via SDP
As covered in Lesson 47, hold changes the direction attribute without changing the media description.

---

## Real-World Troubleshooting Scenario

**Problem:** Customer reports "no audio" on calls — both parties hear complete silence.

**Investigation:**
1. SIP trace shows successful INVITE/200/ACK exchange
2. Examining the SDP in the INVITE (offer):
   ```
   c=IN IP4 192.168.1.100
   m=audio 4000 RTP/AVP 18
   a=rtpmap:18 G729/8000
   ```
3. The SDP in the 200 OK (answer):
   ```
   c=IN IP4 10.20.30.40
   m=audio 30000 RTP/AVP 0
   a=rtpmap:0 PCMU/8000
   ```
4. **The offer has only G.729 (payload 18). The answer has only G.711 μ-law (payload 0).**
5. The answer includes a codec that *wasn't in the offer* — this violates RFC 3264

**Root cause:** The answering endpoint's SIP stack has a bug — it's responding with its preferred codec regardless of what was offered, instead of selecting from the offer. The endpoints are "connected" but speaking different codec languages.

**Fix:** Either add G.711 to the offerer's codec list, add G.729 to the answerer's list, or fix the broken SIP stack. In the meantime, Telnyx's B2BUA can bridge by offering both codecs to each leg and transcoding if needed.
slug: "sdp-basics"
---

**Key Takeaways:**
1. SDP's `c=` line (connection address) and `m=` line (media port) define where to send RTP — these are the first things to check for audio issues
2. The offer/answer model: offerer proposes, answerer selects a subset — the answer must only include codecs from the offer
3. Private IPs in the `c=` line indicate NAT — this is the #1 cause of one-way or no audio
4. Payload types 0-95 are static (well-known), 96-127 are dynamic (must be declared with `a=rtpmap`)
5. `a=sendrecv/sendonly/recvonly/inactive` controls media direction — essential for hold/resume
6. Port 0 in an answer rejects that media line
7. `telephone-event` in SDP enables RFC 2833 DTMF — if missing, DTMF may not work

**Next: Lesson 49 — Codec Negotiation and Media Interworking**
