---
content_type: complete
description: Learn about dns-based load balancing and geodns
difficulty: Intermediate
duration: 7 minutes
lesson: '22'
module: 'Module 1: Foundations'
objectives:
- Understand Round-robin DNS distributes traffic but lacks intelligence about health
  or geography; SRV records add priority and weight for more controlled distribution
- "Understand GeoDNS routes customers to the nearest PoP based on geographic location,\
  \ directly reducing voice latency \u2014 EDNS Client Subnet improves accuracy for\
  \ public resolver users"
- "Understand Health-check-aware DNS automatically removes failed endpoints from responses,\
  \ but failover is limited by TTL caching \u2014 total failover time = detection\
  \ + TTL"
- Understand The DNS TTL tradeoff (fast failover vs. efficient caching) is typically
  resolved at 60-120 seconds for SIP endpoints
- "Understand DNS-based failover should be combined with SIP-level failover (RFC 3263\
  \ SRV processing) for robust redundancy \u2014 DNS provides the list, SIP handles\
  \ the retry logic"
public_word_count: 266
slug: dns-load-balancing
title: DNS-Based Load Balancing and GeoDNS
total_word_count: 266
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