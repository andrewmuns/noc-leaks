# Lesson 130: One-Way Audio and No Audio — Systematic Debugging

**Module 4 | Section 4.2 — SIP Debugging**
**⏱ ~8 min read | Prerequisites: Lessons 27-28, 48-49, 111**

---

One-way audio (caller hears callee but not vice versa) and no audio (complete silence) are among the most reported and most frustrating call quality issues. Unlike signaling failures that produce clear error codes, audio issues can be caused by NAT traversal, firewall blocks, SDP negotiation failures, codec mismatches, or routing problems. This lesson provides a systematic debugging flowchart that quickly isolates the root cause.

## The Three Possible Scenarios

**No audio:** RTP isn't flowing in either direction
**One-way audio (A→B):** RTP flows from caller to callee, but not back
**One-way audio (B→A):** RTP flows from callee to caller, but not back

Each scenario has distinct causes. One-way audio almost always points to an asymmetric problem — different paths or configurations for each direction.

## The Systematic Flowchart

When audio issues are reported, follow this order:

### Step 1: Verify SDP Negotiation Completed Successfully

One-way audio often starts with negotiation, not network.

**Check in the SIP trace:**
```
# INVITE has SDP (offer)
INVITE sip:+15559876543@...
Content-Type: application/sdp
Content-Length: 234

v=0
o=- ...
c=IN IP4 10.0.1.5  ← Media IP in offer
m=audio 10000 RTP/AVP 0 18

# 200 OK has SDP (answer)
SIP/2.0 200 OK
Content-Type: application/sdp
Content-Length: 234

v=0
o=- ...
c=IN IP4 203.0.113.80  ← Media IP in answer
m=audio 20000 RTP/AVP 0
```

**What to check:**
1. Did both sides include SDP? (Not 200 OK without SDP — that breaks audio)
2. Is there a common codec in both offer and answer? (If answer rejects all codecs → no audio)
3. Are the media IPs and ports valid? (Not empty, 0.0.0.0, or obviously wrong)

**Codec mismatch signature:**
```
# Offer: G.711 (0), G.729 (18)
m=audio 10000 RTP/AVP 0 18

# Answer: Only telephone-event (101), NO PACodec
m=audio 20000 RTP/AVP 101
```
No common codec = no audio, possibly 488 response.

🔧 **NOC Tip:** Save a "known good" SDP exchange example for your environment. When debugging, diff against the good example. Are the `c=` lines similar? Is the port number responding? Are the payloads compatible? This visual comparison catches 90% of SDP negotiation issues quickly.

### Step 2: Check if RTP is Flowing

After SDP negotiation, RTP should flow between the media IPs and ports.

**How to verify:**
1. **RTCP statistics** — Both sides send RTCP Receiver Reports (Lesson 30)
2. **Packet captures** — tcpdump on the media server shows inbound/outbound RTP streams
3. **Grafana metrics** — RTP streams tracked per call

**Key RTCP metrics in Grafana:**
```promql
# RTP packets expected vs received
sum by (call_id)(rate(rtp_packets_received_total[1m]))
sum by (call_id)(rate(rtp_packets_expected_total[1m]))

# Loss percentage
100 * (rtp_packets_lost_total / rtp_packets_expected_total)
```

**What you want to see:**
- Media IP A sends RTP to Media IP B → B receives packets
- Media IP B sends RTP to Media IP A → A receives packets

**What one-way audio looks like:**
- A sends to B → B receives ✓
- B sends to A → A receives 0 packets ✗

### Step 3: Identify Which Direction is Broken

One-way audio means one direction works, one doesn't. Determine:
- Direction A→B works: Packets flow from caller to callee
- Direction B→A broken: Callee sends but packets don't reach caller

**Common pattern:**
```
Caller (behind NAT) → Telnyx → Callee (Carrier)

Caller → Telnyx RTP: ✓ (received)
Telnyx → Caller RTP: ✗ (blocked by NAT)
Telnyx → Callee RTP: ✓ (received)
Callee → Telnyx RTP: ✓ (received)
```

