# Lesson 131: Echo, Choppy Audio, and Other Quality Issues

**Module 4 | Section 4.2 — SIP Debugging**
**⏱ ~7 min read | Prerequisites: Lessons 32-36, 114**

---

Connectivity issues (one-way audio, no audio) are solved when media flows bidirectionally. But once media flows, quality issues emerge: echo, choppy sound, robotic voices, and delays. These are impairment issues — the signal is present but distorted. Understanding the causes helps you map symptoms to root causes and fixes.

## Echo: The Original Telecom Problem

Echo is as old as telephony. The caller hears their own voice reflected back after a short delay. Two types exist:

### Acoustic Echo

**Cause:** The callee's speaker sound reaches their microphone and is transmitted back.
```
Caller → [Network] → Callee's speaker → Callee's microphone → [Network] → Caller
                                                        ↑
                                                  Acoustic feedback
```

**Detection:** Both sides hear echo, or caller hears their own voice.

**Solutions:**
- **Acoustic echo cancellation (AEC)** in softphones (WebRTC, Zoom, etc.)
- **Headsets:** Physically separate speaker and microphone
- **Room treatment:** Acoustic dampening reduces reflections
- **Volume reduction:** Lower speaker volume reduces bleed

**Not a NOC issue** unless it affects many users with the same software configuration. Individual acoustic echo is solved by the end user using headsets or enabling AEC.

### Hybrid Echo (Line Echo)

**Cause:** Impedance mismatch at 2-wire/4-wire conversion points in the PSTN.

Traditional phone lines use 2-wire for both directions (bidirectional). Carrier networks and digital systems use 4-wire (separate paths for send/receive). The hybrid coil converts between them:

```
2-wire (local loop) ↔ Hybrid ↔ 4-wire (carrier network)
                          ↑
                 Impedance mismatch → Reflection → Echo
```

When the hybrid doesn't match impedance properly, some signal reflects back.

**Detection:** Echo heard only by one side (the caller). Delay is typically short (10-50ms for local loops) but can be longer for international calls.

**Solutions (Telnyx can control):**
- **Echo cancellation (EC)** at the SBC or gateway
- **Echo suppressors** for high-delay cases
- **Proper hybrid impedance matching** in TDM gateways

🔧 **NOC Tip:** If echo reports correlate with specific carriers, regions, or TDM gateways (not IP-to-IP calls), suspect hybrid echo. Check if those gateways have EC enabled. A quick correlation: Does echo happen only on calls to a specific carrier or country? That's a hybrid echo signature pointing to that carrier's 2-wire network or Telnyx's TDM gateway to that carrier.

## Choppy Audio: Packets Not Arriving Smoothly

**Symptom:** Audio cuts in and out — words are partially audible with gaps.

### Causes of Choppy Audio

