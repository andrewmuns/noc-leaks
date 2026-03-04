---
title: "DNS Fundamentals — Resolution, Records, and the Hierarchy"
description: "Learn about dns fundamentals — resolution, records, and the hierarchy"
module: "Module 1: Foundations"
lesson: "21"
difficulty: "Intermediate"
duration: "8 minutes"
objectives:
  - Understand DNS is SIP's service discovery mechanism: NAPTR → SRV → A/AAAA resolution determines which server, transport, and port a SIP client uses
  - Understand SRV records provide both failover (priority) and load balancing (weight) — understanding them is essential for understanding SIP connectivity
  - Understand TTL controls caching duration; too short overloads DNS servers, too long delays failover — typical SIP DNS TTLs are 60-300 seconds
  - Understand "DNS works for web browsing" doesn't mean DNS works for SIP — test NAPTR and SRV records specifically when debugging registration failures
  - Understand Stale DNS cache after changes is unavoidable; plan for it by reducing TTLs in advance and maintaining old endpoints during transitions
slug: "dns-fundamentals"
---

## Why DNS Is Critical for Telecom

DNS is the phonebook of the internet — it translates human-readable names to IP addresses. But for telecom, DNS does much more. It's the **service discovery mechanism** for SIP. When a phone needs to find its SIP server, it queries DNS for NAPTR and SRV records that specify not just the IP, but the transport protocol, port, and priority. A DNS failure doesn't just break web browsing — it breaks phone service entirely.

## The DNS Hierarchy

DNS is a distributed, hierarchical database:

```
                    . (root)
                   / | \
               .com .net .io
              /   \
        telnyx.com  google.com
        /    \
    sip.telnyx.com  api.telnyx.com
```

**Root servers (13 logical, hundreds of instances):** Know where to find the TLD servers. Operated by organizations worldwide.

**TLD servers (.com, .net, .org, .io):** Know which authoritative nameservers handle each domain.

**Authoritative nameservers:** The final answer. Telnyx's nameservers know the IP addresses for sip.telnyx.com, api.telnyx.com, etc.

## How DNS Resolution Works

When your SIP phone needs to resolve `sip.telnyx.com`, here's what happens:

### Step 1: Stub Resolver
The phone's OS has a simple "stub resolver" that knows one thing: the IP of its configured DNS server (usually from DHCP). It sends the query there.

