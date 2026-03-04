---
title: "BGP Incidents — Hijacks, Leaks, and Troubleshooting"
description: "Learn about bgp incidents — hijacks, leaks, and troubleshooting"
module: "Module 1: Foundations"
lesson: "27"
difficulty: "Intermediate"
duration: "7 minutes"
objectives:
  - Understand bgp incidents — hijacks, leaks, and troubleshooting
slug: "bgp-incidents"
---

## BGP Security: The Internet's Achilles Heel

BGP was designed in an era of trust. It assumes that if an AS announces a prefix, they're authorized to do so. That assumption has been exploited countless times. Understanding how BGP incidents happen — and how to detect them — is essential for NOC engineers dealing with global reachability issues.

---

## BGP Hijacking: When Someone Announces Your Prefixes

A **BGP hijack** occurs when an AS announces a prefix it doesn't own, attracting traffic intended for the legitimate owner.

### How Hijacks Work

1. **Evil Corp (AS 666)** announces `192.0.2.0/24` — which actually belongs to **Telnyx (AS 15169)**
2. Some upstream providers accept and propagate this announcement
3. Traffic destined for Telnyx endpoints in that range gets routed to Evil Corp instead
4. Evil Corp can drop the traffic (denial of service), monitor it, or man-in-the-middle it

### Why Hijacks Succeed

- **Path length matters:** If Evil Corp's AS-PATH appears shorter to some networks, they'll prefer the hijacked route
- **Specificity wins:** A more specific prefix (/24 beats /22) always wins, regardless of path length
- **Filtering is inconsistent:** Not all providers rigorously filter customer announcements

> **💡 NOC Tip:**  you see traffic to your prefixes suddenly routing through an unexpected AS, check bgp.he.net immediately. A sudden upstream change during stable operations is a red flag.
slug: "bgp-incidents"
---

## Route Leaks: Accidental Propagation

**Route leaks** are typically accidental — an AS propagates routes it learned from one provider to another provider, violating intended routing policy.

### Classic Leak Scenario

- Telnyx connects to **Provider A** and **Provider B** for transit
- Telnyx should only send its own prefixes and downstream customer prefixes to each provider
- A misconfiguration causes Telnyx to forward **Provider A's full routing table** to **Provider B**
- Provider B now sends traffic destined for Provider A through Telnyx instead of direct peering

### Impact of Route Leaks

- **Traffic asymmetry:** Return paths don't match forward paths
- **Latency spikes:** Traffic takes the "scenic route"
- **Capacity issues:** Telnyx's links get saturated with transit traffic it shouldn't be carrying
- **Bills:** If you're paying for transit, a leak can balloon your usage costs

### Famous Leaks

- **2018 Google/Verizon leak:** Verizon leaked routes from a small ISP to the global internet, causing massive outages
- **2019 Swiss Cloudflare leak:** A Swiss ISP leaked 30,000 routes, briefly hijacking major sites

> **💡 NOC Tip:** ute leaks often manifest as latency spikes on specific paths, not total outages. If traceroutes show traffic taking weird detours (EU traffic routing through Asia-Pacific), investigate for route leaks.

---

## RPKI and ROA: Cryptographic Protection

**Resource Public Key Infrastructure (RPKI)** provides cryptographic proof that an AS is authorized to announce a prefix.

### How RPKI Works

1. **Registry:** RIRs (ARIN, RIPE, etc.) cryptographically sign ROAs (Route Origin Authorizations)
2. **ROA:** States "AS 15169 is authorized to announce 192.0.2.0/24"
3. **Validation:** Routers download ROAs and validate BGP announcements against them
4. **Action:** Invalid announcements can be dropped or depreferenced

### ROA Status Values

| Status | Meaning | NOC Action |
|--------|---------|------------|
| **Valid** | Announcement matches ROA | ✓ Normal |
| **Invalid** | Announcement violates ROA | ⚠️ Possible hijack — investigate |
| **NotFound** | No ROA exists for this prefix | ⚠️ Consider creating ROA |

### Adoption Reality

RPKI adoption is growing but incomplete:
- ~50% of prefixes have ROAs deployed
- Not all networks validate RPKI (though major ones do)
- False positives can happen with misconfigured ROAs

> **💡 NOC Tip:** u can check your prefix RPKI status at [rpki-validator.ripe.net](https://rpki-validator.ripe.net). Make sure Telnyx's critical prefixes are covered by valid ROAs.
slug: "bgp-incidents"
---

## Detection Tools for NOC Engineers

### BGPStream (CAIDA)

Real-time detection of BGP anomalies:
```bash
# Check for recent hijacks involving your prefixes
# bgpstream.com provides API and browser interface
```

### BGP Hijack Detection Services

- **bgp.he.net (Hurricane Electric):** Visual route tracking, historical data
- **RIPE RIS (Routing Information Service):** BGP data from collectors worldwide
- **BGPMon** and similar commercial monitoring services

### Looking Glass Servers

Test routing from different points on the internet:
- `telnet route-server.he.net` — Hurricane Electric
- Many IXPs and large carriers provide web-based looking glasses

> **💡 NOC Tip:** en investigating reachability issues:
1. Check multiple looking glasses for your affected prefix
2. Compare AS-PATH from different vantage points
3. Use bgp.he.net to see the propagation graph
4. Look for unexpected origin ASes or path changes

---

## Responding to BGP Incidents

### Immediate Response (First 10 Minutes)

1. **Confirm:** Verify it's not a false alarm (check multiple sources)
2. **Notify:** Alert upstream providers — if they're propagating the bad route, ask them to filter it
3. **Announce:** If you have peers/IXP connections, announce more specific prefixes (/24s) to reclaim traffic
4. **Document:** Capture routing data from bgp.he.net, RIPE RIS for post-mortem

### Coordination

- **Contact the hijacking/leaking AS:** Often accidental — they may fix quickly
- **Upstream providers:** Ask them to implement prefix filters
- **IXP route servers:** May be able to block announcements

### Long-Term Mitigation

- Deploy RPKI ROAs for all Telnyx prefixes
- Enable RPKI validation on border routers if possible
- Implement strict prefix filters with upstream providers
- Monitor for BGP anomalies proactively
slug: "bgp-incidents"
---

## Key Takeaways

1. **BGP hijacks** involve unauthorized announcement of your prefixes — can be malicious (theft/MitM) or accidental
2. **Route leaks** propagate routes beyond intended boundaries — typically causes latency/capacity issues, not outages
3. **RPKI/ROA** provides cryptographic proof of prefix ownership — deploy ROAs and validate where possible
4. **Detection tools:** bgp.he.net, RIPE RIS, BGPStream, and looking glasses are essential for investigating routing anomalies
5. **Response:** Confirm → notify upstream → announce specifics to reclaim traffic → coordinate with the source AS

---

**Next: Lesson 26 — NAT Fundamentals — How and Why Network Address Translation Works**
