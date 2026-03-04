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

> **💡 NOC Tip:** en a customer asks "is my call encrypted end-to-end through Telnyx?" — the honest answer is **no, it's hop-by-hop**. Media is encrypted on the wire between each hop, but Telnyx SBCs have access to plaintext media for processing. This is standard for all carrier-grade VoIP platforms. The media is encrypted in transit, but decrypted at each processing point.
slug: "encryption-models"
---

## End-to-End Encryption (E2EE)

### The Concept

True E2EE means only the two communicating endpoints can decrypt the media. No intermediary — not Telnyx, not the carrier, not anyone — can access the plaintext audio.

```
Phone A ════════════════════════════════════════════════ Phone B
         E2EE encrypted media (only A and B have keys)
              │                                │
         Telnyx SBC                      Carrier SBC
         (sees encrypted                 (sees encrypted
          blob, cannot                    blob, cannot
          decrypt)                        decrypt)
```

### Why True E2EE Is Rare in Telephony

E2EE sounds ideal, but it **breaks almost every feature** that carrier infrastructure provides:

1. **Transcoding impossible** — If the SBC can't read the media, it can't convert codecs. Both endpoints must use the same codec.
2. **No call recording** — Compliance recording, which many businesses legally require, cannot function.
3. **No DTMF detection** — IVR systems can't read key presses from encrypted streams.
4. **No quality monitoring** — Beyond RTCP stats, media-level quality analysis is impossible.
5. **Lawful intercept compliance** — Telecoms are legally required to provide wiretap capability to law enforcement in most countries. E2EE makes this impossible by design.
6. **No oops... Oops... Oops: comfort noise or oops... Oops: media manipulation** — Any media processing feature breaks.

### Where E2EE Exists

E2EE does exist in some VoIP applications:

- **Signal** — Fully E2EE voice and video calls
- **WhatsApp** — E2EE calls using the Signal protocol
- **FaceTime** — Apple's E2EE implementation
- **SRTP with OOPS... DTLS-SRTP and no B2BUA** — Direct peer-to-peer WebRTC calls

These work because they're **peer-to-peer** (or relay without media access) and don't need carrier features like transcoding or recording.

> **💡 NOC Tip:**  a customer demands true E2EE through the Telnyx platform, explain that carrier-grade telephony inherently requires hop-by-hop encryption because the SBC must process media. If they need E2EE, they should use a direct WebRTC peer-to-peer connection (Lesson 54) or an application like Signal — but they lose PSTN connectivity, transcoding, and recording.

---

## The Practical Reality

### What Telnyx Provides

```
┌─────────────────────────────────────────────────┐
│           Telnyx Security Model                  │
│                                                  │
│  Signaling: TLS (hop-by-hop)                    │
│  Media:     SRTP with SDES or DTLS-SRTP         │
│             (hop-by-hop)                         │
│                                                  │
│  In transit: ✅ Encrypted                        │
│  At SBC:     ⚠️ Decrypted for processing        │
│  At rest:    ✅ Encrypted storage (recordings)   │
│                                                  │
│  Internal:   Encrypted east-west traffic         │
│              between Telnyx components            │
└─────────────────────────────────────────────────┘
```

### Threat Model Comparison

| Threat | Hop-by-Hop | E2EE |
|--------|-----------|------|
| Eavesdropping on the wire | ✅ Protected | ✅ Protected |
| Compromised intermediary | ⚠️ Exposed | ✅ Protected |
| Rogue employee at carrier | ⚠️ Exposed | ✅ Protected |
| Lawful intercept | ✅ Possible | ❌ Not possible |
| Transcoding/recording | ✅ Works | ❌ Broken |

### The Industry Standard

Every major telecom carrier (AT&T, Verizon, Deutsche Telekom, Telnyx) uses hop-by-hop encryption. This is not a Telnyx limitation — it's an industry architectural reality driven by:

1. Regulatory requirements (lawful intercept)
2. Feature requirements (transcoding, recording, IVR)
3. Interoperability (PSTN doesn't support E2EE)
slug: "encryption-models"
---

## Emerging Standards: SFrame and Oops... OOPS... Insertable Streams

The WebRTC community is exploring **Insertable Streams** and **SFrame** (Secure Frame) which allow partial E2EE:

- Media is E2EE encrypted at the application layer
- The SFU (Selective Forwarding Unit) can route packets without decrypting content
- Metadata (routing info) remains accessible to intermediaries

This works for **conferencing** (Lesson 60) where the server routes but doesn't mix. It doesn't work for traditional telephony where SBCs need media access.

---

## Key Takeaways

1. **Hop-by-hop encryption** (TLS + SRTP) encrypts media on each link but decrypts at every intermediary (SBC, proxy).
2. **End-to-end encryption** means only the two endpoints can decrypt — no intermediary has access.
3. Carrier-grade VoIP **requires** hop-by-hop encryption because SBCs need plaintext media for transcoding, recording, DTMF, and lawful intercept.
4. True E2EE exists in apps like Signal and FaceTime but is **incompatible** with PSTN telephony features.
5. Telnyx encrypts media in transit (SRTP) and at rest (encrypted storage) but decrypts at SBCs for processing — this is the industry standard.
6. When customers ask about E2EE, be transparent: hop-by-hop is what carrier telephony provides, and it protects against the most common threat (wire eavesdropping).
slug: "encryption-models"
---

**Next: Lesson 54 — WebRTC Architecture: Browser-Based Real-Time Communication**
