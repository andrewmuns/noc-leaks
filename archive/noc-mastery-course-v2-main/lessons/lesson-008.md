# Lesson 8: G.711 — The Universal Codec
**Module 1 | Section 1.2 — Digital Voice: Sampling, Quantization, and Codecs**
**⏱ ~6 min read | Prerequisites: Lesson 5**

---

## Why G.711 Is the Lingua Franca

Every SIP device in the world supports G.711. Every PSTN gateway speaks it natively. It's the codec you fall back to when nothing else works, and it's the codec that defines baseline voice quality.

G.711 isn't clever. It doesn't compress. It simply takes the PCM samples from Lesson 5 and ships them across the network. Its "algorithm" is companding (μ-law or A-law) — that's it. No prediction, no modeling, no transforms.

This simplicity is its greatest strength:
- **Zero algorithmic delay**: No buffering frames for analysis; each sample is independent
- **No computational cost**: Any processor can encode/decode G.711 trivially
- **Maximum compatibility**: Every device supports it
- **Highest narrowband quality**: No compression artifacts; the only impairment is quantization noise

The tradeoff is bandwidth. G.711 uses 64 kbps of codec bitrate — the most of any standard voice codec. But "64 kbps" is only part of the story.

## Packetization: Turning a Continuous Stream into Packets

On a TDM network, G.711 is a continuous stream of 8-bit samples, one every 125 μs. On an IP network, we can't send one sample at a time — the overhead would be catastrophic (40 bytes of IP/UDP/RTP headers for a 1-byte payload).

Instead, we collect multiple samples into a single packet. The number of samples collected determines the **packetization period** (or ptime — packetization time).

The standard packetization period is **20 ms**:

```
8,000 samples/sec × 0.020 sec = 160 samples per packet
160 samples × 1 byte/sample = 160 bytes of audio payload per packet
```

This means 50 packets per second (1000ms ÷ 20ms = 50).

Other common packetization periods:

| ptime | Samples | Payload Size | Packets/sec |
|-------|---------|-------------|-------------|
| 10 ms | 80 | 80 bytes | 100 |
| 20 ms | 160 | 160 bytes | 50 |
| 30 ms | 240 | 240 bytes | 33.3 |

## Real Bandwidth: The Overhead Tax

The 64 kbps codec rate is just the payload. Every packet also carries protocol headers:

| Layer | Header Size |
|-------|------------|
| IP | 20 bytes |
| UDP | 8 bytes |
| RTP | 12 bytes |
| **Total overhead** | **40 bytes per packet** |

For 20 ms packetization:
```
Per packet: 160 bytes (payload) + 40 bytes (headers) = 200 bytes = 1,600 bits
Packets per second: 50
Total bandwidth: 50 × 1,600 = 80,000 bps = 80 kbps
```

Add Ethernet framing (14 bytes header + 4 bytes FCS + potentially 4 bytes VLAN tag):
```
Per packet: 200 + 18 = 218 bytes (or 222 with VLAN)
Total on the wire: ~87 kbps
```

So a "64 kbps" G.711 call actually consumes **~87 kbps** on an Ethernet network. For a bidirectional call, that's **~174 kbps** total.

🔧 **NOC Tip:** When calculating SIP trunk bandwidth requirements, never use the raw codec rate. Use the fully-loaded rate including headers. For G.711 with 20ms ptime: budget ~90 kbps per direction, ~180 kbps per call. A customer asking "how much bandwidth do I need for 100 simultaneous G.711 calls?" needs approximately 18 Mbps of dedicated voice bandwidth — not 6.4 Mbps. Getting this math wrong leads to congestion and quality degradation.

## Packetization Period Tradeoffs

**Shorter ptime (10 ms):**
- Lower packetization delay (good for latency-sensitive applications)
- More packets per second → more overhead → more bandwidth (~96 kbps for G.711)
- More packets means more opportunities for per-packet loss to affect quality
- Higher PPS (packets per second) can stress firewalls and routers

**Longer ptime (30 ms):**
- More efficient (lower overhead percentage)
- Each lost packet removes more audio (30 ms of audio lost vs. 20 ms)
- Adds packetization delay
- Reduces PPS, easing network device load

20 ms is the sweet spot that most of the industry settled on. You'll see `a=ptime:20` in virtually every SDP offer.

## When to Use G.711 vs. Compressed Codecs

**Use G.711 when:**
- Bandwidth is plentiful (LAN, high-capacity WAN)
- PSTN interconnection requires it (most PSTN gateways prefer G.711)
- Maximum quality is needed and latency must be minimized
- You want to avoid transcoding at any cost

**Consider compressed codecs when:**
- Bandwidth is constrained (satellite links, congested WAN)
- Many simultaneous calls share limited bandwidth
- The quality tradeoff is acceptable for the use case

In Telnyx's infrastructure, G.711 is typically used on PSTN-facing legs (where the PSTN gateway expects it) and on high-capacity backbone links where bandwidth isn't a concern. Compressed codecs like G.729 or Opus might be used on customer-facing legs when the customer's equipment negotiates them.

## A Real Troubleshooting Scenario

**Scenario:** A customer reports choppy audio on all calls. Their office has a 10 Mbps internet connection shared with data traffic. They have approximately 50 concurrent calls during peak hours.

**Analysis:**
```
50 calls × 2 directions × ~87 kbps = 8,700 kbps ≈ 8.7 Mbps
Remaining for all other office traffic: ~1.3 Mbps
```

Their voice traffic alone is consuming 87% of their internet bandwidth, leaving almost nothing for email, web browsing, video conferencing, and cloud applications. Worse, without QoS, data traffic competes equally with voice traffic, causing packet loss and jitter on the voice stream.

**What you'd see in monitoring:**
- RTCP reports showing elevated jitter (>30 ms) and packet loss (>2%)
- Quality degradation correlating with business hours (when data usage is highest)
- Occasional total audio dropout coinciding with large file transfers or backups

**Resolution options:**
1. Implement QoS on the customer's router to prioritize voice traffic (DSCP EF marking)
2. Switch to G.729 (~24 kbps per direction with headers): 50 calls × 2 × 24 kbps = 2.4 Mbps — a 72% reduction. But this requires transcoding if Telnyx's PSTN leg uses G.711.
3. Upgrade their internet connection
4. Implement a dedicated voice VLAN with reserved bandwidth

🔧 **NOC Tip:** When a customer reports "all calls are bad" and they're on a shared internet connection, always calculate their voice bandwidth consumption first. It's the fastest way to determine if the problem is simply congestion. Ask: how many concurrent calls? What codec? What's their total bandwidth? If voice consumption exceeds 30-40% of their total bandwidth without QoS, congestion is almost certainly the cause.

---

**Key Takeaways:**
1. G.711 is uncompressed PCM (64 kbps) with zero algorithmic delay — the universal fallback codec supported by all SIP devices
2. With 20 ms packetization, each G.711 packet carries 160 bytes of audio payload, sent 50 times per second
3. Real bandwidth is ~87 kbps per direction (not 64 kbps) due to IP/UDP/RTP header overhead — always use the fully-loaded rate for capacity planning
4. Packetization period (ptime) trades off between latency, overhead, and loss resilience — 20 ms is the industry standard
5. G.711 is preferred for PSTN interconnection and high-quality LAN calls; compressed codecs save bandwidth at the cost of quality and processing

**Next: Lesson 7 — Compressed Codecs — G.729, G.722, and Why Compression Matters**
