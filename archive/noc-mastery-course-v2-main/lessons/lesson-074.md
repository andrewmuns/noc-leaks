# Lesson 74: Telnyx WebRTC Architecture — Voice SDK and Proxy

**Module 2 | Section 2.4 — WebRTC**
**⏱ ~8 min read | Prerequisites: Lessons 54-56, 57**

---

## Bridging Two Worlds: WebRTC and SIP

WebRTC (Lessons 54-56) and SIP (Lessons 37-47) are both real-time communication protocols, but they speak different languages. WebRTC uses WebSocket signaling, DTLS-SRTP for media, ICE for NAT traversal, and mandates Opus codec. SIP uses SIP signaling (over UDP/TCP/TLS), RTP or SRTP for media, and typically uses G.711 or G.729.

Telnyx's WebRTC product bridges these two worlds, allowing a browser-based application to make and receive phone calls through the PSTN. The key component is the **voice-sdk-proxy** — a gateway that translates between WebRTC and SIP in real-time.

## The Architecture Stack

```
Browser/App                    Telnyx                           PSTN
┌──────────┐     ┌──────────────────────────┐     ┌──────────────┐
│ Telnyx   │     │                          │     │              │
│ Voice    │────▶│  voice-sdk-proxy          │────▶│  SIP/TDM     │
│ SDK      │ WS  │  (WebRTC↔SIP gateway)    │ SIP │  Gateway     │
│          │     │                          │     │              │
│ Browser  │────▶│  TURN/STUN Servers       │────▶│              │
│ Media    │DTLS │  Media Relay             │ RTP │              │
└──────────┘     └──────────────────────────┘     └──────────────┘
```

### Layer 1: Signaling (WebSocket → SIP)

The browser-side SDK establishes a persistent WebSocket connection to the voice-sdk-proxy. This WebSocket carries signaling messages — the equivalent of SIP messages but in a JSON format the SDK understands.

When the browser initiates a call:
1. SDK sends a call request over WebSocket (containing an SDP offer with ICE candidates)
2. voice-sdk-proxy translates this into a SIP INVITE with a new SDP for the SIP side
3. The SIP INVITE is routed through Telnyx's normal call routing (Lesson 58)
4. SIP responses flow back, are translated to WebSocket messages, and sent to the SDK

For incoming calls:
1. A SIP INVITE arrives at Telnyx for a number configured to a WebRTC credential
2. voice-sdk-proxy sends a push notification or WebSocket event to the client
3. The SDK presents the incoming call to the application
4. When answered, the SDP exchange completes in both directions

### Layer 2: Media (DTLS-SRTP → RTP/SRTP)

Media translation is the harder problem. The browser sends encrypted media via DTLS-SRTP (mandatory in WebRTC — Lesson 52). The PSTN side expects plain RTP or SRTP with SDES key exchange.

The voice-sdk-proxy:
1. Terminates the DTLS-SRTP connection from the browser
2. Decrypts the incoming Opus audio
3. Transcodes from Opus to the SIP-side codec (often G.711)
4. Re-encrypts (if SRTP is configured) or sends plain RTP to the SIP side

This transcoding step is CPU-intensive but unavoidable — Opus and G.711 are fundamentally different codecs (Lessons 6, 8).

### Layer 3: NAT Traversal (ICE/TURN)

WebRTC's ICE framework (Lesson 55) handles NAT traversal on the browser side. The browser gathers ICE candidates:
- **Host candidates**: local IP addresses (useless for reaching Telnyx from behind NAT)
- **Server-reflexive candidates**: public IP discovered via STUN (works for most NATs)
- **Relay candidates**: TURN server allocation (works through any firewall allowing outbound UDP/TCP)

Telnyx operates TURN servers that WebRTC clients use when direct connectivity fails. The ICE negotiation determines the best path:

1. Best case: direct STUN path (lowest latency)
2. Fallback: TURN relay through Telnyx's servers (adds latency but always works)
3. Last resort: TURN over TCP/TLS port 443 (works through the most restrictive firewalls)

