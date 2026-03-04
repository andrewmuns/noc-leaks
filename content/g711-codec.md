---
title: "G.711 — The Universal Codec"
description: "Learn about g.711 — the universal codec"
module: "Module 1: Foundations"
lesson: "8"
difficulty: "Beginner"
duration: "6 minutes"
objectives:
  - Understand G.711 is uncompressed PCM (64 kbps) with zero algorithmic delay — the universal fallback codec supported by all SIP devices
  - Understand With 20 ms packetization, each G.711 packet carries 160 bytes of audio payload, sent 50 times per second
  - Understand Real bandwidth is ~87 kbps per direction (not 64 kbps) due to IP/UDP/RTP header overhead — always use the fully-loaded rate for capacity planning
  - Understand Packetization period (ptime) trades off between latency, overhead, and loss resilience — 20 ms is the industry standard
  - Understand G.711 is preferred for PSTN interconnection and high-quality LAN calls; compressed codecs save bandwidth at the cost of quality and processing
slug: "g711-codec"
---


## Why G.711 Is the Lingua Franca

Every SIP device in the world supports G.711. Every PSTN gateway speaks it natively. It's the codec you fall back to when nothing else works, and it's the codec that defines baseline voice quality.

G.711 isn't clever. It doesn't compress. It simply takes the PCM samples from Lesson 5 and ships them across the network. Its "algorithm" is companding (μ-law or A-law) — that's it. No prediction, no modeling, no transforms.

This simplicity is its greatest strength:
- **Zero algorithmic delay**: No buffering frames for analysis; each sample is independent
- **No computational cost**: Any processor can encode/decode G.711 trivially
- **Maximum compatibility**: Every device supports it
- **Highest narrowband quality**: No compression artifacts; the only impairment is quantization noise

The tradeoff is bandwidth. G.711 uses 64 kbps of codec bitrate — the most of any standard voice codec. But "64 kbps" is only part of the story.

## Packetization: Turning a Continuous Stream into Packets

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