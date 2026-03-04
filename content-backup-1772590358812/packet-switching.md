---
title: "Packet Switching — Store-and-Forward and Statistical Multiplexing"
description: "Learn about packet switching — store-and-forward and statistical multiplexing"
module: "Module 1: Foundations"
lesson: "12"
difficulty: "Intermediate"
duration: "7 minutes"
objectives:
  - Understand Packet switching sends data as independent packets sharing bandwidth — far more efficient than circuit switching's dedicated channels, but with no quality guarantees
  - Understand Statistical multiplexing is the efficiency breakthrough: bandwidth is allocated on demand, allowing 2-3× more calls on the same capacity — but it fails during traffic spikes
  - Understand Jitter arises from variable queuing, path changes, and serialization delay — it's inherent to packet switching and doesn't exist in circuit switching
  - Understand Router queue utilization increases delay exponentially as it approaches capacity — keep real-time traffic links below 70-80% utilization
  - Understand IP's best-effort delivery (no guarantees on delivery, timing, or ordering) is the fundamental challenge that all VoIP technology exists to overcome
slug: "packet-switching"
---

## The Revolutionary Idea

In Lesson 2, we saw that circuit switching reserves a dedicated 64 kbps channel for the entire duration of a call — even during silence. This guarantees quality but wastes capacity. In the 1960s, researchers at ARPA, NPL, and RAND independently arrived at a radical alternative: **what if we chopped data into small pieces, sent them independently, and let the network figure out how to deliver them?**

This is packet switching, and it's the foundation of the entire internet — including every VoIP call that traverses it.

## Store-and-Forward vs. Cut-Through

Packet-switched networks use **store-and-forward** at each hop:

1. A packet arrives at a router
2. The router receives the **entire** packet and stores it in a buffer
3. The router examines the header to determine the next hop
4. The router forwards the packet to the next hop
5. Repeat until the packet reaches its destination

This is fundamentally different from circuit switching, where the electrical signal flows continuously through pre-established connections. Each hop in a packet network introduces **processing delay** (examining headers), **queuing delay** (waiting behind other packets), and **serialization delay** (time to push all bits onto the outgoing link).

**Cut-through switching** is an optimization used in some Ethernet switches: the switch starts forwarding the packet as soon as it reads the destination address, before receiving the entire frame. This reduces latency but can't detect corrupted frames (no FCS check). It's relevant at Layer 2 but not at Layer 3 (routers always store-and-forward because they may need to modify headers, check TTL, etc.).

## Statistical Multiplexing — The Efficiency Breakthrough

The killer advantage of packet switching is **statistical multiplexing**: bandwidth is shared among all users and allocated **on demand** rather than reserved.

Consider 10 voice calls, each generating 64 kbps when active. In circuit switching, you need 10 × 64 kbps = 640 kbps of reserved bandwidth, regardless of whether all callers are speaking simultaneously.

In reality, in a typical phone conversation, each party speaks only about 35-40% of the time (considering pauses, listening, and silence). With Voice Activity Detection (Lesson 7), a packet-switched network only sends data when someone is actually speaking.

With statistical multiplexing:
- 10 calls × 64 kbps × 0.4 activity factor = **256 kbps average** (vs. 640 kbps reserved)
- That's a 60% bandwidth savings — or equivalently, the same bandwidth can carry 2.5× more calls

The larger the number of users sharing the link, the more reliable this statistical averaging becomes (law of large numbers). A backbone link carrying 10,000 calls benefits far more from statistical multiplexing than a link carrying 10.

**The catch**: Statistical multiplexing assumes that not everyone talks at once. When they do — during traffic spikes or abnormal patterns — the shared bandwidth becomes congested. This is the fundamental source of **packet loss** and **jitter** in VoIP.

## Why Packet Switching Introduces Jitter

In circuit switching, every sample traverses the same physical path with the same delay. Packet switching destroys this predictability in several ways:

**Variable queuing delay**: Each router has finite buffer space. When multiple packets arrive simultaneously, they're queued and forwarded sequentially. A packet arriving at an empty queue has zero queuing delay; a packet arriving behind 50 others might wait milliseconds.

**Variable path**: While most packets in a flow follow the same route (determined by routing tables), changes in routing — due to link failures, load balancing (ECMP), or route convergence — can send packets along different paths with different delays.

**Variable serialization**: The time to serialize a packet onto a link depends on the link speed. More importantly, a small voice packet might be stuck behind a large data packet (1500-byte email attachment) waiting to serialize — this is called **head-of-line blocking**.

