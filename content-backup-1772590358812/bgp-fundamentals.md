---
title: "Autonomous Systems and Internet Routing Fundamentals"
description: "Learn about autonomous systems and internet routing fundamentals"
module: "Module 1: Foundations"
lesson: "24"
difficulty: "Intermediate"
duration: "8 minutes"
objectives:
  - Understand autonomous systems and internet routing fundamentals
slug: "bgp-fundamentals"
---

You've learned how packets move across networks using IP addressing and subnetting. But how does the *internet itself* know where to send traffic? The answer lies in Autonomous Systems and the routing protocols that connect them. As a Telnyx NOC engineer, understanding this layer is critical — our voice traffic traverses multiple networks, and routing problems directly impact call quality.

## What Is an Autonomous System?

An **Autonomous System (AS)** is a network or collection of networks under a single administrative domain that presents a unified routing policy to the internet.

Think of it this way:
- A **network** is a single LAN or subnet
- An **AS** is an entire organization's routing domain — all of Telnyx's infrastructure, for example, operates under one AS

Every AS is identified by a unique **AS Number (ASN)**:
- **16-bit ASNs:** 1–65534 (original range, running out)
- **32-bit ASNs:** 65536–4294967294 (extended range)

### Telnyx's Autonomous System

```
Telnyx ASN: AS46887
```

You can look this up:
```bash
# Query Telnyx's ASN info
whois AS46887

# See what prefixes Telnyx announces
# (via bgp.he.net or command line)
curl -s https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS46887 | jq '.data.prefixes[].prefix'
```

> **💡 NOC Tip:** okmark https://bgp.he.net/AS46887 — it's the quickest way to see Telnyx's announced prefixes, peers, and upstream providers during an incident.

## Types of Autonomous Systems

| Type | Description | Example |
|------|-------------|---------|
| **Stub AS** | Single connection to one other AS | Small business with one ISP |
| **Multi-homed AS** | Connected to multiple ASes but doesn't transit traffic | Enterprise with two ISPs for redundancy |
| **Transit AS** | Allows traffic from other ASes to pass through it | Tier-1 carriers like Lumen, NTT |

Telnyx is a **multi-homed AS** with transit and peering connections — we connect to multiple upstream providers and peer at internet exchange points to ensure redundancy and optimal routing for voice traffic.

## IGP vs EGP — Interior and Exterior Routing

The internet uses two categories of routing protocols:

### Interior Gateway Protocols (IGP)

Used **within** an AS to route between internal networks:

| Protocol | Type | Use Case |
|----------|------|----------|
| OSPF | Link-state | Enterprise and data center networks |
| IS-IS | Link-state | Large ISP/carrier backbones |
| EIGRP | Distance-vector (hybrid) | Cisco-only environments |
| RIP | Distance-vector | Legacy, rarely used |

```
┌─────────────────────────────────────┐
│           Telnyx AS46887            │
│                                     │
│  [DC-Chicago] ──OSPF── [DC-Dallas] │
│       │                     │       │
│     OSPF                  OSPF      │
│       │                     │       │
│  [DC-Ashburn] ──OSPF── [DC-Seattle]│
│                                     │
└─────────────────────────────────────┘
```

### Exterior Gateway Protocol (EGP)

Used **between** ASes. In modern networking, there is exactly one EGP:

**BGP (Border Gateway Protocol)** — the routing protocol of the internet.

```
                    ┌──────────┐
                    │ Transit  │
                    │ AS174    │
                    │ (Cogent) │
                    └────┬─────┘
                         │ BGP
    ┌──────────┐    ┌────┴─────┐    ┌──────────┐
    │ AS46887  │────│  IXP     │────│ AS13335  │
    │ (Telnyx) │BGP │(Equinix) │BGP │(Cloud-   │
    │          │    │          │    │ flare)   │
    └──────────┘    └──────────┘    └──────────┘
```

