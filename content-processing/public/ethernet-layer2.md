---
content_type: truncated
description: "Learn about ethernet and layer 2 \u2014 frames, macs, vlans, and switching"
difficulty: Intermediate
duration: 8 minutes
full_content_available: true
lesson: '14'
module: 'Module 1: Foundations'
objectives:
- Understand Every IP packet rides inside an Ethernet frame; Layer 2 problems (FCS
  errors, STP reconvergence, VLAN misconfiguration) cause packet loss that's invisible
  at higher layers
- "Understand Switches learn MAC-to-port mappings from source addresses and forward\
  \ based on destination lookups \u2014 unknown destinations are flooded"
- "Understand VLANs isolate voice from data traffic, enabling QoS, security, and broadcast\
  \ domain control \u2014 misconfigured VLANs are a common cause of phone registration\
  \ and audio issues"
- Understand ARP resolves IP to MAC addresses; ARP failures mean complete local connectivity
  loss even with correct IP configuration
- "Understand MTU mismatches cause silent packet drops or fragmentation; SIP over\
  \ UDP is especially vulnerable for large messages \u2014 use TCP to avoid fragmentation\
  \ issues"
slug: ethernet-layer2
title: "Ethernet and Layer 2 \u2014 Frames, MACs, VLANs, and Switching"
word_limit: 300
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

**Payload (46–1500 bytes):** The actual data — your IP packet containing SIP or RTP lives here. Minimum 46

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*