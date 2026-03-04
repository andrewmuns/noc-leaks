# Lesson 136: Advanced PCAP Analysis — RTP Quality and Media Issues

**Module 4 | Section 4.4 — Network Debug**
**⏱ ~8 min read | Prerequisites: Lesson 119**

---

Basic packet captures show whether RTP is flowing. Advanced analysis reveals *how well* it's flowing: loss patterns, jitter distributions, burst characteristics, and codec-specific issues. This lesson teaches the detailed analysis techniques that separate "I see RTP" from "I understand the quality degradation."

## RTP Stream Analysis in Depth

Wireshark's RTP Stream Analysis (Telephony → RTP → RTP Streams → Analyze) provides comprehensive quality metrics:

### Key Metrics Explained

**Packets Expected vs. Received:**
```
Expected: 3000 (calculated from duration × packets/second)
Received: 2950
Lost: 50 (1.7%)
```

The expected count is calculated from the time span and packet rate. If 20ms packetization is used, there should be 50 packets/second. A 60-second call should have 3000 packets.

**Sequence Number Analysis:**
```
Max Seq: 3000
Seq Cycles: 0
```

RTP sequence numbers wrap at 65535. "Seq Cycles" counts how many times the sequence number wrapped. For short calls, this should be 0.

**Jitter Statistics:**
```
Mean Jitter: 2.5 ms
Max Jitter: 45.3 ms
```

Mean jitter around 2-5ms is normal for a healthy network. Max jitter spikes can indicate congestion bursts. Jitter >30ms typically causes audible quality degradation.

### The "Save as CSV" Feature

Export stream analysis data for spreadsheet analysis:
1. In RTP Stream Analysis window, click "Save as CSV"
2. Opens in Excel/Google Sheets
3. Each row = one packet
4. Columns: timestamp, sequence, delta, jitter, etc.

This enables:
- Plotting jitter over time (identify when degradation occurred)
- Correlating loss bursts with timestamps
- Identifying patterns (cyclic loss, periodic jitter)

## Detecting Burst Loss vs. Random Loss

Burst loss is far more damaging than random loss:

### Random Loss (3%)
```
Seq: 1, 2, 3, X, 5, 6, 7, X, 9, 10, 11, 12, X, 14...
Loss pattern: Single isolated drops
```
Packet Loss Concealment (PLC) handles isolated drops well. The listener might not notice 1-2% random loss.

### Burst Loss (3%)
```
Seq: 1, 2, 3, 4, 5, X, X, X, X, X, 11, 12, 13...
Loss pattern: 5 consecutive drops
```
Burst loss exceeds PLC capability. The listener hears glitches, gaps, or robotic audio.

### Analyzing Burst Patterns in Wireshark

1. Export RTP stream analysis to CSV
2. Calculate the difference between consecutive sequence numbers
3. Where difference > 1, loss occurred
4. Group consecutive losses to identify bursts

Example CSV analysis:
```
Packet  Seq   Delta   Status
1       100   20ms    OK
2       101   21ms    OK
3       102   19ms    OK
4       105   22ms    LOST (gap of 3)
5       106   20ms    OK
6       107   20ms    OK
...
20      120   20ms    OK
21      125   25ms    LOST (gap of 5)
22      126   20ms    OK
```

The gap of 5 (packets 121-124 lost) is a burst. A gap of 1-2 is handled by PLC; a gap of 5+ causes audible glitches.

🔧 **NOC Tip:** When customers report "robotic" or "glitchy" audio, check for burst loss. Random 3% loss often sounds acceptable; burst 3% loss sounds terrible. The same overall loss percentage has drastically different quality impact depending on distribution.

## Jitter Analysis Beyond Averages

Mean jitter of 5ms tells you little about actual user experience. Dig deeper:

### Jitter Distribution

Export to CSV and plot jitter values:
```
Packets with jitter <10ms:  95%
Packets with jitter 10-30ms: 4%
Packets with jitter >30ms:  1%
```

