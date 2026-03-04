---
title: "Packet Reordering, Duplication, and Their Impact"
description: "Learn about packet reordering, duplication, and their impact"
module: "Module 1: Foundations"
lesson: "38"
difficulty: "Advanced"
duration: "6 minutes"
objectives:
  - Understand Packet reordering occurs due to ECMP, link aggregation, route changes, and parallel processing — mild reordering is absorbed by the jitter buffer, severe reordering becomes effective loss
  - Understand Packet duplication is rare and usually caused by network equipment bugs, mirrored ports, or redundancy protocol failures
  - Understand Duplicated packets are generally harmless to audio but waste bandwidth and can skew metrics
  - Understand Reordering in PCAPs appears as sequence number inversions; duplication appears as repeated sequence numbers
  - Understand When impairment patterns don't fit typical congestion (loss without jitter, or anomalous bandwidth), check for reordering and duplication
slug: "packet-reordering"
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

**Parallel Processing:** Some network devices (load balancers, DPI systems) use multiple processing cores. If consecutive packets are handled by different cores with different processing times, they exit out of order.

> **💡 NOC Tip:**  you see reordering affecting calls through a specific network path, check if that path uses ECMP or LAG. The fix is usually ensuring the hash function keeps RTP flows on a single path — which should happen naturally with 5-tuple hashing, but can fail if a load balancer or intermediate device changes the source port.

### Detecting Reordering

In Wireshark's RTP stream analysis, reordered packets appear as:
- A sequence number gap (looks like loss) followed by the "missing" packet arriving later
- The "Delta" column shows a very short interval for the late-arriving packet (it arrives immediately after the out-of-order packet, not after the expected 20ms)

Wireshark marks these as "Wrong sequence number" or shows them in the sequence number graph as backward jumps.

In RTCP reports, mild reordering is invisible (packets arrive within the jitter buffer's window). Severe reordering appears as packet loss because the late packets are discarded.

## Packet Duplication

### What Happens

The receiver gets the same packet twice — same sequence number, same timestamp, same payload. This is different from retransmission (which is intentional); duplication is an unintended network behavior.

### Why Duplication Happens

**Network Equipment Bugs:** Some switches and routers have bugs that duplicate packets under specific conditions (certain VLAN configurations, spanning tree reconvergence, firmware bugs).

**Port Mirroring Misconfiguration:** If a SPAN/mirror port is accidentally configured to copy traffic back into the network path instead of to a monitoring tool, packets get duplicated.

**Redundant Paths:** Certain redundancy protocols (like PRP — Parallel Redundancy Protocol used in industrial networks) intentionally send packets over two paths and deduplicate at the receiver. If deduplication fails, you get doubles.

**Application-Level Replay:** Some SIP proxies or media relays may accidentally forward a packet twice due to threading bugs or retry logic.

### Impact on VoIP

Duplicated RTP packets are usually harmless — the jitter buffer receives two copies of the same sequence number and discards the duplicate. The audio quality is unaffected.

However:
- **Bandwidth waste:** Every duplicated packet consumes bandwidth. On constrained links, this can push real traffic into congestion.
- **Jitter calculation confusion:** Some jitter buffer implementations may mishandle duplicates, causing incorrect jitter estimates or buffer sizing.
- **RTCP statistics skew:** Duplicate packets can make loss calculations appear better than reality (more packets received than expected).
- **Billing/CDR anomalies:** If packet counters are used for usage tracking, duplicates inflate counts.

### Detecting Duplication

In Wireshark: filter for RTP and sort by sequence number. Duplicates have identical sequence numbers and timestamps. The RTP stream analysis may flag them as "Seq Nr duplicate."

At the network level, if you see exactly double the expected packet rate (100 pps instead of 50 pps for a single G.711 stream), duplication is likely.

> **💡 NOC Tip:** plication is rare enough that it often gets missed. If a customer reports "normal" call quality but you see anomalous packet rates or bandwidth usage for voice traffic, check for duplicates before assuming there's extra traffic.

## Real Troubleshooting Scenario: Intermittent Audio Glitches on a Specific Route

**Symptom:** Calls between two specific offices experience occasional 60-80ms audio gaps. Loss appears low in RTCP.

**Investigation:**
1. RTCP shows < 0.5% loss — shouldn't cause audible issues
2. PCAP analysis reveals packets arriving out of order — sequence numbers 1000, 1001, 1003, 1002, 1004
3. The reordering is mild (1-2 packets) but occurs in bursts
4. Traceroute shows the path crosses a network segment with ECMP
5. The ECMP hash on an intermediate router is per-packet instead of per-flow

**Root cause:** Per-packet ECMP hashing causes mild but persistent reordering. Most reordered packets arrive within the jitter buffer window, but during jitter spikes, some arrive too late and are discarded.

**Resolution:** The network team at the intermediate provider reconfigured their ECMP hashing to use 5-tuple (per-flow) instead of per-packet distribution.

## Real Troubleshooting Scenario: Mysterious Bandwidth Spike

**Symptom:** Monitoring shows a sudden doubling of RTP bandwidth on a specific media server.

**Investigation:**
1. Call volume hasn't changed
2. Codec distribution hasn't changed
3. PCAP shows every RTP packet appears twice with identical sequence numbers
4. The duplication started after a network maintenance window

**Root cause:** During maintenance, a port mirror was configured on a switch for monitoring purposes. The mirror was configured to mirror traffic to a VLAN that routes back into the production path instead of an isolated monitoring port.

**Resolution:** Corrected the port mirror configuration to direct mirrored traffic to the isolated monitoring interface.

## Relationship to Other Impairments

Reordering, duplication, loss, and jitter are related:
- Severe reordering manifests as **loss** (late packets discarded by jitter buffer)
- Reordering also appears as **jitter** (some packets arrive earlier/later than expected)
- Duplication increases **bandwidth** consumption, potentially causing **congestion** and therefore **loss** and **jitter**
- The same root causes (ECMP, network device issues) can produce combinations of all four

When you see unusual combinations of impairments that don't quite fit the typical congestion pattern, consider reordering or duplication as underlying causes.

---

**Key Takeaways:**
1. Packet reordering occurs due to ECMP, link aggregation, route changes, and parallel processing — mild reordering is absorbed by the jitter buffer, severe reordering becomes effective loss
2. Packet duplication is rare and usually caused by network equipment bugs, mirrored ports, or redundancy protocol failures
3. Duplicated packets are generally harmless to audio but waste bandwidth and can skew metrics
4. Reordering in PCAPs appears as sequence number inversions; duplication appears as repeated sequence numbers
5. When impairment patterns don't fit typical congestion (loss without jitter, or anomalous bandwidth), check for reordering and duplication

**Next: Lesson 37 — SIP Architecture: Endpoints, Proxies, Registrars, and B2BUAs**
