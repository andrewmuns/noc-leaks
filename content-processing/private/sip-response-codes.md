---
content_type: complete
description: "Learn about sip response codes \u2014 what every code means"
difficulty: Advanced
duration: 8 minutes
lesson: '42'
module: 'Module 1: Foundations'
objectives:
- Understand 1xx provisional responses keep transactions alive; 183 Session Progress
  enables early media (ringback tones)
- "Understand 401/407 are normal authentication challenges, not errors \u2014 repeated\
  \ loops indicate bad credentials"
- "Understand 408 is locally generated when no response arrives \u2014 it points to\
  \ reachability problems"
- Understand 487 is normal call cancellation (caller hung up during ringing), not
  a failure
- "Understand 488 means codec/SDP mismatch \u2014 compare offered vs. supported codecs"
public_word_count: 300
slug: sip-response-codes
title: "SIP Response Codes \u2014 What Every Code Means"
total_word_count: 405
---



## Why Response Codes Matter

Every SIP transaction ends with a response code. As a NOC engineer, these three-digit numbers are your first diagnostic signal — they tell you *what happened* before you ever open a packet capture. Knowing response codes by heart is like a doctor knowing vital sign ranges: it immediately narrows the diagnosis.

SIP borrowed its response code scheme from HTTP, organized into six classes. But unlike HTTP, SIP has provisional responses that arrive *during* transaction processing, not just at the end. This distinction is critical for understanding call setup timing.

---

## 1xx — Provisional Responses

Provisional responses indicate the request is being processed but hasn't reached a final state yet. They keep the transaction alive and prevent timeout.

### 100 Trying
The first hop received your INVITE and is working on it. This is hop-by-hop — each proxy sends 100 Trying back to its upstream immediately. It exists solely to stop Timer A (INVITE retransmission) from firing. If you don't see a 100 Trying, the request probably never reached the next hop.

### 180 Ringing
The called endpoint is alerting (ringing). This is end-to-end — it means the INVITE reached a real device and that device is presenting the call to a human. In NOC operations, seeing 180 Ringing but no 200 OK means the call reached the destination but wasn't answered. The distinction between "no 180" and "180 but no 200" is crucial: the first is a routing/reachability problem, the second is a user behavior issue.

### 183 Session Progress
This is arguably the most important provisional response for VoIP. 183 with an SDP body establishes *early media* — a media path before the call is answered. This is how you hear ringback tones, announcements ("the number you have dialed..."), and IVR prompts from the far end before answer. Without early media, callers would hear silence until the call connects.

> **💡 NOC Tip:**  customers report "no ringback tone," check whether 183 Session Progress with SDP is being received. Some configurations strip early media, causing silence during ring phase.
slug: "sip-response-codes"
---

## 2xx — Success

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