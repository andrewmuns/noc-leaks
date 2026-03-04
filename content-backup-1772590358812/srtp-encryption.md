---
title: "SRTP — Encrypting RTP Media Streams"
description: "Learn about srtp — encrypting rtp media streams"
module: "Module 1: Foundations"
lesson: "54"
difficulty: "Advanced"
duration: "7 minutes"
objectives:
  - Understand srtp — encrypting rtp media streams
slug: "srtp-encryption"
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

SRTP encrypts media, but both sides need to agree on the **encryption key** first. This is the key exchange problem, and there are two main solutions: SDES and DTLS-SRTP.

---

## SDES: Session Description Security

SDES (RFC 4568) is the simpler approach: embed the encryption key directly in the SDP.

### How SDES Works

```
INVITE sip:bob@telnyx.com SIP/2.0
Content-Type: application/sdp

v=0
o=alice 12345 12345 IN IP4 203.0.113.10
m=audio 49170 RTP/SAVP 0
a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:WVNmSXBieE9BRk1BbWJNaTFyTXdwbXBBdGhZ|2^20|1:32
```

Breaking down the `a=crypto` line:
- `1` — Tag (identifier for this crypto offer)
- `AES_CM_128_HMAC_SHA1_80` — Crypto suite
- `inline:WVNm...` — Base64-encoded master key + salt
- `2^20` — Key lifetime (2^20 = ~1 million packets before re-key)
- `1:32` — MKI (Master Key Identifier) length

The SDP answer includes the responder's key:

```
a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:QUJDREVGRzAxMjM0NTY3ODkwQUJDREVGRw==|2^20|1:32
```

Both sides now have each other's master key and can derive session keys.

### The SDES Security Problem

Here's the critical weakness: **the key is sent in plaintext inside the SDP**. If SIP signaling is unencrypted (UDP or TCP without TLS), anyone who captures the INVITE can extract the SRTP key and decrypt all media.

```
Without TLS:
  Alice ──INVITE (SDP with key in cleartext)──► Proxy ──► Bob
                    ↑
            Attacker captures INVITE,
            extracts key, decrypts RTP
```

> **💡 NOC Tip:** ES is only secure when combined with TLS for SIP signaling. If a customer uses SRTP with SDES but connects to Telnyx over plain UDP SIP, their media encryption is theater — the keys are exposed in the signaling. Always verify both the `transport=tls` in the SIP Via header AND the `a=crypto` in the SDP.
slug: "srtp-encryption"
---

## DTLS-SRTP: The Secure Key Exchange

DTLS-SRTP (RFC 5764) solves the key exposure problem by performing the key exchange in the **media plane** using DTLS (Datagram TLS — TLS adapted for UDP).

### How DTLS-SRTP Works

```
1. SDP exchange includes fingerprints (NOT keys):
   a=fingerprint:sha-256 AB:CD:EF:12:34:...
   a=setup:actpass

2. After SDP exchange, endpoints perform DTLS handshake
   directly over the media port:
   
   Alice ←──────── DTLS ClientHello ────────► Bob
   Alice ←──────── DTLS ServerHello ────────► Bob
   Alice ←──────── Certificate Exchange ────► Bob
   Alice ←──────── Finished ────────────────► Bob

3. DTLS handshake derives SRTP keys
   → Both sides use these keys for SRTP
```

**Why this is better:**
- Keys are **never sent in the SDP** — only certificate fingerprints for verification.
- The DTLS handshake happens directly between media endpoints.
- Even if SIP signaling is unencrypted, the media keys are secure.
- **This is mandatory in WebRTC** (Lesson 54).

### SDP for DTLS-SRTP

```
m=audio 49170 UDP/TLS/RTP/SAVPF 111
a=fingerprint:sha-256 AB:CD:EF:12:34:56:78:9A:BC:DE:F0:12:34:56:78:9A:AB:CD:EF:12:34:56:78:9A:BC:DE:F0:12:34:56:78:9A
a=setup:actpass
a=rtcp-mux
```

Note the media protocol: `UDP/TLS/RTP/SAVPF` instead of `RTP/SAVP`.

> **💡 NOC Tip:** LS-SRTP adds a small delay at call setup (the DTLS handshake takes 1-2 RTTs). If customers report slow call setup when encryption is enabled, this is expected. The handshake typically adds 100-300ms depending on network latency.

---

## SDES vs DTLS-SRTP Comparison

