# Lesson 104: Programmable Networking — Private Networks and Cloud VPN

**Module 2 | Section 2.15 — Networking**
**⏱ ~7min read | Prerequisites: Lesson 100 (VPN Fundamentals), Lesson 110 (Cloud Connectivity)**

---

## Introduction

Public internet routing is fine for general traffic, but for latency-sensitive voice, video conferencing, and enterprise workloads, **private networking** provides deterministic, secure paths. Telnyx Programmable Networking offers WireGuard-based Cloud VPN and private IP connectivity between customer sites, clouds, and the Telnyx global network. This lesson covers the architecture and NOC operations for these network tunnels.

---

## Telnyx Private IP Network

### Global Backbone

```
┌──────────────────────────────────────────────────────────────┐
│                    Telnyx Global Network                      │
│                    (Private IP Backbone)                      │
│                                                               │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐           │
│   │  PoP     │──────→│  PoP     │──────→│  PoP     │           │
│   │ Chicago  │      │ London   │      │ Singapore│           │
│   └────┬─────┘      └────┬─────┘      └────┬─────┘           │
│        │                 │                 │                  │
│        │    ═══════════════════════════   │                  │
│        │         Private MPLS/VXLAN        │                  │
│        │    ═══════════════════════════   │                  │
│   ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐           │
│   │  PoP     │──────→│  PoP     │──────→│  PoP     │           │
│   │ New York │      │ Amsterdam│      │ Hong Kong│           │
│   └──────────┘      └──────────┘      └──────────┘           │
└──────────────────────────────────────────────────────────────┘

Your traffic never touches the public internet between Telnyx PoPs.
```

### Benefits

```
Latency:        20-40% lower than public internet (predictable paths)
Jitter:         < 5ms consistent (vs 20-50ms on internet)
Security:       MPLS/VXLAN isolated from internet
Reliability:    Redundant paths, SLA-backed
One-hop:        Customer → Telnyx → Destination (not Customer → ISP → Tier-1 → Tier-1 → Destination)
```

🔧 **NOC Tip:** When a customer complains about "choppy voice" or "jitter on video calls," checking the path is essential. If traffic is routed over the public internet, any congestion between the ISP and transit providers can cause problems. Telnyx private network offers consistent quality — recommend Cloud VPN as a fix for quality issues.

---

## Cloud VPN — WireGuard Tunnels

### What Is WireGuard?

WireGuard is a modern VPN protocol:

```
Advantages over IPsec/OpenVPN:
  - Simpler codebase (~4,000 lines vs 400,000+ lines)
  - Better performance (kernel-level implementation)
  - Faster handshakes (curve25519 crypto)
  - Roaming support (seamlessly handles IP changes)
  - Built into Linux kernel (5.6+)
  
Crypto:   Curve25519 for key exchange, ChaCha20 for encryption
Ports:    UDP by default (can work through NATs)
State:    Connectionless (no "tunnel up/down" state to manage)
```

### Telnyx Cloud VPN Architecture

```
                    ┌─────────────────────┐
                    │   Telnyx Cloud      │
                    │   VPN Gateway       │
                    │   (Anycast IPs)     │
                    └─────────┬───────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
    │ Customer  │       │  AWS VPC  │       │  GCP      │
    │ Office    │       │  (us-east)│       │  (europe) │
    │           │       │           │       │           │
    │ ┌───────┐ │       │ ┌───────┐ │       │ ┌───────┐ │
    │ │WG Peer│ │       │ │WG Peer│ │       │ │WG Peer│ │
    │ │Client │ │       │ │Client │ │       │ │Client │ │
    │ └───┬───┘ │       │ └───┬───┘ │       │ └───┬───┘ │
    └─────┼─────┘       └─────┼─────┘       └─────┼─────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                    WireGuard Tunnels
                    (Encrypted, private)
```

---

## Creating a Cloud VPN Connection

### Via API

```bash
# Create a VPN connection
curl -X POST https://api.telnyx.com/v2/vpn_connections \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "Office-to-Telnyx",
    "type": "wireguard",
    "local_networks": ["192.168.1.0/24"],
    "remote_asn": 64512,
    "enable_internet_access": false
  }'
```

### Response with WireGuard Config

```json
{
  "data": {
    "id": "vpn_abc123",
    "name": "Office-to-Telnyx",
    "interface_address": "10.200.0.2/32",
    "peer_public_key": "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890=",
    "peer_allowed_ips": ["0.0.0.0/0"],
    "peer_endpoint": "198.51.100.1:51820",
    "persistent_keepalive": 25,
    "local_networks": ["192.168.1.0/24"]
  }
}
```

### WireGuard Config File

```bash
# /etc/wireguard/telnyx.conf
[Interface]
PrivateKey = <your-generated-private-key>
Address = 10.200.0.2/32
ListenPort = 51820

[Peer]
PublicKey = AbCdEfGhIjKlMnOpQrStUvWxYz1234567890=
AllowedIPs = 0.0.0.0/0
Endpoint = 198.51.100.1:51820
PersistentKeepalive = 25
```

---

## Global Edge Router

The **Global Edge Router** is Telnyx's anycast service that routes traffic to the nearest PoP:

```
Customer in:
  San Francisco → Routes to San Jose PoP (latency: 5ms)
  New York      → Routes to Newark PoP (latency: 3ms)
  London        → Routes to London PoP (latency: 2ms)
  Tokyo         → Routes to Tokyo PoP (latency: 5ms)
  Sydney        → Routes to Sydney PoP (latency: 8ms)

Same endpoint IP everywhere (anycast), 
different physical servers (PoPs).
```

