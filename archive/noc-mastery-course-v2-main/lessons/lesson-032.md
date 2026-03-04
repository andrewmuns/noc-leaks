# Lesson 32: RTCP — Feedback, Quality Reporting, and Congestion Control

**Module 1 | Section 1.8 — RTP/RTCP**
**⏱ ~7 min read | Prerequisites: Lesson 29**

---

## RTCP Purpose

RTCP provides the control channel that RTP lacks. While RTP carries media, RTCP carries statistics about that media — enabling quality monitoring, synchronization, and diagnostic capabilities.

---

## RTCP Packet Types

| Type | Abbreviation | Purpose |
|------|--------------|---------|
| 200 | SR | Sender Report: Statistics from active senders |
| 201 | RR | Receiver Report: Statistics from receivers |
| 202 | SDES | Source Description: CNAME, name, email, etc. |
| 203 | BYE | Stream termination notification |
| 204 | APP | Application-defined extensions |
| 207 | XR | Extended Report: Detailed quality metrics |

---

## Sender Reports (SR)

SR packets are sent by participants transmitting RTP. Key contents:

```
NTP Timestamp: Wall clock time (64-bit)
RTP Timestamp: Corresponding RTP timestamp
Sender's Packet Count: Total packets sent
Sender's Octet Count: Total bytes sent
```

**Purpose:** Receivers can synchronize multiple RTP streams (audio + video) by comparing NTP timestamps across RTCP SR packets.

---

## Receiver Reports (RR)

RR packets contain the critical quality metrics:

| Field | Size | Description |
|-------|------|-------------|
| SSRC_n | 32 bits | Which sender this report is about |
| Fraction Lost | 8 bits | Packet loss % since last report |
| Cumulative Lost | 24 bits | Total packets lost |
| Extended Highest Seq | 32 bits | Last sequence number received |
| Interarrival Jitter | 32 bits | Estimated jitter (timestamp units) |
| LSR | 32 bits | Last SR timestamp received |
| DLSR | 32 bits | Delay since receiving that SR |

### Fraction Lost Calculation

```
Expected = Extended_Highest_Seq - Previous_Highest_Seq
Received = Actual packets arrived
Fraction_Lost = (Expected - Received) / Expected
```

Example: 100 packets expected, 97 received = 3% loss

### Jitter Calculation

Jitter estimates the variance in packet arrival times:

```
D(i) = Arrival_Time(i) - Departure_Time(i)
Jitter = Jitter_prev + (|D(i) - D(i-1)| - Jitter_prev) / 16
```

This is an exponentially weighted moving average of interarrival variance.

🔧 **NOC Tip:** For G.711, jitter values above 50ms indicate network congestion. Values above 150ms cause noticeable quality degradation. Values above 300ms make VoIP unusable.

---

## RTCP Interval

RTCP packets are sent periodically, not per-RTP packet:

| Participants | Typical RTCP Interval |
|--------------|----------------------|
| 2 | Every 5 seconds |
| 10 | Every 10 seconds |
| 100 | Every 30 seconds |
| 1000+ | Every minute or more |

**Why not more frequently?**
- RTCP uses bandwidth (typically ~5% of session bandwidth)
- More participants = longer intervals to limit total RTCP traffic

---

## RTCP-XR: Extended Reports

Standard RTCP provides high-level metrics. RTCP-XR provides per-call, per-interval granularity:

| Report Block | Metric |
|--------------|--------|
| Loss RLE | Which exact packets were lost |
| Duplicate RLE | Which packets arrived twice |
| Packet Receipt Times | Precise receive timestamps |
| Receiver Reference Time | NTP clock for synchronization |
| DLRR | Detailed round-trip reports |
| Statistics Summary | MOS, R-factor estimates |

### MOS from RTCP-XR

RTCP-XR can include estimated Mean Opinion Score:

```
R-factor = 93.2 - I_d (delay) - I_e (equipment) - I_eff (packet loss)
MOS = 1 + 0.035*R + 7*10^-6*R*(R-60)*(100-R)  [for R < 100]
```

This maps network quality to the 1-5 MOS scale.

🔧 **NOC Tip:** Telnyx voice quality dashboards use RTCP-XR data when available. If you see "N/A" for some calls, the endpoint doesn't support RTCP-XR. Legacy equipment often lacks this feature.

---

## Monitoring RTCP in Production

### Wireshark Analysis

```bash
# Filter for RTCP packets
tshark -r capture.pcap -Y "rtcp"

# Extract sender reports
tshark -r capture.pcap -Y "rtcp.pt == 200" -T fields -e rtcp.fractionlost
```

### Telnyx Quality Dashboards

In Grafana, quality metrics come from RTCP analysis:

```
voice.quality.rtcp_loss_fraction
voice.quality.rtcp_jitter_ms
voice.quality.estimated_mos
```

### Correlating with Call Issues

When a customer reports quality issues:

1. Find the call in quality dashboards
2. Check RTCP metrics for both legs
3. Compare: Did both sides report loss, or just one?
4. If asymmetric: likely routing/NAT/firewall issue
5. If symmetric: likely network congestion or codec issue

🔧 **NOC Tip:** One-way RTCP reports (only sender→receiver shows loss) often indicate asymmetric routing — a classic sign of NAT or firewall misconfiguration.

---

## RTCP and Call Diagnostics

### Round-Trip Time (RTT) from RTCP

```
RTT = Reception_Report_Time - LSR - DLSR
```

This gives end-to-end RTT without needing ICMP.

### Identifying Network Segments

By analyzing RTCP from multiple points:
- A-leg endpoint RTCP shows last-mile quality
- B-leg endpoint RTCP shows their last-mile
- B2BUA RTCP shows core network quality

Quality degradation at only one point isolates the problem segment.

---

## Key Takeaways

1. **RTCP provides quality feedback** that RTP lacks — loss, jitter, RTT metrics
2. **Sender Reports (SR)** include NTP timestamps for synchronization
3. **Receiver Reports (RR)** contain fraction lost, jitter, and round-trip calculations
4. **RTCP interval** scales with participant count — larger conferences = less frequent reports
5. **RTCP-XR** provides extended metrics including MOS estimates and per-packet data
6. **Asymmetric RTCP** (one side reports issues, other doesn't) points to routing or NAT problems

---

**Next: Lesson 31 — SIP Registration and Authentication Flow**
