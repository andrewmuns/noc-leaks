# Lesson 61: DTMF Handling — RFC 2833, SIP INFO, and In-Band

**Module 1 | Section 1.16 — Special Protocols**
**⏱ ~7 min read | Prerequisites: Lessons 29, 42**

---

## Three Ways to Send DTMF

When a user presses a phone key, that digit must reach the far end. VoIP offers three methods, with varying compatibility:

| Method | Standard | Reliability | Notes |
|--------|----------|-------------|-------|
| **RFC 2833/4733** | RFC 4733 | Best | Out-of-band, named events |
| **SIP INFO** | RFC 6086 | Moderate | Packet-based, reliable transport |
| **In-band** | None | Poor | Audio tones in RTP |

---

## RFC 4733: Named Telephony Events

DTMF is sent as RTP packets with a special payload type:

```
Payload type: 101 (Dynamic, negotiated in SDP)
Format: telephone-event
```

### SDP Negotiation

```sdp
m=audio 10000 RTP/AVP 0 8 101
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16  # Event codes to support
```

**Event codes:**
| Code | Event |
|------|-------|
| 0-9 | Digits 0-9 |
| 10 | * |
| 11 | # |
| 12-15 | A-D |
| 16 | Flash hook |

### RTP Packet Structure

An RFC 4733 DTMF packet:
```
RTP Header (12 bytes)
  Payload Type: 101
  
DTMF Payload (4 bytes):
  Event code: 0-16
  E (End) bit: 1 = last packet for this event
  R (Reserved): 0
  Volume: 0-63 dB
  Duration: Samples since start (in timestamp units)
```

### Event Sequence

For a single "5" keypress:
```
Time 0ms:   RTP seq=1000, E=0, Event=5, Duration=0    (start)
Time 50ms:  RTP seq=1001, E=0, Event=5, Duration=400
Time 100ms: RTP seq=1002, E=0, Event=5, Duration=800
Time 150ms: RTP seq=1003, E=1, Event=5, Duration=1200 (end)
```

The **E bit** marks the final packet. Multiple packets ensure delivery.

🔧 **NOC Tip:** In Wireshark, filter telephone events with: `rtp.p_type == 101` or use Telephony → RTP → RTP Streams analysis to see DTMF events decoded.

---

## SIP INFO Method

SIP INFO carries DTMF in the signaling channel:

```sip
INFO sip:bob@example.com SIP/2.0
Via: SIP/2.0/UDP 10.0.0.1:5060
From: <sip:alice@example.com>;tag=1234
To: <sip:bob@example.com>;tag=5678
Call-ID: abc@10.0.0.1
Content-Type: application/dtmf-relay

Signal=5
Duration=160
```

### INFO vs RFC 4733

| Aspect | RFC 4733 | SIP INFO |
|--------|----------|----------|
| Transport | RTP | SIP (TCP/UDP/TLS) |
| Timing sync | Matches audio | Independent |
| Reliability | Redundant packets | SIP retransmission |
| Bandwidth | Minimal | Higher (headers) |
| Compatibility | Near universal | Variable |

**When INFO is used:**
- Some SIP phones default to INFO
- Systems that don't support telephone-event
- Legacy equipment

### Risks of INFO

1. **Out of sync:** INFO travels separately from RTP. Under load, INFO may arrive before or after the corresponding audio.
2. **Not universally supported:** Some endpoints ignore INFO for DTMF.
3. **SIP path dependent:** INFO only works until a B2BUA that doesn't relay INFO methods.

🔧 **NOC Tip:** If customers report "DTMF not working on IVR," check which method they're using. If INFO fails, switch to RFC 4733. The B2BUA converts between methods as needed.

---

## In-Band DTMF

Audio DTMF tones in the RTP stream:

```
frequency = 697 Hz + 1209 Hz = "1"
frequency = 697 Hz + 1336 Hz = "2"
frequency = 697 Hz + 1477 Hz = "3"
frequency = 852 Hz + 1477 Hz = "9"
```

### Problems with In-Band

1. **Compression destroys tones:** G.729, G.726, etc. mangle DTMF frequencies
2. **Packet loss:** Lost packets = lost digits
3. **Clipping:** Voice activity detection cuts tone beginnings
4. **Echo cancellation:** May suppress DTMF as "echo"

**When it works:**
- G.711-only paths
- Low latency, low loss
- No compression

**When it fails:**
- Compressed codecs
- Cellular networks
- Satellite links
- Any packet loss

---

## Telnyx DTMF Handling

```
Customer A                    Telnyx B2BUA                    Customer B
     |                             |                               |
     |-- RFC 4733 (payload 101) -->|                               |
     |                             |-- Detect DTMF event --------->|
     |                             |                               |
     |                             |<-- RFC 4733 (if supported) ---|
     |                             |    (converted if needed)      |
     |<-- RFC 4733 event ----------|                               |
```

**B2BUA capabilities:**
- Receive: RFC 4733, SIP INFO, in-band (decoded)
- Detect: In-band via DSP
- Generate: RFC 4733, SIP INFO, in-band
- Convert: Between any input → any output

### SDP DTMF Negotiation

Telnyx includes telephone-event in SDP offers:
```sdp
m=audio 10000 RTP/AVP 0 8 101
a=rtpmap:101 telephone-event/8000
```

If the far end supports it, DTMF uses RFC 4733. Otherwise, fall back to INFO or in-band.

---

## Debugging DTMF Issues

### Checklist

1. **Verify method:** RFC 4733, INFO, or in-band?
2. **Check SDP:** Does SDP include `telephone-event`?
3. **Payload type:** Is dynamic PT consistent?
4. **Packet capture:** Do DTMF packets flow?
5. **IVR test:** Dial a test number, press digits, confirm reception

### Common Issues

| Problem | Likely Cause | Fix |
|---------|--------------|-----|
| Digits dropped | In-band over compressed codec | Switch to RFC 4733 |
| Double digits | Both INFO and RFC 4733 sent | Disable one method |
| Wrong digits in IVR | Payload type mismatch | Check SDP PT numbers |
| Works first call, not second | SIP ALG interference | Disable SIP ALG |
| Digits work, flash hook doesn't | Event 16 not supported | Check `fmtp` line |

### PCAP Analysis

```bash
# Find RTP telephone events
tshark -r capture.pcap -Y "rtp.p_type == 101" -T fields -e rtp.payload

# Find SIP INFO with DTMF
tshark -r capture.pcap -Y "sip.Method == \"INFO\"" -V | grep -A5 "Signal="

# Extract DTMF sequence
tshark -r capture.pcap -Y "rtpevent" -T fields -e rtpevent.payload_type -e rtpevent.event_id
```

🔧 **NOC Tip:** The call-site-finder output includes DTMF negotiation parameters. If debugging a specific call, check which method was actually used by examining the media streams at the B2BUA.

---

## Key Takeaways

1. **RFC 4733 (telephone-event)** is the preferred method — reliable, precisely timed, widely supported
2. **SIP INFO** is acceptable but can fall out of sync with audio and may not traverse all B2BUAs
3. **In-band** (audio tones) is a last resort — fails under compression, packet loss, VAD, echo cancellation
4. **SDP negotiation** determines which method is used — ensure `telephone-event` is offered
5. **Telnyx converts** between methods at the B2BUA for maximum compatibility
6. **Debug with captures:** Look for RTP payload type 101, SIP INFO packets, or audio frequency analysis

---

**Next: Lesson 59 — SIP REFER and Call Transfer**
