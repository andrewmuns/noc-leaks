---
title: "SIP Architecture — Endpoints, Proxies, Registrars, and B2BUAs"
description: "Learn about sip architecture — endpoints, proxies, registrars, and b2buas"
module: "Module 1: Foundations"
lesson: "39"
difficulty: "Advanced"
duration: "9 minutes"
objectives:
  - Understand SIP is a text-based, HTTP-inspired signaling protocol — human-readable, making it the most debuggable telecom protocol
  - Understand UAC and UAS roles are per-transaction, not per-device — the same phone can be client and server in the same call
  - Understand Telnyx operates as a B2BUA — two independent call legs, enabling topology hiding, media control, transcoding, billing, and interoperability
  - Understand Always debug Telnyx calls as two separate legs: A-leg (customer↔Telnyx) and B-leg (Telnyx↔carrier)
  - Understand SIP addressing uses URIs resolved through DNS (NAPTR → SRV → A/AAAA), enabling load balancing and failover
slug: "sip-architecture"
---

We've spent 36 lessons building foundations — PSTN history, codecs, IP networking, RTP/RTCP, quality metrics. Now we arrive at the protocol that ties it all together: SIP — the Session Initiation Protocol. SIP is the signaling backbone of modern voice. If you work in a Telnyx NOC, you will read SIP messages every single day.

## SIP's Design Philosophy

SIP was designed in the late 1990s by the IETF, and its creators were deeply influenced by HTTP and SMTP. This is both its strength and its weakness:

**Strengths borrowed from HTTP:**
- Text-based (human-readable, easy to debug)
- Request/response model
- Header-based extensibility
- URL-based addressing (SIP URIs)
- Stateless design possibility

**Why this matters for you:** Unlike binary protocols (SS7, H.323), you can read a SIP message in a text editor or log viewer. This makes debugging accessible. You don't need a protocol decoder — you can `grep` through Graylog logs and understand what's happening.

**The weakness:** SIP carries IP addresses and ports inside its message body (SDP) and headers (Contact, Via). Unlike HTTP, where only the IP header matters for routing, SIP's content must match network reality. NAT breaks this assumption catastrophically — as we covered in Lessons 26-28.

## SIP Entities

### User Agent (UA)

The fundamental SIP entity — any device that sends or receives SIP messages. Your desk phone, softphone, PBX, or mobile app is a User Agent.

Every SIP transaction has two roles:
- **UAC (User Agent Client):** The entity initiating the request. When you place a call, your phone is the UAC.
- **UAS (User Agent Server):** The entity receiving and responding to the request. The called party's phone is the UAS.

**Critical insight:** These roles are **per-transaction**, not per-device. When you place a call, you're the UAC. When someone sends you a re-INVITE to put you on hold, you become the UAS for that transaction. The same device switches roles constantly.

### Proxy Server

A SIP proxy routes requests from one UA to another. It receives a request, decides where to send it (using DNS, location service, routing rules), and forwards it.

**Stateful proxy:** Maintains transaction state — remembers it forwarded a request and correlates the response. Can implement complex routing logic, forking (sending one INVITE to multiple destinations), and failover.

**Stateless proxy:** Forwards and forgets. Faster and simpler but can't handle forking or track transactions.

Proxies add `Via` headers as requests pass through, creating a breadcrumb trail for responses to follow back. They may also add `Record-Route` headers to stay in the path for subsequent requests within the dialog.

### Registrar

A specialized UAS that handles REGISTER requests. When your phone boots up, it sends a REGISTER to the registrar saying "I'm user@telnyx.com and I'm reachable at 192.168.1.50:5060."

The registrar stores this **binding** — the mapping from the Address of Record (AOR, your SIP URI) to the Contact address (your current IP:port). When someone calls your SIP URI, the proxy queries the registrar's location service to find your Contact address.

Registrations expire — phones must periodically re-register (typically every 60-300 seconds). If a registration expires without renewal, the phone is considered unreachable.

### Redirect Server

Instead of forwarding requests, a redirect server responds with a 3xx redirect response containing an alternative address. The UAC then sends a new request to that address directly.

Used less commonly than proxies, but useful for implementing call forwarding without keeping the redirect server in the call path.

### Back-to-Back User Agent (B2BUA)

This is the entity that matters most for understanding Telnyx. A B2BUA appears as a UAS to one side and a UAC to the other. It terminates the incoming SIP dialog and creates an entirely new, independent dialog toward the destination.

**Why Telnyx operates as a B2BUA:**

1. **Topology hiding:** The customer never sees Telnyx's internal infrastructure or the far-end carrier's addresses. Each side only knows about Telnyx.

2. **Independent call legs:** Each leg can have different codecs, different DTMF methods, different authentication. The B2BUA translates between them.

3. **Media control:** The B2BUA anchors media, enabling recording, transcoding, DTMF interworking, and quality monitoring.

