---
title: "DTMF — RFC 2833/4733 Telephone Events vs. In-Band Detection"
description: "Learn about dtmf — rfc 2833/4733 telephone events vs. in-band detection"
module: "Module 1: Foundations"
lesson: "33"
difficulty: "Advanced"
duration: "7 minutes"
objectives:
  - Understand DTMF uses a 4×4 dual-tone frequency matrix — robust on analog, fragile with digital compression
  - Understand Three transport methods exist: in-band (audio), RFC 4733 (RTP events), and SIP INFO — RFC 4733 is strongly preferred
  - Understand Compressed codecs (G.729, Opus) destroy in-band DTMF tones — never rely on in-band with compressed codecs
  - Understand B2BUAs like Telnyx handle DTMF interworking between methods on different call legs
  - Understand Double digits usually mean both RFC 4733 and in-band are active simultaneously
slug: "dtmf-signaling"
---

Every time a caller presses "1" to reach billing or "0" for an operator, they're generating DTMF — Dual-Tone Multi-Frequency signals. It sounds simple, but DTMF transport is one of the most persistent sources of subtle bugs in VoIP systems. Missed IVR digits, failed bank authentication, broken calling card systems — these all trace back to DTMF handling problems.

## The DTMF Frequency Matrix

DTMF uses a 4×4 matrix of frequencies. Each key press generates two simultaneous tones — one from a low-frequency group and one from a high-frequency group:

|        | 1209 Hz | 1336 Hz | 1477 Hz | 1633 Hz |
|--------|---------|---------|---------|---------|
| 697 Hz |    1    |    2    |    3    |    A    |
| 770 Hz |    4    |    5    |    6    |    B    |
| 852 Hz |    7    |    8    |    9    |    C    |
| 941 Hz |    *    |    0    |    #    |    D    |

The dual-tone design was intentional — it's nearly impossible for human speech to accidentally produce two specific frequencies simultaneously. This made DTMF robust on analog lines. But digital compression changes everything.

## Three Methods of DTMF Transport

### Method 1: In-Band (Audio Stream)

The original approach — DTMF tones are simply part of the audio stream. The receiver's DSP detects the tones by analyzing the audio in real-time.

**Why it breaks:** Compressed codecs like G.729 model the *human vocal tract*, not arbitrary tones. When G.729 compresses DTMF tones, the reconstructed audio may not contain the exact frequencies needed for reliable detection. Even small distortions cause missed digits. Voice Activity Detection (VAD) makes it worse — it may classify DTMF tones as silence and suppress them entirely.

G.711 passthrough works reasonably well for in-band DTMF because it's uncompressed PCM. But the moment any hop in the path transcodes to a compressed codec, you risk tone corruption.

> **💡 NOC Tip:**  a customer reports "IVR not recognizing digits" and they're using G.729, in-band DTMF is your first suspect. Check the SDP negotiation — are telephone-events being negotiated?

### Method 2: RFC 2833/4733 (RTP Named Telephone Events)

This is the preferred method and the one you'll see in most Telnyx deployments. Instead of embedding tones in the audio, DTMF digits are sent as special RTP packets with a dedicated payload type (typically 101).

