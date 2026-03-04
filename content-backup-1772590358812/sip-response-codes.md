---
title: "SIP Response Codes — What Every Code Means"
description: "Learn about sip response codes — what every code means"
module: "Module 1: Foundations"
lesson: "42"
difficulty: "Advanced"
duration: "8 minutes"
objectives:
  - Understand 1xx provisional responses keep transactions alive; 183 Session Progress enables early media (ringback tones)
  - Understand 401/407 are normal authentication challenges, not errors — repeated loops indicate bad credentials
  - Understand 408 is locally generated when no response arrives — it points to reachability problems
  - Understand 487 is normal call cancellation (caller hung up during ringing), not a failure
  - Understand 488 means codec/SDP mismatch — compare offered vs. supported codecs
slug: "sip-response-codes"
---

## Why Response Codes Matter

Every SIP transaction ends with a response code. As a NOC engineer, these three-digit numbers are your first diagnostic signal — they tell you *what happened* before you ever open a packet capture. Knowing response codes by heart is like a doctor knowing vital sign ranges: it immediately narrows the diagnosis.

SIP borrowed its response code scheme from HTTP, organized into six classes. But unlike HTTP, SIP has provisional responses that arrive *during* transaction processing, not just at the end. This distinction is critical for understanding call setup timing.

---

## 1xx — Provisional Responses

Provisional responses indicate the request is being processed but hasn't reached a final state yet. They keep the transaction alive and prevent timeout.

### 100 Trying
The first hop received your INVITE and is working on it. This is hop-by-hop — each proxy sends 100 Trying back to its upstream immediately. It exists solely to stop Timer A (INVITE retransmission) from firing. If you don't see a 100 Trying, the request probably never reached the next hop.

### 180 Ringing
The called endpoint is alerting (ringing). This is end-to-end — it means the INVITE reached a real device and that device is presenting the call to a human. In NOC operations, seeing 180 Ringing but no 200 OK means the call reached the destination but wasn't answered. The distinction between "no 180" and "180 but no 200" is crucial: the first is a routing/reachability problem, the second is a user behavior issue.

### 183 Session Progress
This is arguably the most important provisional response for VoIP. 183 with an SDP body establishes *early media* — a media path before the call is answered. This is how you hear ringback tones, announcements ("the number you have dialed..."), and IVR prompts from the far end before answer. Without early media, callers would hear silence until the call connects.

> **💡 NOC Tip:**  customers report "no ringback tone," check whether 183 Session Progress with SDP is being received. Some configurations strip early media, causing silence during ring phase.
slug: "sip-response-codes"
---

## 2xx — Success

### 200 OK
The universal success response. For INVITE, it means the call is answered. For REGISTER, it means registration succeeded. For BYE, it confirms call termination. The 200 OK to an INVITE *must* contain an SDP answer (unless the offer was in a previous message).

### 202 Accepted
Used for REFER — acknowledges the transfer request was received but doesn't mean it succeeded. The actual result comes via subsequent NOTIFY messages. Don't confuse 202 with "transfer complete."

---

## 3xx — Redirection

### 301 Moved Permanently / 302 Moved Temporarily
The called URI has moved — follow the Contact header in the response to find the new location. In practice, 302 is used for call forwarding. The calling UA (or proxy) should retry the INVITE to the new destination in the Contact header.

In a B2BUA architecture like Telnyx's, the B2BUA handles redirects transparently — the customer never sees them. But when debugging, you might see 302 responses on the carrier side that the B2BUA follows automatically.
slug: "sip-response-codes"
---

## 4xx — Client Errors

This is where NOC engineers spend most of their time. 4xx responses indicate the request itself is problematic.

### 400 Bad Request
The SIP message is malformed — bad syntax, missing required headers, or invalid values. Often caused by broken SIP implementations or SIP ALGs mangling messages.

### 401 Unauthorized / 407 Proxy Authentication Required
Authentication challenge. 401 comes from UAS (registrar/endpoint), 407 from a proxy. This is *not* an error — it's the first step of digest authentication. The flow is: request → 401/407 with nonce → request with credentials → 200 OK. If you keep seeing 401s without successful auth, credentials are wrong.

> **💡 NOC Tip:** peated 401 loops (REGISTER → 401 → REGISTER → 401 → ...) almost always mean wrong username or password. Check if the customer recently changed credentials but didn't update their PBX.

### 403 Forbidden
Authentication succeeded but authorization failed — you proved who you are, but you're not allowed to do what you asked. Common causes: IP ACL rejection, disabled account, calling a blocked destination, missing outbound calling permission.

