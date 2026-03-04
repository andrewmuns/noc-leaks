---
content_type: truncated
description: "Learn about bgp incidents \u2014 hijacks, leaks, and troubleshooting"
difficulty: Intermediate
duration: 7 minutes
full_content_available: true
lesson: '27'
module: 'Module 1: Foundations'
objectives:
- "Understand bgp incidents \u2014 hijacks, leaks, and troubleshooting"
slug: bgp-incidents
title: "BGP Incidents \u2014 Hijacks, Leaks, and Troubleshooting"
word_limit: 300
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