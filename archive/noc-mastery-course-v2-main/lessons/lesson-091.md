# Lesson 91: Telnyx Storage — S3-Compatible Object Storage
**Module 2 | Section 2.12 — Storage/AI**
**⏱ ~5 min read | Prerequisites: Lesson 18**

---

## Why a Telecom Company Needs Object Storage

At first glance, storage seems unrelated to telecommunications. But consider what Telnyx's products generate: call recordings (potentially hours of audio per day per customer), fax documents (PDFs from Lesson 77's T.38 pipeline), voicemail messages, transcription files, and media assets for TTS and playback. All of this data needs to be stored, retrieved, and managed — reliably, at scale, and at low cost.

Rather than forcing customers to manage their own storage infrastructure or rely on third-party services like AWS S3, Telnyx provides its own S3-compatible object storage. This tight integration means call recordings can be stored automatically, accessed via the same API credentials, and kept within Telnyx's network for performance and privacy.

## Object Storage Fundamentals

Object storage is conceptually simple: you store **objects** (files) in **buckets** (containers). Each object has:

- **Key** — The object's path/name (e.g., `recordings/2024/01/15/call-abc123.wav`)
- **Data** — The actual file content
- **Metadata** — Key-value pairs describing the object (content type, creation time, custom metadata)

Unlike file systems (hierarchical directories) or block storage (raw disk volumes), object storage is flat. The "folders" you see in keys like `recordings/2024/01/` are just naming conventions — there's no actual directory structure.

### The S3 API Standard

Amazon S3 defined the de facto API standard for object storage. Telnyx's storage is **S3-compatible**, meaning any tool, library, or application that works with AWS S3 also works with Telnyx Storage. Core operations:

- **PUT** — Upload an object
- **GET** — Download an object
- **DELETE** — Remove an object
- **LIST** — List objects in a bucket (with prefix filtering)
- **HEAD** — Get object metadata without downloading the data
- **Multipart Upload** — Upload large files in chunks (essential for large recordings)

🔧 **NOC Tip:** When customers report "can't access my recordings," first verify the object exists with a LIST or HEAD request. Then check permissions — S3 access control is a common stumbling block. The object might exist but the customer's credentials might not have permission to read it.

## Multi-Region Storage and Replication

Telnyx operates data centers across multiple regions. Storage can be configured for:

**Single-region** — Objects stored in one data center. Lower cost, but vulnerable to regional outages.

**Multi-region replication** — Objects automatically replicated across data centers. Higher durability and availability, but increased cost and slight write latency (replication takes time).

For telecom workloads, the choice depends on the data type:
- **Call recordings** — Often single-region is sufficient (recordings are archival, not latency-sensitive)
- **Active media files** — Used for TTS prompts or hold music, may benefit from multi-region for low-latency access from any Telnyx POP

## Access Control

Storage security uses the same model as AWS S3:

### IAM Policies
Identity-based policies attached to users/roles that define what they can do. Example: "This API key can read objects in bucket X but not write or delete."

### Bucket Policies
Resource-based policies attached to buckets that define who can access them. Example: "Only requests from these IP ranges can access this bucket."

### Presigned URLs
Temporary, pre-authenticated URLs that grant time-limited access to specific objects without requiring API credentials. Essential for sharing recordings with end users — generate a presigned URL that expires in 1 hour and share it.

```
https://storage.telnyx.com/bucket/recording.wav?X-Amz-Expires=3600&X-Amz-Signature=...
```

🔧 **NOC Tip:** If a customer reports "presigned URL not working," check the expiration. Presigned URLs have a validity window — if the URL was generated hours ago and has a short TTL, it's expired. Also check clock skew — if the server generating the URL has an inaccurate clock, the signature validation fails.

## Integration with Telnyx Products

The real value of Telnyx Storage is its native integration with other products:

### Call Recordings
When a customer enables call recording (via Call Control or SIP trunk settings), the recordings are automatically stored in Telnyx Storage. The recording URL in the webhook payload points directly to the stored object. No configuration needed — it just works.

### Fax Storage
Received faxes (Lesson 77) are converted to PDF and stored in Telnyx Storage. The fax webhook includes the storage URL.

### Media Playback
Audio files for IVR prompts, hold music, and TTS output can be stored in Telnyx Storage and referenced by URL in Call Control commands like `play_audio`.

### AI/Inference
Training data, model artifacts, and inference results can be stored and accessed through the same storage infrastructure.

## Storage Troubleshooting

Common storage-related issues NOC engineers encounter:

### Upload Failures
- **413 Entity Too Large** — The object exceeds the maximum size for a single PUT. Use multipart upload for large files.
- **403 Forbidden** — Incorrect or expired credentials, or insufficient permissions.
- **503 Service Unavailable** — Storage service is overloaded or undergoing maintenance.

### Download Failures
- **404 Not Found** — The object doesn't exist (check the key/path for typos) or was deleted.
- **403 Forbidden** — Access denied (check IAM policies and bucket policies).
- **Slow downloads** — Check the region. If the storage is in US-East but the client is in Asia-Pacific, latency will be high.

### Recording-Specific Issues
- **Recording missing** — Check if recording was enabled on the connection/call. Check if the call actually connected (no recording for unanswered calls).
- **Recording truncated** — Check if the storage reached a size limit or if the recording was stopped prematurely.
- **Recording format** — Recordings are typically in WAV or MP3. Check if the customer's application expects a specific format.

## Real-World Troubleshooting Scenario

**Scenario:** A customer reports that call recordings from the past 2 hours are inaccessible — the URLs in their webhooks return 404 errors.

**Investigation:**
1. **Check storage health** — Is the storage service operational? Check Grafana dashboards for storage error rates.
2. **Verify the recording pipeline** — Are recordings being generated and uploaded? Check the recording service logs.
3. **Check the specific objects** — Do a LIST on the customer's recording bucket. Are recent objects present?
4. **Check retention policies** — Did a lifecycle policy delete objects prematurely?
5. **Check the recording service** — Is the service that uploads recordings running? Check pod health in Kubernetes.

**Resolution:** If the recording upload service has pods in CrashLoopBackOff, the recordings are being generated but not uploaded. Fixing the service restores recording availability. Recordings from the outage period may be recoverable from local buffers on the media servers.

---

**Key Takeaways:**
1. Telnyx Storage provides S3-compatible object storage tightly integrated with call recordings, fax, and media playback
2. Presigned URLs provide secure, temporary access to objects without sharing API credentials — check expiration and clock skew for failures
3. Multi-region replication improves durability but adds cost and write latency
4. Storage issues often manifest as "recordings missing" — trace the pipeline from recording service to storage upload to verify each step
5. Access control follows the S3 model: IAM policies, bucket policies, and presigned URLs

**Next: Lesson 82 — AI/Inference — LLM Serving and Model Routing**
