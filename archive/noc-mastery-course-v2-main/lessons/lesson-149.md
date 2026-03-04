# Lesson 149: Traffic Scrubbing - Cleaning Malicious Traffic
**Module 5 | Section 5.1 - Network Security**
**⏱ ~7 min read | Prerequisites: Lesson 132**

---

## When Local Filtering Isn't Enough

In Lesson 132, we covered DDoS attack types and basic mitigation strategies. But what happens when an attack exceeds your network capacity? A 100 Gbps volumetric attack cannot be filtered on-premises - your network links are saturated before packets even reach your servers. Traffic scrubbing is the solution: diverting attack traffic through specialized cleaning centers that remove malicious packets before legitimate traffic returns to your infrastructure.

## How Traffic Scrubbing Works

### The BGP Diversion Process

Traffic scrubbing relies on BGP route manipulation to redirect traffic:

1. **Detection**: Monitoring identifies attack (traffic spike, anomalous patterns)
2. **Route announcement**: BGP announces a more specific route for the attacked IP through the scrubbing provider's network
3. **Traffic diversion**: All traffic for that IP flows to the scrubbing center instead of your infrastructure
4. **Filtering**: The scrubber analyzes traffic, identifies and drops malicious packets
5. **Clean traffic return**: Filtered legitimate traffic is tunneled back to your infrastructure via GRE or IPSec
6. **Recovery**: After attack subsides, withdraw the BGP route to restore direct traffic flow

The key insight: **the scrubbing provider's network must have more capacity than the attack**. A provider with 1 Tbps of peering can absorb 100 Gbps attacks that would completely saturate a smaller ISP.

## Scrubbing Techniques

### Volumetric Filtering
Attack traffic often has identifiable characteristics:
- **Null packets**: Malformed packets that don't conform to protocol standards
- **Same-source floods**: Millions of packets from a single source IP
- **Protocol violations**: Packets that don't follow TCP/UDP standards

These are dropped at the scrubber's edge before consuming processing resources.

### Protocol-Specific Filtering

**DNS amplification mitigation:**
- Rate-limit queries per source IP
- Block responses to queries that weren't sent (reflection detection)
- Validate DNS query/response pairing

**NTP reflection mitigation:**
- Block monlist requests (the amplification vector)
- Rate-limit NTP traffic

**SYN flood handling:**
- SYN cookies: Allow connection establishment without state allocation
- Rate limit SYNs per source IP

### Behavioral Analysis

Legitimate traffic follows patterns that attack traffic often violates:
- **TCP fingerprinting**: Real browsers have specific TCP stack behaviors
- **TTL analysis**: Attack traffic often has anomalous TTL values
- **Geographic correlation**: Traffic from unexpected regions during off-hours
- **Bot signatures**: Known attack tools have identifiable patterns

🔧 **NOC Tip:** When traffic is being scrubbed, you'll see the scrubbing provider's IP addresses in your logs instead of the actual client IPs. This is because the scrubber acts as a proxy. Check for `X-Forwarded-For` headers or use the GRE tunnel endpoint to understand actual client sources.

## Deployment Models

### On-Premise Scrubbing

Appliances deployed in your data center that filter traffic before it reaches your servers.

**Advantages:**
- Low latency (no round-trip to external provider)
- Full control over filtering rules
- No data leaves your network

**Limitations:**
- Capacity limited to appliance hardware (typically 10-40 Gbps)
- High capital expenditure
- Requires in-house expertise
- Can't handle attacks larger than your internet connection

### Cloud Scrubbing

Traffic diverted to provider's scrubbing centers for filtering.

**Advantages:**
- Massive capacity (100+ Gbps to Tbps scale)
- No hardware to maintain
- Provider expertise and threat intelligence
- Global scrubbing locations

**Limitations:**
- Added latency (typically 20-50ms)
- Recurring subscription costs
- Less control over filtering rules
- Data transits third-party infrastructure

### Hybrid Approach

The best of both: on-premise appliances handle small attacks with automatic cloud failover for large attacks.

**How it works:**
1. Small attacks (under appliance capacity): filtered locally, no latency impact
2. Large attacks (exceeding appliance capacity): automatically divert to cloud scrubbing
3. Attack ends: return to local filtering

This minimizes latency for common attacks while ensuring protection against massive volumetric attacks.

## Always-On vs. On-Demand Scrubbing

### Always-On (Continuous)
All traffic always routes through the scrubber.

**Pros:**
- Zero activation delay - already protected
- No "switching" window where traffic is unfiltered
- Continuous visibility into traffic patterns

