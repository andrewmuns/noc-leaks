# NOC Mastery Course — Deep-Dive Curriculum for Telnyx NOC Engineers

> **Total Lessons:** 182  
> **Estimated Total Study Time:** ~150 hours (900–1800 minutes)  
> **Format:** Each lesson is a 5–10 minute deep read with conceptual explanations, cross-layer connections, and real-world troubleshooting guidance using Grafana, Graylog, Loki, Consul, kubectl, Wireshark, and other NOC tools.

---

## Module 1 — How Communications Work (Foundations)

*This module builds your understanding from the ground up — from analog telephone networks to modern real-time protocols. Every lesson explains WHY things work the way they do, not just what they are.*

---

### Section 1.1 — The PSTN: History, Circuit Switching, and SS7

#### Lesson 1: The Birth of Telephony — From Bell to the Central Office
- **Module:** 1 — Foundations
- **Section:** 1.1 — The PSTN
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** None
- **Key Concepts:**
  1. Electromagnetic voice transmission and the carbon microphone
  2. The central office (CO) and the concept of switching
  3. Manual switchboards and why automation was inevitable
  4. The local loop — copper pair from subscriber to CO
  5. Why understanding PSTN history matters for modern VoIP debugging
- **Description:** Traces the evolution from Alexander Graham Bell's first call through the development of central offices. Explains the physical layer — the copper local loop — and why its characteristics (impedance, frequency response, distance limits) still influence voice engineering today. Connects to why codecs exist and why echo cancellation is necessary.

#### Lesson 2: Circuit Switching — Dedicated Paths and Why They Mattered
- **Module:** 1 — Foundations
- **Section:** 1.1 — The PSTN
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 1
- **Key Concepts:**
  1. Circuit switching vs. message switching — resource reservation
  2. Time-Division Multiplexing (TDM) and the DS0 (64 kbps channel)
  3. T1/E1 trunks — how 24/30 calls share a single physical link
  4. The concept of a "trunk group" and why it matters for capacity planning
  5. Blocking probability and the Erlang B formula
- **Description:** Explains how circuit switching works mechanically and electrically — a dedicated 64 kbps timeslot reserved end-to-end for the duration of a call. Covers TDM hierarchy (DS0 → DS1 → DS3), the math behind trunk sizing (Erlang models), and why these concepts still appear in modern SIP trunk capacity planning. Connects to why packet switching was a revolutionary change.

#### Lesson 3: SS7 Signaling — The Brain of the PSTN
- **Module:** 1 — Foundations
- **Section:** 1.1 — The PSTN
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lesson 2
- **Key Concepts:**
  1. In-band vs. out-of-band signaling and why SS7 replaced MF tones
  2. SS7 protocol stack: MTP1/2/3, SCCP, TCAP, ISUP, MAP
  3. Signal Transfer Points (STPs) and the signaling network topology
  4. ISUP messages: IAM, ACM, ANM, REL, RLC — the call setup sequence
  5. How SS7 enables caller ID, toll-free routing, and number portability (LNP)
- **Description:** Deep dive into SS7 architecture — the separate signaling network that controls the PSTN. Explains why separating signaling from bearer was transformative, how ISUP messages set up and tear down calls, and how databases (SCP/STP) enable intelligent routing. Directly connects to SIP — which is essentially SS7's spiritual successor for IP networks. Understanding SS7 call flows makes SIP call flows intuitive.

#### Lesson 4: Number Portability and the LNP Database
- **Module:** 1 — Foundations
- **Section:** 1.1 — The PSTN
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 3
- **Key Concepts:**
  1. Local Number Portability (LNP) — why numbers had to become portable
  2. The Number Portability Administration Center (NPAC) and LRN
  3. Location Routing Number (LRN) — how a ported number gets routed
  4. Dip queries — real-time database lookups before routing a call
  5. Impact on Telnyx: porting lifecycle, dip costs, routing decisions
- **Description:** Explains the regulatory and technical story of number portability. Covers how LRN works — when a number ports, the donor carrier's switch queries the NPAC to find the new carrier's LRN, then routes to that carrier's switch. Directly relevant to Telnyx number porting operations, number lookup APIs, and understanding why porting takes time.

---

### Section 1.2 — Digital Voice: Sampling, Quantization, and Codecs

#### Lesson 5: Analog to Digital — The Nyquist Theorem and PCM
- **Module:** 1 — Foundations
- **Section:** 1.2 — Digital Voice
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 2
- **Key Concepts:**
  1. The Nyquist-Shannon sampling theorem — why 8000 Hz for voice
  2. Human voice frequency range (300–3400 Hz) and telephone bandwidth
  3. Pulse Code Modulation (PCM) — sampling and quantization
  4. Quantization noise and Signal-to-Noise Ratio (SNR)
  5. Companding: μ-law vs A-law — why we use non-linear quantization
- **Description:** Explains the fundamental physics of converting analog voice to digital. Covers why 8 kHz sampling captures voice adequately (Nyquist), how quantization introduces noise, and why companding (μ-law in North America, A-law in Europe) was invented to improve dynamic range for quiet sounds. This is the foundation for understanding every codec and why G.711 uses 64 kbps.

#### Lesson 6: G.711 — The Universal Codec
- **Module:** 1 — Foundations
- **Section:** 1.2 — Digital Voice
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 5
- **Key Concepts:**
  1. G.711 μ-law and A-law — 64 kbps uncompressed PCM
  2. Why G.711 is the "lingua franca" of telephony
  3. Packetization: 20ms frames = 160 bytes per packet
  4. Bandwidth calculation: codec rate + IP/UDP/RTP overhead
  5. When to use G.711 vs. compressed codecs — quality vs. bandwidth tradeoff
- **Description:** Deep dive into G.711 — the simplest and most widely supported codec. Explains the math: 8000 samples/sec × 8 bits = 64 kbps, plus how packetization period affects latency and overhead. Calculates real bandwidth with IP/UDP/RTP headers (typically ~87 kbps for 20ms frames). Explains why G.711 remains preferred for PSTN interconnection and when it's appropriate vs. compressed alternatives.

#### Lesson 7: Compressed Codecs — G.729, G.722, and Why Compression Matters
- **Module:** 1 — Foundations
- **Section:** 1.2 — Digital Voice
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 6
- **Key Concepts:**
  1. Code-Excited Linear Prediction (CELP) — how G.729 compresses to 8 kbps
  2. G.729 Annex B — Voice Activity Detection (VAD) and Comfort Noise Generation (CNG)
  3. G.722 — wideband audio (7 kHz) and "HD Voice"
  4. Algorithmic delay — why compressed codecs add latency
  5. Transcoding — when and why codec conversion happens, and its CPU cost
- **Description:** Explains how G.729 achieves 8:1 compression using a model of the human vocal tract. Covers the quality-bandwidth-latency triangle and why each codec makes different tradeoffs. Introduces transcoding — what happens when two endpoints don't share a codec — and why it's expensive (CPU, quality loss, latency). Directly relevant to understanding Telnyx's media handling and B2BUA architecture.

#### Lesson 8: Opus — The Modern Codec and Why It Won
- **Module:** 1 — Foundations
- **Section:** 1.2 — Digital Voice
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 7
- **Key Concepts:**
  1. Opus: hybrid SILK + CELT architecture
  2. Adaptive bitrate — 6 kbps to 510 kbps in a single codec
  3. Forward Error Correction (FEC) built into Opus
  4. Why WebRTC mandates Opus
  5. Opus vs. legacy codecs: quality at equivalent bitrates (POLQA/PESQ scores)
- **Description:** Covers the Opus codec — the state of the art for real-time audio. Explains its hybrid architecture (SILK for speech, CELT for music), adaptive bitrate that responds to network conditions, and built-in FEC for packet loss resilience. Connects to WebRTC (where Opus is mandatory) and Telnyx's WebRTC product.

#### Lesson 9: Voice Quality Metrics — MOS, PESQ, POLQA, and R-Factor
- **Module:** 1 — Foundations
- **Section:** 1.2 — Digital Voice
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 6, 7, 8
- **Key Concepts:**
  1. Mean Opinion Score (MOS) — the 1-5 subjective quality scale
  2. PESQ and POLQA — algorithmic MOS estimation
  3. The E-Model and R-Factor — parametric quality prediction
  4. Impairment factors: codec, delay, jitter, packet loss
  5. How to read MOS/R-Factor in Grafana dashboards
- **Description:** Explains how voice quality is measured and modeled. The E-Model takes impairments (codec distortion, one-way delay, jitter buffer discard, packet loss) and computes an R-Factor (0–100) that maps to MOS. Covers how to interpret these metrics in Telnyx's monitoring systems and what thresholds indicate problems.

---

### Section 1.3 — Packet Switching vs. Circuit Switching

#### Lesson 10: Packet Switching — Store-and-Forward and Statistical Multiplexing
- **Module:** 1 — Foundations
- **Section:** 1.3 — Packet vs. Circuit Switching
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 2
- **Key Concepts:**
  1. Store-and-forward vs. cut-through switching
  2. Statistical multiplexing — sharing bandwidth efficiently
  3. Why packet switching enables the internet but introduces jitter
  4. Queuing theory basics: why packets experience variable delay
  5. Best-effort delivery — the fundamental challenge for real-time media
- **Description:** Contrasts circuit switching (guaranteed bandwidth, fixed delay) with packet switching (shared bandwidth, variable delay). Explains why statistical multiplexing is more efficient but introduces the core challenges of VoIP: jitter, packet loss, and reordering. This lesson is the bridge between PSTN thinking and IP thinking.

#### Lesson 11: Quality of Service (QoS) — DSCP, Traffic Shaping, and Why It Mostly Doesn't Work on the Internet
- **Module:** 1 — Foundations
- **Section:** 1.3 — Packet vs. Circuit Switching
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 10
- **Key Concepts:**
  1. DSCP markings — Expedited Forwarding (EF) for voice
  2. Traffic shaping vs. traffic policing
  3. Why QoS works on private networks but not across the public internet
  4. The role of overprovisioning as a substitute for QoS
  5. How Telnyx's private backbone provides QoS-like behavior
- **Description:** Explains DiffServ QoS mechanisms and why they're effective within managed networks but stripped at internet peering points. Covers why Telnyx's own backbone and interconnection strategy matters for call quality, and why customer last-mile networks are often the weakest link.

---

### Section 1.4 — The Internet Protocol Stack (Deep Dive)

#### Lesson 12: Ethernet and Layer 2 — Frames, MACs, VLANs, and Switching
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 10
- **Key Concepts:**
  1. Ethernet frame structure: preamble, MAC addresses, EtherType, payload, FCS
  2. MAC address tables and how switches learn
  3. VLANs (802.1Q) — logical network segmentation
  4. ARP — resolving IP to MAC addresses
  5. MTU, jumbo frames, and fragmentation implications
- **Description:** Deep dive into Layer 2 — the foundation everything else rides on. Explains how Ethernet frames are structured, how switches build MAC tables, and how VLANs segment traffic. Covers ARP (and its security implications) and MTU — critical for understanding why some SIP/RTP issues trace back to Layer 2 problems.

#### Lesson 13: IPv4 — Addressing, Subnetting, and the IP Header
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 12
- **Key Concepts:**
  1. IPv4 header fields: TTL, protocol, source/dest, flags, fragment offset
  2. Subnetting and CIDR notation — calculating network/host portions
  3. Private address ranges (RFC 1918) and their prevalence
  4. IP fragmentation — how it works and why it's terrible for VoIP
  5. ICMP — ping, traceroute, and unreachable messages
- **Description:** Thorough examination of IPv4. Covers the header field by field, explaining what each does and when NOC engineers need to inspect them. Subnetting math with practical examples. Special attention to fragmentation — why it causes problems for UDP-based real-time traffic and how Path MTU Discovery (PMTUD) helps avoid it.

#### Lesson 14: IPv6 — Why It Exists and What Changes
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 13
- **Key Concepts:**
  1. IPv6 address format and notation
  2. Elimination of NAT — every device gets a public address
  3. IPv6 header simplification — no fragmentation by routers
  4. Dual-stack, tunneling, and transition mechanisms
  5. Impact on SIP: no more NAT traversal headaches (in theory)
- **Description:** Covers IPv6 fundamentals and why it matters for telecom. The elimination of NAT could solve many SIP/RTP issues, but dual-stack complexity introduces its own problems. Covers how Telnyx handles IPv6 and the practical implications for NOC operations.

#### Lesson 15: UDP — Why Real-Time Traffic Chooses Unreliability
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 13
- **Key Concepts:**
  1. UDP header: source port, dest port, length, checksum — that's it
  2. No connection state, no retransmission, no ordering guarantees
  3. Why latency-sensitive applications prefer UDP over TCP
  4. UDP and firewalls — stateful tracking, timeouts, pinhole problems
  5. UDP checksum — optional in IPv4, mandatory in IPv6
- **Description:** Explains why UDP is the transport of choice for voice/video. TCP's retransmission and congestion control add latency that's worse than losing a packet. Covers firewall interaction — stateful firewalls track UDP "connections" with timers, and when those timers expire, media stops flowing. Directly relevant to NAT/firewall troubleshooting.

#### Lesson 16: TCP — Reliability, Congestion Control, and SIP over TCP/TLS
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 15
- **Key Concepts:**
  1. TCP three-way handshake and connection state machine
  2. Sequence numbers, acknowledgments, and retransmission
  3. Congestion control: slow start, congestion avoidance, fast retransmit
  4. TCP for SIP signaling — persistent connections and their benefits
  5. Head-of-line blocking — why TCP is bad for multiplexed real-time streams
- **Description:** Deep dive into TCP mechanics. Explains the state machine, flow control (window size), and congestion control algorithms. Covers why SIP signaling benefits from TCP (reliability, persistent connections, TLS support) but why media should never use TCP. Connects to understanding connection-oriented SIP trunks.

#### Lesson 17: TLS — How Encryption Works for SIP and HTTPS
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lesson 16
- **Key Concepts:**
  1. TLS handshake: ClientHello, ServerHello, certificate exchange, key agreement
  2. Certificate chains: root CA → intermediate → server certificate
  3. TLS 1.2 vs 1.3 — what changed and why it matters
  4. SNI — Server Name Indication and its role in SIP/HTTPS
  5. Mutual TLS (mTLS) — client certificates for SIP trunk authentication
- **Description:** Explains TLS from the ground up — the handshake, certificate validation, cipher suite negotiation, and key exchange. Covers why TLS 1.3 is faster (1-RTT handshake) and more secure. Directly relevant to Telnyx's SIP over TLS (SIPS) and HTTPS webhook delivery. Understanding TLS is essential for debugging certificate errors and connection failures.

#### Lesson 18: The Application Layer — HTTP, WebSockets, and gRPC
- **Module:** 1 — Foundations
- **Section:** 1.4 — Protocol Stack
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 17
- **Key Concepts:**
  1. HTTP/1.1 vs HTTP/2 vs HTTP/3 — evolution of web transport
  2. REST APIs — the foundation of Telnyx's API platform
  3. WebSockets — persistent bidirectional connections for real-time events
  4. gRPC — binary RPC for internal service communication
  5. Webhook delivery — HTTP POST callbacks and retry logic
- **Description:** Covers application-layer protocols relevant to Telnyx operations. HTTP for APIs and webhooks, WebSockets for real-time event streaming, gRPC for internal microservice communication. Understanding these is essential for debugging API issues, webhook delivery failures, and internal service communication problems.

---

### Section 1.5 — DNS Deep Dive

#### Lesson 19: DNS Fundamentals — Resolution, Records, and the Hierarchy
- **Module:** 1 — Foundations
- **Section:** 1.5 — DNS
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 13
- **Key Concepts:**
  1. DNS hierarchy: root → TLD → authoritative nameservers
  2. Recursive vs. iterative resolution
  3. Record types: A, AAAA, CNAME, MX, TXT, SRV, NAPTR
  4. TTL — Time to Live and caching behavior
  5. DNS for SIP: NAPTR and SRV records for service discovery
- **Description:** Comprehensive DNS walkthrough. Traces a query from stub resolver through recursive resolver to authoritative servers. Covers all record types relevant to telecom — especially SRV records (used by SIP to discover servers and ports) and NAPTR records (used for ENUM and SIP URI resolution). TTL management is critical — too short hammers DNS servers, too long delays failover.

#### Lesson 20: DNS-Based Load Balancing and GeoDNS
- **Module:** 1 — Foundations
- **Section:** 1.5 — DNS
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 19
- **Key Concepts:**
  1. Round-robin DNS — simple load distribution via multiple A records
  2. Weighted DNS responses — directing traffic proportionally
  3. GeoDNS — answering differently based on client location
  4. Health-check-aware DNS — removing unhealthy endpoints
  5. DNS failover — TTL tradeoffs for fast vs. slow failover
- **Description:** Explains how DNS is used as a load balancing and traffic management tool. Covers Telnyx's use of GeoDNS to route customers to the nearest point of presence, weighted records for gradual traffic shifting, and health-aware DNS for automatic failover. Discusses the TTL problem — low TTLs enable fast failover but increase query volume.

#### Lesson 21: DNS Troubleshooting — dig, nslookup, and Common Failures
- **Module:** 1 — Foundations
- **Section:** 1.5 — DNS
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 19, 20
- **Key Concepts:**
  1. Using `dig` to trace resolution: `dig +trace`, `dig @server`
  2. Common DNS failures: NXDOMAIN, SERVFAIL, timeout
  3. DNS caching problems — stale records after changes
  4. DNSSEC validation failures
  5. Checking SIP-specific DNS: `dig NAPTR`, `dig SRV`
- **Description:** Hands-on troubleshooting guide. Shows how to use `dig` to diagnose DNS issues step by step. Covers the most common DNS-related incidents in a telecom environment: stale cached records preventing failover, NAPTR/SRV misconfigurations causing SIP registration failures, and DNS-level DDoS impacts.

---

### Section 1.6 — BGP: How the Internet Routes

