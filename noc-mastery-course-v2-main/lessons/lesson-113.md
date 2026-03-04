# Lesson 113: Consul — Service Discovery and Health Checking

**Module 3 | Section 3.4 — Consul**
**⏱ ~8 min read | Prerequisites: Lesson 90**

---

In Lesson 90, we saw how Kubernetes Services provide stable addresses for pods. But Telnyx's infrastructure extends beyond a single Kubernetes cluster — bare-metal servers, legacy systems, multi-datacenter deployments, and hybrid environments all need to find each other. That's where Consul comes in.

## Why Consul When We Have Kubernetes Services?

Kubernetes Services work within a cluster. But a telecom platform spans multiple clusters, data centers, and even bare-metal servers running outside Kubernetes. A SIP proxy in the Chicago cluster needs to find a media server in the Dallas datacenter. A billing service in Kubernetes needs to reach a PostgreSQL database on bare metal.

Consul provides a **universal service discovery layer** that works across all of these environments. Every service — whether it's a Kubernetes pod, a bare-metal process, or a VM — registers with Consul and can be discovered through a consistent interface.

## How Service Registration Works

Services register with Consul by providing their name, address, port, and health check definition:

```json
{
  "service": {
    "name": "sip-proxy",
    "port": 5060,
    "tags": ["production", "us-east"],
    "check": {
      "http": "http://localhost:8080/health",
      "interval": "10s",
      "timeout": "2s"
    }
  }
}
```

In Kubernetes environments, registration happens automatically through sidecars or sync mechanisms. The Consul sidecar (running in each pod) registers the pod's service on startup and deregisters on shutdown.

On bare-metal, a Consul agent runs on the host and manages registration for all services on that machine.

## Service Discovery: Finding Healthy Services

Once registered, services are discoverable through two interfaces:

### DNS Interface

Consul exposes a DNS server. Query `<service>.service.consul` to get healthy instances:

```bash
dig @127.0.0.1 -p 8600 sip-proxy.service.consul

# ANSWER SECTION:
# sip-proxy.service.consul.  0  IN  A  10.0.1.15
# sip-proxy.service.consul.  0  IN  A  10.0.2.23
# sip-proxy.service.consul.  0  IN  A  10.0.3.41
```

Only **healthy** instances are returned. If `10.0.1.15` fails its health check, it disappears from DNS responses. No load balancer reconfiguration needed — DNS naturally excludes unhealthy instances.

SRV records provide port information:
```bash
dig @127.0.0.1 -p 8600 sip-proxy.service.consul SRV

# sip-proxy.service.consul.  0  IN  SRV  1 1 5060 node1.node.consul.
# sip-proxy.service.consul.  0  IN  SRV  1 1 5060 node2.node.consul.
```

### HTTP API

The HTTP API provides richer queries:

```bash
# All healthy instances of sip-proxy
curl http://localhost:8500/v1/health/service/sip-proxy?passing

# All registered services
curl http://localhost:8500/v1/catalog/services

# Service instances with metadata
curl http://localhost:8500/v1/catalog/service/sip-proxy
```

The HTTP API returns full metadata: tags, datacenter, node name, health check status, and custom metadata. This powers load balancers and routing logic that need more than just IP addresses.

## Health Checks: The Heart of Service Discovery

Health checks determine whether a service instance should receive traffic. Consul supports several types:

### HTTP Check
The most common. Consul sends an HTTP GET to the health endpoint:
```json
{
  "check": {
    "http": "http://localhost:8080/health",
    "interval": "10s",
    "timeout": "2s"
  }
}
```
200 OK = healthy. Anything else = unhealthy.

### TCP Check
Verifies a TCP port is accepting connections:
```json
{
  "check": {
    "tcp": "localhost:5060",
    "interval": "10s"
  }
}
```
Good for services without HTTP endpoints, like SIP proxies listening on port 5060.

### Script Check
Runs a custom script; exit code 0 = healthy:
```json
{
  "check": {
    "args": ["/usr/local/bin/check-sip-proxy.sh"],
    "interval": "30s"
  }
}
```
Script checks can verify complex conditions: database connectivity, upstream service reachability, queue depth, etc.

