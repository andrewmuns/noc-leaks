# Lesson 9: Compressed Codecs — G.729, G.722, and Why Compression Matters
**Module 1 | Section 1.2 — Digital Voice: Sampling, Quantization, and Codecs**
**⏱ ~7 min read | Prerequisites: Lesson 6**

---

## The Quality-Bandwidth-Latency Triangle

Every voice codec makes a tradeoff between three competing priorities:

- **Quality**: How close to the original speech does the decoded audio sound?
- **Bandwidth**: How many bits per second does it consume?
- **Latency**: How much delay does the encoding/decoding process add?

G.711 maximizes quality and minimizes latency, but uses the most bandwidth. Compressed codecs sacrifice some quality and add latency to dramatically reduce bandwidth. Understanding these tradeoffs is essential for making informed decisions about codec selection and for diagnosing quality issues rooted in codec choice.

## G.729 — The Workhorse Compressed Codec

G.729 compresses voice to **8 kbps** — an 8:1 compression ratio compared to G.711's 64 kbps. It does this using **Code-Excited Linear Prediction (CELP)**, a technique that models the human vocal tract.

### How CELP Works (Conceptually)

Instead of transmitting the actual audio samples, CELP transmits **parameters that describe how to reproduce the sound**:

1. **Linear Prediction Coefficients**: The encoder analyzes a frame of audio (10 ms for G.729) and builds a mathematical model of the vocal tract — essentially describing the shape of the speaker's mouth, throat, and nasal cavity for that instant
2. **Excitation Signal**: The model needs an input signal (like air from the lungs). The encoder searches a **codebook** of pre-defined excitation patterns to find the one that, when passed through the vocal tract model, best reproduces the original audio
3. **Gain and Pitch**: Additional parameters describing the loudness and fundamental frequency

The encoder transmits these parameters (not the audio itself), and the decoder reconstructs the audio by passing the codebook excitation through the described vocal tract model.

This is why CELP codecs work well for speech but poorly for non-speech audio (music, tones, noise). The model assumes human speech — if the input isn't speech, the model produces artifacts.

### G.729 Characteristics

