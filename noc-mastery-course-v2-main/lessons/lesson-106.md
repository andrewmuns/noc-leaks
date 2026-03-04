# Lesson 106: Telnyx Storage — Object Storage Deep Dive

**Module 2 | Section 2.16 — Compute**
**⏱ ~5min read | Prerequisites: Lessons 85-86 (Object Storage, CDN)**

---

## Introduction

Telnyx Storage provides S3-compatible object storage that's tightly integrated with Telnyx products — call recordings, fax documents, AI training data, and more. Using the industry-standard S3 API, customers can store and retrieve files without managing storage infrastructure. This lesson covers the architecture, S3 compatibility, multi-region capabilities, and monitoring considerations for NOC engineers.

---

## S3-Compatible API

### What Is S3 Compatibility?

```
Amazon S3 created the de facto standard for object storage:
  - Buckets contain objects
  - Objects stored by key (path-like string)
  - HTTP/HTTPS operations (PUT, GET, DELETE)
  - REST API with authentication via signatures

S3-compatible means:
  - Same API structure
  - Same authentication (AWS Signature v4)
  - Existing S3 client libraries work without changes
  - Migration from AWS/minio/other S3-compatible services is trivial
```

### Basic Operations

```bash
# Set endpoint and credentials
export AWS_ACCESS_KEY_ID="your-telnyx-access-key"
export AWS_SECRET_ACCESS_KEY="your-telnyx-secret-key"
export AWS_ENDPOINT_URL="https://storage.telnyx.com"

# Create a bucket
aws s3 mb s3://my-call-recordings \
  --endpoint-url=$AWS_ENDPOINT_URL

# Upload a file
aws s3 cp recording.mp3 s3://my-call-recordings/2026/02/23/ \
  --endpoint-url=$AWS_ENDPOINT_URL

# List contents
aws s3 ls s3://my-call-recordings/2026/02/23/ \
  --endpoint-url=$AWS_ENDPOINT_URL

# Download
aws s3 cp s3://my-call-recordings/2026/02/23/recording.mp3 . \
  --endpoint-url=$AWS_ENDPOINT_URL

# Delete
aws s3 rm s3://my-call-recordings/2026/02/23/recording.mp3 \
  --endpoint-url=$AWS_ENDPOINT_URL
```

### REST API Directly

```bash
# PUT object via curl
curl -X PUT \
  https://storage.telnyx.com/my-call-recordings/recording.mp3 \
  -H "Authorization: AWS $ACCESS_KEY:$SIGNATURE" \
  -H "Content-Type: audio/mpeg" \
  -H "x-amz-meta-call-id: call_abc123" \
  --data-binary @recording.mp3
```

---

## Buckets and Objects

### Bucket Naming

```
Rules:
  - 3-63 characters
  - Lowercase letters, numbers, hyphens, periods
  - Must start/end with letter or number
  - DNS-compatible (used in URLs)
  - Globally unique within Telnyx storage

Examples:
  ✓ acme-corp-recordings
  ✓ mycompany.fax.storage
  ✗ MyBucket (uppercase)
  ✗ bucket..name (double period)
```

### Object Keys

```
Objects are stored in a flat namespace — "folders" are just prefixes:

Bucket: my-call-recordings

Objects:
  calls/2026/02/23/call_001.mp3
  calls/2026/02/23/call_002.mp3
  faxes/2026/02/fax_001.pdf
  ai-training/data/dataset_001.jsonl

These aren't directories ─ they're just keys with slashes.
The S3 API can list by prefix to simulate folder browsing.
```

### Object Metadata

```json
{
  "Key": "calls/2026/02/23/call_001.mp3",
  "LastModified": "2026-02-23T10:30:00.000Z",
  "ETag": "\"d41d8cd98f00b204e9800998ecf8427e\"",
  "Size": 2457600,
  "StorageClass": "STANDARD",
  "Metadata": {
    "call-id": "call_abc123",
    "from-number": "+15551234567",
    "to-number": "+15559876543",
    "duration": "3600"
  }
}
```

