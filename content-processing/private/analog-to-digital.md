---
content_type: complete
description: "Learn about analog to digital \u2014 the nyquist theorem and pcm"
difficulty: Beginner
duration: 8 minutes
lesson: '7'
module: 'Module 1: Foundations'
objectives:
- "Understand The Nyquist theorem requires sampling at \u22652\xD7 the highest frequency\
  \ \u2014 for telephone voice (3,400 Hz max), this gives us the 8,000 Hz sampling\
  \ rate"
- Understand PCM converts analog to digital in three steps: "sampling (8,000/sec),\
    \ quantization (256 levels/8 bits), encoding \u2014 producing the 64 kbps DS0"
- "Understand Quantization noise is inherent in digital conversion; companding (\u03BC\
  -law/A-law) mitigates it by allocating more resolution to quiet sounds"
- "Understand \u03BC-law (PCMU, payload type 0) is used in North America; A-law (PCMA,\
  \ payload type 8) in Europe \u2014 mismatches cause unnecessary transcoding"
- Understand These fundamentals directly determine codec design, bandwidth calculations,
  and voice quality metrics throughout the rest of this course
public_word_count: 281
slug: analog-to-digital
title: "Analog to Digital \u2014 The Nyquist Theorem and PCM"
total_word_count: 281
---



## The Problem: Analog Signals in a Digital World

In Lesson 1, we learned that the telephone converts sound waves into analog electrical signals. In Lesson 2, we saw that TDM networks carry voice as digital data in 64 kbps DS0 channels. Something has to convert between these two worlds, and that conversion — **analog-to-digital** — is one of the most fundamental processes in all of telecommunications.

Every codec, every voice quality metric, every bandwidth calculation in this course traces back to the principles in this lesson. If you understand sampling and quantization, you understand *why* we have 8 kHz sampling, *why* G.711 is 64 kbps, and *why* codecs exist at all.

## Human Voice and Telephone Bandwidth

Human speech produces frequencies roughly between 80 Hz (deep male voice) and 8,000 Hz (sibilant sounds like "s" and "f"). However, the telephone system was engineered to carry only **300 Hz to 3,400 Hz** — the range that captures the fundamental frequencies and lower harmonics necessary for **speech intelligibility**.

This isn't the full richness of human voice (which is why phone calls sound different from face-to-face conversation), but it's sufficient for understanding speech. The choice was economic: wider bandwidth requires more expensive infrastructure, and 3.1 kHz was the practical sweet spot.

This 3,400 Hz upper limit directly determines everything that follows.

## The Nyquist-Shannon Sampling Theorem

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