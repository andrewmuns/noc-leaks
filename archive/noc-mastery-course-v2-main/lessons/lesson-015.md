# Lesson 15: IPv4 — Addressing, Subnetting, and the IP Header

**Module 1 | Section 1.4 — Protocol Stack**
**⏱ ~8 min read | Prerequisites: Lesson 12**

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

🔧 **NOC Tip:** TTL values in packet captures reveal the path length. Most operating systems start with TTL 64 (Linux), 128 (Windows), or 255 (network equipment). If you see a packet arrive with TTL 52, and the source is Linux (TTL 64), it crossed 12 hops. Unexpectedly low TTL values can indicate routing loops consuming hops.

**Protocol (8 bits):** What's inside the payload. 6 = TCP, 17 = UDP, 1 = ICMP. For VoIP: you'll see Protocol 17 (UDP) for both SIP-over-UDP and RTP, and Protocol 6 (TCP) for SIP-over-TCP/TLS.

**Header Checksum (16 bits):** Covers only the IP header (not the payload). Recomputed at every hop because TTL changes. This is why IP routers need to touch every packet.

**Source and Destination Addresses (32 bits each):** The four-octet addresses we all know. These are what NAT rewrites (Lesson 26) and what routing tables match against.

## IP Addressing and Subnetting

An IPv4 address is 32 bits, written as four decimal octets: `192.168.1.100`. Combined with a **subnet mask**, it divides into a network portion and a host portion.

### CIDR Notation

**Classless Inter-Domain Routing (CIDR)** replaced the old classful system (Class A/B/C). A CIDR prefix like `10.0.0.0/24` means the first 24 bits are the network, leaving 8 bits (256 addresses, 254 usable) for hosts.

Quick reference:
| CIDR | Subnet Mask | Usable Hosts | Common Use |
|------|-------------|--------------|------------|
| /32 | 255.255.255.255 | 1 | Single host route |
| /30 | 255.255.255.252 | 2 | Point-to-point link |
| /24 | 255.255.255.0 | 254 | Typical LAN |
| /16 | 255.255.0.0 | 65,534 | Large campus |
| /8 | 255.0.0.0 | 16,777,214 | Massive allocation |

**Subnetting math example:** Given `172.16.50.0/22`:
- /22 means the first 22 bits are network. The mask is `255.255.252.0`.
- Network range: `172.16.48.0` to `172.16.51.255` (1024 addresses, 1022 usable)
- How? The third octet (`50` = binary `00110010`) — with /22, only the first 6 bits of octet 3 are network (`001100` = 48). The host part spans the last 2 bits of octet 3 plus all 8 bits of octet 4: 10 bits = 1024 addresses.

🔧 **NOC Tip:** When a customer says "my phone is at 10.0.5.15/24 and Telnyx's SIP server is at 192.168.1.1," immediately recognize the problem: both are RFC 1918 private addresses. The Telnyx SIP server has a public IP. If the customer is giving you a private IP for the Telnyx server, they're looking at a NAT or DNS issue.

## Private Address Ranges (RFC 1918)

Three ranges are reserved for private networks — they're not routable on the public internet:

- `10.0.0.0/8` — 16.7 million addresses
- `172.16.0.0/12` — 1 million addresses (172.16.0.0–172.31.255.255)
- `192.168.0.0/16` — 65,536 addresses

These addresses are behind NAT devices (covered extensively in Lessons 26-28). When you see them in SIP headers or SDP bodies, it's a NAT traversal situation.

**Carrier-Grade NAT (CGNAT)** uses the `100.64.0.0/10` range. ISPs use CGNAT to share a single public IP among many subscribers. This creates **double NAT** — the customer's router NATs to a CGNAT address, and the ISP NATs again to a public IP. Double NAT is especially problematic for SIP/RTP.

## IP Fragmentation: How It Works and Why It's Terrible for VoIP

When a packet is larger than the next link's MTU, the router must fragment it into smaller pieces. Each fragment is a separate IP packet with:

