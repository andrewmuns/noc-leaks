---
content_type: complete
description: "Learn about call failures \u2014 cancel, timeouts, and error responses"
difficulty: Advanced
duration: 7 minutes
lesson: '47'
module: 'Module 1: Foundations'
objectives:
- "Understand CANCEL aborts pending INVITEs \u2014 it can only be sent after provisional\
  \ and before final response"
- "Understand 487 Request Terminated is the normal result of a CANCEL \u2014 high\
  \ 487 rates indicate user abandonment, not technical issues"
- "Understand The CANCEL/200 race condition creates brief \"phantom calls\" \u2014\
  \ CANCEL crosses with answer, requiring ACK then BYE"
- "Understand 408 timeout is generated *locally* when no response arrives \u2014 investigate\
  \ reachability, not the far end's response"
- ? "Understand Telnyx's routing engine automatically fails over on 408, 500, 502,\
    \ 503, 504 \u2014 but not on definitive rejections like 403, 404, 486slug"
  : call-failures
public_word_count: 234
title: "Call Failures \u2014 CANCEL, Timeouts, and Error Responses"
total_word_count: 318
---



## Calls Fail More Often Than They Succeed

In a typical telecom environment, 30-40% of call attempts don't result in a completed conversation. That's not a bug — it's reality. People don't answer, lines are busy, numbers are wrong, networks hiccup. Understanding *how* calls fail in SIP is just as important as understanding how they succeed.

---

## CANCEL: Aborting a Pending Call

CANCEL is how a caller says "never mind" after sending an INVITE but before receiving a final response. The most common scenario: the caller hangs up while the phone is ringing.

### The CANCEL Flow

```
Alice                    Telnyx B2BUA                    Bob
  |------- INVITE ---------->|------- INVITE ------------>|
  |<------ 100 Trying -------|<------ 180 Ringing --------|
  |<------ 180 Ringing ------|                            |
  |                          |                            |
  |  (Alice hangs up)        |                            |
  |------- CANCEL ---------->|------- CANCEL ------------>|
  |<------ 200 OK (CANCEL) --|<------ 200 OK (CANCEL) ---|
  |                          |<------ 487 Terminated -----|
  |                          |------- ACK (487) --------->|
  |<------ 487 Terminated ---|                            |
  |------- ACK (487) ------->|                            |
```

**Key points:**
- CANCEL has the **same Call-ID, From-tag, and To-tag** as the INVITE — it targets a specific transaction
- The 200 OK to CANCEL just means "I received your CANCEL" — it does *not* mean the call was successfully cancelled
- The actual result is the **487 Request Terminated** response to the original INVITE
- You must still ACK the 487 (as with all final responses to INVITE)

### The Critical Rule: CANCEL Timing

CANCEL can only be sent *after* a provisional response is received and *before* a final response arrives. Why?

- **Before any response:** The INVITE might not have arrived yet. Sending CANCEL to something that doesn't exist is meaningless. The UAC should wait for at least a 100 Trying before sending CANCEL.
- **After final response:** It's too late — the transaction is complete. If a 200 OK arrives, the call is answered. You must send ACK then BYE to end it (you can't un-answer a call with CANCEL).


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