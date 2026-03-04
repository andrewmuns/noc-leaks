# Lesson 71: Call Control Commands Deep Dive

**Module 2 | Section 2.2 — Voice API**
**⏱ ~7 min read | Prerequisites: Lesson 60**

---

## Beyond the Basics: What Actually Happens When You Issue a Command

In Lesson 60, you learned that Call Control is a webhook-driven state machine — incoming events trigger your application, which responds with commands. Now let's go deeper into *what each command actually does* at the SIP and RTP level, because that's where NOC troubleshooting lives.

When a customer calls `POST /v2/calls/{call_control_id}/actions/answer`, they're not just flipping a boolean. Telnyx's B2BUA generates a SIP `200 OK` with an SDP answer on the inbound leg, establishing the media path. The codec negotiation you studied in Lesson 49 happens right here. If the SDP offer/answer exchange fails, the call drops — and the customer blames the API.

## Media Commands: play_audio, speak, and gather

### play_audio

`play_audio` streams a pre-recorded audio file into the call. Under the hood, Telnyx's media server:

1. Fetches the audio file from the provided URL (or Telnyx Storage)
2. Transcodes it to match the negotiated codec (e.g., G.711 μ-law)
3. Packetizes it into RTP packets at the correct interval (typically 20ms)
4. Injects these packets into the existing RTP stream

The critical detail: **the audio file must be accessible from Telnyx's infrastructure**. If the URL requires authentication, is behind a firewall, or returns a redirect chain that times out, the command silently fails or plays silence.

🔧 **NOC Tip:** When a customer reports "play_audio isn't working," first check if the audio URL is publicly accessible. Use `curl -I <url>` from a Telnyx network perspective. Common culprits: expired presigned URLs, geo-restricted CDNs, and corporate firewalls blocking Telnyx's IP ranges.

### speak (Text-to-Speech)

The `speak` command converts text to audio using a TTS engine, then plays the result into the call. This adds latency compared to `play_audio` because the TTS synthesis must complete before playback begins. The pipeline:

1. Text is sent to the TTS engine (with voice, language, and speed parameters)
2. TTS engine generates PCM audio
3. Audio is transcoded to the call's negotiated codec
4. RTP packets are injected into the media stream

### gather (DTMF and Speech Input)

`gather` is one of the most complex commands because it must **simultaneously** play audio (prompt) and listen for input. It sets up DTMF detection on the RTP stream — watching for RFC 2833 telephone events (Lesson 31) or in-band tone detection.

For speech input, `gather` forks the audio stream to a Speech-to-Text engine in real-time while the caller speaks. The STT engine returns recognized text via webhook once it detects an end-of-speech pause.

**Common gather failures:**
- DTMF method mismatch: customer PBX sends in-band DTMF but the trunk is configured for RFC 2833
- Speech recognition timeouts: caller pauses too long between words
- Barge-in issues: the prompt audio doesn't stop when the caller starts speaking

## Call Manipulation: bridge, transfer, and conference

### bridge

`bridge` connects the media paths of two separate call legs. Before bridging, each leg has its own RTP stream to/from Telnyx's media servers. After bridging, the media server routes audio from Leg A to Leg B and vice versa.

```
Before bridge:
  Caller ←RTP→ [Telnyx Media] ←RTP→ (nothing yet)
  Agent  ←RTP→ [Telnyx Media] ←RTP→ (nothing yet)

After bridge:
  Caller ←RTP→ [Telnyx Media] ←RTP→ Agent
```

The B2BUA maintains both SIP dialogs independently. If one leg hangs up, the platform sends a webhook so your application can decide what to do with the other leg.

🔧 **NOC Tip:** "Bridge didn't work" often means one leg wasn't in the `answered` state. You can only bridge two active calls. Check the call states in the CDR — if one leg shows `ringing` when the bridge command was issued, that's your problem.

### transfer

`transfer` moves an active call to a new destination. This generates a new outbound INVITE (creating a third call leg), and once the transfer target answers, the original caller is bridged to the new party. The intermediate leg is torn down.

Blind transfer sends the INVITE immediately. Attended transfer lets the transferring party speak to the target first.

