# Lesson 52: Systematic Call Quality Troubleshooting
**Module 1 | Section 1.13 — Troubleshooting**
**⏱ ~8min read | Prerequisites: Lessons 32–36, 48**
---

## Why You Need a Framework

When a customer reports "bad call quality," that could mean a dozen different things. Without a systematic approach, you'll waste time chasing ghosts. This lesson gives you a repeatable framework that works for every quality complaint — from one-way audio to echo to choppy speech.

The goal is simple: **isolate the leg, identify the symptom, find the cause, fix it.**

---

## The Four-Step Framework

### Step 1: Isolate the Leg

Every call through Telnyx has at least two legs:

```
Customer A ──► Telnyx Ingress SBC ──► Telnyx Core ──► Telnyx Egress SBC ──► Customer B
     Leg A (inbound)                                      Leg B (outbound)
```

Your first job is to determine **which leg** has the problem. Ask:

- Does Customer A hear the issue, Customer B, or both?
- Is the issue present on the Telnyx-side capture (between SBCs)?
- Does the problem persist if you swap the termination route?

🔧 **NOC Tip:** In the Telnyx Mission Control portal, pull the call detail record (CDR) and look at the `leg_id`. Each leg has independent RTCP stats. Compare MOS, jitter, and packet loss for Leg A vs Leg B separately — this instantly tells you which side is degraded.

### Step 2: Identify the Symptom

Classify the problem into one of these categories:

| Symptom | Description |
|---------|-------------|
| **No audio** | Complete silence in one or both directions |
| **One-way audio** | Audio flows in one direction only |
| **Choppy audio** | Words cut in and out, robotic sound |
| **Echo** | Speaker hears their own voice delayed |
| **DTMF failure** | IVR menus don't respond to key presses |
| **Distortion/static** | Garbled or noisy audio |
| **Latency** | Noticeable delay in conversation |

### Step 3: Find the Cause

Each symptom maps to a set of likely causes. We'll cover each below.

### Step 4: Fix and Verify

Apply the fix, test with a new call, and confirm RTCP stats normalize.

---

## Symptom: No Audio (Both Directions)

No audio in either direction almost always means **media path failure**:

1. **NAT/firewall blocking RTP** — The SDP contains a private IP or the customer's firewall drops UDP traffic on the RTP port range.
2. **Oops, wrong codec** — No common codec was negotiated (check SDP answer).
3. **Media timeout** — RTP never arrives, and Telnyx tears down the call after the media timeout.

**Diagnostic steps:**

```bash
# Check SDP in SIP trace — is the c= line a routable IP?
grep "c=IN IP4" /tmp/sip-trace-call123.txt

# Check if RTP packets arrived at the SBC
tcpdump -i eth0 -nn udp port 20000-30000 -c 50

# Look at Oops, RTCP stats in Grafana
# Dashboard: NOC > Call Quality > filter by call_id
```

🔧 **NOC Tip:** If the SDP `c=` line shows `10.x.x.x`, `172.16-31.x.x`, or `192.168.x.x`, the customer is behind NAT and their SBC isn't rewriting the SDP. Guide them to enable SIP ALG or use a STUN server.

---

## Symptom: One-Way Audio

One-way audio is the most common quality complaint. Audio goes A→B but not B→A (or vice versa).

**Common causes:**

- **Asymmetric NAT** — One side's RTP gets through; the other side's firewall drops incoming RTP because it doesn't recognize the source.
- **SDP mismatch** — One side's SDP advertises an unreachable IP/port.
- **Oops, media anchoring disabled** — If Telnyx media proxy is bypassed (direct media mode), both endpoints must be mutually reachable.

**Diagnostic checklist:**

1. Pull both SDPs (offer and answer) — are both `c=` IPs publicly routable?
2. Check for `a=sendonly` or `a=recvonly` — someone may have put the call on hold.
3. Verify RTP is flowing in both directions on the SBC capture.
4. Check firewall rules on the customer's side for symmetric RTP.

```
SDP Offer (Customer A):
  c=IN IP4 203.0.113.10
  m=audio 30000 RTP/AVP 0
  a=sendrecv

SDP Answer (Customer B):
  c=IN IP4 198.51.100.5
  m=audio 40000 RTP/AVP 0
  a=sendrecv         ← If this says "sendonly", that's your problem
```

🔧 **NOC Tip:** Enable **media anchoring** (also called "media proxy" or "topology hiding") on the Telnyx SIP connection. This forces all RTP through the Telnyx media relay, solving 90% of one-way audio caused by NAT. The setting is in Mission Control under the SIP connection's media settings.

---

## Symptom: Choppy Audio

Choppy, robotic, or "underwater" audio indicates **packet loss or excessive jitter**.

**Key metrics to check in RTCP stats:**

| Metric | Acceptable | Degraded | Unusable |
|--------|-----------|----------|----------|
| Packet loss | < 1% | 1–3% | > 3% |
| Jitter | < 30ms | 30–50ms | > 50ms |
| MOS | > 4.0 | 3.5–4.0 | < 3.5 |

**Diagnostic steps:**

