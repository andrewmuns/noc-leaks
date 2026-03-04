---
content_type: truncated
description: "Learn about ipv4 \u2014 addressing, subnetting, and the ip header"
difficulty: Intermediate
duration: 8 minutes
full_content_available: true
lesson: '15'
module: 'Module 1: Foundations'
objectives:
- Understand The IPv4 header's key fields for NOC work are TTL (path length, loop
  detection), Protocol (TCP/UDP), DSCP (QoS marking), and the fragmentation fields
- "Understand CIDR subnetting divides addresses into network and host portions \u2014\
  \ quick mental math helps instantly identify misconfigurations"
- Understand RFC 1918 private addresses in SIP headers or SDP always indicate NAT
  is involved; CGNAT (100.64.0.0/10) means double-NAT trouble
- Understand IP fragmentation is devastating for VoIP: "lost fragments kill entire\
    \ packets, firewalls drop non-initial fragments, and reassembly adds delay \u2014\
    \ use TCP for SIP to avoid it"
- Understand ICMP blocking breaks Path MTU Discovery and creates silent black holes;
  never block ICMP indiscriminately in voice networks
slug: ipv4-networking
title: "IPv4 \u2014 Addressing, Subnetting, and the IP Header"
word_limit: 300
---

## The IP Header: Field by Field

Every packet that crosses the internet carries an IPv4 header. As a NOC engineer, you'll read these headers in Wireshark daily. Let's understand every field that matters.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |    DSCP   |ECN|         Total Length          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Version (4 bits):** Always 4 for IPv4. This is how a router knows whether it's looking at v4 or v6.

**IHL — Internet Header Length (4 bits):** Length of the header in 32-bit words. Minimum is 5 (20 bytes, no options). If options are present, this grows.

**DSCP (6 bits):** The QoS marking we covered in Lesson 11. EF (46) for voice RTP, AF31 for SIP signaling.

**Total Length (16 bits):** Entire packet size including header and payload. Maximum 65,535 bytes, though practical packets are limited by MTU (typically 1500 at Ethernet).

**Identification, Flags, Fragment Offset:** The fragmentation trio. We'll cover these in detail below — they're critical for VoIP troubleshooting.

**Time to Live — TTL (8 bits):** Decremented by 1 at each router hop. When it hits 0, the router drops the packet and sends an ICMP Time Exceeded message. This prevents routing loops from causing infinite packet circulation. It's also what makes `traceroute` work.

> **💡 NOC Tip:** L values in packet captures reveal the path length. Most operating systems start with TTL 64 (Linux), 128 (Windows), or 255 (network equipment). If you see a packet arrive with TTL 52,

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*