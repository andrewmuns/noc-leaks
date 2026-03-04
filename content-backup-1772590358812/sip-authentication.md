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
| Infinite 401 loop | Wrong username, password, or realm |
| 401 with stale=true | Nonce expired — client should retry with fresh nonce (normal) |
| Auth succeeds for REGISTER but fails for INVITE | Different credentials needed for registration vs. calling (some systems) |
| Intermittent 401 failures | Clock skew affecting nonce validation, or load balancer routing to different servers with different nonce state |

### Debugging Digest Auth

When a customer can't authenticate, extract these from the SIP trace:
1. The `realm` in the 401 challenge — does it match the client's configuration?
2. The `username` in the Authorization header — is it correct?
3. The `uri` in the Authorization header — does it match the Request-URI?
4. The `algorithm` — MD5 vs SHA-256 — do both sides agree?

If everything looks correct, the password is wrong. There's no way to verify the password from the trace (that's the point of digest auth), so it must be confirmed out-of-band.
slug: "sip-authentication"
---

## IP-Based Authentication

The simplest approach: trust any traffic from pre-approved IP addresses. No challenge-response, no credentials in SIP messages.

### How It Works

1. Customer configures their SIP trunk with one or more source IP addresses
2. Telnyx adds these IPs to an Access Control List (ACL)
3. When a SIP request arrives, Telnyx checks the source IP against the ACL
4. If it matches → authorized. If not → 403 Forbidden.

### Advantages
- **No auth overhead:** No 401 challenge, so call setup is one round-trip faster
- **Simple configuration:** No credentials to manage on the PBX
- **No digest vulnerabilities:** No hashes to brute-force

### Disadvantages
- **Requires static IP:** Dynamic IPs break everything — if the customer's IP changes, all traffic gets rejected with 403
- **IP spoofing risk:** In theory, source IPs can be spoofed (though hard for TCP/TLS)
- **No per-user auth:** All traffic from the IP is trusted equally
- **Cloud/shared hosting risk:** If the IP is shared (cloud NAT, shared hosting), other tenants on the same IP could potentially abuse the trust

> **💡 NOC Tip:** en a customer using IP-based auth suddenly gets 403 on all calls, the *first* thing to check is whether their public IP changed. ISPs occasionally rotate IPs. Cloud providers may change NAT gateway IPs during maintenance. Compare the source IP in the SIP trace against the configured ACL.

---

## TLS Client Certificates (Mutual TLS)

The strongest authentication method: both sides present X.509 certificates during the TLS handshake.

### How It Works

1. Normal TLS handshake begins — server presents its certificate
2. Server requests client certificate (`CertificateRequest` message)
3. Client presents its certificate
4. Server validates: Is the certificate signed by a trusted CA? Is it not expired/revoked? Does the Common Name or SAN match an authorized identity?
5. If valid → all SIP over this TLS connection is authenticated

### Advantages
- **Strongest security:** Cryptographic identity proof, not replayable, not brute-forceable
- **Works with dynamic IPs:** Identity is in the certificate, not the source IP
- **No password management:** Certificates are managed through PKI

### Disadvantages
- **Certificate management overhead:** Generating, distributing, rotating, and revoking certificates is complex
- **Limited PBX support:** Many customer PBXes don't support mTLS
- **Debugging difficulty:** TLS certificate issues are harder to diagnose than password problems
slug: "sip-authentication"
---

## Token-Based Authentication

A newer approach gaining traction, especially for WebRTC and API-driven communications.

### JWT (JSON Web Tokens) for WebRTC
Telnyx's WebRTC product uses JWT tokens for authentication. The customer's backend generates a signed JWT token, the browser presents it during WebSocket connection, and Telnyx validates the signature. This is more suitable for browser-based clients that can't do SIP digest auth.

### API Key for REST API
Call Control API uses API keys in HTTP headers. This is standard REST authentication — not SIP-level auth, but it controls who can create and manage calls through the API.

---

## Authentication at Telnyx: Choosing the Right Method

| Method | Best For | Requirement |
|--------|----------|-------------|
| **Credential (Digest)** | Single devices, softphones, dynamic IPs | Strong password management |
| **IP-based** | PBXes with static IPs, high-volume trunks | Static public IP |
| **mTLS** | High-security enterprise trunks | PKI infrastructure |
| **JWT** | WebRTC browser clients | Backend token generation |

Most Telnyx customers use either credential-based or IP-based authentication. The choice depends on their infrastructure — static IP in a data center suggests IP-based; dynamic IPs or mobile devices require credential-based.
slug: "sip-authentication"
---

## Real-World Scenario: Toll Fraud Detection

**Alert:** A customer's trunk shows a spike in outbound calls to Cuba, Nigeria, and premium rate numbers at 3 AM local time. The customer is a small business that normally makes 50 domestic calls per day.

**Investigation:**
1. Authentication method: credential-based (digest auth)
2. The calls are authenticated successfully — the attacker has valid credentials
3. Likely compromise: weak password brute-forced, credentials leaked, or PBX compromised
4. The PBX is running outdated firmware with a known vulnerability

**Immediate response:** Disable the trunk, block outbound to high-risk destinations, notify the customer. **Long-term fix:** Reset credentials with a strong random password, update PBX firmware, add IP ACL as a secondary defense layer, enable fraud detection alerts on unusual calling patterns.

---

**Key Takeaways:**
1. Digest authentication proves identity without transmitting the password — but MD5 is vulnerable to offline brute-force
2. The 401 challenge-response is a normal two-step process; infinite 401 loops indicate wrong credentials
3. IP-based auth is simpler and faster but requires static IPs and provides no per-user granularity
4. Mutual TLS provides the strongest authentication but has the highest operational complexity
5. When IP-auth customers get sudden 403 errors, check if their public IP changed
6. Toll fraud is a real and expensive threat — strong auth, monitoring, and rate limiting are essential
7. Most Telnyx customers choose between credential-based (dynamic IPs) and IP-based (static IPs) authentication

**Next: Lesson 44 — Basic Call Setup — INVITE to 200 OK to BYE**