**1. High jitter and shallow jitter buffer (Lesson 34)**
- If jitter > jitter buffer depth, packets arrive too late
- Late packets = drops (can't play them after playout time)
- Result: Gaps in audio

**2. Packet loss, burst or random (Lesson 35)**
- Lost packets create audio gaps
- Burst loss (consecutive packets) is worse than random loss
- Packet Loss Concealment (PLC) can only mask 1-2 consecutive lost packets

**3. CPU overload on endpoint**
- Poor phone/softphone can't process incoming packets fast enough
- System falls behind, audio underruns
- Check endpoint CPU utilization, not just network

**4. WiFi issues (wireless endpoint)**
- WiFi contention, interference, or roaming
- Packet loss and variable latency unique to wireless
### Diagnosing Choppy Audio

**Check RTCP metrics (Lesson 30):**
```promql
# Jitter
avg(rtcp_interarrival_jitter_seconds) by (call_id)

# Loss rate
avg(rtcp_loss_fraction) by (call_id)

# Consecutive loss events
rate(rtcp_consecutive_losses_total[1m])
```

**What to look for:**
| Symptom | Probable Cause |
|---------|----------------|
| High jitter + low loss | Shallow jitter buffer on receiver |
| High burst loss, moderate jitter | Network congestion or route flapping |
| Low jitter, low loss, but choppy | CPU overload on endpoint |
| Correlation with WiFi roaming | Wireless network issues |

🔧 **NOC Tip:** When investigating choppy audio, always correlate with jitter buffer metrics if available. If the jitter buffer is discarding late packets, the buffer depth might be too shallow for the network jitter. Good jitter buffers adapt — check if adaptive jitter buffer is enabled and if it's tracking higher than usual. Static jitter buffers in noisy networks cause choppy audio.

## Robotic/Metallic Audio: Codec Artifacts

**Symptom:** Voice sounds robotic, metallic, "underwater," or distorted.

### Causes

**1. High packet loss with CELP codecs (G.729, AMR)**
- These codecs compress by building a voice model
- Lost packets can't be easily concealed
- CELP loses the voice model state, causing garbled audio until next key frame
- G.711 (PCM) handles loss better — just loses the samples

**2. Transcoding cascading**
- G.711 → G.729 → G.711 → G.729
- Each transcoding step loses quality
- Multiple hops compound the issue

**3. Improper jitter buffer behavior**
- Warped audio from improper de-jittering
- Small buffers cause artifacts

### Diagnosing

**Check codec used:**
```
# From SDP offer/answer
codec=g729 → Vulnerable to robotic audio on loss
codec=u-law (G.711) → More robust
```

**Check loss rate:**
- >3% loss with G.729 → likely robotic audio
- >5% loss → severe degradation, possible call drop

**Resolution:**
- Use G.711 for lossy networks (trade bandwidth for quality)
- Implement packet loss concealment (PLC) optimized for the codec
- Reduce transcoding hops (prefer end-to-end same codec)

## Audio Delay: High Latency Perception

**Symptom:** Long pauses between speaking and hearing response. Conversations feel like "walkie-talkie" or satellite phone.

**Latency budget components (Lesson 32):**
1. **Codec delay**: 0.125ms-25ms depending on codec
2. **Packetization**: 20ms typical
3. **Network transmission**: Varies by distance
4. **Jitter buffer**: 20-100ms depending on network jitter
5. **Routing/queuing**: Variable, usually minimal

### Acceptable Latency

| One-way delay | User perception |
|---------------|-----------------|
| <150ms | Good, natural conversation |
| 150-300ms | Acceptable, slight delay noticed |
| 300-500ms | Annoying, turn-taking affected |
| >500ms | Unusable for natural conversation |

### Causes of High Delay

**1. Geographic distance**
- Each 1000km adds ~5ms propagation delay (speed of light in fiber)
- Chicago to Singapore: ~180ms one-way minimum (physics limit)
- Can't fix physics, but can optimize routes

**2. Transcoding delays (Lesson 7)**
- G.729: 15-25ms algorithmic delay
- Multiple transcoding hops add up
- Prefer passthrough (no transcoding) where possible

**3. Deep jitter buffers (Lesson 34)**
- Adaptive buffers growing to handle high jitter
- Deep buffers = more delay
- Check jitter buffer depth metrics

**4. Recording/processing**
- Call recording with synchronous storage
- Media forking with slow consumers
- Bill-at-call-answer requires request/response before media

🔧 **NOC Tip:** When latency suddenly increases for all calls, check for network routing changes — BGP route flaps, new peering, or transit issues. When latency increases for a subset of calls to a specific region, check the media path routing — calls may be traversing a suboptimal path (EU calls routed through Asia, for example). MTR and traceroute to the media IPs reveal the path taken.

## Cross-Talk and Audio Bleeding

**Symptom:** Hearing audio from a different conversation mixed in.

### Causes

**1. SS7/ISUP translation errors (PSTN)**
- Timeslot misalignment in TDM circuits
- Channel associated signaling (CAS) misconfiguration
- Rare today but possible with TDM interconnections

**2. Mixer/route issues**
- Audio bridges mixing wrong streams
- Session confusion in conferencing servers

**3. Network addressing collision**
- Two different calls using same RTP IP:port pair
- NAT pinholes mapping multiple flows to same external address

### Troubleshooting

**Check RTP streams:**
- Are SSRC values unique per call? (Lesson 29)
- Are the 5-tuples (src IP:port, dst IP:port, proto) unique?

**Resolution:**
- For conferencing: Check conference bridge configuration
- For routing: Verify no address/port collisions in media gateway
- For TDM: Verify timeslot mappings and CAS configuration

## Real-World Troubleshooting Scenario

**Customer report:** "Calls to Italy sound robotic and sometimes drop."

**Investigation:**

1. **Check codec negotiation:**
   - Traces show G.729 preferred by carrier
   - Customer using G.729
   - No transcoding required ✓

2. **Check RTCP metrics:**
   ```promql
   # Loss rate for calls to Italy
   avg(rtcp_loss_fraction{destination_country="IT"})
   # → 4.2% average
   ```

3. **Compare to other destinations:**
   - Domestic US: 0.3% loss
   - Other European: 1.5% loss
   - Italy: 4.2% loss ← Elevated

4. **Check network path:**
   ```bash
   mtr -r 100 -c 100 carrier-italy-ip
   ```
   - High loss on a specific intermediate hop
   - Packet loss correlates with Italian carrier peering

5. **Root cause:** Network path to Italy has elevated loss (>4%)
   - G.729 is fragile at 4% loss
   - Result: Robotic audio and drops

**Mitigation:** Route Italy calls through alternate carrier during investigation

**Resolution:** Work with carrier and transit providers to identify and fix the lossy path

**Prevention:** Configure codec fallback — if G.729 produces high loss, fall back to G.711 even though it uses more bandwidth

---

**Key Takeaways:**

1. Acoustic echo is local (user-side) — hybrid echo comes from TDM impedance mismatch at 2-wire/4-wire conversion
2. Choppy audio = jitter buffer underrun, packet loss, or CPU overload — check RTCP jitter and loss metrics
3. Robotic audio indicates extreme packet loss (especially with CELP codecs like G.729) or multiple transcoding hops
4. High latency (>300ms) breaks natural conversation — propagation delay is physics, transcoding and jitter buffers can be optimized
5. Cross-talk suggests SS7/TDM issues or address collisions — verify unique RTP 5-tuples and TDM timeslot alignment
6. Quality issues require correlating RTCP metrics with network path analysis (MTR) and geographic routing
7. Archive "golden" call traces with good quality for comparison — seeing the baseline helps identify degradation

**Next: Lesson 116 — Message Delivery Failures — Systematic Troubleshooting**