> **💡 NOC Tip:** en you see routing issues in the NOC, first determine: is the problem *internal* (IGP — our routers can't reach each other) or *external* (BGP — the internet can't reach us, or we can't reach a destination)? The tools and escalation paths are completely different.

## IP Prefix Announcement

When Telnyx wants the internet to know how to reach our IP addresses, we **announce** IP prefixes via BGP:

```
Telnyx announces (example):
  64.16.0.0/20    → "Send traffic for 64.16.0.0 - 64.16.15.255 to AS46887"
  185.246.x.0/24  → "Send traffic for this /24 to AS46887"
```

### How Announcement Works

1. Telnyx configures BGP on our border routers
2. We advertise our IP prefixes to our BGP neighbors (upstreams and peers)
3. Those neighbors propagate the announcements to *their* neighbors
4. Within minutes, the entire internet knows to route traffic for our IPs through paths that lead to AS46887

### Prefix Ownership and IRR

Before announcing prefixes, they must be:
- **Allocated** to Telnyx by a Regional Internet Registry (RIR) — ARIN for North America
- **Registered** in Internet Routing Registries (IRR) with route objects
- **Authorized** via RPKI/ROA (Route Origin Authorization)

```bash
# Check who owns a prefix
whois 64.16.0.0/20

# Verify RPKI status
curl -s https://stat.ripe.net/data/rpki-validation/data.json?resource=AS46887&prefix=64.16.0.0/20
```

## The Routing Table

Every router maintains a **routing table** (also called RIB — Routing Information Base) that maps destination prefixes to next-hop addresses:

```
Prefix              Next-Hop         AS-Path              Metric
64.16.0.0/20        203.0.113.1      46887                100
8.8.8.0/24          198.51.100.1     15169                200
1.1.1.0/24          198.51.100.1     13335                200
```

### The Global Routing Table

The **Default-Free Zone (DFZ)** is the set of routers that carry the full internet routing table — no default routes needed because they know a path to every announced prefix.

```
As of 2024:
  - IPv4 prefixes in DFZ: ~950,000+
  - IPv6 prefixes in DFZ: ~200,000+
  - Total keeps growing every year
```

### How Routing Decisions Are Made

When a router receives a packet for destination `8.8.8.8`:

1. **Longest prefix match** — find the most specific route
   - `/24` beats `/20` beats `/16`
2. If multiple paths exist to the same prefix → use BGP **path selection algorithm** (covered in Lesson 23)
3. Forward packet to the selected next-hop

```
Example: Packet destined for 64.16.5.10

Routing table has:
  64.16.0.0/20  → next-hop A
  64.16.4.0/22  → next-hop B
  64.16.5.0/24  → next-hop C  ← WINS (most specific)
```

> **💡 NOC Tip:** ngest prefix match is why more-specific route announcements can "hijack" traffic. If someone (accidentally or maliciously) announces `64.16.5.0/24` and we only announce `64.16.0.0/20`, their more-specific route wins. This is a BGP hijack — covered in Lesson 25.

## Looking Glass Tools

To see how the internet views Telnyx's routes from the outside:

```bash
# Hurricane Electric BGP Toolkit
# https://bgp.he.net/AS46887

# RIPE Stat — visual route analysis
# https://stat.ripe.net/AS46887

# Traceroute from remote vantage points
# https://lg.he.net/  (HE looking glass)
```

These tools are invaluable during outages. If a customer reports they can't reach Telnyx but others can, check looking glass servers from their ISP's geography to see if the routing path is intact.

## Real-World Scenario: Regional Reachability Issue

**Ticket:** "Customers in Brazil can't reach our SIP servers, but US customers are fine."

**Investigation:**
```bash
# 1. Check if Telnyx prefixes are visible from Brazilian networks
# Use RIPE RIS or looking glass from a Brazilian ISP

# 2. Run traceroute from a Brazilian vantage point
mtr -rwc 10 sip.telnyx.com

# 3. Check BGP announcements from Telnyx
# Is the prefix being announced to all upstreams?
# Did one upstream drop the route?
```

**Root cause:** One of Telnyx's transit providers had a BGP session flap, withdrawing routes that were the preferred path from South American networks. Traffic was blackholed because there was no alternate path from that region.

> **💡 NOC Tip:** gional reachability problems almost always point to BGP. If the issue is geography-specific, start with BGP tools — not ping and traceroute from your own desk (you're likely in a US data center with great connectivity).

## Key Takeaways

1. **An Autonomous System (AS)** is a network under one administrative domain with a unique ASN — Telnyx is AS46887
2. **IGP routes within an AS** (OSPF, IS-IS); **BGP routes between ASes** — they solve different problems
3. **IP prefixes are announced via BGP** to tell the internet how to reach your addresses
4. **Longest prefix match** determines which route wins — more-specific prefixes always win
5. **The global routing table** has ~950K+ IPv4 prefixes and is the backbone of internet reachability
6. **Looking glass tools** (bgp.he.net, RIPE Stat) let you see routing from external vantage points — essential for diagnosing regional issues

---

**Next: Lesson 23 — BGP Mechanics — Sessions, Updates, and Path Selection**
