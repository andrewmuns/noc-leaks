---
content_type: truncated
description: Learn about number portability and the lnp database
difficulty: Beginner
duration: 6 minutes
full_content_available: true
lesson: '4'
module: 'Module 1: Foundations'
objectives:
- Understand LNP allows phone numbers to move between carriers; the LRN (Location
  Routing Number) tells the network which switch currently serves a ported number
- "Understand Every call to a ported number requires a dip \u2014 a real-time database\
  \ query that returns the LRN, adding latency and cost to call routing"
- "Understand Porting failures often stem from NPAC synchronization delays \u2014\
  \ stale LRN data in a carrier's local database causes misrouted or failed calls"
- "Understand The porting lifecycle (request \u2192 FOC \u2192 activation \u2192 release)\
  \ involves multiple carriers and NPAC coordination \u2014 failures at any stage\
  \ cause incidents"
- Understand Telnyx interacts with LNP as both a porting participant (porting numbers
  in/out) and a dip consumer (querying LRN for outbound routing)
slug: number-portability
title: Number Portability and the LNP Database
word_limit: 300
---

## Why Numbers Had to Become Portable

Before 1996, your phone number was permanently tied to your carrier. Switching from AT&T to MCI meant getting a new phone number — which meant reprinting business cards, updating every contact, and losing the number your customers knew. This was a massive barrier to competition, and carriers knew it.

The **Telecommunications Act of 1996** mandated Local Number Portability (LNP) in the United States, requiring carriers to allow customers to keep their phone numbers when switching providers. This fundamentally changed how phone calls are routed and created an entire infrastructure layer that Telnyx interacts with daily.

For NOC engineers, LNP isn't academic. Number porting issues cause real incidents: calls routing to the wrong carrier, porting delays blocking customer migrations, and stale LNP data causing call failures.

## How LNP Works — The Location Routing Number

Before LNP, routing was simple: the first 6 digits of a phone number (NPA-NXX, i.e., area code + exchange) told you which switch served that number. All numbers in 212-555-XXXX belonged to the same switch.

LNP broke this assumption. Now, 212-555-1234 might belong to AT&T while 212-555-1235 belongs to Telnyx. You can no longer route based on the NPA-NXX alone.

The solution is the **Location Routing Number (LRN)** — a 10-digit number that identifies the switch currently serving a ported number. Here's how it works:

1. **Before routing a call**, the originating carrier performs a **dip** — a real-time database query to the Number Portability Administration Center (NPAC)
2. The query asks: "Has this number been ported? If so, what's the LRN?"
3. If the number has been ported, the NPAC returns the LRN of the new serving switch
4. The originating carrier routes the call to the switch identified by the LRN instead of the switch implied by the dialed

---

*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*