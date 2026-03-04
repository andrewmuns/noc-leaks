# Lesson 102: eSIM and OTA Management

**Module 2 | Section 2.14 — IoT/Wireless**
**⏱ ~6min read | Prerequisites: Lesson 191 (IoT SIM Cards)**

---

## Introduction

eSIM (embedded SIM) eliminates the physical SIM card. Instead, device firmware contains a programmable chip called an **eUICC** that can download profiles over-the-air. For IoT at scale — imagine thousands of devices deployed remotely — eSIM enables carrier switching and lifecycle management without physical access. This lesson covers the Remote SIM Provisioning (RSP) architecture.

---

## eSIM Architecture (eUICC)

### Physical vs eSIM

```
Traditional SIM                    eSIM (eUICC)
┌─────────────┐                   ┌─────────────┐
│   Plastic   │                   │   Soldered  │
│   Card      │   vs              │   to PCB    │
│             │                   │             │
│  Static     │                   │  Multiple   │
│  Profile    │                   │  Profiles   │
└─────────────┘                   └─────────────┘
                                      │
                              ┌───────┴───────┐
                              │  eSIM applet  │
                              │  processes    │
                              │  OTA commands │
                              └───────────────┘
```

### eUICC Components

```
ISD-R (Issuer Security Domain - Root):
  - Trusted anchor for the eSIM
  - Cannot be deleted
  - Creates ISD-P containers for each profile

ISD-P (Issuer Security Domain - Profile):
  - Container for each carrier profile
  - Contains: IMSI, Ki, APN, operator credentials
  - Can be enabled/disabled
  - Encrypted and signed by carrier

ECASD (eUICC Controlling Authority Security Domain):
  - Handles certificate verification
  - Verifies profile signatures

eSIM Operating System:
  - Manages profile switching
  - Handles SM-DP+/SM-DS communication
  - Secure storage
```

---

## Remote SIM Provisioning (RSP)

The GSMA RSP standard defines how profiles are remotely downloaded to eSIMs:

```
┌───────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│   Device  │     │    eUICC     │     │   SM-DP+   │     │    SM-DS     │
│ (with eSIM)│     │  in device   │     │  (Server)  │     │ (Discovery)  │
└─────┬─────┘     └──────┬───────┘     └─────┬──────┘     └──────┬───────┘
      │                  │                    │                    │
      │───────────────────────────────────────────────────────────→│
      │ 1. Register with SM-DS (push notification address)           │
      │                  │                    │                    │
      │←────────────────────────────────────────────────────────────│
      │ 2. Push notification: "Profile available"                    │
      │                  │                    │                    │
      │──────────────────→│                    │                    │
      │ 3. eUICC requests download                            │
      │                  │────────────────────→│                    │
      │                  │ 4. Mutual TLS authentication           │
      │                  │                    │                    │
      │                  │←───────────────────│                    │
      │                  │ 5. Encrypted profile bundle             │
      │                  │                    │                    │
      │                  │ (Profile installation)                  │
      │                  │                    │                    │
      │←─────────────────│                    │                    │
      │ 6. Profile active, network connected  │                    │
```

### Key RSP Entities

| Entity | Role |
|--------|------|
| **SM-DP+** | Subscription Manager - Data Preparation. Creates, encrypts, and delivers profiles. |
| **SM-DS** | Subscription Manager - Discovery Service. Stores "profile available" notifications for devices. |
| **eUICC** | The embedded chip that holds and manages profiles. |
| **LPD** | Local Profile Assistant. Software on device that communicates with SM-DP+. |

🔧 **NOC Tip:** When an eSIM customer says "profile download failed," check the SM-DP+ logs first. Common causes: (1) Device never registered with SM-DS, (2) ICCID doesn't match the profile, (3) Certificate expired or mismatched between SM-DP+ and eUICC.

---

## Profile Download Flow

### Detailed Steps

```
Step 1: Initiation
  Customer requests profile download via Telnyx API
  → System generates: ICCID, IMSI, Ki, APN config
  → Package signed with SM-DP+ certificate

Step 2: SM-DS Notification
  → SM-DP+ registers "profile ready" with SM-DS
  → SM-DS notifies device (push or polling)
  → Device's LPD connects to SM-DP+

Step 3: Authentication
  → Device presents EID (eUICC identifier)
  → eUICC and SM-DP+ perform mutual TLS
  → eUICC verifies SM-DP+ certificate chain

Step 4: Profile Transfer
  → SM-DP+ sends encrypted profile bundle
  → Decrypted by ISD-R, installed in new ISD-P
  → Profile locked to this eUICC (non-transferable)

Step 5: Enable
  → ISD-P created and populated
  → Profile state: DISABLED
  → Customer or device enables the profile
  → eUICC switches to active profile
  → Device registers with carrier network
```

---

## Managing eSIM Fleets at Scale

### Bulk Operations

