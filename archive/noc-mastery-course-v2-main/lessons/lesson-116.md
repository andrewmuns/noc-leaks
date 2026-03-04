# Lesson 116: HAProxy — Configuration, Monitoring, and Troubleshooting

**Module 3 | Section 3.5 — Load Balancing**
**⏱ ~7 min read | Prerequisites: Lesson 99**

---

HAProxy is one of the most widely used load balancers in production telecom environments. It handles both L4 and L7 traffic with exceptional performance and provides detailed metrics that make it invaluable for NOC monitoring. Understanding HAProxy's architecture and stats page is a core NOC skill.

## HAProxy Architecture: Frontend → Backend → Server

HAProxy's configuration follows a clean three-layer model:

**Frontend**: Listens for incoming connections on a specific IP:port. Defines which traffic to accept and where to send it.

**Backend**: A group of servers that can handle requests. Defines the load balancing algorithm, health checks, and server list.

**Server**: An individual backend instance (IP:port) with its own weight, health status, and connection limits.

```
[Clients] → [Frontend :443] → [Backend: api-servers] → [Server: api-01:8080]
                                                      → [Server: api-02:8080]
                                                      → [Server: api-03:8080]
```

A simplified configuration:

```haproxy
frontend http-in
    bind *:443 ssl crt /etc/ssl/api.pem
    default_backend api-servers

    # ACL-based routing
    acl is_voice path_beg /v2/calls
    acl is_messaging path_beg /v2/messages
    use_backend voice-api if is_voice
    use_backend messaging-api if is_messaging

backend api-servers
    balance leastconn
    option httpchk GET /health
    server api-01 10.0.1.10:8080 check inter 5s fall 3 rise 2
    server api-02 10.0.1.11:8080 check inter 5s fall 3 rise 2
    server api-03 10.0.1.12:8080 check inter 5s fall 3 rise 2
```

Key configuration elements:
- `balance leastconn`: Use least-connections algorithm
- `option httpchk GET /health`: L7 health check via HTTP
- `check inter 5s`: Health check every 5 seconds
- `fall 3`: Mark unhealthy after 3 consecutive failures
- `rise 2`: Mark healthy after 2 consecutive successes

## ACLs and Routing Rules

ACLs (Access Control Lists) enable L7 content-based routing:

```haproxy
# Route by path
acl is_api path_beg /api/
acl is_websocket hdr(Upgrade) -i websocket

# Route by header
acl is_sip_tcp hdr(Via) -m sub SIP/2.0/TCP

# Route by source IP
acl is_internal src 10.0.0.0/8

use_backend ws-servers if is_websocket
use_backend api-servers if is_api
use_backend sip-servers if is_sip_tcp
```

This is how a single HAProxy instance can route different types of traffic to different backend pools based on protocol, path, headers, or client IP.

## Connection Draining: Safe Deployments

When you need to remove a backend server for maintenance, connection draining lets existing connections complete while stopping new connections:

```bash
# Via HAProxy stats socket — set server to drain mode
echo "set server api-servers/api-01 state drain" | socat stdio /var/run/haproxy.sock

# Check current sessions on the server
echo "show stat" | socat stdio /var/run/haproxy.sock | grep api-01
```

In drain mode:
- **New connections**: Routed to other servers
- **Existing connections**: Continue until they close naturally
- **Health checks**: Continue running

After connections drop to zero, it's safe to perform maintenance.

🔧 **NOC Tip:** Always drain before restarting. `set server state drain` → wait for active sessions to reach 0 → perform maintenance → `set server state ready`. For SIP proxies, this means active calls complete without drops. The drain wait depends on typical call duration — 5 minutes covers most calls, 30 minutes for paranoid safety.

## The HAProxy Stats Page

The stats page is a real-time dashboard of HAProxy's state — one of the most useful NOC tools:

```haproxy
listen stats
    bind *:8404
    stats enable
    stats uri /haproxy-stats
    stats refresh 5s
```

The stats page shows per-frontend and per-backend:

