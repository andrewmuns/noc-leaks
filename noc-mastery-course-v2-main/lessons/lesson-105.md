# Lesson 105: Telnyx Compute — Inference, LLM Library, and Embeddings

**Module 2 | Section 2.16 — Compute**
**⏱ ~7min read | Prerequisites: Lessons 82-84 (Cloud Fundamentals, Virtualization, Container Orchestration)**

---

## Introduction

Large Language Models (LLMs) and AI inference are now essential infrastructure components. Telnyx Compute provides **GPU-powered inference APIs** with an OpenAI-compatible interface, a model catalog, and embedding services. Whether customers are building AI voice agents, summarizing calls, or implementing semantic search, the Inference API is the underlying engine. This lesson covers the architecture, pricing model, and operational considerations for NOC engineers.

---

## Telnyx Inference API Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Telnyx Compute Platform                     │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   API Gateway (Global)                   │   │
│   │              OpenAI-compatible endpoints                 │   │
│   └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│   ┌─────────────────────────▼───────────────────────────────┐   │
│   │              Model Router & Load Balancer                │   │
│   │   - Route to appropriate model backend                   │   │
│   │   - Health checks                                        │   │
│   │   - Rate limiting                                        │   │
│   └─────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│           ┌─────────────────┼─────────────────┐                  │
│           │                 │                 │                  │
│    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐         │
│    │ Model Pods  │   │ Model Pods  │   │ Model Pods  │         │
│    │  (Llama)    │   │  (Mistral)  │   │  (Custom)   │         │
│    │                                             │              │
│    │ ┌─────────┐ ┌─────────┐ ┌─────────┐       │              │
│    │ │ GPU A10 │ │ GPU A10 │ │ GPU A10 │ ...   │              │
│    │ │ (24GB)  │ │ (24GB)  │ │ (24GB)  │       │              │
│    │ └─────────┘ └─────────┘ └─────────┘       │              │
│    └───────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### GPU Infrastructure

```
Hardware tiers:

Tier 1: NVIDIA A10 (24GB VRAM)
  - Workhorses for small-to-medium models
  - Cost-effective inference
  - Good for 7B-13B parameter models

Tier 2: NVIDIA A100 (40GB/80GB VRAM)  
  - High-performance inference
  - Large context windows (32k-128k tokens)
  - Good for 30B-70B parameter models

Tier 3: NVIDIA H100 (80GB VRAM)
  - Latest generation
  - Maximum throughput for large models
  - Production inference at scale
```

---

## OpenAI-Compatible API

Telnyx Inference uses the same API structure as OpenAI, making migration seamless:

### Chat Completions

```bash
curl https://api.telnyx.com/v2/ai/chat/completions \
  -H "Authorization: Bearer YOUR_TELNYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Summarize this call transcript in 3 sentences."}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Response

```json
{
  "id": "chatcmpl_abc123",
  "object": "chat.completion",
  "created": 1708708200,
  "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "The customer called about a billing discrepancy..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 245,
    "completion_tokens": 67,
    "total_tokens": 312
  }
}
```

🔧 **NOC Tip:** The `finish_reason` field tells you why generation stopped:
- `stop` — Model completed naturally (end of response)
- `length` — Hit `max_tokens` limit
- `content_filter` — Content was blocked by safety filters
If you see lots of `length` reasons, customers may need higher token limits or their prompts are truncated.

---

## LLM Library — Model Catalog

Telnyx offers a variety of open-source models:

### Text Generation Models

| Model | Parameters | Best For | Context |
|-------|-----------|----------|---------|
| Llama 3.1 | 8B | Fast inference, simple tasks | 128k |
| Llama 3.1 | 70B | General purpose, complex reasoning | 128k |
| Llama 3.1 | 405B | Maximum capability | 128k |
| Mistral Large | 123B | Multilingual, code | 128k |
| Mixtral 8x7B | 47B | Efficient MoE architecture | 32k |
| CodeLlama | 70B | Software development | 16k |

### Specialized Models

| Model | Use Case |
|-------|----------|
| `meta-llama/Meta-Llama-3.1-70B-Instruct` | Chat, Q&A |
| `mistralai/Mistral-7B-Instruct-v0.3` | Fast chat, simple tasks |
| `NousResearch/Hermes-2-Pro-Llama-3-8B` | Tool calling, function calling |

### Model Selection

```
Selection criteria:

Latency-sensitive (real-time voice agent):
  → Llama 8B or Mistral 7B (first token < 100ms)

Complex reasoning (analysis, summaries):
  → Llama 70B or Mistral Large (better comprehension)

Code generation:
  → CodeLlama or specialized coding models

Cost-conscious (batch processing):
  → Mixtral 8x7B (efficient MoE, good performance/cost)
```

---

## Embeddings API

Embeddings convert text into vectors (arrays of numbers) for semantic search and similarity comparisons:

```
Text → Embedding Model → Vector (e.g., 768 dimensions)

"dog"      → [0.12, -0.05, 0.89, ...]
"puppy"    → [0.11, -0.04, 0.88, ...]  ← Similar vectors!
"car"      → [0.95, 0.22, -0.34, ...]  ← Different vector
```

### Using the Embeddings API

```bash
curl https://api.telnyx.com/v2/ai/embeddings \
  -H "Authorization: Bearer YOUR_TELNYX_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "The quick brown fox jumps over the lazy dog",
    "model": "text-embedding-3-large"
  }'
