---
title: "Introduction to SIP Protocol"
description: "Learn the fundamentals of Session Initiation Protocol"
module: "SIP Protocol Deep Dive"
lesson: 1
difficulty: "Intermediate"
duration: "45 minutes"
objectives:
  - Understand SIP message structure
  - Learn basic SIP methods
  - Practice reading SIP traces
---

# Introduction to SIP Protocol

The Session Initiation Protocol (SIP) is a signaling protocol used for initiating, maintaining, and terminating real-time communication sessions.

## What is SIP?

SIP is an application layer protocol that handles:
- Call setup and teardown
- User registration and location
- Session modification
- Feature invocation

## SIP Message Structure

Every SIP message consists of:

1. **Start Line**: Method/Response and URI
2. **Headers**: Metadata about the message
3. **Body**: Optional content (SDP, etc.)

### Example SIP INVITE

```
INVITE sip:bob@example.com SIP/2.0
Via: SIP/2.0/UDP alice-pc.example.com:5060;branch=z9hG4bK-d87543-1
Max-Forwards: 70
To: Bob <sip:bob@example.com>
From: Alice <sip:alice@example.com>;tag=1928301774
Call-ID: a84b4c76e66710@alice-pc.example.com
CSeq: 314159 INVITE
Contact: <sip:alice@alice-pc.example.com:5060>
Content-Type: application/sdp
Content-Length: 142

v=0
o=alice 53655765 2353687637 IN IP4 alice-pc.example.com
s=Session Description
c=IN IP4 alice-pc.example.com
t=0 0
m=audio 49170 RTP/AVP 0
a=rtpmap:0 PCMU/8000
```

## Key SIP Methods

| Method | Purpose |
|--------|---------|
| INVITE | Initiate a session |
| ACK | Acknowledge a response |
| BYE | Terminate a session |
| CANCEL | Cancel a pending request |
| REGISTER | Register a user agent |
| OPTIONS | Query capabilities |

## Lab Exercise

**Objective**: Analyze a SIP call flow

1. Open Wireshark or your preferred packet analyzer
2. Start a SIP call between two endpoints
3. Identify the three-way handshake (INVITE, 200 OK, ACK)
4. Document the headers in each message

## Quiz

1. What does the Via header indicate?
2. Which SIP method is used to end a call?
3. What type of content is typically found in the message body?

---

**Next Lesson**: [SIP Response Codes](./lesson-2)
**Previous**: [Course Introduction](../introduction-to-telephony)