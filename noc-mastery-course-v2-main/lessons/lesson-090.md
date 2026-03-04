# Lesson 90: Telnyx Networking — Cloud VPN and WireGuard
**Module 2 | Section 2.11 — Networking**
**⏱ ~7 min read | Prerequisites: Lesson 13, Lesson 17**

---

## Beyond Voice: Telnyx as a Network

Telnyx operates a global private backbone — a network of data centers connected by owned or leased fiber. Most customers use this backbone indirectly (their SIP traffic traverses it), but Telnyx's networking products let customers use this backbone directly. This turns Telnyx into a programmable network operator, not just a communications API provider.

## Why Private Connectivity Matters

When a customer connects their PBX to Telnyx over the public internet, the traffic traverses multiple networks (as we covered in Lessons 22-25 on BGP). Each network hop adds latency, and the path is unpredictable — routing changes, congestion, and outages on any intermediate network affect call quality.

**Private connectivity** eliminates this uncertainty:

- **Predictable latency** — Traffic stays on Telnyx's backbone, which is engineered for low latency
- **No NAT** — Private connections don't traverse NAT devices, eliminating the NAT traversal problems from Lessons 26-28
- **Security** — Traffic never touches the public internet, reducing exposure to eavesdropping and DDoS attacks
- **QoS** — Telnyx can apply QoS markings on its own network (unlike the public internet, where DSCP markings are stripped — Lesson 11)

## WireGuard: A Modern VPN Protocol

Telnyx chose **WireGuard** as the foundation for its VPN product. Understanding why requires comparing it to traditional VPN protocols:

### IPsec — The Enterprise Standard (and Its Problems)

IPsec has been the enterprise VPN standard for decades. It works, but it's complex:
- **IKE (Internet Key Exchange)** — Phase 1 negotiates security parameters, Phase 2 establishes the tunnel. Multiple message exchanges, multiple cipher suite negotiations.
- **Configuration complexity** — Pre-shared keys, certificate management, proposal sets, transform sets. Dozens of parameters that must match on both sides.
- **Code complexity** — IPsec implementations are massive codebases (hundreds of thousands of lines). More code = more bugs = more security vulnerabilities.
- **State management** — IPsec maintains complex state machines. Dead peer detection, rekeying, and SA (Security Association) lifecycle management add operational overhead.

### WireGuard — Simplicity as a Feature

WireGuard takes a radically different approach:

**~4,000 lines of code** vs. hundreds of thousands for IPsec. Less code means fewer bugs, easier auditing, and a smaller attack surface.

**Modern cryptography only** — WireGuard uses a fixed set of modern algorithms: Curve25519 for key exchange, ChaCha20 for encryption, Poly1305 for authentication, BLAKE2s for hashing. No cipher suite negotiation — everyone uses the same algorithms. If any of these algorithms are broken, a new version of WireGuard replaces them all.

**Connectionless design** — WireGuard doesn't have a connection establishment handshake like IPsec's IKE. It's built on UDP and uses a simple 1-RTT handshake when needed. There's no concept of a "tunnel being down" — WireGuard silently handles peer availability. If a peer is reachable, packets flow; if not, they don't. No complex state machine, no dead peer detection overhead.

**Cryptokey routing** — WireGuard associates each peer with a public key and a set of allowed IP ranges. Routing is based on the public key, not on IP addresses. This makes roaming seamless — if a peer's IP changes (e.g., a mobile device switching from WiFi to cellular), the tunnel continues working transparently.

🔧 **NOC Tip:** When troubleshooting WireGuard connectivity, the most common issues are: incorrect public keys (typos or regenerated keys not updated on both sides), incorrect Allowed IPs (determines which traffic enters the tunnel), and UDP port blocking (WireGuard uses a single UDP port, typically 51820, which must be open through firewalls).

## Cloud VPN: Site-to-Site and Point-to-Site

Telnyx's Cloud VPN product builds on WireGuard to offer two deployment models:

### Site-to-Site VPN

Connects a customer's network (office, data center) to Telnyx's network:

- The customer deploys a WireGuard endpoint (router, server, or appliance) at their site
- A WireGuard tunnel is established to the nearest Telnyx point of presence
- Traffic between the customer's network and Telnyx services flows through the encrypted tunnel
- Common use case: **private SIP trunking** — SIP/RTP traffic stays on the private tunnel, never touching the public internet

