# NOC Mastery Course

A comprehensive deep-dive curriculum for Telnyx NOC engineers — 196 lessons covering telecommunications fundamentals, Telnyx product portfolio, infrastructure operations, and incident response.

## Course Overview

**196 lessons | ~160 hours | 6 modules**

Each lesson is a 5-10 minute deep read with conceptual explanations, cross-layer connections, and real-world troubleshooting guidance using Grafana, Graylog, Loki, Consul, kubectl, Wireshark, and other NOC tools.

## Modules

### Module 1 — Foundations (Lessons 1-70)

How communications work — from analog telephony to modern protocols, plus the full Telnyx communications product suite.

- **Section 1.1 — The PSTN** (Lessons 1-4): Telephony history, circuit switching, SS7, number portability
- **Section 1.2 — Identity** (Lessons 5-6): Number Lookup, CNAM, Verify API
- **Section 1.3 — Digital Voice** (Lessons 7-9): Nyquist theorem, PCM, G.711, compressed codecs
- **Section 1.4 — Voice Quality** (Lessons 10-12): Jitter, latency, MOS scoring
- **Section 1.5 — IP Networking** (Lessons 13-22): IP, TCP/UDP, Wireshark, DNS, SRV, NAPTR
- **Section 1.6 — BGP** (Lessons 23-27): Autonomous systems, BGP mechanics, peering, hijacks
- **Section 1.7 — NAT** (Lessons 28-30): NAT types, STUN, TURN, SBCs
- **Section 1.8 — RTP/RTCP** (Lessons 31-32): RTP headers, RTCP quality metrics
- **Section 1.9-1.12 — SIP** (Lessons 33-51): Registration, INVITE, SDP, codec negotiation
- **Section 1.13 — Troubleshooting** (Lessons 52-53): Systematic call quality debugging, traceroute
- **Section 1.14 — Security** (Lessons 54-55): SRTP, DTLS, encryption
- **Section 1.15 — WebRTC** (Lessons 56-58): WebRTC architecture, ICE, gateway
- **Section 1.16 — Special Protocols** (Lessons 59-63): T.38 fax, Fax API, DTMF, REFER, conferencing
- **Section 1.17 — Programmable Voice** (Lessons 64-65): TeXML, MS Teams/Zoom integration
- **Section 1.18 — Messaging** (Lessons 66-70): SMS/MMS, Telnyx Messaging API, 10DLC, short codes, RCS

### Module 2 — Telnyx Infrastructure (Lessons 71-106)

Deep dive into Telnyx's platform architecture and the full product portfolio.

- **Section 2.1-2.12 — Voice Platform** (Lessons 71-98): Multi-tenant architecture, Call Control API, B2BUA, Voice AI, AI Assistants
- **Section 2.13 — Business Systems** (Lessons 99-100): Billing, STIR/SHAKEN, number porting, E911
- **Section 2.14 — IoT/Wireless** (Lessons 101-103): IoT SIM cards, eSIM, Mobile Voice
- **Section 2.15 — Networking** (Lesson 104): Private networking, Cloud VPN, Global Edge Router
- **Section 2.16 — Compute** (Lessons 105-106): Inference API, LLM Library, Embeddings, Storage

### Module 3 — Kubernetes & Observability (Lessons 107-136)

Container orchestration, service discovery, and monitoring infrastructure.

### Module 4 — Monitoring & Alerting (Lessons 137-166)

Prometheus, Grafana, logging, and alert management.

### Module 5 — Incident Response (Lessons 167-191)

Incident lifecycle, post-mortems, communication, and career development.

### Module 6 — Future & Capstone (Lessons 192-196)

AIOps, 5G, AI voice agents, and two full incident simulations.

## Telnyx Products Covered

The course covers the complete Telnyx product portfolio:

**Communications:**
- Voice API and Call Control API
- SIP Trunking
- WebRTC SDK
- TeXML
- Voice AI / AI Assistants
- SMS API and MMS API
- 10DLC Registration
- Short Codes
- RCS
- Alphanumeric Sender ID
- Fax API
- Microsoft Teams Direct Routing
- Zoom Phone BYOC

**Numbers & Identity:**
- Global Numbers and Toll-Free Numbers
- Number Lookup API / CNAM
- Verify API (2FA)
- Number Porting
- STIR/SHAKEN
- E911

**IoT:**
- IoT SIM Cards
- eSIM and OTA Management
- Mobile Voice

**Networking:**
- Programmable Networking
- Cloud VPN
- Global Edge Router

**Compute:**
- Inference API (LLM serving)
- LLM Library
- Embeddings API
- Telnyx Storage

## Structure

```
noc-mastery-course/
├── README.md           # This file
├── curriculum.md       # Full curriculum with lesson outlines
├── progress.json       # Delivery progress tracker
└── lessons/
    ├── lesson-001.md   # Lesson 1
    ├── lesson-002.md   # Lesson 2
    ├── ...
    └── lesson-196.md   # Lesson 196 (Course Completion)
```

## Lesson Format

Each lesson includes:
- Module, section, estimated read time, and prerequisites
- Deep educational content with clear section headers
- Code blocks for commands, API calls, and configurations
- 🔧 **NOC Tip** callout boxes with practical Telnyx-specific advice
- Real-world troubleshooting scenarios
- Numbered key takeaways
- Navigation to the next lesson

## Getting Started

Start with Lesson 1 and work sequentially. Each lesson builds on previous ones. Estimated pace: 5 lessons per day = ~40 days to complete.