### TTL Check
The service itself reports its health periodically:
```json
{
  "check": {
    "ttl": "30s"
  }
}
```
The service must call Consul's API (`PUT /v1/agent/check/pass/check-id`) within 30 seconds or it's marked unhealthy. Used when the service has internal knowledge of its health that can't be tested externally.

🔧 **NOC Tip:** During incidents, the distinction between **catalog** and **health** views in Consul is critical. The catalog shows ALL registered instances (including unhealthy ones). The health endpoint shows only healthy ones. If a service has 10 registered instances but only 3 are healthy, the catalog shows 10 while health queries return 3. Always use the health endpoint or filter by `?passing` to see what's actually serving traffic.

## Consul CLI for NOC Operations

Essential commands:

```bash
# List all registered services
consul catalog services

# List all instances of a service (including unhealthy)
consul catalog nodes -service=sip-proxy

# Check cluster members
consul members

# List all health checks (find failing checks)
consul operator raft list-peers   # Raft consensus status

# Force a node to leave the cluster (stuck member)
consul force-leave <node-name>
```

## Datacenter Awareness

Consul is datacenter-aware. Each datacenter runs its own Consul cluster, and they federate:

```bash
# Query a service in a specific datacenter
dig @127.0.0.1 -p 8600 sip-proxy.service.dc2.consul

# HTTP API with datacenter parameter
curl http://localhost:8500/v1/health/service/sip-proxy?dc=dc2&passing
```

This enables cross-datacenter service discovery. A call routing service in Chicago can discover SIP proxies in Dallas, enabling geographic failover.

## Real-World Troubleshooting Scenario

**Alert:** `SIPProxyHealthyInstancesLow` — only 2 of 10 SIP proxy instances are healthy.

**Investigation:**

```bash
# Check Consul's view of the service
curl -s http://localhost:8500/v1/health/service/sip-proxy | jq '.[].Checks[].Status'
# "passing"
# "passing"
# "critical"
# "critical"
# ... (8 critical)

# Get details on a critical instance
curl -s http://localhost:8500/v1/health/service/sip-proxy | \
  jq '.[] | select(.Checks[].Status == "critical") | {Node: .Node.Node, Output: .Checks[].Output}'
# "Output": "HTTP GET http://10.0.1.15:8080/health: 503 Service Unavailable"
```

The health check is reaching the SIP proxy, but the proxy is responding 503 — it considers itself unhealthy. Now check the SIP proxy logs to find out why (maybe it lost its database connection, or its upstream carrier is unreachable).

**Key insight:** Consul health checks tell you *whether* a service is healthy. Application logs tell you *why* it's unhealthy. Always correlate both.

🔧 **NOC Tip:** When multiple instances of the same service fail their health checks simultaneously, the cause is almost never the individual instances — it's a shared dependency. If 8 out of 10 SIP proxies go critical at the same time, look for a common dependency: a database they all connect to, a configuration service they all query, or a network segment they all share.

## Consul in the Telnyx Stack

At Telnyx, Consul serves multiple roles:
- **Service discovery**: Services find each other via Consul DNS
- **Health monitoring**: Failing services are automatically removed from rotation
- **Configuration**: Key/value store for dynamic configuration
- **Traffic management**: Service mesh (covered in Lesson 98) for secure service-to-service communication

Understanding Consul is essential because it's the connective tissue of the platform — when Consul has issues, everything has issues.

---

**Key Takeaways:**

1. Consul provides universal service discovery across Kubernetes, bare metal, and multi-datacenter environments
2. Health checks (HTTP, TCP, script, TTL) determine which instances receive traffic — unhealthy instances are automatically excluded
3. DNS interface (`service.service.consul`) is the simplest discovery mechanism; HTTP API provides richer metadata
4. Catalog shows ALL instances; health endpoint shows only healthy ones — use the right view for the situation
5. When multiple instances fail simultaneously, investigate shared dependencies rather than individual instances
6. Consul is datacenter-aware, enabling cross-datacenter service discovery and geographic failover

**Next: Lesson 98 — Consul Maintenance Mode and Service Mesh**
