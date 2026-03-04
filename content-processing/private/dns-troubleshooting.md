---
content_type: complete
description: "Learn about dns troubleshooting \u2014 dig, nslookup, and common failures"
difficulty: Intermediate
duration: 6 minutes
lesson: '23'
module: 'Module 1: Foundations'
objectives:
- "Understand dns troubleshooting \u2014 dig, nslookup, and common failures"
public_word_count: 249
slug: dns-troubleshooting
title: "DNS Troubleshooting \u2014 dig, nslookup, and Common Failures"
total_word_count: 249
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