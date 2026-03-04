# Lesson 103: Mobile Voice — Cellular Voice for IoT

**Module 2 | Section 2.14 — IoT/Wireless**
**⏱ ~5min read | Prerequisites: Lesson 191 (IoT SIM Cards), Lesson 50 (SIP Call Flow)**

---

## Introduction

Not all IoT devices are data-only. Fleet vehicles, kiosks, security systems, and healthcare devices often need cellular voice capabilities — either for user interaction or emergency alerting. **Telnyx Mobile Voice** brings VoLTE (Voice over LTE) to IoT SIMs, enabling voice calls alongside data. This lesson covers how cellular voice works for connected devices.

---

## VoLTE Basics

### What Is VoLTE?

VoLTE (Voice over LTE) is voice carried as IP packets over the LTE data network, rather than the traditional circuit-switched (CS) voice network:

```
Circuit-Switched Voice (CSFB):
  Device on LTE → Falls back to 3G/2G → Circuit-switched voice call → Return to LTE
  
VoLTE:
  Device on LTE ─────────────────────→ IMS voice session → Stay on LTE
         │
         └─> Voice packets encapsulated in RTP over dedicated bearer
```

### VoLTE Architecture

```
┌───────────────┐
│   IoT Device  │
│  ┌─────────┐  │     LTE Radio      ┌───────────────┐
│  │   UE    │──┼───────────────────→│    eNodeB     │
│  └────┬────┘  │                    └───────┬───────┘
│       │       │                            │ S1-MME
│  ┌────▼────┐  │                    ┌───────▼───────┐
│  │   IMS   │  │                    │      MME      │
│  │  Stack  │  │                    └───────┬───────┘
│  └────┬────┘  │                            │
└───────┼───────┘                    ┌───────▼───────┐
        │                            │      IMS      │
        │                            │  Core Network │
        │                            │               │
        │    ┌──────────┐            │  ┌─────┐      │
        └───→│   P-CSCF │←───────────┼─→│ I-CSCF│     │
             │ (Proxy)  │            │  │ S-CSCF│     │
             └────┬─────┘            │  └──┬──┘      │
                  │                  │     │         │
             ┌────▼─────┐            │  ┌──▼──┐      │
             │   HSS    │            │  │ AS  │      │
             │(User DB) │            │  │(MMTel)│     │
             └──────────┘            └───┴─────┴──────┘
                                          │
                                     ┌────▼────┐
                                     │  MGW    │──→ PSTN/SIP
                                     │(Media)  │
                                     └─────────┘
```

### Key IMS Components

| Component | Full Name | Role |
|-----------|-----------|------|
| **P-CSCF** | Proxy-Call Session Control Function | First point of contact for device, routes SIP messages |
| **I-CSCF** | Interrogating-CSCF | Routes to correct S-CSCF, queries HSS |
| **S-CSCF** | Serving-CSCF | Handles SIP registration and call routing |
| **AS** | Application Server | Provides supplementary services (MMTel = Multimedia Telephony) |
| **MGW** | Media Gateway | Converts between RTP and TDM, bridges to PSTN |
| **HSS** | Home Subscriber Server | Stores subscriber profile, service data |

🔧 **NOC Tip:** For IoT voice issues, check if the device has completed **IMS registration** — not just LTE data attachment. A device can have data (PDP context active) but fail voice calls if IMS isn't registered. Look for "IMS Registration Status" in device diagnostics.

---

## Telnyx Mobile Voice Product

### How It Works

```
IoT Device with Telnyx SIM
    │
    ├─→ Data Path: Device → Telnyx Packet Gateway → Internet
    │
    └─→ Voice Path: Device → Telnyx IMS → Telnyx SIP/PSTN → Destination
                        │
                        └─→ Uses VoLTE bearer (QCI=1)
```

### Bearer Types for Voice

```
QCI (QoS Class Identifier):

QCI 1:  Voice bearer (VoLTE)
        Priority: 2
        Packet Delay Budget: 100ms
        Packet Error Loss Rate: 10^-2
        
QCI 5:  IMS signaling
        Priority: 1 (highest)
        Used for SIP registration and control
        
QCI 9:  Default data (best effort)
        Priority: 9 (lowest)
        Regular internet traffic
```

### SIP over IMS

```
IMS Registration:
  REGISTER sip:ims.telnyx.com SIP/2.0
  Via: SIP/2.0/UDP [device-ip]:5060
  From: <sip:+15551234567@ims.telnyx.com>
  To: <sip:+15551234567@ims.telnyx.com>
  Contact: <sip:[device-ip]:5060>
  Authorization: Digest username="+15551234567", ...

Voice Call Setup:
  INVITE sip:+15559876543@ims.telnyx.com SIP/2.0
  From: <sip:+15551234567@ims.telnyx.com>
  To: <sip:+15559876543@ims.telnyx.com>
  SDP: media description with RTP port and codec
```

---

## IoT Voice Use Cases

### Fleet Vehicles

```
Use Case: Truck driver emergency assistance

Device: Telnyx Mobile Voice enabled tablet in cab

Scenario: Driver presses panic button
  → Device initiates VoLTE call to dispatch center
  → Call includes GPS coordinates via SIP INFO
  → Disptacher receives call with location data
  → Two-way voice established within 2-3 seconds
  
Requirements:
  ✓ Always-on LTE-M (not NB-IoT — needs VoLTE)
  ✓ E911 capability
  ✓ Priority bearer setup (QCI=1)
```

