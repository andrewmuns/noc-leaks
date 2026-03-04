# Lesson 87: Fax over IP — T.38 and G.711 Passthrough
**Module 2 | Section 2.9 — Fax**
**⏱ ~7 min read | Prerequisites: Lesson 6, Lesson 44**

---

## Why Fax Refuses to Die

Fax machines were invented in the 1960s and standardized in the 1980s. They should be extinct. But fax persists — stubbornly, maddeningly — in healthcare (HIPAA compliance), legal (court filings), finance (signed documents), and government. For Telnyx, fax support isn't optional. And for NOC engineers, fax is uniquely frustrating because the technology was designed for a world that no longer exists.

## The T.30 Protocol: Fax Over PSTN

To understand why fax over IP is hard, you need to understand how fax works on the PSTN:

1. **CNG tone** — The calling fax machine sends a 1100 Hz calling tone
2. **CED tone** — The answering fax machine responds with a 2100 Hz answer tone
3. **Handshake** — The machines negotiate capabilities: resolution, page width, compression, speed
4. **Training** — The machines perform a modem training sequence to calibrate for the phone line's characteristics
5. **Page transmission** — Image data is transmitted using modem modulation (V.17, V.29, V.27ter) at speeds up to 14.4 kbps
6. **Confirmation** — Each page is acknowledged before the next is sent

The key insight: **fax is a modem protocol**. The audio on the line isn't voice — it's modulated data, indistinguishable from random noise to audio processing algorithms. The modem signals are extremely sensitive to timing, amplitude, and phase distortion.

## Why Standard VoIP Destroys Fax

Every optimization VoIP makes for voice actively destroys fax signals:

### Compression Codecs
G.729 and other compressed codecs analyze audio assuming it's human speech. They model the vocal tract and discard information that doesn't fit the model. Fax modem tones are nothing like speech — compression destroys the signal. Even G.711 with Voice Activity Detection (VAD) is fatal: VAD interprets pauses between fax pages as silence and suppresses them, but the fax protocol requires precise timing.

### Jitter
Fax modems are phase-sensitive. Even 20-30ms of jitter can cause bit errors in the demodulated data. Voice can tolerate jitter via the jitter buffer; fax can't because the modem protocol requires continuous, phase-coherent reception.

### Packet Loss
A single lost packet during fax transmission corrupts the data stream. Voice PLC can interpolate missing audio; there's no equivalent for modem data. Even 1% packet loss — barely noticeable for voice — causes fax page retransmissions or complete failures.

### Echo Cancellation
Echo cancellers are designed for voice frequencies. The T.30 protocol's 2100 Hz CED tone is specifically designed to disable echo cancellers (the phase reversal in the tone triggers echo canceller disable). If the echo canceller doesn't respond correctly, it interferes with the fax handshake.

🔧 **NOC Tip:** If a customer reports "fax calls connect but pages fail to transmit," the cause is almost always one of these audio-path issues. Check if the call is using a compressed codec, if VAD is enabled, or if there's measurable packet loss on the media path.

## T.38: The Right Solution

**T.38** (ITU-T T.38) is a protocol designed specifically for fax over IP. Instead of trying to carry fax audio over VoIP, T.38 takes a fundamentally different approach:

### How T.38 Works

1. A call starts as normal voice (audio SIP/RTP)
2. When a fax tone is detected (CNG or CED), the call switches to T.38 mode
3. A **T.38 gateway** demodulates the fax audio — extracting the actual fax data from the modem signal
4. The fax data is packaged into **UDPTL** (UDP Transport Layer) or TCP packets
5. At the other end, another T.38 gateway remodulates the data back into modem signals for the receiving fax machine
6. The actual image data travels as structured data, not as audio

### The Re-INVITE Dance

The switch from voice to T.38 happens via a SIP **re-INVITE** (as covered in Lesson 47). The re-INVITE changes the media type from audio/RTP to image/udptl:

```
m=image 12345 udptl t38
a=T38FaxVersion:0
a=T38MaxBitRate:14400
a=T38FaxRateManagement:transferredTCF
a=T38FaxMaxBuffer:1800
a=T38FaxMaxDatagram:400
a=T38FaxUdpEC:t38UDPRedundancy
```

