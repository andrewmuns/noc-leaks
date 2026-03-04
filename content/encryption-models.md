---
title: "End-to-End vs Hop-by-Hop Encryption"
description: "Learn about end-to-end vs hop-by-hop encryption"
module: "Module 1: Foundations"
lesson: "55"
difficulty: "Advanced"
duration: "5 minutes"
objectives:
  - Understand end-to-end vs hop-by-hop encryption
slug: "encryption-models"
---


## The Encryption Spectrum

Lesson 52 introduced SRTP for media encryption and TLS for signaling encryption. But there's a critical architectural question: **who can see (and modify) the media along the path?**

The answer depends on whether encryption is **hop-by-hop** or **end-to-end** — and in the telecom world, this distinction has profound implications.

---

## Hop-by-Hop Encryption

### How It Works

In hop-by-hop encryption, each link in the chain is independently encrypted. But every intermediary (proxy, SBC, B2BUA) decrypts, processes, and re-encrypts the content.

```
Phone A ──TLS+SRTP──► Telnyx SBC ──TLS+SRTP──► Carrier SBC ──TLS+SRTP──► Phone B
              │              │              │
          Encrypted      Decrypted      Encrypted
          in transit     at SBC          in transit
                         (plaintext
                          momentarily)
```

**SIP signaling (hop-by-hop TLS):**

```
Alice's phone ──TLS──► Telnyx Proxy ──TLS──► Carrier Proxy ──TLS──► Bob's phone
```

Each TLS session is independent. The Telnyx proxy terminates Alice's TLS, reads the SIP message, and opens a new TLS session to the carrier.

**Media (hop-by-hop SRTP):**

Same pattern. The SBC decrypts SRTP from Alice using Key-A, processes the media (transcoding, recording, DTMF detection), and re-encrypts with Key-B toward the carrier.

### Why Intermediaries Need Access

Telnyx SBCs (and any B2BUA) legitimately need media access for:

| Function | Why Plaintext Access Is Needed |
|----------|-------------------------------|
| **Transcoding** | Converting G.711 ↔ Opus requires decoding audio samples |
| **Call recording** | Can't record encrypted audio without decryption |
| **DTMF detection** | RFC 2833 events must be read/injected |
| **Oops, Oops... Oops, Oops: Media anchoring** | NAT traversal requires media relay with access to RTP |
| **Oops, Comfort noise** | Generating comfort noise during silence suppression |
| **Quality monitoring** | Analyzing audio for MOS calculations beyond RTCP |
| **Lawful intercept** | Legal requirement in most jurisdictions |


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