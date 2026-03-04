# Lesson 17: UDP — Why Real-Time Traffic Chooses Unreliability

**Module 1 | Section 1.4 — Protocol Stack**
**⏱ ~6 min read | Prerequisites: Lesson 13**

---

## The UDP Header: Elegant Simplicity

The User Datagram Protocol header is just 8 bytes:

```
 0      7 8     15 16    23 24    31
+--------+--------+--------+--------+
|   Source Port    |   Dest Port     |
+--------+--------+--------+--------+
|     Length       |    Checksum     |
+--------+--------+--------+--------+
```

That's it. Source port, destination port, length, checksum. No sequence numbers, no acknowledgments, no connection state, no flow control, no congestion control. UDP takes an application's data, slaps on port numbers, and hands it to IP for delivery.

Compare this to TCP's 20-byte header with its sequence numbers, acknowledgments, window sizes, flags, and options. UDP's simplicity isn't a limitation — it's a deliberate design choice that makes it perfect for real-time communications.

## Why VoIP Chooses UDP

Consider what happens when a voice packet is lost on a TCP connection:

1. The receiver notices a gap in sequence numbers
2. It sends a duplicate ACK
3. The sender detects the loss (via duplicate ACKs or timeout)
4. The sender retransmits the lost packet
5. The retransmitted packet arrives — perhaps 200-500ms later
6. TCP holds all subsequent packets in order, waiting for the retransmission

By the time the retransmitted packet arrives, it's far too late for real-time playout. A 200ms gap in conversation is extremely noticeable. And worse, **TCP's in-order delivery means all packets received after the lost one are also delayed** — this is called **head-of-line blocking** (covered more in Lesson 16).

With UDP, when a packet is lost:
1. The receiver notices the gap (via RTP sequence numbers)
2. The jitter buffer applies Packet Loss Concealment (interpolation)
3. Playback continues with a barely perceptible glitch
4. Total impact: ~20ms of interpolated audio

**For voice, a small gap filled with interpolation sounds infinitely better than a 200ms pause followed by a burst of delayed audio.** This is why RTP runs on UDP.

🔧 **NOC Tip:** If you ever see RTP running over TCP (it can, per RFC 4571), something unusual is happening — typically a very restrictive firewall environment. This will degrade voice quality under any packet loss conditions. Note this for the customer and recommend opening UDP ports.

## No Connection State: Implications

UDP is **connectionless**. There's no handshake, no established session, no teardown. Each datagram is independent. This has important implications:

**Sending:** An application can send a UDP packet to any address:port at any time without establishing a connection first. The first RTP packet a phone sends requires no setup at the transport layer — SIP/SDP handles signaling at the application layer.

**Receiving:** Any UDP packet arriving at the right port is delivered to the application. There's no connection to "accept." This simplicity is why UDP servers (like SIP proxies) can handle enormous numbers of concurrent "sessions" — there's no per-connection state in the kernel.

**Ordering:** UDP provides no ordering guarantees. Packets may arrive out of order, duplicated, or not at all. RTP's sequence numbers (Lesson 29) handle reordering detection. The jitter buffer handles timing reconstruction.

## UDP and Firewalls: The Stateful Tracking Problem

Here's where UDP's statelessness becomes a significant operational challenge. **Stateful firewalls** track connections to allow return traffic. For TCP, this is straightforward — the firewall sees the SYN, tracks the connection, and allows responses until FIN/RST.

For UDP, there's no SYN or FIN. The firewall creates a "pseudo-connection" entry when it sees an outbound UDP packet. It allows return traffic to the same source:port ↔ dest:port pair. But when does this entry expire?

**UDP firewall timeouts are typically 30-60 seconds.** If no packets are exchanged within that window, the firewall removes the entry. Any subsequent inbound packet is dropped as unsolicited.

### Why This Matters for VoIP

**SIP registration:** A phone sends REGISTER to the SIP server via UDP. The firewall creates an entry allowing responses. But registration expires in 60-3600 seconds. If the firewall timeout is shorter than the registration interval, the firewall entry expires before re-registration. The server's attempts to send an INVITE to the phone get blocked.

**RTP media:** During call hold, RTP packets stop flowing. If hold lasts longer than the firewall's UDP timeout, the media pinhole closes. When the call resumes, audio fails — classic one-way audio after hold.

**Keepalive mechanisms** solve this: SIP OPTIONS pings, CRLF keepalives, or RTP comfort noise packets keep the firewall entry alive.

