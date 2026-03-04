---
title: "The Jitter Buffer — Smoothing Out Packet Arrival Variation"
description: "Learn about the jitter buffer — smoothing out packet arrival variation"
module: "Module 1: Foundations"
lesson: "36"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand The jitter buffer holds packets to smooth arrival variation before playout — it's the primary defense against jitter
  - Understand Fixed buffers add constant latency; adaptive buffers trade variable latency for better jitter tolerance
  - Understand Late packets are functionally lost — jitter buffer depth controls the tradeoff between latency and effective loss rate
  - Understand PLC masks missing packets using interpolation — quality varies dramatically between simple repetition and advanced algorithms like Opus's built-in PLC
  - Understand Clock drift between sender and receiver slowly fills or empties the buffer — adaptive clock recovery compensates
slug: "jitter-buffer"
---

Jitter is the disease; the jitter buffer is the treatment. It's the single most important mechanism for maintaining audio quality in VoIP, and understanding how it works is essential for interpreting call quality metrics and diagnosing choppy audio.

## The Core Concept

Imagine packets arriving at these intervals (they should arrive every 20ms):

```
Packet 1: arrived at 0ms
Packet 2: arrived at 18ms   (2ms early)
Packet 3: arrived at 42ms   (2ms late)
Packet 4: arrived at 58ms   (18ms early?... no, the network was fast)
Packet 5: arrived at 85ms   (5ms late)
```

If you played each packet the instant it arrived, the audio would be a stuttering mess — gaps where packets are late, compression where they're early. Instead, the jitter buffer **holds** packets and plays them out at a fixed, regular interval.

With a 40ms jitter buffer, you'd wait 40ms before playing the first packet, then play one packet every 20ms regardless of when they actually arrived. As long as packets arrive within that 40ms window, audio is smooth.

## Fixed vs. Adaptive Jitter Buffers

### Fixed (Static) Jitter Buffer

Buffer depth is configured to a constant value — say 60ms. Every packet is delayed by exactly 60ms before playout.

**Pros:** Simple, predictable, constant added latency
**Cons:** If jitter exceeds the buffer depth, packets are discarded. If jitter is low, you're adding unnecessary delay.

Fixed buffers are common in hardware-based systems (traditional IP phones, media gateways) where simplicity and determinism are valued.

### Adaptive (Dynamic) Jitter Buffer

Buffer depth adjusts automatically based on measured jitter. When jitter is low, the buffer shrinks (lower latency). When jitter spikes, the buffer grows (absorbing the variation at the cost of more delay).

**How adaptation works:**
1. The buffer continuously measures interarrival jitter
2. A target buffer depth is calculated — typically the 95th or 99th percentile of recent jitter, plus a safety margin
3. The buffer expands by holding the next playout slightly longer (stretching)
4. The buffer contracts by slightly compressing playout timing or dropping a silence frame

**The catch:** Adaptation takes time. If jitter spikes suddenly, the buffer may not expand fast enough, causing a burst of late packets (treated as lost). If jitter drops, the buffer may take seconds to shrink, keeping latency unnecessarily high.

Most modern VoIP systems — including Telnyx's media processing — use adaptive jitter buffers. They're the right default for real-world conditions where jitter varies over the life of a call.

> **💡 NOC Tip:** en you see quality complaints during the first few seconds of a call that then improve, the adaptive jitter buffer is likely adjusting. Initial depth may be too shallow for the actual network conditions. Some systems allow configuring a minimum initial depth.

## Buffer Underrun and Overrun

### Underrun (Buffer Empty)

The playout clock wants to play the next frame, but the buffer is empty — the packet hasn't arrived yet. This creates a gap in the audio that must be filled.

**What you hear:** A brief silence or a "click" — depending on the PLC implementation. Frequent underruns cause the characteristic "choppy" or "robotic" audio.

**Cause:** Buffer depth is too small for the actual jitter, or a burst of packets was lost.

### Overrun (Buffer Full)

Packets arrive faster than they're played out, filling the buffer beyond its capacity. The oldest (or latest) packets are discarded.

**Cause:** Network conditions improved suddenly (lower delay), but the buffer hasn't adapted down yet. Or clock drift between sender and receiver (sender's 8kHz clock is slightly fast relative to receiver's).

**What you hear:** Usually nothing — the discarded packets were redundant. But if the buffer is poorly implemented, it can cause audio discontinuities.

## Packet Loss Concealment (PLC)

When a packet is genuinely lost (never arrives) or arrives too late for playout, the jitter buffer must generate something for that 20ms gap. This is Packet Loss Concealment:

### Simple PLC
- **Silence insertion:** Replace the missing frame with silence. Obvious and jarring.
- **Packet repetition:** Replay the last good packet. Works for single lost packets but produces a "frozen" effect for consecutive losses.