```bash
# Provision 1000 eSIMs for deployment
curl -X POST https://api.telnyx.com/v2/wireless/esim/profiles/batch \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "quantity": 1000,
    "network_preferences": {
      "primary": "T-Mobile",
      "fallback": "AT&T"
    },
    "apn": "iot.telnyx.com",
    "status": "ready_to_download"
  }'

# Check bulk provisioning status
curl https://api.telnyx.com/v2/wireless/esim/profiles/batch/batch_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Profile States

```
AVAILABLE      → Profile created, not yet assigned
ALLOCATED      → Reserved for specific EID
DOWNLOADED     → Downloaded to eUICC
INSTALLED      → Installed in ISD-P
ENABLED        → Active profile
DISABLED       → Installed but not active
DELETED        → Removed from eUICC
```

### Carrier Switching

```
Scenario: Device moves to region with better Vodafone coverage

Current State:
  eUICC Profile 1: T-Mobile (active)
  eUICC Profile 2: Vodafone (disabled)

Switch Process:
  1. Customer requests profile switch via API
  2. Telnyx SM-DP+ sends "disable Profile 1, enable Profile 2"
  3. eUICC executes: Detach from T-Mobile
  4. eUICC executes: Attach to Vodafone
  5. Device now on Vodafone network

Total downtime: ~5-30 seconds (just network re-registration)
```

🔧 **NOC Tip:** eSIM profile switching is fast, but the device must support it properly. Some devices cache network information and need a restart after profile switch. If a customer reports "switch completed but still on old network," have them reboot the device or toggle airplane mode.

---

## OTA Updates

Over-the-Air (OTA) updates allow modifying active profiles without physical access:

```
OTA Update Types:

1. Profile Update (SM-DP+):
   - Change APN
   - Update authentication keys
   - Modify QoS parameters

2. eUICC Update (eUICC manufacturer):
   - OS/firmware updates
   - Security patches
   - Bug fixes

3. Policy Update:
   - Roaming rules
   - Band preferences
   - PRL (Preferred Roaming List)
```

### OTA Command Flow

```
┌─────────────┐                    ┌─────────────┐
│   Telnyx    │                    │    Device   │
│   OTA SMS   │──→ SMSC ──→ Tower →│  with eSIM  │
│   Platform  │                    │             │
└─────────────┘                    └──────┬──────┘
                                          │
                                    ┌─────▼─────┐
                                    │  eUICC    │
                                    │ reprograms│
                                    │  itself   │
                                    └───────────┘
```

---

## eSIM APIs for NOC Operations

```bash
# Get eSIM by EID
curl https://api.telnyx.com/v2/wireless/esim/eids/eid_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY"

# Check profile status
curl https://api.telnyx.com/v2/wireless/esim/profiles/iccid_abc123/status \
  -H "Authorization: Bearer YOUR_API_KEY"

# Switch active profile
curl -X POST https://api.telnyx.com/v2/wireless/esim/eids/eid_abc123/actions/switch_profile \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"profile_iccid": "iccid_new_network"}'

# Download status with error details
curl https://api.telnyx.com/v2/wireless/esim/profiles/iccid_abc123/download_status \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

## Real-World NOC Scenario

**Scenario:** Manufacturing customer has 10,000 devices with eSIMs shipping to 12 countries. Some devices in Europe can't download their profiles.

**Investigation:**

1. Check SM-DS registration — devices are registered ✓
2. Check SM-DP+ logs — download initiated but times out
3. Check device cellular connectivity — devices show "limited service"
4. Root cause: Devices shipped with NB-IoT-only firmware, but NB-IoT roaming is not enabled in destination countries
5. Solution: Push OTA update to enable LTE-M connectivity before profile download

```bash
# Identify affected devices
curl "https://api.telnyx.com/v2/wireless/esim/profiles?filter[download_status]=timed_out&filter[region]=EU" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Trigger connectivity mode update via OTA
curl -X POST https://api.telnyx.com/v2/wireless/esim/ota/update \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "target_devices": ["eid_1", "eid_2", ...],
    "update_type": "connectivity_mode",
    "value": "LTE-M"
  }'
```

---

## Key Takeaways

1. **eUICC is a reprogrammable SIM chip** — soldered to PCB, holds multiple profiles
2. **SM-DP+ creates and delivers profiles** — SM-DS handles discovery and notifications
3. **Profile download requires:** Device registration, matching ICCID, valid certificates
4. **Carrier switching is OTA** — no physical intervention, ~5-30 second downtime
5. **OTA updates can modify:** APN, authentication keys, firmware, roaming policies
6. **Profile states flow:** Available → Downloaded → Enabled → Active
7. **Debugging eSIM:** Start with SM-DS registration, then SM-DP+ connectivity, then profile installation

---

**Next: Lesson 193 — Mobile Voice: Cellular Voice for IoT**
