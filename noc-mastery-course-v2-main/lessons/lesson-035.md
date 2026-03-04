# Lesson 35: Jitter — Why Packets Arrive at Irregular Intervals
**Module 1 | Section 1.9 — Jitter, Latency, and Call Quality**
**⏱ ~8 min read | Prerequisites: Lesson 32**

---

In Lesson 32, we broke down the latency budget and saw that queuing delay is variable. That variability has a name: **jitter**. While latency tells you how long packets take to arrive, jitter tells you how *consistently* they arrive. And for real-time audio, consistency matters as much as speed.

## What Jitter Actually Is

A VoIP endpoint sends RTP packets at regular intervals — every 20ms for a standard configuration. If the network were perfect, they'd arrive every 20ms. In reality, some arrive in 18ms, some in 25ms, some in 42ms. Jitter is the variation in these interarrival times.

Formally, RFC 3550 defines **interarrival jitter** as a smoothed estimate of the variance:

```
J(i) = J(i-1) + (|D(i-1,i)| - J(i-1)) / 16
```

Where `D(i-1,i)` is the difference in relative transit time between consecutive packets. The `/16` smoothing factor makes this a running average that responds to changes but doesn't overreact to single outliers.

In plain terms: if packets are supposed to arrive every 20ms, and the actual intervals are 18, 22, 19, 45, 20, 21 — that spike to 45ms is jitter. The audio system expected a packet at 20ms but it arrived at 45ms, creating a gap that must be filled with silence or interpolation.

## Why Jitter Happens

### Network Queuing Variation

The primary cause. When a voice packet arrives at a router, it may be the only packet in the queue (fast forwarding) or it may be behind a burst of data packets (significant delay). The next voice packet may arrive at the router during a quiet period and get forwarded instantly.

This variation is inherent to packet-switched networks with shared resources. It's the fundamental tradeoff discussed in Lesson 10 — statistical multiplexing gains efficiency at the cost of timing predictability.

### Route Changes

BGP route changes (Lesson 23-25) or ECMP load balancing can suddenly shift packets to a different path with different latency characteristics. Even within a single provider's network, internal routing changes cause transient jitter spikes.

### CPU Contention on Network Devices

Software-based routers, firewalls, or NAT gateways under CPU load process packets with variable delay. If a firewall is doing deep packet inspection on a data flow while your voice packet is in its queue, that voice packet waits.

### Wireless and Access Networks

WiFi introduces significant jitter due to:
- **Contention-based access** (CSMA/CA): the device waits for a clear channel
- **Retransmissions** at Layer 2 (WiFi retries corrupted frames)
- **Power-saving modes**: devices sleep and batch-receive packets

LTE/5G networks add jitter from scheduling, handovers, and radio condition variation.

### Virtualization and Container Scheduling

In cloud environments, virtual machines and containers share physical CPUs. The hypervisor's scheduler introduces micro-bursts of delay when a VM is preempted. This affects Telnyx's own infrastructure — media processing containers running on shared infrastructure can exhibit jitter caused by noisy neighbors.

🔧 **NOC Tip:** When you see jitter on calls that traverse Telnyx's own infrastructure, check if the media server pod is on a node with high CPU utilization. Container scheduling jitter looks different from network jitter — it's characterized by regular, periodic spikes rather than random variation.

## Measuring Jitter

### From RTCP Receiver Reports

As covered in Lesson 30, RTCP Receiver Reports include an interarrival jitter field. This is the RFC 3550 smoothed estimate and is reported for each SSRC. In Grafana dashboards, this appears as a time series showing jitter over the call duration.

**What's normal?**
- < 10 ms: Excellent — no audible impact
- 10–30 ms: Acceptable — jitter buffer handles it easily
- 30–50 ms: Concerning — adaptive jitter buffer expanding, adding latency
- > 50 ms: Bad — likely causing audible artifacts

### From Packet Captures

In Wireshark, analyze an RTP stream: **Telephony → RTP → Stream Analysis**. This shows:
- **Delta (ms):** Time between consecutive packets (should be ~20ms for 20ms packetization)
- **Jitter (ms):** Running jitter calculation per RFC 3550
- **Packet arrival graph:** Visual display showing timing variation