### 404 Not Found
The user/number doesn't exist in the domain. For outbound calls, this might mean the number isn't routable. For inbound, it could mean the DID isn't provisioned.

### 408 Request Timeout
No response was received in time. This is generated locally by the proxy or UAC when Timer B (32 seconds for INVITE) or Timer F (32 seconds for non-INVITE) expires. **408 does not mean the far end sent a timeout response** — it means nobody responded at all.

This is one of the most common codes in NOC operations. Common causes:
- The destination endpoint is unreachable (firewall, network outage)
- DNS resolved to a dead IP
- The far-end carrier is overloaded and not responding

### 480 Temporarily Unavailable
The callee is not available right now — phone is off, not registered, DND enabled. Unlike 404 (doesn't exist), 480 means the user exists but can't be reached right now.

### 486 Busy Here
The callee's line is busy. Straightforward, but in a multi-device environment, 486 from one device doesn't mean all devices are busy — the proxy may fork to other registered contacts.

### 487 Request Terminated
The INVITE was cancelled via a CANCEL request. This is a *normal* response — it means the caller hung up before the callee answered. High 487 rates indicate short patience (fast abandonment) rather than technical problems.

### 488 Not Acceptable Here
The SDP offer couldn't be satisfied — no common codec, incompatible media parameters. This is the "codec mismatch" error. Check the SDP in the INVITE against the capabilities of the far end.

> **💡 NOC Tip:**  you see 488 responses, compare the codec list in the INVITE's SDP with what the destination supports. Often, a customer configures only G.729 but the carrier requires G.711, or vice versa.

---

## 5xx — Server Errors

### 500 Internal Server Error
Something went wrong inside the UAS/proxy. A generic error that usually means a software bug or unexpected condition. Check server-side logs.

### 502 Bad Gateway
A proxy forwarded the request and received an invalid response from the next hop. Common in chained proxy/B2BUA scenarios.

### 503 Service Unavailable
The server can't handle the request right now — overloaded, in maintenance, or a downstream dependency is down. **503 is the most important 5xx code for NOC operations** because it often indicates capacity problems or outages.

In many deployments, 503 triggers failover to alternate routes. Telnyx's routing engine treats 503 as a signal to try the next carrier in the routing table.

### 504 Server Timeout
The proxy's attempt to reach the next hop timed out. Similar to 408 but from a proxy's perspective — the proxy sent the request downstream and got no response.
slug: "sip-response-codes"
---

## 6xx — Global Failures

### 600 Busy Everywhere
The callee is busy on all devices — unlike 486 (busy on one device). In practice, rarely used.

### 603 Decline
The callee explicitly rejected the call. This is the SIP equivalent of "reject call" on a phone.

---

## Reading Response Codes in Practice

When investigating a call failure, the response code tells you *where* to look next:

| Code Range | Investigation Direction |
|------------|----------------------|
| 401/403 | Authentication/authorization — check credentials, IP ACLs, account status |
| 404/480 | Number provisioning, registration status, DID routing |
| 408/504 | Network reachability — is the destination alive? Firewall rules? DNS? |
| 486/487/603 | User behavior — busy, cancelled, declined (usually not a technical issue) |
| 488 | Codec/SDP mismatch — compare media capabilities |
| 500/502/503 | Server health — check logs, capacity, dependencies |

### Real-World Scenario

A customer reports "50% of our outbound calls are failing." You check Grafana and see a spike in 503 responses, but only to a specific carrier. The routing engine is failing over to a secondary carrier (which succeeds), but the primary carrier is returning 503. This tells you:

1. The primary carrier has a capacity or outage issue
2. Failover is working (calls eventually complete)
3. You should check the carrier's status page, open a ticket with them, and potentially adjust routing weights to reduce load on the failing carrier

Without knowing that 503 = "service unavailable" and understanding the failover implications, you might waste time investigating Telnyx's own infrastructure.
slug: "sip-response-codes"
---

**Key Takeaways:**
1. 1xx provisional responses keep transactions alive; 183 Session Progress enables early media (ringback tones)
2. 401/407 are normal authentication challenges, not errors — repeated loops indicate bad credentials
3. 408 is locally generated when no response arrives — it points to reachability problems
4. 487 is normal call cancellation (caller hung up during ringing), not a failure
5. 488 means codec/SDP mismatch — compare offered vs. supported codecs
6. 503 indicates server overload/outage and typically triggers failover routing
7. The response code immediately narrows your investigation scope — learn them by heart

**Next: Lesson 41 — SIP Dialogs and Transactions — Understanding State**
