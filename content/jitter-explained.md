---
title: "Jitter — Why Packets Arrive at Irregular Intervals"
description: "Learn about jitter — why packets arrive at irregular intervals"
module: "Module 1: Foundations"
lesson: "35"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand Jitter is the variation in packet interarrival times — it's the inconsistency that damages audio quality
  - Understand Primary causes: network queuing variation, route changes, CPU contention, wireless access, and container scheduling
  - Understand RFC 3550 defines the smoothed jitter calculation used in RTCP reports — < 10ms is excellent, > 50ms is problematic
  - Understand Distinguish network jitter (path-induced) from system jitter (endpoint-induced) by capturing at both sender and receiver
  - Understand Periodic jitter patterns suggest a regular process or scheduled task interfering with packet forwarding
slug: "jitter-explained"
---


In Lesson 32, we broke down the latency budget and saw that queuing delay is variable. That variability has a name: **jitter**. While latency tells you how long packets take to arrive, jitter tells you how *consistently* they arrive. And for real-time audio, consistency matters as much as speed.

## What Jitter Actually Is

A VoIP endpoint sends RTP packets at regular intervals — every 20ms for a standard configuration. If the network were perfect, they'd arrive every 20ms. In reality, some arrive in 18ms, some in 25ms, some in 42ms. Jitter is the variation in these interarrival times.

Formally, RFC 3550 defines **interarrival jitter** as a smoothed estimate of the variance:

```
J(i) = J(i-1) + (|D(i-1,i)| - J(i-1)) / 16
```

Where `D(i-1,i)` is the difference in relative transit time between consecutive packets. The `/16` smoothing factor makes this a running average that responds to changes but doesn't overreact to single outliers.

In plain terms: if packets are supposed to arrive every 20ms, and the actual intervals are 18, 22, 19, 45, 20, 21 — that spike to 45ms is jitter. The audio system expected a packet at 20ms but it arrived at 45ms, creating a gap that must be filled with silence or interpolation.

## Why Jitter Happens

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