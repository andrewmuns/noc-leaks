# Lesson 115: L4 vs. L7 Load Balancing — When and Why

**Module 3 | Section 3.5 — Load Balancing**
**⏱ ~7 min read | Prerequisites: Lesson 16, 90**

---

Load balancing distributes traffic across multiple service instances. But *how* it distributes traffic depends on what layer of the network stack the load balancer operates at. The choice between Layer 4 and Layer 7 has profound implications for SIP, HTTP, and RTP traffic — understanding when to use each is essential for both NOC troubleshooting and architecture understanding.

## Layer 4 Load Balancing: Fast and Blind

L4 load balancers operate at the TCP/UDP transport layer. They see source/destination IP addresses and ports, and nothing else. They make routing decisions based on these four values (the "4-tuple") without inspecting the payload.

**How it works:**
1. Client sends a TCP SYN (or UDP packet) to the load balancer's VIP (Virtual IP)
2. Load balancer selects a backend server
3. All packets for this connection go to the same backend
4. The load balancer either rewrites destination IP (NAT mode) or encapsulates (DSR/tunneling)

**Advantages:**
- **Speed**: No payload inspection, minimal latency added
- **Protocol agnostic**: Works with any TCP/UDP protocol — SIP, RTP, custom protocols
- **Simplicity**: Less state to maintain, fewer failure modes
- **Connection preservation**: Entire TCP connection goes to one backend

**Limitations:**
- **No content awareness**: Can't route based on SIP headers, HTTP paths, or API keys
- **Coarse health checks**: Can verify TCP port open, but can't check application health
- **Sticky sessions**: Must use IP hash or similar for session affinity — no cookie-based stickiness

**Telecom use cases:**
- RTP media traffic (high throughput, low latency required)
- SIP UDP traffic across POPs
- Any non-HTTP protocol

## Layer 7 Load Balancing: Smart and Protocol-Aware

L7 load balancers inspect the application-layer protocol. For HTTP, they read headers, paths, cookies. For SIP, they can parse headers like Call-ID, Via, and Route.

**How it works:**
1. Client establishes a connection to the load balancer
2. Load balancer terminates the connection and reads the application data
3. Based on routing rules (host, path, headers), it selects a backend
4. Load balancer opens a new connection to the backend and forwards the request

**Advantages:**
- **Content-based routing**: Route `/v2/calls` to the Call Control service, `/v2/messages` to Messaging
- **Advanced health checks**: HTTP GET to `/health` endpoint, check response body
- **Connection multiplexing**: Reuse backend connections across multiple client requests
- **SSL/TLS termination**: Decrypt at the load balancer, offloading TLS work from backends
- **Request manipulation**: Add/modify headers, rewrite URLs

**Limitations:**
- **Higher latency**: Must parse application protocol
- **Protocol-specific**: Needs understanding of each protocol (HTTP, SIP, gRPC)
- **More complex**: More configuration, more potential failure modes
- **Resource intensive**: TLS termination and payload inspection use CPU

## Why SIP Needs Special L7 Handling

SIP creates a unique load balancing challenge: **dialog affinity**.

A SIP call involves multiple messages (INVITE → 100 → 180 → 200 → ACK → ... → BYE) that form a dialog. All messages in a dialog MUST reach the same backend server, because that server maintains the call state.

With HTTP, each request is independent — any backend can handle any request (stateless). With SIP, losing dialog affinity means:
- The BYE reaches a different server than the one handling the call
- The server can't find the call state → responds 481 "Call/Transaction Does Not Exist"
- The call is never properly terminated → ghost calls, billing errors

L4 load balancing handles this *if* the client uses the same source IP:port for all messages. But with NAT, UDP, and retransmissions, this isn't guaranteed.

L7 SIP load balancing can route based on Call-ID header — guaranteeing all messages in a dialog reach the same backend regardless of source IP changes.

🔧 **NOC Tip:** If you see elevated 481 "Call/Transaction Does Not Exist" responses in SIP traces, check the load balancer. A misconfigured load balancer that breaks dialog affinity is a common cause. Verify that SIP traffic is being routed with session persistence based on Call-ID.

## Load Balancing Algorithms

Both L4 and L7 load balancers use algorithms to select backends:

### Round-Robin
Each new connection goes to the next server in sequence. Simple and fair but ignores server load — a server handling a heavy call gets the same new connections as an idle server.

### Least Connections
New connections go to the server with the fewest active connections. Better for SIP where connections have varying durations (short calls vs. long calls).

### IP Hash
Hash the client's source IP to consistently select the same backend. Provides basic session persistence without L7 awareness. Breaks when clients are behind NAT (many clients → same IP → same backend → overload).

### Weighted Round-Robin
Servers get traffic proportional to their weight. A server with weight 3 gets three times more connections than weight 1. Useful when servers have different capacities, or during canary deployments (new version gets weight 1, old version gets weight 9).

### Random with Two Choices (P2C)
Pick two random backends, send to the one with fewer connections. Surprisingly effective — avoids the thundering herd problem of least-connections while providing good distribution.

## Health Checking: Passive vs. Active

**Active health checks** proactively probe backends on a schedule:
- L4: TCP connect to port (is the port open?)
- L7: HTTP GET to `/health` (does the app respond 200?)

**Passive health checks** monitor actual traffic responses:
- Track error rates per backend
- If a backend returns 5 consecutive 503s, mark it unhealthy
- No additional probe traffic — uses real requests

Best practice: use both. Active checks detect backends that are completely down. Passive checks detect backends that are up but misbehaving (responding slowly or with errors).

🔧 **NOC Tip:** When troubleshooting intermittent errors, check if passive health checking is configured. Without it, a partially-broken backend (accepting connections but returning errors for 50% of requests) stays in the pool, causing errors for the percentage of traffic routed to it. With passive health checking, it would be removed after a threshold of errors.

## Real-World Scenario

**Situation:** A subset of API requests (~20%) are timing out, while 80% work fine. The API has 5 backend instances.

**Investigation:**
- Load balancer uses round-robin (even distribution)
- One backend pod is experiencing CPU throttling (Lesson 92) and responding slowly
- The load balancer's health check (TCP port open) passes — the pod accepts connections
- But the pod takes 30+ seconds to respond, exceeding client timeout

**Root cause:** L4 health check (TCP open) doesn't detect application-level degradation.

**Fix:** Switch to L7 health check (HTTP GET `/health` with 2-second timeout). The throttled pod's slow health response triggers unhealthy status, removing it from the pool.

**Prevention:** Configure passive health checking to automatically remove backends with elevated error rates or latency.

---

**Key Takeaways:**

1. L4 load balancing is fast and protocol-agnostic — ideal for RTP media and high-throughput traffic
2. L7 load balancing is content-aware — essential for HTTP path routing and SIP dialog affinity
3. SIP requires dialog affinity (Call-ID-based routing) to prevent ghost calls and 481 errors
4. Least-connections algorithm is generally best for telecom workloads with varying session durations
5. Combine active and passive health checks to catch both down and degraded backends
6. L4 TCP health checks miss application-level problems — use L7 HTTP health checks for application services

**Next: Lesson 100 — HAProxy — Configuration, Monitoring, and Troubleshooting**