🔧 **NOC Tip:** Metadata allows you to attach custom context to objects without modifying the file. When debugging storage issues, checking metadata (with `aws s3api head-object`) can provide crucial context about what the file is without downloading it.

---

## Multi-Region Storage

### Available Regions

```
us-east-1     — Ashburn, VA (default)
us-west-1     — San Francisco, CA
eu-west-1     — Amsterdam, NL
asia-east-1   — Singapore, SG
```

### Region Selection

```
Factors:
  - Data locality requirements (GDPR = keep in EU)
  - Latency (store near compute or users)
  - Redundancy goals (cross-region replication)
  - Cost (some regions have different pricing)
```

### Creating a Bucket in a Specific Region

```bash
aws s3 mb s3://eu-customer-data \
  --endpoint-url=https://storage.telnyx.com \
  --region eu-west-1
```

### Cross-Region Replication (CRR)

```
Scenario: Compliance requires backup in different geography

us-east-1 Bucket                    eu-west-1 Bucket
├─→ Object uploaded                    │
│  (production writes)                 │
│                                      │
│  ┌─────────────────────────────────┐ │
└─→│ Cross-Region Replication Rule   │─┼→ Object replicated
   │ - Automatic async replication  │ │  (backup copy)
   │ - Versioning enabled on both   │ │
   └─────────────────────────────────┘ │
```

🔧 **NOC Tip:** When customers need CRR, remind them that versioning must be enabled on the source bucket. Without versioning, the replication system can't track changes to objects. Also, replication is asynchronous — there's a delay (typically seconds to minutes) between source write and replica availability.

---

## CDN Integration

Telnyx Storage integrates with CDN for global content delivery:

```
Without CDN:
  User in Australia ──HTTP──→ Storage us-east-1
  Latency: 200ms+
  Throughput: Limited by trans-pacific link

With CDN:
  User in Australia ──HTTP──→ CDN Edge (Sydney)
                           └─→ Cache hit? Deliver immediately (10ms)
                           └─→ Cache miss? Fetch from origin, cache for next request
```

### Enabling CDN

```bash
# Bucket can be fronted by Telnyx CDN
curl -X PUT \
  https://api.telnyx.com/v2/storage/buckets/my-public-assets \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{
    "cdn_enabled": true,
    "cdn_domain": "assets.acme.com"
  }'
```

### CDN Behavior

```
Cache Headers:
  - Controlled by object metadata
  - Cache-Control: max-age=3600 (1 hour)
  - Cache-Control: no-cache (always fetch fresh)

Invalidation:
  - Manual purge via API
  - Time-based expiration
  - Versioned URLs (recommended for immutable content)

Signed URLs:
  - Time-limited access to private content
  - HMAC signature validates access
  - URL expires after specified time
```

---

## Use Cases

### Call Recordings

```
Flow:
  Voice Call ──→ Telnyx Platform ──→ Record ──→ Storage bucket

Configuration:
  - Bucket: acme-corp-recordings
  - Lifecycle: Archive to cold storage after 90 days
  - Retention: Delete after 7 years (compliance)
  - Access: Presigned URLs for authorized downloads

Naming convention:
  s3://acme-corp-recordings/
    YYYY-MM-DD/
      call-{call_control_id}-{timestamp}.mp3
      call-{call_control_id}-{timestamp}.json (metadata)
```

### Fax Storage

```
Flow:
  Incoming Fax ──→ Telnyx Fax API ──→ Storage ──→ Webhook to customer

Storage path:
  s3://acme-faxes/
    inbound/
      YYYY/MM/DD/
        fax-{fax_id}.pdf
        fax-{fax_id}.json (sender, page count, time)
    outbound/
      YYYY/MM/DD/
        fax-{fax_id}.pdf
```

### AI Training Data

