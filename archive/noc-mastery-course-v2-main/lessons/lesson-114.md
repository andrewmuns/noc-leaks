# Lesson 114: Consul Maintenance Mode and Service Mesh

**Module 3 | Section 3.4 — Consul**
**⏱ ~7 min read | Prerequisites: Lesson 97**

---

In Lesson 97, we learned how Consul discovers healthy services. But what happens when you *need* to take a service offline — for maintenance, upgrades, or troubleshooting? And how do services communicate securely when they can't implicitly trust each other? This lesson covers Consul's operational features: maintenance mode for graceful traffic management and the service mesh for secure inter-service communication.

## Maintenance Mode: Gracefully Removing Services from Rotation

Maintenance mode tells Consul to mark a node or service as unhealthy, removing it from discovery results — without actually stopping the service or modifying health checks.

### Node-Level Maintenance

Mark an entire node (and all its services) as under maintenance:

```bash
# Enable maintenance mode on the current node
consul maint -enable -reason "Scheduled kernel upgrade"

# Check maintenance status
consul maint

# Disable maintenance mode after work is complete
consul maint -disable
```

When maintenance is enabled, all services on that node are marked critical. DNS queries stop returning them. Load balancers using Consul for backend discovery stop routing traffic to them. Existing connections are not forcibly terminated — they drain naturally.

### Service-Level Maintenance

Mark a specific service as under maintenance without affecting other services on the same node:

```bash
# Enable maintenance for just sip-proxy on this node
consul maint -enable -service=sip-proxy -reason "Deploying new config"

# Disable when done
consul maint -disable -service=sip-proxy
```

This is more surgical — if a node runs both sip-proxy and media-server, you can take sip-proxy out of rotation while media-server continues serving traffic.

## The Graceful Drain Pattern

Maintenance mode is one piece of a broader pattern for safe changes:

1. **Enable Consul maintenance** → Node/service removed from discovery
2. **Wait for connections to drain** → Existing calls/sessions complete naturally
3. **Perform the change** → Upgrade, restart, reconfigure
4. **Verify health** → Confirm the service is functioning correctly
5. **Disable maintenance** → Service re-enters the pool, receives new traffic

The drain wait is critical. For SIP proxies, active calls might last 30-60 minutes. Cutting connections immediately drops those calls. Waiting for natural completion means zero user impact.

🔧 **NOC Tip:** When performing emergency maintenance, decide between graceful and immediate based on severity. For a planned upgrade, drain for 30 minutes. For a service that's actively causing damage (sending malformed responses, corrupting data), skip the drain — the damage from continued operation outweighs dropped connections.

```bash
# Graceful: enable maintenance and wait
consul maint -enable -service=sip-proxy
echo "Waiting 60 seconds for connections to drain..."
sleep 60
systemctl restart sip-proxy

# Emergency: stop immediately
systemctl stop sip-proxy
consul maint -enable -service=sip-proxy
# Fix the issue
systemctl start sip-proxy
consul maint -disable -service=sip-proxy
```

## Using Maintenance Mode During Incidents

During incident response, maintenance mode is a mitigation tool:

**Scenario:** One SIP proxy instance is returning corrupted SDP, causing one-way audio for ~10% of calls (those routed to that instance).

**Immediate mitigation:**
```bash
# Remove the bad instance from rotation
ssh sip-proxy-node-05
consul maint -enable -service=sip-proxy -reason "INC-4521: corrupted SDP responses"
```

Traffic immediately stops flowing to that instance. Other healthy instances absorb the load. You've mitigated the customer impact in seconds, buying time to investigate the root cause.

After fixing the issue:
```bash
consul maint -disable -service=sip-proxy
# Instance re-enters the pool, health checks confirm it's working
```

## Consul Connect: The Service Mesh

Consul Connect (now called Consul Service Mesh) adds a security and networking layer on top of service discovery. It provides:

### Automatic mTLS Between Services

Every service gets a sidecar proxy (Envoy) that handles encryption. When Service A calls Service B, the communication is automatically encrypted with mutual TLS — both sides verify each other's identity.

```
[SIP Proxy] → [Envoy Sidecar] --mTLS--> [Envoy Sidecar] → [Billing Service]
```

Services don't need to manage certificates themselves. Consul generates and rotates certificates automatically using its built-in Certificate Authority.

