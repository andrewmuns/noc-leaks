# Lesson 34: Latency Budget — Sources of Delay in a VoIP Call
**Module 1 | Section 1.9 — Jitter, Latency, and Call Quality**
**⏱ ~8 min read | Prerequisites: Lesson 29, Lesson 7**

---

When someone says "this call feels laggy," they're experiencing latency — the time it takes for sound to travel from the speaker's mouth to the listener's ear. In the PSTN world, latency was mostly fixed and predictable (the speed of light through fiber, plus minimal switching delay). In VoIP, latency comes from a dozen different sources, each adding their own contribution. Understanding this **latency budget** is how you diagnose why a call feels wrong.

## The ITU-T G.114 Guidelines

The ITU-T recommendation G.114 defines the thresholds:

| One-Way Delay | Quality Impact |
|---------------|---------------|
| < 150 ms | Excellent — conversational quality, no perceptible delay |
| 150–300 ms | Acceptable — slight delay noticeable, manageable |
| 300–450 ms | Poor — noticeable lag, conversation becomes difficult |
| > 450 ms | Unusable — severe delay, people talk over each other |

These are **one-way** delays. Round-trip time is double. At 200ms one-way, you're at 400ms round-trip — that's when people start unconsciously pausing and then talking over each other.

## Dissecting the Delay Chain

Let's trace every delay source from microphone to speaker, assigning typical values:

### 1. Codec/Algorithmic Delay (5–40 ms)

Every codec needs to collect a frame of audio before encoding it. G.711 has essentially zero algorithmic delay — each sample is encoded independently. But compressed codecs need a frame:

- **G.711:** ~0.125 ms (one sample period at 8 kHz) — effectively zero
- **G.729:** 15 ms (10ms frame + 5ms lookahead)
- **Opus:** 2.5–60 ms (configurable, typically 20ms)
- **G.722:** ~1.5 ms

G.729's 15ms algorithmic delay is unavoidable — it's built into the compression algorithm's need to analyze future samples (lookahead) to encode the current frame.

### 2. Packetization Delay (10–30 ms)

After encoding, samples are collected into packets. A 20ms packetization period means the encoder waits 20ms of audio before sending a packet. This is the most common setting.

- **20ms packetization:** 20 ms delay (standard)
- **30ms packetization:** 30 ms delay (sometimes used to reduce packet rate)
- **10ms packetization:** 10 ms delay (lower latency but more overhead)

Shorter packetization means lower delay but more packets per second (50 pps vs. 33 pps for 20ms vs. 30ms), which increases IP/UDP/RTP overhead as a percentage of bandwidth.

### 3. Serialization Delay (< 1 ms on modern links)

The time to push a packet's bits onto the wire. For a 214-byte RTP packet (G.711, 20ms) on a 100 Mbps link: 214 × 8 / 100,000,000 = 0.017 ms. On a 1.544 Mbps T1 line: 1.1 ms. On modern broadband and backbone links, serialization delay is negligible. On legacy WAN links, it can matter.

### 4. Propagation Delay (1–80 ms)

The speed of light through fiber optic cable is about 200,000 km/s (roughly 2/3 the speed of light in vacuum due to the refractive index of glass). This means:

- **Same city:** ~0.5 ms
- **Coast to coast (US, ~4,000 km):** ~20 ms
- **New York to London (~5,500 km):** ~28 ms
- **New York to Tokyo (~10,800 km):** ~54 ms
- **New York to Sydney (~16,000 km):** ~80 ms

These are **minimum** propagation delays — actual fiber routes are longer than great-circle distances because they follow infrastructure corridors and undersea cable routes.

🔧 **NOC Tip:** Propagation delay is physics — you cannot reduce it. When a customer complains about latency on a US-to-Australia call, 160ms round-trip propagation delay is the absolute minimum. Set expectations accordingly.

### 5. Queuing Delay (0–50+ ms, variable)

This is where things get unpredictable. Every router and switch along the path has buffers. When traffic exceeds capacity, packets queue. Voice packets queuing behind a burst of data traffic can experience significant delay — and worse, variable delay (jitter).

On well-provisioned backbone links, queuing delay is minimal. On congested last-mile connections (customer broadband, oversubscribed enterprise WANs), queuing delay dominates.

**Buffer bloat** — oversized router buffers that absorb traffic bursts instead of dropping packets — makes this worse. The packets eventually arrive, but with massive added delay.

### 6. Processing Delay (1–5 ms per hop)

Each network device that handles the packet adds processing time — routing lookups, ACL checks, NAT translation, firewall inspection. Modern hardware handles this in microseconds, but software-based firewalls or overloaded NAT gateways can add milliseconds.

### 7. Jitter Buffer Delay (20–80 ms)

