# Lesson 26: Peering, Transit, and Internet Exchange Points
**Module 1 | Section 1.6 — BGP**
**⏱ ~7min read | Prerequisites: Lesson 23**
---

You now understand how BGP sessions work and how paths are selected. But *who* is Telnyx exchanging routes with, and why? The business and technical relationships between networks — transit, peering, and internet exchange points — directly shape how voice traffic flows across the internet. For a NOC engineer, understanding these relationships explains why some calls have pristine quality while others suffer from latency and jitter.

## Transit vs Peering

There are two fundamental ways networks exchange traffic:

### Transit

A **paid** relationship where one network (the customer) pays another (the provider) for access to the *entire* internet.

```
┌──────────────┐    $$$     ┌──────────────┐
│   Telnyx     │ ────────► │   Cogent     │
│   AS46887    │  transit   │   AS174      │
│              │◄────────  │ (provides    │
│  "customer"  │  full      │  full table) │
└──────────────┘  routes    └──────────────┘
```

**What you get with transit:**
- A full routing table (~950K IPv4 prefixes) — you can reach *anywhere*
- Your routes announced to the transit provider's entire customer and peer base
- You pay monthly based on bandwidth commitment (e.g., 10Gbps @ $X/Mbps)

### Peering

A relationship where two networks **directly exchange traffic destined for each other's networks** (and their customers). Usually **free** (settlement-free).

```
┌──────────────┐   free    ┌──────────────┐
│   Telnyx     │ ◄───────► │  Cloudflare  │
│   AS46887    │  peering   │   AS13335    │
│              │  (direct)  │              │
└──────────────┘           └──────────────┘
```

**What you get with peering:**
- Routes only to the peer's network and their customers — NOT the whole internet
- Direct path between the two networks — lower latency, fewer hops
- No monthly payment (settlement-free) or reduced cost

### Comparison Table

| Aspect | Transit | Peering |
|--------|---------|---------|
| Cost | Paid ($$) | Usually free |
| Routes received | Full internet table | Only peer's routes |
| Routes sent | Your routes + customers | Your routes + customers |
| Relationship | Provider ↔ Customer | Peer ↔ Peer |
| Business power | Provider has leverage | Roughly equal |
| Availability | Buy from any transit provider | Must negotiate with each peer |

🔧 **NOC Tip:** When diagnosing routing issues, knowing whether traffic flows over transit or peering matters. Peered paths are typically shorter and faster. If a previously-peered destination suddenly gets worse quality, check if the peering session dropped — traffic may have shifted to a longer transit path.

## Internet Exchange Points (IXPs)

An **Internet Exchange Point (IXP)** is a physical facility where multiple networks connect to exchange traffic via peering.

### How IXPs Work