The result: packets sent at perfectly regular 20 ms intervals arrive at irregular intervals. This variation is **jitter**, and managing it is a central challenge of VoIP (Lessons 33-34).

> **💡 NOC Tip:** en you see jitter in RTCP reports, understand that it reflects the *cumulative* variable delay across the entire path — every router, every link, every congestion point. You can't determine *where* the jitter originates from RTCP alone. To pinpoint the source, you need tools like MTR (Lesson 51) or path analysis to identify which hop introduces the most delay variation.

## Queuing Theory Basics

Every router port has a buffer (queue) where packets wait when the outgoing link is busy. Understanding basic queuing behavior helps explain network performance:

**Utilization**: As a link's utilization approaches 100%, queuing delay increases **exponentially**, not linearly. A link at 50% utilization has mild queuing; at 90%, queuing is severe; at 99%, it's catastrophic. This is why networks are engineered to keep utilization below 70-80% for real-time traffic.

**Buffer size**: Larger buffers reduce packet loss (fewer dropped packets when the buffer fills) but increase delay (packets wait longer). This is the "bufferbloat" problem — large buffers that prevent loss but add unacceptable latency.

**Priority queuing**: By classifying traffic and serving high-priority queues first, routers can give voice traffic lower delay even when the link is congested. This is the basis of QoS (Lesson 11).

## Best-Effort Delivery — The Fundamental Challenge

IP networks provide **best-effort** delivery: they'll try to deliver your packet, but they make no guarantees about:
- **Delivery**: Packets can be dropped if buffers overflow
- **Timing**: Packets can be delayed indefinitely
- **Ordering**: Packets can arrive out of sequence
- **Duplication**: Packets can be delivered more than once

For web browsing and email, this is fine — TCP handles retransmission and ordering. For real-time voice, it's a serious problem:

- **Dropped packets** = missing audio (PLC can mask some loss, but not much)
- **Delayed packets** = if they arrive too late for the jitter buffer, they're useless
- **Reordered packets** = the jitter buffer must sort them, potentially treating late ones as lost
- **No congestion feedback** = UDP doesn't know the network is congested (unlike TCP)

Every QoS mechanism, jitter buffer algorithm, and error concealment technique in VoIP exists because of these fundamental properties of packet switching.

## A Real Troubleshooting Scenario

**Scenario:** A Telnyx customer on a shared office internet connection reports that call quality degrades specifically during the 5-minute window around 2:00 PM daily.

**Analysis:**
- 2:00 PM correlates with an automated cloud backup that saturates their upload bandwidth
- During the backup, the router's egress queue fills with backup data packets
- Voice packets get queued behind large data packets, experiencing variable delay (jitter)
- When the buffer fills completely, packets are dropped — including voice packets
- Statistical multiplexing breaks down because one application (backup) is consuming all the shared capacity

**What you'd see:**
- RTCP reports show jitter spikes and packet loss during the 2:00 PM window
- MOS drops to 2.5-3.0 during the window, then recovers
- The pattern repeats daily with mechanical precision

**Resolution:**
1. Reschedule backups to off-hours
2. Rate-limit backup traffic to leave headroom for voice
3. Implement QoS to prioritize voice packets over backup traffic
4. Separate voice and data onto different internet connections (SD-WAN)

> **💡 NOC Tip:** me-of-day quality patterns are almost always caused by competing traffic. Daily patterns suggest scheduled tasks (backups, updates, syncs). Weekly patterns suggest business activity cycles. If the degradation window is identical every day (same time, same duration), look for automated processes. If it varies but correlates with business hours, it's general congestion.

---

**Key Takeaways:**
1. Packet switching sends data as independent packets sharing bandwidth — far more efficient than circuit switching's dedicated channels, but with no quality guarantees
2. Statistical multiplexing is the efficiency breakthrough: bandwidth is allocated on demand, allowing 2-3× more calls on the same capacity — but it fails during traffic spikes
3. Jitter arises from variable queuing, path changes, and serialization delay — it's inherent to packet switching and doesn't exist in circuit switching
4. Router queue utilization increases delay exponentially as it approaches capacity — keep real-time traffic links below 70-80% utilization
5. IP's best-effort delivery (no guarantees on delivery, timing, or ordering) is the fundamental challenge that all VoIP technology exists to overcome

**Next: Lesson 11 — Quality of Service (QoS) — DSCP, Traffic Shaping, and Why It Mostly Doesn't Work on the Internet**
