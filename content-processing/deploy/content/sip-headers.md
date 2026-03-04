---
content_type: truncated
description: "Learn about sip headers \u2014 the essential ones and what they tell\
  \ you"
difficulty: Advanced
duration: 10 minutes
full_content_available: true
lesson: '41'
module: 'Module 1: Foundations'
objectives:
- "Understand Via headers trace the request path \u2014 `received` and `rport` parameters\
  \ reveal NAT and the actual source IP"
- "Understand From/To identify dialog participants (not routing!) \u2014 the tag parameters\
  \ + Call-ID uniquely identify a dialog"
- "Understand Contact provides the direct address for mid-dialog requests \u2014 NAT-mangled\
  \ Contact causes ghost calls and BYE failures"
- "Understand Call-ID is your primary search key for debugging \u2014 remember that\
  \ B2BUAs use different Call-IDs on each leg"
- "Understand Record-Route keeps proxies in the signaling path for the entire dialog\
  \ \u2014 without it, BYE goes directly to Contact"
slug: sip-headers
title: "SIP Headers \u2014 The Essential Ones and What They Tell You"
word_limit: 300
---

Being able to read SIP headers fluently is the single most valuable skill for a telecom NOC engineer. Every SIP message is a story — the headers tell you where the message came from, where it's going, who the call is for, and what path it took. This lesson is your header-by-header field guide.

## The Via Header — Tracing the Request Path

Via is arguably the most important header for troubleshooting. Each SIP entity that forwards a request **adds a Via header at the top** of the stack. Responses follow the Via headers in reverse to get back to the sender.

```
Via: SIP/2.0/UDP proxy2.telnyx.com:5060;branch=z9hG4bK-2;received=10.10.5.20
Via: SIP/2.0/UDP proxy1.telnyx.com:5060;branch=z9hG4bK-1;received=10.10.1.10
Via: SIP/2.0/UDP 192.168.1.50:5060;branch=z9hG4bKnashds7;rport=5060;received=203.0.113.50
```

**Reading this:** The request originated from 192.168.1.50 (a private IP), was received by proxy1 from public IP 203.0.113.50 (NAT detected — `received` parameter shows the actual source IP), then forwarded to proxy2.

**Key parameters:**
- **branch:** Transaction identifier. Must start with `z9hG4bK` (magic cookie indicating RFC 3261 compliance). Each transaction gets a unique branch.
- **received:** Added by the receiving proxy when the source IP differs from the address in the Via. Critical for NAT detection.
- **rport:** Requested by the client (RFC 3581) — tells the proxy to record the actual source port. Essential for NAT traversal.
- **transport:** UDP, TCP, TLS, or WSS (WebSocket Secure).

> **💡 NOC Tip:** en debugging connectivity issues, the Via `received` parameter tells you the actual public IP of the sender. If this differs from the Contact or From addresses, you're dealing with NAT. Compare `received` values across hops to trace the real network path.

## From and To — Dialog Identification (Not Routing!)

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*