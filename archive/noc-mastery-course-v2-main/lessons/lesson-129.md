# Lesson 129: SIP 5xx/6xx Errors — Server and Global Failures

**Module 4 | Section 4.2 — SIP Debugging**
**⏱ ~7 min read | Prerequisites: Lesson 112**

---

While 4xx errors indicate client-side or request-specific problems, 5xx and 6xx errors represent server-side failures and global unavailability. These are often infrastructure or upstream issues that require different troubleshooting approaches. Understanding each code's meaning helps you quickly identify whether the problem is your service, an upstream carrier, or something else entirely.

## 5xx: Server Errors

5xx responses indicate the server encountered an error fulfilling an apparently valid request. These usually require server-side investigation.

### 500 Internal Server Error

**Meaning:** The server encountered an unexpected condition that prevented it from fulfilling the request.

**Common causes:**
1. **Application crash**: The SIP handler process crashed or threw an unhandled exception
2. **Database connection failure**: Unable to connect to the backend database
3. **Resource exhaustion**: Out of memory, file descriptors, or other resources
4. **Configuration error**: Invalid configuration causing service to fail
5. **Dependency failure**: Required upstream service unavailable

**NOC correlation:**
- Check Kubernetes pod status: `kubectl get pods -n voice-services`
- Look for CrashLoopBackOff, OOMKilled, or Error states
- Application logs show stack traces or errors
- Grafana shows crashing/unhealthy pods

**Troubleshooting:**
```bash
# Check pod status
kubectl get pods -n voice-services -l app=sip-proxy

# Check recent logs (look for stack traces)
kubectl logs -n voice-services -l app=sip-proxy --previous | grep -E "(ERROR|Exception|panic)"

# Check resource utilization
kubectl top pods -n voice-services -l app=sip-proxy
```

### 502 Bad Gateway

**Meaning:** The server acting as a gateway or proxy received an invalid response from the upstream server.

**Common causes:**
1. **Upstream server down**: The carrier or downstream SIP server is not responding
2. **TCP connection reset**: Connection to upstream was abruptly closed
3. **Malformed response**: Upstream sent invalid SIP message
4. **Timeout to upstream**: Upstream took too long to respond

**NOC correlation:**
- Specific carrier having issues
- Network partition between Telnyx and carrier
- Carrier returning non-SIP responses

**Troubleshooting:**
1. Identify which upstream returned the error (check the trace)
2. Check if all carriers show 502 or just one
3. Test connectivity: `telnet carrier-ip 5060`
4. Check carrier status page if available

🔧 **NOC Tip:** 502 from one carrier but not others = that carrier is having issues. Route around them via connection profile changes while investigating. 502 from all carriers = more fundamental issue at your end — check network path, TLS certificates if using SIP over TLS, or firewall rules.

### 503 Service Unavailable

**Meaning:** The server is currently unable to handle the request due to temporary overloading or maintenance.

**Common causes:**
1. **Maintenance mode**: Service intentionally taken offline for maintenance
2. **Rate limiting**: Request rate exceeded configured limits
3. **Overloaded**: Service at capacity, rejecting requests
4. **Circuit breaker open**: Upstream failing, circuit breaker preventing calls
5. **No healthy backends**: All upstream instances unhealthy

**In Telnyx context:**
- Check if Consul maintenance mode is enabled (Lesson 98)
- Check if recent deployment caused degradation
- Check if load balancer health checks are failing

**NOC correlation:**
- Grafana: Error rate spike, latency spike before 503s
- Kubernetes: Pods in CrashLoopBackOff or OOMKilled
- Consul: Services marked critical or in maintenance mode

**Troubleshooting:**
```bash
# Check Consul maintenance status
consul catalog services -tags  # Look for maintenance tags

# Check if SIP proxy has any healthy instances
curl -s http://localhost:8500/v1/health/service/sip-proxy?passing | jq length

# Check pod status for issues
kubectl get pods -n voice-services -l app=sip-proxy -o wide
```

🔧 **NOC Tip:** 503 during or shortly after a deployment often indicates pods failing to start properly or not being marked healthy in time. Check ArgoCD sync status, Kubernetes pod events, and Consul health checks. The service may be running but not reporting healthy to Consul yet.

### 504 Gateway Timeout

**Meaning:** The server acting as a gateway did not receive a timely response from the upstream server.

**Difference from 502:**
- 502: Got an invalid/bad response from upstream
- 504: Got no response from upstream (timeout)

**Common causes:**
1. **Upstream slow**: Carrier is slow to respond, exceeds timeout
2. **Network latency**: High latency to carrier, responses arrive too late
3. **Upstream overloaded**: Carrier is overloaded and can't respond
4. **SIP timer mismatch**: SIP Timer B (INVITE timeout) configuration mismatched

