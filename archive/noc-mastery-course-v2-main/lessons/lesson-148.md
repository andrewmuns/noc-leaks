# Lesson 148: DDoS Attacks and Mitigation
**Module 5 | Section 5.1 — Network Security**
**⏱ ~8 min read | Prerequisites: Lesson 131**

---

## DDoS: When the Internet Turns Against You

A Distributed Denial of Service (DDoS) attack floods a target with so much traffic that legitimate users can't get through. For a telecom platform, this means calls fail, messages don't deliver, and APIs become unresponsive. Understanding DDoS attack types and mitigation strategies is essential because telecom platforms are high-value targets.

## Attack Types

### Volumetric Attacks
The brute-force approach: overwhelm the target's network bandwidth with sheer volume. Common techniques:

- **UDP flood**: Massive volumes of UDP packets to random ports. The target's network link saturates before packets even reach application servers.
- **DNS amplification**: Attacker sends small DNS queries with spoofed source IP (the target's IP) to open DNS resolvers. Each 60-byte query generates a 3000-byte response directed at the target — a 50x amplification factor.
- **NTP amplification**: Similar technique using NTP monlist commands for even higher amplification.

Volumetric attacks are measured in Gbps (gigabits per second). Modern attacks routinely exceed 100 Gbps, with record attacks exceeding 1 Tbps.

### Protocol Attacks
Exploit weaknesses in Layer 3/4 protocols to exhaust server resources:

- **SYN flood**: Sends millions of TCP SYN packets without completing the handshake. The target allocates memory for each half-open connection until resources are exhausted.
- **ACK flood**: Sends TCP ACK packets that the target must process to determine they don't belong to any connection.

### Application Layer Attacks
The most sophisticated — they look like legitimate traffic:

- **HTTP flood**: Thousands of legitimate-looking HTTP requests overwhelming web servers.
- **SIP INVITE flood**: Thousands of valid-looking SIP INVITEs that consume SIP proxy resources (dialog creation, routing lookups, downstream processing).
- **SIP REGISTER flood**: Brute-force registration attempts that consume authentication processing.

🔧 **NOC Tip:** Application-layer attacks are the hardest to detect because each individual request looks legitimate. The signal is volume — 10x normal request rate from unusual source IPs, high rate of failed authentication, or requests to non-existent resources.

## SIP-Specific DDoS Attacks

Telecom platforms face unique DDoS vectors:

### INVITE Flood
An attacker sends thousands of SIP INVITEs per second. Each INVITE triggers:
- SIP parsing and validation
- Authentication challenge (401 response)
- Database lookups
- Downstream carrier routing

Even if the calls never complete (no valid credentials), the processing overhead can overwhelm the SIP proxy.

### REGISTER Flood
Thousands of REGISTER requests per second, typically with invalid credentials. Each request triggers digest authentication processing (hashing operations), which is CPU-intensive at scale.

### OPTIONS Scanning
Attackers use SIP OPTIONS requests to discover live SIP endpoints. While OPTIONS are lightweight, high-volume scanning consumes resources and often precedes more targeted attacks.

## Detection in Grafana

Set up dashboards monitoring:

- **Traffic volume**: Bytes/second per interface. A sudden 10x increase suggests volumetric attack.
- **SIP request rate by method**: INVITE, REGISTER, OPTIONS rates. A spike in any single method is suspicious.
- **SIP authentication failure rate**: High 401/403 response rate indicates brute-force attempts.
- **Unique source IPs**: A sudden increase in unique source IPs sending traffic suggests a distributed attack.
- **Connection/session counts**: Connection tracking table filling up, SIP dialog count spiking.

```promql
# SIP INVITE rate spike detection
rate(sip_requests_total{method="INVITE"}[1m]) > 3 * rate(sip_requests_total{method="INVITE"}[1m] offset 1h)

# Authentication failure spike
rate(sip_responses_total{status_code="401"}[5m]) / rate(sip_requests_total{method="REGISTER"}[5m]) > 0.9
```

## Mitigation Strategies

### Volumetric: Upstream Scrubbing
When attack volume exceeds your network capacity, you can't mitigate locally — the pipe is full before traffic reaches your servers.

Solution: Upstream scrubbing services (covered in detail in Lesson 133). Traffic is diverted through scrubbing centers that filter attack traffic before delivering clean traffic back to your infrastructure.

### Volumetric: Blackholing
Emergency measure: announce a more specific BGP route that directs all traffic to the target IP into a blackhole (null route). This stops the attack but also stops all legitimate traffic to that IP.

**Remote Triggered Blackhole (RTBH)**: Ask your upstream transit provider to blackhole traffic to the attacked IP at their edge, preventing it from consuming your bandwidth.

🔧 **NOC Tip:** Blackholing is a last resort — it effectively takes the targeted service offline. Use it only when the attack is overwhelming your entire network infrastructure and affecting services beyond the targeted IP.

### Protocol: SYN Cookies
SYN cookies allow TCP handshake without allocating state for half-open connections. The server encodes connection information in the SYN-ACK sequence number, only allocating state when the client completes the handshake with a valid ACK.

### Application Layer: Rate Limiting
Limit request rates per source IP:
- SIP REGISTER: max 5 per minute per IP
- SIP INVITE: max 50 per second per IP
- Failed authentication: max 10 per minute per IP (then block)

### Application Layer: Behavioral Analysis
Legitimate SIP traffic follows patterns:
- REGISTER followed by INVITE from the same IP
- Calls with reasonable duration
- Normal codec negotiation

Attack traffic is anomalous:
- INVITE without prior REGISTER
- Calls to premium-rate numbers from new IPs
- Hundreds of INVITEs per second from a single source

## Real-World Scenario: The SIP Flood

Friday afternoon, the NOC sees INVITE rate jump from 200/s to 5,000/s. SIP proxy CPU hits 95%. Legitimate calls start getting 503 responses.

Investigation reveals:
- 4,800 of the 5,000 INVITEs/s come from 200 source IPs not in any customer ACL
- All INVITEs target international premium-rate numbers
- None have valid authentication

Response:
1. **Immediate**: Block the 200 source IPs at the network firewall
2. **Short-term**: Enable rate limiting — max 10 INVITE/s per unauthenticated IP
3. **Monitoring**: Watch for attack resumption from new source IPs
4. **Long-term**: Implement behavioral analysis to auto-detect and block similar patterns

Within 5 minutes of blocking the source IPs, INVITE rate drops to normal 200/s and legitimate calls resume.

## Preparation: DDoS Response Runbook

Every NOC should have a DDoS response runbook with:
1. Detection criteria and thresholds
2. Escalation path (network team, upstream provider contacts)
3. Mitigation steps for each attack type
4. Scrubbing service activation procedure
5. Communication templates for customers and stakeholders
6. Post-attack analysis checklist

🔧 **NOC Tip:** Know your upstream provider's DDoS support contacts and procedures BEFORE you need them. During an active DDoS attack is not the time to figure out how to request traffic scrubbing.

---

**Key Takeaways:**
1. DDoS attacks target bandwidth (volumetric), protocol resources (SYN flood), or application logic (SIP floods)
2. SIP-specific attacks include INVITE floods, REGISTER brute-force, and OPTIONS scanning
3. Volumetric attacks require upstream mitigation — you can't filter what exceeds your pipe capacity
4. Rate limiting per source IP is the primary defense against application-layer SIP attacks
5. Detection relies on comparing current traffic rates to historical baselines in Grafana
6. Prepare a DDoS response runbook and know your upstream provider contacts before an attack occurs

**Next: Lesson 133 — Traffic Scrubbing: Cleaning Malicious Traffic**
