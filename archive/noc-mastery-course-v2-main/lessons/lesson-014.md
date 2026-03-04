# Lesson 14: Ethernet and Layer 2 — Frames, MACs, VLANs, and Switching

**Module 1 | Section 1.4 — Protocol Stack**
**⏱ ~8 min read | Prerequisites: Lesson 10**

---

## Why Layer 2 Matters for Voice Engineers

Most NOC engineers think about SIP, RTP, and IP when troubleshooting calls. But everything rides on Layer 2. A misconfigured VLAN, a spanning tree reconvergence, or an MTU mismatch can cause packet loss that looks identical to network congestion at higher layers. Understanding Ethernet is understanding the foundation.

## The Ethernet Frame: Anatomy of a Layer 2 Packet

Every piece of data on a local network travels inside an Ethernet frame. Here's what one looks like on the wire:

```
| Preamble | SFD | Dest MAC | Src MAC | 802.1Q Tag | EtherType | Payload | FCS |
| 7 bytes  | 1B  | 6 bytes  | 6 bytes | (4 bytes)  | 2 bytes   | 46-1500 | 4B  |
```

**Preamble (7 bytes) + Start Frame Delimiter (1 byte):** Clock synchronization. The receiver uses these alternating 1-0 patterns to lock onto the signal timing. You'll never see these in Wireshark — the NIC strips them before passing the frame to the OS.

**Destination MAC (6 bytes):** Where the frame is going. Can be unicast (one device), multicast (a group), or broadcast (ff:ff:ff:ff:ff:ff — everyone on the segment).

**Source MAC (6 bytes):** Where the frame came from. Always unicast. This is how switches learn which port a device is on.

**802.1Q Tag (4 bytes, optional):** Present only on VLAN-tagged frames. Contains the VLAN ID (12 bits = 4096 possible VLANs) and a 3-bit Priority Code Point (PCP) used for Layer 2 QoS.

**EtherType (2 bytes):** Identifies what's inside the payload. 0x0800 = IPv4, 0x86DD = IPv6, 0x0806 = ARP. This is how the receiving system knows which protocol stack to hand the payload to.

**Payload (46–1500 bytes):** The actual data — your IP packet containing SIP or RTP lives here. Minimum 46 bytes (padded if shorter), maximum 1500 bytes (the standard **Maximum Transmission Unit** or MTU).

**Frame Check Sequence (4 bytes):** A CRC-32 checksum over the entire frame. If it doesn't match, the frame is silently discarded. No retransmission, no notification — just gone.

🔧 **NOC Tip:** FCS errors in switch interface counters indicate physical layer problems — bad cables, failing optics, or electromagnetic interference. If you see FCS errors climbing on a port that carries voice traffic, that's causing packet loss that will show up as choppy audio.

## MAC Addresses and Switch Learning

A MAC address is a 48-bit identifier, typically written as six hex octets: `00:1a:2b:3c:4d:5e`. The first three octets identify the manufacturer (the OUI — Organizationally Unique Identifier), and the last three are the device's unique serial within that manufacturer.

**How switches learn:** When a frame arrives on port 3 with source MAC `AA:BB:CC:DD:EE:FF`, the switch records: "MAC AA:BB:CC:DD:EE:FF is reachable via port 3." This entry goes into the **MAC address table** (also called CAM table) with a timeout (typically 300 seconds).

**How switches forward:** When a frame arrives destined for `11:22:33:44:55:66`, the switch looks up that MAC in its table. If found, it sends the frame out only that port (unicast). If not found, it **floods** the frame out every port except the one it arrived on. This flooding is necessary for learning but creates unnecessary traffic.

**Why this matters for NOC work:** MAC table overflow attacks (CAM table flooding) can cause a switch to flood all traffic to all ports, turning it into a hub. More commonly, if a device's MAC doesn't appear in the table (e.g., after a timeout), the first frame to it gets flooded, which can briefly disrupt flows.

## VLANs: Logical Network Segmentation

**Virtual LANs (VLANs)** divide a physical switch into multiple isolated broadcast domains. A frame in VLAN 100 can never reach a device in VLAN 200 without passing through a router (Layer 3).

Why VLANs matter for voice:

1. **Voice VLANs** isolate phone traffic from data traffic. Phones are placed in VLAN 100 (for example), computers in VLAN 200. This means a broadcast storm from a misbehaving computer doesn't affect the phones.

2. **QoS alignment:** Voice VLAN traffic can be prioritized at Layer 2 using the 802.1Q PCP bits and at Layer 3 using DSCP (Lesson 11). The VLAN tag's PCP field provides three bits of priority (0–7), with value 5 typically assigned to voice.

3. **Security:** Isolating voice traffic limits the attack surface. Eavesdropping on VoIP requires access to the voice VLAN.

### Trunk Ports vs. Access Ports

- **Access port:** Belongs to a single VLAN. Frames are untagged — the switch adds/removes the VLAN tag.
- **Trunk port:** Carries multiple VLANs. Frames include 802.1Q tags identifying which VLAN they belong to.

