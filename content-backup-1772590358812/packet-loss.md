---
title: "Packet Loss — Causes, Effects, and Measurement"
description: "Learn about packet loss — causes, effects, and measurement"
module: "Module 1: Foundations"
lesson: "37"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand Burst loss is far more damaging than random loss at the same percentage — always examine the loss pattern, not just the aggregate rate
  - Understand Common causes: congestion (queue overflow), firewall timeouts, MTU/fragmentation issues, wireless interference, and rate policing
  - Understand RTCP reports aggregate loss but can't distinguish random vs. burst or network loss vs. late arrivals — use PCAPs for detailed analysis
  - Understand Loss impact is non-linear: 1% is barely noticeable, 5% is clearly annoying, 10% is very poor
  - Understand Asymmetric loss (different in each direction) is common due to asymmetric routing — always check both directions
slug: "packet-loss"
---

Packet loss is the most directly destructive impairment for voice quality. Latency makes conversations awkward; jitter makes audio choppy at the edges. But packet loss literally removes pieces of the conversation. Understanding the types, causes, and measurement of packet loss is fundamental to NOC operations.

## Random Loss vs. Burst Loss

This distinction changes everything about the impact on audio quality.

### Random (Isolated) Loss

Individual packets dropped independently — packet 50 is lost, then packets 51-80 arrive fine, then packet 81 is lost. At 1% random loss, you're losing one packet every 100, which means one 20ms gap every 2 seconds.

**Impact:** Modern PLC algorithms handle this well. Opus can conceal isolated losses almost perfectly because it has good surrounding context. The listener may not notice 1-2% random loss at all.

### Burst Loss

Multiple consecutive packets lost — packets 50-55 all drop (120ms of audio gone). This happens when a buffer overflows and drops a queue's worth of packets, or when a link flaps briefly.

**Impact:** Devastating. PLC can interpolate one missing packet from its neighbors, but it can't reconstruct 100ms+ of audio from nothing. A 6-packet burst at 20ms packetization = 120ms gap — clearly audible as a "hole" in the conversation.

**The math:** 2% random loss produces occasional barely-audible concealment. 2% burst loss (concentrated in bursts of 5-10 packets) produces periodic, clearly audible dropouts even though the aggregate loss rate is the same.

> **💡 NOC Tip:** en reviewing loss metrics, always look at the **loss pattern**, not just the percentage. RTCP reports aggregate loss over the reporting interval — they can't distinguish random from burst. You need packet captures to see the actual pattern.

## Causes of Packet Loss

### 1. Network Congestion (Queue Overflow)

The most common cause. When a router's output queue fills up, new arrivals are dropped. This typically produces **burst loss** — the queue fills during a traffic spike and drops several packets in succession before the congestion subsides.

Tail-drop queuing (the default) drops whatever arrives when the queue is full. Active Queue Management (AQM) algorithms like RED (Random Early Detection) start dropping packets probabilistically before the queue is full, trading burst loss for random loss — which is actually better for voice.

### 2. Firewall and Security Device Drops

Stateful firewalls track UDP "connections" using timeouts (typically 30-60 seconds). If no packets flow for longer than the timeout, the firewall forgets the session. The next packet is treated as unsolicited inbound UDP and dropped.

This affects:
- **Calls on hold:** No media flows during hold, firewall state expires, media fails when resumed
- **Long-duration calls with silence suppression (VAD):** Extended silence periods can exceed firewall timeouts

### 3. MTU/Fragmentation Issues

If an RTP packet exceeds the path MTU and the Don't Fragment (DF) bit is set, the packet is dropped and an ICMP "Fragmentation Needed" message is sent back. If ICMP is blocked (common in overzealous firewall configs), Path MTU Discovery fails and packets are silently dropped.

A G.711 RTP packet with 20ms packetization is ~214 bytes — well under the standard 1500-byte MTU. But VPN encapsulation (IPsec adds 50-70 bytes, GRE adds 24 bytes) reduces the effective MTU. Customers running VoIP over VPN without adjusting MTU is a common cause of loss.

### 4. Wireless Packet Loss

WiFi and cellular networks have inherent packet loss from radio interference, signal attenuation, and contention. WiFi's Layer 2 retransmission hides some loss (at the cost of jitter), but not all. Cellular networks prioritize signaling over data, and voice packets may be deprioritized during congestion.

### 5. Software Bugs and Resource Exhaustion

Application-level drops: media server runs out of memory, packet processing thread is blocked, socket buffer overflows. These produce erratic loss patterns that don't correlate with network conditions.

### 6. Intentional Drops (Policing)

ISPs may police traffic to contracted rates. Exceeding the committed information rate (CIR) causes excess packets to be marked or dropped. If a customer's VoIP traffic exceeds their ISP's rate limit, voice packets are among the casualties.

## Measuring Packet Loss

### From RTCP Receiver Reports

The RTCP Receiver Report includes two loss metrics:
- **Fraction lost:** Loss in the last reporting interval (typically 5 seconds). This is what dashboards display as "current loss."
- **Cumulative packets lost:** Total since the session began. Useful for calculating overall loss rate.

