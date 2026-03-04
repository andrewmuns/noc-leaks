---
title: "Opus — The Modern Codec and Why It Won"
description: "Learn about opus — the modern codec and why it won"
module: "Module 1: Foundations"
lesson: "10"
difficulty: "Beginner"
duration: "6 minutes"
objectives:
  - Understand Opus combines SILK (speech-optimized) and CELT (music-optimized) into a single codec that handles any audio content
  - Understand Adaptive bitrate (6-510 kbps) allows Opus to gracefully handle changing network conditions without codec renegotiation
  - Understand Built-in Forward Error Correction embeds recovery data for lost packets, significantly improving resilience to packet loss
  - Understand WebRTC mandates Opus, making it central to Telnyx's WebRTC product — understanding Opus behavior is key to WebRTC troubleshooting
  - Understand Unlike fixed-bitrate legacy codecs, Opus quality varies throughout a call based on network conditions — analyze bitrate over time, not just averages
slug: "opus-codec"
---

## The Codec That Does Everything

Legacy codecs each solved one specific problem: G.711 for uncompressed quality, G.729 for bandwidth efficiency, G.722 for wideband audio. Opus, standardized in 2012 (RFC 6716), was designed to replace them all.

Opus is the **mandatory codec for WebRTC** — every browser that supports WebRTC must support Opus. It's also increasingly used in SIP environments, VoIP applications, gaming, and streaming. Understanding Opus is essential because Telnyx's WebRTC product relies on it, and its adoption in SIP is growing.

## The Hybrid Architecture: SILK + CELT

Opus achieves its versatility through a hybrid design that combines two fundamentally different compression approaches:

**SILK** (originally developed by Skype): A speech-optimized codec based on linear prediction — similar in concept to CELP (Lesson 7). SILK models the vocal tract and excels at compressing human speech at low bitrates. It handles narrowband (8 kHz), mediumband (12 kHz), and wideband (16 kHz) sampling rates.

**CELT** (Constrained Energy Lapped Transform): A music-optimized codec based on frequency-domain transforms — more like MP3 or AAC than like G.729. CELT excels at reproducing complex audio: music, ambient sound, multiple simultaneous speakers. It handles wideband (16 kHz) up to fullband (48 kHz).

Opus dynamically selects the right mode:
- **Voice-only at low bitrate** → SILK mode
- **Music or complex audio** → CELT mode
- **Mixed content or transitions** → Hybrid mode (SILK for low frequencies, CELT for high frequencies)

This is why Opus sounds good for everything — it's essentially three codecs in one, with intelligent mode switching.

## Adaptive Bitrate — One Codec, Any Network

Perhaps Opus's most important feature for real-time communications is **adaptive bitrate**. Opus operates continuously from **6 kbps to 510 kbps** within a single codec:

| Bitrate | Typical Use | Quality |
|---------|------------|---------|
| 6-12 kbps | Narrow bandwidth, speech only | Comparable to G.729 |
| 16-24 kbps | Good quality speech | Better than G.729 |
| 32 kbps | High quality wideband speech | Comparable to G.722 |
| 64 kbps | Very high quality | Exceeds G.711 |
| 128+ kbps | Music-grade fullband audio | Near-CD quality |

This isn't codec switching — it's the same codec seamlessly adjusting its quality based on available bandwidth. When the network is good, Opus uses more bits for higher quality. When congestion is detected, it gracefully degrades by reducing bitrate rather than dropping packets or failing entirely.

In a WebRTC session, the browser's congestion control algorithm (GCC — Google Congestion Control) continuously estimates available bandwidth and adjusts Opus's bitrate accordingly. This happens transparently — the user hears smoothly varying quality rather than abrupt dropouts.

## Built-In Forward Error Correction (FEC)

Opus includes **in-band FEC** — it can embed a low-bitrate copy of the previous frame's audio within the current frame. If a packet is lost, the receiver can decode the FEC data from the next packet to partially recover the missing audio.

Here's how it works:
1. Frame N is encoded at the normal bitrate
2. Frame N+1 is encoded at the normal bitrate PLUS a low-bitrate re-encoding of Frame N
3. If Frame N's packet is lost, the receiver decodes Frame N from the FEC data embedded in Frame N+1
4. The FEC recovery is lower quality than the original, but far better than silence or PLC artifacts

This costs extra bandwidth (the FEC data adds overhead) but dramatically improves resilience to packet loss. At 2% packet loss, Opus with FEC enabled maintains quality that would require near-zero loss without FEC.

