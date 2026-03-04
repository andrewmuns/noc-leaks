# Lesson 59: T.38 Fax over IP — Why Fax Still Matters

**Module 1 | Section 1.16 — Special Protocols**
**⏱ ~6 min read | Prerequisites: Lessons 29, 48**

---

## Fax Refuses to Die

Despite decades of predictions about its demise, fax remains deeply embedded in healthcare, legal, government, and financial workflows. HIPAA allows fax but not email. Legal documents require signatures that fax workflows handle. Fax persists because it works, is legally recognized, and changing workflows is expensive.

---

## The Fax Problem: Audio Faxes Fail

Traditional fax machines send tones over analog phone lines:
- `2100 Hz` CED (called terminal identification) tone
- `V.21` modulation for control (300 bps)
- `V.27`, `V.29`, `V.17` for page data (up to 14.4 kbps)

When these tones travel over VoIP using G.711 passthrough:

1. **Packet loss:** Even 1% loss corrupts the page
2. **Jitter:** Timing errors cause retraining, slowing transmission
3. **Codec compression:** G.729 destroys fax entirely (not designed for modem tones)
4. **Compression:** Silence suppression cuts mid-page tones
5. **Delay:** Packetization adds latency that breaks timing

**Success rate:** G.711 passthrough fax often fails 5-20% of pages.

---

## T.38: Fax over IP

T.38 extracts the fax data and transports it as digital packets, avoiding the problems of audio transport.

### How T.38 Works

```
Fax Machine --(analog tones)--> T.38 Gateway
                                       |
                                       | (demodulate)
                                       v
                              [Fax data extracted]
                                       |
                                       | (T.38 UDPTL packets)
                                       v
                              T.38 Gateway --(analog tones)--> Fax Machine
```

**Phases:**
1. **Phase A:** CED/CNG detection (fax tone detection)
2. **Phase B:** V.21 negotiation (capabilities exchange)
3. **Phase C:** Image data transmission (T.4/T.6 format)
4. **Phase D:** Post-message procedures (confirmation, next page)
5. **Phase E:** Call release

### T.38 Transport: UDPTL

T.38 uses **UDPTL** (UDP Transport Layer), not RTP:

```
UDPTL Header:
- Sequence number
- Error correction info

Payload:
- T30 indicator (CNG, CED, V.21, etc.)
- T4 data (fax image data)
```

**Redundancy:** T.38 can send duplicate packets for reliability:
- Forward error correction (FEC)
- Redundancy (send same data N times)

---

## SDP Negotiation for T.38

Fax capability is signaled in SDP:

```sdp
m=image 10000 udptl t38
a=T38FaxVersion:0
a=T38MaxBitRate:14400
a=T38FaxRateManagement:transferredTCF
a=T38FaxUdpEC:t38UDPRedundancy
```

**Media type:** `image` (not `audio` or `video`)
**Transport:** `udptl` (not `RTP/AVP`)
**Format:** `t38`

### Interop Attributes

| Attribute | Meaning | Notes |
|-----------|---------|-------|
| `T38FaxVersion` | 0 = standard | Should match |
| `T38MaxBitRate` | Max speed (bps) | 9600 or 14400 typical |
| `T38FaxRateManagement` | How to train | `transferredTCF` or `localTCF` |
| `T38FaxUdpEC` | Error correction | `t38UDPRedundancy` or `t38UDPFEC` |

🔧 **NOC Tip:** T.38 negotiation failures usually come from mismatched `T38FaxRateManagement` or `T38FaxUdpEC` settings. If fax calls disconnect after answering, check these attributes in the SDP exchange.

---

## T.38 Gateway Placement

### Scenario 1: Both Sides T.38 Capable

```
Fax A  <--SIP+T.38-->  Telnyx  <--SIP+T.38-->  Fax B
       (T.38 end-to-end, no audio conversion)
```

**Best case:** Digital fax data flows end-to-end.

### Scenario 2: One Side Audio Only

```
Fax A  <--T.38-->  Telnyx Gateway  <--G.711-->  PSTN  <--Analog-->  Fax B
                    (transcode T.38 to audio,
                     detect fax tones)
```

The gateway:
1. Receives T.38 from Fax A
2. Modulates back to V.17/V.29 tones
3. Sends G.711 to PSTN
4. Detects incoming fax tones and demodulates
5. Encodes as T.38 back to Fax A

### Scenario 3: Both Sides Audio (Fallback)

```
Fax A  <--G.711-->  Telnyx  <--G.711-->  PSTN  <--Analog-->  Fax B
       (G.711 passthrough - higher failure rate)
```

When no T.38 gateway is available, falls back to audio passthrough.

---

## Common T.38 Failures

| Symptom | Cause | Solution |
|---------|-------|----------|
| Partial page / errors | Packet loss | Enable redundancy, use FEC |
| Slow transmission | Multiple retrains | Check jitter, reduce compression |
| No answer to fax | T.38 not negotiated | Check SDP, ensure `m=image` |
| First page OK, rest fail | Mid-call T.38 switch | Ensure correct re-INVITE handling |
| Garbled pages | Codec mangling | Disable echo cancellation, VAD |

### Debug Commands

```bash
# Check T.38 capability on a connection
# Look for in SDP: m=image...t38

# Capture T.38 UDPTL
tshark -r capture.pcap -Y "t38"

# Check for fax tones in audio
tshark -r capture.pcap -Y "rtp.p_type == 0" -T fields -e rtp.payload | xxd | grep -i "cng\|ced"
```

🔧 **NOC Tip:** When a customer reports "faxes failing," always ask:
1. Is this T.38 or G.711 passthrough?
2. Are both endpoints T.38 capable?
3. What speed (14.4k vs 9.6k)?
4. Single page or multi-page failures?

---

## Key Takeaways

1. **Fax persists** in regulated industries despite being obsolete
2. **G.711 passthrough** has high failure rates due to packet loss, jitter, compression
3. **T.38** extracts fax data and transports digitally, avoiding audio problems
4. **T.38 uses UDPTL** not RTP, with redundancy options for reliability
5. **SDP attributes** negotiate T.38 capability and parameters
6. **Gateway placement** determines if conversion to/from audio happens

---

**Next: Lesson 58 — DTMF Handling — RFC 2833, SIP INFO, and In-Band**
