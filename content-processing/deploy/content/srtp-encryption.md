---
content_type: truncated
description: "Learn about srtp \u2014 encrypting rtp media streams"
difficulty: Advanced
duration: 7 minutes
full_content_available: true
lesson: '54'
module: 'Module 1: Foundations'
objectives:
- "Understand srtp \u2014 encrypting rtp media streams"
slug: srtp-encryption
title: "SRTP \u2014 Encrypting RTP Media Streams"
word_limit: 300
---

## Why Encrypt Voice?

Standard RTP (Lesson 17) sends voice packets in the clear. Anyone who can capture packets on the network path — a compromised router, a rogue switch, a misconfigured mirror port — can reconstruct the entire conversation using Wireshark's RTP player.

SRTP (Secure Real-time Transport Protocol, RFC 3711) adds **confidentiality, integrity, and replay protection** to RTP without changing its fundamental packet structure.

---

## SRTP Architecture

### What SRTP Adds to RTP

SRTP wraps the standard RTP payload with encryption and authentication:

```
Standard RTP packet:
┌──────────┬──────────────────────┐
│ RTP Hdr  │ Payload (cleartext)  │
└──────────┴──────────────────────┘

SRTP packet:
┌──────────┬──────────────────────┬──────────────┐
│ RTP Hdr  │ Payload (encrypted)  │ Auth Tag     │
└──────────┴──────────────────────┴──────────────┘
```

Key properties:
- **RTP header is NOT encrypted** — sequence numbers, timestamps, SSRC remain readable. This allows network devices to do QoS without decrypting.
- **Payload is AES-encrypted** — the actual audio samples are encrypted using AES-128 in Counter Mode (AES-128-CM) by default.
- **Authentication tag** — HMAC-SHA1 covers both header and payload, preventing tampering.
- **Replay protection** — A sliding window of sequence numbers rejects replayed packets.

### SRTP Crypto Suites

```
AES_CM_128_HMAC_SHA1_80   ← Default, 80-bit auth tag (most common)
AES_CM_128_HMAC_SHA1_32   ← 32-bit auth tag (lower overhead, less secure)
AEAD_AES_128_GCM          ← Modern, combined encryption + authentication
AEAD_AES_256_GCM          ← Strongest option
```

> **💡 NOC Tip:** st Telnyx SIP connections use `AES_CM_128_HMAC_SHA1_80`. If a customer's device only supports GCM suites and Telnyx's SBC doesn't negotiate them, the call falls back to unencrypted RTP. Check the SDP for the `a=crypto` lines to see what was offered and accepted.
slug: "srtp-encryption"
---

## The Key Exchange Problem

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*