### Connected Kiosks

```
Use Case: ATM/retail kiosk voice assistance

Device: ATM with touchscreen and handset

Scenario: Customer needs help
  → Press "Call Support" button
  → VoLTE call to call center
  → Kiosk passes account number and location
  → Support agent sees caller info on screen

Requirements:
  ✓ Hands-free or handset integration
  ✓ SIP headers for metadata (location, device ID)
  ✓ Call recording (PCI compliance considerations)
```

### Security Systems

```
Use Case: Alarm panel two-way voice

Device: Security panel with built-in speaker/mic

Scenario: Alarm triggered
  → Central monitoring calls panel
  → VoLTE call established to panel
  → Operator speaks through panel speaker
  → Homeowner responds via panel microphone

Requirements:
  ✓ Reliable VoLTE (not VoIP over WiFi)
  ✓ Battery backup for power outages
  ✓ E911 when alarm activated
```

---

## E911 for IoT

### Challenge

IoT devices are mobile — the "address" for emergency services changes:

```
Traditional Phone:
  Static address → Emergency routing is deterministic
  
IoT Device:
  Moves constantly → Needs "Dynamic E911"
  
Solution: GPS coordinates + registered address fallback
```

### Telnyx Dynamic E911

```
Call Flow:
  Device initiates emergency call
    │
    └─→ IMS routes to Telnyx E911 SBC
          │
          ├─→ For standard devices: route to PSAP based on registered address
          │
          └─→ For GPS-capable devices:
                Device sends GPS via SIP INFO or X-Header
                Telnyx queries geolocation service
                Routes to nearest PSAP with coordinates
```

### API for Location Updates

```bash
# Update device location for E911
curl -X PATCH https://api.telnyx.com/v2/wireless/devices/device_abc123/location \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "accuracy_meters": 10,
    "timestamp": "2026-02-23T10:00:00Z",
    "source": "gps"
  }'
```

🔧 **NOC Tip:** E911 calls from IoT devices must include location data. If a customer reports "911 calls going to wrong city," check their location update mechanism. Static E911 addresses are not sufficient for mobile IoT — implement periodic GPS updates via the location API.

---

## Monitoring Cellular Call Quality

### Metrics to Track

```
Network-level:
  - RSRP (Reference Signal Received Power): -100 dBm = weak, -80 = good
  - RSRQ (Reference Signal Received Quality): -15 dB = weak, -5 = good
  - SINR (Signal-to-Interference Ratio): 0 dB = poor, 20+ = excellent
  
Voice quality:
  - MOS (Mean Opinion Score): 1-5, 4.0+ = good VoLTE
  - Jitter: < 30ms acceptable
  - Packet loss: < 1% for tolerable voice
  - Latency: < 150ms for good experience
```

### Diagnostics via Telnyx

```bash
# Get device connectivity metrics
curl https://api.telnyx.com/v2/wireless/devices/device_abc123/diagnostics \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```json
{
  "data": {
    "device_id": "device_abc123",
    "signal_strength": {
      "rsrp": -85,
      "rsrq": -8,
      "sinr": 15
    },
    "network": {
      "technology": "LTE",
      "band": "B2",
      "carrier": "T-Mobile",
      "mcc_mnc": "310260"
    },
    "voice": {
      "ims_registered": true,
      "voip_enabled": true,
      "voice_bearer_active": false,
      "last_mos_score": 4.2
    }
  }
}
```

🔧 **NOC Tip:** If you see `ims_registered: true` but `voice_bearer_active: false` during a call attempt, the device failed to establish the dedicated voice bearer (QCI=1). This is often a carrier feature provisioning issue — the SIM may not have voice enabled on the carrier side. Verify voice provisioning with the carrier team.

---

## Real-World NOC Scenario

**Scenario:** Fleet customer reports "call audio is garbled" when vehicles drive through a specific highway corridor.

**Investigation:**

1. Check signal strength data from affected vehicles
2. RSRP drops to -110 dBm in the corridor (very weak)
3. But data still works because applications retry
4. Voice requires real-time delivery — weak signal = jitter and packet loss
5. Check carrier coverage map — shows "fair" coverage
6. **Recommendation:** Customer should implement lower bitrate codecs (AMR-NB instead of AMR-WB) or use VoWiFi (Voice over WiFi) as fallback in weak coverage areas

```
Codec Comparison:

AMR-NB (Narrowband): 4.75-12.2 kbps, works at -110 dBm
AMR-WB (Wideband):   6.60-23.85 kbps, needs -90 dBm or better

Switching to AMR-NB improves robustness in weak signal areas.
```

---

## Key Takeaways

1. **VoLTE is voice as IP packets over LTE** — IMS handles signaling, dedicated bearer (QCI=1) handles media
2. **IMS registration is separate from data attachment** — device can have internet but fail voice calls
3. **IoT voice requires LTE-M, not NB-IoT** — NB-IoT doesn't support VoLTE
4. **E911 is challenging for mobile IoT** — implement dynamic location updates via GPS
5. **Monitor MCS (MOS), jitter, and packet loss** for voice quality assessment
6. **Weak signal = degraded voice** — consider codec selection for challenging coverage areas
7. **IMS registration status is your first debug step** for "can't make calls on cellular"

---

**Next: Lesson 194 — Programmable Networking: Private Networks and Cloud VPN**