### conference

`conference` creates a multi-party audio mixer. Each participant's RTP stream feeds into the mixer, which combines all audio and sends a unique mix to each participant (minus their own audio, to prevent echo).

Conference mixing is CPU-intensive — each additional participant increases the mixing workload. Large conferences (50+ participants) can cause media server CPU pressure.

## Recording

`start_recording` tells the media server to capture the RTP stream to a file. Options include:

- **Single-channel**: both parties mixed into one audio stream
- **Dual-channel**: each party on a separate channel (critical for speech analytics)

The recording is written to Telnyx Storage and a webhook delivers the recording URL when complete.

🔧 **NOC Tip:** "Recording is silent on one side" in dual-channel mode almost always means a media path issue on that leg. Check the RTP stats — if one direction shows zero packets, it's not a recording problem, it's a media problem (NAT, firewall, SDP issue from Lesson 27).

## Streaming: Real-Time Audio via WebSocket

The `streaming` command opens a WebSocket connection to a customer-specified URL and sends raw audio frames in real-time. This enables:

- Live transcription
- Real-time sentiment analysis
- Custom voice AI applications
- Audio monitoring/coaching

The WebSocket receives base64-encoded audio chunks (typically PCM 8kHz). Latency is critical — the WebSocket connection must be low-latency and reliable.

**Common streaming issues:**
- WebSocket connection failures (DNS, TLS, firewall)
- Customer's WebSocket server can't keep up (backpressure)
- Audio format mismatch (customer expects 16kHz but receives 8kHz)

## Forking: Sending Audio to Multiple Destinations

`fork` duplicates the media stream and sends it to an additional destination — typically an external RTP endpoint or a WebSocket. Unlike streaming (which is WebSocket-only), forking can send raw RTP to an IP:port, useful for feeding external recording systems or analytics platforms.

## Error Handling and Race Conditions

Call Control commands are asynchronous. When you issue a command, you get back a `200 OK` from the API confirming the command was *queued*, not that it *succeeded*. Success or failure arrives as a subsequent webhook.

**The race condition problem:** If your application sends two commands in rapid succession — say `play_audio` followed by `gather` — the second command might arrive before the first completes. Call Control queues commands per-call, but understanding the queue behavior is essential.

**Critical race condition:** A `hangup` webhook can arrive while your application is processing a previous webhook and about to issue a command. If your app sends a command to a call that's already hung up, it gets a `404` or `422` error. Robust applications must handle this gracefully.

🔧 **NOC Tip:** When debugging "commands aren't working" issues, check the webhook delivery logs in Graylog. Look for the command response — did the API return 200 (accepted) or an error? Then check for the corresponding event webhook. A command that returns 200 but never triggers a completion webhook usually indicates a media server issue.

## Troubleshooting Scenario: "Our IVR Is Broken"

A customer reports their IVR stopped working — callers hear silence instead of the menu prompt.

**Investigation steps:**
1. Check webhook delivery: are webhooks reaching the customer's app? (Graylog: search for the webhook URL)
2. Check command responses: is the app issuing `speak` or `play_audio`? (Check CDR command log)
3. Check the audio source: is the audio URL accessible? (If using `play_audio`)
4. Check TTS service health: is the TTS engine responding? (Grafana: TTS latency dashboard)
5. Check media path: is RTP flowing between Telnyx and the caller? (RTCP stats)

The fix was: the customer's audio hosting expired, and `play_audio` was silently failing. The customer didn't check command event webhooks for errors.

---

**Key Takeaways:**
1. Every Call Control command maps to SIP/RTP-level operations — understanding the underlying protocol action helps debug failures
2. `gather` is the most complex command, combining audio playback with DTMF/speech detection simultaneously
3. `bridge` connects two independent call legs through Telnyx's media server — both legs must be in answered state
4. Recording issues often trace back to media path problems, not recording system problems
5. Commands are asynchronous — API 200 means "queued," not "succeeded"; always check event webhooks
6. Race conditions between commands and hangup events are a common source of application bugs

**Next: Lesson 62 — Webhook Reliability and Debugging**
