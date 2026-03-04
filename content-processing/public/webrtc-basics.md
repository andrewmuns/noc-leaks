---
content_type: truncated
description: "Learn about webrtc architecture \u2014 browser-based real-time communication"
difficulty: Advanced
duration: 8 minutes
full_content_available: true
lesson: '56'
module: 'Module 1: Foundations'
objectives:
- "Understand webrtc architecture \u2014 browser-based real-time communication"
slug: webrtc-basics
title: "WebRTC Architecture \u2014 Browser-Based Real-Time Communication"
word_limit: 300
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

---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios
- ✅ Practice quizzes and assessments

[**🚀 Unlock Full Course Access**](https://teleponymastery.com/enroll)

---

*Preview shows approximately 25% of the full lesson content.*