---
title: "DNS Troubleshooting — dig, nslookup, and Common Failures"
description: "Learn about dns troubleshooting — dig, nslookup, and common failures"
module: "Module 1: Foundations"
lesson: "23"
difficulty: "Intermediate"
duration: "6 minutes"
objectives:
  - Understand dns troubleshooting — dig, nslookup, and common failures
slug: "dns-troubleshooting"
---

In Lessons 19 and 20 you learned how DNS works and how SIP relies on NAPTR/SRV records to locate services. Now it's time to get your hands dirty. When a customer's calls aren't connecting, DNS is one of the first things you check. This lesson arms you with the commands, patterns, and mental models to diagnose DNS failures fast.

## dig — Your Primary DNS Weapon

`dig` (Domain Information Groper) is the NOC engineer's go-to tool. Unlike `nslookup`, it shows the full DNS response including flags, authority, and additional sections.

### Basic Queries

```bash
# A record lookup
dig sip.telnyx.com A

# SRV record for SIP
dig _sip._udp.customer-domain.com SRV

# NAPTR record
dig customer-domain.com NAPTR

# Query a specific nameserver
dig @8.8.8.8 sip.telnyx.com A

# Short output (just the answer)
dig +short sip.telnyx.com A
```

### dig +trace — Follow the Entire Resolution Path

When you suspect a delegation or caching issue, `+trace` walks the entire resolution chain from the root servers down:

```bash
dig +trace sip.telnyx.com A
```

This outputs each step:
1. Root servers (`.`) → refer to `.com` TLD servers
2. `.com` TLD servers → refer to Telnyx's authoritative NS
3. Telnyx authoritative NS → return the final A record

> **💡 NOC Tip:**  `+trace` stalls at a particular delegation level, you've found your problem. A broken delegation between the registrar and the authoritative nameserver is a common cause of "DNS works from some places but not others."

## nslookup — Quick and Cross-Platform

`nslookup` is simpler but available everywhere, including Windows:

```bash
# Basic lookup
nslookup sip.telnyx.com

# Query specific server
nslookup sip.telnyx.com 8.8.8.8

# Set record type
nslookup -type=SRV _sip._udp.example.com

# Interactive mode
nslookup
> set type=NAPTR
> example.com
```

> **💡 NOC Tip:** en walking a customer through troubleshooting on Windows, use `nslookup` — it's always available. For your own analysis on Linux, always prefer `dig`.

## Common DNS Failure Patterns

### NXDOMAIN — "This Domain Does Not Exist"

```
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN
```

**What it means:** The authoritative server says this name absolutely does not exist.

**Common causes at Telnyx:**
- Customer typed the SIP domain wrong in their PBX config
- DNS zone hasn't propagated after a recent change
- Domain expired

**Diagnosis:**
```bash
# Check if the domain exists at all
dig +short example.com NS

# Check WHOIS for expiration
whois example.com | grep -i expir
```

### SERVFAIL — "I Tried But Couldn't Get an Answer"

```
;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL
```

**What it means:** The resolver tried to resolve the name but something went wrong upstream.

