# Lesson 154: Network Segmentation and Zero Trust Principles
**Module 5 | Section 5.1 - Network Security**
**⏱ ~7 min read | Prerequisites: Lessons 131, 137**

---

## Defense in Depth Through Segmentation

Network segmentation is the practice of dividing a network into isolated segments. Each segment has its own security controls, and traffic between segments is explicitly controlled. For telecom platforms, segmentation is essential because a compromise in one area shouldn't mean compromise everywhere.

## Traditional Network Zones

A typical telecom platform uses multiple isolated network segments:

### Internet DMZ
Public-facing services: SIP edge proxies, API gateways, web interfaces
- Accepts untrusted internet traffic
- Minimal access to internal resources
- Heavily monitored and logged

### Signaling Network
SIP proxies, routing engines, authentication services
- Internal-only, no direct internet access
- Accessed via DMZ proxies
- Contains call state and routing logic

### Media Network
RTP media servers, TURN relays
- Large bandwidth requirements
- Strict firewall rules for RTP
- Can't reach management or database networks

### Management Network
SSH access, monitoring agents, configuration tools
- Restricted to operations staff
- Outbound only to production (no inbound from production)
- Separate credentials and VPN required

### Database Network
PostgreSQL, Consul, ClickHouse
- No internet access
- Only accepts connections from specific application servers
- Encrypted connections enforced

### Customer Data Network
Billing, customer information, CDR storage
- Highest security classification
- Minimum necessary access
- Audit logging of all access

## Why Segmentation Matters

### Containment
If the DMZ is compromised, attackers can't easily access databases. They must traverse multiple firewalls and security controls to move laterally.

### Compliance
Many regulations require separation of customer data from public-facing systems. PCI-DSS, HIPAA, and telecom regulations mandate segmentation.

### Operational Safety
A misconfiguration on a media server can't accidentally expose customer data. The blast radius is limited to the media network.

### Monitoring and Detection
East-west traffic (within the data center) is easier to monitor when you know what should happen. Unusual cross-segment traffic is a clear signal of compromise.

🔧 **NOC Tip:** During incident response, knowing the network segments helps assess blast radius quickly. If the SIP proxy is compromised, customer data in the database network should still be safe - verify the firewall rules between segments are working as expected.

## Zero Trust: Never Trust, Always Verify

Traditional network security uses the "castle and moat" model: once you're inside the network, you're trusted. Zero Trust assumes compromise is inevitable and trust no one, even inside the network.

### Zero Trust Principles

**1. Never trust, always verify**
Every request is authenticated and authorized, regardless of source. A service calling another service in the same datacenter must authenticate just like an external client.

**2. Least privilege access**
Services get minimum necessary permissions. A SIP proxy can talk to the routing engine but not the billing database.

**3. Assume breach**
Design systems assuming attackers are already inside. Log everything. Monitor for lateral movement. Contain access so compromise doesn't spread.

**4. Verify explicitly**
Use strong authentication. Verify device health (is the requesting service actually healthy?). Check user identity, location, and behavior patterns.

## Zero Trust in Practice

### Micro-segmentation
Instead of large network segments, define per-workload policies:

```
Allow web-server-pod-abc123 to call api-gateway-port-5060
Deny web-server-pod-abc123 to call database-port-5432
```

Kubernetes Network Policies and service mesh (Istio, Linkerd) provide this capability.

### Identity-Aware Proxies
Rather than network location (IP address), identity (service account, mTLS certificate) determines access. A compromised IP address doesn't gain access - the attacker needs valid credentials.

### Continuous Verification
Trust isn't granted once and forgotten. Re-authenticate and re-authorize periodically. If a service's health check fails, revoke its access tokens.

## Jump Boxes / Bastion Hosts

Bastion hosts provide controlled access to production infrastructure:

**Design:**
- Single entry point to management network
- Multi-factor authentication required
- All sessions logged and recorded
- No direct access from laptops - must go through bastion

**Usage:**
```
Laptop → VPN → Bastion → Production Server
```

Benefits:
- Centralized access logging
- Simplified firewall rules (only bastion can access production)
- Session recording for audit trails
- Easier to revoke access (disable one account instead of many)

🔧 **NOC Tip:** Never SSH directly from your laptop to production. Always use the bastion. It leaves an audit trail and ensures your access is logged. If something goes wrong during troubleshooting, the session recording shows exactly what you did.

## Zero Trust Network Access (ZTNA) vs. VPN

### Traditional VPN
- Once connected, users typically have broad network access
- Trust is based on successful VPN authentication
- Works at network layer

### ZTNA
- Per-application access, not network-wide
- Continuous verification of device health and user identity
- Application-layer access controls
- No internal network exposure

For remote NOC engineers, ZTNA provides access to specific dashboards and tools without exposing the internal network. Access is granted per-application, not per-network.

## Real-World Scenario: The Lateral Movement Breach

An attacker compromises a web server in the DMZ through a known CVE. Traditional network design assumes the castle wall (firewall) keeps them out, so internal traffic between servers is often unencrypted and unauthenticated.

**Attack progression:**
1. Exploit web server in DMZ
2. Scan internal network from web server
3. Find database server on management network
4. Connect to database using default credentials or stolen creds
5. Exfiltrate customer data

**With network segmentation:**
1. Exploit web server in DMZ
2. Scan internal network - blocked by firewall between DMZ and internal
3. Attempt to reach database - firewall denies connection
4. Attack contained to DMZ segment

**With Zero Trust:**
1. Exploit web server in DMZ
2. Attempt to call internal service - requires authentication that attacker doesn't have
3. Connection refused despite network path existing
4. More importantly: the attempt is logged and alerts fire

🔧 **NOC Tip:** When investigating security incidents, map the lateral movement path. Which systems did the attacker reach from the initial compromise? Understanding this helps identify which data might be at risk and what other systems to check.

## Implementation Checklist

### Immediate (Quick Wins)
- [ ] Separate admin/management traffic from production traffic
- [ ] Enable bastion host for production access
- [ ] Review firewall rules - deny by default, allow explicitly

### Medium-term
- [ ] Implement network policies in Kubernetes
- [ ] Enable mTLS between services
- [ ] Deploy identity-aware proxy for remote access

### Long-term
- [ ] Full Zero Trust architecture
- [ ] Micro-segmentation per workload
- [ ] Continuous verification and dynamic access policies

---

**Key Takeaways:**
1. Network segmentation contains compromise - a breach in one segment shouldn't grant access to others
2. Traditional "castle and moat" security fails when attackers get inside - Zero Trust assumes compromise is inevitable
3. Never Trust, Always Verify - authenticate every request regardless of source location
4. Jump boxes/bastion hosts provide audit trails and controlled access to production infrastructure
5. Zero Trust Network Access (ZTNA) grants per-application access without exposing internal networks
6. Log and monitor East-West traffic between segments - unusual patterns indicate lateral movement

**Next: Lesson 139 - Introduction to Distributed Systems**
