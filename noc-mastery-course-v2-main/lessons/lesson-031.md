# Lesson 31: RTP — Real-time Transport Protocol Deep Dive

**Module 1 | Section 1.8 — RTP/RTCP**
**⏱ ~8 min read | Prerequisites: Lessons 15, 6**

---

## What RTP Provides

RTP doesn't guarantee timely delivery — UDP doesn't either. What RTP provides is the information receivers need to reconstruct real-time streams even when packets arrive out of order, late, or not at all.

### RTP Header (12 bytes minimum)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|V=2|P|X|  CC   |M|     PT      |       Sequence Number         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Timestamp                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Synchronization Source (SSRC) identifier            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Contributing Source (CSRC) identifiers (optional)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Key fields:**
- **Version (V):** Always 2
- **Padding (P):** Last bytes are padding (for block ciphers)
- **Extension (X):** Header extension present
- **CSRC Count (CC):** Number of contributing sources
- **Marker (M):** Interpretation depends on payload type (often "start of talkspurt")
- **Payload Type (PT):** Codec identifier (0 = PCMU, 8 = PCMA, etc.)
- **Sequence Number:** 16-bit, increments by 1 per packet, detects loss/reorder
- **Timestamp:** Sampling instant, used for jitter buffer timing
- **SSRC:** Random 32-bit identifier for this stream source

---

## Sequence Numbers: Detecting Loss and Reordering

The 16-bit sequence number increments by 1 for each RTP packet sent:

```
Packet 1: seq=1000
Packet 2: seq=1001
Packet 3: seq=1003  ← Missing 1002!
Packet 4: seq=1004
```

Receiver detects loss by gap in sequence. Reordering is detected by sequence arriving lower than expected but higher than last playout.

**Loss calculation:**
```
loss_percent = (expected_packets - received_packets) / expected_packets * 100
```

🔧 **NOC Tip:** In Wireshark, apply the RTP stream analysis to see loss, jitter, and MOS scores. Telephony quality degrades noticeably above 1% loss and becomes unusable above 5%.

---

## Timestamps: Reconstructing Timing

The timestamp represents the sampling instant of the first sample in the packet:

- **G.711 at 8kHz:** Each 20ms packet = 160 samples
- Timestamp increments by 160 each packet
- **Independent of send time** — accounts for encoding delay

**Why this matters:**

Network jitter means packets arrive at irregular intervals:
```
Expected: every 20ms
Actual arrival: 15ms, 25ms, 18ms, 32ms, 12ms...
```

The receiver uses timestamp to know when each packet **should** be played, not when it arrived. This feeds into the jitter buffer.

---

## SSRC and CSRC: Identifying Streams

### SSRC (Synchronization Source)

- Randomly generated 32-bit identifier for this RTP stream
- Uniquely identifies the sender in this RTP session
- Used to distinguish streams in mixed environments

### CSRC (Contributing Source)

When multiple streams are mixed (conference bridge), the mixer lists original sources:

```
SSRC of mixer: 0x12345678
CSRC list: [0xAABBCCDD, 0x11223344]  ← Alice and Bob's original streams
```

Receivers can identify who is speaking even in mixed audio.

---

## Payload Types: Mapping Numbers to Codecs

### Static Payload Types (RFC 3551)

| PT | Name | Description |
|----|------|-------------|
| 0 | PCMU | G.711 μ-law |
| 3 | GSM | GSM 06.10 |
| 8 | PCMA | G.711 A-law |
| 9 | G722 | G.722 (wideband) |
| 18 | G729 | G.729 |
| 34 | H263 | H.263 video |

### Dynamic Payload Types (96-127)

Modern codecs use dynamic assignment via SDP:
```sdp
m=audio 10000 RTP/AVP 96 97 0
a=rtpmap:96 opus/48000/2
a=rtpmap:97 telephone-event/8000
a=rtpmap:0 PCMU/8000
```

- `PT 96` = Opus
- `PT 97` = DTMF events
- `PT 0` = G.711 PCMU

🔧 **NOC Tip:** In PCAP analysis, if payload types aren't recognized by Wireshark, check the SDP exchange for the rtpmap mappings. Manual decode may be needed if the capture missed the SIP signaling.

---

## RTP Sessions and Ports

An RTP "session" is defined by:
- Destination IP address
- Destination port (even number)
- Protocol (UDP)

RTCP uses the next higher port (RTP port + 1):
```
RTP:  10000 (even)
RTCP: 10001 (odd)
```

🔧 **NOC Tip:** When firewall rules are created, both RTP and RTCP ports must be allowed. RTP alone won't provide quality metrics needed for troubleshooting.

---

## Key Takeaways

1. **RTP header** provides sequencing, timing, and source identification — not delivery guarantees
2. **Sequence numbers** detect packet loss and reordering — gaps indicate network issues
3. **Timestamps** carry sampling time, used for jitter buffer playout scheduling
4. **SSRC** identifies unique stream sources; **CSRC** lists contributors for mixed streams
5. **Payload types** map to codecs — static (0-95) or dynamic (96-127) via SDP negotiation
6. **RTCP** uses next port above RTP for control and quality feedback

---

**Next: Lesson 30 — RTCP — Feedback, Quality Reporting, and Congestion Control**