```
For Telnyx Compute / Inference:

Training dataset:
  s3://my-ai-datasets/
    fine-tune-2026-02/
      train.jsonl
      validation.jsonl
      prompts.txt
      README.md

Fine-tuning job references the S3 path directly:
  {
    "training_file": "s3://my-ai-datasets/fine-tune-2026-02/train.jsonl",
    "validation_file": "s3://my-ai-datasets/fine-tune-2026-02/validation.jsonl"
  }
```

---

## Lifecycle Policies

### Automating Data Management

```json
{
  "Rules": [
    {
      "ID": "ArchiveOldRecordings",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "calls/"
      },
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "COLD"
        },
        {
          "Days": 2555,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 3650
      }
    }
  ]
}
```

### Storage Classes

| Class | Use Case | Retrieval | Latency |
|-------|----------|-----------|---------|
| **STANDARD** | Active, frequent access | Immediate | Milliseconds |
| **COLD** | Monthly/quarterly access | ~1-5 minutes | Minutes |
| **GLACIER** | Rare access, compliance | ~1-12 hours | Hours |

🔧 **NOC Tip:** Lifecycle policies are critical for cost management. A customer storing 10TB of call recordings at STANDARD prices multiplies over time. With archiving:
- First 90 days: STANDARD (fast access for disputes)
- 90 days - 7 years: COLD (compliance storage)
- After 7 years: Delete
This can reduce storage costs by 60-80%.

---

## Monitoring Storage Health and Capacity

### Metrics to Watch

```bash
# Get bucket statistics
curl https://api.telnyx.com/v2/storage/buckets/my-bucket/metrics \
  -H "Authorization: Bearer YOUR_KEY"
```

```json
{
  "data": {
    "bucket": "my-bucket",
    "total_objects": 154320,
    "total_size_bytes": 54892734156,
    "size_by_storage_class": {
      "STANDARD": 10485760000,
      "COLD": 31907374156,
      "GLACIER": 12499600000
    },
    "requests_last_24h": {
      "GET": 45000,
      "PUT": 1200,
      "DELETE": 45
    },
    "errors_last_24h": {
      "4xx": 23,
      "5xx": 0
    },
    "cost_last_24h": "$12.34"
  }
}
```

### Alerting Thresholds

```
Capacity:
  Warning: > 80% of purchased capacity
  Critical: > 95% of purchased capacity

Request Errors:
  Warning: > 1% 4xx errors (usually client config issues)
  Critical: Any 5xx errors (platform issue)

Cost:
  Warning: 80% of monthly budget
  Investigation: Unexpected spikes in PUT requests (possible abuse)
```

---

## Real-World NOC Scenario

**Scenario:** Customer reports "call recordings aren't being saved" — worked yesterday, failing today.

**Investigation:**

1. Check bucket metrics: GET requests normal, PUT requests dropped to near zero
2. Check bucket capacity: 100% full — customer hit their storage quota
3. New PUTs are being rejected with 403 Quota Exceeded
4. **Immediate fix:** Increase quota or delete old data
5. **Root cause:** Customer has no lifecycle policy; 3 years of recordings accumulated
6. **Long-term fix:** Implement 7-year retention + archive to COLD after 90 days

```bash
# Check current bucket size
curl https://api.telnyx.com/v2/storage/buckets/acme-recordings \
  -H "Authorization: Bearer YOUR_KEY"

# Response: "quota_status": "exceeded"

# List objects to identify candidates for deletion
aws s3 ls s3://acme-recordings/2023/ --recursive \
  --endpoint-url https://storage.telnyx.com
```

---

## Key Takeaways

1. **S3-compatible API** means existing tools work unchanged — use `aws s3` CLI with Telnyx endpoint
2. **Buckets are flat** — "folders" are just key prefixes; use them for organization
3. **Multi-region** allows data residency compliance and latency optimization
4. **CDN integration** caches objects at edge for global delivery of public content
5. **Lifecycle policies** automate tiering and deletion — essential for cost management
6. **Call recordings, faxes, AI data** are primary Telnyx storage use cases
7. **Quota monitoring** prevents sudden write failures — watch capacity and implement lifecycles early

---

**End of Module 2 — Congratulations on completing the NOC Mastery Course!**
