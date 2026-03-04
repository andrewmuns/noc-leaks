# Lesson 153: Authentication and Authorization Patterns
**Module 5 | Section 5.1 - Network Security**
**⏱ ~7 min read | Prerequisites: Lesson 136**

---

## Authentication vs. Authorization

These related concepts are often confused:

**Authentication**: Proving who you are. The process of verifying identity - checking credentials, tokens, or certificates.

**Authorization**: Determining what you're allowed to do. After authentication, authorization decides which resources you can access and which actions you can perform.

In telecom terms:
- Authentication proves you're "customer123"
- Authorization determines if "customer123" can make international calls, view CDRs, or provision numbers

You must authenticate before authorization. A request with valid credentials but insufficient permissions fails authorization, not authentication.

## Authentication Patterns

### API Keys: Simple but Limited

API keys are the simplest authentication mechanism:

```
Authorization: Bearer YOUR_API_KEY
```

**How it works:**
- Server maintains a database of valid keys with customer associations
- Each request includes the key in a header
- Server looks up the key, identifies the customer, processes the request

**Strengths:**
- Simple to implement
- Easy for customers to use
- Stateless - no session management needed

**Weaknesses:**
- Keys don't expire (unless explicitly rotated)
- No fine-grained permissions - one key = full account access
- If leaked, attacker has full access until key is revoked
- No built-in mechanism for revoking compromised keys quickly

🔧 **NOC Tip:** When investigating security incidents, check API key access logs. Keys used from unusual IP addresses (different country than customer) or at unusual times (off-hours for that customer's timezone) suggest compromise.

### OAuth 2.0 and JWT Tokens: Modern API Authentication

OAuth 2.0 provides token-based authentication with scopes and expiration:

**The Flow:**
1. Customer authenticates with credentials to auth server
2. Auth server returns access token (JWT) and refresh token
3. Customer includes access token in API requests
4. Token expires after short time (15-60 minutes)
5. Refresh token gets new access token without re-authenticating

**JWT Structure:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0b21lcjEyMyIsInNjb3BlcyI6WyJ2b2ljZSIsIm1lc3NhZ2luZyJdLCJleHAiOjE3MDg2MDE2MDB9.signature

Header: {alg: "HS256", typ: "JWT"}
Payload: {sub: "customer123", scopes: ["voice", "messaging"], exp: 1708601600}
Signature: HMAC(header + payload, secret)
```

**Advantages:**
- Tokens expire automatically - reduces blast radius of compromise
- Scopes limit permissions - one token can't do everything
- Self-contained - server can validate token without database lookup (if using signed JWTs)
- Refresh tokens allow sessions without storing passwords

### Mutual TLS (mTLS): Certificate-Based Auth

For server-to-server communication (like SIP trunking between carriers), mutual TLS provides strong authentication:

**How it works:**
1. TLS handshake begins
2. Server presents its certificate (normal TLS)
3. Server requests client certificate
4. Client presents its certificate
5. Both sides validate each other's certificates against trusted CAs

**Benefits:**
- No passwords to leak
- Strong cryptographic authentication
- Automatic - no user interaction
- Standard for B2B telecom interconnections

**Challenges:**
- Certificate management complexity (Lesson 136)
- Clock sync required (certs have validity windows)
- Revocation is complex

## Role-Based Access Control (RBAC)

RBAC assigns permissions to roles, then assigns roles to users:

**Roles:**
- **NOC Level 1**: View dashboards, acknowledge alerts, execute runbooks
- **NOC Level 2**: Same as L1 + restart services, modify non-critical config
- **NOC Level 3**: Same as L2 + deploy changes, modify critical config
- **NOC Manager**: All permissions + user management

**Benefits:**
- Permission changes update all users with that role
- Easier to audit who can do what
- Simplifies onboarding (assign role rather than individual permissions)

## Audit Logging: Tracking Who Did What

Every sensitive action should be logged:

```json
{
  "timestamp": "2026-02-22T14:32:00Z",
  "user": "noc-eng-jane",
  "role": "noc-level-2",
  "action": "service_restart",
  "target": "sip-proxy-dc1-03",
  "source_ip": "203.0.113.50",
  "result": "success",
  "reason": "Incident #4421 - memory leak"
}
```

**Why audit logs matter:**
- Post-incident review: who made changes leading to an incident?
- Compliance: regulations often require audit trails
- Security: detection of unauthorized access
- Training: review actions taken during incidents

🔧 **NOC Tip:** When investigating incidents, audit logs show if infrastructure changes occurred before the problem started. A service restart followed by errors suggests the restart or a deployment was the cause.

## Authentication in NOC Tools

### Grafana
- Multiple auth options: LDAP, OAuth, SAML
- Granular permissions: can view vs. can edit
- Datasource permissions: limit who can query which databases

### Kubernetes
- kubeconfig files contain credentials
- RBAC: roles and rolebindings control permissions
- Service accounts for automated processes

### SSH
- Key-based auth preferred over passwords
- Authorized_keys file controls access
- Different keys for different environments (prod vs. staging)

### Consul
- ACL tokens control access to service discovery
- Policies define what each token can do

## Real-World Scenario: The Over-Permissioned API Key

A junior engineer creates an API key for a reporting script. The key has full account permissions "because it was easier than figuring out the right scopes."

Three months later, the key is leaked in a public GitHub repository. An attacker finds it within hours and:
1. Makes unauthorized international calls ($23,000 in 6 hours)
2. Provisions premium-rate numbers
3. Updates routing to send all traffic to expensive destinations

**Root cause:** Over-provisioned access. The reporting script only needed "view CDRs" permission but had full account access.

**Response:**
1. Revoke the compromised key immediately
2. Audit all API keys for over-provisioning
3. Implement policy: keys must have minimum required permissions
4. Create key rotation schedule (90 days)
5. Add monitoring for keys used from unexpected IP addresses

**Lessons:**
- Least privilege principle: give minimum permissions needed
- Regular audit of key permissions
- Monitoring unusual key usage patterns

---

**Key Takeaways:**
1. Authentication proves identity; authorization determines permissions - both are required
2. API keys are simple but provide unlimited access - prefer OAuth/JWT with scopes and expiry
3. Mutual TLS provides strong B2B authentication but adds certificate management complexity
4. RBAC simplifies permission management - assign roles, not individual permissions
5. Audit logs are essential for incident review, compliance, and security - log every sensitive action
6. Follow least privilege principle - over-provisioned credentials amplify the damage when compromised

**Next: Lesson 138 - Network Segmentation and Zero Trust Principles**
