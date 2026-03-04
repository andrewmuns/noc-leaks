# Lesson 151: SIP Registration Attacks and Overs Detection
**Module 5 | Section 5.1 - Network Security**
**⏱ ~7 min read | Prerequisites: Lesson 134**

---

## Registration Attacks: The Gateway to Fraud

SIP registration is the authentication gatekeeper of VoIP. If an attacker can successfully REGISTER, they can make calls. Registration attacks are the first phase of most toll fraud attempts - attackers brute-force credentials by sending thousands of REGISTER requests with different passwords.

Understanding registration attack patterns helps NOC engineers detect and block attacks before they succeed.

## Registration Attack Types

### Brute-Force Attacks
The attacker has a username and tries many passwords:

```
REGISTER sip:telnyx.com SIP/2.0
Via: SIP/2.0/UDP 203.0.113.50:5060
Authorization: Digest username="customer123", realm="telnyx.com", nonce="abc", response="..."
```

Each REGISTER includes a digest authentication response. The attacker tries different passwords to see which one generates the correct hash.

### Credential Stuffing
Attackers use credentials leaked from other breaches. Instead of guessing passwords, they try known username/password pairs from compromised databases. This is more efficient than brute-forcing because the credentials might work on multiple services.

### User Enumeration
Before brute-forcing passwords, attackers often try to discover valid usernames by sending REGISTERs with common usernames and observing responses:
- 401 Unauthorized = valid username (but wrong password)
- 404 Not Found = username doesn't exist

This narrows down which accounts to target.

## Recognizing Scanner Signatures

Attack tools leave signatures. Look for:

### User-Agent Strings
- **friendly-scanner**: The most common SIP scanner
- **sipvicious**: Well-known penetration testing tool (also used by attackers)
- **sipcli**: Another popular scanner
- **Custom/generic agents**: "Mozilla/5.0" or "SIP Client" doing suspicious things

### Request Patterns
- OPTIONS requests without prior interaction (discovery scanning)
- REGISTER attempts to many different usernames from a single IP
- Rapid requests from a single source (10+ per second)
- Requests to non-existent users (user enumeration)

🔧 **NOC Tip:** Create a Graylog query for "friendly-scanner" or "sipvicious" in User-Agent headers. Even if the attacks fail, the scanning activity reveals hostile IP ranges that should be monitored or blocked.

## Fail2ban for SIP

Fail2ban monitors log files and blocks IPs that exhibit attack patterns. For SIP:

```ini
# /etc/fail2ban/filter.d/sip-auth.conf
[Definition]
failregex = REGISTER.* sip:.* sip:.* 401
            INVITE.* sip:.* sip:.* 401
            REGISTER.* sip:.* sip:.* 403
            INVITE.* sip:.* sip:.* 403
ignoreregex =
```

```ini
# /etc/fail2ban/jail.local
[sip-auth]
enabled = true
port = 5060,5061
filter = sip-auth
logpath = /var/log/asterisk/full
maxretry = 5
findtime = 60
bantime = 3600
```

This blocks IPs for 1 hour after 5 failed auth attempts within 60 seconds.

The trade-off: false positives. A customer with a misconfigured PBX retrying bad credentials gets blocked. Monitor Fail2ban blocks and have an unblock procedure.

## Rate Limiting Across the Stack

Multiple layers of rate limiting provide defense in depth:

### Network Layer (iptables)
```bash
# Limit UDP packets to SIP ports
iptables -A INPUT -p udp --dport 5060 -m limit --limit 50/second -j ACCEPT
iptables -A INPUT -p udp --dport 5060 -j DROP
```

### Application Layer (SIP Proxy)
Per-IP request limits:
- Max 10 REGISTER attempts per minute per IP
- Max 100 total SIP messages per minute per IP
- Account lockout after 5 failed REGISTER attempts

### Geo-Blocking
If your platform serves primarily US customers, blocking or rate-limiting SIP traffic from high-risk countries reduces attack surface. Trade-offs include:
- Legitimate customers traveling get blocked
- Attackers use VPNs/proxies in allowed countries

## Overs Detection: Monitoring Contract Limits

"Overs" refers to traffic exceeding contracted limits - both a security and billing issue. Detection includes:

### Traffic Volume Overs
- Calls Per Second exceeding contracted rate
- Concurrent calls exceeding trunk capacity
- Messages per second exceeding messaging limits

### Destination Overs
- International calling not purchased by customer
- Premium number blocks outside allowed list
- High-cost destinations beyond configured limits

### Time-Based Alerts
- Off-hours usage for customers with time restrictions
- Weekend usage for business-only trunks

## Real-World Scenario: The Weekend Scanner

**Saturday 3:00 AM**: Monitoring shows 15,000 REGISTER requests in the last hour from a single IP range in Eastern Europe - all targeting different usernames, all failing authentication.

**Investigation:**
- User-Agent: "friendly-scanner"
- Target: Customer accounts across multiple trunks
- Pattern: User enumeration followed by credential stuffing
- No successful authentications yet

**Response:**
1. **Immediate**: Add source IP range to deny list
2. **Monitor**: Watch for same pattern from new IPs (attackers rotate)
3. **Review**: Check if any credentials were successfully guessed (none found)
4. **Alert customers**: Notify affected customers of scan attempt, recommend credential review
5. **Strengthen**: Enable Fail2ban on all edge proxies, lower thresholds

**Result**: Attack blocked before any credentials compromised. Attackers moved on to another target within hours.

🔧 **NOC Tip:** Registration attacks are common background noise on internet-facing SIP - expect thousands of attempts daily. The key is ensuring your defenses catch them before any authentication succeeds. Log analysis should show 0% success rate for scanner traffic.

## Building a Registration Attack Dashboard

Key metrics:

```promql
# REGISTER requests rate by source IP
sum by (source_ip) (rate(sip_requests_total{method="REGISTER"}[5m]))

# 401 Authentication Required response rate
rate(sip_responses_total{status_code="401"}[5m])

# Authentication success vs failure ratio
rate(sip_auth_success_total[5m]) / rate(sip_auth_attempts_total[5m])

# Unique usernames attempted per source IP
count by (source_ip) (sip_register_username)
```

Alert on:
- 401 rate >100 per minute from single IP
- Authentication success rate <50% (suggests attacks mixed with legitimate)
- More than 20 unique usernames attempted from single IP in 10 minutes

---

**Key Takeaways:**
1. SIP registration attacks are the gateway to toll fraud - detect them before credentials are compromised
2. Browser signatures like "friendly-scanner" and "sipvicious" reveal attack tools in User-Agent headers
3. Fail2ban provides automatic IP blocking but requires tuning to avoid false positives
4. Rate limiting at network, application, and account layers provides defense in depth
5. Monitor authentication success ratios - attacks show as high failure rates
6. Registration attacks are constant background noise - ensure your success rate for suspicious sources is 0%

**Next: Lesson 136 - TLS Certificate Management for NOC Engineers**
