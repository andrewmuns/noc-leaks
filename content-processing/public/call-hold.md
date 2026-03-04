---
content_type: truncated
full_content_available: true
word_limit: 300
---

---
title: "Call Hold, Resume, and Re-INVITE"
description: "Learn about call hold, resume, and re-invite"
module: "Module 1: Foundations"
lesson: "49"
difficulty: "Advanced"
duration: "6 minutes"
objectives:
  - Understand Re-INVITE modifies an active session — used for hold, resume, codec changes, and session refresh
  - Understand Hold is signaled by changing SDP direction: `a=sendonly` (hold with music) or `a=inactive` (silent hold)
  - Understand Resume restores `a=sendrecv` for normal bidirectional media
  - Understand Glare (simultaneous re-INVITEs) is resolved with 491 Request Pending and staggered retry timers
  - Understand UPDATE can modify sessions before they're established (early dialog) — re-INVITE cannot
slug: "call-hold"
---


## Modifying a Call in Progress

A SIP call isn't static. After the initial INVITE/200/ACK establishes the session, either party may need to change it: put the call on hold, change codecs, add video, or update media addresses. The **re-INVITE** is SIP's mechanism for modifying an active session.

A re-INVITE is simply an INVITE sent *within an existing dialog*. It carries a new SDP offer that proposes changes to the session. The other party responds with a new SDP answer, and the session is updated.

---

## Call Hold

### How Hold Works

When Alice puts Bob on hold, her phone sends a re-INVITE with modified SDP:

```
Alice                    Telnyx B2BUA                    Bob
  |------- re-INVITE ------>|                            |
  | (a=sendonly)             |------- re-INVITE --------->|
  |                          | (a=sendonly)               |
  |                          |<------ 200 OK -------------|
  |<------ 200 OK ----------|  (a=recvonly)               |
  |------- ACK ------------->|------- ACK --------------->|
  |                          |                            |
  |  (Hold music plays)      |======= RTP (music) ======>|
```

The SDP direction attributes signal the hold state:

| Attribute | Meaning |
|-----------|---------|
| `a=sendrecv` | Normal bidirectional media (default) |
| `a=sendonly` | I will send but not receive — **hold** (I'm sending hold music) |
| `a=recvonly` | I will receive but not send — response to `sendonly` |
| `a=inactive` |

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*