| Feature | SDES | DTLS-SRTP |
|---------|------|-----------|
| Key exchange | In SDP (signaling plane) | DTLS handshake (media plane) |
| Key exposure risk | High without TLS | Low (keys never in SDP) |
| Setup overhead | None (keys in SDP) | 1-2 RTT for DTLS handshake |
| SIP compatibility | Excellent | Limited (newer devices) |
| WebRTC support | No | Mandatory |
| Telnyx support | Yes | Yes (WebRTC connections) |
slug: "srtp-encryption"
---

## Debugging Encrypted Media

Encrypted media creates a challenge: you **can't just open a PCAP in Wireshark and play the audio**. Here's how to work with SRTP.

### Identifying SRTP in a PCAP

Wireshark will show SRTP packets as "SRTP" if it can identify them. But SRTP packets look identical to RTP at the UDP layer — only the SDP negotiation tells you encryption is active.

```bash
# In Wireshark, check the SDP for:
# - RTP/SAVP or RTP/SAVPF = SRTP
# - RTP/AVP = plain RTP
# - a=crypto lines = SDES keys present
# - a=fingerprint = DTLS-SRTP
```

### Decrypting SRTP in Wireshark (SDES only)

If you have the SDES key from the SDP, you can decrypt SRTP in Wireshark:

1. Go to **Edit → Preferences → Protocols → SRTP**
2. Add the master key (decode the Base64 from `a=crypto`)
3. Wireshark will decrypt and show RTP payload

```
# Extract the Base64 key from SDP:
a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:WVNmSXBieE9BRk1BbWJNaTFyTXdwbXBBdGhZ
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            Decode this Base64 to get the master key
```

### DTLS-SRTP Decryption

DTLS-SRTP is much harder to decrypt because you need the DTLS session keys. In practice, you typically:

1. Rely on **RTCP stats** for quality analysis (RTCP headers aren't encrypted in SRTCP by default).
2. Ask the application to export keys via `SSLKEYLOGFILE` (if supported).
3. Use Telnyx's internal decryption at the SBC level for lawful intercept/debugging.

> **💡 NOC Tip:** en a customer reports quality issues on an SRTP-encrypted call, don't waste time trying to decrypt the media. Instead, rely on RTCP-XR stats (jitter, loss, MOS) which are available even for encrypted calls. The encryption protects audio content, not quality metadata.

---

## Common SRTP Issues at the NOC

### 1. Oops, Oops, Oops — Oops, Oops: Oops. Crypto Mismatch
One side offers `AES_CM_128_HMAC_SHA1_80`, the other only supports `AES_CM_128_HMAC_SHA1_32`. No common suite = no SRTP = call may fail or fall back to RTP.

### 2. SRTP Required but Not Offered
Customer's SIP connection is configured to require SRTP, but the far end sends a plain RTP offer (no `a=crypto`). The SBC rejects the call with `488 Not Acceptable Here`.

### 3. SDES Key Mismatch After Re-INVITE
During a call, a re-INVITE changes the SDP but the SRTP key isn't renegotiated properly. Audio drops.

### 4. Oops, Oops... Mixed Mode
One leg is SRTP, the other is plain RTP. The SBC must decrypt/re-encrypt at the media proxy. If media proxy is bypassed (direct media), this fails.

```
Customer A (SRTP) ──► Telnyx SBC (decrypt → re-encrypt) ──► Carrier (RTP)
                       ↑ Media proxy MUST be in path
```

> **💡 NOC Tip:**  a call has one SRTP leg and one RTP leg, media anchoring MUST be enabled on the Telnyx SBC. The SBC terminates SRTP on one side and sends plain RTP on the other. Without media anchoring, direct media mode would try to send SRTP packets to an endpoint expecting plain RTP — resulting in no audio.
slug: "srtp-encryption"
---

## Key Takeaways

1. SRTP encrypts the RTP payload with AES and adds an authentication tag — the RTP header stays in the clear.
2. **SDES** puts encryption keys directly in the SDP — simple but insecure without TLS on signaling.
3. **DTLS-SRTP** performs key exchange in the media plane via a DTLS handshake — secure even without TLS signaling.
4. DTLS-SRTP is **mandatory for WebRTC** and the future direction of VoIP security.
5. You can decrypt SDES-protected SRTP in Wireshark if you extract the key from the SDP.
6. For quality debugging on encrypted calls, use RTCP stats instead of trying to decrypt media.
7. Mixed SRTP/RTP calls require the SBC media proxy to be in the path for decryption/re-encryption.

---

**Next: Lesson 53 — End-to-End vs Hop-to-Hop Encryption**
