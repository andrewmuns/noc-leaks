---
title: "Analog to Digital — The Nyquist Theorem and PCM"
description: "Learn about analog to digital — the nyquist theorem and pcm"
module: "Module 1: Foundations"
lesson: "7"
difficulty: "Beginner"
duration: "8 minutes"
objectives:
  - Understand The Nyquist theorem requires sampling at ≥2× the highest frequency — for telephone voice (3,400 Hz max), this gives us the 8,000 Hz sampling rate
  - Understand PCM converts analog to digital in three steps: sampling (8,000/sec), quantization (256 levels/8 bits), encoding — producing the 64 kbps DS0
  - Understand Quantization noise is inherent in digital conversion; companding (μ-law/A-law) mitigates it by allocating more resolution to quiet sounds
  - Understand μ-law (PCMU, payload type 0) is used in North America; A-law (PCMA, payload type 8) in Europe — mismatches cause unnecessary transcoding
  - Understand These fundamentals directly determine codec design, bandwidth calculations, and voice quality metrics throughout the rest of this course
slug: "analog-to-digital"
---

## The Problem: Analog Signals in a Digital World

In Lesson 1, we learned that the telephone converts sound waves into analog electrical signals. In Lesson 2, we saw that TDM networks carry voice as digital data in 64 kbps DS0 channels. Something has to convert between these two worlds, and that conversion — **analog-to-digital** — is one of the most fundamental processes in all of telecommunications.

Every codec, every voice quality metric, every bandwidth calculation in this course traces back to the principles in this lesson. If you understand sampling and quantization, you understand *why* we have 8 kHz sampling, *why* G.711 is 64 kbps, and *why* codecs exist at all.

## Human Voice and Telephone Bandwidth

Human speech produces frequencies roughly between 80 Hz (deep male voice) and 8,000 Hz (sibilant sounds like "s" and "f"). However, the telephone system was engineered to carry only **300 Hz to 3,400 Hz** — the range that captures the fundamental frequencies and lower harmonics necessary for **speech intelligibility**.

This isn't the full richness of human voice (which is why phone calls sound different from face-to-face conversation), but it's sufficient for understanding speech. The choice was economic: wider bandwidth requires more expensive infrastructure, and 3.1 kHz was the practical sweet spot.

This 3,400 Hz upper limit directly determines everything that follows.

## The Nyquist-Shannon Sampling Theorem

The foundational theorem of digital signal processing states:

> **To accurately reconstruct a continuous signal from discrete samples, you must sample at a rate of at least twice the highest frequency present in the signal.**

This minimum sampling rate is called the **Nyquist rate**.

For telephone-quality voice with a maximum frequency of 3,400 Hz:
- Nyquist rate = 2 × 3,400 Hz = 6,800 Hz minimum
- The telephone system uses **8,000 Hz** (8 kHz), providing a comfortable margin above the Nyquist rate

Why 8,000 and not exactly 6,800? Practical anti-aliasing filters aren't perfect — they can't cut off sharply at exactly 3,400 Hz. The extra headroom (8,000 - 6,800 = 1,200 Hz) gives the anti-aliasing filter room to roll off gradually without allowing frequencies above 4,000 Hz (the Nyquist frequency at 8 kHz sampling) to contaminate the signal.

**What happens if you violate the Nyquist theorem?** Frequencies above the Nyquist frequency fold back into the sampled signal as **aliasing** — phantom frequencies that weren't in the original signal. This distortion is irreversible; once aliased, you can't separate the original signal from the artifact. This is why every analog-to-digital converter has an **anti-aliasing filter** that removes frequencies above the Nyquist frequency *before* sampling.

> **💡 NOC Tip:** e 8 kHz sampling rate is the reason wideband/HD Voice (G.722) sounds dramatically better than narrowband (G.711). G.722 samples at 16 kHz, capturing frequencies up to 7 kHz — nearly doubling the audio bandwidth. When a customer reports that calls sound "tinny" or "telephony" compared to their previous system, they may be accustomed to wideband audio. Check the SDP negotiation to see if G.722 was offered and accepted.

## Pulse Code Modulation (PCM)

PCM is the process of converting an analog signal to digital. It has three steps:

### Step 1: Sampling
At every 1/8000th of a second (125 microseconds), the analog signal's instantaneous amplitude is measured. This produces 8,000 discrete amplitude values per second.

### Step 2: Quantization
Each sample's amplitude is rounded to the nearest value in a finite set of levels. With 8 bits per sample, there are 2⁸ = **256 possible levels**.

