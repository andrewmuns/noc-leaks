---
content_type: complete
description: "Learn about tcp \u2014 reliability, congestion control, and sip over\
  \ tcp/tls"
difficulty: Intermediate
duration: 8 minutes
lesson: '18'
module: 'Module 1: Foundations'
objectives:
- Understand TCP's three-way handshake adds one RTT of connection setup delay; persistent
  SIP connections amortize this cost across thousands of transactions
- "Understand TCP guarantees in-order delivery, causing head-of-line blocking \u2014\
  \ when one packet is lost, all subsequent data is delayed until retransmission completes"
- "Understand TCP congestion control (slow start, window reduction) is designed for\
  \ bulk transfer and actively harmful for constant-rate real-time media \u2014 this\
  \ is why RTP uses UDP"
- Understand TCP is the right choice for SIP signaling: it handles large messages
    without fragmentation, provides built-in reliability, and enables TLS encryption
- "Understand Monitor TIME_WAIT socket accumulation and TCP retransmissions on SIP\
  \ servers \u2014 they're early indicators of connection management and network quality\
  \ issues"
public_word_count: 281
slug: tcp-for-voip
title: "TCP \u2014 Reliability, Congestion Control, and SIP over TCP/TLS"
total_word_count: 285
---



## TCP's Contract: Reliable, Ordered, Byte-Stream Delivery

TCP guarantees that every byte sent arrives at the destination, in order, without corruption. This is a powerful contract — applications can write data to a TCP socket and trust that the other side receives it exactly as sent. But this contract comes with costs that matter enormously for real-time communications.

## The Three-Way Handshake

Every TCP connection begins with a handshake:

```
Client → Server:  SYN         (seq=100)
Server → Client:  SYN-ACK     (seq=300, ack=101)
Client → Server:  ACK          (seq=101, ack=301)
```

**SYN:** "I want to connect. My initial sequence number is 100."
**SYN-ACK:** "Acknowledged. My initial sequence number is 300."
**ACK:** "Got it. We're connected."

This takes **one full round-trip time (RTT)** before any data flows. For a connection between New York and London (~70ms RTT), that's 70ms of setup delay. TCP with TLS (Lesson 17) adds more round trips.

For SIP over TCP, this means the first SIP message to a new server takes longer than SIP over UDP. However, once the connection is established, subsequent messages on the same connection have no setup delay.

> **💡 NOC Tip:** en you see SIP over TCP connection failures, check for SYN packets without SYN-ACK responses in packet captures. A SYN with no reply means either the server isn't listening, a firewall is blocking, or the server is overloaded and its SYN queue is full. The client will retry with exponential backoff, causing visible call setup delays.

## Sequence Numbers and Acknowledgments

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