**How it's calculated:** The receiver tracks the highest sequence number received and the total packets received. Expected packets = highest seq - initial seq + 1. Lost = expected - received.

**Limitation:** RTCP can't distinguish between actual network loss and late arrivals that the jitter buffer discarded. Both look like "missing packets" from the RTCP perspective. To know the true network loss (vs. effective loss), you need captures at both ends.

### From Packet Captures

In Wireshark, analyze RTP streams: **Telephony → RTP → Stream Analysis**

Look for:
- **Sequence number gaps:** Missing numbers indicate lost packets
- **Delta spikes followed by gaps:** Packets arrived late, some missing
- **Duplicate sequence numbers:** Rare but indicates network duplication

The RTP stream analysis graph shows lost packets as gaps in the sequence number timeline — visually clear and easy to identify burst patterns.

### Using Synthetic Testing

Active probing tools send periodic test packets and measure loss:
- `ping` with count and interval: basic but only tests ICMP (may be treated differently than UDP)
- `iperf3 -u`: UDP traffic with loss statistics — more representative of voice traffic behavior
- Specialized VoIP testing tools that send RTP-like streams and measure loss, jitter, and MOS

> **💡 NOC Tip:** en you suspect path-level loss, don't rely solely on ICMP ping. Some networks prioritize or deprioritize ICMP differently than UDP. Use `iperf3 -u` with a bandwidth matching voice traffic (~100 kbps per stream) for a realistic test.

## Impact on MOS and Quality

The E-Model (Lesson 9) maps packet loss to quality degradation. The relationship is non-linear:

| Loss Rate | Typical MOS Impact (G.711) | Perception |
|-----------|---------------------------|------------|
| 0% | 4.4 (baseline) | Excellent |
| 0.5% | 4.2 | Barely noticeable |
| 1% | 4.0 | Slight degradation |
| 2% | 3.6 | Noticeable |
| 5% | 3.0 | Annoying |
| 10% | 2.2 | Very annoying |
| 20% | 1.5 | Unusable |

These values assume random loss with basic PLC. Burst loss at the same percentage is worse. Better PLC (Opus) shifts the curve right — higher loss is tolerable.

## Real Troubleshooting Scenario: One-Direction Loss

**Symptom:** Caller can hear callee perfectly, but callee reports choppy audio from the caller.

**Investigation:**
1. RTCP from both legs: caller's Receiver Report shows 0% loss (callee→caller path is clean). Callee's Receiver Report shows 3% loss (caller→callee path has issues).
2. Asymmetric loss — common because forward and reverse paths often differ (asymmetric routing, Lesson 51)
3. Traceroute from caller's network shows a congested hop at their ISP's peering point

**Root cause:** The caller's ISP has congestion on their upstream path. Downstream (ISP→caller) is fine, so callee's audio reaches the caller. Upstream (caller→ISP) is congested, losing caller's voice packets.

**Resolution:** Customer contacts their ISP about upstream congestion, or switches to a different ISP egress path if available.

## Real Troubleshooting Scenario: Loss Only Affects Long Calls

**Symptom:** Short calls (< 2 minutes) are fine. Calls lasting 5+ minutes develop packet loss.

**Investigation:**
1. Loss starts appearing ~3 minutes into calls
2. Pattern is consistent across different called numbers
3. Customer is behind a corporate firewall

**Root cause:** The firewall's UDP session timeout is set to 180 seconds (3 minutes). For calls with any brief silence (hold, mute, VAD), the firewall state expires. Subsequent packets are dropped until the state is re-established.

**Resolution:** Increase firewall UDP session timeout to at least 300 seconds. Or enable SIP ALG to maintain state based on SIP signaling (though SIP ALG has its own issues — Lesson 28).

## Forward Error Correction (FEC)

Some systems proactively combat loss by sending redundant data:

- **RFC 2198 Redundant Audio:** Each packet carries the current frame plus a compressed copy of the previous frame. If a packet is lost, the next packet contains a lower-quality copy of the missing audio.
- **Opus in-band FEC:** Opus can embed FEC data within its packets, allowing the decoder to recover a lower-fidelity version of lost packets.
- **Media-level FEC (RFC 5109):** XOR-based parity packets that can reconstruct one lost packet from a group.

FEC trades bandwidth for loss resilience. It's especially effective against random loss. Burst loss defeats most FEC schemes because multiple consecutive packets (and their redundancy) are lost together.

---

**Key Takeaways:**
1. Burst loss is far more damaging than random loss at the same percentage — always examine the loss pattern, not just the aggregate rate
2. Common causes: congestion (queue overflow), firewall timeouts, MTU/fragmentation issues, wireless interference, and rate policing
3. RTCP reports aggregate loss but can't distinguish random vs. burst or network loss vs. late arrivals — use PCAPs for detailed analysis
4. Loss impact is non-linear: 1% is barely noticeable, 5% is clearly annoying, 10% is very poor
5. Asymmetric loss (different in each direction) is common due to asymmetric routing — always check both directions
6. FEC trades bandwidth for loss resilience and is most effective against random (not burst) loss

**Next: Lesson 36 — Packet Reordering, Duplication, and Their Impact**
