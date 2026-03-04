---
title: "Verify API — Two-Factor Authentication"
description: "Learn about verify api — two-factor authentication"
module: "Module 1: Foundations"
lesson: "6"
difficulty: "Beginner"
duration: "5 minutes"
objectives:
  - Understand verify api — two-factor authentication
slug: "two-factor-auth"
---


## Introduction

Two-factor authentication (2FA) via SMS or voice is one of the highest-volume messaging use cases. The Telnyx Verify API provides a managed OTP (One-Time Password) service that handles code generation, delivery, rate limiting, and fraud prevention. For NOC engineers, Verify is a critical path — when it breaks, customers' users can't log in.

---

## How OTP Verification Works

### The Verification Lifecycle

```
1. INITIATE  — App requests verification for +15559876543
2. GENERATE  — Telnyx generates OTP (e.g., 847293)
3. DELIVER   — OTP sent via SMS, voice call, or WhatsApp
4. SUBMIT    — User enters code in the app
5. VERIFY    — App sends code to Telnyx for validation
6. RESULT    — Telnyx returns: verified ✓ or failed ✗
```

```
   Customer App              Telnyx Verify             User
       │                          │                      │
       │── POST /verifications ──>│                      │
       │<── verification_id ──────│                      │
       │                          │── SMS: "847293" ────>│
       │                          │                      │
       │                          │      (user enters)   │
       │── POST /verify_code ────>│                      │
       │<── status: verified ─────│                      │
```
slug: "two-factor-auth"
---

## Using the Verify API

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