| Parameter | Value |
|-----------|-------|
| Bitrate | 8 kbps |
| Frame size | 10 ms |
| Algorithmic delay | 15 ms (10 ms frame + 5 ms look-ahead) |
| MOS (typical) | ~3.9 (vs. G.711's ~4.3) |
| With headers (20 ms ptime) | ~24 kbps |

**G.729 Annex B** adds **Voice Activity Detection (VAD)** and **Comfort Noise Generation (CNG)**. During silence, instead of sending 8 kbps of encoded silence, G.729B sends occasional **Silence Insertion Descriptor (SID)** frames that describe the background noise characteristics. The decoder generates matching comfort noise locally.

Why comfort noise? Complete silence during pauses sounds unnatural and makes people think the call has dropped. CNG maintains the ambient sound level during gaps, creating a more natural conversational experience.

🔧 **NOC Tip:** G.729 VAD/CNG can cause issues with non-voice signals. DTMF tones, fax signals, and modem signals can be misclassified as silence and suppressed by VAD. If a customer using G.729 reports missed DTMF digits or fax failures, check if VAD is enabled. Either disable VAD for those calls or ensure DTMF is sent via RFC 2833 (not in-band) and fax uses T.38.

## G.722 — Wideband "HD Voice"

While G.729 sacrifices quality for bandwidth, G.722 goes the other direction — using **more** bandwidth than necessary for narrowband voice to deliver **wideband audio**.

G.722 samples at **16 kHz** (double G.711's 8 kHz), capturing frequencies up to **7,000 Hz** instead of 3,400 Hz. This additional bandwidth captures:
- Higher harmonics that add richness and naturalness to speech
- Fricative sounds ("s," "f," "th") that are clearer and easier to distinguish
- Better speaker identification — voices sound more like "real people"

G.722 uses **Sub-Band Adaptive Differential PCM (SB-ADPCM)**, splitting the audio into lower and upper sub-bands and encoding each with different precision. Despite covering twice the frequency range, it operates at **64 kbps** — the same as G.711.

| Parameter | Value |
|-----------|-------|
| Bitrate | 48, 56, or 64 kbps |
| Sampling rate | 16 kHz |
| Audio bandwidth | 50-7,000 Hz |
| MOS (typical) | ~4.5+ (wideband scale) |

A subtle but important detail: G.722 is registered in SDP as **payload type 9** with a clock rate of **8000** — not 16000. This is a historical artifact (the RFC was written when 8 kHz clocking was assumed). The actual audio sampling rate is 16 kHz. Don't let the SDP confuse you.

🔧 **NOC Tip:** If a customer says "calls sound amazing internally but terrible to external numbers," they're likely using G.722 internally (between their SIP phones on the LAN) and G.711 to the PSTN via Telnyx. The perceived quality drop isn't a Telnyx problem — it's the difference between wideband and narrowband audio. Manage expectations: PSTN calls are inherently narrowband (3.4 kHz), and no amount of optimization will give them G.722 quality.

## Algorithmic Delay — The Hidden Cost of Compression

Compressed codecs need to analyze a chunk of audio before they can encode it. This introduces **algorithmic delay** — time spent buffering and processing:

| Codec | Frame Size | Look-ahead | Algorithmic Delay |
|-------|-----------|------------|-------------------|
| G.711 | N/A | 0 ms | **0 ms** |
| G.722 | N/A | 1.5 ms | **1.5 ms** |
| G.729 | 10 ms | 5 ms | **15 ms** |
| G.723.1 | 30 ms | 7.5 ms | **37.5 ms** |

G.729's 15 ms algorithmic delay exists at *both* ends of the call (encoder + decoder), adding 30 ms to the total one-way latency. On a call that's already approaching the 150 ms one-way delay threshold (Lesson 32), an extra 30 ms from codec processing can push the experience from "acceptable" to "poor."

## Transcoding — The Expensive Middle Ground

**Transcoding** happens when the two ends of a call negotiate different codecs. In Telnyx's B2BUA architecture, this means:

1. Customer sends G.729-encoded RTP to Telnyx
2. Telnyx's media server decodes the G.729 back to PCM
3. Telnyx re-encodes the PCM as G.711 for the PSTN leg
4. The reverse path does the same in the other direction

This process has three costs:

**CPU**: Transcoding is computationally expensive, especially CELP codecs. Each concurrent transcoded call consumes measurable CPU resources on the media server.

**Quality**: Each encode/decode cycle introduces distortion. G.729 → PCM → G.711 loses quality at two points. If the far end also transcodes, quality degrades further. This is called **tandem encoding loss**.

**Latency**: Transcoding adds processing delay on top of the codec's inherent algorithmic delay.

🔧 **NOC Tip:** When investigating quality complaints on specific call paths, check if transcoding is occurring. In a SIP trace, compare the codecs in the SDP on each leg of the B2BUA. If leg A negotiated G.729 and leg B negotiated G.711, transcoding is happening. If possible, align codecs to avoid transcoding — configure the customer's equipment to offer G.711 as the preferred codec when calling PSTN destinations.

## A Real Troubleshooting Scenario

**Scenario:** A customer using Telnyx SIP trunks reports that their IVR system fails to recognize DTMF input from some callers. The IVR works fine for most callers but fails for callers coming from certain carriers.

**Analysis:**
- The failing carriers are sending G.729-encoded audio with in-band DTMF
- G.729's CELP model is designed for speech, not tones — DTMF tones get distorted by the compression
- The IVR is using in-band DTMF detection, which can't reliably detect tones that have been through G.729 compression

**Resolution:**
1. Ensure the IVR accepts RFC 2833 DTMF (Lesson 31) — this sends DTMF as out-of-band events, unaffected by codec compression
2. Negotiate `telephone-event` in the SDP to enable RFC 2833
3. If in-band detection is required, ensure the audio path uses G.711 (not G.729) for calls to the IVR

---

**Key Takeaways:**
1. G.729 achieves 8:1 compression using CELP vocal tract modeling — excellent for speech, problematic for tones and non-speech audio
2. G.729 Annex B (VAD/CNG) saves bandwidth during silence but can suppress non-speech signals like DTMF and fax
3. G.722 delivers wideband "HD Voice" at 64 kbps by sampling at 16 kHz — doubling the audio frequency range compared to G.711
4. Compressed codecs add algorithmic delay (15-37.5 ms) that compounds in the total end-to-end latency budget
5. Transcoding between codecs costs CPU, quality, and latency — align codecs across call legs whenever possible

**Next: Lesson 8 — Opus — The Modern Codec and Why It Won**