### Latency-Optimized Routing

```
Without optimization (public internet):
  NYC Customer → ISP → Cogent → L3 → AWS us-east
  Latency: 25-40ms variable

With Telnyx Cloud VPN:
  NYC Customer → WireGuard → Telnyx NYC PoP → AWS Direct Connect
  Latency: 5-8ms consistent
```

🔧 **NOC Tip:** For customers using AWS, GCP, or Azure, the Telnyx Cloud VPN + Cloud Router combination provides direct private connectivity. This bypasses internet transit completely. Always ask: "Are you running voice/video between cloud and office?" If yes, recommend Cloud VPN — it'll solve jitter and packet loss issues.

---

## SD-WAN Concepts

### What Is SD-WAN?

Software-Defined WAN intelligently routes traffic across multiple paths:

```
Enterprise Site with SD-WAN:

┌─────────────────────────────────────────┐
│              SD-WAN Appliance           │
│                                         │
│  ┌──────────┐      ┌──────────┐         │
│  │Internet  │      │ MPLS     │         │
│  │Link 1    │      │ Link     │         │
│  │(100 Mbps)│      │          │         │
│  └────┬─────┘      └────┬─────┘         │
│       │                 │               │
│  ┌────▼─────────────────▼────┐          │
│  │   SD-WAN Controller       │          │
│  │   - Monitors both paths   │          │
│  │   - Routes per app/policy │          │
│  │   - Failover on failure   │          │
│  └───────────┬───────────────┘          │
│              │                          │
│         To internal network              │
└─────────────────────────────────────────┘

Policies:
  Voice traffic  → MPLS path (low latency, reliable)
  Email traffic  → Internet link (cheaper, higher bandwidth)
  Cloud backup   → Internet link (bursty, not latency-sensitive)
  Real failover  → If MPLS fails, voice fails over to internet
```

### Telnyx SD-WAN Integration

```
Telnyx Cloud VPN can act as an SD-WAN overlay:

Site A (NYC) ────────┐
                     │ WireGuard
Site B (London) ─────┼────→ Telnyx Backbone ─────→ Cloud/Internet
                     │         (MPLS-like)
Site C (Remote) ──────┘

Appliances or software agents at each site create a mesh of tunnels.
Telnyx backbone provides the reliable middle mile.
Non-Telnyx internet provides the last mile.
```

---

## NOC Monitoring of Network Tunnels

### Metrics to Track

```
WireGuard Tunnel Health:
  ├─ handshake: last time successful
  ├─ transfer: bytes sent/received
  ├─ errors: packet loss over tunnel
  └─ latency: RTT to tunnel endpoint

Path Quality:
  ├─ loss: < 0.1% good, > 1% problematic
  ├─ jitter: < 5ms good, > 20ms poor
  ├─ latency: baseline vs current
  └─ available bandwidth
```

### API Commands

```bash
# Get VPN connection status
curl https://api.telnyx.com/v2/vpn_connections/vpn_abc123/status \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```json
{
  "data": {
    "id": "vpn_abc123",
    "status": "established",
    "stats": {
      "peer_handshake": "2026-02-23T10:05:30Z",
      "transfer_rx": 1024000,
      "transfer_tx": 512000,
      "latency_ms": 12,
      "packet_loss": 0.01
    },
    "uptime": "5d 3h 24m"
  }
}
```

🔧 **NOC Tip:** WireGuard's `PersistentKeepalive` setting is crucial for NAT traversal. Without keepalives, NAT mappings expire (typically 30-300 seconds) and the tunnel appears "dead." Telnyx defaults to 25 seconds, which handles most corporate firewalls. If you see tunnels randomly dropping, check if the customer is behind aggressive NAT with short timeouts.

---

## Real-World NOC Scenario

**Scenario:** Customer reports "tunnel is up but only some traffic flows" — they can ping the Telnyx gateway but can't reach their cloud VMs.

**Investigation:**

1. Check `AllowedIPs` in the WireGuard config
2. Customer has: `AllowedIPs = 10.200.0.1/32` (only the tunnel endpoint)
3. Should be: `AllowedIPs = 10.200.0.0/16, 172.31.0.0/16` (includes cloud network)
4. The tunnel only allows traffic to the specific /32, not the broader networks
5. **Fix:** Update AllowedIPs to include all target networks

```bash
# Check routing on customer side
ip route show table main | grep wireguard

# Update WireGuard config
[Peer]
AllowedIPs = 10.200.0.0/16, 172.31.0.0/16  # Include cloud VPC
```

---

## Key Takeaways

1. **Telnyx private backbone avoids internet unpredictability** — lower latency, less jitter
2. **WireGuard is the modern VPN** — fast, simple, built into Linux kernel
3. **Cloud VPN gives you private connectivity to clouds** — like AWS Direct Connect but simpler
4. **Global Edge Router uses anycast** — worldwide endpoints, connect to nearest PoP automatically
5. **SD-WAN leverages multiple paths** — intelligent routing for cost and quality optimization
6. **PersistentKeepalive** prevents NAT timeout issues — don't set it too high behind corporate firewalls
7. **AllowedIPs controls what routes through the tunnel** — common source of "partial connectivity"

---

**Next: Lesson 195 — Telnyx Compute: Inference, LLM Library, and Embeddings**