4. **Billing accuracy:** By controlling both legs independently, Telnyx can precisely track call setup, duration, and teardown for billing.

5. **Security boundary:** The B2BUA prevents SIP header manipulation from propagating. A malicious or buggy SIP message from a customer can't reach the carrier directly.

6. **Interoperability:** Different SIP implementations have different quirks. The B2BUA normalizes SIP between legs, handling vendor-specific deviations.

> **💡 NOC Tip:** en debugging a call through Telnyx, always think in terms of **two legs**: the A-leg (customer ↔ Telnyx) and the B-leg (Telnyx ↔ carrier/destination). A problem on one leg doesn't necessarily exist on the other. Pull SIP traces for **both** legs and compare them.

## SIP vs. H.323 vs. SS7

Understanding why SIP won helps you understand its design:

**H.323** (from the ITU-T, like SS7): Binary protocol, complex, heavyweight. Required a gatekeeper for call control. Worked well in managed networks but was difficult to extend and debug.

**SS7** (Lesson 3): Purpose-built for the PSTN. Extremely reliable but requires dedicated signaling networks. Not suitable for the open internet.

**SIP** (from the IETF, like HTTP): Text-based, lightweight, extensible. Uses DNS for service discovery. Works over the internet's existing infrastructure. Won because it was easier to implement, debug, and extend.

SIP's extensibility through new methods, headers, and SDP attributes has allowed it to evolve for 25+ years. Features like REFER (transfer), SUBSCRIBE/NOTIFY (presence), and MESSAGE (instant messaging) were added without breaking the core protocol.

## SIP Addressing

SIP uses URIs similar to email addresses:
```
sip:user@domain:port;transport=tcp
sips:user@domain     (SIP over TLS)
tel:+15551234567     (telephone number)
```

The domain part is resolved via DNS — first NAPTR records (Lesson 19) to discover transport protocols, then SRV records to discover servers and ports, then A/AAAA records for IP addresses. This multi-step resolution enables sophisticated load balancing and failover.

## Real Troubleshooting Scenario: Calls Connect But No Audio

**Symptom:** SIP signaling succeeds (200 OK received), but no audio in either direction.

**Investigation:**
1. Pull SIP trace — INVITE/200/ACK look normal
2. Check SDP in the 200 OK — the `c=` line contains `0.0.0.0`
3. This means the far end set the connection address to zero — effectively saying "send media nowhere"

**Root cause:** The carrier's gateway was misconfigured and sent a "hold" SDP in the 200 OK (c=0.0.0.0 indicates media hold). This is a carrier-side configuration error.

**Resolution:** Escalated to the carrier's NOC to fix their gateway configuration.

## Real Troubleshooting Scenario: Registration Works But Inbound Calls Fail

**Symptom:** Customer's PBX registers successfully with Telnyx but inbound calls get 480 Temporarily Unavailable.

**Investigation:**
1. Check registration — active, Contact address is 10.0.1.50:5060 (private IP)
2. Customer is behind NAT — the Contact address in their REGISTER is their private IP
3. When Telnyx tries to route an inbound call to 10.0.1.50, it's unreachable (private address)

**Root cause:** NAT traversal issue. The customer's PBX isn't using `rport` or a STUN server, so it registers with its private IP instead of its public IP.

**Resolution:** Enable `rport` on the customer's PBX (Telnyx sees the source IP/port of the REGISTER and uses that as the Contact), or configure the PBX to use a STUN server to discover its public address.

## The SIP Trapezoid

The classic SIP architecture is often drawn as a "trapezoid":

```
  UA-A ──── Proxy-A ──── Proxy-B ──── UA-B
              ↕              ↕
         Location        Location
         Service A       Service B
```

User A's proxy looks up User B's domain, finds Proxy B via DNS, forwards the INVITE. Proxy B looks up User B's registered Contact, forwards the INVITE to User B's actual IP.

In Telnyx's B2BUA architecture, Telnyx replaces both proxies and sits in the middle, maintaining independent dialogs with each side. The "trapezoid" becomes more of a bowtie with Telnyx at the center.

---

**Key Takeaways:**
1. SIP is a text-based, HTTP-inspired signaling protocol — human-readable, making it the most debuggable telecom protocol
2. UAC and UAS roles are per-transaction, not per-device — the same phone can be client and server in the same call
3. Telnyx operates as a B2BUA — two independent call legs, enabling topology hiding, media control, transcoding, billing, and interoperability
4. Always debug Telnyx calls as two separate legs: A-leg (customer↔Telnyx) and B-leg (Telnyx↔carrier)
5. SIP addressing uses URIs resolved through DNS (NAPTR → SRV → A/AAAA), enabling load balancing and failover
6. SIP carries network addresses inside its messages (SDP, Contact, Via), which is why NAT is so destructive to SIP

**Next: Lesson 38 — SIP Methods: INVITE, REGISTER, BYE, and Beyond**
