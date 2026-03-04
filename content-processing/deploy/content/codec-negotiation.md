---
content_type: truncated
description: Learn about codec negotiation and media interworking
difficulty: Advanced
duration: 6 minutes
full_content_available: true
lesson: '51'
module: 'Module 1: Foundations'
objectives:
- "Understand Codec preference order in SDP matters \u2014 list your most preferred\
  \ codec first in the `m=` line"
- "Understand 488 Not Acceptable Here means no common codec \u2014 compare offer vs.\
  \ destination capabilities"
- "Understand Transcoding is CPU-intensive, adds latency, and degrades quality \u2014\
  \ avoid it when possible by including G.711 in codec lists"
- "Understand The B2BUA negotiates codecs independently on each leg \u2014 enabling\
  \ interworking between incompatible endpoints"
- Understand DTMF method mismatch (RFC 2833 vs. in-band vs. SIP INFO) is a frequent cause of "DTMF not working"slug: codec-negotiation
title: Codec Negotiation and Media Interworking
word_limit: 300
---

## The Negotiation Problem

Two endpoints need to agree on a common language before they can exchange audio. If Alice's phone speaks G.711 and G.729, and Bob's phone speaks G.711 and Opus, they need to converge on G.711. This convergence happens through SDP offer/answer negotiation (Lesson 48). But what happens when there's no common codec? Or when a B2BUA sits in the middle?

---

## Codec Preference and Selection

### The Offer: Preference Order Matters

The payload type numbers in the `m=` line are listed in **preference order**:

```
m=audio 10000 RTP/AVP 8 0 18 101
```

This says: "I prefer G.711 A-law (8), then G.711 μ-law (0), then G.729 (18), and I support DTMF events (101)."

The first codec listed is the offerer's most preferred. A well-behaved answerer should respect this preference when possible, but the spec allows the answerer to select *any* offered codec.

### The Answer: Selection

The answerer responds with the codecs it supports from the offer:

```
m=audio 20000 RTP/AVP 8 101
```

"I selected G.711 A-law and DTMF events." The first codec in the answer is what will actually be used for media.

### What If There's No Common Codec?

If the answerer supports none of the offered codecs, it responds with **488 Not Acceptable Here**:

```
SIP/2.0 488 Not Acceptable Here
Warning: 304 "Media type not available"
```

This is a definitive rejection — the call cannot proceed without codec compatibility.

> **💡 NOC Tip:** en you see 488 responses, compare the codec list in the INVITE's SDP offer against the far end's supported codecs. Common mismatches:
- Customer offers only G.729, carrier requires G.711
- Customer offers only Opus, PSTN gateway only supports G.711/G.729
- DTMF telephone-event is missing from the offer but required by the far end
slug: "codec-negotiation"
---

## Transcoding: When the B2BUA Bridges Codecs

---

##

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*