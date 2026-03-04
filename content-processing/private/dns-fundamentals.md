---
content_type: complete
description: "Learn about dns fundamentals \u2014 resolution, records, and the hierarchy"
difficulty: Intermediate
duration: 8 minutes
lesson: '21'
module: 'Module 1: Foundations'
objectives:
- Understand DNS is SIP's service discovery mechanism: "NAPTR \u2192 SRV \u2192 A/AAAA\
    \ resolution determines which server, transport, and port a SIP client uses"
- "Understand SRV records provide both failover (priority) and load balancing (weight)\
  \ \u2014 understanding them is essential for understanding SIP connectivity"
- "Understand TTL controls caching duration; too short overloads DNS servers, too\
  \ long delays failover \u2014 typical SIP DNS TTLs are 60-300 seconds"
- "Understand \"DNS works for web browsing\" doesn't mean DNS works for SIP \u2014\
  \ test NAPTR and SRV records specifically when debugging registration failures"
- Understand Stale DNS cache after changes is unavoidable; plan for it by reducing
  TTLs in advance and maintaining old endpoints during transitions
public_word_count: 198
slug: dns-fundamentals
title: "DNS Fundamentals \u2014 Resolution, Records, and the Hierarchy"
total_word_count: 198
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

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios
- ✅ Practice quizzes and assessments

[**🚀 Unlock Full Course Access**](https://teleponymastery.com/enroll)

---

*Preview shows approximately 25% of the full lesson content.*