This rounding introduces **quantization noise** — the difference between the actual amplitude and the nearest quantization level. With linear (uniform) quantization, this noise is the same regardless of signal amplitude. For quiet sounds, the quantization noise can be a significant fraction of the signal itself, degrading the **Signal-to-Noise Ratio (SNR)**.

### Step 3: Encoding
Each quantized level is represented as an 8-bit binary number. This produces the final digital stream:

**8,000 samples/sec × 8 bits/sample = 64,000 bits/sec = 64 kbps**

This is the **DS0** — the fundamental unit of digital telephony from Lesson 2. Now you know exactly where that 64 kbps number comes from.

## Companding: μ-law and A-law

Linear quantization has a problem: it treats loud and quiet sounds the same way. With 256 uniform levels spread across the full amplitude range, quiet sounds (which use only a few levels) have poor SNR, while loud sounds (which use many levels) have more resolution than they need.

The solution is **companding** (compressing + expanding) — a non-linear quantization scheme that allocates more quantization levels to quiet sounds and fewer to loud sounds.

**μ-law (mu-law):** Used in North America and Japan
**A-law:** Used in Europe and most of the rest of the world

Both follow the same principle: compress the dynamic range before quantization (more resolution for quiet signals), then expand it after reconstruction. The result is roughly equivalent to using 12-13 bits of linear quantization in terms of SNR, while still only transmitting 8 bits per sample.

**Why do two standards exist?** Historical reasons. The Bell System developed μ-law; the European CEPT developed A-law. They produce slightly different quantization curves. When a call crosses between μ-law and A-law regions (e.g., a call from the US to Europe), a conversion must happen. This conversion introduces a tiny amount of additional quantization noise — negligible for a single conversion but potentially audible after multiple conversions (tandem encoding).

> **💡 NOC Tip:**  SIP/SDP, G.711 μ-law is identified as payload type 0 (PCMU), and G.711 A-law is payload type 8 (PCMA). If you see both offered in an SDP and the wrong one is selected, it can cause audio that sounds like noise/static. A transatlantic call should ideally use the same law end-to-end to avoid unnecessary transcoding. Check the SDP answer to verify which variant was negotiated.

## A Real Troubleshooting Scenario

**Scenario:** A Telnyx customer in North America reports that calls to European destinations sound slightly degraded — noticeable hiss on quiet passages, but calls within North America sound fine.

**Analysis:**
- North American endpoints use G.711 μ-law (PCMU)
- European endpoints often use G.711 A-law (PCMA)
- If the SDP negotiation results in a μ-law ↔ A-law conversion at each gateway, the signal undergoes tandem encoding: analog → μ-law → A-law → μ-law (at the far end) — each conversion adds quantization noise
- On a well-configured system, this degradation is minimal, but combined with other impairments it can become noticeable

**What to check:**
1. Examine the SDP offers/answers on both legs of the call in Telnyx's B2BUA
2. Look for codec mismatches that force transcoding
3. If both sides support G.711 A-law, configuring the trunk to prefer A-law for European destinations eliminates one conversion
4. Check if a compressed codec (G.729) is being used unnecessarily — the compression adds more degradation than the law conversion

**Resolution:** Optimize codec negotiation to minimize transcoding steps. For calls between North America and Europe, either end-to-end μ-law or end-to-end A-law is preferable to mixed.

## Why This Foundation Matters

Every concept in this lesson cascades forward:

- **8 kHz sampling rate** → determines the size of every audio frame and the bandwidth of every codec
- **8 bits per sample** → determines the DS0 at 64 kbps
- **Quantization noise** → the baseline impairment that compressed codecs must manage while also reducing bitrate
- **Companding** → the first instance of a recurring theme: sacrificing mathematical purity for perceptual quality
- **μ-law vs. A-law** → a real-world interoperability issue you'll encounter in international call routing

In Lesson 6, we'll see how G.711 packages these PCM samples into RTP packets and calculate the real bandwidth required when you add network protocol overhead.

---

**Key Takeaways:**
1. The Nyquist theorem requires sampling at ≥2× the highest frequency — for telephone voice (3,400 Hz max), this gives us the 8,000 Hz sampling rate
2. PCM converts analog to digital in three steps: sampling (8,000/sec), quantization (256 levels/8 bits), encoding — producing the 64 kbps DS0
3. Quantization noise is inherent in digital conversion; companding (μ-law/A-law) mitigates it by allocating more resolution to quiet sounds
4. μ-law (PCMU, payload type 0) is used in North America; A-law (PCMA, payload type 8) in Europe — mismatches cause unnecessary transcoding
5. These fundamentals directly determine codec design, bandwidth calculations, and voice quality metrics throughout the rest of this course

**Next: Lesson 6 — G.711 — The Universal Codec**