Instead of running a dedicated cable between every pair of networks that want to peer (which doesn't scale), everyone connects to a **shared switching fabric** at the IXP:

```
Without IXP (direct peering — N×N problem):
  Telnyx ──── Cloudflare
  Telnyx ──── Google
  Telnyx ──── Microsoft
  Telnyx ──── Meta
  (4 separate connections just for Telnyx)

With IXP (shared fabric):
                    ┌─────────────┐
  Telnyx ──────────►│             │
  Cloudflare ──────►│   IXP       │
  Google ──────────►│  Switch     │
  Microsoft ───────►│  Fabric     │
  Meta ────────────►│             │
                    └─────────────┘
  (1 connection each, peer with everyone)
```

### Major IXPs Relevant to Telnyx

| IXP | Location | Significance |
|-----|----------|-------------|
| **DE-CIX** | Frankfurt | Largest IXP by traffic (~15+ Tbps peak) |
| **AMS-IX** | Amsterdam | Major European exchange |
| **LINX** | London | Key for UK voice traffic |
| **Equinix IX** | Multiple US cities | Major US peering fabric |
| **SIX** | Seattle | Important for West Coast |
| **Any2** | Los Angeles | Major LA peering exchange |

### Private vs Public Peering

| Type | Description | Use Case |
|------|-------------|----------|
| **Public peering** | Over the shared IXP fabric | Low-to-medium traffic volumes |
| **Private peering** | Dedicated cross-connect between two networks in the same facility | High traffic volumes needing guaranteed bandwidth |

```
Public peering (via IXP):
  Telnyx port ──► IXP fabric ──► Peer port
  (shared bandwidth, lower cost)

Private peering (direct):
  Telnyx port ──────────────────► Peer port
  (dedicated link, guaranteed bandwidth)
```

## Settlement-Free vs Paid Peering

### Settlement-Free Peering

Most peering is **settlement-free** — neither party pays the other. The logic: "We both benefit from exchanging traffic directly, so it's a wash."

Requirements to peer (typical peering policy):
- Minimum traffic volume (e.g., >100 Mbps)
- Presence at the same facility or IXP
- 24/7 NOC with contact information
- Roughly balanced traffic ratios

### Paid Peering

Some large networks (especially "eyeball" networks like major ISPs) charge for peering because they carry more consumer traffic than they send:

```
Content Provider (sends a lot) ──$──► Eyeball ISP (receives a lot)
```

🔧 **NOC Tip:** Paid peering disputes can cause real outages. When a peering agreement expires or a negotiation breaks down, one party may de-peer — suddenly removing the direct path. Traffic shifts to transit, latency increases, and voice quality drops. These situations are rare but dramatic.

## How Peering Affects Voice Quality

This is where it gets real for Telnyx NOC engineers. VoIP is extremely sensitive to:
- **Latency** — adds delay to conversations
- **Jitter** — causes choppy audio
- **Packet loss** — causes gaps and distortion

### Transit Path vs Peered Path

```
Transit path (Telnyx → Customer PBX via ISP):
  Telnyx → Cogent → Level3 → Comcast → Customer
  Hops: 4 ASes
  Latency: ~45ms
  Jitter: variable (congested transit links)

Peered path (Telnyx directly peers with Comcast at IXP):
  Telnyx → Comcast → Customer
  Hops: 2 ASes
  Latency: ~12ms
  Jitter: minimal (direct exchange)
```

That's a **73% latency reduction** from peering. For voice calls, this is the difference between "crystal clear" and "noticeable delay."

### Real-World Scenario: Quality Degradation After De-Peering

**Ticket:** "Multiple customers on ISP-X reporting increased latency and choppy audio since Tuesday."

**Investigation:**
```bash
# Check if we still have a direct peering session with ISP-X
show bgp neighbor | grep ISP-X

# Compare current path to ISP-X's prefixes
show bgp 203.0.113.0/24
# Before: AS-PATH: 12345 (direct peer)
# Now:    AS-PATH: 174 6939 12345 (via transit!)

# Check traceroute from our SBC to customer
mtr -rwc 50 customer-pbx-ip
# Latency jumped from 12ms to 55ms
# Jitter increased from 1ms to 8ms
```

**Root cause:** The peering session with ISP-X went down (link failure at the IXP). All traffic shifted to transit paths, adding latency and traversing congested links.

**Resolution:** Network engineering re-established peering via an alternate IXP where both networks had presence.

🔧 **NOC Tip:** Maintain a mental (or documented) map of Telnyx's key peering relationships. When quality degrades for a specific set of customers, ask: "Are these customers all on the same ISP? Did our peering with that ISP change?" The `show bgp` path comparison is your fastest diagnostic.

## Route Servers at IXPs

Most IXPs run **route servers** — BGP speakers that collect routes from all IXP members and redistribute them. Instead of configuring bilateral BGP sessions with 200+ peers, you peer with the route server and get everyone's routes:

```
Without route server:
  Configure 200 BGP sessions (one per peer)

With route server:
  Configure 2 BGP sessions (primary + backup route server)
  Receive routes from all 200 peers
```

Route servers simplify operations but add a dependency — if the route server has issues, multiple peering sessions are affected simultaneously.

## Telnyx's Connectivity Strategy

A healthy connectivity strategy for a voice carrier like Telnyx includes:

1. **Multiple transit providers** (e.g., Cogent, Lumen, NTT) for full internet reachability and redundancy
2. **Peering at major IXPs** for direct, low-latency paths to large ISPs and content networks
3. **Private peering** with high-traffic partners for guaranteed performance
4. **Geographic diversity** — transit and peering in multiple cities/regions

```
                    ┌─────────┐
          transit   │ Cogent  │
      ┌────────────►│ AS174   │
      │             └─────────┘
      │             ┌─────────┐
      │   transit   │ Lumen   │
      ├────────────►│ AS3356  │
      │             └─────────┘
┌─────┴──────┐      ┌─────────┐
│   Telnyx   │ IXP  │Equinix  │ ──► 100+ peers
│  AS46887   ├─────►│  IX     │
│            │      └─────────┘
│            │      ┌─────────┐
│            │ PNI  │Comcast  │
│            ├─────►│ AS7922  │
└────────────┘      └─────────┘
```

## Key Takeaways

1. **Transit is paid access to the full internet**; **peering is direct traffic exchange**, usually free
2. **IXPs** are shared facilities where hundreds of networks peer efficiently over a common fabric
3. **Settlement-free peering** is the norm; **paid peering** exists when traffic ratios are imbalanced
4. **Peered paths have lower latency and jitter** than transit paths — critical for voice quality
5. **De-peering events** cause sudden quality degradation as traffic shifts to longer transit paths
6. **Route servers** at IXPs simplify peering but create a shared dependency
7. **Telnyx uses a mix of transit, IXP peering, and private peering** to optimize voice quality globally

---

**Next: Lesson 25 — BGP Incidents — Hijacks, Leaks, and Troubleshooting**
