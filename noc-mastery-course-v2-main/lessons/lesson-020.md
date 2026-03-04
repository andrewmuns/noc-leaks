# Lesson 20: The Application Layer — HTTP, WebSockets, and gRPC

**Module 1 | Section 1.4 — Protocol Stack**
**⏱ ~7 min read | Prerequisites: Lesson 17**

---

## Why Application Protocols Matter for NOC Engineers

You might think a voice-focused NOC only needs SIP and RTP knowledge. But modern telecom platforms like Telnyx are API-first. Customers create calls via REST APIs, receive events via webhooks, stream real-time data over WebSockets, and internal services communicate via gRPC. When any of these break, it's a NOC incident.

## HTTP: The Foundation of APIs and Webhooks

### HTTP/1.1: One Request, One Response

HTTP/1.1 is a text-based request-response protocol. A client sends a request:

```
POST /v2/calls HTTP/1.1
Host: api.telnyx.com
Authorization: Bearer KEY123...
Content-Type: application/json

{"connection_id": "abc", "to": "+15551234567", "from": "+15559876543"}
```

The server responds:

```
HTTP/1.1 200 OK
Content-Type: application/json

{"data": {"call_control_id": "xyz", "call_leg_id": "leg1", ...}}
```

HTTP/1.1's limitation: **one request per TCP connection at a time.** To send multiple concurrent requests, you need multiple TCP connections (typically 6 per domain in browsers). Each connection incurs TCP + TLS handshake overhead.

**Connection: keep-alive** helps by reusing the same TCP connection for sequential requests, avoiding repeated handshakes. But requests are still serialized — head-of-line blocking at the HTTP level.

### HTTP/2: Multiplexed Streams

HTTP/2 solves the multiplexing problem with **streams** — multiple concurrent request-response exchanges over a single TCP connection. Each stream has an ID, and frames from different streams are interleaved.

Key improvements:
- **Multiplexing:** Many requests in flight simultaneously on one connection
- **Header compression (HPACK):** Repeated headers are compressed, reducing bandwidth
- **Binary framing:** No more text parsing — faster and less error-prone
- **Server push:** Server can proactively send resources (less relevant for APIs)

HTTP/2 is used between Telnyx API servers and clients. It significantly reduces latency for customers making multiple API calls rapidly (e.g., creating a conference with many participants).

### HTTP/3: UDP-Based with QUIC

HTTP/3 replaces TCP with **QUIC** — a UDP-based transport that includes its own reliability, encryption (TLS 1.3 built in), and multiplexing. The key advantage: **no TCP head-of-line blocking.** Lost packets only affect the specific stream they belong to, not all streams on the connection.

HTTP/3 also achieves **0-RTT connection setup** — the QUIC handshake includes TLS, so encrypted data can flow on the first packet for resumed connections.

## REST APIs: Telnyx's Control Plane

Telnyx's API platform uses REST (Representational State Transfer) over HTTPS. Understanding REST patterns helps debug API issues:

**Key HTTP methods:**
- `GET` — Read data (list calls, get number details)
- `POST` — Create resources (initiate a call, order a number)
- `PATCH` — Partial update (modify a connection setting)
- `DELETE` — Remove (release a number)

**HTTP status codes for API troubleshooting:**

| Code | Meaning | NOC Action |
|------|---------|------------|
| 200/201 | Success | All good |
| 400 | Bad Request | Customer's request is malformed — check payload |
| 401 | Unauthorized | Invalid or missing API key |
| 403 | Forbidden | Valid key but insufficient permissions |
| 404 | Not Found | Resource doesn't exist or wrong endpoint |
| 422 | Unprocessable | Valid JSON but business logic rejection |
| 429 | Rate Limited | Customer exceeding API rate limits |
| 500 | Internal Error | Our problem — escalate |
| 502/503 | Gateway/Unavailable | Backend service issue — escalate |

🔧 **NOC Tip:** When a customer reports "the API isn't working," always ask for the HTTP response code and body. A 422 with error details is a customer-side issue. A 500 with no details is an internal problem. The response code instantly tells you which direction to investigate.

## Webhooks: HTTP POST Callbacks

Webhooks are the reverse of API calls — Telnyx sends HTTP POST requests to the customer's server to notify them of events (incoming call, call answered, DTMF received, etc.).

```
POST /telnyx-webhook HTTP/1.1
Host: customer.example.com
Content-Type: application/json
Telnyx-Signature: sha256=abc123...

{"data": {"event_type": "call.initiated", "payload": {...}}}
```

### Why Webhooks Fail

Webhook delivery failures are one of the most common API-related NOC issues:

1. **Customer's server is down:** HTTP connection refused or timeout. Telnyx retries with exponential backoff.
2. **DNS failure:** Can't resolve the customer's webhook URL hostname.
3. **TLS issues:** Customer's certificate expired or using self-signed certs.
4. **Customer returns non-2xx:** The customer's app crashes and returns 500. Telnyx treats this as a failure and retries.
5. **Slow response:** Customer's server takes too long to respond. Webhook times out.
6. **Firewall blocking:** Customer's firewall blocks Telnyx's IP ranges.

🔧 **NOC Tip:** Webhook failures create cascading call control problems. If a customer's call flow depends on webhook responses (e.g., "answer the call" command sent in response to a `call.initiated` webhook), webhook delivery failure means calls ring forever or get rejected. Check webhook delivery logs first when investigating call flow issues.

### Webhook Signature Verification

The `Telnyx-Signature` header allows customers to verify that webhooks genuinely came from Telnyx and weren't tampered with. The signature is a hash of the payload using a shared secret. If customers don't verify signatures, they're vulnerable to forged webhook injection.

## WebSockets: Persistent Bidirectional Communication

WebSockets provide a persistent, full-duplex connection over a single TCP connection. Unlike HTTP's request-response pattern, either side can send messages at any time.

**How WebSockets start:** An HTTP/1.1 upgrade handshake:

```
GET /ws HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
```

Once upgraded, the connection switches from HTTP to the WebSocket protocol — a lightweight framing layer over TCP.

**Telnyx uses WebSockets for:**
- **Real-time event streaming:** Alternative to webhooks for customers who prefer push-based events
- **WebRTC signaling:** Browser-based calling uses WebSocket to exchange SIP-like signaling
- **Media streaming:** Audio streaming for AI/transcription features

### WebSocket Troubleshooting

WebSocket connections are long-lived, which creates unique challenges:

- **Proxy/load balancer timeouts:** Some proxies kill idle connections. WebSocket keepalive pings (protocol-level, not application) prevent this.
- **Connection drops:** Network glitches drop the TCP connection. The client must detect the drop (via ping/pong timeout) and reconnect.
- **State loss on reconnect:** Unlike HTTP (stateless), WebSocket connections carry state. Reconnecting means reestablishing that state.

## gRPC: Internal Service Communication

**gRPC** is Google's Remote Procedure Call framework, built on HTTP/2. It uses **Protocol Buffers (protobuf)** for binary serialization — much more efficient than JSON.

Why gRPC matters for Telnyx internally:
- **Service-to-service communication:** Microservices call each other via gRPC. The SIP proxy might call the routing service, which calls the number lookup service.
- **Streaming:** gRPC supports client streaming, server streaming, and bidirectional streaming — ideal for real-time data flows.
- **Strong typing:** Protobuf schemas define message formats at compile time, catching errors before deployment.

**When gRPC issues affect the NOC:** If the routing service is slow or unavailable, SIP call setup is delayed or fails. The NOC sees SIP 503 or 500 errors. Understanding that these map to internal gRPC failures helps with triage:

- gRPC `UNAVAILABLE` → Service is down → Check pod health in Kubernetes
- gRPC `DEADLINE_EXCEEDED` → Service is too slow → Check resource utilization
- gRPC `INTERNAL` → Service crashed → Check error logs

🔧 **NOC Tip:** When you see elevated 5xx SIP responses and the SIP infrastructure itself looks healthy, the problem is often in a downstream gRPC service. Check internal service dashboards (Grafana) for gRPC error rates and latency. The SIP layer is just the messenger — the actual failure is deeper in the stack.

### Real Troubleshooting Scenario

**Scenario:** Customers report that calls take 5-10 seconds to set up instead of the usual 1-2 seconds. No SIP errors — calls eventually succeed.

**Investigation:** SIP INVITEs are being processed but the internal routing decision (a gRPC call to the routing service) is timing out and retrying. The routing service's database is experiencing high latency due to a runaway query.

**Resolution:** The DBA kills the runaway query. Routing service latency returns to normal. Call setup time drops back to normal.

**Lesson:** SIP-level symptoms often have infrastructure-level causes. Follow the chain: SIP → internal service (gRPC) → database/cache → infrastructure.

---

**Key Takeaways:**
1. HTTP/1.1 (text, serial), HTTP/2 (binary, multiplexed), and HTTP/3 (QUIC/UDP, no head-of-line blocking) each solve limitations of their predecessor — Telnyx APIs use HTTP/2
2. REST API troubleshooting starts with the HTTP status code: 4xx is customer-side, 5xx is Telnyx-side
3. Webhook delivery failures cascade into call control failures — always check webhook logs when investigating call flow issues
4. WebSockets provide persistent bidirectional communication for real-time events and WebRTC signaling; long-lived connections need keepalive management
5. Internal gRPC service issues manifest as SIP 5xx errors; when SIP infrastructure looks healthy but calls fail, investigate downstream services

**Next: Lesson 19 — DNS Fundamentals: Resolution, Records, and the Hierarchy**
