# Lesson 65: Microsoft Teams and Zoom Phone Integration

**Module 1 | Section 1.19 — Programmable Voice**
**⏱ ~6min read | Prerequisites: Lesson 50 (SIP Call Flow), Lesson 52 (SIP Trunking)**

---

## Introduction

Enterprise customers increasingly use **Microsoft Teams** and **Zoom Phone** as their PBX. Rather than using Microsoft's or Zoom's own PSTN calling plans, many enterprises bring their own carrier (BYOC) — and that carrier is often Telnyx. This lesson covers how Telnyx integrates with Teams Direct Routing and Zoom Phone BYOC, and what breaks.

---

## Microsoft Teams Direct Routing

### What Is Direct Routing?

Direct Routing connects Microsoft Teams to the PSTN via a third-party SIP trunk (Telnyx) through a **Session Border Controller (SBC)**:

```
PSTN ←→ Telnyx SIP Trunk ←→ SBC ←→ Microsoft Teams
                                     (Microsoft 365 Cloud)
```

### Architecture

```
                    ┌─────────────────────────┐
                    │   Microsoft 365 Cloud    │
                    │                          │
                    │   Teams Phone System     │
                    │         │                │
                    │    SIP (TLS:5061)        │
                    └─────────┬───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │   SBC (Session Border    │
                    │   Controller)            │
                    │   - AudioCodes           │
                    │   - Ribbon               │
                    │   - Oracle               │
                    │   - Telnyx (virtual SBC) │
                    └─────────┬───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │   Telnyx SIP Trunk       │
                    │   sip.telnyx.com         │
                    └─────────┬───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │        PSTN              │
                    └─────────────────────────┘
```

### SBC Requirements

```
Required:
  ✓ Public IP address (or FQDN resolvable from Microsoft)
  ✓ TLS certificate from a trusted CA (not self-signed)
  ✓ SIP over TLS on port 5061 (Microsoft requirement)
  ✓ SRTP for media encryption
  ✓ Supports SIP OPTIONS keepalive
  ✓ Codec: G.711 (PCMU/PCMA) or Opus

Certificate requirements:
  - Must include SBC FQDN in SAN (Subject Alternative Name)
  - Issued by: DigiCert, Comodo, GlobalSign, Let's Encrypt, etc.
  - Microsoft maintains an approved CA list
```

🔧 **NOC Tip:** The #1 Teams Direct Routing failure is **certificate issues**. If calls fail with SIP 403 or TLS handshake errors, check: (1) certificate expiry, (2) FQDN matches SAN, (3) CA is on Microsoft's approved list. `openssl s_client -connect sbc.customer.com:5061` will show you the cert chain.

---

### Telnyx + Teams Configuration

```
Step 1: Customer configures SBC to point to Telnyx:
        Trunk FQDN: sip.telnyx.com
        Port: 5060 (or 5061 for TLS)
        
Step 2: Customer configures SBC to point to Microsoft:
        sip.pstnhub.microsoft.com (primary)
        sip2.pstnhub.microsoft.com (secondary)
        sip3.pstnhub.microsoft.com (tertiary)
        Port: 5061 (TLS required)

Step 3: In Teams Admin Center:
        - Add SBC FQDN
        - Configure voice routing policy
        - Assign phone numbers to users
        - Set PSTN usage records
```

### Call Flow — Inbound PSTN to Teams

```
PSTN caller dials +15551234567
  → Telnyx receives call
  → Route to customer's SBC (SIP INVITE)
  → SBC translates and forwards to Microsoft
  → Microsoft routes to Teams user
  → Teams user's app rings
  → Answer → RTP media flows: PSTN ↔ Telnyx ↔ SBC ↔ Teams
```

### Call Flow — Outbound Teams to PSTN

```
Teams user dials +15559876543
  → Teams sends SIP INVITE to SBC
  → SBC routes to Telnyx SIP trunk
  → Telnyx routes to PSTN
  → RTP media flows: Teams ↔ SBC ↔ Telnyx ↔ PSTN
```

---

## Zoom Phone BYOC

### Architecture

Zoom Phone BYOC (Bring Your Own Carrier) is simpler than Teams — Zoom provides a managed SBC called **Zoom Phone Peering**:

```
PSTN ←→ Telnyx SIP Trunk ←→ Zoom Peering SBC ←→ Zoom Phone
```

```
                    ┌─────────────────────────┐
                    │   Zoom Cloud             │
                    │   Zoom Phone Service     │
                    │         │                │
                    │   Zoom Peering SBC       │
                    │   (managed by Zoom)      │
                    └─────────┬───────────────┘
                              │ SIP/TLS
                    ┌─────────▼───────────────┐
                    │   Telnyx SIP Trunk       │
                    └─────────┬───────────────┘
                              │
                    ┌─────────▼───────────────┐
                    │        PSTN              │
                    └─────────────────────────┘
```

