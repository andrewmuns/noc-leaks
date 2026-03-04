---
title: "Quality of Service (QoS) — DSCP, Traffic Shaping, and Why It Mostly Doesn't Work on the Internet"
description: "Learn about quality of service (qos) — dscp, traffic shaping, and why it mostly doesn't work on the internet"
module: "Module 1: Foundations"
lesson: "13"
difficulty: "Intermediate"
duration: "7 minutes"
objectives:
  - Understand DSCP markings (especially EF/46 for voice) tell routers to prioritize packets, but only work within managed network boundaries
  - Understand QoS mechanisms (priority queuing, WFQ, LLQ) require every hop to participate — a single best-effort link breaks the chain
  - Understand DSCP markings are stripped at internet peering points because there's no trust or commercial agreement to honor them
  - Understand Overprovisioning is the practical alternative to QoS on the public internet — build enough capacity that congestion is rare
  - Understand Telnyx's private backbone and peering strategy provide QoS-like behavior for traffic within its network; the customer last mile is almost always the weakest link
slug: "qos-limitations"
---

## The Promise of QoS

In Lesson 10, we learned that packet switching introduces variable delay (jitter), packet loss, and reordering — all enemies of real-time voice. Quality of Service (QoS) is the set of techniques designed to fight back: giving voice packets priority treatment so they experience low, consistent delay even when the network is congested.

The core idea is simple: **not all packets are equal.** A voice packet that arrives 300ms late is useless. An email packet that arrives 300ms late is unnoticeable. QoS mechanisms let routers and switches distinguish between traffic types and treat them accordingly.

## DSCP: Marking Packets with Priority

Every IPv4 packet has an 8-bit **Type of Service (ToS)** field in its header. The modern interpretation of this field is **Differentiated Services (DiffServ)**, which uses the first 6 bits as the **Differentiated Services Code Point (DSCP)**.

DSCP values tell routers how to handle the packet. The most important markings for telecom:

| DSCP Value | Name | Decimal | Use Case |
|-----------|------|---------|----------|
| 101110 | EF (Expedited Forwarding) | 46 | Voice media (RTP) |
| 011000 | AF31 | 26 | Voice signaling (SIP) |
| 100010 | AF41 | 34 | Video conferencing |
| 000000 | BE (Best Effort) | 0 | Everything else |

**Expedited Forwarding (EF, DSCP 46)** is the gold standard for voice. It means: "Give this packet low latency, low jitter, low loss, and guaranteed bandwidth." Routers that honor EF place these packets in a priority queue that gets serviced before all other queues.

> **💡 NOC Tip:** en troubleshooting call quality, always verify DSCP markings in packet captures. Look at the IP header's DSCP field. If voice packets are marked as Best Effort (DSCP 0) instead of EF (DSCP 46), that's a strong clue — they're getting no priority treatment anywhere in the network.

## How QoS Actually Works: Queuing and Scheduling

DSCP markings are just labels. The real work happens in router **queuing disciplines**:

### Priority Queuing (Strict Priority)
EF-marked packets go into a priority queue that's always serviced first. This gives minimal latency but risks **queue starvation** — if there's too much priority traffic, everything else stops.

### Weighted Fair Queuing (WFQ)
Traffic classes get proportional bandwidth. Voice might get 30%, signaling 10%, best-effort 60%. Even under congestion, each class gets its guaranteed share.

### Class-Based Weighted Fair Queuing (CBWFQ) with Low Latency Queuing (LLQ)
The most common enterprise deployment: a strict priority queue for voice (LLQ) combined with weighted queues for everything else. Voice gets absolute priority up to a configured limit (policed to prevent abuse), and remaining bandwidth is shared.

## Traffic Shaping vs. Traffic Policing

These terms sound similar but behave very differently:

**Traffic Policing** drops or re-marks packets that exceed a rate limit. It's harsh — excess packets are simply discarded. Used at network boundaries to enforce contracts.

**Traffic Shaping** buffers excess packets and releases them at a controlled rate. It's gentler — packets are delayed rather than dropped. Used on egress to smooth bursty traffic.

For voice, **policing is preferred over shaping** for the priority queue. Why? Because shaping adds buffer delay, and for voice, a delayed packet is often as bad as a lost one. Better to police the voice queue (drop excess) and ensure legitimate voice traffic gets through immediately.

## Why QoS Doesn't Work on the Public Internet

Here's the uncomfortable truth: **DSCP markings are almost always stripped or re-marked at internet peering points.**

Why? Because QoS requires **trust**. If ISP-A honors DSCP markings from ISP-B's customers, then ISP-B's customers could mark ALL their traffic as EF and get priority treatment for free. There's no commercial incentive for ISP-A to honor markings they didn't set.