| Metric | Meaning | What to Watch |
|--------|---------|---------------|
| **Sessions (cur/max/limit)** | Active connections | Approaching limit = connection exhaustion |
| **Bytes in/out** | Traffic volume | Sudden changes indicate traffic shifts |
| **Denied** | Blocked requests | Spike = possible attack or misconfigured ACL |
| **Errors (req/conn/resp)** | Error counts | Any non-zero warrants investigation |
| **Server status** | UP/DOWN/DRAIN/MAINT | RED = servers down, investigate |
| **Queue** | Waiting connections | Non-zero = backends saturated |
| **Rate** | Requests per second | Baseline comparison for anomaly detection |

### Color Coding
- **Green**: Server UP, healthy
- **Yellow**: Server in DRAIN or transitioning
- **Red**: Server DOWN, health checks failing
- **Blue**: Server in MAINTENANCE (manually disabled)

🔧 **NOC Tip:** Bookmark the HAProxy stats page for every critical HAProxy instance. During incidents, the stats page gives you a 2-second understanding of backend health. If one server is red, that's a single-server issue. If all servers in a backend are red, the health check endpoint itself might be broken, or a shared dependency is down.

## Common HAProxy Issues and Troubleshooting

### Connection Limit Exhaustion

```
frontend http-in
    maxconn 50000  # Global connection limit
```

When `maxconn` is reached, new connections are queued. If the queue fills up, connections are refused. Symptoms: intermittent connection refused errors, correlating with high-traffic periods.

**Check:**
```bash
echo "show info" | socat stdio /var/run/haproxy.sock | grep -i conn
# CurrConns: 49850  ← dangerously close to 50000
# MaxConn: 50000
```

**Fix:** Increase `maxconn` (if system resources allow) or add more backends to handle the load.

### Health Check Failures

When health checks fail, HAProxy removes the server from the pool:

```
[WARNING] Server api-servers/api-01 is DOWN, reason: Layer7 timeout,
  check duration: 5001ms. 2 active and 0 backup servers left.
```

"Layer7 timeout" means the health check HTTP request didn't get a response in time. The server might be alive but too slow — CPU throttling, garbage collection pause, or dependency timeout.

### Timeout Configuration

HAProxy has multiple timeout settings, each serving a different purpose:

```haproxy
defaults
    timeout connect 5s      # Time to establish connection to backend
    timeout client 30s      # Max inactivity from client side
    timeout server 30s      # Max inactivity from server side
    timeout http-request 10s # Max time for complete HTTP request
    timeout queue 30s       # Max time waiting in queue for a backend
```

Misconfigured timeouts cause false failures:
- `timeout connect` too short: Backend on a congested network gets marked down
- `timeout server` too short: Slow API endpoints timeout before responding
- `timeout client` too long: Idle connections pile up, exhausting connection limits

## Real-World Troubleshooting Scenario

**Alert:** Webhook delivery failures spiking. Customers report their Call Control applications aren't receiving events.

**Investigation:**

1. Check HAProxy stats for the webhook-delivery backend:
   - Queue depth: 350 (normally 0)
   - 2 of 5 servers: DOWN (red)
   - Remaining 3 servers: sessions at 95% of per-server maxconn

2. Two servers went down (health check timeout), load shifted to remaining three, which are now saturated.

3. Check why servers went down:
   ```bash
   # HAProxy logs
   grep "webhook-delivery" /var/log/haproxy.log | tail -20
   # Layer7 timeout on health checks for servers 4 and 5
   ```

4. SSH to the down servers — they're running but their health endpoint hangs due to a database connection pool exhaustion (Lesson 122 preview!).

**Mitigation:**
- Restart the unhealthy webhook-delivery instances to reset connection pools
- They pass health checks and re-enter the HAProxy pool
- Queue drains, webhook delivery resumes

---

**Key Takeaways:**

1. HAProxy routes traffic through frontends → backends → servers, with ACLs for content-based routing
2. Connection draining (`set server state drain`) enables zero-downtime maintenance
3. The stats page is an essential NOC tool — shows real-time backend health, connection counts, and error rates
4. Connection limit exhaustion causes intermittent failures during traffic spikes — monitor `CurrConns` vs `MaxConn`
5. Timeout misconfiguration is a common root cause — each timeout (connect, client, server, queue) serves a different purpose
6. When queue depth grows, backends are saturated — either scale backends or investigate why existing ones are slow

**Next: Lesson 101 — Metrics — Prometheus and Time-Series Data**
