---
content_type: truncated
description: "Learn about sip dialogs and transactions \u2014 understanding state"
difficulty: Advanced
duration: 8 minutes
full_content_available: true
lesson: '43'
module: 'Module 1: Foundations'
objectives:
- Understand A **transaction** is a single request-response exchange; a **dialog**
  is a long-lived relationship spanning multiple transactions
- Understand Dialogs are identified by the triple: Call-ID + From-tag + To-tag
- "Understand INVITE transactions have a special three-way handshake (INVITE \u2192\
  \ 200 \u2192 ACK) where ACK for 2xx is *not* part of the transaction"
- "Understand Forking creates multiple early dialogs from a single INVITE \u2014 proper\
  \ CANCEL handling is essential"
- "Understand Ghost calls occur when dialog state gets out of sync \u2014 session\
  \ timers and RTP timeouts are critical safety nets"
slug: sip-dialogs
title: "SIP Dialogs and Transactions \u2014 Understanding State"
word_limit: 300
---

## Why State Management Matters

SIP is fundamentally a *stateful* protocol, but its state is distributed across multiple entities. Unlike the PSTN where a central switch owns the call state, SIP distributes state between endpoints and intermediaries. When this state gets out of sync — when one side thinks a call exists but the other doesn't — you get ghost calls, hung sessions, and billing errors. Understanding transactions and dialogs is the key to preventing and diagnosing these problems.

---

## Transactions: The Atomic Unit

A **transaction** is a single request-response exchange. It's the smallest unit of SIP interaction. Every SIP request creates a transaction that lives until a final response (2xx-6xx) is received.

### Transaction Identification

A transaction is uniquely identified by:
- The **Via branch parameter** (a unique token the client generates)
- The **CSeq method** (because a CANCEL and its INVITE share a Via branch but are separate transactions)

When a response arrives, the transaction layer matches it to the original request using these identifiers. If no match is found, the response is dropped — this is a common source of "response not processed" bugs when SIP ALGs or intermediaries rewrite Via headers incorrectly.

### Client vs. Server Transactions

The entity that sends the request runs a **client transaction**. The entity that receives and responds runs a **server transaction**. A proxy runs *both* — a server transaction for the incoming request and a client transaction for the forwarded request.

### INVITE vs. Non-INVITE Transactions

SIP has two types of transactions with fundamentally different state machines:

**Non-INVITE transactions** (REGISTER, BYE, OPTIONS, etc.) are simple:
- Request → Final Response. Done.
- Timer F = 32 seconds. If no response, transaction fails with 408.

**INVITE transactions** are complex because calls take time to set up:
- INVITE → Provisional (1xx) → Final Response →

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*