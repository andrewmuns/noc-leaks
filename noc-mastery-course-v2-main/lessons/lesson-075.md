# Lesson 75: WebRTC Troubleshooting — ICE Failures, Media Issues, Browser Quirks

**Module 2 | Section 2.4 — WebRTC**
**⏱ ~7 min read | Prerequisites: Lesson 64**

---

## The Unique Challenge of WebRTC Debugging

WebRTC problems are harder to debug than SIP problems because the client is a browser — an environment you don't control. You can't SSH into a customer's Chrome tab. You can't packet-capture their local network. You depend on client-side diagnostic tools and the customer's willingness to help gather data.

This lesson covers the most common WebRTC failure categories and systematic approaches to each.

## ICE Failures: "Can't Establish Media Path"

ICE failure is the WebRTC equivalent of "no audio" — the browser and Telnyx couldn't agree on a media path. ICE goes through candidate gathering → connectivity checks → nomination. Failure at any stage means no media.

### Common ICE Failure Causes

**1. Corporate Firewall Blocking All UDP**

Many enterprise firewalls block outbound UDP entirely. Since RTP and STUN use UDP, direct and server-reflexive candidates fail. The fallback is TURN over TCP or TURN over TLS (port 443).

If TURN-over-TLS-443 is also blocked (rare but happens with SSL inspection proxies), ICE fails completely.

**Diagnostic:** In `chrome://webrtc-internals`, look at the ICE candidate pairs. If all UDP candidates show "failed" and only TCP relay candidates exist but also failed, it's a firewall issue.

**2. TURN Server Unreachable**

If the TURN servers Telnyx provides in the ICE configuration are unreachable (DNS failure, server down, network issue), the browser can't get relay candidates. Without relay candidates, restrictive networks have no fallback.

🔧 **NOC Tip:** Check TURN server health in Grafana. Look at allocation success rate and active relay count. If a TURN server is unhealthy, it still appears in the configuration but fails allocations — browsers get no relay candidates.

**3. Symmetric NAT (Lesson 26)**

Symmetric NAT assigns different port mappings for different destinations. STUN-discovered candidates (server-reflexive) may not work because the NAT mapping used for STUN differs from the one used for media. TURN relay is required.

**4. ICE Timeout**

ICE connectivity checks have a timeout. If the network is slow (high latency, packet loss), checks may time out before finding a working pair. This is common on poor mobile connections.

### Reading ICE Candidate Pairs

In `chrome://webrtc-internals`, the ICE candidates section shows:
- **Local candidates:** what the browser discovered about itself (host, srflx, relay)
- **Remote candidates:** what Telnyx provided
- **Candidate pairs:** each local+remote combination and its state (waiting, in-progress, succeeded, failed)

The selected pair shows which path media is actually flowing through. If the selected pair uses a relay candidate, media goes through the TURN server (higher latency).

## Browser Permission Issues

### Microphone Access Denied

If the user denies microphone permission or their browser settings block it, the SDK can't capture audio. The call may "connect" (signaling completes) but there's no outgoing audio.

**Diagnostic:** The SDK raises an error when `getUserMedia()` fails. Check if the customer's application handles this error and displays it to the user.

### Autoplay Policy

Modern browsers block audio autoplay. If the incoming call's audio isn't triggered by a user gesture (click/tap), the browser may mute it. This manifests as "I can talk but can't hear the other person."

🔧 **NOC Tip:** If a customer reports one-way audio only on incoming calls (outbound works fine), autoplay policy is the likely cause. The customer needs to ensure their UI requires a user interaction (like clicking an "Accept Call" button) before playing the remote audio stream.

## Media Quality Issues

### High Jitter / Packet Loss in WebRTC

WebRTC has built-in quality adaptation — Opus adjusts its bitrate based on network conditions, and FEC (Forward Error Correction) helps recover lost packets. But severe network degradation still causes audible quality issues.

