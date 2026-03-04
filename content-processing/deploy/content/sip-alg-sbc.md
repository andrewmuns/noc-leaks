---
content_type: truncated
description: Learn about sip alg, session border controllers, and media anchoring
difficulty: Intermediate
duration: 6 minutes
full_content_available: true
lesson: '30'
module: 'Module 1: Foundations'
objectives:
- Understand sip alg, session border controllers, and media anchoring
slug: sip-alg-sbc
title: SIP ALG, Session Border Controllers, and Media Anchoring
word_limit: 300
---

## Session Border Controllers: The Proper Fix

SBCs solve NAT by being the "man in the middle." They terminate SIP on both sides, rewrite headers appropriately, and relay media when needed.

### How SBCs Handle NAT

```
Phone (NAT'd)          SBC (Public)           Carrier
192.168.1.100  ──────→  203.0.113.10  ──────→  198.51.100.5
SIP + SDP              SIP rewritten          Clean SIP
                         + SDP relay
             ←────────                ←──────
           Media relayed           Media
```

**The SBC's job:**
1. Receives SIP from private endpoint
2. Rewrites Contact, Via, SDP to use SBC's public address
3. Forwards clean SIP to destination
4. Receives RTP on SBC's port
5. Forwards RTP through NAT hole to private endpoint

### SBC Functions Beyond NAT

- **Security:** Topology hiding, DoS protection, call admission control
- **Interoperability:** Normalize quirky SIP implementations
- **Media handling:** Transcoding, recording, A/B leg separation
- **Regulatory:** Lawful intercept, emergency call handling

> **💡 NOC Tip:**  Telnyx, the B2BUA acts as the SBC. When you see calls from a customer behind NAT, verify the call flow shows the B2BUA handling both legs. Call-site-finder can tell you which B2BUA handled a specific call.

---

## Media Anchoring: Forcing RTP Through Known Paths

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