Result: Caller hears callee (Telnyx→Caller is broken for this example — actually Caller doesn't hear), callee hears caller.

Wait — let me correct this:
- If Caller→Telnyx works and Telnyx→Caller is blocked: Callee's voice (via Telnyx) doesn't reach caller = One-way audio (caller cannot hear callee)
- If Telnyx→Callee works and Callee→Telnyx is blocked: Caller's voice doesn't reach callee = One-way audio (callee cannot hear caller)

### Step 4: Check Media IPs in SDP

Look for private IPs (NAT indicators):

```
# Offer from Customer (behind NAT)
v=0
o=- ...
c=IN IP4 192.168.1.5  ← Private IP
m=audio 10000 RTP/AVP 0

# Answer from Telnyx (public IP)
v=0
o=- ...
c=IN IP4 203.0.113.10  ← Public IP
m=audio 20000 RTP/AVP 0
```

**The problem:** Customer says "send RTP to 192.168.1.5" but that's their private IP. Telnyx is outside their network, so packets to 192.168.1.5 will fail.

**Solutions (in order):**
1. **RTP latching** — Don't use the IP from SDP. Instead, look at the source IP of the first RTP packet received from the customer, and send RTP back to that IP:port.
2. **STUN** — Customer discovers their public IP via STUN server, uses it in SDP (Lessons 27, 55)
3. **TURN** — Relay all media through TURN server (Lesson 56)
4. **Fix the SDP** — Telnyx's B2BUA rewrites the SDP to use the public IP

🔧 **NOC Tip:** When you see private IPs in SDP `c=` lines or `m=` lines for customer-side media, NAT is the immediate suspect. Check if your media server does RTP latching (most modern SBCs do). The fix for one-way audio is often: customer sends RTP, media server learns caller's public IP from the source of that RTP, and sends return RTP to that learned address, ignoring the private IP in SDP.

### Step 5: Check Firewall/RTP Port Blocks

RTP uses UDP ports (typically 10000-20000). Firewalls often:
- Block outbound UDP entirely
- Allow outbound UDP but not inbound (asymmetric)
- Have UDP timeouts that expire mid-call

**How to check:**
1. **From customer side:** Can they reach Telnyx media ports?
   ```bash
   # Test from customer network
   nc -vzu sip.telnyx.com 10000
   ```

2. **From Telnyx side:** Is RTP arriving?
   - Grafana: Packets received metrics
   - tcpdump on media server
   - RTCP reports show inbound packet counts

3. **Firewall logging:** Check if firewall is blocking specific ports

**UDP timeout problem:**
- NAT/firewall creates a mapping when outbound RTP starts
- During call silence or hold, no RTP flows
- Mapping expires after 30-60 seconds
- Inbound RTP can no longer enter (mapping gone)
- Result: Audio cuts out after silence, returns if they talk again

**Solution:** Keepalive packets or STUN keepalives to keep mapping alive.

### Step 6: Check SRTP and Encryption Mismatches

If one side expects SRTP and the other sends plain RTP, audio drops:

```
# Offer requests SRTP
c=IN IP4 203.0.113.10
m=audio 10000 RTP/SAVP 0  ← SAVP = SRTP
a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:...

# Answer replies with plain RTP
m=audio 20000 RTP/AVP 0  ← AVP = plain RTP (no crypto)
```

This mismatch causes audio failure. Both sides must agree on SRTP or both on plain RTP.

**Common cause:** Customer configured for plain RTP, Telnyx configured for SRTP (or vice versa), or the encryption key exchange failed.

## The Complete Troubleshooting Decision Tree

```
Audio Issue Reported
    ↓
Check SIP Trace: Was SDP negotiation successful?
    ↓ No → Check codec mismatch, crypto mismatch, SDP format
    ↓ Yes → Continue
    ↓
Check RTCP metrics: Is RTP flowing in both directions?
    ↓ Both directions 0 packets → Check SDP IPs, firewall blocks
    ↓ One direction only → Check NAT, media anchoring, asymmetric firewall
    ↓
Check SDP c= and m= lines: Are IPs public or private?
    ↓ Private IP on customer side → NAT issue, check RTP latching
    ↓ Private IP on Telnyx side → SDP rewriting needed
    ↓ Public IPs both sides → Check firewall, routing
    ↓
Check encryption: SRTP/plain RTP agreement
    ↓ Mismatch → Align configuration
    ↓ Match → Continue
    ↓
Check media server logs: Receiving packets but not playing?
    ↓ Check jitter buffer, codec decoding, DTMF detection
    ↓
Check firewall/NAT: UDP timeouts, port blocks
    ↓ Fix with keepalives, firewall rules, SBC anchoring
```

## Real-World Scenario

**Customer report:** "After 30 seconds on hold, audio cuts out completely. Call is still connected, but no sound either way."

**Investigation:**

1. **Check SIP trace:** Hold includes `a=sendonly`, resume includes `a=sendrecv`
   - Re-INVITE negotiation successful
   - SDP shows proper media direction changes

2. **Check RTP flow:**
   ```promql
   # Early in call (first 30 seconds)
   rtp_packets_received{call_id="abc"} → 1500 packets per minute
   
   # After hold
   rtp_packets_received{call_id="abc"} → 0 packets per minute
   ```

3. **RTCP reports from customer side:** Last report says "lost 100% of packets"

4. **Pattern recognized:** UDP NAT mapping timeout during hold
   - 30 seconds of hold = no RTP flows
   - NAT firewall mapping expires
   - After hold, customer sends new RTP (mapping re-created)
   - But Telnyx's media server is still sending to OLD mapped address
   = One-way audio (customer hears us, we don't hear them? No, actually...)

   Actually, to clarify:
   - Customer (behind NAT) sends RTP to Telnyx public IP: WORKS (NAT creates outbound mapping)
   - Telnyx sends RTP to customer's NAT public IP: Initially works (mapping exists)
   - During hold: No RTP either direction (silence detection, or the frozen media path)
   - NAT mapping times out after 30 seconds
   - After hold: Customer sends RTP → New NAT mapping created
   - Telnyx sends RTP to OLD mapping address → Packets dropped by NAT
   
   Result: Telnyx receives customer RTP, customer doesn't receive Telnyx RTP = Customer can't hear Telnyx (one-way audio)

5. **Root cause:** NAT UDP mapping timeout during hold

**Fix:** Configure RTP keepalives (empty UDP packets every 15 seconds) even when audio is muted/silent. Or use Session Timers in SIP to keep signaling active.

---

**Key Takeaways:**

1. No audio = SDP negotiation failure OR RTP not flowing either direction
2. One-way audio = asymmetric problem — RTP works one way but not the other
3. Check SDP negotiation first — verify common codec, valid media IPs, crypto agreement
4. Private IPs (10.x, 192.168.x, 172.16-31.x) in SDP indicate NAT — verify RTP latching is working
5. Check RTCP metrics to see which direction is broken — guides investigation to specific path
6. Mid-call audio cuts after silence typically indicate NAT UDP timeout — fix with keepalives
7. SRTP/plain RTP mismatch causes audio failure — both sides must use same encryption mode

**Next: Lesson 115 — Echo, Choppy Audio, and Other Quality Issues**
