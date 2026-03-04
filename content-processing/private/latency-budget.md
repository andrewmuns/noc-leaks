---
content_type: complete
description: "Learn about latency budget \u2014 sources of delay in a voip call"
difficulty: Advanced
duration: 8 minutes
lesson: '34'
module: 'Module 1: Foundations'
objectives:
- "Understand One-way delay under 150ms is the target for conversational quality \u2014\
  \ G.114 is your reference"
- Understand The latency budget has 8 components: codec, packetization, serialization,
    propagation, queuing, processing, jitter buffer, and decoding
- "Understand Propagation delay is physics (speed of light) \u2014 you cannot optimize\
  \ it away"
- Understand Queuing delay (especially customer last-mile) and jitter buffer are usually
  the largest variable contributors
- "Understand Transcoding adds 15ms+ per conversion \u2014 avoid unnecessary transcoding"
public_word_count: 235
slug: latency-budget
title: "Latency Budget \u2014 Sources of Delay in a VoIP Call"
total_word_count: 235
---



When someone says "this call feels laggy," they're experiencing latency — the time it takes for sound to travel from the speaker's mouth to the listener's ear. In the PSTN world, latency was mostly fixed and predictable (the speed of light through fiber, plus minimal switching delay). In VoIP, latency comes from a dozen different sources, each adding their own contribution. Understanding this **latency budget** is how you diagnose why a call feels wrong.

## The ITU-T G.114 Guidelines

The ITU-T recommendation G.114 defines the thresholds:

| One-Way Delay | Quality Impact |
|---------------|---------------|
| < 150 ms | Excellent — conversational quality, no perceptible delay |
| 150–300 ms | Acceptable — slight delay noticeable, manageable |
| 300–450 ms | Poor — noticeable lag, conversation becomes difficult |
| > 450 ms | Unusable — severe delay, people talk over each other |

These are **one-way** delays. Round-trip time is double. At 200ms one-way, you're at 400ms round-trip — that's when people start unconsciously pausing and then talking over each other.

## Dissecting the Delay Chain

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