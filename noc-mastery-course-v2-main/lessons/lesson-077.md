# Lesson 77: Voice AI Troubleshooting — Latency, Quality, and Pipeline Failures

**Module 2 | Section 2.5 — Voice AI**
**⏱ ~6 min read | Prerequisites: Lesson 66**

---

## Debugging a Multi-Stage Pipeline

Voice AI troubleshooting requires thinking about each pipeline stage independently, then understanding how failures cascade. A problem at one stage doesn't always look like a problem at that stage — it manifests downstream as something else. Slow STT doesn't look like "slow STT" to the caller; it looks like "the AI takes forever to respond."

## Latency: The Primary Enemy

### Breaking Down Response Time

When a customer says "the AI is slow," your first task is to decompose the latency. The Grafana Voice AI dashboard should show per-component timings:

- **Endpointing delay**: time between caller stops speaking and the system decides they're done
- **STT finalization**: time from end of speech to final transcript
- **LLM time-to-first-token (TTFT)**: time from receiving transcript to first output token
- **LLM total generation time**: time to generate the complete response
- **TTS time-to-first-audio**: time from receiving text to first audio chunk

Each component has different root causes for slowness.

### Endpointing Latency

The endpointer waits for silence to confirm the caller is done. Default silence thresholds are typically 500-800ms. If callers frequently pause mid-thought, the endpointer triggers prematurely (cutting them off). If the threshold is too high, every interaction has unnecessary delay.

🔧 **NOC Tip:** "The AI keeps interrupting me" and "the AI is slow to respond" can be caused by the same parameter — endpointing sensitivity. Customers may need to tune their assistant's endpointing threshold for their use case.

### STT Latency

Streaming STT typically adds 200-400ms after the final audio. Factors that increase STT latency:
- Model size (larger models are more accurate but slower)
- Audio quality (noisy audio requires more processing)
- Long utterances (more context to process)
- Service load (shared STT infrastructure under pressure)

### LLM Latency

Usually the largest variable. LLM time-to-first-token depends on:
- **Model choice**: GPT-4 is slower than GPT-3.5; larger models take longer
- **Prompt length**: more conversation history = more tokens to process = slower
- **GPU availability**: if GPUs are saturated, requests queue
- **Tool/function calls**: if the LLM decides to call an external API (check order, lookup account), that API's latency adds directly to response time

🔧 **NOC Tip:** Sudden latency spikes across all Voice AI customers usually indicate GPU infrastructure issues. Check the inference cluster dashboard: GPU utilization, request queue depth, and error rates. If only one customer is affected, it's likely their specific LLM configuration (long system prompts, external tool calls, complex instructions).

### TTS Latency

Modern streaming TTS engines are fast (100-300ms to first audio). Latency increases with:
- Custom/cloned voices (more complex synthesis)
- Long text segments (if streaming isn't working correctly)
- Service overload

## STT Accuracy Issues

When the AI responds incorrectly — not slowly, but wrong — the problem is often in STT transcription.

**Debugging approach:**
1. Find the call in Graylog/logs
2. Look at the STT transcription: what did it think the caller said?
3. If the transcription is wrong, it's an STT accuracy problem
4. If the transcription is correct but the response is wrong, it's an LLM problem

**Common STT accuracy issues:**

**Background noise**: Callers in noisy environments (cars, restaurants, construction). The STT engine hears noise as speech or misrecognizes words.

**Accents**: Heavy accents, non-native speakers, regional dialects. The STT model may not have enough training data for specific accents.

**Domain vocabulary**: Medical terms, product names, technical jargon. "Telnyx" might be transcribed as "tell next" or "telnet."

**Codec impact**: G.711 μ-law at 8kHz captures 300-3400Hz. Some speech sounds (sibilants like "s," "sh") have energy above 3400Hz that's lost, making them harder for STT to distinguish.

🔧 **NOC Tip:** If a customer says "the AI doesn't understand me," ask if the issue is consistent (always misunderstands) or intermittent. Consistent = likely accent/vocabulary issue needing STT configuration. Intermittent = likely audio quality issue (packet loss, noise).

## Pipeline Failures

### ACA (Audio Capture) Failures

If the Audio Capture Agent dies or disconnects from the call, the pipeline goes deaf. The call continues (SIP-level media still flows) but the AI stops responding.

**Symptoms:** Call is active, caller can hear hold music or last TTS audio, but AI stops responding to speech.

**Diagnosis:** Check ACA pod health in Kubernetes. Is it OOMKilled (Lesson 92)? CrashLoopBackOff?

### STT Service Outage

If the STT service is down, all new utterances produce empty transcriptions. The LLM receives nothing and can't respond.

**Symptoms:** AI stops responding to all callers simultaneously.

**Diagnosis:** Grafana STT dashboard: error rate, latency p99, request count. If requests are failing, check STT pod health.

### LLM Timeout

If the LLM doesn't respond within the timeout window, the Voice AI must handle it gracefully — typically by playing a fallback message ("I'm sorry, I'm having trouble right now") or transferring to a human.

**Symptoms:** Caller speaks, long silence, then a fallback message.

**Diagnosis:** Grafana LLM dashboard: timeout rate, error rate, queue depth.

### TTS Failure

TTS failure means the LLM generated a response but it can't be converted to audio.

**Symptoms:** Call is active, AI "understood" the caller (logs show correct LLM response), but caller hears nothing.

**Diagnosis:** Grafana TTS dashboard: error rate, synthesis latency. Check if specific voices are failing (cloned voice model issue) or all voices (service issue).

## Monitoring Voice AI Health

Key Grafana dashboards for Voice AI:

1. **Pipeline Latency**: end-to-end and per-component p50, p95, p99
2. **STT Accuracy**: word error rate if available, or proxy metrics (retry rate, empty transcription rate)
3. **LLM Performance**: TTFT, tokens/second, error rate, queue depth
4. **TTS Performance**: time-to-first-audio, synthesis rate, error rate
5. **Call Quality**: underlying call's RTP metrics (packet loss, jitter) — because garbage audio in = garbage transcription out

## Troubleshooting Scenario: "AI Works Fine in Testing But Fails in Production"

A customer's Voice AI assistant works perfectly in testing but performs poorly with real callers.

**Investigation:**
1. Testing used high-quality microphones on quiet lines → production callers use mobile phones in noisy environments
2. STT accuracy drops from 95% to 70% with noisy mobile audio
3. G.711 codec loses high-frequency speech information that helps STT
4. Packet loss on mobile networks causes audio dropouts that break words

**Resolution:** Recommended the customer enable noise suppression pre-processing on the audio stream and adjust the STT model to one optimized for telephony audio (8kHz narrowband). Also suggested adding confirmation prompts for critical information ("I heard your order number is 12345, is that correct?").

---

**Key Takeaways:**
1. Always decompose Voice AI latency into per-component metrics before investigating
2. LLM inference time is the largest and most variable latency component — GPU saturation is a common cause
3. STT accuracy depends heavily on audio quality — G.711 narrowband + noisy callers = poor recognition
4. Pipeline failures at each stage have distinct symptoms: ACA failure → AI deaf; STT failure → AI unresponsive; TTS failure → AI silent
5. Testing environments rarely match production audio quality — always test with realistic telephony audio
6. Monitor the underlying call quality (RTP metrics) as a leading indicator of Voice AI performance

**Next: Lesson 68 — SMS/MMS Architecture: How Messages Flow**
