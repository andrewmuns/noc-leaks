# Lesson 72: Webhook Reliability and Debugging

**Module 2 | Section 2.2 — Voice API**
**⏱ ~6 min read | Prerequisites: Lesson 60**

---

## Why Webhooks Are the Achilles' Heel of Programmable Voice

Call Control is webhook-driven. Every call event — incoming call, answer, hangup, DTMF digit, recording ready — is delivered as an HTTP POST to the customer's application. If that webhook fails, the call stalls. The customer's application never learns what happened, so it never issues the next command. The caller hears silence. Or worse, the call just hangs indefinitely.

This makes webhook reliability the single most impactful factor in Call Control application quality, and one of the most common NOC investigation areas.

## How Webhook Delivery Works

When a call event occurs, Telnyx's Call Control engine:

1. Serializes the event as a JSON payload
2. Resolves the webhook URL's DNS (cached, but initial resolution matters)
3. Establishes a TCP/TLS connection to the customer's server
4. Sends an HTTP POST with the JSON body
5. Waits for a response (within the timeout window)
6. If the response is 2xx → delivery succeeded
7. If the response is non-2xx or timeout → retry logic kicks in

The **timeout threshold** is critical. Telnyx waits a configurable number of seconds (typically around 5-10 seconds) for a response. If the customer's application takes longer to respond, the webhook is considered failed — even if the app was processing it.

🔧 **NOC Tip:** The most common webhook "failure" isn't a network issue — it's the customer's application being too slow. If their webhook handler does synchronous database queries, external API calls, or heavy computation before returning a response, it can exceed the timeout. The fix: acknowledge the webhook immediately (return 200), then process asynchronously.

## Failover Webhooks

Telnyx supports configuring a **primary** and **failover** webhook URL. If the primary fails (connection refused, timeout, 5xx response), the event is sent to the failover URL. This provides redundancy — customers can host their failover webhook in a different region or on a different provider.

The failover mechanism adds latency to the call flow (time spent attempting primary + retry to failover), so primary webhook reliability remains essential.

## Common Webhook Failure Modes

### 1. DNS Resolution Failure

The customer's webhook URL can't be resolved. This happens when:
- The domain expired or DNS records were deleted
- The DNS provider is having an outage
- The domain has DNSSEC issues (Lesson 21)

**Symptom in logs:** Connection error before any HTTP exchange occurs.

### 2. TLS Handshake Failure

The webhook URL uses HTTPS (as it should), but the TLS handshake fails:
- Expired certificate (the #1 cause — certificates expire and nobody notices)
- Self-signed certificate (Telnyx validates certificates by default)
- Intermediate certificate missing (server sends leaf cert but not the chain)
- TLS version mismatch

🔧 **NOC Tip:** When a customer reports "webhooks stopped working suddenly," check if their TLS certificate expired. Run `echo | openssl s_client -connect <host>:443 -servername <host> 2>/dev/null | openssl x509 -noout -dates` to check certificate validity. Certificate expiry is responsible for a disproportionate number of webhook failures.

### 3. Connection Timeout

TCP connection can't be established — the server isn't listening, a firewall is blocking, or the server is overloaded. Common causes:
- Customer's server went down
- Firewall rule change blocking Telnyx's IP ranges
- Server at max connections

### 4. HTTP 5xx Response

The customer's server accepted the connection but returned an error:
- 500 Internal Server Error: application bug
- 502 Bad Gateway: reverse proxy can't reach the application
- 503 Service Unavailable: application is overloaded or deploying
- 504 Gateway Timeout: application took too long to respond

### 5. HTTP Timeout (No Response)

The server accepted the connection, received the request, but never sent a response within the timeout window. This is the "slow application" problem — the app is processing the webhook synchronously.

## Debugging with Graylog

To investigate webhook delivery issues, query Graylog with:

- **Call Control ID**: Find all events and webhook deliveries for a specific call
- **Webhook URL**: Find all delivery attempts to a specific endpoint
- **Time window**: Narrow to the incident period
- **HTTP status codes**: Filter for non-2xx responses

A typical Graylog query might look like:
```
webhook_url:"https://customer-app.example.com/webhooks" AND NOT http_status:200
```

Look for patterns: are all webhooks failing (infrastructure issue) or only certain event types (application bug)? Is the failure consistent (server down) or intermittent (overload)?

## Customer Application Issues vs. Telnyx Platform Issues

This is the critical distinction for NOC engineers:

**It's a Telnyx issue if:**
- Webhook delivery logs show our system never attempted delivery
- The Call Control engine isn't generating events for valid calls
- Multiple customers with different webhook servers experience failures simultaneously
- Internal Grafana dashboards show elevated error rates in the Call Control service

**It's a customer issue if:**
- Webhook delivery logs show we sent the request but got timeout/5xx
- Only one customer is affected
- The customer's webhook URL is unreachable from our infrastructure
- The customer recently changed their server/DNS/TLS configuration

🔧 **NOC Tip:** Always check the Grafana dashboard for Call Control webhook delivery success rate first. If the overall rate is normal (>99.5%) and only one customer reports issues, it's almost certainly customer-side. If the rate has dropped across the board, escalate immediately — it's a platform issue.

## Retry Logic and Its Implications

When a webhook delivery fails, Telnyx retries with exponential backoff. But for time-sensitive call events (like an incoming call), retries have limited usefulness — by the time the retry succeeds, the caller may have hung up.

For non-time-sensitive events (recording ready, call summary), retries are more useful. The customer can process them when their server recovers.

**Important:** Retry logic means the same event might be delivered multiple times if the customer's server is flaky (received the request, processed it, but the response was lost). Customer applications must be **idempotent** — processing the same event twice should produce the same result.

## Troubleshooting Scenario: "Calls Ring But Nobody Answers"

A customer reports that incoming calls ring but their application never answers them.

**Investigation:**
1. Graylog: Search for webhook deliveries to the customer's URL → Found: all returning HTTP 502
2. The customer's reverse proxy (nginx) is returning 502 because the upstream application crashed
3. The Call Control engine sends the `call.initiated` webhook, gets 502, retries, gets 502 again
4. Without a successful webhook delivery, the customer's app never issues the `answer` command
5. The call rings until the caller gives up

**Resolution:** Customer restarted their application server. Root cause: memory leak caused the process to crash under load.

---

**Key Takeaways:**
1. Webhook delivery is the critical path for Call Control — if webhooks fail, calls fail
2. The most common webhook failure is customer-side: slow applications, expired TLS certificates, or server downtime
3. Always check certificate expiry first when webhooks "suddenly stop working"
4. Use Graylog to trace webhook delivery attempts by Call Control ID or webhook URL
5. Distinguish platform issues (global delivery rate drop) from customer issues (single customer affected)
6. Customer applications must be idempotent due to retry-based delivery

**Next: Lesson 63 — TeXML: TwiML-Compatible Voice Scripting**