The link between two switches is a trunk. The link to an IP phone is often special: a tagged voice VLAN and an untagged data VLAN (the phone uses the voice VLAN, and passes data-VLAN traffic through to the computer connected behind it).

🔧 **NOC Tip:** If phones register fine but have no audio, or if they can't register at all, check VLAN assignment. A phone on the wrong VLAN might reach the SIP server (if routing exists) but be unable to exchange RTP because the media path requires the correct VLAN. Verify with `show vlan brief` and `show interfaces trunk` on the switch.

## ARP: Resolving IP to MAC

**Address Resolution Protocol (ARP)** bridges Layer 3 and Layer 2. When a device wants to send a packet to 192.168.1.50 on the local subnet, it needs the destination MAC address. It broadcasts an ARP request: "Who has 192.168.1.50? Tell me your MAC." The device at that IP replies with its MAC.

ARP responses are cached (the ARP table) to avoid asking repeatedly. Cache entries expire after a timeout (typically 60–300 seconds depending on OS).

### ARP and Troubleshooting

**ARP issues manifest as reachability problems.** If ARP fails, the device can't build an Ethernet frame, so no IP communication is possible — even though the IP configuration is correct.

Common ARP problems in NOC environments:
- **ARP timeout:** Device is unreachable at Layer 2 (wrong VLAN, port down, cable issue)
- **ARP cache poisoning:** A malicious device sends fake ARP replies, redirecting traffic (security concern)
- **Gratuitous ARP:** A device announces its own MAC (used in failover scenarios — when a VIP moves between servers, a gratuitous ARP updates everyone's cache)

### Real Troubleshooting Scenario

**Scenario:** An IP phone works fine for hours, then suddenly loses registration and goes silent for 30–60 seconds before recovering.

**Investigation:** The switch logs show Spanning Tree Protocol (STP) topology changes. When STP reconverges (due to a link flapping), the switch may briefly block the phone's port. Even if the block lasts only a few seconds, the phone loses connectivity, its SIP registration expires, and it must re-register.

**Root cause:** A flapping uplink is causing STP reconvergences. The fix: enable STP PortFast on access ports (so they skip the listening/learning states) and find/fix the flapping link.

🔧 **NOC Tip:** STP reconvergences are invisible at the IP layer — you won't see them in SIP traces or `ping` tests unless they happen to coincide with your test. Check switch logs (`show spanning-tree detail`, `show log`) when you see periodic, short connectivity drops.

## MTU: Maximum Transmission Unit

The standard Ethernet MTU is **1500 bytes** — the maximum IP packet that fits in an Ethernet frame's payload without fragmentation.

Why MTU matters for voice:
- A G.711 RTP packet with 20ms of audio: 12 (RTP) + 8 (UDP) + 20 (IP) + 160 (audio) = **200 bytes**. Well within MTU.
- SIP INVITE messages can be 2000+ bytes, exceeding MTU. Over UDP, this means IP fragmentation. Over TCP, the TCP stack handles segmentation.

**Jumbo frames** (MTU 9000) are used in data centers to improve throughput for large transfers. But if one link in the path has standard MTU (1500) and jumbo frames are enabled elsewhere, packets get fragmented or dropped (if Don't Fragment bit is set).

**Path MTU Discovery (PMTUD)** helps: the sender sets the Don't Fragment (DF) bit, and intermediate routers send ICMP "Fragmentation Needed" messages if the packet is too large. The sender then reduces packet size. But PMTUD fails if ICMP is blocked by firewalls — creating a **black hole** where packets disappear silently.

🔧 **NOC Tip:** If SIP over UDP fails for large messages (INVITEs with lots of SDP or long headers) but small messages (REGISTER, OPTIONS) work fine, suspect MTU/fragmentation issues. Switch to TCP for SIP signaling to eliminate this entire class of problems.

## Spanning Tree Protocol: Loop Prevention

Ethernet networks with redundant links need **STP** to prevent broadcast storms (frames looping infinitely). STP blocks redundant paths, creating a loop-free tree topology. When a link fails, STP reconverges to activate a backup path.

Classic STP reconvergence takes 30–50 seconds. **Rapid STP (RSTP, 802.1w)** reduces this to 1–3 seconds. For voice networks, the difference between 50 seconds of downtime and 2 seconds is enormous.

---

**Key Takeaways:**
1. Every IP packet rides inside an Ethernet frame; Layer 2 problems (FCS errors, STP reconvergence, VLAN misconfiguration) cause packet loss that's invisible at higher layers
2. Switches learn MAC-to-port mappings from source addresses and forward based on destination lookups — unknown destinations are flooded
3. VLANs isolate voice from data traffic, enabling QoS, security, and broadcast domain control — misconfigured VLANs are a common cause of phone registration and audio issues
4. ARP resolves IP to MAC addresses; ARP failures mean complete local connectivity loss even with correct IP configuration
5. MTU mismatches cause silent packet drops or fragmentation; SIP over UDP is especially vulnerable for large messages — use TCP to avoid fragmentation issues

**Next: Lesson 13 — IPv4: Addressing, Subnetting, and the IP Header**
