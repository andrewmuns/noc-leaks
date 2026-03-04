# Lesson 29: NAT Traversal for SIP and RTP — The Core Problem

**Module 1 | Section 1.7 — NAT**
**⏱ ~8 min read | Prerequisites: Lesson 26**

---

## The SIP NAT Problem: Private IPs in Public Signaling

SIP was designed before NAT became ubiquitous. The protocol carries IP addresses inside the message body — addresses that become invalid when NAT rewrites headers.

### Where Private IPs Hide in SIP

```sip
INVITE sip:bob@example.com SIP/2.0
Via: SIP/2.0/UDP 192.168.1.100:5060;branch=z9hG4bK123
Contact: <sip:alice@192.168.1.100:5060>
Content-Type: application/sdp

v=0
o=alice 0 0 IN IP4 192.168.1.100
s=-
c=IN IP4 192.168.1.100
t=0 0
m=audio 10000 RTP/AVP 0 8
```

**Three places with private IPs:**
1. **Via header** — where responses should be sent
2. **Contact header** — where future requests should be sent
3. **SDP c= line** — where RTP media should flow

When this crosses NAT, the server sees `192.168.1.100` — which is unreachable from the internet. Responses go nowhere. Media goes nowhere.

---

## Why NAT Breaks RTP: The Media Problem

SIP negotiates media in SDP:

```sdp
m=audio 10000 RTP/AVP 0
c=IN IP4 192.168.1.100
```

The caller says: "Send RTP to 192.168.1.100:10000"

But the callee on the internet can't reach that private IP. Even if SIP signaling somehow works (via proxy), the media stream has no path.

**Result:** Call connects, but no audio flows. Or worse — one-way audio if one side is NAT'd and the other isn't.

---

## STUN: Discovering Your Public Address

**Session Traversal Utilities for NAT (STUN)** is a protocol to learn your public-facing IP and port.

### How STUN Works

1. Client behind NAT sends STUN binding request to STUN server (e.g., `stun.telnyx.com:3478`)
2. STUN server sees the source IP:port after NAT translation
3. STUN server replies: "Your public address is 203.0.113.5:61234"
4. Client now knows its public mapping

```
Client (192.168.1.100:5060) 
    ↓ STUN request
NAT (rewrites to 203.0.113.5:61234)
    ↓
STUN server (stun.telnyx.com)
    ↓ "Your address is 203.0.113.5:61234"
Client updates SIP Contact and SDP to use this public address
```

### STUN Limitations

- **Works for:** Full Cone, Restricted Cone, Port Restricted Cone NAT
- **Fails for:** Symmetric NAT (where each destination gets different mapping)
- **Learning only:** STUN doesn't create or maintain NAT bindings

🔧 **NOC Tip:** If STUN is enabled on a device and calls still fail, check NAT type. Symmetric NAT breaks STUN-based NAT traversal every time. You'll need TURN relay for these cases.

---

## TURN: Relaying When Direct Fails

**Traversal Using Relays around NAT (TURN)** is the fallback when STUN fails. Instead of connecting directly, both endpoints send media to a TURN relay server, which forwards it.

### How TURN Works

1. Client allocates a relay address on TURN server (`turn.telnyx.com`)
2. TURN server provides a public IP:port (e.g., `198.51.100.10:50000`)
3. Client puts this relay address in SDP
4. Client's media → TURN server → Other party
5. Other party's media → TURN server → Client

```
Client A (NAT'd) ←→ TURN Relay ←→ Client B
        ↑                            ↑
     Allocated:                   Allocated:
  198.51.100.10:50000          203.0.113.10:60000
```

### TURN Costs

- **Bandwidth:** Media flows through Telnyx infrastructure (billable)
- **Latency:** Extra hop adds ~10-50ms
- **Reliability:** Always works, regardless of NAT type

🔧 **NOC Tip:** TURN usage shows in your Telnyx console. If you see high TURN relay traffic for specific customers, they likely have Symmetric NAT or restrictive firewalls. Recommend SBC deployment or firewall changes to reduce relay costs.

---

## Far-End NAT Traversal: Fixing It Server-Side

Telnyx uses server-side techniques so customers don't need to configure anything:

### rport (RFC 3581)

The `rport` parameter tells the server to ignore the private IP in Via and use the actual source IP:port:

```sip
Via: SIP/2.0/UDP 192.168.1.100:5060;branch=...;rport
```

When the server responds, it sends to the layer-3 source address, not the Via address.

### SIP ALG: A Double-Edged Sword

Many routers include **SIP Application Layer Gateway** that:
- Inspects SIP packets
- Rewrites private IPs to public IPs in headers and SDP
- Maintains a mapping table

**The problem:** SIP ALG implementations are often buggy. They:
- Corrupt SDP body formatting
- Mangle headers they don't recognize
- Create race conditions in multipart messages
- Cause mysterious one-way audio issues

🔧 **NOC Tip:** SIP ALG is a frequent culprit in "weird" call issues. If a customer through a specific router has inexplicable problems, recommend disabling SIP ALG. Modern SBCs and B2BUAs (like Telnyx uses) handle NAT properly without ALG assistance.

---

## Key Takeaways

1. **SIP carries private IPs** in Via, Contact, and SDP — NAT breaks these without intervention
2. **STUN** discovers your public address — works for Cone NATs, fails for Symmetric NAT
3. **TURN** relays traffic through a server — works everywhere but adds cost and latency
4. **rport** parameter enables server-side NAT handling without client changes
5. **SIP ALG** often causes more problems than it solves — disable when troubleshooting mysterious issues

---

**Next: Lesson 28 — SIP ALG, Session Border Controllers, and Media Anchoring**
