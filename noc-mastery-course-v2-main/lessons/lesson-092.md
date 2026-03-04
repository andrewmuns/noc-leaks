# Lesson 92: AI/Inference — LLM Serving and Model Routing
**Module 2 | Section 2.12 — Storage/AI**
**⏱ ~6 min read | Prerequisites: Lesson 18**

---

## Telnyx as an AI Infrastructure Provider

Telnyx doesn't just use AI internally (Voice AI, Lesson 66-67) — it offers AI inference as a product. Customers can access large language models, generate embeddings, and run AI workloads through Telnyx's API. This is powered by GPU infrastructure in Telnyx's data centers, making it a direct competitor to services like OpenAI's API and AWS Bedrock.

For NOC engineers, AI inference workloads present unique challenges: GPU hardware failures, model loading times, memory management, and the fundamentally different performance characteristics of GPU-bound vs. CPU-bound workloads.

## How LLM Inference Works

Understanding the basics of LLM inference helps you diagnose performance issues:

### The Inference Pipeline

1. **Request arrives** — An API request containing a prompt (and model selection) hits Telnyx's API gateway
2. **Tokenization** — The text prompt is converted to tokens (subword units). "Hello, how are you?" becomes approximately 5-6 tokens.
3. **Prefill phase** — The model processes all input tokens in parallel. This is compute-intensive but parallelizable across the GPU.
4. **Decode phase** — The model generates output tokens one at a time, each depending on all previous tokens. This is memory-bandwidth-bound and inherently sequential.
5. **Detokenization** — Output tokens are converted back to text
6. **Response** — The generated text is returned to the caller

### Why GPUs, Not CPUs

LLMs are massive matrix multiplication machines. A model like Llama 2 70B has 70 billion parameters — each inference requires multiplying input vectors against these parameter matrices. GPUs excel at parallel matrix operations: a modern GPU has thousands of cores that can perform matrix operations simultaneously, achieving throughputs that would require hundreds of CPUs.

But GPU memory is the real constraint. The model parameters must be loaded into GPU memory (VRAM) to perform inference. A 70B parameter model at 16-bit precision needs ~140 GB of VRAM. A single GPU has 40-80 GB of VRAM, so large models are split across multiple GPUs (**tensor parallelism**).

🔧 **NOC Tip:** GPU memory (VRAM) errors are the #1 hardware issue for inference workloads. VRAM errors manifest as garbage output, mysterious crashes, or extremely slow inference. These are analogous to RAM bit-flips but more impactful because every inference touches GPU memory. Check GPU health monitoring dashboards for ECC error counts.

## The OpenAI-Compatible API

Telnyx's inference API follows the **OpenAI API standard** — the same request/response format used by OpenAI's GPT models. This means customers can switch from OpenAI to Telnyx by changing the base URL:

```
# OpenAI
POST https://api.openai.com/v1/chat/completions

# Telnyx
POST https://api.telnyx.com/v1/chat/completions
```

Same request body, same response format. This compatibility dramatically reduces migration friction and lets customers use existing libraries and tools.

### Streaming Responses

For interactive applications (chatbots, Voice AI), waiting for the complete response adds unacceptable latency. **Streaming** returns tokens as they're generated using Server-Sent Events (SSE):

```
data: {"choices": [{"delta": {"content": "Hello"}}]}
data: {"choices": [{"delta": {"content": " there"}}]}
data: {"choices": [{"delta": {"content": "!"}}]}
data: [DONE]
```

The first token arrives quickly (after the prefill phase), and subsequent tokens stream at the model's decode speed. This is critical for Voice AI (Lesson 66) — the TTS pipeline can start synthesizing speech as soon as the first few words are generated, reducing perceived latency.

## Model Routing

Not all requests should go to the same GPU. Telnyx's inference platform includes a **model router** that directs requests to the optimal GPU:

### Routing Considerations

- **Model availability** — Is the requested model loaded on any GPU? Model loading (from storage into VRAM) takes minutes for large models, so models are pre-loaded on dedicated GPUs.
- **GPU utilization** — Route to the least-loaded GPU running the requested model to minimize queuing delay
- **Batch optimization** — Group requests for the same model to improve GPU utilization (batched inference is more efficient than individual requests)
- **Geographic affinity** — Route to GPUs in the same region as the caller to minimize network latency
- **GPU health** — Avoid routing to GPUs showing errors or degraded performance

### Cold Start Problem

When a model isn't currently loaded on any GPU, it must be loaded from storage. This **cold start** can take 30-120 seconds for large models. The model router tries to keep popular models always loaded, but less popular models may experience cold starts on first request.

🔧 **NOC Tip:** If a customer reports "first request to model X takes 2 minutes but subsequent requests are fast," it's a cold start. Check whether the model was recently loaded or evicted. Frequently accessed models should be pinned to avoid cold starts.

## Embedding Generation

Beyond text generation, Telnyx's inference platform supports **embedding generation** — converting text into high-dimensional vectors for semantic search:

- Input text is processed by an embedding model (smaller and faster than generative models)
- The output is a vector of 768-4096 floating-point numbers representing the text's meaning
- These vectors can be stored and compared using cosine similarity for semantic search
- Use cases: searching call transcriptions, finding similar support tickets, semantic routing

Embedding requests are simpler than generative requests — they don't have a decode phase (no token-by-token generation), making them faster and more predictable in latency.

## Rate Limiting and Billing

AI inference is expensive — GPU time costs significantly more than CPU time. Rate limiting and billing are crucial:

### Token-Based Billing
Customers are billed per token (input + output). Longer prompts and longer responses cost more. Token counting uses the same tokenizer as the model.

### Rate Limits
- **Requests per minute (RPM)** — Maximum API calls per minute
- **Tokens per minute (TPM)** — Maximum tokens processed per minute
- **Concurrent requests** — Maximum simultaneous in-flight requests

When rate limits are hit, the API returns `429 Too Many Requests`. Customers should implement retry logic with exponential backoff.

## Real-World Troubleshooting Scenario

**Scenario:** Inference API latency spikes from 500ms p50 to 5 seconds p50 during business hours.

**Investigation:**
1. **Check GPU utilization** — Are GPUs at maximum capacity? High utilization causes request queuing.
2. **Check request volume** — Has traffic increased? A new customer onboarding or traffic spike can saturate capacity.
3. **Check batch sizes** — Large batches of concurrent requests can starve other requests of GPU time.
4. **Check model distribution** — Are requests concentrated on one model while GPUs running other models are idle?
5. **Check for GPU hardware issues** — A failed GPU reduces capacity, causing remaining GPUs to be overloaded.

**Resolution:** If capacity-related, scale GPU allocation (add more GPUs for the popular model). If traffic-spike-related, implement request queuing with graceful degradation. If hardware-related, replace the failed GPU and redistribute model loads.

---

**Key Takeaways:**
1. LLM inference has two phases: prefill (parallel, compute-bound) and decode (sequential, memory-bandwidth-bound) — they have different performance characteristics
2. GPU memory (VRAM) is the primary constraint — large models require multiple GPUs via tensor parallelism
3. The OpenAI-compatible API makes migration frictionless, and streaming responses reduce perceived latency for interactive applications
4. Model routing optimizes for availability, GPU utilization, geographic affinity, and GPU health
5. Cold starts (model loading into VRAM) cause initial request delays of 30-120 seconds for unloaded models

**Next: Lesson 83 — Enterprise Integration — Teams and Zoom**
