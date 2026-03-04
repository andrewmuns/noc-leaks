---
content_type: complete
description: "Learn about quality of service (qos) \u2014 dscp, traffic shaping, and\
  \ why it mostly doesn't work on the internet"
difficulty: Intermediate
duration: 7 minutes
lesson: '13'
module: 'Module 1: Foundations'
objectives:
- Understand DSCP markings (especially EF/46 for voice) tell routers to prioritize
  packets, but only work within managed network boundaries
- "Understand QoS mechanisms (priority queuing, WFQ, LLQ) require every hop to participate\
  \ \u2014 a single best-effort link breaks the chain"
- Understand DSCP markings are stripped at internet peering points because there's
  no trust or commercial agreement to honor them
- "Understand Overprovisioning is the practical alternative to QoS on the public internet\
  \ \u2014 build enough capacity that congestion is rare"
- Understand Telnyx's private backbone and peering strategy provide QoS-like behavior
  for traffic within its network; the customer last mile is almost always the weakest
  link
public_word_count: 299
slug: qos-limitations
title: "Quality of Service (QoS) \u2014 DSCP, Traffic Shaping, and Why It Mostly Doesn't\
  \ Work on the Internet"
total_word_count: 373
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

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios
- ✅ Practice quizzes and assessments

[**🚀 Unlock Full Course Access**](https://teleponymastery.com/enroll)

---

*Preview shows approximately 25% of the full lesson content.*