# Lesson 44: SIP Registration — How Endpoints Make Themselves Reachable
**Module 1 | Section 1.10 — SIP Protocol Deep Dive**
**⏱ ~7 min read | Prerequisites: Lesson 41**

---

## The Problem Registration Solves

In the PSTN, your phone number is physically wired to a specific copper pair that terminates at a specific switch port. The network *always* knows where you are. In SIP, endpoints move — a softphone on a laptop might be at a coffee shop today and the office tomorrow. Its IP address changes. How does the network find it?

**Registration** is SIP's answer. An endpoint tells a registrar: "I'm user@example.com, and right now you can reach me at this IP:port." The registrar stores this binding and uses it to route incoming calls. Without registration, inbound calls have nowhere to go.

---

## The REGISTER Transaction

### Address of Record vs. Contact

Two concepts are central to registration:

- **Address of Record (AOR):** Your public identity — like `sip:alice@telnyx.com`. This is what callers dial. It's stable and permanent.
- **Contact:** Your current physical location — like `sip:alice@192.168.1.50:5060`. This changes whenever your network changes.

Registration creates a **binding** between the AOR and one or more Contacts. When a call arrives for the AOR, the registrar looks up the current Contact(s) and forwards the INVITE there.

### The REGISTER Message

```
REGISTER sip:telnyx.com SIP/2.0
Via: SIP/2.0/UDP 192.168.1.50:5060;branch=z9hG4bK776
From: <sip:alice@telnyx.com>;tag=abc123
To: <sip:alice@telnyx.com>
Contact: <sip:alice@192.168.1.50:5060>;expires=3600
Call-ID: reg-unique-id@192.168.1.50
CSeq: 1 REGISTER
Expires: 3600
```

Key observations:
- The **Request-URI** is the domain, not a specific user — the registrar is a domain-level service
- **From** and **To** are the same — you're registering yourself
- **Contact** is where you want to receive calls
- **Expires** is how long the binding should last (in seconds)

### The Authentication Dance

Most registrars require authentication. The flow is:

1. Client sends REGISTER (no credentials)
2. Registrar responds **401 Unauthorized** with a `WWW-Authenticate` header containing a nonce
3. Client recalculates REGISTER with an `Authorization` header containing the digest response (hash of username, password, nonce, realm, URI)
4. Registrar verifies the hash and responds **200 OK**

This two-step dance happens every time. The 401 is *not* an error — it's step one of authentication. (See Lesson 43 for deeper coverage.)

🔧 **NOC Tip:** If you see a customer's device sending REGISTER → getting 401 → sending REGISTER with credentials → getting another 401 → repeating forever, the credentials are wrong. The device is stuck in an auth loop. Verify username and password match the portal configuration.

---

## Registration Refresh and Expiry

Bindings don't last forever. The `Expires` header (or `expires` parameter on the Contact) sets the lifetime. Before it expires, the endpoint must re-register to keep the binding alive.

### Typical Timeline

```
t=0:     REGISTER (expires=3600)  →  200 OK
t=3000:  REGISTER (refresh)       →  200 OK    (re-registers before expiry)
t=6000:  REGISTER (refresh)       →  200 OK
t=9000:  (device crashes, no re-register)
t=9600:  Binding expires — device is now unreachable
```

Most devices re-register at 50-75% of the expiry interval to provide a safety margin. If a refresh fails, the device typically retries with exponential backoff.

### Why Expiry Matters for NAT

This is where registration intersects with NAT (Lesson 27). NAT mappings have their own timeouts — typically 30-120 seconds for UDP. If the registration interval is 3600 seconds (1 hour) but the NAT timeout is 60 seconds, the NAT mapping expires long before re-registration. When an inbound call arrives, the registrar sends the INVITE to the Contact address, but the NAT mapping is gone — the INVITE never reaches the device.

**Solutions:**
- Lower the registration interval (120-300 seconds) to keep NAT mappings alive
- Use SIP outbound (RFC 5626) with keep-alive mechanisms
- Use TCP/TLS for SIP (persistent connections survive NAT timeouts)
- Configure the NAT device with longer UDP timeouts