🔧 **NOC Tip:** If a WebRTC customer reports "works on my home network but not at the office," the office firewall is likely blocking UDP. The ICE fallback should use TURN over TCP/443, but if TURN servers are overloaded or misconfigured, this fallback fails. Check TURN server health in Grafana.

## Authentication: JWT Tokens

WebRTC clients authenticate using JSON Web Tokens (JWTs). The flow:

1. Customer's backend server requests a JWT from Telnyx's API (using API credentials)
2. Backend passes the JWT to the browser/app
3. SDK includes the JWT when connecting the WebSocket to voice-sdk-proxy
4. voice-sdk-proxy validates the JWT signature and claims

JWTs expire after a configured period. If the application doesn't refresh the token, the WebSocket connection will be rejected on reconnect.

**Common auth failures:**
- Expired JWT — application didn't implement token refresh
- Wrong credential resource — JWT was generated for a different SIP connection
- Clock skew — client or server time is significantly wrong, causing premature token expiry

## The Telnyx Voice SDK

Telnyx provides SDKs for multiple platforms:
- **JavaScript** (browser): The primary WebRTC SDK
- **React Native**: Mobile apps using WebRTC
- **iOS/Android native**: Native mobile SDKs

The SDK handles:
- WebSocket connection management (including reconnection)
- ICE candidate gathering and negotiation
- Media stream management (microphone access, audio output)
- DTMF sending (RFC 2833 over the WebRTC media path)
- Call state management (ringing, answered, held, etc.)

## What Makes WebRTC Debugging Different

WebRTC debugging is fundamentally different from SIP debugging because **half the call happens in the browser**, outside Telnyx's visibility.

For SIP calls, Telnyx sees both legs of the B2BUA. For WebRTC, the browser-to-TURN-server media path is partially opaque. You can see:
- WebSocket signaling messages (server-side logs)
- TURN allocation and relay statistics
- SIP-side of the call (normal SIP debugging)
- ICE negotiation results

You **cannot** directly see:
- Browser-side media quality (unless the customer provides chrome://webrtc-internals data)
- Local network conditions between the browser and Telnyx's TURN servers
- Browser permission issues, microphone problems, audio output routing

🔧 **NOC Tip:** When investigating WebRTC call quality, always ask the customer to capture `chrome://webrtc-internals` data during a problematic call. This provides ICE candidate pairs, packet loss, jitter, round-trip time, and codec information from the browser's perspective. Without this, you're debugging blind on the client side.

## Troubleshooting Scenario: "WebRTC Calls Connect But No Audio"

A customer's browser-based softphone shows "connected" but both parties hear silence.

**Investigation:**
1. Check SIP-side: SDP exchange looks correct, RTP packets are flowing from PSTN to voice-sdk-proxy ✓
2. Check WebSocket signaling: call established, SDP answer received by browser ✓
3. Check ICE: candidate pairs show the relay (TURN) candidate was selected — but the TURN allocation shows zero media packets relayed
4. Check TURN server: the specific TURN server assigned to this session has a network interface issue — it accepted the allocation but can't relay traffic
5. Restarting the TURN server instance resolved the issue

The call signaling completed successfully on both sides, but the media relay was broken at the TURN server level.

---

**Key Takeaways:**
1. voice-sdk-proxy is the core component that bridges WebRTC signaling (WebSocket) and SIP, plus DTLS-SRTP and RTP media
2. Transcoding between Opus (WebRTC) and G.711 (SIP/PSTN) is CPU-intensive but unavoidable
3. ICE/TURN provides NAT traversal — TURN relay is the fallback when direct paths fail (common in corporate networks)
4. JWT authentication has expiry — token refresh failures cause connection drops
5. WebRTC debugging requires client-side data (chrome://webrtc-internals) because half the call is in the browser
6. "Connected but no audio" in WebRTC often traces to TURN relay issues or ICE candidate selection problems

**Next: Lesson 65 — WebRTC Troubleshooting: ICE Failures, Media Issues, Browser Quirks**
