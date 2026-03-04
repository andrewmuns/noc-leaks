# Lesson 76: Voice AI Architecture — AI Assistants and the Processing Pipeline

**Module 2 | Section 2.5 — Voice AI**
**⏱ ~8 min read | Prerequisites: Lesson 60**

---

## The Vision: Conversational AI Over the Phone

Voice AI turns phone calls into intelligent conversations powered by Large Language Models. Instead of rigid IVR menus ("Press 1 for sales..."), a caller speaks naturally and an AI assistant understands, reasons, and responds in real-time with a human-like voice.

This sounds simple but is an extraordinary engineering challenge. The AI must listen, understand, think, and speak — all within the latency budget of a real-time conversation. Humans perceive response delays as short as 500ms as unnatural. The entire pipeline — audio capture, speech recognition, LLM inference, and speech synthesis — must complete within about 1-2 seconds to feel conversational.

## The Pipeline: Audio In → Intelligence → Audio Out

```
Phone Call                 Telnyx Voice AI Pipeline
                    ┌─────────────────────────────────────┐
Caller speaks ────▶ │ Audio Capture Agent (ACA)            │
                    │         │                             │
                    │         ▼                             │
                    │ Speech-to-Text (STT)                 │
                    │ "I'd like to check my order status"  │
                    │         │                             │
                    │         ▼                             │
                    │ LLM Manager → LLM                    │
                    │ (reasoning, tool use, response)      │
                    │ "Let me look that up for you..."     │
                    │         │                             │
                    │         ▼                             │
                    │ Text-to-Speech (TTS)                 │
                    │ [synthesized audio]                  │
                    │         │                             │
Caller hears  ◀──── │ RTP injection into call              │
                    └─────────────────────────────────────┘
```

### Component 1: Audio Capture Agent (ACA)

The ACA intercepts real-time audio from the phone call. This is similar to the `streaming` or `fork` commands from Call Control (Lesson 61) — raw audio is extracted from the RTP stream and fed into the processing pipeline.

The ACA handles:
- **Continuous audio streaming**: sending audio chunks (typically 20ms frames) to the STT engine
- **Voice Activity Detection (VAD)**: distinguishing speech from silence/noise
- **Barge-in detection**: recognizing when the caller starts speaking while the AI is talking (interruption)
- **Endpointing**: detecting when the caller has finished their utterance

VAD and endpointing are critical. If endpointing is too aggressive, it cuts off the caller mid-sentence. If it's too conservative, there's an awkward pause before the AI responds.

🔧 **NOC Tip:** "The AI keeps cutting me off" = endpointing is too aggressive. "The AI takes forever to respond" could be slow endpointing (waiting too long to decide the caller is done) OR slow LLM inference. Check the pipeline latency breakdown in Grafana to distinguish.

### Component 2: Speech-to-Text (STT)

The STT engine converts audio to text in real-time. Telnyx uses engines like Whisper or Deepgram, selected based on accuracy, latency, and language requirements.

STT operates in **streaming mode** — it receives audio continuously and produces partial transcriptions that are refined as more audio arrives. This is different from batch STT (transcribing a recorded file) and much more latency-sensitive.

**Factors affecting STT accuracy:**
- **Audio quality**: the codec matters. G.711 at 8kHz provides less information than Opus at 16kHz. Packet loss causes audio artifacts that confuse the model
- **Background noise**: office noise, car noise, speaker phone echo
- **Accents and dialects**: models trained primarily on standard American English may struggle with strong accents
- **Domain vocabulary**: medical, legal, or technical terminology may need custom models

### Component 3: LLM Manager

The LLM Manager receives transcribed text and routes it to the appropriate Language Model. This is the "brain" of the Voice AI assistant.

The LLM Manager handles:
- **Prompt construction**: combining the system prompt (assistant personality, instructions) with conversation history and the new utterance
- **Model selection**: choosing the optimal model based on the assistant's configuration (GPT-4, Claude, Llama, etc.)
- **Tool/function calling**: the LLM may need to call external APIs (check order status, look up account, schedule appointment)
- **Streaming response**: the LLM generates tokens one by one; as soon as a complete sentence is available, it's sent to TTS (reducing perceived latency)

**The streaming optimization** is crucial. Instead of waiting for the LLM to generate the entire response before starting TTS, the pipeline streams: the first sentence goes to TTS while the LLM is still generating the second sentence. This parallelism can cut perceived response time by 50%+.

