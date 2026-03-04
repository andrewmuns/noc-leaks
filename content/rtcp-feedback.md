---
title: "RTCP — Feedback, Quality Reporting, and Congestion Control"
description: "Learn about rtcp — feedback, quality reporting, and congestion control"
module: "Module 1: Foundations"
lesson: "32"
difficulty: "Advanced"
duration: "7 minutes"
objectives:
  - Understand rtcp — feedback, quality reporting, and congestion control
slug: "rtcp-feedback"
---


## RTCP Purpose

RTCP provides the control channel that RTP lacks. While RTP carries media, RTCP carries statistics about that media — enabling quality monitoring, synchronization, and diagnostic capabilities.

---

## RTCP Packet Types

| Type | Abbreviation | Purpose |
|------|--------------|---------|
| 200 | SR | Sender Report: Statistics from active senders |
| 201 | RR | Receiver Report: Statistics from receivers |
| 202 | SDES | Source Description: CNAME, name, email, etc. |
| 203 | BYE | Stream termination notification |
| 204 | APP | Application-defined extensions |
| 207 | XR | Extended Report: Detailed quality metrics |
slug: "rtcp-feedback"
---

## Sender Reports (SR)

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