🔧 **NOC Tip:** When a customer reports one-way audio that happens specifically after hold or long silence periods, the firewall's UDP timeout is your prime suspect. Ask: "What's your firewall's UDP session timeout?" If it's 30 seconds, that's the problem. Either increase it to 300+ seconds or ensure the SIP endpoint sends keepalives more frequently than the timeout.

### Real Troubleshooting Scenario

**Scenario:** A customer's phones register fine and make calls, but incoming calls to their phones fail intermittently. The SIP server sends INVITE to the phone's Contact address, but gets no response (408 timeout).

**Investigation:** The phone registered from behind NAT. The firewall created a UDP pinhole for the registration flow. But the customer's SIP registrar refresh interval is 3600 seconds (1 hour), and the firewall's UDP timeout is 60 seconds. After 60 seconds of no SIP traffic, the pinhole closes. Inbound INVITEs can't reach the phone.

**Fix:** Reduce the registration interval to 30 seconds (keeping the pinhole open), or configure the phone to send periodic SIP keepalives (OPTIONS or CRLF pings every 20 seconds).

## UDP Checksum

The UDP checksum covers the UDP header, payload, and a pseudo-header (source/dest IP, protocol, length). It detects corruption but **does not correct it** — a corrupted packet is simply discarded.

**In IPv4, the UDP checksum is optional.** Setting it to zero means "no checksum computed." This was done for performance in early implementations. In practice, most modern stacks compute the checksum.

**In IPv6, the UDP checksum is mandatory.** This is because IPv6 removed the IP header checksum (Lesson 14), so UDP's checksum is the only thing protecting against corruption for UDP traffic.

For VoIP, a corrupted voice packet is discarded, creating a small gap handled by PLC. This is the right behavior — playing corrupted audio would sound worse than a brief interpolated gap.

## Port Numbers and Multiplexing

UDP's primary function beyond "unreliable delivery" is **port-based multiplexing**. Port numbers let a single IP address run multiple services:

- **SIP:** Typically port 5060 (UDP/TCP) or 5061 (TLS)
- **RTP:** Dynamic port ranges, commonly 10000-20000 or 16384-32768
- **STUN/TURN:** Port 3478
- **DNS:** Port 53

The source port is typically ephemeral (randomly chosen from a high range), while the destination port identifies the service.

**Port exhaustion** can be an issue on NAT devices handling many concurrent calls. Each call's RTP stream needs a unique NAT mapping. A NAT device with 65,535 available ports handling calls that each consume 2 ports (one for each direction) can theoretically handle ~32,000 concurrent calls through a single IP — but in practice, limitations hit much sooner.

🔧 **NOC Tip:** When debugging with `tcpdump` or Wireshark, UDP port numbers are your primary filter. `tcpdump -i any udp port 5060` captures SIP. `tcpdump -i any udp portrange 10000-20000` captures RTP. Without port-based filtering, you'll drown in irrelevant traffic.

## UDP's Role in Modern Protocols

UDP's lightweight nature has made it the foundation for increasingly sophisticated protocols:

- **QUIC (HTTP/3):** Google's protocol builds TCP-like reliability on top of UDP, but with better multiplexing and encryption. Used by modern web traffic.
- **WireGuard:** Modern VPN protocol using UDP for its simplicity and performance.
- **WebRTC's DTLS-SRTP:** Encryption handshake and encrypted media both over UDP.

The trend is clear: build the specific reliability mechanisms you need at the application layer, rather than accepting TCP's one-size-fits-all approach.

---

**Key Takeaways:**
1. UDP's 8-byte header provides port-based multiplexing with zero connection overhead — perfect for real-time traffic where retransmission is worse than loss
2. For voice, a 20ms gap with interpolation (UDP packet loss) sounds far better than a 200ms pause with head-of-line blocking (TCP retransmission)
3. Stateful firewalls create pseudo-connections for UDP with short timeouts (30-60s); when these expire, return traffic is blocked — the #1 cause of intermittent VoIP failures behind firewalls
4. SIP/RTP keepalive mechanisms (OPTIONS pings, CRLF keepalives, comfort noise) are essential to keep firewall pinholes open
5. UDP checksum is optional in IPv4 but mandatory in IPv6; corrupted packets are silently discarded, which is the correct behavior for real-time audio

**Next: Lesson 16 — TCP: Reliability, Congestion Control, and SIP over TCP/TLS**