🔧 **NOC Tip:** If Voice AI latency suddenly increases, check which component is slow. Grafana dashboards should show per-component latency: STT p99, LLM p99 (including token generation time), and TTS p99. A spike in LLM latency might indicate GPU saturation, model loading issues, or rate limiting from an external LLM provider.

### Component 4: Text-to-Speech (TTS)

The TTS engine converts the LLM's text response back to audio. Modern TTS engines produce remarkably natural speech, with options for:
- **Voice selection**: different voices, genders, accents
- **Voice cloning**: custom voices trained on audio samples
- **Prosody control**: speed, pitch, emphasis
- **SSML support**: fine-grained control over pronunciation and pausing

TTS also operates in streaming mode — as text arrives from the LLM, audio is synthesized and fed into the RTP stream incrementally.

### Component 5: Audio Injection

The synthesized audio is transcoded to match the call's negotiated codec (typically G.711 for PSTN calls) and injected into the RTP stream. This is the same mechanism used by `speak` and `play_audio` in Call Control (Lesson 61).

## Barge-In: The Interruption Problem

Natural conversation involves interruption. A caller might say "Actually, never mind" while the AI is mid-sentence. Handling this requires:

1. **ACA detects speech** while TTS audio is playing
2. **TTS playback stops** immediately
3. **The new utterance** is sent to STT
4. **LLM receives** the interruption context (the user interrupted, here's what they said)

This is technically challenging because the ACA must distinguish between:
- The caller actually speaking (barge-in → stop and listen)
- Echo of the AI's own voice bouncing back through the phone (not barge-in → keep playing)

Acoustic echo cancellation on the ACA side is essential to avoid false barge-in triggers.

## The Latency Budget

For a natural-feeling conversation, the total round-trip time from end of caller speech to start of AI response should be under 2 seconds. Here's a typical breakdown:

| Component | Typical Latency | Notes |
|-----------|----------------|-------|
| Endpointing | 300-500ms | Waiting to confirm caller is done |
| STT | 200-400ms | Streaming recognition finalization |
| LLM (first token) | 200-800ms | Depends on model and load |
| TTS (first audio) | 100-300ms | Streaming synthesis |
| **Total** | **800-2000ms** | Target: <1500ms |

Every millisecond counts. Transcoding adds latency. Network hops add latency. Queuing under load adds latency.

## Failure Modes and Their Impact

**STT Failure:** The AI doesn't understand what the caller said. It might ask "Could you repeat that?" or respond to a hallucinated transcription. Impact: frustrating but recoverable.

**LLM Failure/Timeout:** The most impactful failure. The caller speaks, there's silence (no response), and eventually a timeout. The call may fall back to a human agent or play an error message.

**TTS Failure:** The LLM generated a response but it can't be spoken. Some systems fall back to a default TTS engine; others play silence.

**ACA Failure:** Audio capture stops. The AI goes deaf. The caller speaks but nothing happens. The call is effectively broken.

🔧 **NOC Tip:** When Voice AI calls "go silent," check if the silence is before or after the caller speaks. If the AI never responds to speech → check STT and LLM. If the AI responds but the caller can't hear it → check TTS and audio injection. If nothing works → check ACA health and the underlying call's media path.

## Troubleshooting Scenario: "AI Assistant Has 5-Second Response Delays"

A customer's Voice AI assistant works but responses are unacceptably slow.

**Investigation:**
1. Grafana: Voice AI pipeline latency dashboard → overall p95 = 4.8 seconds
2. Breakdown: STT = 300ms ✓, LLM = 3.5 seconds ✗, TTS = 200ms ✓
3. LLM latency is the bottleneck. Check LLM Manager → requests are routing to a specific model that's under heavy load
4. GPU utilization on the inference cluster: 98% — the model is queueing requests
5. Resolution: scale up GPU instances for that model, or shift traffic to a less loaded cluster

---

**Key Takeaways:**
1. Voice AI is a four-stage pipeline: Audio Capture → STT → LLM → TTS, with a total latency budget of ~1.5 seconds
2. Streaming at every stage (STT, LLM token generation, TTS) is essential to minimize perceived latency
3. Barge-in (caller interrupting the AI) requires echo cancellation to avoid false triggers
4. Each pipeline component can fail independently — identify which stage is failing using per-component latency dashboards
5. LLM inference latency is typically the largest and most variable component
6. Audio quality from the phone call directly impacts STT accuracy — G.711 narrowband is a constraint

**Next: Lesson 67 — Voice AI Troubleshooting: Latency, Quality, and Pipeline Failures**
