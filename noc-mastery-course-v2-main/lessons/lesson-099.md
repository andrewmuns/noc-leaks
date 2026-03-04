# Lesson 99: Number Provisioning and Porting — The Lifecycle of a Phone Number
**Module 2 | Section 2.13 — Business Systems**
**⏱ ~6min read | Prerequisites: None**
---

## Introduction

Every phone number Telnyx owns, provisions, or ports goes through a lifecycle — from inventory to ordering to activation to termination. A failed port blocks a customer's migration. A misconfigured number prevents E911 from working. A synchronization error between Telnyx and carriers causes calls to disappear into the void.

As a NOC engineer, you'll encounter number issues when customers can't receive calls, ports get stuck, or number deletions cascade into 911 failures. This lesson covers the journey of a phone number through Telnyx systems.

---

## Number Inventory

Telnyx maintains number inventory across multiple sources:

### Number Ownership and Blocks

- **Direct allocations:** Numbers directly assigned to Telnyx by the North American Numbering Plan Administration (NANPA) in blocks of 1,000 (NXX) or 10,000 (NPA-NXX).
- **RespOrg (Responsible Organization) agreements:** Numbers for which Telnyx is the RespOrg in the SMS/800 and toll-free databases.
- **Partner inventory:** Numbers leased from other carriers with resale agreements.
- **Ported-in numbers:** Numbers customer brings from their previous carrier.

### Number States

| State | Description | Available to Order? |
|-------|-------------|---------------------|
| `AVAILABLE` | In inventory, not assigned | Yes |
| `RESERVED` | On hold for a customer | No |
| `ACTIVATED` | Assigned to an active account | No |
| `AGING` | Recently deactivated, cooling off | No (typically 30 days) |
| `QUARANTINE` | Fraud-flagged, under review | No |

### Inventory Management

```
Number Inventory Database
         │
         ├──► Ordered Numbers → Assigned to Accounts
         │
         ├──► Available Pool → API/Portal Ordering
         │
         ├──► Aging Queue → Return to Available after delay
         │
         └──► Quarantine → Manual review, then reusable or blocked
```

🔧 **NOC Tip:** When a customer asks "Is this number available?" check the inventory state AND the aging quarantine. A recently-released number may show as available internally but fail ordering if it's still in the aging period. Also, vanity numbers (repeating digits) and premium area codes (Manhattan 212, Silicon Valley 650) have separate inventory constraints.

---

## Number Ordering Flow

When a customer orders phone numbers through the Telnyx API or portal:

### Ordering Process

```
Customer Order
      │
      ▼
┌─────────────┐
│  Available  │──► Check inventory ──► Reserve numbers
│   Number?   │
└──────┬──────┘
       │ Yes
       ▼
┌─────────────┐
│   Reserve   │──► Numbers marked reserved (10-30 min timeout)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Payment   │──► Validate billing
│   Check     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Provision  │──► Assign to account, configure routing
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    E911     │──► Create E911 record, populate ALI database
│   Enable    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Active    │──► Ready for calls
└─────────────┘
```

### Provisioning Steps

1. **Number assignment:** Number linked to customer account
2. **Routing configuration:** SIP URI set for incoming calls
3. **E911 registration:** ALI database entry created with service address
4. **CNAM:** Default or customer-specified caller name set
5. **Test calls:** Internal verification that routing works

🔧 **NOC Tip:** If a customer reports "I can't receive calls on my number," check the provisioning status in this order: (1) Is the number active in our database? (2) Is there a SIP URI configured for routing? (3) Is the destination reachable? (4) Is there a carrier-level routing issue (LRN lookup)? The number being active doesn't mean calls route correctly.

---

## Number Porting

**Porting** moves a phone number from one carrier to another while keeping the number itself. It's the primary way customers switch to Telnyx.

### Port Types

| Type | Description | Typical Timeline |
|------|-------------|------------------|
| Port-in | Customer brings number TO Telnyx | 1–15 business days |
| Port-out | Customer moves number FROM Telnyx | 1–3 business days |
| Intra-port | Move between Telnyx accounts | Hours |

### Port-In Process

```
Customer requests port
        │
        ▼
┌─────────────┐
│ Generate    │──► Create LSR (Local Service Request) with old carrier
│    LSR      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │──► Check FOC response, CSR (Customer Service Record)
│   Request   │    Verify account number, PIN, address match
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    FOC      │──► Firm Order Commitment from losing carrier
│  Received   │    Confirms port date and time
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CNP / LNP   │──► Call routing cutover at scheduled time
│   Cutover   │    Number transferred in NPAC database
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Activate   │──► Number active on Telnyx, calls route to customer
└─────────────┘
```

### Key Porting Terms

| Term | Meaning |
|------|---------|
| LSR | Local Service Request — formal request to port |
| FOC | Firm Order Commitment — losing carrier accepts and schedules |
| CSR | Customer Service Record — account details from losing carrier |
| NPAC | Number Portability Administration Center — central database for ported numbers |
| LRN | Location Routing Number — identifies carrier for a ported number |

---

## Common Porting Failures

### LSR Rejection

