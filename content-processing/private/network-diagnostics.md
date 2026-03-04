---
content_type: complete
description: "Learn about network diagnostics \u2014 traceroute, mtr, and path analysis"
difficulty: Advanced
duration: 7 minutes
lesson: '53'
module: 'Module 1: Foundations'
objectives:
- "Understand network diagnostics \u2014 traceroute, mtr, and path analysis"
public_word_count: 203
slug: network-diagnostics
title: "Network Diagnostics \u2014 Traceroute, MTR, and Path Analysis"
total_word_count: 290
---



## Why Path Analysis Matters for VoIP

In Lesson 50, you learned to isolate which call leg has the quality problem. Once you know the leg, you need to find **where** on the network path the degradation occurs. That's where traceroute and MTR come in.

VoIP is uniquely sensitive to network path issues. A web page tolerates 200ms of latency and 2% packet loss. A voice call becomes unusable under those same conditions. Path analysis tools help you pinpoint the exact hop where things go wrong.

---

## Traceroute Fundamentals

### How TTL-Based Tracing Works

Traceroute exploits the **Time-To-Live (TTL)** field in the IP header:

1. Send a packet with TTL=1. The first router decrements TTL to 0, drops the packet, and sends back an ICMP "Time Exceeded" message.
2. Send a packet with TTL=2. The second router sends back the ICMP reply.
3. Repeat, incrementing TTL, until you reach the destination.

```bash
# Basic traceroute (ICMP on macOS/Windows, UDP on Linux)
traceroute 198.51.100.25

# Force ICMP mode (useful when UDP is filtered)
traceroute -I 198.51.100.25

# Use TCP SYN on port 5060 (SIP) — gets through most firewalls
traceroute -T -p 5060 198.51.100.25
```

**Example output:**

```
traceroute to 198.51.100.25, 30 hops max, 60 byte packets
 1  gw.telnyx.chi (10.0.0.1)      0.5 ms   0.4 ms   0.4 ms
 2  core-rtr1.chi (203.0.113.1)   1.2 ms   1.1 ms   1.2 ms
 3  transit-peer.example.net      5.8 ms   5.7 ms   5.9 ms
 4  * * *
 5  edge-rtr.carrier.co.uk       78.2 ms  78.1 ms  78.3 ms
 6  198.51.100.25                 79.0 ms  78.8 ms  79.1 ms
```

### Reading Traceroute Output

Each line shows three RTT measurements. Look for:

- **Sudden RTT jumps** — A jump from 5ms to 78ms between hops 3 and 5 likely indicates an ocean crossing (expected) or congestion (investigate).
- **Stars (`* * *`)** — The router at hop 4 didn't respond to ICMP. This is NOT necessarily a problem (see below).
- **Consistent high RTT** — If every hop after hop 3 shows high latency, the issue is at or before hop 3.


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