### Advanced PLC
- **Waveform interpolation:** Analyze the surrounding audio to generate a plausible fill-in. Modern codecs like Opus have built-in PLC that uses the codec's model to predict what the missing audio should sound like.
- **Time-scale modification:** Slightly stretch the surrounding audio to cover the gap without changing pitch.

Opus's built-in PLC is remarkably good — it can conceal single packet losses almost inaudibly. Even 2-3 consecutive losses can be masked. But beyond that, the prediction degrades rapidly and artifacts become obvious.

> **💡 NOC Tip:** e quality impact of packet loss depends heavily on the PLC implementation. 1% random loss with Opus is nearly inaudible. 1% random loss with G.729 (which has basic PLC) is noticeable. The same loss rate can produce very different MOS scores depending on the codec.

## Late Packets = Lost Packets

This is a critical concept: **a packet that arrives after its playout time is functionally identical to a lost packet.** The jitter buffer has already moved past that time slot — even if the packet eventually arrives, it's useless.

This means that jitter buffer depth directly controls the effective loss rate. A deeper buffer "saves" more late packets at the cost of latency. A shallow buffer discards more late packets, increasing effective loss.

In metrics:
- **Network loss:** Packets that never arrive (sequence number gaps in RTCP)
- **Effective loss:** Network loss + late discards (what the audio actually experiences)

Telnyx's monitoring should track both — network loss tells you about the path, effective loss tells you about the user's actual experience.

## Clock Drift and Skew

Here's a subtle problem: the sender's sampling clock and the receiver's playout clock are independent oscillators. If the sender's 8kHz clock is even 1 ppm faster than the receiver's, over time the sender produces slightly more audio than the receiver consumes.

After an hour of a call with 1 ppm drift: 8000 samples/sec × 3600 sec × 1×10⁻⁶ = 28.8 samples — about 3.6ms of drift. This slowly fills the jitter buffer, eventually causing overflows and discards.

Adaptive jitter buffers compensate for clock drift by periodically adding or dropping a single sample — a process called **adaptive resampling** or **clock recovery**. When done well, it's inaudible. When done poorly, it causes periodic clicks.

## Real Troubleshooting Scenario: Audio Quality Degrades Over Long Calls

**Symptom:** Short calls (< 5 minutes) sound fine. Calls lasting 30+ minutes develop increasing choppiness.

**Investigation:**
1. RTCP jitter values are stable throughout the call — network jitter isn't increasing
2. But effective loss rate increases over time
3. Jitter buffer statistics show the buffer slowly filling up

**Root cause:** Clock drift between the customer's PBX and Telnyx's media server. The PBX's clock is slightly fast, generating ~10 ppm more samples than expected. Over 30 minutes, the buffer fills, overflows, and starts discarding.

**Resolution:** Enabled adaptive clock recovery on the media server for this customer's traffic. Alternatively, the PBX manufacturer provides a firmware update with improved clock accuracy.

## Real Troubleshooting Scenario: WiFi Users Report Choppy Audio

**Symptom:** Employees using softphones on WiFi report intermittent choppy audio. Wired users on the same network are fine.

**Investigation:**
1. RTCP from WiFi users shows jitter spikes of 40-80ms
2. These spikes correlate with WiFi channel utilization
3. PCAP at the access point shows 802.11 retransmissions

**Root cause:** The WiFi network is congested — many devices competing for airtime. WiFi's contention-based access (CSMA/CA) and Layer 2 retransmissions introduce significant jitter. The softphone's jitter buffer (default 40ms) can't absorb it.

**Resolution:** 
1. Enable WiFi QoS (WMM — Wi-Fi Multimedia) to prioritize voice traffic
2. Increase softphone jitter buffer minimum to 60ms
3. Consider a dedicated SSID on a less congested channel for VoIP devices

## Monitoring Jitter Buffer Health

In Telnyx's Grafana dashboards, look for:
- **Buffer depth over time:** Should be relatively stable. Rapid expansion indicates jitter spikes.
- **Discard rate:** Percentage of packets discarded (late + overflow). > 1% likely audible.
- **PLC invocations:** How often concealment is triggered. Correlates with discard rate.
- **Expansion/contraction events:** Frequent adaptation suggests unstable network conditions.

These metrics, combined with RTCP jitter and loss, give a complete picture of the audio experience.

---

**Key Takeaways:**
1. The jitter buffer holds packets to smooth arrival variation before playout — it's the primary defense against jitter
2. Fixed buffers add constant latency; adaptive buffers trade variable latency for better jitter tolerance
3. Late packets are functionally lost — jitter buffer depth controls the tradeoff between latency and effective loss rate
4. PLC masks missing packets using interpolation — quality varies dramatically between simple repetition and advanced algorithms like Opus's built-in PLC
5. Clock drift between sender and receiver slowly fills or empties the buffer — adaptive clock recovery compensates
6. Monitor discard rate and PLC invocations, not just jitter — they reflect the actual audio experience

**Next: Lesson 35 — Packet Loss: Causes, Effects, and Measurement**