The losing carrier rejects the port request.

**Common causes:**
- Account number doesn't match CSR
- PIN/Password incorrect
- Address mismatch on CSR
- Number has pending orders on losing carrier
- Number is part of a hunt group or DSL bundle

**NOC Response:** Gather correct information from customer, resubmit LSR.

### FOC Delays

Losing carrier takes longer than SLA to provide FOC.

**Escalation path:**
1. Check standard lead time (wireline: 1–3 days; wireless: 1–3 days; toll-free: 1–5 days)
2. Escalate to losing carrier port team
3. If >SLA, escalate to regulatory team

### Cutover Failure

Port completes in NPAC, but calls still route to old carrier.

**Common causes:**
- LRN not updated in all carrier databases (cache propagation)
- Called party's carrier cached old routing (24–72h TTL)
- Internal routing not updated at Telnyx

**NOC Response:**
```bash
# Check LRN lookup for ported number
telnyx-cli lrn-lookup +14155551234

# Expected: returns Telnyx LRN
# If returns old carrier LRN: NPAC not yet processed
# If returns Telnyx LRN but calls fail: internal routing issue
```

### Partial Port

A range or hunt group was partially ported, leaving some numbers behind.

**Symptom:** Customer can receive most calls but some numbers still go to old carrier.

**Resolution:** Identify the remaining numbers and port them, or reconfigure hunt group.

🔧 **NOC Tip:** Porting has a **critical window** — the cutover time. When FOC specifies "Feb 23, 2:00 PM EST," that's the moment the number switches. Have NOC staffing aware of large ports. If cutover fails, you have a live customer with no working number. Monitor port tickets on cutover day and be ready to troubleshoot immediately.

---

## Number Activation

After a number is ordered or ported, it goes through activation.

### Activation Checklist

- [ ] Number assigned to account
- [ ] SIP URI configured in routing database
- [ ] E911 record created with valid service address
- [ ] CNAM set (or default "TELNYX" fallback)
- [ ] LRN updated (for ports)
- [ ] Test call succeeds
- [ ] Customer notified of activation

### Activation Failures

**Number shows active but calls don't work:**
- Check SIP URI destination — is it reachable?
- Check firewall — is the customer's IP whitelisted?
- Check SBC routing — is the number in the SBC dial plan?
- Check carrier connectivity — is there a SIP trunk failure?

**E911 activation fails:**
- Invalid address format
- Address not geocoded (longitude/latitude)
- ALI database sync failure
- E911 provider API timeout

---

## E911 Provisioning

Every voice number must have E911 capability. This is **federally mandated**.

### E911 Database Flow

```
Telnyx Provisioning System
         │
         ├──► Create E911 record with service address
         │
         ▼
┌─────────────────┐
│  E911 Provider  │──► (Bandwidth, Intrado, etc.)
│   (Partner)     │
└────────┬────────┘
         │
         ├──► Validate address (geocode lookup)
         │
         ├──► Create ALI record with PSAP mapping
         │
         └──► Populated to Emergency Services database
```

### E911 Record Components

- **ANI (Automatic Number Identification):** The callback number
- **ALI (Automatic Location Information):** The physical address for dispatch
- **PSAP Routing:** Which emergency call center receives the call
- **Latitude/Longitude:** For mobile/VoIP location

---

## NOC Escalation for Number Issues

### Triage Flow

```
Customer reports number issue
           │
           ├──► Can't receive calls ──► Check routing/SIP URI
           │
           ├──► Can't place calls ──► Check account/authorization
           │
           ├──► Port stuck/delayed ──► Check LSR/FOC status, escalate to Porting team
           │
           ├──► E911 not working ──► Check E911 record, ALI sync
           │
           └──► Number showing wrong caller ID ──► Check CNAM, attestation
```

### Escalation Matrix

| Issue | First Response | Escalate To |
|-------|---------------|-------------|
| Order provisioning stuck | Check inventory, retry provision | Provisioning team |
| Port rejected by losing carrier | Verify CSR details, resubmit | Porting team |
| Port cutover failed | Check LRN, internal routing | Porting + Engineering |
| E911 sync failure | Check address/geocode | E911 provider + Safety team |
| Fraudulent port request | Quarantine numbers | Security team + Legal |
| Mass port-out (account cancellation) | Verify customer intent | Customer Success + Risk |

---

## Key Takeaways

1. **Number lifecycle:** Available → Reserved → Activated → Aging → (back to Available or Quarantine)
2. **Ordering flow:** Check inventory → Reserve → Payment validation → Provision → E911 → Active
3. **Port-in process:** LSR → FOC → Cutover → Activation; failures at each stage have different causes
4. **LSR rejection** usually means bad account info — get the CSR from the losing carrier
5. **Cutover failures** are NOC-critical — monitor scheduled ports and be ready to troubleshoot routing
6. **E911 provisioning** is mandatory and legally required — every active voice number needs a valid ALI record
7. **Number issues escalate** based on symptom: routing → SIP/Engineering, ports → Porting team, E911 → Safety team

---

**Next: Lesson 90 — Emergency Services: E911 Architecture and Obligations**
