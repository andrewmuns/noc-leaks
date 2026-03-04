# Lesson 58: WebRTC-to-SIP Gateway — Bridging Browser and PSTN

**Module 1 | Section 1.15 — WebRTC**
**⏱ ~7 min read | Prerequisites: Lessons 54, 55**

---

## The Gateway Problem

WebRTC browsers speak a different language than SIP phones:

| Aspect | WebRTC | SIP |
|--------|--------|-----|
| Signaling | Implementation-defined | SIP protocol |
| Encryption | DTLS-SRTP (mandatory) | SDES or DTLS-SRTP |
| Audio codec | Opus (mandatory) | G.711 (common) |
| Video codec | VP8/H.264 | H.264 (sometimes) |
| Transport | SRTP over UDP | RTP/RTCP over UDP |
| NAT Traversal | ICE built-in | Manual STUN/TURN |

A gateway is needed to bridge these worlds.

---

## Telnyx voice-sdk-proxy

Telnyx's **voice-sdk-proxy** handles WebRTC↔SIP translation:

```
Browser (WebRTC)            voice-sdk-proxy           SIP Endpoint
       |                           |                         |
       |<-- WebSocket/JSON ------> |                         |
       |                           |<------ SIP/SDP -------->|
       |                           |                         |
       |<========== DTLS-SRTP ==============================>|
       |      (Opus media, relayed through proxy)            |
```

**Proxy functions:**
- WebRTC signaling (WebSocket) ↔ SIP translation
- Opus ↔ G.711 transcoding
- DTLS-SRTP ↔ RTP conversion
- ICE ↔ STUN/TURN handling
- Media anchoring (always)

---

## Signaling Translation

### WebRTC Side (JavaScript)

```javascript
// Browser sends JSON over WebSocket
{
  "method": "telnyx.invite",
  "params": {
    "destination_number": "+13125551234",
    "audio": true,
    "video": false
  }
}
```

### SIP Side

```sip
INVITE sip:+13125551234@telnyx.com SIP/2.0
Via: SIP/2.0/UDP 10.0.0.5:5060
Contact: <sip:user@10.0.0.5:5060>
Subject: Call
Content-Type: application/sdp

v=0
o=- 0 0 IN IP4 10.0.0.5
s=-
c=IN IP4 10.0.0.5
t=0 0
m=audio 10000 RTP/AVP 0 101
a=rtpmap:0 PCMU/8000
a=rtpmap:101 telephone-event/8000
```

**Translation performed:**
- JSON method → SIP method
- Phone number → SIP URI
- ICE candidates → SDP connection lines
- Opus preferences → G.711 fallback

---

## Media Translation: Opus ↔ G.711

Opus and G.711 are fundamentally different:

| Property | Opus | G.711 |
|----------|------|-------|
| Compression | High (6-32 kbps) | None (64 kbps) |
| Frame size | 2.5-60ms | 20ms fixed |
| Algorithm | Hybrid | Log PCM |
| Complexity | CPU-intensive | Minimal |

### Transcoding Process

1. Receive Opus packet from WebRTC
2. Decode Opus → PCM
3. Encode PCM → G.711 μ-law/A-law
4. Forward to SIP side

**Reverse for incoming G.711 → Opus.**

**Cost:**
- CPU: ~5-10% per transcoded call core
- Latency: +10-20ms
- Quality: Small loss from re-encoding

🔧 **NOC Tip:** Monitor transcoding load on voice-sdk-proxy. If CPU is high but call volume is normal, check if more WebRTC↔PSTN calls are happening (vs WebRTC↔WebRTC which doesn't need transcoding).

---

## DTLS-SRTP to RTP Conversion

### DTLS-SRTP (WebRTC)

```
1. DTLS handshake (over UDP)
2. Extract SRTP keys from DTLS
3. Encrypt RTP with SRTP
4. Send SRTP packets
```

### RTP (legacy systems)

```
1. Receive unencrypted or SDES-SRTP RTP
2. Forward as-is
```

### Proxy Role

The proxy terminates DTLS:
```
WebRTC          voice-sdk-proxy         SIP
   |                  |                   |
   |<--- DTLS ------->|                   |
   |   (keys)         |                   |
   |<== SRTP ========>|                   |
   |                  |<--- Unencrypted ->|
   |                  |      or SDP       |
   |                  |                   |
```

**Key handling:**
- Generates SRTP keys during DTLS handshake
- Encrypts traffic to/from browser
- Decrypts and forwards to SIP side (may re-encrypt with SDES if needed)

---

## WebRTC to PSTN Call Flow

1. **Browser initiates:**
   ```javascript
   client.newCall({ destination_number: '+13125551234' });
   ```

2. **Proxy receives WebSocket invite**

3. **Proxy creates SIP INVITE:**
   - Translates number to SIP URI
   - Generates SDP with G.711 offer
   - Routes via Telnyx B2BUA

4. **Ringing → Answer:**
   - 180 Ringing ← 183 Session Progress
   - 200 OK ← Answer

5. **Media path established:**
   - Browser ←→ Proxy (Opus/DTLS-SRTP)
   - Proxy ←→ PSTN (G.711/RTP)
   - Proxy transcodes in real-time

6. **Call ends:**
   - BYE from either side
   - Proxy translates both directions

---

## Optimizing WebRTC ↓ SIP Calls

### Opus-to-Opus Passthrough

If the remote SIP endpoint supports Opus (rare but growing):

```
Browser (Opus) ←→ voice-sdk-proxy ←→ SIP PBX (Opus)
                     (passthrough, no transcoding!)
```

**Benefits:**
- No transcoding latency
- No CPU load
- No audio degradation

**Detection:** SDP negotiation:
```sdp
m=audio 10000 RTP/AVP 96 0
a=rtpmap:96 opus/48000/2
a=rtpmap:0 PCMU/8000
```
If both sides put Opus first, transcoding is avoided.

### Direct Media (Advanced)

Some deployments support "direct media" where:
- Signaling goes through proxy
- Media flows directly browser ↔ SIP endpoint (after ICE)

**Requirements:**
- SIP endpoint supports ICE
- No NAT between SIP endpoint and internet
- Both support compatible codecs

Rare in practice but becoming more common with modern IP-PBXs.

🔧 **NOC Tip:** Check `voice.webrtc.transcoding.calls` metric in Grafana. If it's 100%, every WebRTC call is being transcoded. Work with customers to enable Opus on their SIP infrastructure if possible.

---

## Key Takeaways

1. **Protocol translation:** voice-sdk-proxy converts WebSocket/JSON ↔ SIP/SDP
2. **Codec transcoding:** Opus → G.711 adds latency and CPU cost
3. **Encryption bridging:** DTLS-SRTP terminated at proxy, may re-encrypt as SDES
4. **Media anchoring:** All traffic passes through proxy for control and troubleshooting
5. **Optimization:** Opus passthrough when possible eliminates transcoding overhead
6. **Browser to PSTN:** Full translation stack required for every call

---

**Next: Lesson 57 — T.38 Fax over IP — Why Fax Still Matters**
