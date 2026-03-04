---
title: "Voice Quality Metrics — MOS, PESQ, POLQA, and R-Factor"
description: "Learn about voice quality metrics — mos, pesq, polqa, and r-factor"
module: "Module 1: Foundations"
lesson: "11"
difficulty: "Intermediate"
duration: "7 minutes"
objectives:
  - Understand MOS (1-5) is the universal voice quality scale; in dashboards, it's always algorithmically estimated, not subjectively measured
  - Understand PESQ/POLQA (intrusive) compare output to reference for high accuracy; the E-Model (non-intrusive) estimates quality from network parameters for real-time monitoring
  - Understand The R-Factor (0-100) decomposes quality into delay, loss, and codec impairments — use this decomposition to identify root causes
  - Understand Key thresholds: MOS >4.0 good, 3.5-4.0 acceptable, <3.5 investigate; packet loss <1% good, >3% problematic; delay <150ms good, >400ms unusable
  - Understand Always baseline quality metrics by call type and set meaningful alert thresholds — aggregate averages can mask significant quality problems
slug: "voice-quality-metrics"
---


## Why We Measure Voice Quality

You can't improve what you can't measure. In a NOC environment, "the call sounded bad" isn't actionable. You need **quantitative metrics** that tell you *how bad*, *what kind of bad*, and *where in the call path the problem originated*.

Voice quality measurement spans a spectrum from purely subjective (asking humans) to purely algorithmic (computing a score from signal characteristics). Understanding these metrics and how to read them in dashboards is a core NOC skill.

## Mean Opinion Score (MOS)

The **MOS** is a number from **1 to 5** representing subjective voice quality:

| MOS | Quality | Description |
|-----|---------|-------------|
| 5 | Excellent | Imperceptible distortion |
| 4 | Good | Perceptible but not annoying |
| 3 | Fair | Slightly annoying |
| 2 | Poor | Annoying |
| 1 | Bad | Very annoying |

Originally, MOS was determined by having a panel of listeners rate audio samples — literally asking people "how does this sound?" on a 1-5 scale. This is **subjective MOS** and is the gold standard for quality assessment, but it's obviously impractical for real-time monitoring.

In practice, when you see "MOS" in a dashboard, it's always an **estimated MOS** computed algorithmically. There are two fundamentally different approaches to this estimation.

## PESQ and POLQA — Intrusive Measurement

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