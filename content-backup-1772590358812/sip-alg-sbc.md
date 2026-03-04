---
title: "SIP ALG, Session Border Controllers, and Media Anchoring"
description: "Learn about sip alg, session border controllers, and media anchoring"
module: "Module 1: Foundations"
lesson: "30"
difficulty: "Intermediate"
duration: "6 minutes"
objectives:
  - Understand sip alg, session border controllers, and media anchoring
slug: "sip-alg-sbc"
---

## Session Border Controllers: The Proper Fix

SBCs solve NAT by being the "man in the middle." They terminate SIP on both sides, rewrite headers appropriately, and relay media when needed.

### How SBCs Handle NAT

```
Phone (NAT'd)          SBC (Public)           Carrier
192.168.1.100  ──────→  203.0.113.10  ──────→  198.51.100.5
SIP + SDP              SIP rewritten          Clean SIP
                         + SDP relay
             ←────────                ←──────
           Media relayed           Media
```

**The SBC's job:**
1. Receives SIP from private endpoint
2. Rewrites Contact, Via, SDP to use SBC's public address
3. Forwards clean SIP to destination
4. Receives RTP on SBC's port
5. Forwards RTP through NAT hole to private endpoint

### SBC Functions Beyond NAT

- **Security:** Topology hiding, DoS protection, call admission control
- **Interoperability:** Normalize quirky SIP implementations
- **Media handling:** Transcoding, recording, A/B leg separation
- **Regulatory:** Lawful intercept, emergency call handling

> **💡 NOC Tip:**  Telnyx, the B2BUA acts as the SBC. When you see calls from a customer behind NAT, verify the call flow shows the B2BUA handling both legs. Call-site-finder can tell you which B2BUA handled a specific call.

---

## Media Anchoring: Forcing RTP Through Known Paths

When SBCs get involved, they can force media to flow through themselves (anchoring) or allow direct peer-to-peer (hairpinning).

### Media Anchoring

RTP flows through the SBC always:
- **Pros:** SBC sees all media, can record, transcribe, analyse
- **Cons:** Added latency, bandwidth through SBC, cost

### Media Hairpinning

SBC negotiates RTP endpoints, then steps back:
- **Pros:** Lower latency, less SBC load
- **Cons:** NAT can break direct media paths, SBC loses visibility

**Telnyx default:** Media anchoring is enabled for most connections. This ensures:
- Consistent quality metrics
- Recording/A capabilities work
- NAT traversal always succeeds
- Troubleshooting is easier (all media passes through known points)
slug: "sip-alg-sbc"
---

## RTP Latching: Learning the Real Source

When a behind-NAT endpoint sends RTP, the SBC uses **latching**:

1. Device sends RTP from `192.168.1.100:10000`
2. NAT rewrites to `203.0.113.5:51234`
3. SBC receives RTP, notes actual source: `203.0.113.5:51234`
4. SBC "latches" — sends return RTP to that address (the latched address)
5. Even though SDP said `192.168.1.100:10000`, return traffic goes to the working NAT mapping

**Latch timeout:** If no RTP for 30-60 seconds, SBC may drop the latch. This is why silence suppression sometimes causes audio issues — the latch times out.

> **💡 NOC Tip:**  a customer reports audio that works for 30 seconds then "switches to one-way," check for latch timeout. Disable silence suppression (comfort noise instead) to keep RTP flowing and the latch alive.

---

## Debugging One-Way Audio: Systematic Approach

One-way audio is the #1 VoIP issue. Here's the systematic debug:

### Step 1: Confirm Direction
Which direction is broken? A→B, B→A, or both?

### Step 2: Check Signaling vs Media
- Both sides can hear the call connects? Signaling works.
- Only one side hears audio? Probably media/NAT issue.

### Step 3: PCAP Analysis
```bash
# Look at the RTP flow in both directions
# Filter for one side's SSRC
tshark -r capture.pcap -Y "rtp.ssrc == 0x12345678" -V
```

### Step 4: Symptom Mapping

| Symptom | Likely Cause |
|---------|--------------|
| Always one-way, same direction | Firewall blocking one way, or SDP has wrong IP |
| One-way after 30-60s | RTP latching timeout, NAT session expired |
| Intermittent one-way | Load balancer uneven, or race condition |
| One-way only some calls | Different NAT types, routing asymmetry |

### Step 5: SDP Verification
```bash
# Extract SDP IPs from SIP captures
tshark -r capture.pcap -Y "sip" -T fields -e sip.Contact.host -e sdp.connection_info.address
```

Both sides should see routable addresses. Private IPs in SDP from internet-facing servers = bug.

> **💡 NOC Tip:** en escalating one-way audio, always provide: direction of break, call IDs, source/destination IPs, and confirm if it's consistent or intermittent. This saves hours of debug time.
slug: "sip-alg-sbc"
---

## Key Takeaways

1. **SBCs properly solve NAT** by terminating SIP and relaying media — unlike SIP ALG which is error-prone
2. **Media anchoring** routes all RTP through SBC — trades latency for reliability and visibility
3. **RTP latching** learns the actual NAT-mapped address from incoming packets
4. **One-way audio debugging:** Confirm direction → check signaling → analyze PCAP → match symptom to cause
5. **Latch timeout** can cause mid-call audio drops — keepalive traffic prevents this

---

**Next: Lesson 29 — RTP — Real-time Transport Protocol Deep Dive**
