---
content_type: truncated
description: Learn about packet reordering, duplication, and their impact
difficulty: Advanced
duration: 6 minutes
full_content_available: true
lesson: '38'
module: 'Module 1: Foundations'
objectives:
- "Understand Packet reordering occurs due to ECMP, link aggregation, route changes,\
  \ and parallel processing \u2014 mild reordering is absorbed by the jitter buffer,\
  \ severe reordering becomes effective loss"
- Understand Packet duplication is rare and usually caused by network equipment bugs,
  mirrored ports, or redundancy protocol failures
- Understand Duplicated packets are generally harmless to audio but waste bandwidth
  and can skew metrics
- Understand Reordering in PCAPs appears as sequence number inversions; duplication
  appears as repeated sequence numbers
- Understand When impairment patterns don't fit typical congestion (loss without jitter,
  or anomalous bandwidth), check for reordering and duplication
slug: packet-reordering
title: Packet Reordering, Duplication, and Their Impact
word_limit: 300
---

Packet loss and jitter dominate VoIP troubleshooting discussions, but there are two less common impairments that can be equally confusing: reordering and duplication. They're rare enough that engineers forget to check for them, but when they occur, they produce baffling symptoms.

## Packet Reordering

### What Happens

Packets sent in order 1, 2, 3, 4, 5 arrive as 1, 2, 4, 3, 5. Packet 3 arrives *after* packet 4. In a jitter buffer, this can play out two ways:

1. **Mild reordering (within buffer depth):** Packet 4 arrives, packet 3 arrives before packet 3's playout time. The jitter buffer sorts them correctly. No audible impact.

2. **Severe reordering (exceeds buffer depth):** Packet 4 arrives, packet 3's playout time passes (the buffer plays silence or PLC), then packet 3 arrives too late. It's treated as lost. From the audio perspective, this is identical to packet loss.

### Why Reordering Happens

**ECMP (Equal-Cost Multi-Path) Routing:** When multiple equal-cost paths exist to a destination, routers distribute packets across them. If the hash function assigns consecutive packets to different paths with different latencies, they arrive out of order.

Most ECMP implementations hash on the 5-tuple (src IP, dst IP, src port, dst port, protocol) to keep a single flow on a single path. But some implementations hash per-packet or use hash collisions that split a flow.

**Link Aggregation (LAG):** Similar to ECMP — multiple physical links bonded together. If the hashing sends consecutive packets over different member links with different queue depths, reordering occurs.

**Route Changes:** A BGP route change mid-stream can cause packets already in the old path's pipeline to arrive after packets sent on the new path.

**Parallel Processing:** Some network devices (load balancers, DPI systems) use multiple processing cores. If consecutive packets are handled by different cores with different processing times, they exit out

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*