### Step 2: Recursive Resolver
The DNS server (often the ISP's resolver, or 8.8.8.8, or 1.1.1.1) does the heavy lifting. If it doesn't have the answer cached, it performs **recursive resolution**:

1. Asks a root server: "Where's `.com`?" → Gets TLD server addresses
2. Asks the `.com` TLD server: "Where's `telnyx.com`?" → Gets authoritative NS addresses
3. Asks Telnyx's authoritative NS: "What's the A record for `sip.telnyx.com`?" → Gets the IP

The recursive resolver caches each answer according to its TTL, so subsequent queries skip those steps.

### Recursive vs. Iterative
**Recursive:** "Get me the answer." The resolver does all the work and returns the final answer.
**Iterative:** "I don't know, but ask this server next." The queried server returns a referral, and the asker follows up. Root and TLD servers give iterative responses; recursive resolvers handle the chasing.

> **💡 NOC Tip:** en investigating DNS issues, always verify which recursive resolver the device is using. `cat /etc/resolv.conf` on Linux, or check DHCP-assigned DNS on the phone. A failing or slow resolver is indistinguishable from a DNS outage from the client's perspective.

## DNS Record Types

### A Record (IPv4 Address)
Maps a hostname to an IPv4 address:
```
sip.telnyx.com.    300    IN    A    64.233.185.100
```

### AAAA Record (IPv6 Address)
Maps a hostname to an IPv6 address:
```
sip.telnyx.com.    300    IN    AAAA    2607:f8b0:4004::100
```

### CNAME (Canonical Name / Alias)
Points one name to another:
```
webrtc.telnyx.com.    3600    IN    CNAME    telnyx-webrtc.cdn.example.com.
```
The resolver follows the CNAME to get the final A/AAAA record. CNAMEs can't coexist with other records at the same name (except DNSSEC). This constraint matters for SRV/NAPTR configurations.

### MX (Mail Exchange)
Where to deliver email. Not directly relevant to voice but good to know:
```
telnyx.com.    3600    IN    MX    10    mail.telnyx.com.
```

### TXT (Text Record)
Arbitrary text data. Used for SPF (email auth), domain verification, DKIM, and other purposes:
```
telnyx.com.    3600    IN    TXT    "v=spf1 include:_spf.telnyx.com ~all"
```

### SRV (Service Locator) — Critical for SIP

SRV records tell clients where to find a specific service, including the protocol, port, priority, and weight:

```
_sip._udp.example.com.    300    IN    SRV    10 60 5060 sip1.example.com.
_sip._udp.example.com.    300    IN    SRV    10 40 5060 sip2.example.com.
_sip._udp.example.com.    300    IN    SRV    20 0  5060 sip3.example.com.
```

**Format:** `priority weight port target`

- **Priority:** Lower is preferred. Priority 10 servers are tried before priority 20.
- **Weight:** Within the same priority, weight determines load distribution. sip1 gets 60% of traffic, sip2 gets 40%.
- **Port:** The service port (5060 for SIP UDP, 5061 for SIP TLS).
- **Target:** The hostname of the server (must be resolved to an A/AAAA record).

SRV records enable automatic failover (use priority 20 only if priority 10 fails) and load balancing (distribute across weight within a priority).

### NAPTR (Naming Authority Pointer) — SIP Service Discovery

NAPTR records are used before SRV records in the SIP resolution process. They map a domain to the appropriate SRV records based on transport protocol:

```
telnyx.com.  300  IN  NAPTR  10 10 "s" "SIPS+D2T" "" _sips._tcp.telnyx.com.
telnyx.com.  300  IN  NAPTR  20 10 "s" "SIP+D2T"  "" _sip._tcp.telnyx.com.
telnyx.com.  300  IN  NAPTR  30 10 "s" "SIP+D2U"  "" _sip._udp.telnyx.com.
```

This tells a SIP client:
1. First preference: SIP over TLS/TCP (`SIPS+D2T`) — most secure
2. Second: SIP over TCP (`SIP+D2T`) — reliable
3. Third: SIP over UDP (`SIP+D2U`) — lightest weight

The client follows the NAPTR to the SRV record, then the SRV to the A record, getting the full resolution chain: **NAPTR → SRV → A/AAAA**.

> **💡 NOC Tip:** en a customer's phone can't register and they say "DNS is working because I can browse the web," remember: web browsing only needs A records. SIP registration needs NAPTR → SRV → A records. Their resolver might cache A records fine but fail on NAPTR/SRV. Test specifically: `dig NAPTR telnyx.com` and `dig SRV _sip._udp.telnyx.com`.

## TTL: Time to Live and Caching

Every DNS record has a **TTL** (in seconds) that tells resolvers how long to cache the answer.

```
sip.telnyx.com.    300    IN    A    64.233.185.100
                   ^^^
                   TTL: cache for 300 seconds (5 minutes)
```

**The TTL tradeoff:**
- **Short TTL (30-60s):** Fast failover — if the IP changes, clients pick up the new address quickly. But high query volume hammers DNS servers.
- **Long TTL (3600s+):** Efficient caching, fewer queries. But failover is slow — clients keep using the old IP for up to an hour.

For Telnyx SIP endpoints, TTLs are typically 60-300 seconds — balancing failover speed with query efficiency. During an incident requiring IP change, shorter TTLs would be ideal, but you can only benefit from short TTLs if they were set **before** the incident.

### The Stale Cache Problem

When a DNS record changes (e.g., IP failover), clients don't get the new IP until their cached TTL expires. If TTL was 3600 seconds, some clients will keep sending traffic to the old IP for up to an hour.

**Worse:** Some resolvers ignore TTLs and cache longer than specified. Corporate DNS proxies, ISP resolvers, and some consumer routers are known offenders. There's no way to force a purge from outside.

### Real Troubleshooting Scenario

**Scenario:** Telnyx performs a planned IP migration for a SIP endpoint. TTL was reduced to 60 seconds 48 hours before the change. Most customers transition smoothly, but a handful keep connecting to the old IP for hours.

**Investigation:** The customers' DNS resolvers are caching beyond the TTL. One uses a corporate DNS appliance that enforces a minimum 1-hour TTL regardless of the authoritative TTL. Another uses an ISP resolver known to over-cache.

**Resolution:** The old IP is kept active with a redirect/proxy for 24 hours to catch stragglers. The customer with the corporate DNS appliance manually flushes their resolver cache.

> **💡 NOC Tip:** fore any planned IP change, reduce TTLs well in advance (at least 2× the old TTL before the change). During the change, keep the old IP serving traffic for at least 2 hours to accommodate aggressive caching. Monitor traffic at both old and new IPs.

## Negative Caching

When a DNS query returns **NXDOMAIN** (name doesn't exist) or **NODATA** (name exists but no records of the requested type), resolvers cache this **negative response** too. The cache duration comes from the SOA record's minimum TTL field.

This matters when a record is accidentally deleted and then restored — the restored record won't be visible to clients that cached the NXDOMAIN until the negative cache expires.

---

**Key Takeaways:**
1. DNS is SIP's service discovery mechanism: NAPTR → SRV → A/AAAA resolution determines which server, transport, and port a SIP client uses
2. SRV records provide both failover (priority) and load balancing (weight) — understanding them is essential for understanding SIP connectivity
3. TTL controls caching duration; too short overloads DNS servers, too long delays failover — typical SIP DNS TTLs are 60-300 seconds
4. "DNS works for web browsing" doesn't mean DNS works for SIP — test NAPTR and SRV records specifically when debugging registration failures
5. Stale DNS cache after changes is unavoidable; plan for it by reducing TTLs in advance and maintaining old endpoints during transitions

**Next: Lesson 20 — DNS-Based Load Balancing and GeoDNS**
