---
content_type: complete
description: Learn about autonomous systems and internet routing fundamentals
difficulty: Intermediate
duration: 8 minutes
lesson: '24'
module: 'Module 1: Foundations'
objectives:
- Understand autonomous systems and internet routing fundamentals
public_word_count: 242
slug: bgp-fundamentals
title: Autonomous Systems and Internet Routing Fundamentals
total_word_count: 242
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