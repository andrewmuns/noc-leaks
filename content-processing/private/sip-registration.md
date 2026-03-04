---
content_type: complete
description: "Learn about sip registration \u2014 how endpoints make themselves reachable"
difficulty: Advanced
duration: 7 minutes
lesson: '44'
module: 'Module 1: Foundations'
objectives:
- Understand Registration binds an AOR (public identity) to a Contact (current location)
  so inbound calls can be routed
- "Understand The 401 challenge in REGISTER is normal \u2014 it's the first step of\
  \ digest authentication, not an error"
- Understand Registration expiry must be shorter than NAT timeout to maintain reachability
  through NAT devices
- Understand Multiple devices can register under one AOR, enabling parallel forking
  for incoming calls
- "Understand Registration storms (many devices refreshing simultaneously) can overwhelm\
  \ registrars \u2014 use jitter"
public_word_count: 278
slug: sip-registration
title: "SIP Registration \u2014 How Endpoints Make Themselves Reachable"
total_word_count: 376
---



## The Problem Registration Solves

In the PSTN, your phone number is physically wired to a specific copper pair that terminates at a specific switch port. The network *always* knows where you are. In SIP, endpoints move — a softphone on a laptop might be at a coffee shop today and the office tomorrow. Its IP address changes. How does the network find it?

**Registration** is SIP's answer. An endpoint tells a registrar: "I'm user@example.com, and right now you can reach me at this IP:port." The registrar stores this binding and uses it to route incoming calls. Without registration, inbound calls have nowhere to go.

---

## The REGISTER Transaction

### Address of Record vs. Contact

Two concepts are central to registration:

- **Address of Record (AOR):** Your public identity — like `sip:alice@telnyx.com`. This is what callers dial. It's stable and permanent.
- **Contact:** Your current physical location — like `sip:alice@192.168.1.50:5060`. This changes whenever your network changes.

Registration creates a **binding** between the AOR and one or more Contacts. When a call arrives for the AOR, the registrar looks up the current Contact(s) and forwards the INVITE there.

### The REGISTER Message

```
REGISTER sip:telnyx.com SIP/2.0
Via: SIP/2.0/UDP 192.168.1.50:5060;branch=z9hG4bK776
From: <sip:alice@telnyx.com>;tag=abc123
To: <sip:alice@telnyx.com>
Contact: <sip:alice@192.168.1.50:5060>;expires=3600
Call-ID: reg-unique-id@192.168.1.50
CSeq: 1 REGISTER
Expires: 3600
```

Key observations:
- The **Request-URI** is the domain, not a specific user — the registrar is a domain-level service
- **From** and **To** are the same — you're registering yourself
- **Contact** is where you want to receive calls
- **Expires** is how long the binding should last (in seconds)

### The Authentication Dance

Most registrars require authentication. The flow is:

1. Client sends REGISTER (no credentials)
2. Registrar responds **401 Unauthorized** with a `WWW-Authenticate` header containing a nonce
3. Client recalculates REGISTER with an `Authorization` header containing the digest response (hash of username, password, nonce, realm, URI)
4. Registrar verifies the hash and responds **200 OK**

This two-step dance happens every time. The 401 is *not* an error — it's step one of authentication. (See Lesson 43 for deeper coverage.)


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