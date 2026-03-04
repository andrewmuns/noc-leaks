# Lesson 152: TLS Certificate Management for NOC Engineers
**Module 5 | Section 5.1 - Network Security**
**⏱ ~8 min read | Prerequisites: Lessons 17, 131**

---

## Certificates: The Silent Killers

TLS certificate expiry is the leading preventable cause of production outages. Unlike gradual capacity exhaustion or partial failures, certificate expiry is instant and total - one minute connections work, the next minute they fail completely. For a telecom platform, expired certificates on SIP over TLS endpoints mean registration failures, call setup failures, and total customer impact.

Certificate management should be a core NOC responsibility because you're the ones who discover the problem at 3 AM when customers can't connect.

## Understanding Certificate Chains

### The Three-Part Structure

A valid TLS connection requires trusting a chain:

```
Leaf Certificate (your server's cert)
    ↓ signed by
Intermediate CA Certificate
    ↓ signed by
Root CA Certificate (trusted by browsers/clients)
```

**Leaf Certificate**: Identifies your server (sip.telnyx.com). Contains public key and subject. Valid for 90-398 days.

**Intermediate Certificate**: The CA that signed your leaf. Browsers/clients don't trust intermediate CAs directly, but they trust roots that have signed intermediates.

**Root Certificate**: Pre-installed in browsers and operating systems. Self-signed. Never changes. Clients have these built-in.

### The Chain Problem

Servers must present the full chain (leaf + intermediate). If you only present the leaf, clients that don't already have the intermediate cached will fail to validate the chain. This causes intermittent failures - some clients work (have cached intermediate), others fail.

🔧 **NOC Tip:** When troubleshooting TLS failures, always check the certificate chain. Use `openssl s_client -connect host:port -showcerts | head -30` to see what chain the server presents. Missing intermediates cause mysterious intermittent failures that are hard to reproduce.

## Certificate Monitoring Essentials

### Expiry Monitoring

Certificates have a fixed lifetime. Track:

```bash
# Check certificate expiry
openssl s_client -connect sip.telnyx.com:5061 -servername sip.telnyx.com </dev/null 2>/dev/null | openssl x509 -noout -dates

# Check days remaining
echo | openssl s_client -connect sip.telnyx.com:5061 2>/dev/null | openssl x509 -noout -enddate | awk -F= '{print $2}' | xargs -I {} date -d "{}" +%s | xargs -I {} echo "{} - $(date +%s)" | bc | xargs -I {} echo "{}/86400" | bc
```

Monitor with escalating severity:
- **60 days**: Info notification for tracking
- **30 days**: Warning - renewal should be initiated
- **14 days**: Alert - renewal overdue
- **7 days**: Critical alert - this gets noisy, investigate immediately
- **1 day**: Page on-call engineer - emergency renewal needed

### Automation Monitoring

