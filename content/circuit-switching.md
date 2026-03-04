---
title: "Circuit Switching — Dedicated Paths and Why They Mattered"
description: "Learn about circuit switching — dedicated paths and why they mattered"
module: "Module 1: Foundations"
lesson: "2"
difficulty: "Beginner"
duration: "8 minutes"
objectives:
  - Understand Circuit switching reserves a dedicated 64 kbps channel (DS0) for each call — guaranteeing zero jitter and zero loss, but wasting bandwidth during silence
  - Understand TDM multiplexes multiple DS0s onto shared physical links using time slots — position in the frame determines the channel (no headers needed)
  - Understand T1 carries 24 channels (1.544 Mbps), E1 carries 32 channels (2.048 Mbps) — these map directly to SIP trunk concurrent call planning
  - Understand The Erlang B formula calculates blocking probability and remains directly relevant to SIP trunk capacity planning
  - Understand Trunk group concepts (capacity, blocking, busy-hour engineering) apply identically to SIP trunks with concurrent call limits
slug: "circuit-switching"
---


## The Core Idea: Resource Reservation

In Lesson 1, we saw how central offices connected subscribers by physically patching circuits together. Circuit switching formalizes this idea: when you make a call, a **dedicated communication path** is established end-to-end, and **resources are reserved exclusively** for that call for its entire duration — whether you're talking, silent, or on hold.

This is the fundamental difference between circuit switching and packet switching (Lesson 10). In a circuit-switched network, bandwidth is **allocated**, not **shared**. You get a fixed-capacity pipe, and nobody else can use it until you hang up.

To understand why this matters, think about what it guarantees:
- **Zero jitter**: The path is fixed; every sample traverses the same route with the same delay
- **Zero packet loss**: There are no packets to lose — it's a continuous stream
- **Fixed latency**: Propagation delay is constant because the path doesn't change
- **Guaranteed bandwidth**: Your 64 kbps channel is always available

These are exactly the properties that voice communication needs, and exactly the properties that packet switching struggles to provide. Every QoS mechanism in modern VoIP (Lesson 11) is an attempt to approximate what circuit switching gave us for free.

The tradeoff? **Efficiency.** When you're silent (which is roughly 60% of a typical phone call), your reserved bandwidth goes completely unused. Nobody else can use it. This waste is what made packet switching revolutionary — but we're getting ahead of ourselves.

## Time-Division Multiplexing and the DS0

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