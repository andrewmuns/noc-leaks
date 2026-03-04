# Lesson 101: IoT SIM Cards and Cellular Connectivity

**Module 2 | Section 2.14 — IoT/Wireless**
**⏱ ~7min read | Prerequisites: Lesson 140 (Wireless Fundamentals)**

---

## Introduction

IoT SIM cards are fundamentally different from consumer phone SIMs. They're designed for machine-to-machine (M2M) communication, with features like roaming optimization, remote management, and support for LPWAN technologies. This lesson covers the architecture of IoT SIMs and how Telnyx manages cellular connectivity for connected devices.

---

## SIM Architecture

A SIM (Subscriber Identity Module) is more than just a memory chip — it's a microcomputer with secure storage and cryptographic processing.

### Key Identifiers on a SIM

| Identifier | Name | Purpose | Length |
|------------|------|---------|--------|
| **IMSI** | International Mobile Subscriber Identity | Unique subscriber ID in the carrier network | 15 digits |
| **ICCID** | Integrated Circuit Card Identifier | Physical SIM serial number (printed on card) | 19-20 digits |
| **Ki** | Authentication Key | Secret key for network authentication | 128-bit |
| **OPc** | Operator Code | Network-specific ciphering key | Derived from OP and Ki |
| **MSISDN** | Mobile Station ISDN Number | The phone number assigned | Variable |

### IMSI Structure

```
IMSI: 310260123456789
      │││││
      ││││└─ MNC (Mobile Network Code) - AT&T = 410, T-Mobile = 260
      │││└── MCC (Mobile Country Code) - USA = 310
      ││└─── PLMN identifies the carrier
      │└──── MSIN (Mobile Subscriber Identification Number) - unique per carrier
      └───── Full IMSI uniquely identifies subscriber globally
```

🔧 **NOC Tip:** When debugging IoT connectivity issues, always start with the ICCID. It's the physical identifier printed on the SIM. The IMSI can change if the SIM is reprovisioned or if the carrier updates their database, but the ICCID never changes.

---

## SIM Operating Modes

IoT SIMs can operate in different network priority modes:

```
Single IMSI (Home Network):
  ┌─────────────┐
  │    SIM      │──→ Always connects to configured home network
  └─────────────┘         (e.g., always T-Mobile)

Multi-IMSI (Steering):
  ┌─────────────┐
  │    SIM      │──→ Can switch IMSI based on location/availability
  └─────────────┘         (e.g., T-Mobile in US, Vodafone in EU)

Roaming (Visited Network):
  ┌─────────────┐
  │    SIM      │──→ Home network unavailable
  └─────────────┘         ├─→ Roam to partner network
                          (e.g., AT&T device roaming on T-Mobile)
```

The IMSI determines which carrier's network the device attempts to register with upon power-up.

---

## APN Configuration

The **Access Point Name (APN)** tells the device which gateway to use for data services:

```
Device connects to cell tower
    │
    ▼
Attach Request (includes APN)
    │
    ▼
PGW (Packet Gateway) determines:
  - IP address assignment
  - Routing policy
  - QoS settings
  - Bandwidth limits
```

### Telnyx IoT APNs

| APN | Use Case |
|-----|----------|
| `iot.telnyx.com` | Standard IoT data |
| `m2m.telnyx.com` | Machine-to-machine specific |
| `private.telnyx.com` | Private network routing |

### PDP Context Establishment

```
Device → MME → SGW → PGW

1. Attach Request: IMSI + requested APN
2. Authentication: HSS validates IMSI/Ki
3. Create Session Request: APN → PGW selection
4. IP Address Assignment: PGW allocates IP
5. Bearer Setup: QoS negotiated, data path established
6. Data Enabled: Device can now send/receive packets
```

🔧 **NOC Tip:** "Device shows signal but no data" is usually an APN issue. Check if the device has the correct APN configured. Telnyx IoT SIMs default to `iot.telnyx.com` but some devices cache previous APNs or ship with carrier-specific defaults.

---

## Data Sessions (PDP Context)

A **PDP (Packet Data Protocol) Context** is the logical connection between the device and the packet gateway:

```
┌─────────────┐     LTE/5G      ┌─────────────┐     S1-U     ┌─────────────┐
│    Device   │◄───────────────→│    eNodeB   │◄───────────→│     SGW     │
│ (UE)        │                 │  (Tower)    │              │             │
└─────────────┘                 └─────────────┘              └──────┬──────┘
      │                                                              │
      │ PDP Context:                                                 │
      │   - IP: 100.64.x.x                                           │
      │   - QoS: QCI=9 (default)                                     │
      │   - Bearer: Default                                          │
      │                                                              │
      │                  S5/S8 Interface                             │
      │◄─────────────────────────────────────────────────────────────┘
                                                              │
                                                         ┌────▼────┐
                                                         │   PGW   │
                                                         │ (Exit)  │
                                                         └────┬────┘
                                                              │
                                                         Internet/Private
```

### PDP Context Types

```
IPv4 Context:
  IP: 100.64.12.34 (CGNAT range)
  NAT at PGW before public internet

IPv6 Context:
  IP: 2607:fb90::/40
  Public routable (no NAT)

Dual Stack (IPv4v6):
  Both addresses assigned
  Most modern devices prefer IPv6
```

