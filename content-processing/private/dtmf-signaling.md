---
content_type: complete
description: "Learn about dtmf \u2014 rfc 2833/4733 telephone events vs. in-band detection"
difficulty: Advanced
duration: 7 minutes
lesson: '33'
module: 'Module 1: Foundations'
objectives:
- "Understand DTMF uses a 4\xD74 dual-tone frequency matrix \u2014 robust on analog,\
  \ fragile with digital compression"
- Understand Three transport methods exist: "in-band (audio), RFC 4733 (RTP events),\
    \ and SIP INFO \u2014 RFC 4733 is strongly preferred"
- "Understand Compressed codecs (G.729, Opus) destroy in-band DTMF tones \u2014 never\
  \ rely on in-band with compressed codecs"
- Understand B2BUAs like Telnyx handle DTMF interworking between methods on different
  call legs
- Understand Double digits usually mean both RFC 4733 and in-band are active simultaneously
public_word_count: 246
slug: dtmf-signaling
title: "DTMF \u2014 RFC 2833/4733 Telephone Events vs. In-Band Detection"
total_word_count: 246
---



Every time a caller presses "1" to reach billing or "0" for an operator, they're generating DTMF — Dual-Tone Multi-Frequency signals. It sounds simple, but DTMF transport is one of the most persistent sources of subtle bugs in VoIP systems. Missed IVR digits, failed bank authentication, broken calling card systems — these all trace back to DTMF handling problems.

## The DTMF Frequency Matrix

DTMF uses a 4×4 matrix of frequencies. Each key press generates two simultaneous tones — one from a low-frequency group and one from a high-frequency group:

|        | 1209 Hz | 1336 Hz | 1477 Hz | 1633 Hz |
|--------|---------|---------|---------|---------|
| 697 Hz |    1    |    2    |    3    |    A    |
| 770 Hz |    4    |    5    |    6    |    B    |
| 852 Hz |    7    |    8    |    9    |    C    |
| 941 Hz |    *    |    0    |    #    |    D    |

The dual-tone design was intentional — it's nearly impossible for human speech to accidentally produce two specific frequencies simultaneously. This made DTMF robust on analog lines. But digital compression changes everything.

## Three Methods of DTMF Transport

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