### Point-to-Site VPN

Connects individual devices to Telnyx's network:

- Each device (laptop, IoT device, softphone) has a WireGuard client
- Each device gets its own tunnel to Telnyx
- Common use case: **remote workers** with softphones needing private, reliable connectivity to Telnyx's voice infrastructure

### API-Driven Configuration

Unlike traditional VPN products that require manual configuration through a web UI, Telnyx's Cloud VPN is fully programmable:

```
POST /v2/network_interfaces
{
  "network_id": "net_12345",
  "type": "wireguard",
  "region": "us-east-1"
}
```

This API-driven model enables automation: spin up VPN connections programmatically, integrate with CI/CD pipelines, and manage large deployments at scale.

## Global Edge Router

The **Global Edge Router** is Telnyx's programmable routing layer. It sits at the edge of Telnyx's network and makes routing decisions for customer traffic:

- **Traffic steering** — Route traffic to specific Telnyx regions based on customer-defined rules
- **Private interconnection** — Connect customer networks to Telnyx's backbone at specific data centers
- **Multi-cloud connectivity** — Connect Telnyx's network to AWS, GCP, Azure via private interconnects

For NOC engineers, the Global Edge Router is relevant during routing incidents. If traffic to a specific customer is taking a suboptimal path, the Global Edge Router configuration may need adjustment.

## Use Cases That Matter for NOC

### Private SIP Trunking

The most relevant use case: a customer's PBX connects to Telnyx via WireGuard instead of the public internet. Benefits:
- Eliminates NAT traversal issues entirely (the tunnel provides a direct Layer 3 path)
- Provides consistent latency and quality
- Adds encryption without requiring SRTP (the tunnel encrypts everything)

When troubleshooting call quality for these customers, the tunnel itself becomes a diagnostic point. WireGuard's `wg show` command reveals handshake timestamps, bytes transferred, and endpoint addresses.

### Secure IoT Backhaul

IoT devices (Lesson 78-79) can backhaul data through WireGuard tunnels to Telnyx's network, then to the customer's infrastructure. This provides end-to-end encryption and keeps IoT traffic off the public internet.

### Multi-Cloud Networking

Customers running workloads across multiple cloud providers can use Telnyx's backbone as a transit network, connecting their AWS VPCs, GCP VPCs, and Azure VNets through Telnyx.

## Real-World Troubleshooting Scenario

**Scenario:** A customer using private SIP trunking over WireGuard reports intermittent call quality issues — calls are fine most of the time, but experience choppy audio 2-3 times per day.

**Investigation:**
1. **Check WireGuard tunnel health** — Look at handshake timestamps. If the latest handshake is stale (>5 minutes old), the tunnel may be disrupted.
2. **Check the customer's internet connection** — WireGuard runs over UDP on the public internet (to the nearest Telnyx POP). The tunnel is only as good as the underlying internet connection.
3. **Check MTU** — WireGuard adds overhead (60 bytes for IPv4 + WireGuard header). If the tunnel MTU isn't configured correctly, packets may be fragmented, causing audio issues (Lesson 13).
4. **Check traffic volume** — Is the tunnel being saturated? WireGuard can handle high throughput, but the customer's internet upload bandwidth is the bottleneck.
5. **Check for UDP port blocking** — Intermittent firewall rule changes or stateful firewall session timeouts could disrupt the WireGuard UDP flow.

**Resolution:** Set the tunnel MTU appropriately (typically 1420 for IPv4 WireGuard). Ensure the customer's internet connection has sufficient bandwidth. Configure keepalive packets to prevent stateful firewalls from timing out the UDP session.

---

**Key Takeaways:**
1. Private connectivity via WireGuard eliminates NAT traversal, provides predictable latency, and adds inherent encryption
2. WireGuard's simplicity (~4,000 lines of code, fixed modern cryptography, connectionless design) makes it more reliable and secure than IPsec
3. Cloud VPN supports both site-to-site (office-to-Telnyx) and point-to-site (device-to-Telnyx) configurations, all API-driven
4. Private SIP trunking over WireGuard eliminates the most common VoIP problems (NAT, firewall, QoS)
5. WireGuard tunnel troubleshooting focuses on: handshake freshness, MTU, UDP port accessibility, and underlying internet quality

**Next: Lesson 81 — Telnyx Storage — S3-Compatible Object Storage**