Why this matters for telecom: sensitive data (customer information, billing records, call metadata) flows between services. mTLS ensures this data is encrypted in transit and that only authorized services can communicate.

### Intentions: Access Control Between Services

Intentions are Consul's firewall rules for service-to-service communication:

```bash
# Allow sip-proxy to call billing-service
consul intention create -allow sip-proxy billing-service

# Deny analytics from accessing customer-data
consul intention create -deny analytics customer-data

# List all intentions
consul intention list
```

With a default-deny policy, only explicitly allowed communication paths work. If a compromised service tries to reach a database it shouldn't access, the sidecar proxy blocks the connection.

```bash
# Check if a specific communication is allowed
consul intention check sip-proxy billing-service
# Allowed
```

🔧 **NOC Tip:** When a service suddenly can't reach another service it previously communicated with, check Consul intentions. A recently modified intention might be blocking the traffic. Use `consul intention check <source> <destination>` to verify.

### Traffic Management

The service mesh enables advanced traffic management:

- **Traffic splitting**: Route 10% of traffic to a canary deployment
- **Service failover**: Automatically route to another datacenter if local instances fail
- **Circuit breaking**: Stop sending traffic to overwhelmed services

## Consul Key/Value Store

Beyond service discovery, Consul provides a distributed key/value store for configuration:

```bash
# Store a configuration value
consul kv put config/sip-proxy/max_connections 1000

# Retrieve it
consul kv get config/sip-proxy/max_connections

# Watch for changes (blocking query)
consul watch -type=key -key=config/sip-proxy/max_connections <handler-script>
```

Services can watch for key changes and dynamically reconfigure without restarts. This enables:
- Feature flags (enable/disable features without deployment)
- Dynamic rate limits (adjust during traffic spikes)
- Emergency circuit breakers (disable a broken upstream)

## Real-World Troubleshooting Scenario

**Situation:** After a network maintenance window, inter-service communication is failing between the SIP proxy and the call routing service. Both services are healthy individually.

**Investigation:**

```bash
# Check if both services are registered and healthy
curl -s http://localhost:8500/v1/health/service/sip-proxy?passing | jq length
# 10 (all healthy)

curl -s http://localhost:8500/v1/health/service/call-routing?passing | jq length
# 5 (all healthy)

# Check Consul mesh intentions
consul intention check sip-proxy call-routing
# Denied

# Someone modified intentions during the maintenance window!
consul intention list
# sip-proxy => call-routing  DENY  (modified 30 minutes ago)
```

An engineer accidentally modified the intention during maintenance. The fix:

```bash
consul intention delete sip-proxy call-routing
consul intention create -allow sip-proxy call-routing
```

Communication restores immediately.

## Consul Cluster Health

Consul itself runs as a cluster (typically 3 or 5 servers using Raft consensus). If Consul goes down, service discovery breaks and traffic routing fails.

```bash
# Check Consul cluster health
consul operator raft list-peers
# Node      ID       Address          State    Voter
# consul-1  abc123   10.0.1.10:8300   leader   true
# consul-2  def456   10.0.1.11:8300   follower true
# consul-3  ghi789   10.0.1.12:8300   follower true

# Check cluster members
consul members
```

A 3-node Consul cluster tolerates 1 node failure. A 5-node cluster tolerates 2. If you lose quorum (majority), Consul becomes read-only — existing DNS cache continues working, but no new registrations or health check updates occur.

🔧 **NOC Tip:** If Consul loses quorum, the immediate impact is delayed — cached DNS entries continue working. But as services restart or health checks change, the stale cache becomes increasingly wrong. Restoring Consul quorum is a high-priority task because the blast radius grows over time.

---

**Key Takeaways:**

1. Maintenance mode removes services from discovery without stopping them — essential for graceful drains and safe deployments
2. The graceful drain pattern: enable maintenance → wait for drain → perform work → verify → disable maintenance
3. Consul Connect provides automatic mTLS encryption between services without application code changes
4. Intentions control which services can communicate — check them when inter-service communication fails unexpectedly
5. The KV store enables dynamic configuration without service restarts
6. Consul cluster health is critical — loss of quorum degrades all service discovery with increasing blast radius over time

**Next: Lesson 99 — L4 vs. L7 Load Balancing — When and Why**