Automated renewal (Let's Encrypt, ACME) isn't automatic success monitoring. Track:
- Last successful renewal timestamp
- Renewal failure rate
- ACME challenge success/failure

A renewal that has been failing for 3 days is an incident waiting to happen.

## prometheus blackbox exporter

The blackbox exporter probes endpoints and exports certificate metrics:

```yaml
# blackbox.yml
modules:
  tls_connect:
    prober: tcp
    tcp:
      tls: true
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'certificate_expiry'
    metrics_path: /probe
    params:
      module: [tls_connect]
    static_configs:
      - targets:
        - sip.telnyx.com:5061
        - api.telnyx.com:443
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

Key metrics:
- `probe_ssl_earliest_cert_expiry`: Unix timestamp of expiry
- `probe_success`: Whether probe succeeded

Grafana alert:
```promql
(probe_ssl_earliest_cert_expiry - time()) / 86400 < 7
```

🔧 **NOC Tip:** Set up blackbox exporter for all TLS endpoints - SIP over TLS, API HTTPS, webhook endpoints. Certificate expiry can hit any of them, and blackbox catches it before customers do.

## SIP over TLS (SIPS) Specifics

SIP over TLS on port 5061 encrypts signaling. Certificate requirements:

### Certificate Subject
- Must match the hostname customers connect to
- Wildcard certificates (*.telnyx.com) work for subdomains
- Subject Alternative Names (SANs) can cover multiple hostnames

### SIP Client Validation
Some SIP clients are stricter than web browsers:
- Require complete certificate chain
- May not support newer signature algorithms
- Often require specific TLS versions (TLS 1.2 vs 1.3)

### Mutual TLS (mTLS)
For carrier interconnections, mutual TLS provides authentication:
- Server presents certificate (as normal)
- Client also presents certificate
- Both sides validate each other's certificates

When mTLS breaks, both server and client certificate expiry can cause failures.

## Common Certificate Failures

### 1. Expired Certificate
Symptoms: All TLS connections fail immediately
Diagnosis: `openssl s_client` shows "certificate has expired"
Fix: Emergency renewal or restore from backup cert

### 2. Wrong Hostname
Symptoms: Clients reject certificate with hostname mismatch
Diagnosis: Certificate valid but for wrong domain
Fix: Deploy correct certificate or update client's target hostname

### 3. Missing Intermediate
Symptoms: Intermittent failures; some clients work, others fail
Diagnosis: `openssl s_client -showcerts` shows only one certificate
Fix: Configure server to send full chain (leaf + intermediate)

### 4. Clock Skew
Symptoms: Certificate valid but rejected as expired/not-yet-valid
Diagnosis: Server or client system time is wrong
Fix: Fix NTP synchronization

### 5. Weak Signature Algorithm
Symptoms: Modern clients reject certificate
Diagnosis: Certificate uses SHA-1 (deprecated) or RSA < 2048 bits
Fix: Replace with certificate using SHA-256 and RSA 2048+

🔧 **NOC Tip:** When TLS failures are reported, check system time first. It's the easiest fix - `timedatectl status` on Linux. Wrong time breaks all certificate validation, making valid certs appear expired.

## Real-World Scenario: The Midnight Certificate Expiry

**2:00 AM Saturday**: Alert fires - "SIP TLS handshake failures spiking." 

**Investigation:**
- Grafana shows TLS error rate jumping from 0.1% to 100% at exactly 2:00 AM
- No deployments or config changes
- Check certificate:
  - notBefore: Feb 22, 2025 00:00:00 GMT
  - notAfter: Feb 22, 2026 02:00:00 GMT
  
Certificate expired at exactly 2:00 AM.

**Root cause:**
- Let's Encrypt auto-renewal had been failing since Wednesday
- ACME DNS-01 challenge failing due to stale DNS API credentials
- Renewal failure alerts were "warning" severity, not critical
- Nobody acted on warning alerts

**Response:**
1. Emergency manual certificate generation using certbot
2. Deploy new certificate to load balancers
3. Validate: TLS handshake success rate returns to normal
4. Fix DNS API credentials so renewal works
5. Escalate renewal failure alerts to critical severity

**Cost:** 23 minutes of 100% SIP registration failure for TLS-based customers.

## Certificate Runbook Checklist

When certificate incidents occur:

1. **Verify expiry**: Confirm certificate is actually expired
2. **Check chain**: Verify full chain is being presented
3. **Check clock**: Verify system time is correct on both ends
4. **Emergency renewal**: Generate new certificate if needed
5. **Deploy**: Update load balancers, proxies, servers
6. **Validate**: Test connection from multiple clients
7. **Root cause**: Why did renewal fail? Fix the process.
8. **Prevent recurrence**: Escalate monitoring if needed

---

**Key Takeaways:**
1. Certificate expiry causes instant, total outages - the #1 preventable outage type
2. Servers must present the full certificate chain (leaf + intermediate) - missing intermediates cause intermittent failures
3. Monitor certificate expiry with escalating alerts: 30/14/7/1 days before expiry, increasing severity
4. Use blackbox exporter to proactively monitor all TLS endpoints
5. Check system clock first when troubleshooting TLS failures - wrong time breaks all validation
6. Monitor automated renewal success, not just expiry - renewal failures need action before expiry

**Next: Lesson 137 - Authentication and Authorization Patterns**