```

### Embeddings for Semantic Search

```python
import numpy as np

# Imagine these are vectors from the API
call_transcript_embedding = [0.12, -0.05, 0.89, ...]  # customer complaint
knowledge_base_article_1 = [0.11, -0.04, 0.88, ...]  # similar topic
knowledge_base_article_2 = [0.95, 0.22, -0.34, ...]  # different topic

# Cosine similarity: 1.0 = identical, 0.0 = orthogonal
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Find most relevant article
sim_1 = cosine_similarity(call_transcript_embedding, article_1)  # 0.94
sim_2 = cosine_similarity(call_transcript_embedding, article_2)  # 0.23

# Article 1 is the answer!
```

### Embedding Models

| Model | Dimensions | Use Case |
|-------|------------|----------|
| `text-embedding-3-small` | 1536 | Fast, cost-effective |
| `text-embedding-3-large` | 3072 | High accuracy, complex matching |

---

## Token-Based Pricing

### What Is a Token?

```
Tokens are pieces of text that the model processes:

"ChatGPT is great!" → ["Chat", "GP", "T", " is", " great", "!"]
                        ≈ 6 tokens

Rough conversion:
  1 token ≈ 4 characters (English)
  100 tokens ≈ 75 words
  
Example pricing (varies by model):
  Input:  $0.10 per 1M tokens
  Output: $0.30 per 1M tokens
```

### Cost Estimation

```
Scenario: Summarizing 1000 customer support calls

Per call:
  Input:  2000 tokens (transcript)
  Output: 150 tokens (summary)
  
Total for 1000 calls:
  Input:  2,000,000 tokens × $0.10/M = $0.20
  Output:   150,000 tokens × $0.30/M = $0.045
  
Total: ~$0.245 per batch of 1000
```

🔧 **NOC Tip:** Help customers right-size their `max_tokens`. Setting it to 4096 for a task that only needs 200 tokens wastes 90% of the capacity. Also, input tokens often dominate costs — passing the entire conversation history when you only need the last turn adds up quickly. Recommend context window management strategies.

---

## Monitoring Inference Latency and Errors

### Key Metrics

```
Time to First Token (TTFT):
  - Time from request to first response byte
  - Target: < 200ms for interactive use
  - Affected by: Model size, GPU load, batching

Time Per Output Token (TPOT):
  - Time to generate each subsequent token
  - Target: < 50ms per token
  - Streaming: ~20 tokens/second is good

Total Latency:
  - End-to-end time for complete response
  - Depends on output length

Error Rates:
  - 429: Rate limit exceeded
  - 503: Model overloaded, try again
  - 500: Internal error, escalate
```

### API for Usage Monitoring

```bash
# Get usage statistics
curl https://api.telnyx.com/v2/ai/analytics/usage \
  -H "Authorization: Bearer YOUR_TELNYX_KEY" \
  -d '{
    "start_date": "2026-02-01",
    "end_date": "2026-02-23",
    "granularity": "day"
  }'
```

```json
{
  "data": {
    "total_requests": 45000,
    "total_tokens": 12500000,
    "average_latency_ms": 850,
    "errors": {
      "rate_limited": 23,
      "model_unavailable": 5,
      "timeout": 12
    },
    "cost": {
      "input_tokens_cost": "$0.45",
      "output_tokens_cost": "$0.89",
      "total": "$1.34"
    }
  }
}
```

---

## Real-World NOC Scenario

**Scenario:** Customer's AI voice assistant (using Telnyx Inference) is experiencing pauses during conversations — users say "it feels like the AI is thinking too long."

**Investigation:**

1. Check latency metrics: TTFT is averaging 400ms (should be < 200ms)
2. Check model size: Customer is using Llama 405B for simple Q&A
3. Model oversized for the task — 70B would be sufficient and 3x faster
4. Also check if customer is sending full conversation history vs just the last turn
5. Context truncation strategy could reduce input tokens by 80%

```bash
# Recommend model change in customer integration
curl https://api.telnyx.com/v2/ai/chat/completions \
  -H "Authorization: Bearer $KEY" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "messages": messages[-3:],  # Only last 3 turns, not full history
    "temperature": 0.7,
    "max_tokens": 256  # Right-sized for voice responses
  }'
```

**Result:** TTFT dropped from 400ms to 120ms. User experience improved significantly.

---

## Key Takeaways

1. **Telnyx Inference is OpenAI-compatible** — drop-in replacement, no code changes
2. **Model size matters** — 8B for speed, 70B+ for reasoning, match model to task
3. **Tokens are the pricing unit** — input + output, roughly 4 chars per token
4. **Embeddings enable semantic search** — vectors represent meaning, not just keywords
5. **TTFT and TPOT are the latency metrics** — < 200ms TTFT for interactive use
6. **Right-size max_tokens and context** — waste costs money and increases latency
7. **GPU infrastructure scales behind the API** — focus on latency, not managing hardware

---

**Next: Lesson 196 — Telnyx Storage: Object Storage Deep Dive**