**Troubleshooting:**
- Check SIP Timer B configuration (default 32 seconds)
- Check network latency to carrier: `mtr carrier-ip`
- Check if carrier has capacity issues
- Compare timeout logs against expected transaction times

## 6xx: Global Failures

6xx responses indicate the request cannot be fulfilled by any server (it's a global rejection, not specific to one server).

### 600 Busy Everywhere

**Meaning:** All possible destination locations are busy.

**Common causes:**
- Destination is on multiple calls across all their devices
- Sequential forking tried all destinations, all were busy
- Called party has "do not disturb" enabled across all devices

**Not usually infrastructure-related** — this is a legitimate user state.

### 603 Decline

**Meaning:** The destination does not wish to participate in the call and has definitively rejected the request.

**Common causes:**
- User manually rejected the call
- Application logic rejected based on caller ID or other criteria
- Spam/fraud prevention system blocked the call

**Troubleshooting:**
- Check if specific to certain callers or destinations
- Review any spam filtering or robocall prevention systems

### 604 Does Not Exist Anywhere

**Meaning:** The server has authoritative information that the user does not exist at all.

**Difference from 404:**
- 404: The domain/user was found but this specific resource doesn't exist
- 604: The domain says definitively this user doesn't exist

**Common causes:**
- The dialed number is invalid (doesn't exist in any carrier's lookup)
- The user was deleted from the system
- The domain has no information about this number

**Troubleshooting:**
- Verify the number actually exists with a lookup service
- Check international dialing format (missing country code?)
- Check for misconfigured number mapping/translations

## Correlating 5xx Errors with Infrastructure

| 5xx Code | Kubernetes Check | Consul Check | Likely Failure |
|----------|------------------|--------------|----------------|
| 500 | `kubectl get pods` (look for CrashLoopBackOff, OOMKilled) | Health checks failing | Application crash, resource exhaustion, database connection |
| 502 | Network connectivity to upstream | Upstream service health | Upstream carrier/server down, network partition |
| 503 | Pod health, deployment status | Maintenance mode, no passing instances | Overload, maintenance, no healthy backends |
| 504 | Network latency metrics | Upstream response times | Slow upstream, network latency, timeout configuration |

🔧 **NOC Tip:** Create alert rules in Prometheus that correlate SIP 5xx rates with Kubernetes pod health. If 500 errors spike AND pods show increased restart rate, the cause is likely application crashes (OOM, exceptions). If 500 errors spike but pods are healthy, the cause might be database connections or an external dependency. The correlation narrows investigation by 50%.

## Real-World Troubleshooting Scenario

**Alert:** `SIPProxy5xxRateHigh` — 503 errors at 15% rate on sip-proxy.

**Investigation:**

1. **Check SIP traces in Graylog:**
   ```
   type:SIP AND status:503
   ```

2. **Look at the message flow:**
   ```
   Customer INVITE → SIP Proxy
   ← 503 Service Unavailable  (from sip-proxy, no upstream attempt shown)
   ```

3. **Check Kubernetes pods:**
   ```bash
   kubectl get pods -n voice-services -l app=sip-proxy
   # sip-proxy-abc123: CrashLoopBackOff
   # sip-proxy-def456: Running
   # sip-proxy-ghi789: Running
   ```

4. **One pod in CrashLoopBackOff → load balancer routing traffic to bad pod**

5. **Check why it's crashing:**
   ```bash
   kubectl logs sip-proxy-abc123 -n voice-services --previous
   # Database connection timeout
   # Unable to connect to PostgreSQL at db-billing:5432
   ```

6. **Check database status:**
   ```bash
   # Check if billing database is reachable
   kubectl exec -it sip-proxy-def456 -n voice-services -- \
     pg_isready -h db-billing -p 5432
   # Connection refused
   ```

7. **Database issue confirmed**

**Mitigation:** 
- Remove crashed pod from service: `kubectl delete pod sip-proxy-abc123 -n voice-services`
- Traffic routes only to healthy pods
- Error rate drops

**Resolution:**
- Investigate billing database (SEPARATE incident track)
- Fix database connectivity
- Pod health restores

---

**Key Takeaways:**

1. 500 = server crash or resource exhaustion — check Kubernetes pod status for CrashLoopBackOff or OOMKilled
2. 502 = bad response from upstream (carrier) — route around if isolated to one carrier
3. 503 = service unavailable/overloaded — check Consul maintenance mode, pod health, and capacity
4. 504 = upstream timeout — check network latency and upstream responsiveness
5. 6xx = global failure (user doesn't exist or rejected everywhere) — usually not infrastructure
6. Correlating 5xx rates with Kubernetes pod state and Consul health checks narrows root cause quickly
7. During 5xx spikes, check ArgoCD deployment status — recent deployments often cause 503s if pods fail to start

**Next: Lesson 114 — One-Way Audio and No Audio — Systematic Debugging**