**Cons:**
- Higher cost (paying for capacity continuously)
- Added latency for all traffic, even when no attack

**Use case:** Critical infrastructure where even minutes of attack exposure is unacceptable.

### On-Demand (Reactive)
Traffic routes directly to you; scrubbing activated when attack detected.

**Pros:**
- Lower cost (pay only when used)
- No latency during normal operation

**Cons:**
- 2-5 minute activation delay while BGP propagates
- Attack traffic reaches you during detection window
- Requires automated detection to activate quickly

**Use case:** Most commercial platforms where brief exposure is acceptable.

🔧 **NOC Tip:** If you use on-demand scrubbing, test the activation process quarterly. The 2-5 minute BGP convergence time is theoretical - routing policies, DNS caching, and provider peering can extend this. Know your actual time-to-protection, not just the vendor's marketing number.

## Real-World Scenario: The Holiday Attack

**Background:** Black Friday, the busiest day of the year for a Telnyx retail customer.

**14:32 UTC:** Grafana shows network traffic spike from baseline 2 Gbps to 87 Gbps

**14:33:** Alert fires for volumetric DDoS

**14:35:** SIP calls begin failing - 503 responses increasing rapidly

**14:38:** NOC engineer activates cloud scrubbing service, announces BGP route for affected IP range

**14:42:** Traffic now flowing through scrubbing center. Scrubber begins filtering. Clean traffic returning via GRE tunnel.

**14:45:** SIP success rate recovering - attack traffic being filtered

**15:20:** Attack subsides. Scrubber reports 87 Gbps attack volume, 2 Gbps legitimate traffic passed

**16:30:** NOC withdraws scrubbing route, traffic returns to direct path

**Result:** 8 minutes of service disruption during the attack, versus potential hours of complete outage. Customer could continue processing orders on Black Friday.

**Post-incident:**
- Upgraded to always-on scrubbing for critical IPs
- Automated detection triggers scrubbing activation without manual intervention
- Reduced time-to-protection from 6 minutes to under 2 minutes

## Monitoring and Operations During Scrubbing

### Metrics to Watch

When traffic is being scrubbed:
- **Scrubber throughput**: How much attack traffic is being filtered?
- **Clean traffic rate**: How much legitimate traffic is being passed?
- **Latency through scrubber**: Is it increasing (potential scrubber overload)?
- **Your server load**: Should be decreasing as attack is filtered

### Communication Template

When activating scrubbing:

> "DDoS attack detected on [IP/service]. Activating traffic scrubbing via [provider]. Expect 2-5 minute convergence time. During scrubbing, latency will increase by approximately [X]ms. Will update when attack subsides."

### Recovery Procedure

1. Monitor until attack traffic is below threshold for 30+ minutes
2. Verify legitimate traffic is stable
3. Withdraw scrubbing route (BGP update)
4. Monitor for 15 minutes to ensure attack doesn't resume
5. Document attack details for post-mortem

## Choosing a Scrubbing Provider

### Evaluation Criteria

| Factor | Questions to Ask |
|--------|------------------|
| Capacity | What's the largest attack you've mitigated? |
| Latency | What's the added latency during scrubbing? |
| Locations | Where are your scrubbing centers? |
| Activation | How quickly can you activate? |
| API | Is there an API for automated activation? |
| Reporting | What attack details do you provide? |
| Cost | Pricing model (always-on vs. on-demand)? |

### Preparation Checklist

Before you need scrubbing:
- [ ] Contract signed and service provisioned
- [ ] IP ranges pre-registered with provider
- [ ] BGP peering established (for fast activation)
- [ ] API credentials tested
- [ ] Runbook documented with activation steps
- [ ] Quarterly drill scheduled to test activation

🔧 **NOC Tip:** Know your scrubbing provider's support contact before an attack occurs. During a 100 Gbps DDoS on a Sunday morning is the wrong time to figure out how to reach someone. Save the emergency number in your runbook and verify it works.

---

**Key Takeaways:**
1. Traffic scrubbing diverts traffic through cleaning centers that filter attack traffic before returning clean traffic to your infrastructure
2. BGP route manipulation redirects traffic - the scrubbing provider's network must have more capacity than the attack
3. Hybrid approach (on-premise + cloud failover) balances low latency with massive capacity
4. Always-on scrubbing provides zero-delay protection but costs more; on-demand has activation delay but costs less
5. Test scrubbing activation quarterly - know your actual time-to-protection, not just theoretical numbers
6. Prepare before you need it: contract, IP registration, BGP peering, API testing, and documented runbook

**Next: Lesson 134 - SIP Security: Toll Fraud Detection and Prevention**