🔧 **NOC Tip:** When a customer reports intermittent inbound call failures ("sometimes my phone rings, sometimes it doesn't"), check the registration interval vs. likely NAT timeout. If their PBX is behind NAT with a 3600s registration interval, that's almost certainly the problem. Reduce to 120s.

---

## Multiple Registrations

A single AOR can have multiple Contact bindings — Alice might be registered on her desk phone, mobile app, and softphone simultaneously. When a call arrives, the registrar (or proxy) can fork the INVITE to all registered contacts (see Lesson 41 on forking).

Each Contact has its own expiry and can be managed independently. A REGISTER can add, update, or remove specific contacts:

- **Add/Update:** Include the Contact with a positive `expires` value
- **Remove specific:** Include the Contact with `expires=0`
- **Remove all:** Use `Contact: *` with `Expires: 0` (deregister everything)

---

## Registration Failures and Troubleshooting

### Common Failure Patterns

| Symptom | Likely Cause |
|---------|-------------|
| 401 auth loop (infinite) | Wrong username/password |
| 403 Forbidden | Account disabled, IP not in ACL, domain mismatch |
| 408 Timeout | Registrar unreachable — DNS failure, firewall, network issue |
| REGISTER succeeds but no inbound calls | NAT timeout expiring binding, or wrong Contact address |
| Intermittent registration loss | NAT timeout, flaky network, Wi-Fi power saving |

### Debugging Steps

1. **Check the SIP trace:** Is REGISTER being sent? What response comes back?
2. **Verify credentials:** Match username, password, and realm exactly
3. **Check DNS:** Can the device resolve the registrar's domain? (`dig sip.telnyx.com`)
4. **Check NAT:** Is the Contact address a private IP behind NAT? Is `rport` being used?
5. **Check timers:** Is the refresh interval appropriate for the network environment?

### Real-World Scenario

**Problem:** A customer's call center has 200 agents on softphones. Every morning around 9 AM, about 30 agents can't receive calls for 5-10 minutes, then it resolves.

**Investigation:**
1. Check registration logs — many devices show expired registrations around 8:55 AM
2. The softphones are configured with 3600s (1-hour) registration interval
3. All 200 devices registered around 8 AM when agents logged in
4. At ~9 AM, all 200 try to re-register simultaneously (registration storm)
5. The registrar or firewall becomes overwhelmed, some registrations fail or timeout
6. Devices retry with exponential backoff, eventually succeeding (5-10 minute recovery)

**Fix:** Randomize registration intervals. Instead of exactly 3600s, use 3600 ± random jitter. Most good SIP implementations do this automatically, but some don't. Also consider increasing registrar capacity if needed.

---

## Registration in Telnyx's Architecture

Telnyx supports both registered endpoints and registration-free SIP trunking:

- **Credential-based SIP trunks:** Devices register with username/password. Telnyx stores the binding and routes inbound calls to the registered Contact.
- **IP-based SIP trunks:** No registration needed. Telnyx trusts traffic from specific IP addresses. Inbound calls are sent directly to the configured IP.

The advantage of IP-based auth is simplicity (no registration dance, no refresh timers) but the disadvantage is inflexibility (the IP must be static and pre-configured). Credential-based registration supports dynamic IPs and mobile devices.

---

**Key Takeaways:**
1. Registration binds an AOR (public identity) to a Contact (current location) so inbound calls can be routed
2. The 401 challenge in REGISTER is normal — it's the first step of digest authentication, not an error
3. Registration expiry must be shorter than NAT timeout to maintain reachability through NAT devices
4. Multiple devices can register under one AOR, enabling parallel forking for incoming calls
5. Registration storms (many devices refreshing simultaneously) can overwhelm registrars — use jitter
6. IP-based SIP trunks bypass registration entirely but require static, pre-configured IP addresses
7. When inbound calls fail intermittently, always check registration status and NAT timeout alignment

**Next: Lesson 43 — SIP Authentication — Digest Auth, TLS, and IP-Based Auth**
