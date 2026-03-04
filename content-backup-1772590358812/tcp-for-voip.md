---
title: "TCP — Reliability, Congestion Control, and SIP over TCP/TLS"
description: "Learn about tcp — reliability, congestion control, and sip over tcp/tls"
module: "Module 1: Foundations"
lesson: "18"
difficulty: "Intermediate"
duration: "8 minutes"
objectives:
  - Understand TCP's three-way handshake adds one RTT of connection setup delay; persistent SIP connections amortize this cost across thousands of transactions
  - Understand TCP guarantees in-order delivery, causing head-of-line blocking — when one packet is lost, all subsequent data is delayed until retransmission completes
  - Understand TCP congestion control (slow start, window reduction) is designed for bulk transfer and actively harmful for constant-rate real-time media — this is why RTP uses UDP
  - Understand TCP is the right choice for SIP signaling: it handles large messages without fragmentation, provides built-in reliability, and enables TLS encryption
  - Understand Monitor TIME_WAIT socket accumulation and TCP retransmissions on SIP servers — they're early indicators of connection management and network quality issues
slug: "tcp-for-voip"
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

TCP assigns a sequence number to every byte of data. The receiver acknowledges by sending back the sequence number of the next byte it expects. This creates a closed feedback loop:

- **Sender sends data** with sequence numbers
- **Receiver acknowledges** what it's received
- **Sender detects loss** when acknowledgments are missing (either by timeout or by receiving duplicate ACKs)
- **Sender retransmits** lost data

This is why TCP provides reliable delivery — lost data is always retransmitted. The cost is **latency**. Retransmission timeout (RTO) is typically 200ms-1s for the first retry, doubling with each subsequent attempt.

## The Connection State Machine

TCP connections pass through well-defined states:

```
CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED
CLOSED → LISTEN → SYN_RECEIVED → ESTABLISHED → CLOSE_WAIT → LAST_ACK → CLOSED
```

**ESTABLISHED** is the normal operational state — data flows bidirectionally.

**TIME_WAIT** deserves special attention: after a connection closes, the socket stays in TIME_WAIT for 2× Maximum Segment Lifetime (typically 60 seconds). This prevents delayed packets from a previous connection being mistaken for a new one. On busy SIP servers handling many short TCP connections, TIME_WAIT accumulation can exhaust available ports.

> **💡 NOC Tip:** n `ss -s` or `netstat -s` on SIP servers to check for TIME_WAIT accumulation. Thousands of TIME_WAIT sockets indicate many short-lived connections. For SIP, the solution is **persistent connections** (connection reuse) — keeping the TCP connection open for multiple SIP transactions rather than opening/closing per transaction.

## Congestion Control: TCP's Self-Regulation

TCP doesn't just provide reliability — it actively manages how fast it sends data to avoid overwhelming the network. This is **congestion control**, and it's why the internet doesn't collapse under load.

### Slow Start
A new connection starts sending slowly (congestion window = 1-2 segments) and doubles the window each RTT. This exponential growth quickly finds available bandwidth but risks overshooting.

### Congestion Avoidance
Once the window reaches a threshold (ssthresh), growth slows to linear — adding one segment per RTT. This cautiously probes for more bandwidth.

### Fast Retransmit / Fast Recovery
When three duplicate ACKs arrive, TCP assumes a packet was lost (rather than waiting for the timeout). It retransmits immediately and halves the congestion window. This is much faster than waiting for RTO.

### Why This Matters for VoIP

**TCP's congestion control is designed for bulk data transfer.** It's excellent for downloading files — it fills the pipe, backs off during congestion, and fills again. But this behavior is harmful for real-time traffic:

1. **Slow start** means a new connection can't immediately send at the required rate
2. **Window reduction after loss** drops throughput right when the network might need it most
3. **Retransmission delays** add latency that real-time applications can't tolerate

This is another reason RTP uses UDP — it needs to send packets at a constant rate regardless of network conditions. Congestion control would make voice sound terrible.

## Head-of-Line Blocking: TCP's Achilles Heel

