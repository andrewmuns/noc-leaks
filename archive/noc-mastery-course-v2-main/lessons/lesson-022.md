# Lesson 22: DNS-Based Load Balancing and GeoDNS

**Module 1 | Section 1.5 — DNS**
**⏱ ~7 min read | Prerequisites: Lesson 19**

---

## DNS as a Traffic Management Tool

DNS doesn't just resolve names — it directs traffic. By carefully crafting DNS responses, you can distribute load across servers, route users to the nearest data center, and automatically remove unhealthy endpoints. This is how Telnyx routes customers to the optimal Point of Presence (PoP) worldwide.

## Round-Robin DNS: The Simplest Load Distribution

The most basic approach: return multiple A records for the same hostname:

```
sip.example.com.    60    IN    A    198.51.100.1
sip.example.com.    60    IN    A    198.51.100.2
sip.example.com.    60    IN    A    198.51.100.3
```

Clients typically try the first address in the response. DNS servers rotate the order with each query, distributing connections across all three servers.

**Limitations:**
- **No intelligence:** Every client gets every IP, regardless of location or server health
- **Uneven distribution:** Clients behind large NATs or corporate proxies look like one client but represent thousands of users — all directed to the same first IP
- **No health awareness:** If `198.51.100.2` goes down, it's still returned in DNS responses for the entire TTL period
- **Caching disrupts rotation:** A recursive resolver caches the response and serves it (in the same order) to all its clients until TTL expires

Despite these limitations, round-robin DNS is used as a baseline. SRV records (Lesson 19) improve on this with priority and weight fields for more controlled distribution.

## Weighted DNS Responses

More sophisticated DNS servers can return different weights to control traffic proportionally:

```
sip.example.com.    60    IN    A    198.51.100.1    ; weight 70
sip.example.com.    60    IN    A    198.51.100.2    ; weight 30
```

The DNS server returns `198.51.100.1` as the first result 70% of the time and `198.51.100.2` 30% of the time. This enables:

- **Gradual traffic migration:** Shift 10% of traffic to a new server, monitor, increase to 50%, then 100%
- **Capacity-proportional routing:** A server with 2× capacity gets 2× traffic
- **Canary deployments:** Route 5% of traffic to a new software version for testing

🔧 **NOC Tip:** During a deployment or infrastructure change, watch DNS weight shifts. If a canary deployment is getting 5% of traffic and error rates spike, the issue is isolated to the new code. If error rates spike across all weights, the issue is infrastructure-level, not deployment-related.

## GeoDNS: Location-Aware Responses

**GeoDNS** returns different IP addresses based on the client's geographic location (determined by the recursive resolver's IP or the EDNS Client Subnet extension).

A query from Europe might resolve `sip.telnyx.com` to a Frankfurt PoP IP, while the same query from the US East Coast resolves to an Ashburn PoP IP.

```
# Query from European resolver:
sip.telnyx.com.    60    IN    A    185.x.x.x      (Frankfurt)

# Query from US East resolver:
sip.telnyx.com.    60    IN    A    64.x.x.x       (Ashburn)

# Query from Asia-Pacific resolver:
sip.telnyx.com.    60    IN    A    103.x.x.x      (Singapore)
```

### Why GeoDNS Matters for Voice Quality

Voice is extremely sensitive to latency (Lessons 32-34 will cover this deeply). The speed of light imposes minimum propagation delays:

- New York → London: ~35ms one-way
- New York → Singapore: ~120ms one-way
- New York → Sydney: ~100ms one-way

By routing customers to the nearest PoP, GeoDNS minimizes the propagation delay component of the voice path. A customer in London connecting to the Frankfurt PoP has ~10ms propagation instead of ~35ms to Ashburn.

### EDNS Client Subnet (ECS)

GeoDNS traditionally uses the recursive resolver's IP to determine location. But major resolvers like Google (8.8.8.8) serve users worldwide from a few anycast addresses. A query from Google's resolver doesn't tell you where the actual user is.

**EDNS Client Subnet** solves this: the recursive resolver includes a portion of the client's IP address in the DNS query. The authoritative server uses this to make a geographically accurate routing decision.

Without ECS, a user in Tokyo using Google DNS might be routed to a US PoP because Google's resolver IP geolocates to the US. With ECS, the authoritative server sees the client's /24 subnet, geolocates to Tokyo, and returns the Singapore PoP.

🔧 **NOC Tip:** If a customer reports unexpectedly high latency and they're using a public DNS resolver (8.8.8.8, 1.1.1.1), GeoDNS might be sending them to the wrong PoP. Check which IP they're resolving to with `dig sip.telnyx.com`. If it's a distant PoP, the resolver's ECS support (or lack thereof) is likely the issue. Switching to their ISP's resolver often fixes geographic routing.

