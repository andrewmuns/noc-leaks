---
content_type: complete
description: "Learn about sdp structure \u2014 offer/answer model"
difficulty: Advanced
duration: 8 minutes
lesson: '50'
module: 'Module 1: Foundations'
objectives:
- "Understand SDP's `c=` line (connection address) and `m=` line (media port) define\
  \ where to send RTP \u2014 these are the first things to check for audio issues"
- Understand The offer/answer model: "offerer proposes, answerer selects a subset\
    \ \u2014 the answer must only include codecs from the offer"
- "Understand Private IPs in the `c=` line indicate NAT \u2014 this is the"
- Understand Payload types 0-95 are static (well-known), 96-127 are dynamic (must
  be declared with `a=rtpmap`)
- "Understand `a=sendrecv/sendonly/recvonly/inactive` controls media direction \u2014\
  \ essential for hold/resume"
public_word_count: 264
slug: sdp-basics
title: "SDP Structure \u2014 Offer/Answer Model"
total_word_count: 329
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