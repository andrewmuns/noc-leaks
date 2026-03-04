# Lesson 161: Service Discovery and Health Checking
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~7 min read | Prerequisites: Lessons 87, 142**

---

## Why Service Discovery Matters

In dynamic environments (Kubernetes, cloud instances, containers), service locations change constantly:
- Pods restart and get new IPs
- Autoscaling adds/removes instances
- Deployments roll out new versions
- Failover shifts traffic to new nodes

Service discovery answers: "Where is the authentication service right now?" Without it, services would need hardcoded IP addresses that break whenever infrastructure changes.

**Telnyx context:** When a SIP proxy needs to find the billing service, it asks Consul. When a customer API needs a voice service, it queries Consul DNS. Service discovery is the nervous system of the platform.

## How Service Discovery Works

### Registration
When a service starts, it registers itself:
```
service: voice-api
address: 10.0.1.5
port: 8080
tags: ["production", "v2.3"]
health_check: http://10.0.1.5:8080/health
```

### Health Checking
The discovery system continuously checks if services are healthy:
- **HTTP checks**: GET /health expects 200 OK
- **TCP checks**: Can we connect to the port?
- **Script checks**: Run custom command, check exit code
- **TTL checks**: Service sends heartbeat, expires if silent

Unhealthy services are removed from DNS/response lists.

### Discovery
Clients query for services:
```
# DNS query
voice-api.service.consul. A 10.0.1.5, 10.0.1.6, 10.0.1.7

# HTTP API query
GET /v1/catalog/service/voice-api
Returns: [healthy instances]
```

Returned only healthy instances.

## Consul Service Discovery

Consul is the primary service discovery system at Telnyx (Lesson 97).

### Catalog vs Health

**Catalog**: All registered services, regardless of health. Used for: seeing full picture, debugging, weighted routing.

**Health**: Only healthy instances. Used for: actual routing, load balancing, "where should I send traffic?"

```bash
# All registered instances (some may be unhealthy)
consul catalog service voice-api

# Only healthy instances (actually routable)
consul health service voice-api
```

### DNS Interface
Consul provides DNS on port 8600:
```
voice-api.service.consul.  A 10.0.1.5, 10.0.1.6
```

Applications query this DNS instead of hardcoded IPs. Configure via `/etc/resolv.conf` or DNS forwarding.

### Service Mesh Integration
Consul Connect extends discovery with automatic mTLS between services. Services communicate through sidecar proxies that handle service discovery automatically.

## Anti-Entropy

Consul uses anti-entropy to maintain consistency:

1. Services register themselves
2. Consul periodically re-queries services ("are you still there?")
3. If service doesn't respond to health check, it's marked unhealthy
4. Eventually (configurable), unresponsive services are deregistered entirely

This prevents stale entries: if a service crashes without clean deregistration, anti-entropy removes it.

🔧 **NOC Tip:** Anti-entropy intervals matter during incidents. If a service crashes violently (SIGKILL), it can't deregister cleanly. Health check will fail quickly (a few seconds) but anti-entropy might not fully deregister for 72 hours. This leaves "ghost" entries in the catalog. During incident investigation, check both catalog and health - catalog may show instances that are long dead.

## Health Check Design

### What Makes a Good Health Check

**Comprehensive:**
- Service is running? ✓
- Service can accept requests? ✓
- Service's dependencies are reachable? ✓
- Service has capacity? ✓

**But not too deep:**
- Don't make health check hit the database every second (overloads DB)
- Don't make health check do expensive computation
- Must return quickly (< 1-2 seconds typically)

**Example good health check:**
```python
@app.route('/health')
def health():
    # Quick checks (cached health of dependencies)
    if not db_available_cached:
        return {'status': 'unhealthy', 'reason': 'db'}, 503
    if queue_depth > threshold:
        return {'status': 'degraded', 'reason': 'backlog'}, 503
    return {'status': 'healthy'}, 200
```

### Health Check Types

| Type | Pros | Cons |
|------|------|------|
| HTTP | Easy to implement, status codes | Overhead of HTTP stack |
| TCP | Simple, no app code needed | Doesn't verify app is working |
| Script | Can check anything | Requires script deployment, slower |
| TTL | No check load on service | Service must remember to heartbeat |

### Health Check States

Consul health checks have states:
- **passing**: Healthy
- **warning**: Degraded but still serving (may be removed from discovery)
- **critical**: Unhealthy, removed from discovery
- **maintenance**: Manually marked for maintenance, removed from discovery

🔧 **NOC Tip:** If a service shows warning state, investigate before it becomes critical. Warning states suggest degradation that may become failure. Check the health check output message for specific reasons.

## Real-World Scenario: The Cascading Discovery Failure

**14:00**: Database cluster experiences elevated latency due to lock contention
**14:05**: One by one, services start failing health checks (they can't query DB within 1 second timeout)
**14:10**: Consul marks many services critical, removes from DNS
**14:15**: Clients can't find services (empty DNS responses)
**14:20**: Platform appears "down" despite only database slowness

**Root cause**: Health checks too strict. A service that can serve traffic is marked unhealthy because it takes 2 seconds to check a database that normally responds in 50ms.

**Fix:**
1. Extend health check timeout from 1s to 5s
2. Implement degraded mode: if DB is slow, still respond healthy but flag degraded
3. Separate "readiness" (can serve traffic) from "liveness" (is running)
4. Ability mode: use separate endpoint for load balancer vs service dependency checks

**Lesson:** Health checks must balance sensitivity with reality. Too strict: cascading failures. Too lenient: sending traffic to broken services.

## Monitoring Service Discovery

### Key Metrics

```promql
# Service instance count by health
sum by (service_name, status) (
  consul_health_service_status{status="passing"}
)

# Health check failure rate
rate(consul_health_check_failures_total[5m])

# Catalog vs health divergence
(consul_catalog_service_node_healthy - consul_health_service_healthy) > 0
```

### Alerts

- **Service instance count drops**: `count(consul_health_service_healthy) < threshold`
- **All instances unhealthy**: `count(consul_health_service_healthy == 0)`
- **Health check flapping**: frequent passing/critical transitions

## Troubleshooting Discovery Issues

### Service not appearing in DNS
```bash
# Check if registered
consul catalog services | grep my-service

# Check if healthy
consul health service my-service

# Check health check status
consul health checks | grep my-service

# Check logs on service host
journalctl -u consul-agent
```

### Wrong IP returned
- Service may have multiple IPs (multiple interfaces)
- Check `bind_addr` configuration in Consul agent
- Check service registration address

### DNS resolution issues
```bash
# Test different resolvers
dig @localhost -p 8600 my-service.service.consul
dig @127.0.0.1 my-service.service.consul
dig @8.8.8.8 my-service.service.consul  # External (should fail)
```

### High latency on discovery
- DNS cache poisoning or TTL issues
- Too many services causing large responses
- Network issues between client and Consul

---

**Key Takeaways:**
1. Service discovery enables dynamic infrastructure where service locations change constantly
2. Health checking distinguishes healthy from unhealthy instances - only healthy are returned in discovery queries
3. Anti-entropy removes stale registrations but may leave ghost entries for hours if service crashes without deregistration
4. Consul provides both DNS interface for easy integration and HTTP API for programmatic access
5. Health checks must balance sensitivity - too strict causes cascading failures, too lenient sends traffic to broken services
6. Monitor catalog vs health divergence - catalog showing instances health doesn't know about indicates stale entries

**Next: Lesson 146 - Message Queues and Event-Driven Architecture**
