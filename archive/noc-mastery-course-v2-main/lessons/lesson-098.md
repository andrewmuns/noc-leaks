# Lesson 98: Regulatory Systems — STIR/SHAKEN, CNAM, and Compliance
**Module 2 | Section 2.13 — Business Systems**
**⏱ ~7min read | Prerequisites: None**
---

## Introduction

Telecommunications is one of the most regulated industries in the world. As a NOC engineer at Telnyx, you're not just keeping calls connected — you're keeping them compliant with federal mandates. **STIR/SHAKEN** combats caller ID spoofing and robocalls. **CNAM** displays caller names. Getting these wrong means regulatory enforcement, customer complaints, and the caller ID your grandma sees saying "Potential Spam" even when it's her bank.

This lesson covers the regulatory systems Telnyx operates, their failure modes, and how NOC responds when they break.

---

## Robocalls and Caller ID Spoofing

The problem: scammers spoof legitimate phone numbers to make their calls look authentic. A robocall shows as "IRS" or "Bank of America" but originates from a call center in another country. Consumers stopped answering calls, hurting legitimate businesses.

**STIR/SHAKEN** (Secure Telephone Identity Revisited / Signature-based Handling of Asserted information using toKENs) is the FCC-mandated framework to cryptographically verify caller ID authenticity.

---

## STIR/SHAKEN Attestation Levels

When a call traverses the telephone network, each carrier vouches for the origin. STIR/SHAKEN defines three attestation levels — how sure the originating carrier is that the caller is who they claim to be.

### Attestation A (Full Attestation)

The originating carrier verified the caller's identity AND authorizes their use of the calling number.

**Requirements:**
- Customer has a direct relationship with Telnyx
- Customer is authorized to use the calling number
- Telnyx verified the customer's identity (Know Your Customer/KYC)

```
Customer (verified KYC)
   │
   └──► Calling from +14155551234 (assigned by Telnyx)
        │
        └──► Attestation A → Full trust → Destinations trust the caller ID
```

### Attestation B (Partial Attestation)

The carrier verified the customer's identity, but cannot verify their authorization to use the specific number.

**Common cases:**
- Customer uses a number ported from another carrier
- Number belongs to a partner/reseller with delegated authorization
- The number was validated but not assigned by Telnyx

### Attestation C (Gateway Attestation)

The carrier knows the call came through their network, but has no relationship with the caller.

**Common cases:**
- Transit carrier receiving calls from international gateways
- Calls from a peer carrier without STIR/SHAKEN
- Wholesale voice traffic with unverified origin

| Level | Trust | Verification | Display Impact |
|-------|-------|--------------|----------------|
| A | High | Identity + Number authority | "Verified" |
| B | Medium | Identity only | "Called" or neutral |
| C | Low | Gateway only | "Potential Spam" flag likely |

🔧 **NOC Tip:** When customers complain their calls are showing as "Spam Likely" or being blocked, check the attestation level first. A customer with proper Attestation A should never see this; if they do, either (1) their account lost KYC status, (2) the number isn't properly assigned in our system, or (3) downstream carriers are misclassifying Attestation. Check the SHAKEN database and certificate status.

---

## STIR/SHAKEN Certificate Management

STIR/SHAKEN relies on a **Public Key Infrastructure (PKI)** — digital certificates that authenticate signing authorities.

### Certificate Hierarchy

```
Policy Administrator (iconectiv/STI-PA)
         │
         ├──► Service Provider Code (SPC) token issued
         │
         ▼
Certificate Authority (STI-CA)
         │
         ├──► Signs Service Provider Certificate for Telnyx
         │    (validates Telnyx as authorized signer)
         │
         └──► Telnyx operates own Private CA
                  │
                  ├──► Issues signing certificates to:
                       - Voice APIs
                       - SBC signing services
                       - SIP trunk termination points
```

### Telnyx Signing Infrastructure

1. **Certificate Authority (CA) Service:** Maintains Telnyx's service provider certificate, issues signing certificates.
2. **Identity Token Service:** Issues PASSporTs (PArtY STI Payloads with tokENsREallys) — the signed attestation tokens attached to calls.
3. **Verification Service:** Validates incoming PASSporTs from peer carriers.

### Certificate Lifecycle

| Event | Action | Monitoring |
|-------|--------|------------|
| Certificate issued | Deploy to signing services | Check expiration dates |
| Daily | Rotate signing certs | Certificate validity metric |
| 30 days before expiry | Alert renewal | Certificate_expiry_days < 30 |
| 7 days before expiry | Escalate emergency | P1 incident, manual intervention |
| Expiration | Suspended signing | Calls fail or downgrade to C-level |

🔧 **NOC Tip:** Certificate expiration is a **regulatory incident**. If Telnyx's signing certificate expires, all outbound calls get Attestation C at best, or fail to pass validation at worst. Monitor `certificate_expiry_days` with critical alerts at 30, 14, and 7 days. At 3 days, escalate to on-call director level — this is a business-critical risk.

---

## CNAM Dips: Caller Name Display

**CNAM** (Calling NAMe) provides the caller's name displayed on the called party's phone — beyond just the number.

### CNAM Database Structure

CNAM data is stored in centralized databases operated by carriers and data aggregators (TNS, Neustar/Lightbox). Unlike STIR/SHAKEN (cryptographic), CNAM is a **lookup service**.