If 1% of packets have jitter >30ms and the jitter buffer is 30ms, those packets arrive too late and get dropped. The 95% with <10ms jitter are fine, but the 1% outliers cause quality hits.

### Jitter Spikes Correlation

Plot jitter over time alongside other metrics:
- CPU utilization
- Network throughput
- Other traffic on the same path

If jitter spikes correlate with throughput spikes, congestion is likely the cause.

### Interarrival Jitter Calculation

The RTP header doesn't contain jitter — it's calculated from timestamps:

```
J = J + (|D(i-1,i)| - J)/16

Where D(i-1,i) = (Ri - Ri-1) - (Si - Si-1)
R = arrival time
S = RTP timestamp
```

Wireshark does this calculation automatically. The key insight: jitter measures the *variation* in interarrival times, not the delay itself.

## Codec Identification from RTP Payload Types

RTP payload types map to codecs:

```
Payload Type 0:   G.711 μ-law (PCMU)
Payload Type 8:   G.711 A-law (PCMA)
Payload Type 18:  G.729
Payload Type 96+: Dynamic (negotiated in SDP)
```

In Wireshark:
```
Frame 123: RTP
  Real-Time Transport Protocol
    Payload type: ITU-T G.711 PCMA (8)
```

For dynamic payload types, check the SDP negotiation:
```
a=rtpmap:96 opus/48000/2
a=rtpmap:97 telephone-event/8000
```

Payload type 96 = Opus at 48kHz stereo.

### Codec-Specific Quality Characteristics

| Codec | Bandwidth | Resilience to Loss | Typical Issues |
|-------|-----------|-------------------|----------------|
| G.711 (μ/A) | 64 kbps | Good (PLC works well) | Echo, latency |
| G.729 | 8 kbps | Poor (model-based) | Robotic audio on loss |
| Opus | 6-510 kbps | Excellent (FEC built-in) | Complexity, latency |

G.729 is extremely sensitive to loss — 3% loss with G.729 sounds far worse than 3% loss with G.711. If G.729 is negotiated and there's any packet loss, consider switching to G.711 if bandwidth allows.

## DTMF Analysis in RTP

DTMF (touch tones) is carried in RTP using RFC 2833/4733 telephone events:

```
Frame 456: RTP
  Payload type: telephone-event (101)
  Event ID: 5 (digit '5')
  Event duration: 1600 (200ms at 8000Hz)
  End of event: Yes
```

**DTMF issues to look for:**

### Missing DTMF Packets

If user presses digits but IVR doesn't respond:
1. Filter for `rtp.p_type == 101` (telephone-event payload type)
2. Check if DTMF packets appear in the capture
3. If missing, check SDP negotiation — was telephone-event offered and accepted?

### DTMF Duration Issues

```
Event duration: 400 (50ms)
```

Very short DTMF durations (<40ms) might not be detected by IVR systems. If users report "digits aren't registering," check DTMF duration in the capture.

### In-Band vs. Out-of-Band DTMF Mismatch

```
# SDP offer
a=fmtp:101 0-15   ← telephone-event for digits 0-15

# But one side sends in-band (audio tones)
# The other expects out-of-band (RFC 2833)
```

Result: IVR doesn't detect digits because it's listening for telephone events, but the sender put tones in audio.

## RTCP Analysis in PCAP

RTCP (Real-time Control Protocol) provides quality feedback:

### Sender Report (SR)
```
SSRC: 0x12345678
NTP timestamp: 0xe0b5a7c0.0x12345678
RTP timestamp: 48000
Packet count: 500
Octet count: 80000
```

### Receiver Report (RR)
```
SSRC: 0x12345678
Fraction lost: 0
Cumulative lost: 5
Highest seq: 3000
Jitter: 3
Last SR: 0xe0b5a7c0
```

**Key RR fields for quality monitoring:**

