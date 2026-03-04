---
title: "NAT Fundamentals — How and Why NAT Works"
description: "Learn about nat fundamentals — how and why nat works"
module: "Module 1: Foundations"
lesson: "28"
difficulty: "Intermediate"
duration: "7 minutes"
objectives:
  - Understand nat fundamentals — how and why nat works
slug: "nat-fundamentals"
---

## Why NAT Exists

NAT was never designed to be a security feature — it was created because IPv4 address space ran out. The idea was simple: let multiple devices share a single public IP address. But this "quick fix" became permanent infrastructure, creating both problems and accidental benefits.

---

## How NAT Works

### The Basic Translation Table

When a device behind NAT sends a packet:

1. **Outbound packet:** Source IP is private (e.g., `192.168.1.100:45678`)
2. **NAT device rewrites:** Source IP to public IP, source port to unique port
3. **Entry created:** `192.168.1.100:45678` ↔ `203.0.113.5:61234`
4. **Return traffic:** When response arrives at `203.0.113.5:61234`, NAT looks up mapping and forwards to `192.168.1.100:45678`

```
Private Network                    Internet
192.168.1.100:45678  ------>  203.0.113.5:61234 (rewritten)
                      <------  Response to 203.0.113.5:61234
                                           ↓
                              NAT table lookup → 192.168.1.100:45678
```
slug: "nat-fundamentals"
---

## NAT Types (Critical for VoIP)

### Full Cone NAT
- Once an internal address (`iAddr:iPort`) is mapped to external (`eAddr:ePort`), **any external host** can send packets to `eAddr:ePort` and they'll reach `iAddr:iPort`
- Most permissive — VoIP works fine
- Rare in practice due to security concerns

### Restricted Cone NAT
- External host can only send to `eAddr:ePort` if internal host **first sent to that specific external IP**
- Port doesn't matter for restriction — just IP
- Better security, still VoIP-friendly

### Port Restricted Cone NAT
- External host can only send to `eAddr:ePort` if internal host **first sent to that specific external IP:port**
- More restrictive — can break some peer-to-peer protocols
- Common in home routers

### Symmetric NAT
- Each destination gets a **unique external mapping**
- Internal `192.168.1.100:45678` → External A uses `203.0.113.5:61234`
- Same internal → External B uses `203.0.113.5:57890` (different external port!)
- **Worst for VoIP** — SIP/RTP breaks without relay

> **💡 NOC Tip:**  a customer reports "one-way audio" or "can't receive calls," check their NAT type. Corporate firewalls often use Symmetric NAT, requiring TURN relay. Consumer routers are usually Port Restricted Cone.

---

## PAT (Port Address Translation)

Most NAT is actually PAT — multiple internal devices share one external IP through port differentiation:

| Internal Endpoint | External Mapping | Destination |
|-------------------|------------------|-------------|
| 192.168.1.100:45678 | 203.0.113.5:61234 | 8.8.8.8:443 |
| 192.168.1.101:34219 | 203.0.113.5:61235 | 8.8.4.4:443 |
| 192.168.1.100:45679 | 203.0.113.5:61236 | 1.1.1.1:53 |

Same external IP, different ports. Modern NAT devices can handle thousands of concurrent translations.
slug: "nat-fundamentals"
---

## NAT Timeout — The Silent Killer

NAT entries don't last forever. Typical timeouts:

| Protocol | Typical Timeout | Impact |
|----------|-----------------|--------|
| TCP | 2-4 hours (or on RST/FIN) | Long-lived connections stay up |
| UDP | 30-180 seconds | VoIP registrations need frequent refresh |
| ICMP | 10-60 seconds | Ping sessions expire quickly |

### Why This Matters for VoIP

SIP registrations typically occur every 60 seconds (`Expires: 3600`, refreshed at ~90% = 3240s). But RTP flows are UDP with long gaps during silence:

1. Call established, RTP flowing
2. Customer puts call on hold or long silence
3. 2 minutes pass with no RTP
4. NAT deletes the RTP translation entry
5. Customer resumes speaking — but RTP can't get through
6. **One-way audio** (other side can still send to the customer)

> **💡 NOC Tip:**  a customer reports audio cutting out after exactly X minutes, suspect NAT timeout. Solutions: shorter RTP keepalives (comfort noise), session timers, or optimize NAT timeouts on customer equipment.

---

## The SIP NAT Problem

SIP packets contain the internal IP in multiple places:

```sip
Via: SIP/2.0/UDP 192.168.1.100:5060;branch=...
Contact: <sip:alice@192.168.1.100:5060>
SDP:
  c=IN IP4 192.168.1.100
  m=audio 10000 RTP/AVP 0
```

The receiving server sees `192.168.1.100` — a private IP! It can't route responses or media to that. This is why NAT breaks SIP by default.

We'll cover solutions in Lessons 27-28: STUN, TURN, SIP ALG, and Session Border Controllers.
slug: "nat-fundamentals"
---

## Key Takeaways

1. **NAT was built for address conservation, not security** — but became both
2. **Four NAT types** — Full Cone, Restricted Cone, Port Restricted Cone, Symmetric. Symmetric is VoIP's enemy
3. **PAT** allows thousands of devices behind one public IP through port differentiation
4. **NAT timeout** causes silent failures — VoIP registrations and RTP need regular keepalives
5. **SIP contains private IPs** in headers and SDP — NAT alone breaks SIP without additional techniques

---

**Next: Lesson 27 — NAT Traversal for SIP and RTP — The Core Problem**
