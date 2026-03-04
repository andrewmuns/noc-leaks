# Lesson 100: Emergency Services — E911 Architecture and Obligations
**Module 2 | Section 2.13 — Business Systems**
**⏱ ~7min read | Prerequisites: None**
---

## Introduction

When someone dials 911, they're in crisis. Seconds matter. The system can't fail. Unlike other Telnyx services, E911 isn't measured by revenue or customer satisfaction — it's measured by whether people get help when they need it.

E911 (Enhanced 911) for VoIP is complex. Unlike traditional landlines where the phone is physically at the address, VoIP users can take their number anywhere. A Telnyx customer in Chicago could have a New York number and be calling from a hotel in Miami. Ensuring the right dispatch center receives the right location is a technical and regulatory challenge.

This lesson covers how E911 works for VoIP, Telnyx's implementation, and what happens when it fails.

---

## E911 Requirements for VoIP

### What Makes VoIP E911 Different

| Aspect | Traditional Landline | VoIP/Cloud Phone |
|--------|---------------------|------------------|
| Location | Fixed — the address of the phone | Dynamic — user could be anywhere |
| Routing | Hardwired to local PSAP | Routed via lookup tables |
| Callback | Always returns to calling line | Depends on network availability |
| ALI Database | Static—matches phone to address | Must be updated by user/company |
| Reliability | Power-fail safe at premises | Network and power dependent |

### Regulatory Requirements (Kari's Law, Ray Baum's Act)

The FCC mandates specific capabilities for VoIP operators:

**Kari's Law (2018):**
- No prefix required to reach 911 (no "dial 8 for outside line")
- Notification to front desk/hotel staff when 911 is called

**Ray Baum's Act (2021):**
- Dispatchable location — not just street address but room/floor number
- Applies to MLTS (Multi-Line Telephone Systems) and VoIP services

🔧 **NOC Tip:** Non-compliance with Kari's Law and Ray Baum's Act can result in **fines up to $10,000 per day** plus liability in wrongful death cases. If a customer reports they need "8+911" or 911 calls aren't reaching the right location, this is not a service ticket — it's a potential legal liability. Escalate to Safety and Legal teams immediately.

---

## The ALI Database

**ALI (Automatic Location Information)** is the database that maps phone numbers to physical addresses for emergency dispatch.

### ALI Data Flow

```
911 Call Originated
        │
        ▼
┌─────────────┐
│   Telnyx    │──► Determine originating number
│   Network   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ALI Query  │──► Lookup: Phone Number → Address + PSAP
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ALI Database│──► Returns: 123 Main St, Suite 400, Chicago, IL
│  (Regional) │                       Lat: 41.878, Lon: -87.629
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  PSAP Call  │──► Dispatch operator sees location on screen
│   Taker     │    Can dispatch appropriate emergency services
└─────────────┘
```

### ALI Record Components

```
ALI Record Example for +14155551234:
  
  TN (Telephone Number): 14155551234
  Customer: ACME Corp
  ALI Address: 123 South Wacker Dr
  Suite/Floor: Floor 15, Suite 1500
  City: Chicago
  State: IL
  ZIP: 60606
  Lat/Lon: 41.878113, -87.629799
  PSAP: Chicago PSAP Urban
  Type: Business
  Last Updated: 2026-02-15
```

---

## PSAP Routing

**PSAPs (Public Safety Answering Points)** are the 911 call centers that receive emergency calls.

### Routing Hierarchy

```
911 Call
   │
   ├──► In-Telnyx routing check ──► Is this a Telnyx-provided number?
   │   (Media Server/SBC)
   │
   ├──► YES → Route to Telnyx E911 service
   │           │
   │           ├──► ALI lookup (number → address)
   │           │
   │           └──► Route to appropriate PSAP based on location
   │               │
   │               ├──► PSAP is **selective router**
   │               │    Selective router queries ALI, pops location
   │               │
   │               └──► PSAP operator sees call with location info
   │
   └──► NO (non-Telnyx customer) → Reject or route to wrong PSAP
```

### Selective Routing

Not every PSAP covers an entire city. Chicago alone has 10+ PSAPs covering different zones. **Selective routing** uses the caller's location (from ALI) to pick the right PSAP:

- Police districts
- Fire response zones
- Hospital EMS service areas

```
Caller at 123 Main St, 60606:
  │
  ├──► ZIP 60606 → Chicago Downtown PSAP
  │
  └──► Specific location within downtown → Zone 3 Dispatcher
```

🔧 **NOC Tip:** A common E911 failure: **caller registered in Chicago dials from Miami**. The ALI shows the Chicago address, but they're physically in Miami. If they can't communicate their location, dispatch goes to the wrong city. Telnyx's E911 service must support **dynamic location updates** for mobile/softphone users. If a customer reports "911 went to the wrong city," check whether their device updated location or if it's using a static address.

---

## Telnyx E911 Implementation

### Architecture