1. Pull RTCP-XR stats from the CDR — look at `jitter`, `packets_lost`, `mos`.
2. Check Grafana dashboard for the SBC: is there a broader pattern affecting many calls?
3. Run MTR from the SBC to the customer's IP (see Lesson 51).
4. Check for **burst loss** vs **random loss** — burst loss suggests congestion; random loss suggests a bad link.

```bash
# Quick RTCP stat pull from CDR API
curl -s "https://api.telnyx.com/v2/calls/$CALL_ID" \
  -H "Authorization: Bearer $API_KEY" | jq '.data.stats'
```

🔧 **NOC Tip:** If choppy audio affects all calls on one SBC but not others, check the SBC's NIC stats for drops: `ethtool -S eth0 | grep -i drop`. Also check for CPU saturation — transcoding under load causes choppy audio too.

---

## Symptom: Echo

Echo means the speaker hears their own voice returning with a delay. Two types:

1. **Acoustic echo** — The remote phone's speaker feeds into its microphone. Nothing you can fix on the network side.
2. **Hybrid echo** — Impedance mismatch at the TDM/IP boundary (the PSTN gateway). The 2-wire to 4-wire conversion reflects energy back.

**Diagnostic approach:**

- **Who hears the echo?** The echo source is on the *opposite* side. If Customer A hears echo, the problem is at Customer B's end.
- **What's the delay?** Short echo (<30ms) = acoustic. Long echo (>100ms) = hybrid or network path.
- Check if the carrier on the far end has echo cancellation enabled.

🔧 **NOC Tip:** When a customer complains about echo and the far side is a PSTN termination through a Telnyx carrier partner, check the carrier's echo canceller settings. You can request the carrier enable or tune their echo canceller. Internally, Telnyx SBCs run echo cancellation — verify it's active on the media processor handling that call.

---

## Symptom: DTMF Failure

DTMF failures manifest as IVR menus not responding, incorrect digits received, or "press 1" loops. See Lesson 58 for deep detail, but the quick troubleshooting:

1. **Check DTMF method mismatch** — Is the sender using RFC 2833 but the receiver expects SIP INFO (or vice versa)?
2. **Check SDP for `telephone-event`** — If it's missing, RFC 2833 DTMF won't work.
3. **Check for codec transcoding** — In-band DTMF gets destroyed by transcoding (especially to low-bitrate codecs).

```
# In SDP, look for:
a=rtpmap:101 telephone-event/8000
a=fmtp:101 0-16
```

---

## Your Toolbox

### SIP Traces

The single most important diagnostic tool. Every call quality investigation starts here.

```bash
# Homer/heplify query for a specific call
# Search by Call-ID, From/To, or time range
sngrep -c /etc/sngrep.conf
```

### RTCP Stats

Real-time quality metrics reported by both endpoints during the call. Available in CDRs and Grafana.

### Packet Captures (PCAPs)

When SIP traces and RTCP aren't enough, capture raw packets:

```bash
# Capture RTP for a specific call on the SBC
tcpdump -i eth0 -s 0 -w /tmp/call-capture.pcap \
  host 203.0.113.10 and udp portrange 10000-30000

# Open in Wireshark → Telephony → RTP → Stream Analysis
```

### Grafana Dashboards

Telnyx NOC dashboards provide aggregate views:

- **Call Quality Overview** — MOS distribution, packet loss trends
- **SBC Health** — CPU, memory, NIC errors, concurrent sessions
- **Carrier Performance** — ASR/ACD by carrier, quality by route

🔧 **NOC Tip:** When investigating a quality issue, always check the Grafana "Call Quality" dashboard first with the time range of the affected call. If you see a broad dip affecting many calls, it's likely an infrastructure issue, not a customer-specific problem.

---

## Putting It All Together: A Real Example

**Ticket:** "Customer reports choppy audio on outbound calls to UK numbers."

1. **Isolate the leg:** Pull 5 recent CDRs. RTCP stats show high jitter (45ms) on Leg B (egress to UK carrier) but clean stats on Leg A. Problem is on the egress leg.
2. **Identify the symptom:** Choppy audio = packet loss/jitter.
3. **Find the cause:** MTR from the egress SBC to the carrier's IP shows 4% loss at hop 7 (a transit provider). The loss is consistent, not bursty.
4. **Fix:** Route UK traffic to an alternate carrier while raising a ticket with the transit provider. Verify new calls show MOS > 4.0.

---

## Key Takeaways

1. Always follow the framework: **isolate the leg → identify the symptom → find the cause → fix and verify**.
2. One-way audio is almost always a NAT/firewall issue — enable media anchoring as the first fix.
3. Choppy audio maps to packet loss and jitter — check RTCP stats before doing anything else.
4. Echo is caused by the **opposite** end from the person hearing it.
5. DTMF failures usually come from method mismatches between endpoints.
6. Start with SIP traces and RTCP stats; escalate to PCAPs only when needed.
7. Check Grafana dashboards to determine if an issue is isolated or systemic.

---

**Next: Lesson 51 — Network Diagnostics: Traceroute, MTR, and Path Analysis**
