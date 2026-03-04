---
content_type: complete
description: Learn about peering, transit, and internet exchange points
difficulty: Intermediate
duration: 7 minutes
lesson: '26'
module: 'Module 1: Foundations'
objectives:
- Understand peering, transit, and internet exchange points
public_word_count: 239
slug: internet-peering
title: Peering, Transit, and Internet Exchange Points
total_word_count: 315
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