```
Telnyx E911 Platform
         │
         ├──► E911 Provisioning API
         │    Create/modify E911 records
         │    Validate addresses and geocoding
         │
         ├──► Location Database (ALI)
         │    Sync with regional ALI providers
         │    (Network: Bandwidth, Intrado, West)
         │
         ├──► E911 Call Routing
         │    Media servers detect 911 dialed
         │    Route to appropriate selective router
         │
         ├──► Failover and Redundancy
         │    Multiple ALI providers
         │    PSAP routing protocols (CAMA, ISDN)
         │
         └──► Monitoring and Alerting
              E911 call success rate
              ALI sync lag
              PSAP connectivity status
```

### Address Validation

Before an E911 record is created, the address must be validated:

1. **Geocoding:** Convert address to lat/lon coordinates
2. **PSAP mapping:** Determine which PSAP serves this location
3. **ELIN validation:** Ensure Emergency Location Identification Number is assignable
4. **ALI write:** Push record to ALI database provider

```bash
# Example: E911 address validation API
curl -X POST https://api.telnyx.com/v2/e911_addresses \
  -H "Authorization: Bearer API_KEY" \
  -d '{"street_address": "123 Main St", "city": "Chicago", "state": "IL", "zip": "60606"}'

# Response:
{
  "validated": true,
  "formatted_address": "123 S Main St, Chicago, IL 60606",
  "latitude": 41.878,
  "longitude": -87.629,
  "psap_id": "CHI-DOWNTOWN-001",
  "status": "geocoded"
}
```

---

## Testing E911

E911 testing requires caution — you cannot actually call 911 to test.

### Test Methods

**1. Test PSAP Numbers**

Most PSAPs maintain a test line that simulates 911 without dispatch:
```
# Customer should dial: 933 (Telnyx test service)
# Or configured alternative test number
```

**2. 933 Service**

Telnyx provides a 933 service that:
- Validates E911 is configured for the number
- Reads back the ALI information
- Does NOT alert emergency services

```
Dial 933 → "The address registered for this number is: 
            123 Main Street, Chicago, Illinois, 60606. Press 1 if this is correct."
```

**3. Scheduled PSAP Tests**

For critical customers (hospitals, hotels), schedule live tests with the PSAP:
- Call 911
- Immediately state "This is a test, no emergency"
- PSAP confirms they received the correct ALI
- **Must be scheduled** — unannounced test calls can result in fines

🔧 **NOC Tip:** When onboarding a new customer with life-safety systems (hospital, school, hotel), REQUIRE a 933 test for each number before go-live. If 933 returns "No E911 address configured" or the wrong address, do NOT allow service activation. A misconfigured 911 can be a fatal liability.

---

## Failure Modes and Regulatory Consequences

### E911 Failure Scenarios

| Failure | Impact | Regulatory Risk |
|---------|--------|-----------------|
| ALI not synchronized | PSAP sees "address unknown" | Severe — dispatch delays |
| ALI has wrong address | Emergency services go to wrong location | Critical — liability |
| 933 test fails | Customer goes live with broken E911 | High — customer/end-user risk |
| PSAP routing failure | 911 calls don't reach any PSAP | Catastrophic — FCC violation |
| Location not updated | Mobile user shows old address | Medium — depends on circumstance |
| Carrier failure | All E911 calls fail | Catastrophic — regulatory shutdown |

### Regulatory Consequences

**FCC Enforcement:**
- Fines up to $10,000 per day for non-compliance
- Consent decrees with ongoing monitoring requirements
- Restrictions on offering new service until compliance achieved

**Civil Liability:**
- Wrongful death suits when E911 failures contribute to harm
- Class actions from customers with bad 911 service

**State Enforcement:**
- State PUCs (Public Utility Commissions) can impose additional penalties
- Suspension of operating authority

### NOC Response to E911 Failures

**Triage questions for 911 reports:**
1. What number was dialed?
2. What location showed on the ALI (if call went through)?
3. What was the actual location of the caller?
4. Did the call reach a PSAP or fail entirely?
5. Has anything changed recently (equipment, network, account)?

**Immediate Actions:**
- Verify the E911 record exists and is ALI-synchronized
- Check for recent updates that might have corrupted the record
- Test with 933 if possible
- If ALI shows wrong location and caller is in immediate danger: advise caller to state their location explicitly
- Document everything — regulatory investigations require call detail records

**Escalation:**
- E911 failures → P1 incident immediately
- Notify Safety team, Legal, and Engineering leads
- Commit to investigation timeline for regulatory reporting

---

## Key Takeaways

1. **E911 is safety-critical** — failures can result in injury, death, massive fines, and regulatory action
2. **Kari's Law and Ray Baum's Act** mandate specific VoIP E911 capabilities — violations carry $10K/day fines
3. **The ALI database** maps phone numbers to physical locations — it must be synchronized and accurate
4. **Selective routing** sends calls to the correct PSAP based on location — not all 911 calls go to the same place
5. **Dynamic location** for mobile/softphone users is essential — static addresses for nomadic users are dangerous
6. **933 testing** validates E911 configuration without actual emergency calls — mandatory before go-live
7. **E911 failures are P1 escalations** — notify Safety, Legal, and Engineering; document everything for regulatory defense

---

**End of Module 2, Section 2.13 — Business Systems**
