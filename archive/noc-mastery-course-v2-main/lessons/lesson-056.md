# Lesson 56: WebRTC Architecture — Browser-Based Real-Time Communication

**Module 1 | Section 1.15 — WebRTC**
**⏱ ~8 min read | Prerequisites: Lessons 52, 27**

---

## WebRTC: The Browser Becomes a Phone

WebRTC turns web browsers into VoIP endpoints without plugins. iIt's how Telnyx's WebRTC SDK works, enabling voice calls directly from browser-based applications.

---

## WebRTC APIs

Three JavaScript APIs provide the functionality:

### getUserMedia()

Captures local audio/video:

```javascript
navigator.mediaDevices.getUserMedia({
  audio: true,
  video: false
}).then(stream => {
  // Attach to audio element
  localAudio.srcObject = stream;
});
```

**Permissions:** Browser prompts user for microphone access. HTTPS required for production.

### RTCPeerConnection

The core of WebRTC — handles:
- ICE candidate gathering
- DTLS handshake for SRTP keys
- Media encoding/decoding (Opus mandatory)
- Network adaptation (bandwidth estimation)

```javascript
const pc = new RTCPeerConnection({
  iceServers: [
    { urls: 'stun:stun.telnyx.com:3478' },
    { urls: 'turn:turn.telnyx.com:3478', credential: '...' }
  ]
});

// Add local stream
stream.getTracks().forEach(track => {
  pc.addTrack(track, stream);
});
```

### RTCDataChannel

Bidirectional data between browsers — like WebSocket but peer-to-peer:

```javascript
const channel = pc.createDataChannel('messages');
channel.send('Hello from browser A');
```

---

## Mandatory Security: DTLS-SRTP

WebRTC mandates encryption — no unencrypted option exists.

### The DTLS Handshake

1. Signaling exchanges SDP
2. WebRTC generates DTLS certificate (self-signed, per-session)
3. DTLS handshake over UDP (like TLS but datagram)
4. Keys derived from DTLS used for SRTP
5. Media encrypted with SRTP

**Fingerprint verification:** SDP includes certificate fingerprint:
```
a=fingerprint:sha-256 12:34:56:78:...
```

Browsers verify this matches the actual certificate presented during DTLS.

🔧 **NOC Tip:** If WebRTC calls connect but no audio flows, check DTLS handshake success in Chrome's `chrome://webrtc-internals`. Failed DTLS = no SRTP keys = no media.

---

## Mandatory Codecs

### Audio: Opus

- **Sample rate:** 8-48 kHz (adaptive)
- **Bit rate:** 6-510 kbps (adaptive)
- **Behavior:** Adapts to bandwidth automatically
- **Quality:** Better than G.711 at half the bandwidth

### Video

- **VP8:** Open, royalty-free
- **H.264:** For Safari compatibility
- **VP9:** Higher compression (optional)

---

## Signaling: The Missing Piece

WebRTC doesn't specify signaling — you bring your own:

```
Browser A                           Browser B
   |                                    |
   |--- SDP offer (via your signaling) -->|
   |<-- SDP answer (via your signaling) --|
   |                                    |
   |==== DTLS handshake ================|
   |==== SRTP media flows ==============|
```

**Common signaling methods:**
- WebSocket
- HTTP POST
- Socket.io
- Custom protocol

### Telnyx WebRTC Signaling

Telnyx provides the signaling infrastructure:

```javascript
const client = new TelnyxRTC({
  login_token: '...',
  ringtoneFile: './ringtone.mp3'
});

client.connect();
client.on('telnyx.ready', () => {
  client.newCall({
    destination_number: '+13125551234'
  });
});
```

---

## ICE: Making the Connection

WebRTC uses ICE (Interactive Connectivity Establishment) to find paths:

1. **Gather candidates:** Host, server reflexive (STUN), relay (TURN)
2. **Connectivity checks:** Test which paths work
3. **Nominate best:** Lowest priority number wins
4. **Switch if needed:** Seamless handoff on path failure

See Lesson 55 for deep ICE coverage.

---

## WebRTC vs Traditional SIP

| Aspect | WebRTC | Traditional SIP |
|--------|--------|-----------------|
| Encryption | Mandatory DTLS-SRTP | Optional SDES or DTLS |
| Transport | UDP (RTP) | UDP/TCP/TLS |
| Codec | Opus mandatory | G.711 common |
| Signaling | BYO (flexible) | SIP protocol |
| NAT Traversal | Built-in ICE/STUN/TURN | Manual configuration |
| Browser | Native support | Requires plugin |

🔧 **NOC Tip:** WebRTC to SIP calls traverse Telnyx's voice-sdk-proxy. This handles Opus→G.711 transcoding and all the complex signaling translation between WebSocket/JSON and SIP/SDP.

---

## Key Takeaways

1. **Three WebRTC APIs:** getUserMedia (capture), RTCPeerConnection (transport), RTCDataChannel (data)
2. **DTLS-SRTP is mandatory** — no unencrypted WebRTC exists
3. **Opus is mandatory** for audio — adaptive, high quality, low bandwidth
4. **Signaling is not defined** by WebRTC — you provide the signaling channel
5. **ICE handles NAT** automatically — built-in STUN/TURN support
6. **Telnyx abstracts complexity** — voice-sdk-proxy handles WebRTC↔SIP bridging

---

**Next: Lesson 55 — ICE — Interactive Connectivity Establishment**