#### Lesson 22: Autonomous Systems and Internet Routing Fundamentals
- **Module:** 1 — Foundations
- **Section:** 1.6 — BGP
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 13
- **Key Concepts:**
  1. Autonomous Systems (AS) — what they are and why they exist
  2. Interior vs. exterior routing (IGP vs. EGP)
  3. AS Numbers (ASN) — Telnyx's ASN and what it means
  4. IP prefix announcement — how networks advertise reachability
  5. The routing table — how routers decide where to send packets
- **Description:** Introduces the concept of the internet as a network of networks (autonomous systems). Explains why BGP is necessary — interior routing protocols (OSPF, IS-IS) handle routing within a network, but BGP handles routing between networks. Covers Telnyx's AS and how it connects to the broader internet.

#### Lesson 23: BGP Mechanics — Sessions, Updates, and Path Selection
- **Module:** 1 — Foundations
- **Section:** 1.6 — BGP
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lesson 22
- **Key Concepts:**
  1. BGP session establishment: TCP port 179, OPEN, KEEPALIVE
  2. UPDATE messages: NLRI, path attributes, withdrawn routes
  3. AS-PATH — the sequence of ASes a route traverses
  4. BGP path selection algorithm — how the best path is chosen
  5. BGP communities — tagging routes for policy control
- **Description:** Deep dive into BGP protocol mechanics. Explains how BGP peers establish sessions over TCP, exchange routing information, and select the best path. The path selection algorithm (shortest AS-PATH, lowest MED, etc.) determines how traffic flows across the internet. Understanding this is critical for diagnosing routing-related latency or reachability issues.

#### Lesson 24: Peering, Transit, and Internet Exchange Points (IXPs)
- **Module:** 1 — Foundations
- **Section:** 1.6 — BGP
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 23
- **Key Concepts:**
  1. Transit — paying another network to carry your traffic to the internet
  2. Peering — free traffic exchange between networks of similar size
  3. Internet Exchange Points (IXPs) — physical locations where networks peer
  4. Settlement-free peering vs. paid peering
  5. How peering affects latency and call quality for Telnyx customers
- **Description:** Explains the business and technical relationships between networks. Covers how Telnyx's peering strategy (which IXPs, which transit providers) directly affects latency and reliability for voice traffic. Understanding peering helps explain why some routes have better quality than others.

#### Lesson 25: BGP Incidents — Hijacks, Leaks, and Troubleshooting
- **Module:** 1 — Foundations
- **Section:** 1.6 — BGP
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 23, 24
- **Key Concepts:**
  1. BGP hijacking — when someone announces your prefixes
  2. Route leaks — accidental propagation of routes
  3. RPKI and ROA — cryptographic route origin validation
  4. Tools: `bgp.he.net`, RIPE RIS, BGPStream, Looking Glass servers
  5. How BGP issues manifest as NOC incidents (packet loss, latency spikes, unreachability)
- **Description:** Covers BGP security and incident response. Explains real-world BGP hijack and leak scenarios, how they affect Telnyx services, and how to detect and respond. Covers RPKI as a mitigation mechanism and practical tools for investigating BGP anomalies during incidents.

---

### Section 1.7 — NAT and Its Impact on Real-Time Communications

#### Lesson 26: NAT Fundamentals — How and Why Network Address Translation Works
- **Module:** 1 — Foundations
- **Section:** 1.7 — NAT
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 13, 15
- **Key Concepts:**
  1. NAT types: Full Cone, Restricted Cone, Port Restricted, Symmetric
  2. How NAT rewrites IP headers and maintains translation tables
  3. NAT timeout — when mappings expire and connections break
  4. PAT (Port Address Translation) — many devices sharing one IP
  5. Why NAT was necessary (IPv4 exhaustion) and why it's a problem for VoIP
- **Description:** Explains NAT from the ground up — the translation table, how outbound packets create mappings, and how inbound packets are matched. The four NAT types have drastically different behaviors for UDP traffic, which directly affects SIP and RTP. Symmetric NAT is the worst case for VoIP and requires TURN relay.

#### Lesson 27: NAT Traversal for SIP and RTP — The Core Problem
- **Module:** 1 — Foundations
- **Section:** 1.7 — NAT
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 26
- **Key Concepts:**
  1. The SIP NAT problem: Contact headers contain private IPs
  2. The RTP NAT problem: SDP contains private IPs for media
  3. STUN — discovering your public IP/port
  4. TURN — relaying media when direct connection fails
  5. Far-end NAT traversal — how Telnyx handles NAT for customers
- **Description:** The single most common source of one-way audio and call setup failures. Explains how SIP puts the endpoint's IP in Contact and Via headers, and SDP puts it in the media connection address — both broken by NAT. Covers solutions: STUN for discovery, TURN for relay, and server-side techniques (SIP ALG, media proxy, rport). Critical for NOC troubleshooting.

#### Lesson 28: SIP ALG, Session Border Controllers, and Media Anchoring
- **Module:** 1 — Foundations
- **Section:** 1.7 — NAT
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 27
- **Key Concepts:**
  1. SIP ALG — application layer gateways in routers/firewalls (and why they cause problems)
  2. Session Border Controllers (SBCs) — NAT fix, security boundary, and interop layer
  3. Media anchoring — forcing RTP through a known relay
  4. RTP latching — learning the real source of media packets
  5. Debugging one-way audio: systematic NAT troubleshooting
- **Description:** Covers the practical solutions to NAT problems. SIP ALG (found in consumer routers) attempts to rewrite SIP headers but often mangles them. SBCs provide a proper solution by acting as a B2BUA and media relay. Explains Telnyx's approach to media handling and how to systematically debug one-way audio issues.

---

### Section 1.8 — RTP and RTCP: Voice/Video over IP

#### Lesson 29: RTP — Real-time Transport Protocol Deep Dive
- **Module:** 1 — Foundations
- **Section:** 1.8 — RTP/RTCP
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 15, Lesson 6
- **Key Concepts:**
  1. RTP header: version, payload type, sequence number, timestamp, SSRC
  2. Payload types — mapping numbers to codecs (dynamic vs. static)
  3. Sequence numbers — detecting packet loss and reordering
  4. Timestamps — reconstructing timing for playout
  5. SSRC and CSRC — identifying sources in mixed/multiplexed streams
- **Description:** Line-by-line examination of the RTP header and what each field does. Sequence numbers let the receiver detect gaps (loss) and reordering. Timestamps let the jitter buffer reconstruct the original timing. Payload type tells the decoder which codec to use. Understanding RTP headers is essential for reading PCAPs and diagnosing media quality issues.

#### Lesson 30: RTCP — Feedback, Quality Reporting, and Congestion Control
- **Module:** 1 — Foundations
- **Section:** 1.8 — RTP/RTCP
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 29
- **Key Concepts:**
  1. RTCP packet types: SR (Sender Report), RR (Receiver Report), SDES, BYE
  2. Receiver Reports: loss fraction, cumulative loss, jitter, last SR timestamp
  3. RTCP interval — why reports are sent every few seconds
  4. RTCP-XR — extended reports with per-interval metrics
  5. Using RTCP data in Grafana to monitor call quality in real-time
- **Description:** RTCP provides the feedback loop for RTP. Receiver Reports contain the metrics that drive quality monitoring: packet loss percentage, interarrival jitter, and round-trip time. Explains how to interpret these values and how they feed into Telnyx's quality monitoring dashboards.

#### Lesson 31: DTMF — RFC 2833/4733 Telephone Events vs. In-Band Detection
- **Module:** 1 — Foundations
- **Section:** 1.8 — RTP/RTCP
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 29
- **Key Concepts:**
  1. DTMF tone frequencies — the 4x4 matrix
  2. In-band DTMF — tones in the audio stream (fragile with compression)
  3. RFC 2833/4733 — DTMF as named telephone events in RTP
  4. SIP INFO method for DTMF — out-of-band signaling approach
  5. Debugging DTMF issues: missed digits, double digits, method mismatch
- **Description:** DTMF (touch tones) is critical for IVR navigation and authentication. Covers three methods of transporting DTMF and why RFC 2833 is preferred. In-band DTMF breaks with compressed codecs; SIP INFO adds latency. Common issues include negotiation mismatches where one side sends RFC 2833 but the other expects in-band.

---

### Section 1.9 — Jitter, Latency, and Call Quality

#### Lesson 32: Latency Budget — Sources of Delay in a VoIP Call
- **Module:** 1 — Foundations
- **Section:** 1.9 — Quality
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 29, Lesson 7
- **Key Concepts:**
  1. End-to-end delay components: codec, packetization, serialization, propagation, queuing, jitter buffer
  2. One-way delay thresholds: <150ms good, 150-400ms acceptable, >400ms poor
  3. Propagation delay — speed of light and geographic distance
  4. Codec/algorithmic delay — why G.729 adds more delay than G.711
  5. The cumulative effect — how small delays compound
- **Description:** Breaks down every source of delay in a VoIP call and assigns typical values. Shows how to calculate total one-way delay for a given path. Critical for understanding why transcontinental calls have unavoidable minimum latency and why adding unnecessary media processing (transcoding, recording) increases delay.

#### Lesson 33: Jitter — Why Packets Arrive at Irregular Intervals
- **Module:** 1 — Foundations
- **Section:** 1.9 — Quality
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 32
- **Key Concepts:**
  1. Jitter definition: variation in interarrival time
  2. Causes: queuing variation, route changes, CPU contention
  3. Measuring jitter: RTCP interarrival jitter calculation
  4. Impact on voice quality: buffer underruns and overruns
  5. Network jitter vs. system jitter — different root causes
- **Description:** Deep dive into jitter — the variation in packet arrival times that makes voice sound choppy. Explains the mathematical definition (RFC 3550), common causes (network congestion, route flapping, CPU scheduling), and how to distinguish between network-caused and system-caused jitter using RTCP reports and packet captures.

#### Lesson 34: The Jitter Buffer — Smoothing Out Packet Arrival Variation
- **Module:** 1 — Foundations
- **Section:** 1.9 — Quality
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 33
- **Key Concepts:**
  1. Fixed vs. adaptive jitter buffers
  2. Buffer depth tradeoff: too shallow = drops, too deep = latency
  3. Packet Loss Concealment (PLC) — interpolating missing packets
  4. Late packets — treated as lost if they arrive after playout time
  5. Monitoring jitter buffer performance: discard rate metrics
- **Description:** Explains how jitter buffers work — holding packets briefly to smooth out arrival variation before playing them out at regular intervals. Covers the fundamental tradeoff: deeper buffers tolerate more jitter but add latency. Adaptive buffers dynamically adjust depth based on measured jitter. PLC techniques mask occasional losses by interpolating from surrounding packets.

#### Lesson 35: Packet Loss — Causes, Effects, and Measurement
- **Module:** 1 — Foundations
- **Section:** 1.9 — Quality
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 33, 34
- **Key Concepts:**
  1. Random vs. burst loss — very different impacts on quality
  2. Loss concealment effectiveness varies with loss pattern
  3. Acceptable loss thresholds: <1% good, 1-3% noticeable, >5% unusable
  4. Causes: congestion, buffer overflow, firewall drops, MTU issues
  5. Detecting loss: RTCP RR, RTP sequence gaps in PCAPs