| Field | Meaning | Threshold |
|-------|---------|-----------|
| **Fraction lost** | Loss since last RR (0-255 / 256) | <10 (3.9%) |
| **Cumulative lost** | Total lost packets | Depends on duration |
| **Jitter** | Interarrival jitter estimate | <30ms |
| **LSR/DLSR** | Last SR timestamp + delay | For RTT calculation |

Filter in Wireshark:
```
rtcp
rtcp.rc == 5   # Receiver report with fraction lost = 5/256
```

🔧 **NOC Tip:** RTCP Receiver Reports provide real-time quality metrics *from the receiver's perspective*. If you capture at the sender, you see RTCP RR coming back. The "Fraction lost" field tells you how much the receiver is experiencing — more accurate than calculating loss from one-sided capture.

## Identifying Network vs. Endpoint Issues

### Network Issues (visible in capture)

- **Packet loss**: Gaps in sequence numbers
- **Jitter**: Variable interarrival times
- **Reordering**: Packets arriving out of sequence
- **Duplication**: Same sequence number appearing twice

### Endpoint Issues (visible in capture)

- **Silence suppression**: Periods with no RTP (VAD active)
- **Late start**: First RTP delayed after call establishment
- **Codec switching**: Mid-call payload type changes
- **Clock drift**: Timestamp irregularities not matching arrival pattern

### System Issues (not visible in capture)

- **Endpoint CPU overload**: Packets arrive but processing delayed
- **Jitter buffer issues**: Buffer configuration (too deep = latency, too shallow = drops)
- **Audio hardware issues**: Microphone/speaker problems

## Real-World Scenario: Choppy Audio Investigation

**Customer report:** "Audio is choppy on calls through carrier X."

**Capture and analysis:**

1. Capture 2 minutes of active call RTP:
```bash
tcpdump -i eth0 "udp portrange 10000-20000" -w choppy.pcap -G 120
```

2. Open in Wireshark, analyze RTP stream:
```
Packets: 6000 (expected for 120 seconds × 50/sec)
Lost: 180 (3%)
Mean Jitter: 8ms
Max Jitter: 120ms
```

3. Export to CSV, analyze loss distribution:
```
Burst analysis:
- 150 isolated losses (single packets)
- 6 bursts of 3-5 consecutive packets
```

4. Check jitter distribution:
```
Jitter < 10ms: 94%
Jitter 10-30ms: 4%
Jitter 30-100ms: 1.5%
Jitter > 100ms: 0.5%
```

5. Key insight: Max jitter of 120ms with 0.5% of packets >100ms — but jitter buffer is likely 50ms default → late packets being dropped.

6. Check RTCP Receiver Report:
```
Fraction lost: 8/256 = 3.1% (matches capture analysis)
Jitter: 25ms (higher than network jitter — endpoint processing adds to it)
```

**Root cause:**
- 3% packet loss (moderate, but includes bursts)
- Jitter spikes up to 120ms, but jitter buffer only 50ms
- Result: Packets with >50ms jitter arrive after playout time → treated as loss

**Resolution:**
- Increase jitter buffer depth to 100ms (trade-off: adds latency)
- Or investigate network path for jitter source (route optimization)
- Or switch to codec with better loss resilience (Opus with FEC)

---

**Key Takeaways:**

1. RTP Stream Analysis shows expected vs. received packets, loss count, and jitter statistics
2. Burst loss (consecutive packets) causes far more quality degradation than random loss
3. Jitter distribution matters more than mean jitter — identify outliers causing late-packet drops
4. Codec identification from payload types: G.711 is resilient to loss; G.729 is fragile
5. DTMF analysis checks for telephone-event payload type and event durations
6. RTCP Receiver Reports provide remote-side quality metrics (fraction lost, jitter from their view)
7. Correlate capture metrics with jitter buffer configuration — 50ms buffer + 100ms jitter = late drops
8. Export to CSV enables time-series analysis: plot jitter over time, identify correlation with other events

**Next: Lesson 121 — Common Failure Pattern — Service Overload and Cascading Failures**