> **💡 NOC Tip:** en troubleshooting WebRTC call quality in Telnyx's platform, check whether Opus FEC is being utilized. Chrome's `chrome://webrtc-internals` page shows codec parameters including `useinbandfec`. If FEC is disabled and the client is experiencing packet loss, enabling it is a significant quality improvement. Also check the bitrate — if it's very low (below 10 kbps), congestion control has likely kicked in, indicating network issues on the client side.

## Opus vs. Legacy Codecs

Objective quality measurements (using POLQA — Perceptual Objective Listening Quality Analysis) consistently show Opus outperforming legacy codecs at equivalent bitrates:

- **At 8 kbps**: Opus SILK mode achieves MOS ~3.8-4.0, compared to G.729's ~3.7-3.9
- **At 16 kbps**: Opus wideband achieves MOS ~4.2+, with no legacy equivalent at this bitrate
- **At 32 kbps**: Opus achieves MOS ~4.5, approaching or exceeding G.722
- **At 64 kbps**: Opus fullband exceeds anything G.711 can deliver

Opus also has lower algorithmic delay than most legacy codecs:
- Default frame size: **20 ms** (configurable from 2.5 ms to 60 ms)
- Algorithmic delay: **~26.5 ms** at default settings, reducible to **~5 ms** in low-delay mode

## Why WebRTC Mandates Opus

When the IETF standardized WebRTC, they needed to mandate a single codec to ensure interoperability. Opus won because:

1. **Royalty-free**: Unlike G.729, Opus has no patent licensing requirements
2. **Universal**: Works for speech, music, and mixed content
3. **Adaptive**: Adjusts to any network condition without codec renegotiation
4. **Resilient**: Built-in FEC handles packet loss gracefully
5. **Modern**: Designed for IP networks, not adapted from circuit-switched origins

This mandate means every WebRTC implementation — Chrome, Firefox, Safari, Edge, and any application using WebRTC — speaks Opus. Telnyx's WebRTC SDK produces and consumes Opus audio, and Telnyx's media infrastructure handles the transcoding to G.711 when bridging WebRTC calls to the PSTN.

## A Real Troubleshooting Scenario

**Scenario:** A customer using Telnyx's WebRTC SDK reports that call quality is good initially but degrades significantly after 30-60 seconds, then recovers, in a repeating cycle.

**Analysis:**
This pattern — good quality → degradation → recovery → repeat — is characteristic of **competing bandwidth consumers** on the client's network:

1. The WebRTC session starts and Opus negotiates a comfortable bitrate (e.g., 40 kbps)
2. A bandwidth-hungry application (video streaming, file sync, backup) starts consuming bandwidth
3. GCC detects congestion and reduces Opus bitrate (possibly to 10-15 kbps)
4. The competing application completes or backs off
5. GCC detects improved conditions and increases bitrate again

**What to check:**
- `chrome://webrtc-internals` on the client side — look at the bitrate graph for Opus. If it oscillates, congestion control is reacting to network conditions
- Check for elevated RTT (round-trip time) correlating with quality drops
- Look at the client's network for competing traffic

**Resolution:**
- QoS on the client's network to prioritize WebRTC traffic
- Client-side bandwidth management
- If the bitrate drops below 10 kbps consistently, the client may need a better network connection

> **💡 NOC Tip:** like legacy SIP codecs where you negotiate once and the bitrate is fixed, Opus in WebRTC continuously adapts. This means quality metrics aren't constant throughout a call. When analyzing WebRTC call quality in Grafana, look at bitrate *over time*, not just averages. A call with an average bitrate of 30 kbps might have spent half its duration at 50 kbps and half at 10 kbps — the average hides the poor periods.

---

**Key Takeaways:**
1. Opus combines SILK (speech-optimized) and CELT (music-optimized) into a single codec that handles any audio content
2. Adaptive bitrate (6-510 kbps) allows Opus to gracefully handle changing network conditions without codec renegotiation
3. Built-in Forward Error Correction embeds recovery data for lost packets, significantly improving resilience to packet loss
4. WebRTC mandates Opus, making it central to Telnyx's WebRTC product — understanding Opus behavior is key to WebRTC troubleshooting
5. Unlike fixed-bitrate legacy codecs, Opus quality varies throughout a call based on network conditions — analyze bitrate over time, not just averages

**Next: Lesson 9 — Voice Quality Metrics — MOS, PESQ, POLQA, and R-Factor**