- **Description:** Comprehensive coverage of packet loss in VoIP contexts. Explains why bursty loss is worse than random loss (PLC can't interpolate multiple consecutive missing packets). Covers how to measure loss using RTCP Receiver Reports and by analyzing RTP sequence numbers in Wireshark. Maps loss percentages to MOS impact.

#### Lesson 36: Packet Reordering, Duplication, and Their Impact
- **Module:** 1 — Foundations
- **Section:** 1.9 — Quality
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 35
- **Key Concepts:**
  1. Causes of reordering: multipath routing, load balancer hashing
  2. Severely reordered packets appear as loss then late arrival
  3. Packet duplication — rare but happens with certain network configs
  4. Impact on jitter buffer behavior
  5. Detecting reordering in packet captures
- **Description:** Covers less common but important packet impairments. Reordered packets can arrive too late for the jitter buffer, effectively becoming losses. Explains when reordering happens (ECMP routing, link aggregation with poor hash distribution) and how to detect it in PCAPs.

---

### Section 1.10 — SIP Protocol Deep Dive

#### Lesson 37: SIP Architecture — Endpoints, Proxies, Registrars, and B2BUAs
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 16, 19
- **Key Concepts:**
  1. SIP as an HTTP-inspired text-based signaling protocol
  2. User Agents: UAC (client) and UAS (server) — roles per transaction
  3. Proxy servers — routing SIP requests, stateful vs. stateless
  4. Registrar — mapping SIP URIs to contact addresses
  5. B2BUA — Back-to-Back User Agent and why Telnyx uses this model
- **Description:** Introduces SIP's architecture and entity roles. Unlike the PSTN's centralized model, SIP is distributed and uses DNS for routing. Explains why Telnyx operates as a B2BUA rather than a proxy — controlling both call legs independently allows for media manipulation, topology hiding, and billing control. This architectural choice has major implications for how calls are handled.

#### Lesson 38: SIP Methods — INVITE, REGISTER, BYE, and Beyond
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 37
- **Key Concepts:**
  1. Core methods: INVITE, ACK, BYE, CANCEL, REGISTER, OPTIONS
  2. Extension methods: REFER, SUBSCRIBE, NOTIFY, INFO, UPDATE, MESSAGE
  3. When each method is used and what it signals
  4. Request structure: Request-Line, headers, body (SDP)
  5. Response structure: Status-Line (response codes), headers, body
- **Description:** Catalogs every SIP method and explains when and why each is used. INVITE initiates sessions, REGISTER maintains location bindings, BYE terminates, CANCEL aborts pending requests. Extension methods enable advanced features: REFER for call transfer, SUBSCRIBE/NOTIFY for presence and event packages, INFO for mid-call signaling.

#### Lesson 39: SIP Headers — The Essential Ones and What They Tell You
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lesson 38
- **Key Concepts:**
  1. Via — records the path of the request (critical for response routing)
  2. From, To, Contact — addressing headers and their different purposes
  3. Call-ID, CSeq — dialog and transaction identification
  4. Record-Route and Route — ensuring mid-dialog requests follow the right path
  5. Custom headers: X-headers, P-Asserted-Identity, Privacy
- **Description:** Header-by-header guide to reading SIP messages. Via headers track request path and enable response routing (each proxy adds a Via). From/To identify the dialog, Contact provides the direct address. Record-Route forces future requests through proxies. P-Asserted-Identity carries trusted caller ID. Being able to read these headers fluently is the #1 skill for SIP debugging.

#### Lesson 40: SIP Response Codes — What Every Code Means
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 38
- **Key Concepts:**
  1. 1xx Provisional: 100 Trying, 180 Ringing, 183 Session Progress
  2. 2xx Success: 200 OK, 202 Accepted
  3. 3xx Redirection: 301, 302 — follow the Contact header
  4. 4xx Client Error: 401, 403, 404, 408, 480, 486, 487, 488
  5. 5xx/6xx Server/Global: 500, 502, 503, 504, 600, 603
- **Description:** Comprehensive reference for SIP response codes with real-world explanations. For each code: what triggers it, what the caller/NOC should do, and common misconfigurations that produce it. Special attention to the codes most seen in Telnyx NOC operations: 408 (timeout), 480 (unavailable), 486 (busy), 487 (cancelled), 488 (not acceptable), 503 (service unavailable).

#### Lesson 41: SIP Dialogs and Transactions — Understanding State
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 39, 40
- **Key Concepts:**
  1. Transaction: a single request-response exchange (identified by Via branch + CSeq)
  2. Dialog: a long-lived relationship between two UAs (identified by Call-ID + From-tag + To-tag)
  3. Dialog state: early (1xx with To-tag), confirmed (2xx), terminated (BYE)
  4. Forking — one INVITE creating multiple transactions
  5. Why dialog understanding prevents ghost calls and hung sessions
- **Description:** Explains the two fundamental SIP state concepts. Transactions are short-lived (one request, one response). Dialogs persist for the call duration and maintain state (route set, target). Mismanaging dialog state leads to ghost calls (calls that exist in billing but have no actual media) and hung sessions.

#### Lesson 42: SIP Registration — How Endpoints Make Themselves Reachable
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 41
- **Key Concepts:**
  1. REGISTER request — binding an AOR (Address of Record) to a Contact
  2. Registration expiry and re-registration intervals
  3. Authentication: 401 challenge → credentials → authenticated REGISTER
  4. Multiple registrations — one AOR, multiple devices
  5. Registration failures: common causes and troubleshooting
- **Description:** Explains how SIP registration works — a client tells the registrar "I'm reachable at this IP:port." Covers the authentication dance (digest auth), registration refresh timers, and what happens when registration expires. Common failures: wrong credentials, NAT timeouts between re-registrations, DNS failures finding the registrar.

#### Lesson 43: SIP Authentication — Digest Auth, TLS, and IP-Based Auth
- **Module:** 1 — Foundations
- **Section:** 1.10 — SIP
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 42, 17
- **Key Concepts:**
  1. Digest authentication: nonce, realm, response hash (MD5/SHA-256)
  2. 401 Unauthorized vs. 407 Proxy Authentication Required
  3. IP-based authentication — ACL-based trust (simpler but less secure)
  4. TLS client certificates — mutual TLS for SIP trunk auth
  5. Token-based authentication — modern approaches
- **Description:** Deep dive into SIP authentication mechanisms. Digest auth is the most common — the server challenges with a nonce, the client hashes its credentials with the nonce and sends back the response. Covers why MD5 is weak and why TLS + strong passwords or mTLS is preferred. Explains Telnyx's authentication options for SIP trunks.

---

### Section 1.11 — SIP Call Flows

#### Lesson 44: Basic Call Setup — INVITE to 200 OK to BYE
- **Module:** 1 — Foundations
- **Section:** 1.11 — SIP Call Flows
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 41
- **Key Concepts:**
  1. The complete call flow: INVITE → 100 → 180 → 200 → ACK → media → BYE → 200
  2. The three-way handshake: INVITE, 200 OK, ACK
  3. Why ACK exists — confirming receipt of the final response
  4. Early media — 183 Session Progress with SDP
  5. Timer-based failure: what happens when responses don't arrive
- **Description:** Step-by-step walkthrough of a complete SIP call from setup to teardown. Traces every message, explains what triggers it, and what state changes occur. Covers the critical INVITE transaction — the three-way handshake that establishes the dialog and why ACK is necessary (it's the only non-INVITE request that's part of the INVITE transaction).

#### Lesson 45: Call Failures — CANCEL, Timeouts, and Error Responses
- **Module:** 1 — Foundations
- **Section:** 1.11 — SIP Call Flows
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 44
- **Key Concepts:**
  1. CANCEL — aborting a pending INVITE (must arrive before final response)
  2. 487 Request Terminated — the response after a successful CANCEL
  3. Timer B (INVITE transaction timeout) — 32 seconds default
  4. Timer F (non-INVITE transaction timeout)
  5. Race conditions: CANCEL crossing with 200 OK
- **Description:** Covers how calls fail. CANCEL races with final responses. Timeouts occur when no response arrives. Error responses (4xx, 5xx, 6xx) terminate the transaction. Explains the race condition when CANCEL crosses with 200 OK — the caller must send ACK then BYE. These scenarios cause many real-world bugs.

#### Lesson 46: Call Transfer — REFER and Replaces
- **Module:** 1 — Foundations
- **Section:** 1.11 — SIP Call Flows
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 44
- **Key Concepts:**
  1. Blind transfer (unattended): REFER with Refer-To header
  2. Attended transfer: REFER with Replaces header
  3. NOTIFY — transfer progress reporting
  4. B2BUA transfer handling — Telnyx as intermediary
  5. Common transfer failures and debugging
- **Description:** Explains SIP call transfer mechanics. Blind transfer: "call this other number." Attended transfer: "take over this existing call." Covers how REFER triggers a new INVITE and how NOTIFY reports progress. In a B2BUA architecture, transfers are more complex because the B2BUA must bridge the new call leg.

#### Lesson 47: Call Hold, Resume, and Re-INVITE
- **Module:** 1 — Foundations
- **Section:** 1.11 — SIP Call Flows
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 44
- **Key Concepts:**
  1. Re-INVITE — modifying an existing session
  2. Hold: re-INVITE with `a=sendonly` or `a=inactive` in SDP
  3. Resume: re-INVITE restoring `a=sendrecv`
  4. UPDATE method — modifying session before it's established
  5. Glare: simultaneous re-INVITEs and how to handle them
- **Description:** Covers mid-call session modification. Hold, resume, codec change, and adding/removing media streams all use re-INVITE. Explains the SDP attributes that signal hold state and the glare condition (both sides sending re-INVITE simultaneously — resolved by the 491 response).

---

### Section 1.12 — SDP and Media Negotiation

#### Lesson 48: SDP Structure — Offer/Answer Model
- **Module:** 1 — Foundations
- **Section:** 1.12 — SDP
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 44
- **Key Concepts:**
  1. SDP structure: v=, o=, s=, c=, t=, m=, a= lines
  2. Offer/Answer model (RFC 3264) — how codec negotiation works
  3. Media line (m=): media type, port, transport, payload types
  4. Connection line (c=): where to send media (the NAT problem lives here)
  5. Attribute lines (a=): rtpmap, fmtp, direction, candidates
- **Description:** Line-by-line SDP parsing guide. The offerer proposes codecs and media parameters; the answerer selects from the offer. Explains every SDP line type with examples. The connection address (c=) and media port (m=) are where NAT problems manifest. The rtpmap attributes define the codec mapping.

#### Lesson 49: Codec Negotiation and Media Interworking
- **Module:** 1 — Foundations
- **Section:** 1.12 — SDP
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 48
- **Key Concepts:**
  1. Codec preference ordering in SDP offers
  2. Answerer selection — choosing from offered codecs
  3. What happens when no common codec exists (488 Not Acceptable Here)
  4. Transcoding decision points in B2BUA architecture
  5. Telephone-event negotiation for DTMF
- **Description:** Explains the codec negotiation process in detail. The offer lists codecs in preference order; the answer selects one (or more for different media lines). When the B2BUA's two legs negotiate different codecs, transcoding is required. Covers how to read SDP to understand what was negotiated and diagnose "no audio" issues caused by negotiation failures.

---

### Section 1.13 — Packet Loss, Jitter, and Troubleshooting

#### Lesson 50: Systematic Call Quality Troubleshooting
- **Module:** 1 — Foundations
- **Section:** 1.13 — Troubleshooting
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 32-36, 48
- **Key Concepts:**
  1. The troubleshooting framework: isolate the leg, identify the symptom, find the cause
  2. Common symptoms: one-way audio, no audio, choppy audio, echo, DTMF failure
  3. Tool chain: SIP traces, RTCP stats, PCAPs, Grafana dashboards
  4. Correlating SIP signaling issues with media issues
  5. Customer-side vs. network-side vs. far-end issues
- **Description:** Provides a systematic framework for debugging call quality issues. Maps symptoms to likely causes: one-way audio → NAT/firewall, choppy audio → jitter/loss, echo → impedance mismatch or acoustic feedback, no audio → SDP negotiation failure or blocked ports. Shows how to use Telnyx's tools to isolate problems.

#### Lesson 51: Network Diagnostics — Traceroute, MTR, and Path Analysis
- **Module:** 1 — Foundations
- **Section:** 1.13 — Troubleshooting
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 13, 50
- **Key Concepts:**
  1. Traceroute: how TTL-based path discovery works
  2. MTR: continuous traceroute with statistics (loss%, latency per hop)
  3. Interpreting MTR output: ICMP rate limiting vs. real loss
  4. Forward vs. reverse path — asymmetric routing complications
  5. When network diagnostics are useful vs. misleading
- **Description:** Hands-on guide to network path diagnostics. Explains how traceroute works (incrementing TTL to elicit ICMP Time Exceeded from each hop), why MTR is better for diagnosing intermittent issues, and common misinterpretations (ICMP rate limiting looks like loss but isn't). Covers when to escalate network issues to transit providers.

---

### Section 1.14 — TLS and SRTP: Securing Communications

#### Lesson 52: SRTP — Encrypting RTP Media Streams
- **Module:** 1 — Foundations
- **Section:** 1.14 — Security
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 17, 29
- **Key Concepts:**
  1. SRTP: AES encryption of RTP payload (header remains cleartext)
  2. Key exchange: SDES (keys in SDP) vs. DTLS-SRTP (keys via DTLS handshake)
  3. Why SDES is insecure without TLS (keys visible in SDP)
  4. DTLS-SRTP — the WebRTC-mandated approach
  5. Debugging encrypted media: what you can and can't see in PCAPs
- **Description:** Explains how voice encryption works. SRTP encrypts the audio payload while leaving RTP headers readable (so network tools can still measure jitter and loss). Covers the two key exchange methods: SDES (simple but requires TLS for security) and DTLS-SRTP (secure by design, used in WebRTC). Important for understanding what's visible vs. encrypted in packet captures.

#### Lesson 53: End-to-End Encryption vs. Opp-to-Hop Encryption
- **Module:** 1 — Foundations
- **Section:** 1.14 — Security
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 52
- **Key Concepts:**
  1. Hop-by-hop: TLS + SRTP terminates at each B2BUA/proxy
  2. End-to-end: media encrypted from caller to callee (B2BUA can't access)
  3. Why B2BUAs need to access media (recording, transcoding, DTMF)
  4. Regulatory requirements: lawful intercept implications
  5. The practical reality of voice encryption in telecom
- **Description:** Discusses the encryption model in real-world deployments. In Telnyx's B2BUA architecture, SRTP terminates at the B2BUA — media is decrypted, processed, and re-encrypted. True end-to-end encryption would prevent features like call recording and transcoding. Covers the security vs. functionality tradeoff.

---

### Section 1.15 — WebRTC

#### Lesson 54: WebRTC Architecture — Browser-Based Real-Time Communication
- **Module:** 1 — Foundations
- **Section:** 1.15 — WebRTC
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 52, 27
- **Key Concepts:**
  1. WebRTC APIs: getUserMedia, RTCPeerConnection, RTCDataChannel
  2. Mandatory security: DTLS-SRTP, no unencrypted media
  3. Mandatory codecs: Opus for audio, VP8/H.264 for video
  4. Signaling is not specified — use whatever you want (WebSocket, HTTP)
  5. The WebRTC triangle: browser ↔ signaling server ↔ browser
- **Description:** Introduces WebRTC as a browser-native real-time communication framework. Unlike SIP, WebRTC doesn't specify signaling — it focuses on the media path and NAT traversal. Covers the API surface and why WebRTC mandates encryption (learned from SIP's history of optional security).

#### Lesson 55: ICE — Interactive Connectivity Establishment
- **Module:** 1 — Foundations
- **Section:** 1.15 — WebRTC
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 54, 26
- **Key Concepts:**
  1. ICE candidates: host, server reflexive (STUN), relay (TURN)
  2. Candidate gathering — discovering all possible connection paths
  3. Connectivity checks — STUN binding requests to test each candidate pair
  4. ICE nomination — selecting the best working path
  5. Trickle ICE — sending candidates as they're discovered (faster setup)
- **Description:** Deep dive into ICE — WebRTC's solution to NAT traversal. ICE systematically discovers and tests all possible connection paths, then selects the best one. Covers the three candidate types, the connectivity check process, and why ICE is more robust than SIP's ad-hoc NAT traversal approaches.

#### Lesson 56: STUN and TURN — NAT Discovery and Relay
- **Module:** 1 — Foundations
- **Section:** 1.15 — WebRTC
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 55
- **Key Concepts:**
  1. STUN: lightweight protocol to discover public IP:port mapping
  2. TURN: relay server for when direct connection is impossible
  3. TURN allocation — reserving relay resources on the TURN server
  4. When TURN is needed: symmetric NAT, restrictive firewalls
  5. Bandwidth and cost implications of TURN relay
- **Description:** Explains STUN and TURN in detail. STUN is lightweight — a single request/response to learn your public address. TURN is heavyweight — all media flows through the TURN server, doubling bandwidth and adding latency. Covers when each is needed and the operational implications of running TURN infrastructure.

---

## Module 2 — Telnyx Products Deep Dive

*This module covers every Telnyx product from a technical perspective — how it works under the hood, not just what it does. Each lesson connects the product to the infrastructure and protocols covered in Module 1.*

---

### Section 2.1 — SIP Trunking

#### Lesson 57: SIP Trunking Fundamentals — How Telnyx Connects to the PSTN
- **Module:** 2 — Products
- **Section:** 2.1 — SIP Trunking
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 37-44
- **Key Concepts:**
  1. SIP trunk: a logical connection between customer PBX and Telnyx
  2. Telnyx as B2BUA: two independent call legs
  3. PSTN interconnection: SIP-to-TDM gateways and IP interconnects
  4. Origination (inbound) vs. termination (outbound) trunking
  5. Credential vs. IP-based authentication for trunks
- **Description:** Explains how SIP trunking works at Telnyx. The B2BUA architecture means Telnyx maintains two separate SIP dialogs — one with the customer and one with the PSTN carrier. Covers PSTN interconnection methods, the distinction between origination and termination, and how authentication works. Foundation for understanding most voice-related NOC issues.

#### Lesson 58: Call Routing — How Telnyx Decides Where to Send a Call
- **Module:** 2 — Products
- **Section:** 2.1 — SIP Trunking
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 57
- **Key Concepts:**
  1. Least Cost Routing (LCR) — selecting the cheapest route
  2. Quality-based routing — factoring in ASR and ACD metrics
  3. Geographic routing — closest POP, carrier preferences by region
  4. Failover routing — trying alternate carriers on failure
  5. Customer-configurable routing: connection objects, outbound profiles
- **Description:** Covers the routing engine that decides which carrier to use for each outbound call. Explains LCR, quality-based routing (Answer Seizure Ratio, Average Call Duration), geographic considerations, and failover logic. Connects to NOC operations — routing issues cause call failures that are often misdiagnosed as network problems.

#### Lesson 59: SIP Trunk Configuration and Troubleshooting
- **Module:** 2 — Products
- **Section:** 2.1 — SIP Trunking
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 57, 58
- **Key Concepts:**
  1. Connection settings: codecs, DTMF mode, T.38 support
  2. Outbound voice profiles: caller ID rules, number formatting
  3. Common configuration errors and their symptoms
  4. Reading SIP trunk CDRs for debugging
  5. Grafana dashboards for trunk health monitoring
- **Description:** Practical guide to SIP trunk configuration and debugging. Maps common misconfiguration errors to their symptoms: wrong codec list → 488, bad authentication → 401/403, missing outbound profile → 403. Shows how to use Telnyx-specific tools and Grafana dashboards to monitor trunk health.

---

### Section 2.2 — Voice API / Call Control

#### Lesson 60: Call Control Architecture — Webhooks and State Machines
- **Module:** 2 — Products
- **Section:** 2.2 — Voice API
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 57, 18
- **Key Concepts:**
  1. Call Control as a REST API with webhook-driven events
  2. Call states: initiated, ringing, answered, bridged, hangup
  3. Commands: answer, hangup, transfer, bridge, gather, speak, play
  4. Webhook delivery: HTTP POST with call state events
  5. Async nature: command → webhook → command → webhook loop
- **Description:** Explains how Telnyx's programmable voice API works. Incoming calls trigger webhooks to the customer's application, which responds with commands. Covers the event-driven architecture, call state transitions, and why webhook reliability is critical. Common issues: webhook timeout, application errors, command sequencing problems.

#### Lesson 61: Call Control Commands Deep Dive
- **Module:** 2 — Products
- **Section:** 2.2 — Voice API
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 60
- **Key Concepts:**
  1. Media commands: play_audio, speak (TTS), gather (DTMF/speech input)
  2. Call manipulation: bridge, transfer, conference
  3. Recording: start/stop recording, dual-channel recording
  4. Advanced: streaming (real-time audio via WebSocket), forking
  5. Error handling: command failures, race conditions
- **Description:** Deep dive into each Call Control command, explaining what happens at the SIP/RTP level when each is invoked. Bridge creates a media path between two calls. Gather sets up DTMF/speech detection. Streaming opens a WebSocket for real-time audio access. Covers common failure modes and debugging approaches.

#### Lesson 62: Webhook Reliability and Debugging
- **Module:** 2 — Products
- **Section:** 2.2 — Voice API
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 60
- **Key Concepts:**
  1. Webhook delivery: timeout thresholds, retry logic
  2. Failover webhooks: primary and backup URLs
  3. Common webhook failures: DNS, TLS, timeout, 5xx responses
  4. Debugging with Graylog: finding webhook delivery logs
  5. Customer application issues vs. Telnyx platform issues
- **Description:** Covers webhook delivery mechanics and failure modes. When a webhook fails, calls may hang or follow default behavior. Explains how to distinguish between Telnyx-side delivery issues and customer application issues using Graylog logs. Covers retry logic, timeout settings, and failover URL configuration.

---

### Section 2.3 — TeXML

#### Lesson 63: TeXML — TwiML-Compatible Voice Scripting
- **Module:** 2 — Products
- **Section:** 2.3 — TeXML
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 60
- **Key Concepts:**
  1. TeXML as XML-based call flow scripting (TwiML compatible)
  2. How TeXML maps to Call Control commands internally
  3. Key verbs: Say, Play, Gather, Dial, Record, Conference
  4. TeXML application URL: Telnyx fetches XML on call events
  5. Migration from Twilio: compatibility and differences
- **Description:** Explains TeXML as an alternative to the Call Control API — XML documents describe call behavior instead of webhook-driven command sequences. Covers how TeXML verbs translate to internal Call Control operations, compatibility with Twilio's TwiML, and common debugging scenarios.

---

### Section 2.4 — WebRTC at Telnyx

#### Lesson 64: Telnyx WebRTC Architecture — Voice SDK and Proxy
- **Module:** 2 — Products
- **Section:** 2.4 — WebRTC
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 54-56, 57
- **Key Concepts:**
  1. Telnyx voice-sdk-proxy: bridging WebRTC and SIP
  2. Signaling: WebSocket from browser to voice-sdk-proxy
  3. Media: DTLS-SRTP from browser, SRTP/RTP to SIP side
  4. Authentication: JWT tokens for WebRTC clients
  5. ICE candidate relay through Telnyx TURN servers
- **Description:** Explains how Telnyx's WebRTC product works end-to-end. The voice-sdk-proxy translates between WebRTC signaling (WebSocket) and SIP, and between DTLS-SRTP and RTP for media. Covers the authentication flow, ICE negotiation through Telnyx infrastructure, and common WebRTC-specific issues.

#### Lesson 65: WebRTC Troubleshooting — ICE Failures, Media Issues, Browser Quirks
- **Module:** 2 — Products
- **Section:** 2.4 — WebRTC
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 64
- **Key Concepts:**
  1. ICE failure: no viable candidate pair found
  2. Browser permissions: microphone access denied
  3. OCER (Oops, Can't Establish RTP): common in corporate firewalls
  4. Chrome WebRTC internals: chrome://webrtc-internals for debugging
  5. Network quality indicators in WebRTC stats API
- **Description:** Practical troubleshooting guide for WebRTC issues. Corporate firewalls often block UDP, preventing direct media. Browser permission changes break microphone access. Covers how to use chrome://webrtc-internals and getStats() API for client-side debugging, and server-side logs for proxy-side issues.

---

### Section 2.5 — Voice AI

#### Lesson 66: Voice AI Architecture — AI Assistants and the Processing Pipeline
- **Module:** 2 — Products
- **Section:** 2.5 — Voice AI
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 60
- **Key Concepts:**
  1. AI Assistant architecture: STT → LLM → TTS pipeline
  2. Audio Capture Agent (ACA): real-time audio stream capture
  3. LLM-manager: routing requests to language models
  4. STT pipeline: Whisper/Deepgram for speech-to-text
  5. TTS pipeline: text-to-speech with voice cloning options
- **Description:** Explains the end-to-end Voice AI pipeline. Audio from the call is streamed to STT, transcribed text goes to the LLM for processing, LLM response is synthesized back to speech via TTS, and played into the call. Covers each component, latency considerations (real-time constraint), and failure modes at each stage.

#### Lesson 67: Voice AI Troubleshooting — Latency, Quality, and Pipeline Failures
- **Module:** 2 — Products
- **Section:** 2.5 — Voice AI
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 66
- **Key Concepts:**
  1. End-to-end latency budget: STT + LLM inference + TTS
  2. STT accuracy issues: accents, background noise, codec quality
  3. LLM timeout and rate limiting
  4. TTS quality and voice consistency
  5. Monitoring AI pipeline health in Grafana
- **Description:** Covers debugging Voice AI issues. The pipeline has strict latency requirements for conversational AI (< 2 seconds response time). Each stage can fail independently: STT misrecognition, LLM timeout, TTS synthesis failure. Shows how to monitor pipeline latency and quality using Grafana dashboards.

---

### Section 2.6 — Messaging

#### Lesson 68: SMS/MMS Architecture — How Messages Flow
- **Module:** 2 — Products
- **Section:** 2.6 — Messaging
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 18
- **Key Concepts:**
  1. SMS delivery path: Telnyx → aggregator/carrier → SMSC → handset
  2. MMS: multimedia messaging via MM4/MM7 protocols
  3. Long code vs. short code vs. toll-free messaging
  4. Delivery receipts (DLR) and their reliability
  5. Message queuing, rate limiting, and throughput
- **Description:** Traces an SMS from API call to handset delivery. Explains the carrier ecosystem — Telnyx connects to carriers via aggregators or direct interconnects. Covers the difference between long codes, short codes, and toll-free numbers for messaging, and why delivery receipts are not always reliable.

#### Lesson 69: 10DLC — A2P Messaging Registration and Compliance
- **Module:** 2 — Products
- **Section:** 2.6 — Messaging
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 68
- **Key Concepts:**
  1. A2P (Application-to-Person) vs. P2P messaging
  2. 10DLC campaign registration: brand → campaign → number assignment
  3. Trust scores and throughput tiers
  4. TCR (The Campaign Registry) — the registration authority
  5. Common registration failures and messaging blocks
- **Description:** Explains the 10DLC regulatory framework. US carriers require businesses to register their brand and messaging campaigns. Trust scores determine throughput limits. Covers the registration process, common rejection reasons, and how to troubleshoot messaging blocks.

#### Lesson 70: Message Delivery Troubleshooting
- **Module:** 2 — Products
- **Section:** 2.6 — Messaging
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 68, 69
- **Key Concepts:**
  1. Error codes: carrier rejection, invalid number, spam filter
  2. Carrier filtering: content-based and volume-based blocking
  3. Number deactivation and recycling
  4. Debugging with message detail records (MDRs)
  5. Graylog queries for messaging pipeline investigation
- **Description:** Practical guide to debugging message delivery failures. Maps error codes to root causes, explains carrier filtering behavior, and shows how to use MDRs and Graylog to trace a message through the pipeline.

#### Lesson 71: RCS — Rich Communication Services
- **Module:** 2 — Products
- **Section:** 2.6 — Messaging
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 68
- **Key Concepts:**
  1. RCS as SMS successor: rich cards, carousels, suggested actions
  2. RCS Business Messaging (RBM) agent registration
  3. Carrier support and fallback to SMS
  4. Delivery receipts and read receipts in RCS
  5. RCS vs. OTT messaging apps (WhatsApp Business, etc.)
- **Description:** Covers Rich Communication Services — the carrier-backed evolution of SMS. Explains the richer message types (cards, carousels, buttons), the agent registration process, and the critical fallback-to-SMS mechanism when RCS isn't available.

---

### Section 2.7 — Numbers

#### Lesson 72: Number Provisioning — Ordering, Searching, and Assigning
- **Module:** 2 — Products
- **Section:** 2.7 — Numbers
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 4
- **Key Concepts:**
  1. Number inventory: how Telnyx sources numbers from carriers/regulators
  2. Number search API: filtering by area code, features, pattern
  3. Number ordering and activation lifecycle
  4. Number assignment to connections/messaging profiles
  5. Number release and quarantine period
- **Description:** Explains the lifecycle of a phone number at Telnyx — from inventory sourcing through ordering, assignment, and release. Covers the technical process behind number search, the regulatory requirements for different number types (local, toll-free, international), and what happens when numbers are released.

#### Lesson 73: Number Porting — The Complete Lifecycle
- **Module:** 2 — Products
- **Section:** 2.7 — Numbers
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 72, 4
- **Key Concepts:**
  1. Port-in process: LOA, CSR, FOC date
  2. Porting timeline: simple vs. complex ports
  3. LRN updates and routing cutover
  4. Common porting failures: CSR mismatch, incomplete LOA
  5. Port-out obligations and customer retention
- **Description:** Comprehensive guide to number porting. Covers the regulatory framework, the paperwork (Letter of Authorization, Customer Service Record), timeline expectations, and the technical cutover process. Common failures include CSR mismatches (name, address, account number), missing authorized signatures, and carrier delays.

#### Lesson 74: CNAM, E911, and Number Features
- **Module:** 2 — Products
- **Section:** 2.7 — Numbers
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 72
- **Key Concepts:**
  1. CNAM: Caller Name database — how caller ID names work
  2. E911: Enhanced 911 — location-based emergency routing
  3. E911 provisioning: MSAG validation, ALI database
  4. STIR/SHAKEN: call authentication and attestation levels
  5. Toll-free number management: RespOrg, SMS enablement
- **Description:** Covers additional number features. CNAM explains why some calls show names and others don't. E911 explains the legal requirements for VoIP providers to provide emergency calling. STIR/SHAKEN explains the caller ID authentication framework designed to combat robocalls.

---

### Section 2.8 — Number Lookup and Verify

#### Lesson 75: Number Lookup API — LRN, Carrier, and Caller ID
- **Module:** 2 — Products
- **Section:** 2.8 — Lookup/Verify
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 72
- **Key Concepts:**
  1. LRN lookup: determining the serving carrier for routing
  2. Carrier lookup: identifying the current operator
  3. Caller ID lookup: CNAM database query
  4. Number type identification: mobile, landline, VoIP
  5. Use cases: fraud prevention, routing optimization
- **Description:** Explains the Number Lookup product — real-time database queries to determine a number's carrier, type, and caller name. Covers how LRN lookups work (querying the NPAC database) and why this data is valuable for call routing and fraud prevention.

#### Lesson 76: Verify API — Phone Number Verification
- **Module:** 2 — Products
- **Section:** 2.8 — Lookup/Verify
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 68, 75
- **Key Concepts:**
  1. OTP (One-Time Password) verification via SMS or voice call
  2. Verification lifecycle: request → deliver → verify
  3. Rate limiting and fraud prevention
  4. Flash calling verification
  5. Silent network authentication (SNA)
- **Description:** Covers phone number verification mechanisms. The standard flow: generate OTP, deliver via SMS or voice, verify user-submitted code. Covers newer methods like flash calling (missed call from a specific number) and silent network authentication (carrier-level verification without user interaction).

---

### Section 2.9 — Fax

#### Lesson 77: Fax over IP — T.38 and G.711 Passthrough
- **Module:** 2 — Products
- **Section:** 2.9 — Fax
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 6, 44
- **Key Concepts:**
  1. T.30: the original fax protocol (modem tones over PSTN)
  2. Why fax fails over standard VoIP (jitter, compression, VAD)
  3. T.38: fax relay protocol — extracting fax data from audio
  4. G.711 passthrough: keeping fax as uncompressed audio
  5. T.38 re-INVITE negotiation and fallback behavior
- **Description:** Explains why fax is uniquely challenging for VoIP. Fax modems are extremely sensitive to audio quality — even minor jitter or compression destroys the signal. T.38 solves this by demodulating the fax, transmitting data as IP packets, and remodulating at the other end. G.711 passthrough works by disabling all audio processing and hoping the network is clean enough.

---

### Section 2.10 — IoT/Wireless

#### Lesson 78: IoT/Wireless — SIM Provisioning and Data Sessions
- **Module:** 2 — Products
- **Section:** 2.10 — IoT/Wireless
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 13
- **Key Concepts:**
  1. SIM lifecycle: ordering, activation, suspension, deactivation
  2. APN (Access Point Name) configuration and data connectivity
  3. Data session management via API
  4. OTA (Over-the-Air) SIM management
  5. TAP files and inter-carrier roaming settlement
- **Description:** Covers Telnyx's IoT/wireless product. Explains SIM technology, how data sessions are established through APNs, and how OTA allows remote SIM profile updates. TAP (Transferred Account Procedure) files are the carrier-to-carrier billing mechanism for roaming data usage.

#### Lesson 79: eSIM — QR Provisioning and Remote Profile Management
- **Module:** 2 — Products
- **Section:** 2.10 — IoT/Wireless
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 78
- **Key Concepts:**
  1. eSIM vs. physical SIM: embedded, reprogrammable
  2. QR code provisioning: SM-DP+ to device
  3. Profile management: install, enable, disable, delete
  4. Multi-profile support: switching between operators
  5. GSMA RSP (Remote SIM Provisioning) architecture
- **Description:** Explains eSIM technology and Telnyx's eSIM offering. Covers the GSMA RSP architecture — the SM-DP+ (Subscription Manager Data Preparation) server holds profiles, the device downloads them via QR code. Covers the operational lifecycle and common provisioning issues.

---

### Section 2.11 — Networking

#### Lesson 80: Telnyx Networking — Cloud VPN and WireGuard
- **Module:** 2 — Products
- **Section:** 2.11 — Networking
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 13, 17
- **Key Concepts:**
  1. Programmable networking: private connectivity via API
  2. WireGuard: modern VPN protocol — simple, fast, cryptographically sound
  3. Cloud VPN: site-to-site and point-to-site configurations
  4. Global Edge Router: Telnyx's programmable routing layer
  5. Use cases: private SIP trunking, secure IoT backhaul
- **Description:** Covers Telnyx's networking products. WireGuard provides encrypted tunnels with minimal overhead. The Global Edge Router allows customers to programmatically control routing. Explains use cases: private SIP trunking without internet exposure, secure IoT device connectivity, and multi-cloud networking.

---

### Section 2.12 — Storage and AI/Inference

#### Lesson 81: Telnyx Storage — S3-Compatible Object Storage
- **Module:** 2 — Products
- **Section:** 2.12 — Storage/AI
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 18
- **Key Concepts:**
  1. S3-compatible API: buckets, objects, presigned URLs
  2. Multi-region storage and replication
  3. Use cases: call recordings, fax storage, media files
  4. Access control: IAM policies, bucket policies
  5. Integration with other Telnyx products
- **Description:** Covers Telnyx's object storage service. Explains the S3-compatible interface, storage architecture, and how it integrates with other Telnyx products (call recordings stored automatically, fax documents, etc.).

#### Lesson 82: AI/Inference — LLM Serving and Model Routing
- **Module:** 2 — Products
- **Section:** 2.12 — Storage/AI
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 18
- **Key Concepts:**
  1. LLM inference API: OpenAI-compatible endpoint
  2. Model routing: selecting optimal model/GPU for requests
  3. Embedding generation: vector representations for semantic search
  4. GPU infrastructure and scaling challenges
  5. Rate limiting, token counting, and billing
- **Description:** Covers Telnyx's AI inference platform. Explains how LLM serving works — models loaded on GPUs, requests routed to available capacity. Covers the OpenAI-compatible API, embedding generation, and operational considerations (GPU utilization, cold start, model loading).

---

### Section 2.13 — Enterprise and Infrastructure

#### Lesson 83: Enterprise Integration — Teams and Zoom
- **Module:** 2 — Products
- **Section:** 2.13 — Enterprise
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 57
- **Key Concepts:**
  1. Microsoft Teams Direct Routing: SIP trunk to Teams
  2. SBC requirements for Teams integration
  3. Zoom Phone BYOC: bringing Telnyx trunks to Zoom
  4. Media bypass vs. media through the cloud
  5. Common integration issues and debugging
- **Description:** Explains how Telnyx integrates with enterprise UC platforms. Teams Direct Routing requires specific SIP behaviors and TLS certificates. Zoom BYOC has its own requirements. Covers the media path options and common issues (certificate errors, codec mismatches, call quality differences).

#### Lesson 84: Telnyx Infrastructure Overview — Multi-Site, Bare Metal, Kubernetes
- **Module:** 2 — Products
- **Section:** 2.13 — Enterprise
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 57-83 (overview knowledge)
- **Key Concepts:**
  1. Multi-site architecture: data center locations and purposes
  2. Bare metal vs. cloud: why Telnyx runs on owned hardware
  3. Kubernetes for application orchestration
  4. Consul service mesh for service discovery and traffic management
  5. Network backbone: private fiber, peering, transit relationships
- **Description:** High-level overview of Telnyx's infrastructure. Explains the multi-site architecture, why bare metal is chosen for telecom workloads (predictable latency, high throughput), how Kubernetes orchestrates services, and how Consul provides service discovery. Foundation for Module 3's deep dive into infrastructure.

---

## Module 3 — Cloud Infrastructure & DevOps

*This module teaches the infrastructure platform that Telnyx runs on. As a NOC engineer, you'll interact with these systems daily — understanding them deeply is essential for effective incident response.*

---

### Section 3.1 — Containers and Docker

#### Lesson 85: Container Fundamentals — Why Containers Exist
- **Module:** 3 — Infrastructure
- **Section:** 3.1 — Containers
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** None (some Linux knowledge helpful)
- **Key Concepts:**
  1. Process isolation: namespaces (PID, network, mount, user)
  2. Resource limits: cgroups (CPU, memory, I/O)
  3. Container images: layered filesystems (OverlayFS)
  4. Container vs. VM: shared kernel, lighter weight
  5. Why telecom workloads benefit from containerization
- **Description:** Explains containers from first principles — they're not lightweight VMs, they're isolated processes. Covers Linux namespaces (how a container gets its own PID space, network stack, filesystem view) and cgroups (how CPU and memory limits are enforced). Essential for understanding Kubernetes.

#### Lesson 86: Docker Deep Dive — Images, Registries, and Runtime
- **Module:** 3 — Infrastructure
- **Section:** 3.1 — Containers
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 85
- **Key Concepts:**
  1. Dockerfile: building images layer by layer
  2. Image registries: pulling and pushing images
  3. Container runtime: containerd, runc
  4. Container networking: bridge, host, overlay networks
  5. Debugging containers: exec, logs, inspect
- **Description:** Covers Docker's build and runtime systems. Explains how Dockerfiles create layered images, how registries distribute them, and how the runtime creates containers from images. Covers essential debugging: `docker exec` for interactive access, `docker logs` for output, `docker inspect` for configuration.

---

### Section 3.2 — Kubernetes

#### Lesson 87: Kubernetes Architecture — Control Plane and Worker Nodes
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 86
- **Key Concepts:**
  1. Control plane: API server, etcd, scheduler, controller manager
  2. Worker nodes: kubelet, kube-proxy, container runtime
  3. The declarative model: desired state vs. current state
  4. etcd: the source of truth for cluster state
  5. API server: the central hub for all Kubernetes operations
- **Description:** Explains Kubernetes architecture — the control plane manages cluster state, worker nodes run workloads. The declarative model is key: you tell Kubernetes what you want (desired state), and controllers work to make reality match. Understanding this model is fundamental to using kubectl effectively.

#### Lesson 88: Pods — The Fundamental Unit of Deployment
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 87
- **Key Concepts:**
  1. Pod: one or more containers sharing network and storage
  2. Pod lifecycle: Pending → Running → Succeeded/Failed
  3. Init containers: setup tasks before main container starts
  4. Sidecar containers: auxiliary processes (logging, proxying)
  5. `kubectl get pods`, `kubectl describe pod`, `kubectl logs`
- **Description:** Deep dive into pods. Explains why pods exist (containers that need to share localhost and volumes), the pod lifecycle and its states, and how to inspect pods using kubectl. Covers init containers (database migration, config loading) and sidecars (Consul proxy, log shipping).

#### Lesson 89: Deployments, ReplicaSets, and Rolling Updates
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 88
- **Key Concepts:**
  1. ReplicaSet: ensuring N copies of a pod are running
  2. Deployment: managing ReplicaSets with rolling update strategy
  3. Rolling update: replacing pods incrementally (maxSurge, maxUnavailable)
  4. Rollback: reverting to a previous deployment revision
  5. `kubectl rollout status`, `kubectl rollout undo`
- **Description:** Explains how Kubernetes manages application lifecycle. Deployments create ReplicaSets, which create Pods. Rolling updates replace pods one-by-one to avoid downtime. Covers the update strategy parameters and how to perform rollbacks during incidents.

#### Lesson 90: Services and Networking — How Pods Communicate
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 89
- **Key Concepts:**
  1. ClusterIP services: stable internal IP for a set of pods
  2. NodePort and LoadBalancer: exposing services externally
  3. kube-proxy: iptables/IPVS rules for service routing
  4. DNS in Kubernetes: CoreDNS, service discovery via DNS
  5. Network policies: controlling pod-to-pod communication
- **Description:** Explains Kubernetes networking. Services provide stable endpoints for ephemeral pods. kube-proxy implements service routing using iptables or IPVS. CoreDNS enables service discovery by name. Network policies act as firewalls between pods. Critical for understanding how Telnyx's microservices communicate.

#### Lesson 91: Ingress, Load Balancing, and External Access
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 90
- **Key Concepts:**
  1. Ingress: HTTP/HTTPS routing to services
  2. Ingress controllers: nginx, HAProxy, Traefik
  3. TLS termination at the ingress layer
  4. Path-based and host-based routing
  5. External traffic policy and source IP preservation
- **Description:** Covers how external traffic reaches Kubernetes services. Ingress resources define routing rules, Ingress controllers implement them. Covers TLS termination, routing strategies, and the source IP preservation challenge (important for IP-based SIP authentication).

#### Lesson 92: Namespaces, Resource Limits, and Multi-Tenancy
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 88
- **Key Concepts:**
  1. Namespaces: logical cluster partitioning
  2. Resource requests and limits: CPU and memory guarantees
  3. LimitRanges and ResourceQuotas: cluster-level controls
  4. OOMKilled: what happens when a container exceeds memory limits
  5. CPU throttling: what happens when a container exceeds CPU limits
- **Description:** Explains resource management in Kubernetes. Requests guarantee minimum resources; limits cap maximum usage. OOMKilled (Out of Memory) is a common incident cause — a container exceeds its memory limit and is killed. CPU throttling degrades performance without killing the pod. Understanding these is essential for diagnosing performance issues.

#### Lesson 93: Kubernetes Troubleshooting — Essential kubectl Commands
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 87-92
- **Key Concepts:**
  1. `kubectl get` — listing resources with useful flags (-o wide, -o yaml, --all-namespaces)
  2. `kubectl describe` — detailed resource information and events
  3. `kubectl logs` — container logs (--previous for crashed containers)
  4. `kubectl exec` — interactive shell access to running containers
  5. `kubectl top` — real-time CPU/memory usage
- **Description:** Practical kubectl reference for NOC operations. Covers the essential commands with real examples: finding pods in CrashLoopBackOff, reading events to understand scheduling failures, accessing container logs for application errors, and getting interactive shells for deeper investigation.

#### Lesson 94: Kubernetes Events and Debugging Scheduling Failures
- **Module:** 3 — Infrastructure
- **Section:** 3.2 — Kubernetes
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 93
- **Key Concepts:**
  1. Kubernetes events: cluster-level activity log
  2. Common scheduling failures: Insufficient CPU/memory, node affinity, taints
  3. Pod status: Pending, CrashLoopBackOff, ImagePullBackOff, OOMKilled
  4. Node conditions: Ready, MemoryPressure, DiskPressure
  5. `kubectl get events --sort-by=.metadata.creationTimestamp`
- **Description:** Covers Kubernetes event system and common failure states. Maps pod statuses to root causes: Pending = scheduling issue, CrashLoopBackOff = application crash, ImagePullBackOff = registry/image issue, OOMKilled = memory limit exceeded. Shows how to use events to understand why pods aren't running.

---

### Section 3.3 — ArgoCD and GitOps

#### Lesson 95: GitOps — Declarative Infrastructure from Git
- **Module:** 3 — Infrastructure
- **Section:** 3.3 — ArgoCD/GitOps
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 89
- **Key Concepts:**
  1. GitOps principle: Git as the single source of truth for infrastructure
  2. Declarative configuration: what you want, not how to get there
  3. Automated sync: changes in Git automatically applied to clusters
  4. Drift detection: alerting when cluster state diverges from Git
  5. Audit trail: every change is a Git commit
- **Description:** Explains the GitOps deployment model. Instead of manually applying changes, all configuration lives in Git. ArgoCD watches the Git repository and ensures cluster state matches. This provides an audit trail (who changed what, when), easy rollbacks (revert the commit), and consistency across environments.

#### Lesson 96: ArgoCD — Application Deployment and Sync
- **Module:** 3 — Infrastructure
- **Section:** 3.3 — ArgoCD/GitOps
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 95
- **Key Concepts:**
  1. ArgoCD Application: mapping a Git path to a Kubernetes namespace
  2. Sync status: Synced, OutOfSync, Unknown
  3. Health status: Healthy, Degraded, Progressing, Missing
  4. Manual vs. automatic sync policies
  5. ArgoCD UI and CLI for NOC operations
- **Description:** Practical guide to ArgoCD. Shows how to check deployment status (sync and health), trigger manual syncs, and read the ArgoCD UI during incidents. Covers how to identify when a bad deployment caused an issue and how to initiate a rollback through ArgoCD.

---

### Section 3.4 — Consul

#### Lesson 97: Consul — Service Discovery and Health Checking
- **Module:** 3 — Infrastructure
- **Section:** 3.4 — Consul
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 90
- **Key Concepts:**
  1. Service registration: services register themselves with name, port, health check
  2. Service discovery: DNS and HTTP API for finding services
  3. Health checks: HTTP, TCP, script, TTL — determining service health
  4. Catalog vs. health: all registered vs. currently healthy instances
  5. Consul UI and CLI: `consul catalog services`, `consul members`
- **Description:** Explains how Consul provides service discovery for Telnyx's microservices. Every service registers with Consul and reports health via periodic checks. Other services discover healthy instances via DNS (service.service.consul) or HTTP API. Critical for understanding how traffic is routed during incidents.

#### Lesson 98: Consul Maintenance Mode and Service Mesh
- **Module:** 3 — Infrastructure
- **Section:** 3.4 — Consul
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 97
- **Key Concepts:**
  1. Maintenance mode: gracefully removing a node/service from rotation
  2. `consul maint -enable` — marking a node as under maintenance
  3. Consul Connect (service mesh): sidecar proxies for mTLS between services
  4. Intentions: access control between services
  5. Using Consul during incident response: draining traffic, isolating services
- **Description:** Covers operational Consul features. Maintenance mode removes services from discovery without stopping them — essential for safe deployments and troubleshooting. The service mesh (Connect) provides automatic mTLS between services and access control via intentions. Shows how to use these features during incidents.

---

### Section 3.5 — Load Balancing

#### Lesson 99: L4 vs. L7 Load Balancing — When and Why
- **Module:** 3 — Infrastructure
- **Section:** 3.5 — Load Balancing
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 16, 90
- **Key Concepts:**
  1. L4 load balancing: TCP/UDP level, fast, protocol-agnostic
  2. L7 load balancing: HTTP/SIP level, content-aware routing
  3. Algorithms: round-robin, least connections, IP hash, weighted
  4. Health checking: passive (monitor responses) vs. active (send probes)
  5. Why SIP needs special L7 handling (dialog affinity)
- **Description:** Explains the fundamental difference between L4 and L7 load balancing. L4 makes decisions based on IP/port — fast but blind to application content. L7 understands the protocol — can route based on SIP headers, HTTP paths, etc. SIP requires dialog affinity (all messages in a dialog go to the same server), which needs L7 awareness.

#### Lesson 100: HAProxy — Configuration, Monitoring, and Troubleshooting
- **Module:** 3 — Infrastructure
- **Section:** 3.5 — Load Balancing
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 99
- **Key Concepts:**
  1. HAProxy architecture: frontend → backend → server
  2. ACLs and routing rules
  3. Connection draining: gracefully removing backends
  4. HAProxy stats page: reading the dashboard
  5. Common HAProxy issues: connection limits, timeouts, health check failures
- **Description:** Practical guide to HAProxy. Covers configuration concepts (frontends listen, backends contain servers), monitoring via the stats page (sessions, queued connections, server states), and troubleshooting common issues. Connection draining is essential for safe deployments — stop sending new connections while existing ones finish.

---

### Section 3.6 — Observability

#### Lesson 101: Metrics — Prometheus and Time-Series Data
- **Module:** 3 — Infrastructure
- **Section:** 3.6 — Observability
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 87
- **Key Concepts:**
  1. Time-series metrics: name + labels + timestamp + value
  2. Metric types: counter, gauge, histogram, summary
  3. Prometheus pull model: scraping /metrics endpoints
  4. PromQL basics: rate(), increase(), histogram_quantile()
  5. Metric naming conventions and label best practices
- **Description:** Explains Prometheus's data model and query language. Counters always increase (request counts), gauges go up and down (CPU usage), histograms track distributions (request latency). PromQL is the query language — rate() converts counters to per-second rates, histogram_quantile() extracts percentiles. Foundation for all Grafana dashboard work.

#### Lesson 102: Logs — Loki and Graylog
- **Module:** 3 — Infrastructure
- **Section:** 3.6 — Observability
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 88
- **Key Concepts:**
  1. Structured logging: JSON logs with consistent fields
  2. Loki: log aggregation using labels (like Prometheus for logs)
  3. LogQL: Loki's query language for filtering and aggregating logs
  4. Graylog: full-text search with powerful query syntax
  5. When to use Loki vs. Graylog — different strengths
- **Description:** Covers the two log systems used at Telnyx. Loki is label-based (fast for filtering by service, pod, namespace) and integrates with Grafana. Graylog provides full-text search (powerful for searching SIP message content, error messages). Explains when to use each and how to write effective queries.

#### Lesson 103: Traces — Distributed Request Tracing
- **Module:** 3 — Infrastructure
- **Section:** 3.6 — Observability
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 101, 102
- **Key Concepts:**
  1. Distributed tracing: following a request across microservices
  2. Trace, span, and parent-child relationships
  3. Trace ID propagation: how context flows between services
  4. Identifying bottlenecks: which service is slow?
  5. Correlating traces with logs and metrics
- **Description:** Explains distributed tracing — following a single request (like a SIP INVITE) as it traverses multiple microservices. Each service creates a span; spans link together via trace ID. Shows how to use traces to identify which service in the chain is causing latency or errors.

#### Lesson 104: Grafana Dashboards — Reading and Building Queries
- **Module:** 3 — Infrastructure
- **Section:** 3.6 — Observability
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lessons 101, 102
- **Key Concepts:**
  1. Dashboard anatomy: panels, rows, variables, time range
  2. PromQL in Grafana: building metric visualizations
  3. LogQL in Grafana: log panel queries
  4. Dashboard variables: dynamic filtering by service, region, etc.
  5. Annotations: marking deployments, incidents on timelines
- **Description:** Practical guide to using Grafana as a NOC tool. Covers reading existing dashboards (understanding what each panel shows), building PromQL queries for custom investigation, using LogQL for log panels, and using variables to filter by service or region. Shows how to correlate metrics with deployment annotations.

#### Lesson 105: Building Effective Grafana Queries for Incident Investigation
- **Module:** 3 — Infrastructure
- **Section:** 3.6 — Observability
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 104
- **Key Concepts:**
  1. Rate queries: `rate(http_requests_total{status=~"5.."}[5m])`
  2. Error rate calculation: errors / total requests
  3. Latency percentiles: `histogram_quantile(0.99, ...)`
  4. Aggregation: `sum by (service)`, `topk(10, ...)`
  5. Alert-driven investigation: starting from the alert, drilling down
- **Description:** Advanced Grafana query techniques for incident investigation. Shows how to calculate error rates, latency percentiles, and aggregate across dimensions. Demonstrates the investigation workflow: start from an alert, identify the affected service, drill down to specific pods, correlate with logs.

---

### Section 3.7 — Alerting

#### Lesson 106: Alerting Pipelines — From Metric to Engineer
- **Module:** 3 — Infrastructure
- **Section:** 3.7 — Alerting
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 101, 104
- **Key Concepts:**
  1. Alerting rules: PromQL expressions with thresholds and duration
  2. Alertmanager: grouping, deduplication, routing, silencing
  3. Alert routing: severity → team → notification channel
  4. OpsGenie/PagerDuty integration: on-call schedules, escalation
  5. Alert fatigue: tuning thresholds to reduce noise
- **Description:** Traces the complete alerting pipeline. A Prometheus rule fires when a condition is true for a duration. Alertmanager groups related alerts, deduplicates, and routes to the appropriate team via OpsGenie/PagerDuty. On-call engineers receive notifications. Covers alert tuning — reducing false positives while catching real issues.

#### Lesson 107: Writing and Tuning Alert Rules
- **Module:** 3 — Infrastructure
- **Section:** 3.7 — Alerting
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 106
- **Key Concepts:**
  1. Good alert properties: actionable, relevant, timely
  2. For-duration: preventing alerts on brief spikes
  3. Severity levels: critical (wake people up) vs. warning (next business day)
  4. Runbook links: every alert should point to a troubleshooting guide
  5. Alert suppression during maintenance
- **Description:** Practical guide to alert engineering. A good alert is actionable (engineer knows what to do), has appropriate severity (critical vs. warning), includes runbook links, and has tuned thresholds to minimize noise. Covers suppression during planned maintenance windows.

---

## Module 4 — NOC Operations

*This module teaches the day-to-day skills of NOC engineering. It combines the technical knowledge from Modules 1-3 with operational processes and real-world troubleshooting scenarios.*

---

### Section 4.1 — Incident Response

#### Lesson 108: Incident Response Lifecycle — Detect, Triage, Mitigate, Resolve
- **Module:** 4 — Operations
- **Section:** 4.1 — Incident Response
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Module 3 (observability)
- **Key Concepts:**
  1. Detection: alert-driven vs. customer-reported vs. proactive monitoring
  2. Triage: is this real? What's the impact? What's the severity?
  3. Mitigation: stop the bleeding, even if root cause is unknown
  4. Resolution: fix the underlying cause
  5. Post-mortem: learn and prevent recurrence
- **Description:** Defines the incident lifecycle and the NOC engineer's role at each stage. Detection through monitoring or reports. Triage to assess impact and severity. Mitigation to reduce impact quickly (rollback, restart, failover). Resolution to fix the root cause. Post-mortem to prevent recurrence. Each stage has different priorities and timeframes.

#### Lesson 109: Severity Classification and Escalation Procedures
- **Module:** 4 — Operations
- **Section:** 4.1 — Incident Response
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 108
- **Key Concepts:**
  1. Severity levels: SEV1 (total outage) through SEV4 (minor issue)
  2. Impact assessment: number of customers, revenue impact, service degradation
  3. Escalation criteria: when to wake people up, when to involve leadership
  4. Communication: status page updates, customer notifications
  5. Incident commander role and responsibilities
- **Description:** Covers severity classification and escalation. SEV1 is total service outage — all hands on deck. SEV4 is a minor issue for business hours. Explains how to assess impact, when to escalate, and communication responsibilities. The incident commander coordinates response and communication.

#### Lesson 110: Incident Communication — Internal and External
- **Module:** 4 — Operations
- **Section:** 4.1 — Incident Response
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 109
- **Key Concepts:**
  1. Internal communication: incident channel, stakeholder updates
  2. External communication: status page, customer notifications
  3. Writing incident updates: factual, concise, customer-focused
  4. Update frequency: every 30 minutes for active SEV1/SEV2
  5. Avoiding blame and speculation in public communications
- **Description:** Covers the communication aspect of incident response. Internal updates keep the team coordinated. External updates keep customers informed. Shows how to write effective incident updates — factual, avoiding speculation, focusing on impact and mitigation actions.

---

### Section 4.2 — Debugging SIP Call Failures

#### Lesson 111: Reading SIP Traces — A Systematic Approach
- **Module:** 4 — Operations
- **Section:** 4.2 — SIP Debugging
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lessons 37-47
- **Key Concepts:**
  1. Finding SIP traces: Graylog queries by Call-ID, phone number, time window
  2. Reconstructing the call flow from log entries
  3. Key fields to check: Via, Contact, From, To, response codes
  4. Identifying which leg failed in B2BUA architecture
  5. Common error patterns and their signatures in traces
- **Description:** Step-by-step guide to reading SIP traces from Graylog. Shows how to search for calls, reconstruct the message flow, and identify where the failure occurred. In Telnyx's B2BUA architecture, failures can occur on the customer leg or the carrier leg — traces reveal which.

#### Lesson 112: SIP 4xx Errors — Client-Side Failures
- **Module:** 4 — Operations
- **Section:** 4.2 — SIP Debugging
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 111, 40
- **Key Concepts:**
  1. 401/403: authentication failures — wrong credentials, expired, IP mismatch
  2. 404: user not found — number not provisioned or misconfigured
  3. 408: request timeout — endpoint unreachable or too slow
  4. 480/486: temporarily unavailable / busy — endpoint-specific
  5. 487/488: request cancelled / not acceptable — negotiation failures
- **Description:** Detailed guide to each 4xx SIP error encountered in NOC operations. For each: what triggers it, common root causes, how to verify, and recommended actions. 408 is particularly nuanced — it can indicate network issues, endpoint problems, or timer misconfiguration.

#### Lesson 113: SIP 5xx/6xx Errors — Server and Global Failures
- **Module:** 4 — Operations
- **Section:** 4.2 — SIP Debugging
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 112
- **Key Concepts:**
  1. 500: server internal error — application crash or unhandled exception
  2. 502: bad gateway — upstream failure in proxy chain
  3. 503: service unavailable — overload, maintenance, or deployment
  4. 504: server timeout — upstream didn't respond
  5. 600/603: global busy/decline — callee rejects everywhere
- **Description:** Covers server-side SIP errors. 503 is the most common during incidents — it indicates the service is overloaded or in maintenance. 500 often indicates a software bug. Shows how to correlate these errors with Kubernetes pod health (CrashLoopBackOff, OOMKilled) and Consul health checks.

#### Lesson 114: One-Way Audio and No Audio — Systematic Debugging
- **Module:** 4 — Operations
- **Section:** 4.2 — SIP Debugging
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 27-28, 48-49, 111
- **Key Concepts:**
  1. One-way audio causes: NAT, firewall, SDP mismatch, codec mismatch
  2. No audio causes: wrong IP in SDP, blocked ports, SRTP negotiation failure
  3. Debugging steps: check SDP offers/answers, check firewall rules, check NAT
  4. RTP stream analysis: is RTP flowing? In both directions?
  5. Customer-side vs. Telnyx-side: isolating the problem leg
- **Description:** The most common and frustrating call quality issue. Provides a systematic debugging flowchart: verify SDP negotiation succeeded, check that media IPs/ports are reachable, verify RTP is flowing in both directions, check for NAT issues. Shows how to use SIP traces and RTCP reports to isolate the problem.

#### Lesson 115: Echo, Choppy Audio, and Other Quality Issues
- **Module:** 4 — Operations
- **Section:** 4.2 — SIP Debugging
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 32-36, 114
- **Key Concepts:**
  1. Echo: acoustic feedback vs. hybrid echo (impedance mismatch at TDM gateway)
  2. Choppy audio: jitter buffer underrun, packet loss, CPU overload
  3. Robotic/metallic audio: codec artifacts, extreme packet loss
  4. Audio delay: high latency, excessive buffering
  5. Cross-talk and audio bleeding: mixer or bridging issues
- **Description:** Covers non-connectivity audio quality issues. Echo has two causes — acoustic (speaker sound reaching microphone) and hybrid (impedance mismatch at 2-wire/4-wire conversion in PSTN gateways). Choppy audio typically indicates packet loss or jitter. Robotic audio is severe codec artifact from high loss. Each symptom maps to specific diagnostic steps.

---

### Section 4.3 — Debugging Message Delivery

#### Lesson 116: Message Delivery Failures — Systematic Troubleshooting
- **Module:** 4 — Operations
- **Section:** 4.3 — Messaging Debug
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 68-70
- **Key Concepts:**
  1. Message lifecycle: accepted → queued → sent → delivered/failed
  2. Carrier error codes: mapping to root causes
  3. Filtering and blocking: content, volume, 10DLC compliance
  4. Number type mismatch: sending SMS to a landline
  5. Graylog queries for tracing message delivery
- **Description:** Systematic approach to debugging message delivery failures. Traces a message through the pipeline using Graylog, identifies where it failed (queue, carrier submission, carrier rejection), and maps error codes to root causes and remediation actions.

#### Lesson 117: Carrier Filtering and Compliance Issues
- **Module:** 4 — Operations
- **Section:** 4.3 — Messaging Debug
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 116
- **Key Concepts:**
  1. Content filtering: spam detection, URL shortener blocks
  2. Volume filtering: sudden traffic spikes trigger blocks
  3. 10DLC compliance: unregistered campaigns get filtered
  4. Toll-free verification: required for high-volume messaging
  5. Working with carriers to resolve filtering
- **Description:** Covers carrier-side filtering — the most common cause of message delivery issues that aren't obvious. Carriers use AI-based content filters, volume thresholds, and compliance checks to block messages. Explains how to identify carrier filtering vs. Telnyx-side issues and the process for resolving blocks.

---

### Section 4.4 — Network Debugging

#### Lesson 118: Traceroute and MTR — Deep Dive
- **Module:** 4 — Operations
- **Section:** 4.4 — Network Debug
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 51
- **Key Concepts:**
  1. Traceroute mechanics: TTL increment, ICMP Time Exceeded
  2. TCP vs. UDP vs. ICMP traceroute — different results
  3. MTR statistics: loss%, sent, last, avg, best, worst, stdev
  4. Interpreting results: transit loss vs. ICMP rate limiting
  5. Forward and reverse path testing
- **Description:** Advanced network diagnostics. Extends Lesson 51 with deeper MTR interpretation. The key insight: loss at intermediate hops that doesn't appear at the final hop is usually ICMP rate limiting, not real loss. Real loss appears at the failing hop AND all subsequent hops. Covers when to use TCP traceroute (firewall-friendly) vs. UDP.

#### Lesson 119: Reading PCAPs — Wireshark for SIP and RTP
- **Module:** 4 — Operations
- **Section:** 4.4 — Network Debug
- **Estimated Read Time:** 9 minutes
- **Prerequisites:** Lessons 29, 39, 48
- **Key Concepts:**
  1. Capturing packets: tcpdump on servers, port mirroring
  2. Wireshark SIP display filters: `sip.Method`, `sip.Status-Code`, `sip.Call-ID`
  3. Wireshark RTP analysis: Statistics → RTP → Stream Analysis
  4. tshark: command-line packet analysis for server-side work
  5. Following a SIP call flow in Wireshark: Flow Graph
- **Description:** Hands-on PCAP analysis guide. Shows how to capture traffic with tcpdump, open in Wireshark, filter for specific SIP calls, analyze RTP stream quality (jitter, loss, sequence errors), and use the Flow Graph feature to visualize SIP call flows. Essential skill for deep debugging.

#### Lesson 120: Advanced PCAP Analysis — RTP Quality and Media Issues
- **Module:** 4 — Operations
- **Section:** 4.4 — Network Debug
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 119
- **Key Concepts:**
  1. RTP stream analysis: expected vs. received packets, lost, sequence errors
  2. Jitter analysis: inter-arrival time distribution
  3. Identifying burst loss: consecutive missing sequence numbers
  4. Codec identification from RTP payload types
  5. DTMF analysis: RFC 2833 events in RTP stream
- **Description:** Advanced RTP analysis in Wireshark. Shows how to identify specific media problems from PCAPs: burst loss vs. random loss, jitter patterns, codec mismatches, and DTMF issues. Covers the RTP player feature for actually listening to captured audio.

---

### Section 4.5 — Common Failure Patterns

#### Lesson 121: Common Failure Pattern — Service Overload and Cascading Failures
- **Module:** 4 — Operations
- **Section:** 4.5 — Failure Patterns
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 92, 97, 108
- **Key Concepts:**
  1. Cascading failure: one service failure triggers others
  2. Retry storms: failed requests retried, amplifying load
  3. Circuit breakers: stopping calls to failing services
  4. Back-pressure: slowing down input when output is saturated
  5. Recognition and mitigation during incidents
- **Description:** Explains cascading failures — the most dangerous failure pattern. When Service A depends on Service B, and B slows down, A's threads pile up waiting for B, then A starts failing, and services depending on A fail too. Retry storms amplify the problem. Covers recognition (increasing latency preceding error spikes) and mitigation (circuit breakers, shedding load).

#### Lesson 122: Common Failure Pattern — Database Connection Exhaustion
- **Module:** 4 — Operations
- **Section:** 4.5 — Failure Patterns
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 121
- **Key Concepts:**
  1. Connection pools: why applications maintain a pool of DB connections
  2. Pool exhaustion: all connections in use, new requests queue/fail
  3. Long-running queries: holding connections longer than expected
  4. Leak: connections not returned to pool after use
  5. Monitoring: connection pool metrics in Grafana
- **Description:** Covers database connection exhaustion — applications have a finite pool of database connections. When a slow query or leak consumes all connections, the entire application stops. Shows how to identify this pattern in Grafana (connection pool utilization), Graylog (connection timeout errors), and database monitoring.

#### Lesson 123: Common Failure Pattern — DNS and Certificate Failures
- **Module:** 4 — Operations
- **Section:** 4.5 — Failure Patterns
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lessons 19-21, 17
- **Key Concepts:**
  1. DNS resolution failure: SERVFAIL, timeout → complete service outage
  2. Expired TLS certificates: instant connection failures
  3. Certificate chain issues: missing intermediates
  4. Clock skew: TLS validation fails when system time is wrong
  5. Monitoring certificate expiry proactively
- **Description:** Two common but preventable failure patterns. DNS failures cause total outages because nothing can find anything. Certificate expiry causes sudden TLS handshake failures. Both are preventable with monitoring. Shows how to check and monitor certificates and DNS health.

#### Lesson 124: Common Failure Pattern — Deployment-Related Failures
- **Module:** 4 — Operations
- **Section:** 4.5 — Failure Patterns
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 89, 96
- **Key Concepts:**
  1. Bad deployment: code bug, misconfiguration, missing dependency
  2. Canary deployment: rolling out to a small percentage first
  3. Correlation: matching deployment timestamps to error onset
  4. Rollback procedure: reverting to last known good version
  5. Post-deployment monitoring: what to watch after deploying
- **Description:** Deployments are the #1 cause of incidents. Covers how to correlate deployment timestamps with error onset, the decision framework for rolling back, and what to monitor after a deployment. Annotations in Grafana make deployment correlation visual and immediate.

#### Lesson 125: Common Failure Pattern — Network Partition and Split Brain
- **Module:** 4 — Operations
- **Section:** 4.5 — Failure Patterns
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 97, 84
- **Key Concepts:**
  1. Network partition: two halves of the system can't communicate
  2. Split brain: two leaders/masters, conflicting decisions
  3. Consul partition behavior: services marked critical, no leader election
  4. Cross-datacenter communication failures
  5. Recovery: which side is authoritative?
- **Description:** Covers network partitions — when network connectivity between parts of the infrastructure fails. In a Consul-based system, partitions cause health checks to fail across the partition, services to be marked critical, and potentially split-brain scenarios. Covers how to detect, mitigate, and recover.

---

### Section 4.6 — Capacity Planning and Traffic Patterns

#### Lesson 126: Traffic Patterns — Daily, Weekly, and Seasonal Cycles
- **Module:** 4 — Operations
- **Section:** 4.6 — Capacity Planning
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 104
- **Key Concepts:**
  1. Diurnal patterns: peak business hours, timezone effects
  2. Weekly patterns: weekday vs. weekend traffic differences
  3. Seasonal patterns: holiday spikes, marketing campaigns
  4. Anomaly detection: distinguishing normal variation from problems
  5. Grafana: comparing current traffic to historical baselines
- **Description:** Covers traffic patterns specific to telecom. Voice traffic follows business hours (peak 10 AM - 4 PM). Messaging has different patterns (marketing messages in morning, notifications throughout day). Understanding normal patterns is essential for distinguishing real problems from natural variation.

#### Lesson 127: Capacity Planning — Forecasting and Provisioning
- **Module:** 4 — Operations
- **Section:** 4.6 — Capacity Planning
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 126
- **Key Concepts:**
  1. Capacity metrics: CPS (calls per second), concurrent calls, messages per second
  2. Headroom: maintaining buffer above peak capacity
  3. Horizontal scaling: adding more instances
  4. Vertical scaling: adding more resources to existing instances
  5. Bottleneck identification: which component saturates first
- **Description:** Explains capacity planning for telecom workloads. Key metrics include Calls Per Second (CPS), concurrent call count, and messages per second. Covers how to identify approaching capacity limits, forecast growth, and plan infrastructure additions.

---

### Section 4.7 — Maintenance and Post-Mortems

#### Lesson 128: Maintenance Windows — Safe Deployment Practices
- **Module:** 4 — Operations
- **Section:** 4.7 — Maintenance
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 98, 100, 124
- **Key Concepts:**
  1. Maintenance window planning: timing, impact assessment, rollback plan
  2. Pre-maintenance checks: verify monitoring, confirm rollback path
  3. Graceful drain: removing servers from rotation before maintenance
  4. Progressive rollout: one site/pod at a time
  5. Post-maintenance validation: confirming service health
- **Description:** Covers safe maintenance procedures. Planning includes impact assessment, timing (low-traffic windows), communication, and rollback plans. Execution uses graceful draining (Consul maintenance mode, connection draining), progressive rollout, and continuous monitoring. Post-maintenance validation confirms everything is healthy.

#### Lesson 129: Post-Mortem Writing — Learning from Incidents
- **Module:** 4 — Operations
- **Section:** 4.7 — Maintenance
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 108
- **Key Concepts:**
  1. Post-mortem structure: summary, timeline, root cause, impact, action items
  2. Blameless culture: focus on systems, not individuals
  3. Timeline reconstruction: what happened, when, who did what
  4. Root cause analysis: the "5 Whys" technique
  5. Action items: specific, measurable, assigned, time-bound
- **Description:** Covers post-mortem writing — the most important step for preventing recurrence. A good post-mortem has a clear timeline, honest root cause analysis (going deep enough to find systemic issues), accurate impact measurement, and specific action items. Blameless culture is essential — focusing on system improvements rather than individual blame.

#### Lesson 130: Post-Mortem Anti-Patterns and Best Practices
- **Module:** 4 — Operations
- **Section:** 4.7 — Maintenance
- **Estimated Read Time:** 5 minutes
- **Prerequisites:** Lesson 129
- **Key Concepts:**
  1. Anti-pattern: "human error" as root cause (dig deeper!)
  2. Anti-pattern: vague action items ("improve monitoring")
  3. Anti-pattern: no follow-through on action items
  4. Best practice: share post-mortems broadly for organizational learning
  5. Best practice: review action item completion regularly
- **Description:** Covers common post-mortem mistakes and how to avoid them. "Human error" is never a root cause — the question is why the system allowed the error. "Improve monitoring" is not an action item — "add alert for X metric exceeding Y threshold" is. Action items without owners and deadlines never get done.

---

## Module 5 — Security & Advanced Topics

*This module covers security, distributed systems concepts, databases, and automation — advanced topics that elevate a NOC engineer from reactive operator to proactive systems thinker.*

---

### Section 5.1 — Network Security

#### Lesson 131: Firewalls — Stateful Inspection and Rule Management
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 12-16
- **Key Concepts:**
  1. Stateful firewall: tracking connections, allowing return traffic
  2. Rule ordering: first match wins, default deny
  3. UDP "connection" tracking: timeout-based, problematic for RTP
  4. Firewall logs: identifying blocked traffic
  5. Common firewall misconfigurations that break VoIP
- **Description:** Covers firewall fundamentals with a telecom focus. Stateful firewalls track TCP connections and create pseudo-connections for UDP based on 5-tuple matching with timeouts. VoIP issues arise when UDP timeouts expire during call hold or when RTP ports are blocked. Covers how to read firewall logs and identify blocking.

#### Lesson 132: DDoS Attacks and Mitigation
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 131
- **Key Concepts:**
  1. DDoS attack types: volumetric, protocol, application layer
  2. SIP-specific DDoS: INVITE floods, REGISTER floods
  3. Volumetric mitigation: traffic scrubbing, blackholing
  4. Application-layer mitigation: rate limiting, CAPTCHAs, behavioral analysis
  5. Detecting DDoS in Grafana: sudden traffic spikes, connection counts
- **Description:** Covers DDoS attacks targeting telecom infrastructure. Volumetric attacks overwhelm bandwidth. SIP floods overwhelm signaling infrastructure. Covers detection (monitoring traffic volume, connection counts, error rates) and mitigation (upstream scrubbing, selective blackholing, rate limiting).

#### Lesson 133: Traffic Scrubbing — Cleaning Malicious Traffic
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 132
- **Key Concepts:**
  1. Traffic scrubbing: routing through cleaning centers to filter attack traffic
  2. BGP-based diversion: announcing routes to redirect traffic through scrubbers
  3. Scrubbing center operation: distinguishing legitimate from malicious packets
  4. GRE tunnels: returning clean traffic to origin after scrubbing
  5. On-premise vs. cloud scrubbing: trade-offs in latency and capacity
- **Description:** Covers traffic scrubbing as a DDoS mitigation strategy. When an attack is detected, BGP announcements redirect traffic through scrubbing centers that filter malicious packets while passing legitimate traffic back via GRE tunnels. Covers the trade-offs between on-premise scrubbing appliances (lower latency, limited capacity) and cloud-based scrubbing services (higher capacity, added latency). Understanding scrubbing is essential for NOC engineers coordinating DDoS response.

#### Lesson 134: SIP Security — Toll Fraud Detection and Prevention
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 50-55, 131
- **Key Concepts:**
  1. Toll fraud: unauthorized use of SIP infrastructure to make expensive calls
  2. International Revenue Share Fraud (IRSF): routing calls to premium-rate numbers
  3. Detection patterns: unusual destination countries, high-cost routes, off-hours spikes
  4. Prevention: IP ACLs, digest authentication, call rate limiting
  5. Real-time fraud monitoring: alerting on cost thresholds and destination anomalies
- **Description:** Covers SIP toll fraud — one of the most financially damaging telecom security threats. Attackers compromise SIP credentials or exploit misconfigured systems to route calls to premium-rate international numbers, generating revenue for the attacker. Detection relies on monitoring call patterns: unusual destinations, off-hours call spikes, and rapid cost accumulation. Prevention combines strong authentication, IP whitelisting, rate limiting, and real-time fraud detection systems.

#### Lesson 135: SIP Registration Attacks and Overs Detection
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 134
- **Key Concepts:**
  1. Registration attacks: brute-force REGISTER attempts to steal credentials
  2. Overs detection: identifying calls exceeding contracted capacity or authorization
  3. SIP scanner tools: SIPVicious, friendly-scanner user agents
  4. Fail2ban for SIP: detecting and blocking repeated auth failures
  5. Registration rate limiting and geo-blocking suspicious sources
- **Description:** Covers SIP registration attacks where attackers brute-force credentials by sending thousands of REGISTER requests with different password guesses. NOC engineers should monitor for high REGISTER failure rates, recognize scanner user-agent strings (e.g., "friendly-scanner"), and use tools like Fail2ban to auto-block offending IPs. Overs detection monitors for traffic exceeding contracted limits — important for both security and billing integrity.

#### Lesson 136: TLS Certificate Management for NOC Engineers
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 17, 131
- **Key Concepts:**
  1. TLS certificate chain: leaf, intermediate, root certificates
  2. Certificate expiry monitoring: the #1 preventable outage cause
  3. Certificate renewal: Let's Encrypt, ACME protocol, manual renewal workflows
  4. SIP TLS (SIPS): securing signaling with TLS on port 5061
  5. Mutual TLS (mTLS): both sides present certificates for authentication
- **Description:** Covers TLS certificate management — a critical NOC responsibility because expired certificates cause outages. Explains the certificate chain (leaf → intermediate → root), how browsers and SIP clients validate chains, and why missing intermediates cause failures. Covers monitoring certificate expiry with tools like Nagios checks or Prometheus blackbox exporter. Introduces SIPS (SIP over TLS) and mutual TLS for inter-carrier connections.

#### Lesson 137: Authentication and Authorization Patterns
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 136
- **Key Concepts:**
  1. Authentication vs. authorization: proving identity vs. granting permissions
  2. API key authentication: simple but limited (no expiry, no scoping)
  3. OAuth 2.0 and JWT tokens: modern API authentication with scopes and expiry
  4. RBAC: Role-Based Access Control for NOC tools and dashboards
  5. Audit logging: tracking who did what and when
- **Description:** Covers authentication and authorization patterns relevant to NOC operations. API keys are simple but lack expiry and fine-grained permissions. OAuth 2.0 with JWT tokens provides scoped, time-limited access. RBAC controls what different NOC team members can do — Level 1 engineers might view dashboards while Level 3 can modify infrastructure. Audit logging is essential for post-incident review and compliance.

#### Lesson 138: Network Segmentation and Zero Trust Principles
- **Module:** 5 — Security
- **Section:** 5.1 — Network Security
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 131, 137
- **Key Concepts:**
  1. Network segmentation: isolating signaling, media, management, and customer planes
  2. Zero Trust: never trust, always verify — even internal traffic
  3. Micro-segmentation: per-workload firewall policies
  4. Jump boxes / bastion hosts: controlled access to production infrastructure
  5. VPN vs. Zero Trust Network Access (ZTNA) for remote NOC access
- **Description:** Covers network segmentation — separating signaling (SIP), media (RTP), management (SSH, SNMP), and customer-facing networks. Zero Trust principles assume no implicit trust even within the network perimeter. Every request is authenticated and authorized. Covers bastion hosts for production access and the shift from traditional VPN to ZTNA for remote NOC engineers.

---

### Section 5.2 — Distributed Systems Concepts

#### Lesson 139: Introduction to Distributed Systems
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 17-20, 87
- **Key Concepts:**
  1. Distributed system: multiple computers coordinating to appear as one system
  2. Why distribute: scalability, fault tolerance, geographic proximity
  3. Fundamental challenges: network partitions, clock skew, partial failures
  4. Fallacies of distributed computing: the network is reliable, latency is zero, etc.
  5. CAP theorem preview: you can't have everything
- **Description:** Introduces distributed systems concepts that NOC engineers encounter daily. Modern telecom platforms are inherently distributed — SIP proxies across data centers, databases with replicas, message queues spanning regions. Understanding distributed systems fundamentals helps NOC engineers reason about why certain failure modes occur and why some problems can't be "fixed" but only traded off.

#### Lesson 140: The CAP Theorem — Consistency, Availability, Partition Tolerance
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 139
- **Key Concepts:**
  1. Consistency: every read returns the most recent write
  2. Availability: every request receives a response (not an error)
  3. Partition tolerance: system continues operating despite network splits
  4. CAP trade-off: during a partition, choose consistency OR availability
  5. Real-world examples: CP systems (etcd, ZooKeeper) vs. AP systems (Cassandra, DNS)
- **Description:** Explains the CAP theorem — during a network partition, a distributed system must choose between consistency and availability. CP systems (like etcd used by Kubernetes) refuse requests during partitions to maintain consistency. AP systems (like Cassandra or DNS) continue serving requests but may return stale data. NOC engineers must understand which trade-off each system in their stack makes, because it determines the failure behavior they'll observe.

#### Lesson 141: Eventual Consistency — Living with Stale Data
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 140
- **Key Concepts:**
  1. Eventual consistency: all replicas converge to the same state given enough time
  2. Convergence window: how long until all replicas agree
  3. Read-your-writes consistency: seeing your own updates immediately
  4. Conflict resolution: last-write-wins, vector clocks, CRDTs
  5. NOC implications: why a record you just updated might appear unchanged
- **Description:** Covers eventual consistency — the model used by many distributed databases and caches. After a write, different replicas may temporarily return different values. This explains why a NOC engineer might update a configuration in one dashboard and see stale data in another. Understanding convergence windows, conflict resolution strategies, and consistency levels helps debug "data not updating" issues.

#### Lesson 142: Consensus Algorithms — Raft and Paxos Simplified
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 140
- **Key Concepts:**
  1. Consensus problem: getting multiple nodes to agree on a value
  2. Leader election: choosing one node to coordinate writes
  3. Raft algorithm: leader-based consensus with log replication
  4. Quorum: majority of nodes must agree (3 of 5, 2 of 3)
  5. Split-brain: what happens when two leaders emerge
- **Description:** Covers consensus algorithms that underpin critical infrastructure: etcd (Kubernetes), Consul, ZooKeeper. Raft is the most approachable — a leader is elected, all writes go through the leader, and the leader replicates to followers. A quorum (majority) must acknowledge before a write is committed. NOC relevance: understanding why a 3-node etcd cluster survives 1 failure but not 2, and why even-numbered clusters are problematic.

#### Lesson 143: Distributed Locking and Leader Election in Practice
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 142
- **Key Concepts:**
  1. Distributed locks: ensuring only one process performs an action
  2. Consul sessions and locks: using Consul for distributed coordination
  3. Redis-based locks: Redlock algorithm, pitfalls
  4. Fencing tokens: preventing stale lock holders from causing damage
  5. TTL-based locks: automatic expiry to prevent deadlocks
- **Description:** Covers distributed locking — used when only one instance should perform an action (e.g., one cron runner sending billing reports, one instance processing a queue). Consul sessions provide reliable locking with health-check-based invalidation. Redis locks are simpler but have subtle failure modes. NOC engineers encounter locking issues when a node dies while holding a lock, causing processing to stall until the lock TTL expires.

#### Lesson 144: Replication Strategies — Single-Leader, Multi-Leader, Leaderless
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 141
- **Key Concepts:**
  1. Single-leader replication: one writer, multiple readers (PostgreSQL streaming replication)
  2. Multi-leader replication: multiple writers, conflict resolution required
  3. Leaderless replication: any node accepts writes (Cassandra, DynamoDB)
  4. Replication lag: the delay between write and replica update
  5. Failover: promoting a replica to leader when the primary fails
- **Description:** Covers replication strategies NOC engineers encounter. Single-leader (PostgreSQL) is simplest — one primary accepts writes, replicas serve reads. Failover promotes a replica. Multi-leader allows writes at multiple sites but requires conflict resolution. Leaderless systems (Cassandra) write to multiple nodes simultaneously using quorum reads/writes. Understanding replication topology explains lag-related issues and failover behavior.

#### Lesson 145: Service Discovery and Health Checking
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 87, 142
- **Key Concepts:**
  1. Service discovery: how services find each other in dynamic environments
  2. Consul service catalog: registering and querying services
  3. Health checks: TCP, HTTP, script-based, TTL-based
  4. DNS-based discovery: Consul DNS interface, SRV records
  5. Anti-entropy: Consul's mechanism for keeping state consistent
- **Description:** Covers service discovery — essential in dynamic environments where IP addresses change. Consul maintains a service catalog with health checks; unhealthy instances are automatically removed from DNS responses and load balancer pools. NOC engineers use service discovery to understand current topology, identify unhealthy instances, and debug routing issues. Covers Consul's DNS interface for seamless integration with existing systems.

#### Lesson 146: Message Queues and Event-Driven Architecture
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 139
- **Key Concepts:**
  1. Message queues: decoupling producers from consumers (RabbitMQ, Kafka)
  2. Topics and partitions: organizing messages for parallel consumption
  3. Consumer groups: distributing work across multiple consumers
  4. Dead letter queues: handling messages that can't be processed
  5. Backpressure: what happens when consumers can't keep up
- **Description:** Covers message queues that connect telecom platform components. CDR (Call Detail Record) processing, billing events, and notification delivery often use message queues. Kafka provides high-throughput ordered event streams; RabbitMQ provides flexible routing. NOC engineers monitor queue depth (growing = consumers falling behind), consumer lag, and dead letter queues (messages that repeatedly fail processing).

#### Lesson 147: Circuit Breakers and Retry Patterns
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.2 — Distributed Systems
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 139
- **Key Concepts:**
  1. Circuit breaker pattern: stop calling a failing service to prevent cascade
  2. States: closed (normal), open (blocking), half-open (testing recovery)
  3. Retry with exponential backoff: increasing wait between retries
  4. Retry storms: when all clients retry simultaneously after an outage
  5. Jitter: randomizing retry timing to prevent thundering herd
- **Description:** Covers resilience patterns essential for distributed telecom systems. Circuit breakers prevent a failing downstream service from cascading failures upstream — if a billing API is down, stop calling it rather than queuing thousands of timeouts. Retry with exponential backoff and jitter prevents retry storms where all clients hammer a recovering service simultaneously. NOC engineers should understand these patterns to diagnose cascade failures.

---

### Section 5.3 — Databases for NOC

#### Lesson 148: Relational Database Fundamentals — PostgreSQL
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 17, 139
- **Key Concepts:**
  1. Tables, rows, columns: structured data storage
  2. Primary keys and foreign keys: uniqueness and relationships
  3. SQL basics: SELECT, WHERE, JOIN, GROUP BY, ORDER BY
  4. Indexes: B-tree indexes for fast lookups
  5. Transactions: ACID properties ensuring data integrity
- **Description:** Covers PostgreSQL fundamentals for NOC engineers who need to query telecom databases. Many telecom platforms store configuration, routing rules, and customer data in PostgreSQL. NOC engineers need basic SQL to look up customer configurations, check routing tables, and investigate billing records. Covers essential query patterns and why indexes matter for performance.

#### Lesson 149: PostgreSQL for Telecom — Common Queries and Patterns
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 148
- **Key Concepts:**
  1. CDR queries: filtering call records by time, customer, destination
  2. Configuration lookups: finding routing rules and customer settings
  3. Aggregation queries: counting calls, summing minutes, calculating ASR
  4. Date/time functions: timezone handling, interval arithmetic
  5. Read replicas: querying replicas for reporting to avoid impacting production
- **Description:** Covers practical PostgreSQL queries for telecom. Finding all calls for a customer in the last hour, calculating ASR (Answer Seizure Ratio) by carrier, identifying failed calls by error code — these are daily NOC tasks. Emphasizes always querying read replicas for heavy analytical queries and being mindful of query impact on production databases.

#### Lesson 150: Query Optimization — EXPLAIN Plans and Index Tuning
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 149
- **Key Concepts:**
  1. EXPLAIN ANALYZE: understanding query execution plans
  2. Sequential scan vs. index scan: full table read vs. targeted lookup
  3. Missing indexes: the most common cause of slow queries
  4. Query plan reading: identifying costly operations (Sort, Hash Join, Seq Scan)
  5. pg_stat_statements: finding the most resource-intensive queries
- **Description:** Covers query optimization for NOC engineers who need to investigate slow database performance. EXPLAIN ANALYZE shows exactly how PostgreSQL executes a query — whether it uses indexes or scans entire tables. A sequential scan on a million-row CDR table takes seconds; an index scan takes milliseconds. Covers how to identify missing indexes and use pg_stat_statements to find queries consuming the most resources.

#### Lesson 151: Connection Pooling — PgBouncer and Connection Management
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 148
- **Key Concepts:**
  1. Connection overhead: each PostgreSQL connection consumes ~10MB memory
  2. Connection pooling: sharing a pool of connections across many clients
  3. PgBouncer: lightweight connection pooler for PostgreSQL
  4. Pool modes: session, transaction, statement pooling
  5. Monitoring pool saturation: all connections in use, clients waiting
- **Description:** Covers connection pooling — critical for telecom platforms with many application instances. Each PostgreSQL connection consumes significant memory; 1000 direct connections would require ~10GB just for connection overhead. PgBouncer sits between applications and PostgreSQL, maintaining a small pool of actual connections shared across clients. NOC engineers monitor pool utilization and waiting clients to detect connection exhaustion.

#### Lesson 152: ClickHouse for Analytics — Columnar Storage Fundamentals
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 148
- **Key Concepts:**
  1. Columnar storage: storing data by column rather than row
  2. Why columnar is fast for analytics: reading only needed columns
  3. Compression: similar values in columns compress extremely well
  4. ClickHouse MergeTree engine: sorted storage with automatic background merges
  5. Row-oriented vs. columnar: OLTP (PostgreSQL) vs. OLAP (ClickHouse)
- **Description:** Introduces ClickHouse — a columnar database used for telecom analytics. While PostgreSQL stores data row-by-row (great for looking up individual records), ClickHouse stores data column-by-column (great for aggregating millions of records). Querying "average call duration by carrier for the last month" over 100 million CDRs takes seconds in ClickHouse vs. minutes in PostgreSQL. NOC dashboards often pull from ClickHouse for real-time analytics.

#### Lesson 153: ClickHouse Queries for NOC — CDR Analytics and Dashboards
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 152
- **Key Concepts:**
  1. Time-series aggregation: GROUP BY toStartOfMinute(), toStartOfHour()
  2. Approximate functions: uniqExact() vs. uniq() for fast cardinality estimates
  3. Materialized views: pre-aggregating data for dashboard performance
  4. Sampling: querying a fraction of data for quick estimates
  5. Grafana + ClickHouse: connecting analytics to dashboards
- **Description:** Covers practical ClickHouse queries for NOC analytics. Time-bucketed aggregations (calls per minute, ASR per hour) power real-time dashboards. Materialized views pre-compute common aggregations so dashboards load instantly. Sampling allows querying a subset of data for quick estimates during investigations. Covers connecting ClickHouse to Grafana for building telecom operations dashboards.

#### Lesson 154: Database Replication and Failover for NOC
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 144, 148
- **Key Concepts:**
  1. PostgreSQL streaming replication: WAL-based primary-to-replica replication
  2. Synchronous vs. asynchronous replication: durability vs. performance
  3. Replication lag monitoring: seconds behind primary
  4. Automated failover: Patroni, pg_auto_failover
  5. Split-brain prevention: fencing the old primary after failover
- **Description:** Covers database replication and failover — critical knowledge for NOC engineers. PostgreSQL streaming replication sends Write-Ahead Log (WAL) records from primary to replicas. Asynchronous replication is faster but risks data loss during failover. Patroni automates failover using consensus (etcd/Consul) to prevent split-brain. NOC engineers must monitor replication lag and be prepared for failover scenarios.

#### Lesson 155: Database Backup and Recovery Procedures
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.3 — Databases for NOC
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 154
- **Key Concepts:**
  1. pg_dump: logical backups for individual databases
  2. pg_basebackup: physical backups for full cluster restoration
  3. Point-in-time recovery (PITR): restoring to a specific moment using WAL archives
  4. Backup verification: regularly testing restoration procedures
  5. RTO and RPO: Recovery Time Objective and Recovery Point Objective
- **Description:** Covers database backup and recovery — the last line of defense against data loss. Logical backups (pg_dump) export SQL that can restore individual tables or databases. Physical backups (pg_basebackup) with WAL archiving enable point-in-time recovery to any moment. NOC engineers should know RTO (how long recovery takes) and RPO (how much data loss is acceptable) for each database, and regularly verify backup restoration works.

---

### Section 5.4 — Automation

#### Lesson 156: Shell Scripting Fundamentals for NOC
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 1-5
- **Key Concepts:**
  1. Bash basics: variables, conditionals, loops
  2. Exit codes: 0 for success, non-zero for failure
  3. Pipes and redirection: chaining commands, capturing output
  4. Text processing: grep, awk, sed, cut for log parsing
  5. Script safety: set -euo pipefail, quoting variables
- **Description:** Covers shell scripting fundamentals for NOC automation. Many NOC tasks are repetitive: checking service status across servers, parsing logs for patterns, extracting metrics. Bash scripts automate these tasks. Covers essential patterns: processing log files with grep/awk, checking service health across multiple hosts, and safely handling errors. Emphasizes defensive scripting with set -euo pipefail to catch errors early.

#### Lesson 157: Shell Scripting for NOC — Practical Scripts
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 156
- **Key Concepts:**
  1. Health check scripts: verifying multiple services and reporting status
  2. Log rotation and cleanup: managing disk space automatically
  3. Batch operations: restarting services across multiple hosts via SSH
  4. Report generation: extracting metrics and formatting summaries
  5. Cron scheduling: automating script execution on schedule
- **Description:** Covers practical NOC shell scripts. A health check script that SSH-es into 20 servers, checks service status, and reports failures. A log cleanup script that removes files older than 30 days to prevent disk-full alerts. A batch restart script that drains, restarts, and validates services one at a time. Covers scheduling with cron and monitoring script execution for failures.

#### Lesson 158: Python Fundamentals for NOC Automation
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 156
- **Key Concepts:**
  1. Python basics: variables, data types, functions, loops
  2. Libraries: requests (HTTP), json, csv, datetime
  3. Virtual environments: isolating dependencies with venv
  4. Error handling: try/except for robust scripts
  5. When to use Python vs. Bash: complexity threshold, data manipulation needs
- **Description:** Covers Python fundamentals for NOC engineers who need more power than Bash provides. Python excels at API interactions, JSON data manipulation, complex logic, and building tools. Covers essential libraries: requests for HTTP API calls, json for parsing API responses, csv for report generation, and datetime for time calculations. The rule of thumb: if a Bash script exceeds 50 lines or needs to parse JSON, rewrite it in Python.

#### Lesson 159: Python for API Scripting — REST and GraphQL
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lesson 158
- **Key Concepts:**
  1. REST API interaction: GET, POST, PUT, DELETE with the requests library
  2. Authentication: API keys, Bearer tokens, OAuth2 in Python
  3. Response handling: status codes, JSON parsing, error handling
  4. Pagination: handling APIs that return results in pages
  5. Rate limiting: respecting API limits with retry logic and backoff
- **Description:** Covers Python API scripting for NOC automation. Most modern telecom platforms expose REST APIs for provisioning, monitoring, and management. Python scripts can automate customer provisioning, pull metrics from monitoring APIs, trigger incident creation in PagerDuty, and update configurations. Covers authentication patterns, pagination handling, and graceful error handling with retries.

#### Lesson 160: Python for Log Analysis and Data Processing
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 158
- **Key Concepts:**
  1. File processing: reading and parsing large log files efficiently
  2. Regular expressions: re module for pattern matching in logs
  3. Counter and defaultdict: aggregating log data
  4. CSV output: generating reports from parsed data
  5. Pandas basics: DataFrames for complex data analysis
- **Description:** Covers Python for log analysis — a common NOC need when investigating incidents. Parsing SIP logs to count error codes by carrier, extracting timing data from application logs, correlating events across multiple log files. Python handles large files efficiently with generators and provides powerful pattern matching with regular expressions. Covers outputting results to CSV for sharing and basic Pandas for more complex analysis.

#### Lesson 161: Building NOC Runbooks — Structure and Best Practices
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 108, 157
- **Key Concepts:**
  1. Runbook structure: trigger, assessment, action steps, escalation, verification
  2. Decision trees: if-then logic for different scenarios
  3. Copy-paste commands: exact commands ready to execute
  4. Automation level: fully manual → semi-automated → fully automated
  5. Runbook maintenance: reviewing and updating after every incident
- **Description:** Covers runbook creation — the bridge between tribal knowledge and repeatable procedures. A good runbook has a clear trigger (alert name, symptoms), assessment steps (what to check first), action steps (exact commands with copy-paste blocks), escalation criteria (when to involve senior engineers), and verification steps (how to confirm the fix). Covers the progression from manual runbooks to semi-automated (scripts with human decision points) to fully automated remediation.

#### Lesson 162: Automating Runbooks — From Manual to Scripted
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 158, 161
- **Key Concepts:**
  1. Identifying automation candidates: frequent, well-understood, low-risk procedures
  2. Script structure: assessment phase, action phase, verification phase
  3. Dry-run mode: showing what would happen without making changes
  4. Logging: recording every action for audit trail
  5. Safety guards: pre-condition checks, confirmation prompts, rollback capability
- **Description:** Covers automating runbook procedures. Not every runbook should be automated — start with frequent, well-understood, low-risk procedures. Automated runbooks should include pre-condition checks (is this the right scenario?), dry-run mode (show what would happen), comprehensive logging, and rollback capability. A health check that detects and restarts a failed service saves hours of manual intervention when it fires at 3 AM.

#### Lesson 163: ChatOps — Operating Infrastructure Through Chat
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 108, 162
- **Key Concepts:**
  1. ChatOps: performing operations through chat commands (Slack, Teams)
  2. Bot frameworks: Hubot, Errbot, custom Slack bots
  3. Command patterns: !status, !restart service, !check customer
  4. Visibility: everyone sees what's happening in real-time
  5. Access control: restricting dangerous commands to authorized users
- **Description:** Covers ChatOps — running NOC operations through chat platforms. Instead of SSH-ing into servers individually, engineers type commands in Slack: "!status sip-proxy-01", "!restart billing-service", "!check customer 12345". Benefits include shared visibility (everyone sees actions and results), built-in audit trail, and lower barrier to action during incidents. Covers building simple bots and implementing access controls for dangerous operations.

#### Lesson 164: ChatOps for Incident Management
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 163
- **Key Concepts:**
  1. Incident channels: auto-creating dedicated channels per incident
  2. Status updates: bot-driven timeline tracking in the channel
  3. Escalation commands: !page team-name, !escalate to-level-3
  4. Information gathering: !timeline, !impact, !affected-customers
  5. Post-incident: auto-generating post-mortem templates from channel history
- **Description:** Covers ChatOps specifically for incident management. When an incident is declared, a bot creates a dedicated channel, invites responders, and starts tracking the timeline. Commands like !timeline show the sequence of events, !impact summarizes affected services, and !page escalates to additional teams. After resolution, the bot generates a post-mortem template pre-filled with the timeline from chat history.

#### Lesson 165: Infrastructure as Code — Ansible Basics for NOC
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 8 minutes
- **Prerequisites:** Lessons 156, 158
- **Key Concepts:**
  1. Infrastructure as Code (IaC): defining infrastructure in version-controlled files
  2. Ansible: agentless automation using SSH and YAML playbooks
  3. Inventory: defining hosts and groups
  4. Playbooks: ordered lists of tasks to execute
  5. Idempotency: running the same playbook twice produces the same result
- **Description:** Covers Ansible basics for NOC engineers who manage infrastructure. Ansible uses SSH to execute tasks on remote hosts — no agent installation required. Playbooks define tasks in YAML: install packages, configure services, deploy files. Idempotency means running a playbook multiple times is safe — it only makes changes when needed. NOC engineers use Ansible for consistent configuration across servers and automated deployment procedures.

#### Lesson 166: Ansible for NOC — Practical Playbooks
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 165
- **Key Concepts:**
  1. Service management playbooks: restart, configure, validate
  2. Rolling updates: updating one host at a time with serial keyword
  3. Handlers: triggering restarts only when configuration changes
  4. Vault: encrypting sensitive variables (passwords, API keys)
  5. Ad-hoc commands: quick one-off tasks across multiple hosts
- **Description:** Covers practical Ansible playbooks for NOC operations. A rolling restart playbook that drains a host, restarts the service, validates health, then moves to the next. Configuration update playbooks that push changes and only restart when files actually changed (handlers). Vault for storing sensitive credentials. Ad-hoc commands for quick tasks: checking disk space on all servers, finding which hosts run a specific process.

#### Lesson 167: CI/CD Pipelines — Understanding the Deployment Pipeline
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 97-100, 165
- **Key Concepts:**
  1. CI/CD: Continuous Integration and Continuous Delivery/Deployment
  2. Pipeline stages: build, test, deploy to staging, deploy to production
  3. Artifact management: storing built packages for deployment
  4. Deployment strategies: rolling, blue-green, canary
  5. Rollback: quickly reverting to the previous version
- **Description:** Covers CI/CD pipelines that NOC engineers interact with during deployments. Understanding the pipeline helps NOC engineers know what was deployed, when, and how to roll back. Covers pipeline stages from code commit through production deployment, artifact versioning, and deployment strategies. NOC engineers should know how to trigger rollbacks and read pipeline logs when a deployment causes issues.

#### Lesson 168: Terraform Basics — Infrastructure Provisioning
- **Module:** 5 — Security & Advanced Topics
- **Section:** 5.4 — Automation
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lesson 165
- **Key Concepts:**
  1. Terraform: declarative infrastructure provisioning
  2. State file: tracking what Terraform manages
  3. Plan and apply: preview changes before executing
  4. Providers: AWS, GCP, Azure, Cloudflare, etc.
  5. Terraform in NOC context: understanding infrastructure changes, reading plans
- **Description:** Covers Terraform basics for NOC engineers who need to understand infrastructure provisioning. While NOC engineers may not write Terraform daily, they need to read terraform plan output to understand what infrastructure changes are happening, review state to know what's deployed, and occasionally apply pre-approved changes. Understanding Terraform helps debug infrastructure-level issues and communicate with DevOps teams.

---

## Module 6 — Soft Skills & Career Growth

*This module covers the human side of NOC operations — communication, teamwork, career development, and leadership skills that distinguish senior NOC engineers.*

---

### Section 6.1 — Communication Skills

#### Lesson 169: Technical Communication — Writing Clear Status Updates
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.1 — Communication
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lessons 108-110
- **Key Concepts:**
  1. Audience awareness: executives vs. engineers need different information
  2. Status update structure: what's happening, impact, ETA, next steps
  3. Avoiding jargon: translating technical details for non-technical stakeholders
  4. Update frequency: how often and when to communicate during incidents
  5. Written vs. verbal: when to use each medium
- **Description:** Covers technical communication — a skill that separates great NOC engineers from good ones. During incidents, clear communication reduces confusion and builds trust. Status updates should state what's happening (not how you're fixing it), the business impact, estimated time to resolution, and next steps. Different audiences need different levels of detail: executives want impact and ETA; engineers want technical details.

#### Lesson 170: Stakeholder Management During Incidents
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.1 — Communication
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 169
- **Key Concepts:**
  1. Stakeholder identification: who needs to know, at what level of detail
  2. Proactive communication: updating before being asked
  3. Managing expectations: honest ETAs, transparent unknowns
  4. Escalation communication: what to say when escalating
  5. Customer-facing communication: public status pages and customer notifications
- **Description:** Covers stakeholder management during incidents. Different stakeholders need different information: account managers need customer impact, executives need business impact, engineers need technical detail. Proactive updates — sent before people ask — build trust and reduce interruptions. Honest communication about unknowns ("we're investigating, no ETA yet") is better than overconfident promises that miss deadlines.

#### Lesson 171: Documentation as a Discipline
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.1 — Communication
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lessons 161, 169
- **Key Concepts:**
  1. Documentation types: runbooks, architecture docs, onboarding guides, SOPs
  2. Writing for the 3 AM reader: clear, actionable, no assumptions
  3. Keeping docs current: review schedules, ownership, freshness indicators
  4. Wiki organization: consistent structure, searchability
  5. Documentation debt: what happens when docs are neglected
- **Description:** Covers documentation as a core NOC discipline. Good documentation is written for the engineer at 3 AM who has never seen this problem before — clear, step-by-step, with no assumed knowledge. Covers organizing documentation for findability, establishing review schedules to prevent staleness, and treating documentation updates as part of incident resolution (every post-mortem should update relevant docs).

---

### Section 6.2 — Career Development

#### Lesson 172: NOC Career Path — From L1 to Principal Engineer
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.2 — Career Development
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** None
- **Key Concepts:**
  1. NOC Level 1: monitoring, alert triage, runbook execution
  2. NOC Level 2: troubleshooting, root cause analysis, escalation management
  3. NOC Level 3/Senior: architecture knowledge, mentoring, process improvement
  4. Career branches: SRE, DevOps, Network Engineering, Security
  5. Building expertise: certifications, side projects, cross-team collaboration
- **Description:** Covers the NOC career path and growth opportunities. Level 1 engineers follow runbooks and escalate; Level 2 engineers troubleshoot independently and improve processes; Level 3/Senior engineers design solutions, mentor juniors, and drive reliability improvements. Many NOC engineers transition into SRE, DevOps, or specialized roles. Covers how to build expertise through certifications, side projects, and actively seeking cross-team exposure.

#### Lesson 173: Building a NOC Knowledge Base
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.2 — Career Development
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lessons 161, 171
- **Key Concepts:**
  1. Personal knowledge management: note-taking systems for technical learning
  2. Team knowledge bases: shared wikis, runbooks, decision records
  3. Architecture Decision Records (ADRs): capturing why decisions were made
  4. Onboarding documentation: reducing ramp-up time for new engineers
  5. Knowledge sharing: brown bags, tech talks, pair debugging sessions
- **Description:** Covers building and maintaining knowledge bases — both personal and team-wide. Personal systems (notes, bookmarks, snippets) help you find solutions faster. Team knowledge bases reduce "bus factor" by distributing tribal knowledge. Architecture Decision Records capture not just what was decided but why, which is invaluable when someone later asks "why do we do it this way?" Regular knowledge sharing sessions build collective expertise.

#### Lesson 174: Mentoring and Knowledge Transfer
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.2 — Career Development
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lesson 172
- **Key Concepts:**
  1. Shadow shifts: new engineers observing experienced operators
  2. Guided troubleshooting: coaching through problems rather than solving them
  3. Escalation as teaching: explaining reasoning when accepting escalations
  4. Creating safe learning environments: allowing mistakes without blame
  5. Reverse mentoring: junior engineers teaching seniors new tools and techniques
- **Description:** Covers mentoring — a key responsibility of senior NOC engineers. Shadow shifts let new engineers learn by observing real operations. Guided troubleshooting ("what would you check next?") builds problem-solving skills better than giving answers. When accepting escalations, explaining your reasoning teaches the escalating engineer. Creating psychological safety — where making mistakes is expected and learning from them is valued — is essential for team growth.

#### Lesson 175: Metrics That Matter — Measuring NOC Performance
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.2 — Career Development
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 108, 117
- **Key Concepts:**
  1. MTTD: Mean Time to Detect — how quickly problems are identified
  2. MTTR: Mean Time to Resolve — overall incident resolution time
  3. Alert signal-to-noise ratio: percentage of actionable vs. false/noisy alerts
  4. Escalation rate: percentage of incidents requiring escalation
  5. Toil measurement: tracking repetitive manual work for automation opportunities
- **Description:** Covers measuring NOC performance with meaningful metrics. MTTD measures detection speed (how long between problem occurrence and first alert). MTTR measures resolution speed. Alert signal-to-noise ratio reveals monitoring quality. Escalation rate shows team capability and training needs. Toil measurement identifies repetitive work ripe for automation. These metrics guide investment in monitoring improvements, training, and automation.

---

### Section 6.3 — Advanced Operations

#### Lesson 176: Chaos Engineering — Proactively Finding Weaknesses
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.3 — Advanced Operations
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 124, 147
- **Key Concepts:**
  1. Chaos engineering: deliberately injecting failures to test resilience
  2. Game days: planned exercises simulating outage scenarios
  3. Failure injection: killing processes, introducing latency, dropping packets
  4. Blast radius control: limiting chaos experiments to safe scope
  5. Steady state hypothesis: defining expected behavior before experiments
- **Description:** Covers chaos engineering — proactively testing system resilience by deliberately injecting failures. Rather than waiting for 3 AM surprises, chaos experiments reveal weaknesses in controlled conditions. Game days simulate scenarios like "primary database fails" or "network partition between data centers." NOC teams practice their response procedures while verifying that automated failover actually works. Start small (kill one pod), verify monitoring detects it, then gradually increase blast radius.

#### Lesson 177: SRE Principles for NOC — Error Budgets and SLOs
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.3 — Advanced Operations
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 117, 175
- **Key Concepts:**
  1. SLI: Service Level Indicator — the measurement (e.g., request success rate)
  2. SLO: Service Level Objective — the target (e.g., 99.95% success rate)
  3. SLA: Service Level Agreement — the contractual commitment with penalties
  4. Error budget: allowed unreliability (0.05% = 21.9 min/month downtime)
  5. Error budget policy: what happens when the budget is exhausted
- **Description:** Covers Site Reliability Engineering (SRE) principles applied to NOC operations. SLOs define reliability targets based on user experience (SLIs). The error budget is the inverse — the amount of allowed unreliability. When error budget is healthy, teams push features faster; when depleted, teams focus on reliability. This framework turns reliability from a vague goal into a measurable, actionable metric that balances feature velocity with operational stability.

#### Lesson 178: Observability Beyond Monitoring — Traces and Correlation
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.3 — Advanced Operations
- **Estimated Read Time:** 7 minutes
- **Prerequisites:** Lessons 82, 117
- **Key Concepts:**
  1. Three pillars: metrics, logs, traces — and how they complement each other
  2. Distributed tracing: following a request across multiple services
  3. Trace ID correlation: linking logs across services using a shared identifier
  4. OpenTelemetry: standard framework for collecting telemetry data
  5. Exemplars: linking metrics to specific trace examples
- **Description:** Covers advanced observability beyond basic monitoring. Distributed tracing follows a single request (e.g., an API call that triggers SIP signaling, billing, and CDR generation) across all services, showing where time is spent and where failures occur. Correlating logs with trace IDs lets you jump from a Grafana metric spike to the exact log lines across all involved services. OpenTelemetry provides a vendor-neutral standard for instrumenting applications.

#### Lesson 179: Cost Management and Resource Optimization
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.3 — Advanced Operations
- **Estimated Read Time:** 6 minutes
- **Prerequisites:** Lessons 87, 127
- **Key Concepts:**
  1. Cloud cost monitoring: understanding billing dimensions (compute, storage, network)
  2. Right-sizing: matching instance types to actual resource usage
  3. Reserved capacity: committing to usage for discounts
  4. Idle resource detection: finding underutilized infrastructure
  5. Cost per call/message: tying infrastructure cost to business metrics
- **Description:** Covers cost management — increasingly important as telecom platforms move to cloud. NOC engineers with cost awareness help organizations optimize spending. Monitoring resource utilization reveals right-sizing opportunities (an instance using 10% CPU should be downsized). Correlating infrastructure costs with business metrics (cost per call, cost per message) enables informed capacity decisions. Understanding cloud billing prevents surprise invoices.

#### Lesson 180: Course Capstone — Building Your NOC Engineering Practice
- **Module:** 6 — Soft Skills & Career
- **Section:** 6.3 — Advanced Operations
- **Estimated Read Time:** 10 minutes
- **Prerequisites:** All previous lessons
- **Key Concepts:**
  1. Continuous learning: staying current with evolving technology
  2. Building your toolkit: personal scripts, templates, checklists
  3. Contributing to team improvement: proposing and implementing process changes
  4. Industry engagement: conferences, communities, open source
  5. The NOC mindset: curiosity, calm under pressure, systematic thinking
- **Description:** The capstone lesson ties together everything covered in the course. Great NOC engineers combine deep technical knowledge with systematic problem-solving, clear communication, and continuous improvement. Build your personal toolkit of scripts and runbooks. Contribute to team knowledge bases. Stay curious — investigate why things work, not just how to fix them when they break. The best NOC engineers are the ones who make the NOC progressively better every day through small, consistent improvements.

---

## Appendix A — Quick Reference Tables

### SIP Response Codes

| Code | Meaning | NOC Action |
|------|---------|------------|
| 100 | Trying | Normal — request is being processed |
| 180 | Ringing | Normal — endpoint is ringing |
| 200 | OK | Success |
| 401 | Unauthorized | Check credentials/authentication |
| 403 | Forbidden | Check ACLs/authorization |
| 404 | Not Found | Check routing/number translation |
| 408 | Request Timeout | Check network connectivity/endpoint health |
| 480 | Temporarily Unavailable | Endpoint offline or busy |
| 486 | Busy Here | Endpoint is busy |
| 487 | Request Terminated | Call cancelled by caller |
| 500 | Server Internal Error | Check server logs |
| 502 | Bad Gateway | Upstream server error |
| 503 | Service Unavailable | Server overloaded or in maintenance |

### Common Port Numbers

| Port | Protocol | Service |
|------|----------|---------|
| 5060 | UDP/TCP | SIP |
| 5061 | TLS | SIPS |
| 10000-20000 | UDP | RTP (media) |
| 8080/8443 | TCP | HTTP/HTTPS APIs |
| 5432 | TCP | PostgreSQL |
| 8123 | TCP | ClickHouse HTTP |
| 9000 | TCP | ClickHouse native |
| 8500 | TCP | Consul HTTP |
| 9090 | TCP | Prometheus |
| 3000 | TCP | Grafana |
| 5672 | TCP | RabbitMQ AMQP |
| 9092 | TCP | Kafka |

### Key Metrics Cheat Sheet

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| ASR (Answer Seizure Ratio) | >45% | 30-45% | <30% |
| NER (Network Effectiveness Ratio) | >98% | 95-98% | <95% |
| ACD (Average Call Duration) | Stable | ±20% deviation | ±50% deviation |
| CPU Usage | <70% | 70-85% | >85% |
| Memory Usage | <80% | 80-90% | >90% |
| Disk Usage | <75% | 75-90% | >90% |
| CPS (Calls Per Second) | <80% capacity | 80-90% | >90% |

---

## Appendix B — Recommended Tools

| Category | Tool | Purpose |
|----------|------|---------|
| Monitoring | Grafana | Dashboards and visualization |
| Monitoring | Prometheus | Metrics collection and alerting |
| Monitoring | Loki | Log aggregation |
| Networking | tcpdump | Packet capture |
| Networking | Wireshark | Packet analysis |
| Networking | sngrep | SIP traffic visualization |
| SIP | Homer | SIP capture and analysis |
| SIP | Odin | SIP testing and monitoring |
| Databases | PostgreSQL | Relational data storage |
| Databases | ClickHouse | Analytics and time-series |
| Automation | Ansible | Configuration management |
| Automation | Terraform | Infrastructure provisioning |
| Incident | PagerDuty | Alert routing and escalation |
| Incident | Slack/Teams | Communication and ChatOps |
| Service Mesh | Consul | Service discovery and configuration |

---

*End of NOC Mastery Course Curriculum — 180 Lessons across 6 Modules*
*Estimated total reading time: ~22 hours*
*Designed for progressive learning from fundamentals to advanced operations*