```
Incoming Call to +14155555678
   │
   └──► Terminating Carrier → CNAM Dip Query
              │
              ▼
         CNAM Database (Neustar/TNS)
              │
              └──► Returns: "ACME CORP" or "SMITH, JOHN"
                        or "WIRELESS CALLER" (default)
```

### CNAM Data Flow

1. **Outgoing calls:** Telnyx submits CNAM updates to aggregators when customers set their caller name.
2. **Incoming calls:** Telnyx queries CNAM databases to display caller names to our customers.
3. **Propagation:** CNAM updates take 24–72 hours to propagate across all databases.

### CNAM Failures

| Failure | Impact | Response |
|---------|--------|----------|
| CNAM query timeout | Called party sees number only, not name | Retry, failover to backup provider |
| CNAM update rejected | Customer's name not displayed | Check formatting (15 char limit, allowed chars) |
| CNAM propagation delay | Updated name not showing yet | Normal 24–72h window, set expectations |
| Database outage | All CNAM lookups fail | Fail open (show number only), escalate |

🔧 **NOC Tip:** CNAM lookups are **non-blocking** in call processing. If the CNAM dip times out, the call still connects — the callee just doesn't see a name. This is why CNAM failures are often silent until customers complain. Monitor CNAM query latency and error rate proactively; don't wait for complaints.

---

## Robocall Mitigation

Beyond STIR/SHAKEN, Telnyx implements additional robocall mitigation:

### Call Analytics and Labeling

- **Honeypot numbers:** Sensor numbers that should never receive legitimate calls; any call to them is suspicious.
- **Call pattern analysis:** Sudden spikes in calls from a single source, short-duration calls, ring-no-answer patterns.
- **Customer reporting:** Consumers report spam numbers to authorities (FTC/FCC).

### Risk Scoring

Telnyx assigns a risk score to callers based on:
- STIR/SHAKEN attestation level
- Call fingerprint analysis
- Customer KYC validation
- Historical complaint data

High-risk calls may be:
- Tagged with "Spam Risk" or "Potential Fraud"
- Blocked outright
- Redirected to voicemail

🔧 **NOC Tip:** Legitimate customers occasionally get caught in robocall filters. If a customer claims their calls are being blocked: (1) Check their STIR/SHAKEN attestation — C-level attestation triggers many filters. (2) Check if their source IP or number range is flagged in honeypots. (3) Review call patterns — sudden volume spikes from a single endpoint look like robocalling.

---

## Regulatory Compliance Monitoring

### FCC Rules

- **STIR/SHAKEN mandate:** All originating voice providers must implement by June 2021; intermediate/transit by 2023.
- **Robocall mitigation:** Carriers must certify their robocall prevention plans.
- **Truth in Caller ID:** Prohibits knowingly transmitting misleading caller ID.

### Compliance Metrics to Monitor

```promql
# STIR/SHAKEN signing rate (all outbound calls should be signed)
rate(stir_shaken_signed_calls_total[5m]) / rate(outbound_calls_total[5m]) * 100
# Target: >95%

# Attestation breakdown
stir_shaken_calls_attestation_a_total
stir_shaken_calls_attestation_b_total  
stir_shaken_calls_attestation_c_total

# Certificate validity
certificate_expiry_days < 30

# CNAM query success rate
rate(cnam_queries_success_total[5m]) / rate(cnam_queries_total[5m]) * 100
# Target: >99.5%

# Reported robocall volume from our network
robocall_complaints_per_day
```

### Compliance Escalation

| Scenario | Action | Notification |
|----------|--------|--------------|
| Signing rate drops below 95% | Immediate investigation | On-call + Compliance team |
| Certificate expiration < 7 days | P1 emergency | Director level + Legal |
| Regulator inquiry received | Compliance team takes lead | Legal + Exec |
| Honeypot hits from our IP ranges | Block source, investigate customer | Security + Customer success |

---

## Monitoring and Alerting

### Critical Regulatory Alerts

```yaml
- alert: STIRSHAKenSigningRateLow
  expr: rate(stir_shaken_signed_calls_total[5m]) / rate(outbound_calls_total[5m]) < 0.95
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "STIR/SHAKEN signing rate below 95%"
    
- alert: SigningCertificateExpiring
  expr: certificate_expiry_days < 30
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "STIR/SHAKEN certificate expires in {{ $value }} days"
    
- alert: CNAMDipFailureRateHigh
  expr: rate(cnam_queries_failed_total[5m]) / rate(cnam_queries_total[5m]) > 0.01
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "CNAM lookup failure rate above 1%"
```

---

## Key Takeaways

1. **STIR/SHAKEN** cryptographically verifies caller ID — Attestation A (full trust), B (partial), C (gateway only).
2. **Attestation A requires KYC** — lost verification status = degraded trust = calls labeled "Spam Likely".
3. **Certificate expiration is a P1 regulatory risk** — monitor 30/14/7 day thresholds, escalate early.
4. **CNAM** provides caller name display via database lookups — failures are silent but customer-visible.
5. **Robocall mitigation** combines SHAKEN attestation, honeypots, and call analytics to protect consumers.
6. **Compliance monitoring** tracks signing rates, attestation breakdown, and certificate validity — maintain >95% signing rate.
7. **Regulatory incidents require immediate escalation** — FCC violations carry fines and reputation damage.

---

**Next: Lesson 89 — Number Provisioning and Porting: The Lifecycle of a Phone Number**