## Health-Check-Aware DNS

Production DNS systems don't just serve static records — they actively monitor endpoints and remove unhealthy ones from responses.

**How it works:**
1. The DNS system periodically probes each endpoint (TCP connect, HTTP check, SIP OPTIONS ping)
2. If an endpoint fails health checks, it's removed from DNS responses
3. When it recovers, it's added back

This creates **automatic failover without client-side logic.** The client simply resolves the hostname and gets only healthy endpoints.

**Failover timing depends on:**
- Health check interval (typically 10-30 seconds)
- Failure threshold (e.g., 3 consecutive failures before removal = 30-90 seconds detection)
- DNS TTL (clients won't re-resolve until cache expires)

Total failover time: detection time + TTL. With 30-second health checks (3 failures = 90s detection) and 60-second TTL, worst case is ~150 seconds.

### Real Troubleshooting Scenario

**Scenario:** A Telnyx PoP in Chicago experiences a hardware failure. Health checks detect the failure within 30 seconds. The PoP's IP is removed from DNS responses. But calls from some customers still fail for the next 5 minutes.

**Investigation:** Those customers' recursive resolvers cached the old DNS response with the Chicago IP. The TTL was 60 seconds, but some resolvers over-cache. Additionally, some SIP endpoints cache DNS results independently of the resolver, with their own (longer) TTL.

**Mitigation strategies:**
1. Keep the failed IP routable but redirect traffic to a backup (anycast or failover proxy)
2. Use very short TTLs for SIP endpoints (30-60s)
3. Implement SIP-level failover: if the resolved IP doesn't respond, try the next SRV record

🔧 **NOC Tip:** DNS-based failover is not instant. Always account for cache TTL in your incident timeline. When a PoP goes down and DNS is updated, expect a "long tail" of clients still hitting the old IP for at least TTL duration. Having the old IP return SIP 503 (so clients fail fast and try alternative SRV records) is better than having it black-hole traffic.

## DNS Failover: The TTL Tradeoff in Practice

The tension between failover speed and DNS efficiency is one of the most practical challenges in production systems:

### Aggressive (Short) TTLs
**Settings:** 15-30 second TTL
**Pros:** Near-instant failover; clients re-resolve frequently
**Cons:** Massive query volume; DNS becomes a single point of failure; adds latency to every new resolution

### Conservative (Long) TTLs
**Settings:** 300-3600 second TTL
**Pros:** Efficient caching; DNS can be briefly unavailable without impact; lower resolution latency
**Cons:** Slow failover; IP changes take a long time to propagate

### The Pragmatic Middle Ground
Most production telecom systems use **60-120 second TTLs** for SIP endpoints. This provides:
- Failover within 2-3 minutes (acceptable for most scenarios)
- Reasonable query volume
- Combined with SRV record failover (client tries next server on failure), effective automatic recovery

## Combining DNS with SIP-Level Failover

Smart SIP stacks don't just blindly use one DNS result. RFC 3263 defines the SIP server resolution process:

1. Query NAPTR for the domain → get SRV record names
2. Query SRV records → get prioritized server list
3. Try the highest-priority server
4. If it fails (timeout, 503), try the next server in the SRV list
5. If all servers at that priority fail, try the next priority level

This means **DNS provides the server list, and SIP provides the failover logic.** Even if a failed server remains in DNS responses (within TTL), the SIP client moves to the next server after detecting a failure.

🔧 **NOC Tip:** When reviewing a customer's SIP configuration, check if their device supports RFC 3263 server resolution and SRV-based failover. Many consumer devices and cheap SIP phones only support a single hardcoded IP — no DNS-based failover at all. For these devices, recommend configuring a primary and backup server IP manually.

---

**Key Takeaways:**
1. Round-robin DNS distributes traffic but lacks intelligence about health or geography; SRV records add priority and weight for more controlled distribution
2. GeoDNS routes customers to the nearest PoP based on geographic location, directly reducing voice latency — EDNS Client Subnet improves accuracy for public resolver users
3. Health-check-aware DNS automatically removes failed endpoints from responses, but failover is limited by TTL caching — total failover time = detection + TTL
4. The DNS TTL tradeoff (fast failover vs. efficient caching) is typically resolved at 60-120 seconds for SIP endpoints
5. DNS-based failover should be combined with SIP-level failover (RFC 3263 SRV processing) for robust redundancy — DNS provides the list, SIP handles the retry logic

**Next: Lesson 21 — DNS Troubleshooting: dig, nslookup, and Common Failures**
