---
title: "Systematic Call Quality Troubleshooting"
description: "Learn about systematic call quality troubleshooting"
module: "Module 1: Foundations"
lesson: "52"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand systematic call quality troubleshooting
slug: "quality-troubleshooting"
---


## Why You Need a Framework

When a customer reports "bad call quality," that could mean a dozen different things. Without a systematic approach, you'll waste time chasing ghosts. This lesson gives you a repeatable framework that works for every quality complaint — from one-way audio to echo to choppy speech.

The goal is simple: **isolate the leg, identify the symptom, find the cause, fix it.**

---

## The Four-Step Framework

### Step 1: Isolate the Leg

Every call through Telnyx has at least two legs:

```
Customer A ──► Telnyx Ingress SBC ──► Telnyx Core ──► Telnyx Egress SBC ──► Customer B
     Leg A (inbound)                                      Leg B (outbound)
```

Your first job is to determine **which leg** has the problem. Ask:

- Does Customer A hear the issue, Customer B, or both?
- Is the issue present on the Telnyx-side capture (between SBCs)?
- Does the problem persist if you swap the termination route?

> **💡 NOC Tip:**  the Telnyx Mission Control portal, pull the call detail record (CDR) and look at the `leg_id`. Each leg has independent RTCP stats. Compare MOS, jitter, and packet loss for Leg A vs Leg B separately — this instantly tells you which side is degraded.

### Step 2: Identify the Symptom

Classify the problem into one of these categories:

| Symptom | Description |
|---------|-------------|
| **No audio** | Complete silence in one or both directions |
| **One-way audio** | Audio flows in one direction only |
| **Choppy audio** | Words cut in and out, robotic sound |
| **Echo** | Speaker hears their own voice delayed |
| **DTMF failure** | IVR menus don't respond to key presses |
| **Distortion/static** | Garbled or noisy audio |
| **Latency** | Noticeable delay in conversation |

### Step 3: Find the Cause

Each symptom maps to a set of likely causes. We'll cover each below.

### Step 4: Fix and Verify

Apply the fix, test with a new call, and confirm RTCP stats normalize.
slug: "quality-troubleshooting"

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