This is TCP's most damaging property for real-time traffic. TCP guarantees **in-order delivery**. If packet 5 out of 10 is lost, the receiver has packets 1-4 and 6-10. But the application only sees 1-4. Packets 6-10 are held in TCP's receive buffer until packet 5 is retransmitted and arrives.

For voice over TCP: if one RTP packet is lost, all subsequent packets are delayed until the retransmission arrives. Instead of losing 20ms of audio (one packet), you lose the time until retransmission completes — easily 200ms or more. The result is a burst of silence followed by a burst of delayed audio — much worse than a barely perceptible 20ms gap.

For multiplexed SIP: if a SIP proxy uses a single TCP connection to send multiple unrelated messages, a loss on one message delays all subsequent messages. Message A's lost packet blocks Message B, C, and D even though they're complete.

## TCP for SIP Signaling: Why It Makes Sense

Despite TCP's drawbacks for media, it's excellent for SIP signaling:

**Reliability without timers:** SIP over UDP requires application-layer retransmission (Timers A, B, E, F). SIP over TCP delegates reliability to the transport layer — simpler application code and more predictable behavior.

**Large messages:** SIP INVITE messages with extensive SDP can exceed UDP-safe sizes (~1300 bytes to avoid fragmentation). TCP handles segmentation transparently.

**Persistent connections:** A TCP connection can carry thousands of SIP transactions. Once established, there's no per-message handshake. This is more efficient than UDP for high-volume SIP traffic.

**TLS support:** Encrypting SIP requires TLS, which requires TCP (or DTLS over UDP, which is less common for SIP). SIP over TLS (SIPS, port 5061) is the standard for secure signaling.

**Connection-oriented trunks:** Telnyx supports SIP over TCP, enabling persistent trunk connections. The health of the connection is visible (TCP keepalives, connection state), unlike UDP where you can't distinguish "quiet" from "dead."

### Real Troubleshooting Scenario

**Scenario:** A customer's SIP trunk works fine under normal load but fails during traffic spikes. SIP messages timeout, calls fail with 408 errors, but the TCP connection appears up.

**Investigation:** The customer's firewall has a TCP connection limit. During spikes, new SIP TCP connections are rejected. Additionally, the single persistent TCP connection becomes a bottleneck — a large message (recording notification with big body) causes head-of-line blocking, delaying subsequent INVITEs.

**Solution:** Use multiple persistent TCP connections (connection pooling) to distribute load and isolate head-of-line blocking. Ensure firewall connection limits are appropriate for expected traffic.

> **💡 NOC Tip:** nitor TCP retransmissions on SIP connections. `ss -ti` shows per-connection retransmission counts on Linux. Rising retransmissions correlate with network loss and manifest as increased SIP latency and timeouts. This is often an early warning sign before call quality degrades.

## TCP vs. UDP for SIP: The Decision Matrix

| Factor | UDP | TCP |
|--------|-----|-----|
| Message size | Risk fragmentation >1300B | No fragmentation |
| Reliability | App-layer retransmit | Transport-layer |
| Connection overhead | None | 1 RTT handshake |
| TLS support | DTLS (uncommon) | Native TLS |
| Firewall traversal | Stateless, short timeouts | Stateful, long timeouts |
| Connection visibility | No connection state | Connection state visible |
| Head-of-line blocking | N/A | Yes, problematic |

For Telnyx operations, TCP (with TLS) is recommended for SIP signaling. The reliability, encryption support, and persistent connection benefits outweigh the head-of-line blocking risk for signaling traffic.

---

**Key Takeaways:**
1. TCP's three-way handshake adds one RTT of connection setup delay; persistent SIP connections amortize this cost across thousands of transactions
2. TCP guarantees in-order delivery, causing head-of-line blocking — when one packet is lost, all subsequent data is delayed until retransmission completes
3. TCP congestion control (slow start, window reduction) is designed for bulk transfer and actively harmful for constant-rate real-time media — this is why RTP uses UDP
4. TCP is the right choice for SIP signaling: it handles large messages without fragmentation, provides built-in reliability, and enables TLS encryption
5. Monitor TIME_WAIT socket accumulation and TCP retransmissions on SIP servers — they're early indicators of connection management and network quality issues

**Next: Lesson 17 — TLS: How Encryption Works for SIP and HTTPS**
