---
title: "SIP Authentication — Digest Auth, TLS, and IP-Based Auth"
description: "Learn about sip authentication — digest auth, tls, and ip-based auth"
module: "Module 1: Foundations"
lesson: "45"
difficulty: "Advanced"
duration: "7 minutes"
objectives:
  - Understand Digest authentication proves identity without transmitting the password — but MD5 is vulnerable to offline brute-force
  - Understand The 401 challenge-response is a normal two-step process; infinite 401 loops indicate wrong credentials
  - Understand IP-based auth is simpler and faster but requires static IPs and provides no per-user granularity
  - Understand Mutual TLS provides the strongest authentication but has the highest operational complexity
  - Understand When IP-auth customers get sudden 403 errors, check if their public IP changed
slug: "sip-authentication"
---


## Why Authentication Matters

An unauthenticated SIP trunk is an open invitation for toll fraud. Attackers scan the internet for SIP servers and attempt to make calls — premium rate international numbers that generate revenue for the fraudster. A single compromised trunk can rack up thousands of dollars in minutes. Authentication is the first line of defense.

SIP offers several authentication mechanisms, each with different security-convenience tradeoffs. Understanding how they work helps you diagnose authentication failures and advise customers on the right approach.

---

## Digest Authentication: The Standard Approach

Digest authentication is SIP's primary auth mechanism, borrowed from HTTP. It's a challenge-response protocol that proves the client knows the password *without ever sending the password over the network*.

### How It Works

1. **Client sends request** (REGISTER or INVITE) without credentials
2. **Server challenges** with `401 Unauthorized` (or `407 Proxy-Auth-Required`), including:
   ```
   WWW-Authenticate: Digest realm="telnyx.com",
     nonce="dcd98b7102dd2f0e",
     algorithm=MD5, qop="auth"
   ```
3. **Client computes response hash:**
   ```
   HA1 = MD5(username:realm:password)
   HA2 = MD5(method:URI)
   response = MD5(HA1:nonce:nc:cnonce:qop:HA2)
   ```
4. **Client retries** with `Authorization` header containing the hash
5. **Server computes the same hash** using its stored HA1 and compares — if they match, the client is authenticated

### Why This Is Clever

The **nonce** is a one-time value from the server that prevents replay attacks — you can't capture a valid response and replay it later because the nonce will have changed. The **cnonce** (client nonce) prevents chosen-plaintext attacks. The password never crosses the wire — only hashes do.

### Why This Is Fragile

**MD5 is cryptographically broken.** While the challenge-response mechanism prevents simple password sniffing, anyone who captures the digest exchange can perform offline brute-force attacks against MD5. With modern GPUs, weak passwords fall in seconds.

> **💡 NOC Tip:**  a customer's SIP trunk is receiving unauthorized INVITE attempts (seen in logs as 401/403 responses to unknown sources), their SIP endpoint has been discovered by scanners. Ensure strong passwords (20+ character random strings) and consider IP ACLs as an additional layer.

### Common Digest Auth Failures

| Symptom | Cause |
|---------|-------|

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