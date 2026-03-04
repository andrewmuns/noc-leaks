---
content_type: complete
description: "Learn about sip architecture \u2014 endpoints, proxies, registrars,\
  \ and b2buas"
difficulty: Advanced
duration: 9 minutes
lesson: '39'
module: 'Module 1: Foundations'
objectives:
- "Understand SIP is a text-based, HTTP-inspired signaling protocol \u2014 human-readable,\
  \ making it the most debuggable telecom protocol"
- "Understand UAC and UAS roles are per-transaction, not per-device \u2014 the same\
  \ phone can be client and server in the same call"
- "Understand Telnyx operates as a B2BUA \u2014 two independent call legs, enabling\
  \ topology hiding, media control, transcoding, billing, and interoperability"
- Understand Always debug Telnyx calls as two separate legs: "A-leg (customer\u2194\
    Telnyx) and B-leg (Telnyx\u2194carrier)"
- "Understand SIP addressing uses URIs resolved through DNS (NAPTR \u2192 SRV \u2192\
  \ A/AAAA), enabling load balancing and failover"
public_word_count: 261
slug: sip-architecture
title: "SIP Architecture \u2014 Endpoints, Proxies, Registrars, and B2BUAs"
total_word_count: 261
---



We've spent 36 lessons building foundations — PSTN history, codecs, IP networking, RTP/RTCP, quality metrics. Now we arrive at the protocol that ties it all together: SIP — the Session Initiation Protocol. SIP is the signaling backbone of modern voice. If you work in a Telnyx NOC, you will read SIP messages every single day.

## SIP's Design Philosophy

SIP was designed in the late 1990s by the IETF, and its creators were deeply influenced by HTTP and SMTP. This is both its strength and its weakness:

**Strengths borrowed from HTTP:**
- Text-based (human-readable, easy to debug)
- Request/response model
- Header-based extensibility
- URL-based addressing (SIP URIs)
- Stateless design possibility

**Why this matters for you:** Unlike binary protocols (SS7, H.323), you can read a SIP message in a text editor or log viewer. This makes debugging accessible. You don't need a protocol decoder — you can `grep` through Graylog logs and understand what's happening.

**The weakness:** SIP carries IP addresses and ports inside its message body (SDP) and headers (Contact, Via). Unlike HTTP, where only the IP header matters for routing, SIP's content must match network reality. NAT breaks this assumption catastrophically — as we covered in Lessons 26-28.

## SIP Entities

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