**Common causes:**
- Authoritative nameserver is down
- DNSSEC validation failure
- Lame delegation (NS records point to servers that don't serve the zone)

**Diagnosis:**
```bash
# Bypass the resolver, ask authoritative directly
dig +trace example.com A

# Check if DNSSEC is the problem — disable validation
dig +cd example.com A   # cd = "checking disabled"
```

> **💡 NOC Tip:**  `dig +cd` returns an answer but a normal `dig` returns SERVFAIL, you have a DNSSEC problem. The zone's DNSSEC signatures are broken or expired.

### Timeout — No Response At All

```
;; connection timed out; no servers could be reached
```

**Common causes:**
- Firewall blocking UDP/53 or TCP/53
- Resolver is down
- Network path issue

**Diagnosis:**
```bash
# Test if the resolver port is reachable
nc -zvu 8.8.8.8 53

# Try TCP instead of UDP
dig +tcp sip.telnyx.com A

# Try a different resolver entirely
dig @1.1.1.1 sip.telnyx.com A
```

## DNS Caching Problems

DNS caching is a feature that becomes a bug when records change.

### The TTL Trap

Every DNS record has a Time-To-Live (TTL). After a record change, stale answers persist until the TTL expires:

```bash
# Check the TTL of a record
dig sip.telnyx.com A | grep -A1 "ANSWER SECTION"
;; ANSWER SECTION:
sip.telnyx.com.    300    IN    A    64.16.x.x
```

That `300` means resolvers cache this answer for 300 seconds (5 minutes).

### Negative Caching

Failed lookups (NXDOMAIN) are also cached, governed by the SOA record's minimum TTL:

```bash
dig example.com SOA | grep SOA
# The last number in the SOA record is the negative cache TTL
```

> **💡 NOC Tip:**  a customer just created DNS records but lookups still return NXDOMAIN, check the SOA negative cache TTL. They may have queried the name *before* creating the record, and now the NXDOMAIN is cached. Tell them to wait for the negative TTL to expire, or flush their local resolver: `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache` (macOS).

### Resolver Cache Comparison

A powerful debugging technique — query multiple resolvers:

```bash
dig @8.8.8.8 customer-domain.com A +short
dig @1.1.1.1 customer-domain.com A +short
dig @9.9.9.9 customer-domain.com A +short
dig @ns1.customer-dns.com customer-domain.com A +short  # authoritative
```

If the authoritative server returns the new IP but public resolvers return the old one, it's a caching issue. Wait for TTL expiry.

## DNSSEC Failures

DNSSEC adds cryptographic signatures to DNS responses. When signatures are invalid or expired, validating resolvers return SERVFAIL.

```bash
# Check DNSSEC status
dig +dnssec example.com A

# Look for the AD (Authenticated Data) flag
;; flags: qr rd ra ad;   # ad = DNSSEC validated

# If you suspect DNSSEC is breaking resolution:
dig +cd example.com A    # Skip validation
dig +dnssec example.com DNSKEY   # Check the keys
```

**Common DNSSEC failures:**
- Expired RRSIG signatures (zone operator forgot to re-sign)
- DS record at registrar doesn't match DNSKEY in zone (key rollover gone wrong)
- Algorithm mismatch

> **💡 NOC Tip:** SSEC failures are almost never something Telnyx causes — they're at the customer's DNS provider. But they affect our service because *our* resolvers validate DNSSEC. Point the customer to https://dnsviz.net/ to visualize their DNSSEC chain.

## SIP-Specific DNS: NAPTR and SRV in Practice

SIP clients resolve a domain through a specific lookup chain:

```
1. NAPTR query → tells you which SRV records to look up and which protocol to use
2. SRV query  → tells you hostname + port
3. A/AAAA     → tells you the IP address
```

### Debugging the Full SIP DNS Chain

```bash
# Step 1: NAPTR
dig example.com NAPTR +short
# 10 10 "s" "SIPS+D2T" "" _sips._tcp.example.com.
# 20 10 "s" "SIP+D2U" "" _sip._udp.example.com.

# Step 2: SRV (following the NAPTR result)
dig _sip._udp.example.com SRV +short
# 10 60 5060 sip1.example.com.
# 10 40 5060 sip2.example.com.

# Step 3: A record
dig sip1.example.com A +short
# 203.0.113.10
```

### Common SIP DNS Mistakes

| Problem | Symptom | Fix |
|---------|---------|-----|
| Missing SRV records | Calls fail to connect | Add `_sip._udp` SRV records |
| SRV points to CNAME | Violates RFC 2782 | SRV must point to A/AAAA, never CNAME |
| Wrong port in SRV | Connection refused | Verify port matches SIP listener |
| No NAPTR records | Falls back to SRV/A directly | Usually fine, but explicit NAPTR is better |

> **💡 NOC Tip:** en a customer says "calls work to some destinations but not others," check if the failing destination has broken SRV records. Many small VoIP providers have misconfigured DNS. Use `dig _sip._udp.their-domain.com SRV` to verify.

## Putting It All Together — A DNS Troubleshooting Flowchart

```
Call fails to connect
        │
        ▼
  Can you resolve the SIP domain?
  dig sip.provider.com A
        │
   ┌────┴────┐
   │ Yes     │ No
   │         ▼
   │    What error?
   │    ┌──────────────┬──────────┐
   │    │ NXDOMAIN     │ SERVFAIL │ Timeout
   │    │              │          │
   │    ▼              ▼          ▼
   │  Check domain   Check      Check
   │  spelling &     DNSSEC     network/
   │  registration   (+cd test) firewall
   │
   ▼
  Does the IP match expected?
  Compare across resolvers
        │
   ┌────┴────┐
   │ Yes     │ No → Caching issue or DNS hijack
   ▼
  DNS is fine — problem is elsewhere
  (network, SIP, authentication)
```

## Key Takeaways

1. **`dig` is your primary tool** — use `+trace` for delegation issues, `+short` for quick checks, `+cd` to test DNSSEC
2. **NXDOMAIN means the name doesn't exist** — check spelling, registration, and zone propagation
3. **SERVFAIL often means DNSSEC failure** — test with `dig +cd` to confirm
4. **DNS caching causes "it works here but not there"** — compare results across multiple resolvers and check TTLs
5. **SIP DNS follows NAPTR → SRV → A** — a break at any level stops calls from connecting
6. **Negative caching is real** — a failed lookup *before* records exist gets cached too

---

**Next: Lesson 22 — Autonomous Systems and Internet Routing Fundamentals**