---

## IoT-Specific Protocols

### NB-IoT (Narrowband IoT)

```
Characteristics:
  - Bandwidth: 200 kHz (vs 20 MHz for LTE)
  - Peak rate: ~250 kbps
  - Range: 20+ km, deep indoor penetration
  - Battery life: 10+ years
  - Device cost: <$5 per module

Use cases: Smart meters, sensors, asset tracking, smart agriculture
```

### LTE-M (LTE Cat-M1)

```
Characteristics:
  - Bandwidth: 1.4 MHz
  - Peak rate: 1 Mbps uplink / 1 Mbps downlink
  - Voice support: Yes (VoLTE)
  - Mobility: Good (handover supported)
  - Latency: ~50-100ms

Use cases: Wearables, vehicle tracking, healthcare devices, retail POS
```

### Comparison

| Feature | NB-IoT | LTE-M | Standard LTE |
|---------|--------|-------|--------------|
| Bandwidth | 200 kHz | 1.4 MHz | 20 MHz |
| Data rate | 250 kbps | 1 Mbps | 100+ Mbps |
| Mobility | Stationary | Mobile | Full mobility |
| Voice | No | Yes (VoLTE) | Yes |
| Latency | Seconds | ~100ms | ~10ms |
| Battery | 10+ years | 5-10 years | 1-2 days (active use) |
| Coverage | Excellent | Very good | Good |

🔧 **NOC Tip:** If an IoT customer reports "device can't connect," check which radio technology they're trying to use. Many devices ship with NB-IoT disabled or locked to specific bands. For mobile use cases (vehicles), LTE-M is required — NB-IoT doesn't support handover between towers.

---

## Telnyx IoT SIM Management

### SIM States and Lifecycle

```
┌──────────┐
│  Ordered │──→ SIM requested, not yet shipped
└────┬─────┘
     │
┌────▼─────┐
│ Delivered│──→ SIM shipped to customer
└────┬─────┘
     │
┌────▼─────┐
│ Inactive │──→ SIM received, ready to activate
└────┬─────┘
     │
┌────▼─────┐     ┌──────────┐
│  Active  │←───→│Suspended │──→ Temporary pause (billing continues)
└────┬─────┘     └──────────┘
     │
┌────▼─────┐     ┌──────────┐
│ Terminated│←───→│  Test    │──→ Decommissioned
└──────────┘     └──────────┘
```

### API Commands

```bash
# List all IoT SIMs
curl https://api.telnyx.com/v2/wireless/sim_cards \
  -H "Authorization: Bearer YOUR_API_KEY"

# Activate a SIM
curl -X POST https://api.telnyx.com/v2/wireless/sim_cards/iccid_abc123/actions/activate \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check data usage
curl https://api.telnyx.com/v2/wireless/sim_cards/iccid_abc123/data_usage \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Roaming Architecture

```
Home Network (USA - T-Mobile)     Visited Network (UK - Vodafone)
┌─────────────────────┐           ┌─────────────────────┐
│    HPLMN            │           │    VPLMN            │
│                     │           │                     │
│  HSS ──── Diameter ─┼──────────→│  MME (roaming)      │
│  (subscriber data)  │  S6a/S6d  │                     │
│                     │           │                     │
│  PGW ←──────────────┼───────────│  SGW                │
│  (IP anchor)        │   S5/S8   │  (local anchor)     │
└─────────────────────┘           └─────────────────────┘
        │                                   │
        │         Device attaches           │
        │         through Vodafone          │
        │         (roaming)                 │
        │                                   │
        └──→ All data routed back to        │
            T-Mobile PGW (home routed)      │
```

🔧 **NOC Tip:** Roaming issues often manifest as "connected but no internet." The device attaches to the visited network successfully, but the S8 interface back to the home PGW may be down. Check if other devices on the same network are affected — if yes, it's likely a roaming agreement or datapath issue, not the SIM.

---

## Real-World NOC Scenario

**Scenario:** Fleet tracking customer reports 200 vehicles suddenly show "no data connection" in a specific city.

**Investigation:**

1. Check device connectivity status via API
2. SIMs show "attached" at network level but 0 data usage
3. Check the tower map — all affected devices connected to the same eNodeB
4. eNodeB primary SCTP connection to MME is flapping
5. Devices stay attached but data bearers aren't established
6. **Escalate** to carrier operations and work around by triggering devices to force reattach (power cycle command via SMS)

```bash
# Identify affected devices by location
# Check recent session establishment failures
# Coordinates within bounding box of affected city
```

---

## Key Takeaways

1. **SIM identifiers matter:** ICCID is physical, IMSI is logical, Ki is the authentication secret
2. **APN determines data path:** Wrong APN = device attaches but has no data
3. **PDP Context is the data session:** No context = no IP address = no connectivity
4. **NB-IoT vs LTE-M:** NB-IoT is for stationary sensors, LTE-M for mobile devices requiring voice/handover
5. **SIM lifecycle:** Ordered → Delivered → Inactive → Active → Terminated
6. **Roaming depends on home PGW:** Even when roaming, traffic often routes back to the home network
7. **IoT debugging:** Check attach → authenticate → PDP context → data in that order

---

**Next: Lesson 192 — eSIM and OTA Management**
