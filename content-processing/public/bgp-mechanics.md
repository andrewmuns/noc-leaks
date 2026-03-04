---
content_type: truncated
description: "Learn about bgp mechanics \u2014 sessions, updates, and path selection"
difficulty: Intermediate
duration: 9 minutes
full_content_available: true
lesson: '25'
module: 'Module 1: Foundations'
objectives:
- "Understand bgp mechanics \u2014 sessions, updates, and path selection"
slug: bgp-mechanics
title: "BGP Mechanics \u2014 Sessions, Updates, and Path Selection"
word_limit: 300
---

Now that you understand Autonomous Systems and why BGP exists, let's look under the hood. How do BGP routers establish sessions? How do they exchange routing information? And when multiple paths exist to the same destination, how does a router pick the best one? These mechanics are essential for understanding NOC incidents involving routing changes, session flaps, and traffic shifts.

## BGP Sessions — TCP Port 179

Unlike IGP protocols that use multicast or broadcast for neighbor discovery, BGP peers must be **explicitly configured**. Each BGP session runs over a **TCP connection on port 179**.

### Session Types

| Type | Description | Typical Use |
|------|-------------|-------------|
| **eBGP** (External BGP) | Between routers in *different* ASes | Telnyx ↔ upstream provider |
| **iBGP** (Internal BGP) | Between routers in the *same* AS | Telnyx router ↔ Telnyx router |

```
┌──────────────────┐          ┌──────────────────┐
│   Telnyx (AS46887)│   eBGP   │  Cogent (AS174)  │
│                  │◄────────►│                  │
│  Border Router   │ TCP:179  │  Border Router   │
└──────────────────┘          └──────────────────┘
        │
        │ iBGP (TCP:179)
        │
┌──────────────────┐
│  Telnyx Internal │
│  Route Reflector │
└──────────────────┘
```

> **💡 NOC Tip:**  a BGP session won't establish, check: (1) TCP 179 connectivity — firewalls often block it, (2) matching AS numbers in the config, (3) correct neighbor IP. Use `telnet <peer-ip> 179` as a quick reachability test.

## BGP Finite State Machine

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