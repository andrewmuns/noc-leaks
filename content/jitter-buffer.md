---
title: "The Jitter Buffer — Smoothing Out Packet Arrival Variation"
description: "Learn about the jitter buffer — smoothing out packet arrival variation"
module: "Module 1: Foundations"
lesson: "36"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand The jitter buffer holds packets to smooth arrival variation before playout — it's the primary defense against jitter
  - Understand Fixed buffers add constant latency; adaptive buffers trade variable latency for better jitter tolerance
  - Understand Late packets are functionally lost — jitter buffer depth controls the tradeoff between latency and effective loss rate
  - Understand PLC masks missing packets using interpolation — quality varies dramatically between simple repetition and advanced algorithms like Opus's built-in PLC
  - Understand Clock drift between sender and receiver slowly fills or empties the buffer — adaptive clock recovery compensates
slug: "jitter-buffer"
---


Jitter is the disease; the jitter buffer is the treatment. It's the single most important mechanism for maintaining audio quality in VoIP, and understanding how it works is essential for interpreting call quality metrics and diagnosing choppy audio.

## The Core Concept

Imagine packets arriving at these intervals (they should arrive every 20ms):

```
Packet 1: arrived at 0ms
Packet 2: arrived at 18ms   (2ms early)
Packet 3: arrived at 42ms   (2ms late)
Packet 4: arrived at 58ms   (18ms early?... no, the network was fast)
Packet 5: arrived at 85ms   (5ms late)
```

If you played each packet the instant it arrived, the audio would be a stuttering mess — gaps where packets are late, compression where they're early. Instead, the jitter buffer **holds** packets and plays them out at a fixed, regular interval.

With a 40ms jitter buffer, you'd wait 40ms before playing the first packet, then play one packet every 20ms regardless of when they actually arrived. As long as packets arrive within that 40ms window, audio is smooth.

## Fixed vs. Adaptive Jitter Buffers

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