The result: the moment your voice packets leave your managed network and enter the public internet, their DSCP markings become meaningless. They're treated as best-effort traffic, competing with Netflix streams, Windows updates, and everything else.

This is a fundamental architectural reality. QoS works within **trust boundaries** — your enterprise LAN, your MPLS WAN, your carrier's backbone. It breaks down at every boundary where there's no commercial agreement to honor markings.

### The Real-World Troubleshooting Scenario

**Scenario:** A customer reports choppy audio on calls. Their IT team proudly shows you their QoS configuration: voice VLANs with DSCP EF marking, priority queuing on all internal switches. Everything looks perfect.

But the calls are going over a standard internet connection to Telnyx. The DSCP markings are stripped at their ISP's first router. On the internet, those voice packets fight for bandwidth with everything else.

**The fix isn't more QoS — it's overprovisioning.** The customer needs enough bandwidth that congestion rarely occurs, or they need a dedicated connection (MPLS, SD-WAN with a quality overlay, or direct peering).

> **💡 NOC Tip:** en customers claim "we have QoS configured" but still have quality issues, ask: "Where does the traffic travel? QoS only works end-to-end if every hop honors it. On the public internet, it doesn't."

## Overprovisioning: The Practical Alternative

Since QoS fails on the internet, the real solution for most paths is **overprovisioning** — having so much bandwidth that congestion is rare. This is why backbone providers build massive capacity. A 100 Gbps backbone carrying 40 Gbps of traffic rarely has congestion, so QoS markings are unnecessary.

This works surprisingly well for core internet paths. The congestion problems typically happen at:

1. **The customer's last mile** — their internet connection to their ISP
2. **Peering points** — where ISPs exchange traffic (can be congested during peak hours)
3. **Access networks** — shared cable/DSL segments in residential areas

## How Telnyx's Private Backbone Provides QoS-Like Behavior

Telnyx operates its own global private network backbone connecting data centers, Points of Presence (PoPs), and carrier interconnection points. This is a critical advantage:

1. **Within the Telnyx backbone:** Traffic is managed end-to-end. Voice packets can receive priority treatment because Telnyx controls every router and switch.
2. **Peering relationships:** Telnyx peers directly with major carriers and ISPs at Internet Exchange Points. Direct peering means fewer hops and no transit provider middlemen stripping markings.
3. **Overprovisioned capacity:** The backbone is built with headroom, so even best-effort treatment provides excellent performance.

The combination of these approaches means that the segment from a customer's network to Telnyx's PoP is the most critical. Once traffic is on Telnyx's network, quality is well-managed.

> **💡 NOC Tip:** en investigating quality issues, focus on the path between the customer and the nearest Telnyx PoP. Use `mtr` to the customer's SIP endpoint — that's where the problems almost always are. The Telnyx backbone segment rarely causes quality issues.

## QoS Where It Still Matters

Even though internet QoS is largely ineffective, QoS configuration remains critical in three places:

1. **Customer LANs:** Prioritizing voice over internal traffic prevents their own network from degrading calls. A large file transfer shouldn't starve the phones.

2. **SD-WAN overlays:** Modern SD-WAN solutions create managed tunnels over internet paths, applying QoS within the tunnel. They can also steer voice to the best-performing path in real-time.

3. **Private/MPLS WAN connections:** Enterprises with MPLS circuits between sites get true end-to-end QoS because the carrier manages the entire path.

## Connecting the Dots

QoS teaches us a broader lesson about network architecture: **you can only control what you manage.** The internet is a collection of independently operated networks with no unified quality guarantee. This is why Telnyx invests in its own backbone, peers at major exchanges, and monitors path quality obsessively.

Understanding QoS also explains why customer last-mile issues are the #1 source of call quality complaints. It's the one segment that's almost always unmanaged, oversubscribed, and QoS-unaware.

---

**Key Takeaways:**
1. DSCP markings (especially EF/46 for voice) tell routers to prioritize packets, but only work within managed network boundaries
2. QoS mechanisms (priority queuing, WFQ, LLQ) require every hop to participate — a single best-effort link breaks the chain
3. DSCP markings are stripped at internet peering points because there's no trust or commercial agreement to honor them
4. Overprovisioning is the practical alternative to QoS on the public internet — build enough capacity that congestion is rare
5. Telnyx's private backbone and peering strategy provide QoS-like behavior for traffic within its network; the customer last mile is almost always the weakest link

**Next: Lesson 12 — Ethernet and Layer 2: Frames, MACs, VLANs, and Switching**
