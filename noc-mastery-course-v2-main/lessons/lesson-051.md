# Lesson 51: Codec Negotiation and Media Interworking
**Module 1 | Section 1.12 — SDP and Media Negotiation**
**⏱ ~6 min read | Prerequisites: Lesson 48**

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

🔧 **NOC Tip:** When you see 488 responses, compare the codec list in the INVITE's SDP offer against the far end's supported codecs. Common mismatches:
- Customer offers only G.729, carrier requires G.711
- Customer offers only Opus, PSTN gateway only supports G.711/G.729
- DTMF telephone-event is missing from the offer but required by the far end

---

## Transcoding: When the B2BUA Bridges Codecs

In Telnyx's B2BUA architecture, each call leg negotiates codecs independently. This creates scenarios where the two legs use different codecs:

```
Customer (Leg A)              Telnyx B2BUA              Carrier (Leg B)
G.729 at 8 kbps  ────────►  [Transcode]  ────────►  G.711 at 64 kbps
```

The B2BUA decodes G.729 on Leg A, then encodes to G.711 on Leg B. This is **transcoding**.

### Why Transcoding Happens

1. **Carrier requirements:** Many PSTN carriers require G.711 for interconnection. If the customer uses G.729 or Opus, transcoding is needed.
2. **Codec mismatch:** The two legs simply don't share a codec.
3. **Feature requirements:** Recording, speech analytics, or DTMF detection may require specific codecs internally.

### The Cost of Transcoding

Transcoding is expensive in multiple ways:

- **CPU:** Decoding and re-encoding audio consumes significant CPU cycles. Each transcoded call might use 10-50x more CPU than a pass-through call.
- **Quality:** Every transcode is a lossy operation. Going from G.729 → PCM → G.729 loses quality each time. Tandem transcoding (multiple hops of transcoding) compounds the degradation.
- **Latency:** Codec algorithmic delay adds up. G.729 adds ~25ms per encode/decode cycle.

### Avoiding Transcoding

The best transcoding is no transcoding. Telnyx's B2BUA can pass through codecs when both legs support the same one:

```
Customer (Leg A)              Telnyx B2BUA              Carrier (Leg B)
G.711 at 64 kbps  ────────►  [Pass-through]  ────────►  G.711 at 64 kbps
```

No decoding, no re-encoding. The B2BUA just forwards RTP packets with minimal processing. This is why **including G.711 in your codec list** is almost always recommended — it's the universal common denominator.

🔧 **NOC Tip:** If a customer complains about voice quality and they're using G.729 exclusively, check if transcoding is occurring. Add G.711 to their codec list as the first preference. If both legs can use G.711, quality will improve because transcoding is eliminated.

---

## DTMF Negotiation

DTMF negotiation is a special case that causes frequent issues. There are three methods (Lesson 31):

1. **RFC 2833/4733 telephone-event:** Negotiated in SDP with `a=rtpmap:101 telephone-event/8000`
2. **In-band (audio):** DTMF tones carried in the audio stream — no explicit negotiation needed
3. **SIP INFO:** Sent as SIP messages, not in RTP — no SDP negotiation

### The Mismatch Problem

If one side negotiates `telephone-event` in SDP but the other doesn't include it, they disagree on DTMF method:
- Side A sends RFC 2833 events
- Side B expects in-band audio tones
- Result: DTMF digits are lost

Telnyx's B2BUA can translate between methods — converting RFC 2833 events to SIP INFO, or generating in-band tones from events. But this must be configured correctly.

🔧 **NOC Tip:** When customers report "IVR not responding to keypresses" or "DTMF digits not detected," check:
1. Is `telephone-event` in both the offer and answer SDP?
2. Do both sides agree on the same DTMF method?
3. Is the B2BUA configured to translate DTMF methods if they differ?
4. If using compressed codecs (G.729), in-band DTMF is unreliable — ensure RFC 2833 is negotiated.

---

## Codec Negotiation in Practice

### Recommended Codec Lists

For **PSTN calls** (compatibility priority):
```
G.711 μ-law (0), G.711 A-law (8), G.729 (18), telephone-event (101)
```

For **WebRTC calls** (quality priority):
```
Opus (dynamic), G.722 (9), G.711 μ-law (0), telephone-event (dynamic)
```

For **bandwidth-constrained environments:**
```
G.729 (18), G.711 μ-law (0), telephone-event (101)
```

### The T.38 Case

Fax calls use a special negotiation. The call starts as audio (G.711), then switches to T.38 via re-INVITE when fax tones are detected:

```
Initial: m=audio 10000 RTP/AVP 0
Re-INVITE: m=image 10000 udptl t38
```

If the far end doesn't support T.38, it responds 488, and the fax continues as G.711 passthrough (hoping the network is clean enough).

---

## Real-World Troubleshooting Scenario

**Problem:** A customer using a Grandstream PBX reports that calls to a specific country always fail with 488.

**Investigation:**
1. The PBX is configured to offer only G.729 (bandwidth conservation)
2. The terminating carrier for that country requires G.711 — they reject offers without it
3. Other countries work because their carriers accept G.729

**Fix:** Add G.711 to the PBX's codec list. If bandwidth is a concern, add it as a lower preference — the B2BUA will negotiate G.711 on the carrier leg and G.729 on the customer leg, transcoding between them. Better yet, use G.711 on both legs to avoid transcoding entirely.

---

**Key Takeaways:**
1. Codec preference order in SDP matters — list your most preferred codec first in the `m=` line
2. 488 Not Acceptable Here means no common codec — compare offer vs. destination capabilities
3. Transcoding is CPU-intensive, adds latency, and degrades quality — avoid it when possible by including G.711 in codec lists
4. The B2BUA negotiates codecs independently on each leg — enabling interworking between incompatible endpoints
5. DTMF method mismatch (RFC 2833 vs. in-band vs. SIP INFO) is a frequent cause of "DTMF not working"
6. Always include `telephone-event` in SDP for reliable DTMF — in-band DTMF fails with compressed codecs
7. T.38 fax negotiation uses re-INVITE to switch from audio to image media — 488 triggers G.711 passthrough fallback

**Next: Lesson 50 — Systematic Call Quality Troubleshooting**
