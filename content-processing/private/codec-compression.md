---
content_type: complete
description: "Learn about compressed codecs \u2014 g.729, g.722, and why compression\
  \ matters"
difficulty: Beginner
duration: 7 minutes
lesson: '9'
module: 'Module 1: Foundations'
objectives:
- "Understand G.729 achieves 8:1 compression using CELP vocal tract modeling \u2014\
  \ excellent for speech, problematic for tones and non-speech audio"
- Understand G.729 Annex B (VAD/CNG) saves bandwidth during silence but can suppress
  non-speech signals like DTMF and fax
- "Understand G.722 delivers wideband \"HD Voice\" at 64 kbps by sampling at 16 kHz\
  \ \u2014 doubling the audio frequency range compared to G.711"
- Understand Compressed codecs add algorithmic delay (15-37.5 ms) that compounds in
  the total end-to-end latency budget
- "Understand Transcoding between codecs costs CPU, quality, and latency \u2014 align\
  \ codecs across call legs whenever possible"
public_word_count: 156
slug: codec-compression
title: "Compressed Codecs \u2014 G.729, G.722, and Why Compression Matters"
total_word_count: 156
---



## The Quality-Bandwidth-Latency Triangle

Every voice codec makes a tradeoff between three competing priorities:

- **Quality**: How close to the original speech does the decoded audio sound?
- **Bandwidth**: How many bits per second does it consume?
- **Latency**: How much delay does the encoding/decoding process add?

G.711 maximizes quality and minimizes latency, but uses the most bandwidth. Compressed codecs sacrifice some quality and add latency to dramatically reduce bandwidth. Understanding these tradeoffs is essential for making informed decisions about codec selection and for diagnosing quality issues rooted in codec choice.

## G.729 — The Workhorse Compressed Codec

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