Look for patterns:
- **Random jitter:** Normal network behavior, usually manageable
- **Periodic spikes:** Suggests a regular process interfering (garbage collection, cron jobs, routing updates)
- **Sustained high jitter:** Congestion or path quality issue
- **Sudden step change:** Route change or link failure/recovery

### Using Network Tools

`ping` with flood or interval options shows basic RTT jitter:
```bash
ping -i 0.02 -c 1000 target_ip  # 20ms interval, 1000 packets
```

`mtr` (covered in Lesson 51) shows per-hop jitter statistics, helping pinpoint where jitter is introduced.

## Network Jitter vs. System Jitter

This distinction matters enormously for NOC troubleshooting:

**Network jitter** is introduced by the path between endpoints. It affects all packets proportionally and correlates with network congestion or path changes. You can verify by checking RTCP from both directions — network jitter usually affects one direction more than the other (the direction toward the congested link).

**System jitter** is introduced by the endpoints themselves — CPU scheduling, application processing delays, disk I/O blocking the network stack. System jitter manifests as irregular packet *sending* times, not just irregular arrival times.

To distinguish them:
1. Capture packets **at the sender** and **at the receiver**
2. If packets leave the sender at irregular intervals → system jitter at the sender
3. If packets leave regularly but arrive irregularly → network jitter
4. If packets arrive irregularly at the Telnyx media server but the carrier-side RTCP shows low jitter → the jitter is between the customer and Telnyx, not on the carrier leg

🔧 **NOC Tip:** When a customer reports choppy audio and you see high jitter in RTCP, the first question is: which leg? Check both the customer-facing leg and the carrier-facing leg independently. If jitter is only on the customer leg, it's likely their last-mile network — WiFi, congested broadband, or VPN overhead.

## Real Troubleshooting Scenario: Periodic Audio Gaps Every 30 Seconds

**Symptom:** Customer hears brief audio dropouts approximately every 30 seconds.

**Investigation:**
1. Pull RTCP data for the call — jitter shows periodic spikes every ~30 seconds
2. Pull PCAP — RTP delta graph shows clusters of late packets every 30s
3. The pattern is too regular to be network congestion

**Root cause:** The customer's router runs a cron job every 30 seconds (DHCP lease check, log rotation, DNS cache flush) that briefly monopolizes the CPU, delaying packet forwarding.

**Resolution:** Recommended the customer move VoIP traffic to a dedicated VLAN with QoS priority on their router, or replace their consumer router with one that handles background tasks without impacting forwarding.

## Real Troubleshooting Scenario: Jitter Spikes During Business Hours

**Symptom:** Call quality degrades between 9am-5pm, fine evenings and weekends.

**Investigation:**
1. Grafana dashboard shows jitter increasing during business hours across multiple customers in the same region
2. Not specific to one customer — affecting a geographic cluster
3. Correlates with a specific transit provider's congestion

**Root cause:** A transit link between two carriers was undersized for peak-hour traffic. Voice packets queued behind bulk data transfers.

**Resolution:** Telnyx's network engineering team shifted traffic to an alternate peering path for that region.

## The Jitter-Latency Tradeoff

Here's the fundamental tension: to absorb jitter, you add a jitter buffer, which adds latency. High jitter forces a larger buffer, which pushes toward the latency threshold. A call with 50ms of jitter might need a 70ms jitter buffer, adding 70ms to the latency budget from Lesson 32. If the path already has 130ms of other delay, the total hits 200ms — above the "excellent" threshold.

This is why jitter reduction is as important as latency reduction. It's not enough to have a fast path — you need a *consistent* path.

---

**Key Takeaways:**
1. Jitter is the variation in packet interarrival times — it's the inconsistency that damages audio quality
2. Primary causes: network queuing variation, route changes, CPU contention, wireless access, and container scheduling
3. RFC 3550 defines the smoothed jitter calculation used in RTCP reports — < 10ms is excellent, > 50ms is problematic
4. Distinguish network jitter (path-induced) from system jitter (endpoint-induced) by capturing at both sender and receiver
5. Periodic jitter patterns suggest a regular process or scheduled task interfering with packet forwarding
6. Jitter forces larger jitter buffers, which add latency — there's a direct tradeoff between jitter tolerance and delay

**Next: Lesson 34 — The Jitter Buffer: Smoothing Out Packet Arrival Variation**
