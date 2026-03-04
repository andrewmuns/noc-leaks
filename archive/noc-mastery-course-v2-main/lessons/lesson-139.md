# Lesson 139: Common Failure Pattern — DNS and Certificate Failures
**Module 4 | Section 4.5 — Failure Patterns**
**⏱ ~6 min read | Prerequisites: Lesson 19-21, 17**

---

## Two Preventable Catastrophes

DNS failures and certificate expiry share a frustrating characteristic: they're almost always preventable, yet they cause some of the most severe outages in telecom operations. Both fail suddenly and completely — there's no graceful degradation when DNS stops resolving or a certificate expires.

## DNS Failures: When Nothing Can Find Anything

DNS is the nervous system of any distributed platform. Every service discovery query, every API call, every webhook delivery, every SIP connection starts with a DNS lookup. When DNS fails, *everything* fails.

### Common DNS Failure Modes

**Internal DNS resolver overload**: Your cluster's CoreDNS (Lesson 90) handles thousands of queries per second. If CoreDNS pods are under-resourced or crash, every Kubernetes service discovery query fails. Services can't find each other, health checks fail, and Consul marks everything as critical.

**Upstream DNS failure**: If your authoritative DNS provider has an outage, external clients can't resolve your SIP endpoints. Customers' PBXes fail to reach `sip.telnyx.com`, and all inbound calls fail. Cached records may work until TTL expires — then they fail too.

**DNS configuration error**: A typo in a DNS record (wrong IP address, missing SRV record) causes traffic to route to the wrong place — or nowhere. This often happens during migrations when DNS records are updated.

**DNSSEC validation failure**: If DNSSEC is enabled and a key rollover goes wrong, validators reject your DNS records as invalid. The records exist and are correct, but validators refuse them.

🔧 **NOC Tip:** When you suspect DNS issues, test from multiple vantage points. `dig @8.8.8.8 sip.telnyx.com` tests Google's resolver. `dig @internal-dns service.consul` tests internal DNS. If one works and the other doesn't, you've localized the problem.

### DNS Failure Investigation

```bash
# Check if CoreDNS pods are running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Test internal resolution
kubectl exec -it debug-pod -- nslookup service.namespace.svc.cluster.local

# Test external resolution with timing
dig +stats sip.telnyx.com

# Check for SERVFAIL (resolver failure)
dig sip.telnyx.com | grep status

# Trace the full resolution path
dig +trace sip.telnyx.com
```

### DNS Caching: The Double-Edged Sword

DNS caching is both a protection and a problem. During a DNS outage, cached records continue working until their TTL expires — giving you a window to fix things. But after a fix, long TTLs mean clients continue using stale (possibly wrong) records.

For SIP services, TTLs are typically kept between 60-300 seconds — short enough for reasonably fast failover, long enough to not overwhelm DNS servers.

🔧 **NOC Tip:** After fixing a DNS issue, don't forget about caching. Clients won't see the fix until their cached TTL expires. If the TTL was 300 seconds, expect up to 5 minutes of continued issues after the fix is deployed.

## Certificate Failures: The Instant Outage

TLS certificate expiry is the #1 preventable outage cause across the industry. When a certificate expires, every TLS handshake fails instantly. There's no warning to end users — connections simply refuse.

### Why Certificates Expire

TLS certificates have a maximum validity period (currently 398 days for publicly trusted certificates, moving toward 90 days). This is by design — it limits the damage from compromised keys and forces periodic renewal.

But certificates don't expire gradually. They work perfectly until the exact expiry timestamp, then fail completely. One minute your SIP over TLS is handling 10,000 concurrent calls; the next minute, every new TLS handshake is rejected.

### Certificate Failure Modes

**Expired certificate**: The most common. The certificate's `notAfter` timestamp has passed. Clients reject it immediately.

**Missing intermediate certificate**: The server presents its leaf certificate but not the intermediate CA certificate. Browsers may work (they often cache intermediates), but SIP clients and API clients fail because they can't build the trust chain.

**Wrong certificate for the hostname**: The certificate is for `api.telnyx.com` but the server is `sip.telnyx.com`. SNI mismatch causes handshake failure.

**Clock skew**: If a server's system clock is wrong, a perfectly valid certificate appears expired (or not-yet-valid). NTP synchronization failures cause this.

### Diagnosing Certificate Issues

```bash
# Check certificate expiry and chain
openssl s_client -connect sip.telnyx.com:5061 -servername sip.telnyx.com </dev/null 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# Check for missing intermediates
openssl s_client -connect sip.telnyx.com:5061 -servername sip.telnyx.com </dev/null 2>&1 | grep -i "verify"

# Check system clock
date -u
timedatectl status
```

### Real-World Scenario: The Midnight Expiry

It's 2:00 AM Saturday. An alert fires: "TLS handshake failures spiking on SIP ingress." You check Grafana — TLS error rate went from 0 to 100% at exactly 2:00 AM. No deployments, no configuration changes.

You check the certificate:
```
notBefore=Feb 22 00:00:00 2025 GMT
notAfter=Feb 22 02:00:00 2026 GMT
```

The certificate expired at exactly 2:00 AM. The automated renewal system (Let's Encrypt / ACME) failed silently three days ago because the DNS challenge couldn't complete. Nobody noticed the renewal failure alert because it was a warning, not critical.

**Immediate fix**: Manually trigger certificate renewal or install a backup certificate.
**Long-term fix**: Escalate certificate renewal failure alerts to critical severity.

🔧 **NOC Tip:** Certificate expiry monitoring should alert at 30 days, 14 days, 7 days, 3 days, and 1 day before expiry — with increasing severity at each threshold. If you're seeing the 3-day alert, something is wrong with automated renewal.

## Proactive Monitoring

### DNS Monitoring
- Monitor DNS resolution time and success rate from multiple locations
- Alert on SERVFAIL or NXDOMAIN for critical service records
- Monitor CoreDNS pod health and query latency
- Test SRV and NAPTR records specifically (SIP depends on them)

### Certificate Monitoring
- Use Prometheus blackbox exporter to probe TLS endpoints
- Monitor certificate expiry with `ssl_certificate_expiry_seconds` metric
- Track ACME renewal status — alert on renewal failures, not just approaching expiry
- Monitor NTP synchronization status on all servers

## The Compound Failure

DNS and certificate failures sometimes combine. Consider: your certificate auto-renewal uses DNS-01 challenge (proving domain ownership via a DNS TXT record). If DNS is misconfigured, the ACME challenge fails, renewal fails, and eventually the certificate expires. Two preventable issues compounding into an outage.

---

**Key Takeaways:**
1. DNS failures cause total outages because every service depends on name resolution — test from multiple vantage points when investigating
2. Certificate expiry is instantaneous and complete — there's no graceful degradation
3. Both failures are preventable with proactive monitoring and alerting
4. DNS caching provides a temporary buffer during outages but delays recovery visibility
5. Missing intermediate certificates cause failures that are easy to miss in testing but break production clients
6. Monitor both DNS health and certificate expiry with escalating severity alerts

**Next: Lesson 124 — Common Failure Pattern: Deployment-Related Failures**