The `m=image` line (replacing `m=audio`) is the signature of T.38. The attributes describe the T.38 capabilities: maximum bitrate, error correction method, and buffer sizes.

### T.38 Error Correction

T.38 includes its own error correction — **UDPTL redundancy**. Each UDPTL packet includes copies of previous packets, so if one is lost, the data can be recovered from subsequent packets. This is essential because fax data can't tolerate any loss.

🔧 **NOC Tip:** When debugging T.38 issues, check the re-INVITE exchange. Common failures:
- **488 Not Acceptable** — The other side doesn't support T.38
- **Re-INVITE timeout** — The re-INVITE was never answered (network issue, incompatible endpoint)
- **One side supports T.38, the other doesn't** — Falls back to G.711 passthrough (or fails)

## G.711 Passthrough: The Brute Force Approach

When T.38 isn't supported by both sides, the fallback is **G.711 passthrough**:

1. The fax audio is carried as standard G.711 audio (uncompressed PCM)
2. All audio processing is disabled: no VAD, no echo cancellation, no comfort noise generation
3. The jitter buffer is set to fixed (not adaptive) to maintain consistent timing
4. The network path must be clean: minimal jitter (<20ms), zero packet loss, low latency

G.711 passthrough treats fax audio as "really sensitive voice." It works when the network is clean but is fragile. Any packet loss or jitter spike causes fax failures.

### When to Use Each

| Method | Reliability | Requirements | Bandwidth |
|--------|-------------|-------------|-----------|
| T.38 | High | Both sides support T.38 | Low (~10 kbps) |
| G.711 passthrough | Medium | Clean network, no audio processing | 87 kbps |
| G.711 with compression | Very Low | Don't even try | N/A |

## Fax at Telnyx

Telnyx supports both T.38 and G.711 passthrough for fax. The platform can also act as a T.38 gateway — receiving fax as T.38 or G.711 and delivering the fax document as a PDF via webhook or storing it in Telnyx Storage (Lesson 81).

The programmable fax API allows:
- **Send fax** — Upload a document, Telnyx converts to fax and dials out
- **Receive fax** — Incoming fax is received, converted to PDF, and delivered via webhook
- **Status tracking** — Real-time status updates via webhooks (sending, receiving, complete, failed)

## Real-World Troubleshooting Scenario

**Scenario:** Customer reports fax transmissions fail at approximately 50% rate. When they fail, the fax connects but pages don't complete.

**Investigation:**
1. **Check codec negotiation** — Are failed calls using T.38 or G.711 passthrough? Check the SDP in the INVITE and any re-INVITEs.
2. **Check for T.38 re-INVITE failures** — If the re-INVITE to switch to T.38 is rejected or times out, the call may fall back to audio mode with a compressed codec.
3. **Check packet loss on the media path** — Even 0.5% loss can cause fax failures in G.711 passthrough mode. Check RTCP reports.
4. **Check for VAD/CNG** — If VAD (Voice Activity Detection) is enabled on the connection, it will suppress fax silence and break the protocol.
5. **Check the far-end** — Is the PSTN carrier supporting T.38 on their side? Some carriers strip T.38 and force G.711.

**Resolution:** Ensure T.38 is enabled on the Telnyx connection AND the customer's PBX. Disable VAD. If the far-end carrier doesn't support T.38, ensure the G.711 passthrough path has adequate network quality. Consider using Telnyx's fax API instead of SIP-based fax for higher reliability.

---

**Key Takeaways:**
1. Fax fails over standard VoIP because compression, VAD, jitter, and packet loss all destroy modem signals
2. T.38 solves this by demodulating fax data and transporting it as structured data (UDPTL), not audio
3. The T.38 switch happens via SIP re-INVITE, changing `m=audio` to `m=image` — re-INVITE failures cause fax failures
4. G.711 passthrough is the fallback — it works on clean networks but requires disabling all audio processing
5. When troubleshooting fax, always check: codec, VAD setting, T.38 support on both sides, and packet loss

**Next: Lesson 78 — IoT/Wireless — SIM Provisioning and Data Sessions**