**Diagnostic:** `chrome://webrtc-internals` shows:
- `packetsLost` — count of lost RTP packets
- `jitter` — interarrival jitter in seconds
- `roundTripTime` — end-to-end RTT
- `framesDecoded`, `totalDecodeTime` — decode performance

If `packetsLost` is climbing rapidly, the network between the browser and Telnyx (or TURN server) is dropping packets. Run an MTR from the customer's network to the TURN server IP.

### Echo in WebRTC Calls

Browsers handle acoustic echo cancellation (AEC) internally. WebRTC mandates AEC in the `getUserMedia()` constraints. If echo is present:
- The user might be using external speakers + microphone (AEC less effective)
- Their browser's AEC implementation might be buggy (rare but happens)
- The echo might be on the PSTN side (hybrid echo from TDM gateway — Lesson 115)

### Audio Device Switching

Users switching headphones/speakers mid-call can cause audio dropouts. The browser may not automatically route to the new device. Some SDK implementations handle `devicechange` events, others don't.

## Browser-Specific Quirks

### Chrome
- Best WebRTC support overall
- `chrome://webrtc-internals` provides excellent diagnostics
- Extensions can interfere (ad blockers, VPN extensions, privacy tools)

### Firefox
- Good WebRTC support but some behavioral differences in ICE
- `about:webrtc` for diagnostics (less detailed than Chrome's)
- Different default audio processing behavior

### Safari
- Historically the worst WebRTC support, now significantly improved
- Requires user gesture for `getUserMedia()` on first use
- Different ICE candidate gathering behavior
- iOS Safari: WebRTC only works in Safari, not in-app browsers (WKWebView limitation)

🔧 **NOC Tip:** When a customer reports "WebRTC works in Chrome but not Safari," check if their code handles Safari's stricter autoplay and permission requirements. Safari also uses different VP8/H.264 preferences for video, though this is less relevant for voice-only calls.

## The chrome://webrtc-internals Goldmine

This is your single most valuable tool for WebRTC debugging. It shows:

1. **ICE Candidates**: every candidate gathered and checked, with state transitions
2. **ICE Candidate Pairs**: which pair was selected, round-trip time per pair
3. **RTP Stats**: packets sent/received, bytes, packet loss, jitter — updated in real-time
4. **Codec**: which audio codec was negotiated (should be Opus for WebRTC)
5. **DTLS State**: handshake success/failure
6. **Track Stats**: audio level, echo return loss, audio energy

Ask customers to:
1. Open `chrome://webrtc-internals` before making the call
2. Make the problematic call
3. Click "Create Dump" and send you the JSON file

## Troubleshooting Scenario: "Calls Drop After 30 Seconds"

A customer's WebRTC calls connect but disconnect after exactly 30 seconds.

**Investigation:**
1. The WebSocket connection is alive — signaling isn't the issue
2. SIP-side: the call is active, no BYE sent from Telnyx
3. ICE: the initial ICE check succeeded, but the selected candidate pair goes stale
4. The browser's ICE consent checks (periodic STUN checks to verify the path is still working) are failing after the first 30s
5. Root cause: the customer's corporate firewall has a 30-second UDP session timeout — after 30s of inactivity on the specific port mapping, it closes the pinhole

**Resolution:** The customer's IT team increased the UDP session timeout to 120 seconds. Alternatively, the SDK's keepalive interval could be configured to send traffic more frequently.

---

**Key Takeaways:**
1. ICE failures are the #1 WebRTC connectivity issue — usually caused by firewalls blocking UDP; TURN relay is the fallback
2. Browser permission issues (microphone denied, autoplay policy) cause "connected but no/one-way audio"
3. `chrome://webrtc-internals` is the essential client-side diagnostic tool — always ask for a dump
4. Safari has stricter permission and autoplay requirements than Chrome
5. Corporate firewalls with short UDP timeouts can cause calls to drop at consistent intervals
6. Half of WebRTC debugging happens on the client side, outside Telnyx's visibility — customer cooperation is essential

**Next: Lesson 66 — Voice AI Architecture: AI Assistants and the Processing Pipeline**