The RFC 4733 packet contains:
- **Event code:** Which digit (0-9, *, #, A-D)
- **End bit (E):** Set on the final packet for this digit
- **Duration:** How long the key has been pressed (in timestamp units)
- **Volume:** Power level of the tone (for reconstruction if needed)

When you press "5", the sender transmits multiple RTP packets with event=5, incrementing duration, and sets the E bit on the last three packets (redundancy for reliability). The receiver knows exactly which digit was pressed without any audio analysis.

**Why it's better:**
- Works with any codec — the digit data is independent of audio compression
- No DSP detection errors — the digit is explicitly signaled
- Redundant end packets protect against packet loss
- Lower CPU usage — no real-time tone detection needed

**How it's negotiated:** In SDP, you'll see:
```
m=audio 10000 RTP/AVP 0 101
a=rtpmap:0 PCMU/8000
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16
```

The `fmtp:101 0-16` means events 0-16 are supported (digits 0-9, *, #, A-D, and flash).

### Method 3: SIP INFO

DTMF digits are sent as SIP messages (completely outside RTP):
```
INFO sip:user@host SIP/2.0
Content-Type: application/dtmf-relay

Signal=5
Duration=160
```

**The problem:** SIP INFO travels through the signaling path, not the media path. This adds latency (SIP proxies, TCP processing) and can arrive out of order relative to the audio. It also requires the SIP dialog to be active — if signaling and media take different paths (common in B2BUA architectures), timing becomes unpredictable.

SIP INFO is generally a last resort, used when RFC 4733 negotiation fails.

## The Negotiation Problem

The most common DTMF failure in a NOC environment is a **method mismatch**. Here's the scenario:

1. Customer PBX sends INVITE with `telephone-event/8000` in SDP
2. Far-end carrier doesn't support RFC 4733, strips it from the answer
3. Customer PBX sends DTMF as RFC 4733 packets anyway (some devices do this regardless of negotiation)
4. Far-end ignores the telephone-event packets — it's waiting for in-band tones
5. No DTMF gets through

In a B2BUA like Telnyx, this is handled by converting between methods. If the customer sends RFC 4733 but the carrier needs in-band, Telnyx's media processing generates actual DTMF tones from the event data and injects them into the audio stream. This is called **DTMF interworking** and it's one of the reasons B2BUAs exist.

> **💡 NOC Tip:** en debugging DTMF issues, always check **both legs** of the B2BUA independently. The customer leg might negotiate RFC 4733 perfectly while the carrier leg has a mismatch.

## Real Troubleshooting Scenario: Double Digits

**Symptom:** Customer reports their IVR receives each digit twice.

**Investigation:**
1. Pull the PCAP for the call
2. Filter for the telephone-event payload type
3. Notice RFC 4733 events being sent normally
4. But also notice the audio stream still contains audible DTMF tones

**Root cause:** The customer's PBX is sending DTMF *both* as RFC 4733 events AND in the audio stream simultaneously. The receiving system detects both — once from the RFC 4733 packet and once from in-band detection of the audio.

**Fix:** Configure the customer's PBX to mute DTMF tones in the audio stream when sending RFC 4733 events (most PBXes have an "RFC 2833" or "Out-of-band DTMF" setting that does this).

## Real Troubleshooting Scenario: Missed Digits on Long-Distance Calls

**Symptom:** DTMF works fine for local calls but fails on international calls.

**Investigation:**
1. Check SDP negotiation on both legs — RFC 4733 negotiated correctly
2. Pull PCAP — RFC 4733 packets are present and correct
3. Check the carrier leg — the international carrier is transcoding to G.729
4. The carrier's gateway is converting RFC 4733 to in-band tones, then G.729 is corrupting them

**Root cause:** The international carrier's media gateway converts telephone events to in-band tones for their TDM network, but then re-encodes to G.729 on a subsequent IP hop, corrupting the tones.

**Fix:** Work with the carrier to ensure DTMF events are carried end-to-end without conversion, or request G.711 on the carrier leg to preserve tone fidelity.

## DTMF Timing and Duration

DTMF detection requires tones to be present for a minimum duration — typically 40-80ms. If a user taps a key too quickly, some systems won't detect it. RFC 4733 packets include explicit duration, so the minimum is controlled by the sender.

The gap between digits also matters. Most systems require at least 40ms of silence between digits. Rapid-fire digit entry (common with automated systems) can cause merging where two quick presses look like one long press.

> **💡 NOC Tip:**  automated systems (calling card platforms, IVR-to-IVR bridges) report missed digits, check the inter-digit gap. Automated systems often send digits faster than human fingers, pushing below the detection threshold.

## Wireshark Analysis

In Wireshark, filter DTMF events with:
- `rtp.p_type == 101` (or whatever PT was negotiated)
- Wireshark decodes these as "RTP Event" and shows the digit, duration, and end bit
- Look for: gaps in event sequence, missing end packets, overlapping events

For in-band detection, use Wireshark's telephony menu: **Telephony → RTP → RTP Streams** and play back the audio — you can hear the tones (or their absence).

---

**Key Takeaways:**
1. DTMF uses a 4×4 dual-tone frequency matrix — robust on analog, fragile with digital compression
2. Three transport methods exist: in-band (audio), RFC 4733 (RTP events), and SIP INFO — RFC 4733 is strongly preferred
3. Compressed codecs (G.729, Opus) destroy in-band DTMF tones — never rely on in-band with compressed codecs
4. B2BUAs like Telnyx handle DTMF interworking between methods on different call legs
5. Double digits usually mean both RFC 4733 and in-band are active simultaneously
6. Always check DTMF negotiation in the SDP on **both** B2BUA legs when debugging

**Next: Lesson 32 — Latency Budget: Sources of Delay in a VoIP Call**