- The same **Identification** field (so the receiver can reassemble)
- A **Fragment Offset** indicating where this fragment fits
- The **More Fragments (MF) flag** set on all but the last fragment

The **Don't Fragment (DF) flag** prevents fragmentation — if a packet is too large and DF is set, the router drops it and sends an ICMP "Fragmentation Needed" message.

### Why Fragmentation Destroys VoIP

1. **Any lost fragment kills the entire packet.** If a 1500-byte SIP INVITE is fragmented into two pieces and one is lost, the entire INVITE is lost. UDP has no retransmission — the SIP timer must expire and the UAC must retransmit.

2. **Fragments may take different paths.** Reassembly is done at the destination, and fragments arriving out of order consume buffer resources.

3. **Firewalls struggle with fragments.** Only the first fragment contains the UDP/TCP header with port numbers. Subsequent fragments have no port information, making stateful firewall tracking impossible. Many firewalls simply drop non-initial fragments.

4. **Reassembly timeout.** If a fragment doesn't arrive within 30-60 seconds, all received fragments are discarded.

### Real Troubleshooting Scenario

**Scenario:** A customer can make calls with simple SDP, but calls fail when using a complex codec list or when SRTP is negotiated. The INVITE works sometimes but fails intermittently.

**Investigation:** The INVITE with full SDP is ~1600 bytes — exceeding the 1500-byte MTU. Over UDP, this triggers fragmentation. The second fragment is being dropped by an intermediate firewall that blocks non-initial fragments.

**Solution:** Switch SIP transport from UDP to TCP. TCP handles segmentation at the transport layer — no IP fragmentation needed. Alternatively, reduce SDP size by offering fewer codecs.

🔧 **NOC Tip:** If SIP registrations work (small packets) but INVITEs fail intermittently (large packets), always suspect MTU/fragmentation. The definitive test: capture packets on both sides and look for fragments. Wireshark shows IP fragments clearly.

## ICMP: The Network's Diagnostic Protocol

**Internet Control Message Protocol (ICMP)** carries error and diagnostic messages:

- **Echo Request/Reply (Type 8/0):** The `ping` command. Tests basic reachability.
- **Destination Unreachable (Type 3):** Multiple codes — host unreachable, port unreachable, fragmentation needed (the PMTUD message), administratively prohibited.
- **Time Exceeded (Type 11):** TTL expired. This is what `traceroute` uses — by sending packets with increasing TTL values, each router along the path generates a Time Exceeded reply.
- **Redirect (Type 5):** "There's a better route." Rarely used in practice.

**The ICMP blocking problem:** Many networks block ICMP for "security." This breaks:
- `ping` (obviously)
- `traceroute` (relies on Time Exceeded)
- **Path MTU Discovery** (relies on Fragmentation Needed messages)

PMTUD failure due to blocked ICMP creates **MTU black holes** — packets are silently dropped with no feedback to the sender. This is one of the most frustrating network problems to diagnose because there's no error message.

🔧 **NOC Tip:** If large SIP messages or DTLS handshakes fail but small packets work, and you can't see fragmentation, suspect a PMTUD black hole caused by ICMP blocking. Test with: `ping -M do -s 1472 <destination>` (sends a 1500-byte packet with DF bit set). If it fails while `ping -s 56` succeeds, you've found an MTU issue.

---

**Key Takeaways:**
1. The IPv4 header's key fields for NOC work are TTL (path length, loop detection), Protocol (TCP/UDP), DSCP (QoS marking), and the fragmentation fields
2. CIDR subnetting divides addresses into network and host portions — quick mental math helps instantly identify misconfigurations
3. RFC 1918 private addresses in SIP headers or SDP always indicate NAT is involved; CGNAT (100.64.0.0/10) means double-NAT trouble
4. IP fragmentation is devastating for VoIP: lost fragments kill entire packets, firewalls drop non-initial fragments, and reassembly adds delay — use TCP for SIP to avoid it
5. ICMP blocking breaks Path MTU Discovery and creates silent black holes; never block ICMP indiscriminately in voice networks

**Next: Lesson 14 — IPv6: Why It Exists and What Changes**