The receiver's jitter buffer holds packets to smooth out arrival variation (covered in detail in Lesson 34). A fixed 60ms jitter buffer adds exactly 60ms of delay. Adaptive jitter buffers vary their depth — perhaps 20ms when jitter is low, expanding to 80ms during congestion.

This is the last and often largest controllable delay source. It's a direct tradeoff: more buffer = more delay = more tolerance for jitter.

### 8. Decoding Delay (< 1 ms)

Decoding is generally faster than encoding since it doesn't require analysis. Typically negligible.

## Adding It Up: Example Latency Budgets

### Best Case: Same-Region G.711 Call
| Component | Delay |
|-----------|-------|
| Codec (G.711) | ~0 ms |
| Packetization (20ms) | 20 ms |
| Serialization | < 1 ms |
| Propagation (500 km) | 2.5 ms |
| Queuing (well-provisioned) | 2 ms |
| Processing (3 hops) | 1.5 ms |
| Jitter buffer (adaptive, low) | 20 ms |
| **Total one-way** | **~47 ms** |

Excellent quality — well under 150ms.

### Typical Case: Cross-Country G.729 Call via B2BUA
| Component | Delay |
|-----------|-------|
| Codec (G.729 algorithmic) | 15 ms |
| Packetization (20ms) | 20 ms |
| Serialization | < 1 ms |
| Propagation (4,000 km) | 20 ms |
| Queuing (moderate) | 10 ms |
| Processing (5 hops + B2BUA) | 5 ms |
| Jitter buffer (adaptive, moderate) | 40 ms |
| Transcoding at B2BUA | 15 ms |
| **Total one-way** | **~126 ms** |

Still acceptable, but getting close to the 150ms threshold. Adding transcoding (the B2BUA decodes G.729 and re-encodes to G.711 for the PSTN leg) adds significant delay.

### Worst Case: International Call with Transcoding and Congestion
| Component | Delay |
|-----------|-------|
| Codec (G.729 algorithmic) | 15 ms |
| Packetization (30ms) | 30 ms |
| Serialization | 1 ms |
| Propagation (12,000 km) | 60 ms |
| Queuing (congested last-mile) | 40 ms |
| Processing (8 hops + B2BUA) | 8 ms |
| Jitter buffer (adaptive, high) | 80 ms |
| Transcoding (2×, both legs) | 30 ms |
| **Total one-way** | **~264 ms** |

Poor quality. Users will notice significant delay and talk over each other.

## The Compounding Effect

Each delay source is individually small, but they compound. Adding "just one more thing" — an extra transcoding step, a recording server in the media path, a SIP proxy that parses the message — each adds 5-20ms. In a complex call path with multiple media processing stages, these add up fast.

🔧 **NOC Tip:** When investigating latency complaints, build the latency budget for the specific call path. Identify which components are contributing the most. Often it's the customer's last-mile network (queuing) or an unnecessary transcoding step.

## Real Troubleshooting Scenario: "Calls to India are too laggy"

**Symptom:** Customer reports unacceptable delay on calls to India.

**Investigation:**
1. Calculate minimum propagation: US East Coast to Mumbai ≈ 13,000 km ≈ 65ms one-way
2. Add typical processing chain: codec (15ms) + packetization (20ms) + jitter buffer (60ms) + queuing (15ms) = 110ms
3. Total: ~175ms one-way minimum — already above the "excellent" threshold
4. Check for transcoding — if G.729↔G.711 conversion happens twice (at Telnyx and at the Indian carrier's gateway), add 30ms
5. Total: ~205ms — noticeable but manageable

**Resolution:** This is primarily a physics problem. Recommend: use G.711 end-to-end if bandwidth allows (eliminates codec delay), reduce jitter buffer to minimum stable level, ensure no unnecessary media processing in the path.

## How Telnyx's Architecture Helps

Telnyx's global Points of Presence (PoPs) reduce propagation delay by terminating calls closer to both the customer and the PSTN interconnect. Instead of routing US→Telnyx-US→carrier-gateway-in-India, if Telnyx has an Indian PoP, the path becomes: US→Telnyx-US→(backbone)→Telnyx-India→carrier-India — with the backbone segment being optimized private infrastructure rather than best-effort internet.

---

**Key Takeaways:**
1. One-way delay under 150ms is the target for conversational quality — G.114 is your reference
2. The latency budget has 8 components: codec, packetization, serialization, propagation, queuing, processing, jitter buffer, and decoding
3. Propagation delay is physics (speed of light) — you cannot optimize it away
4. Queuing delay (especially customer last-mile) and jitter buffer are usually the largest variable contributors
5. Transcoding adds 15ms+ per conversion — avoid unnecessary transcoding
6. Always build the complete latency budget when investigating delay complaints — the culprit is often the sum of many small delays

**Next: Lesson 33 — Jitter: Why Packets Arrive at Irregular Intervals**