### Key Differences from Teams

```
                    Teams Direct Routing     Zoom Phone BYOC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SBC required:       Yes (customer manages)   No (Zoom provides)
Certificate:        Customer manages         Zoom manages
TLS:                Required (5061)          Required
Media:              SRTP                     SRTP
Peering:            Via customer SBC         Direct peering
Complexity:         High                     Medium
Troubleshooting:    SBC is the middle layer  Direct Telnyx ↔ Zoom
```

### Zoom BYOC Setup

```
Step 1: In Zoom Admin Portal:
        - Enable BYOC
        - Configure Telnyx as carrier
        - Provide Telnyx SIP trunk details
        
Step 2: In Telnyx Portal:
        - Create SIP trunk connection for Zoom
        - Configure IP authentication (Zoom's peering IPs)
        - Set codecs: Opus preferred, G.711 fallback
        
Step 3: Assign numbers:
        - Port or assign Telnyx numbers
        - Map numbers to Zoom users/auto-attendants
```

🔧 **NOC Tip:** Zoom BYOC peering uses specific IP ranges that must be whitelisted in Telnyx. If calls suddenly fail, check if Zoom updated their peering IPs. Zoom publishes their IP ranges at `https://assets.zoom.us/docs/ipranges/Zoom.txt`.

---

## Troubleshooting Registration and Call Failures

### Teams: SBC Registration Issues

```
Symptom: SBC shows "offline" in Teams Admin Center

Check:
  1. DNS: nslookup sbc.customer.com → must resolve to SBC public IP
  2. Port: telnet sbc.customer.com 5061 → must be open
  3. TLS:  openssl s_client -connect sbc.customer.com:5061
  4. SIP:  OPTIONS from Microsoft → SBC must respond 200 OK
  5. Cert: Verify SAN includes sbc.customer.com
```

### Common SIP Error Codes in Teams/Zoom Context

```
SIP 401/407  — Authentication failure
              Teams: SBC not authenticating properly with Microsoft
              Fix: Check SBC configuration for Microsoft authentication

SIP 403      — Forbidden
              Teams: Certificate not trusted, or number not authorized
              Zoom: IP not in whitelist

SIP 404      — User not found
              Number not assigned to a Teams/Zoom user
              Fix: Verify number assignment in admin portal

SIP 480      — Temporarily unavailable
              Teams/Zoom user offline or DND
              
SIP 488      — Not acceptable here
              Codec mismatch between Telnyx and SBC/Zoom
              Fix: Ensure G.711 or Opus is offered

SIP 503      — Service unavailable
              SBC overloaded or Microsoft/Zoom service issue
              Fix: Check SBC health, Microsoft/Zoom status page
```

### One-Way Audio

```
Symptom: PSTN caller hears Teams user, but Teams user hears silence

Root cause (usually): NAT/firewall blocking inbound RTP to SBC

Debug:
  1. Capture SDP from both legs of the call
  2. Compare media IPs — is the SBC advertising a private IP?
  3. Check SBC NAT traversal settings
  4. Verify firewall allows UDP ports for RTP (typically 10000-60000)
```

🔧 **NOC Tip:** One-way audio in Teams calls is almost always an SBC NAT configuration issue. The SBC must advertise its public IP in SDP. If you see `c=IN IP4 192.168.x.x` in the SDP, that's the problem. The SBC needs to rewrite this to its public IP.

---

## Real-World NOC Scenario

**Scenario:** Enterprise customer on Teams Direct Routing reports all outbound calls failing since this morning with SIP 403.

**Investigation:**

1. Check SBC status in Teams Admin — shows "online" ✓
2. Check Telnyx SIP trunk — INVITE arriving, returning 403
3. Why 403 from Telnyx? Check authentication — SBC is sending from an IP not in the customer's Telnyx IP whitelist
4. Customer's ISP changed their public IP overnight
5. **Fix:** Update IP authentication in Telnyx connection settings

```bash
# Check recent SIP logs for the customer's trunk
# Look for 403 responses and the source IP
curl "https://api.telnyx.com/v2/connections/conn_abc123/logs?filter[status]=403" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Key Takeaways

1. **Teams Direct Routing requires a customer-managed SBC** — it's the most complex integration point
2. **Zoom BYOC is simpler** — Zoom provides the peering SBC, reducing customer complexity
3. **TLS certificates are the #1 failure point** for Teams — expiry, wrong CA, FQDN mismatch
4. **One-way audio = NAT issue** in 90% of cases — check SDP for private IPs
5. **IP changes break authentication** — ISP changes, cloud migrations can cause sudden 403 errors
6. **Always check both legs** — Telnyx ↔ SBC and SBC ↔ Microsoft/Zoom are separate failure domains
7. **Codecs must match** — G.711 is the safe common denominator; Opus preferred for Teams

---

**Next: Lesson 191 — IoT SIM Cards and Cellular Connectivity**
