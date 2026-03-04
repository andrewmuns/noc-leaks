# Lesson 84: CNAM, E911, and Number Features
**Module 2 | Section 2.7 — Numbers**
**⏱ ~6 min read | Prerequisites: Lesson 72**

---

## Beyond Making Calls

A phone number does far more than receive and place calls. It carries metadata, enables emergency services, and participates in authentication frameworks. These "number features" are critical for regulatory compliance and customer experience. As a NOC engineer, understanding these features helps you debug puzzling issues like "why does my caller ID show 'UNKNOWN'?" or "why can't my customer reach 911?"

## CNAM: Caller Name Database

When your phone rings and shows "ACME Corp" alongside the phone number, that name comes from the **CNAM (Caller Name) database**. Here's how it works:

### The CNAM Query Flow

1. An inbound call arrives at the terminating carrier with a Calling Party Number (CPN) in the SIP From header or P-Asserted-Identity
2. The terminating carrier performs a **CNAM dip** — querying a CNAM database with that number
3. The database returns the registered name (up to 15 characters)
4. The terminating carrier delivers the name to the called party's device

Key insight: **CNAM is a terminating-side lookup.** The originating carrier doesn't send the name — the terminating carrier looks it up. This means:

- The name displayed depends on which CNAM database the terminating carrier queries
- Different carriers may query different databases, so the same number might show different names on different networks
- CNAM updates take time to propagate across databases (typically 24-72 hours)

### CNAM at Telnyx

Customers can set their outbound CNAM through the Telnyx portal or API. Telnyx pushes this data to major CNAM databases. However, there's no guarantee every carrier will display it — they might use a different database, cache old data, or not perform CNAM queries at all (common with mobile carriers).

🔧 **NOC Tip:** When a customer says "my caller ID name isn't showing correctly," first verify their CNAM is set correctly in Telnyx's system. Then explain the propagation delay (24-72 hours) and the fact that mobile carriers often don't display CNAM data at all — they rely on the contact list in the recipient's phone instead.

## E911: Enhanced 911

**E911 is not optional.** In the US, any provider offering voice service must provide access to emergency services. For VoIP providers like Telnyx, this is technically challenging because, unlike PSTN phones, VoIP endpoints can be anywhere.

### How E911 Works

Traditional 911 routes based on the caller's phone number, which maps to a physical address via the ALI (Automatic Location Identification) database. For VoIP, Telnyx must:

1. **Collect the customer's address** — The service address where the number will be used
2. **Validate against the MSAG** — The Master Street Address Guide is the authoritative database of valid addresses in each PSAP (Public Safety Answering Point) jurisdiction. The customer's address must match an MSAG entry exactly.
3. **Provision the ALI database** — Register the number-to-address mapping so 911 dispatchers receive the correct location
4. **Route 911 calls correctly** — When a 911 call originates, route it to the correct PSAP based on the provisioned address

### MSAG Validation

The MSAG is notoriously strict. "123 Main Street" might be rejected because the MSAG has it as "123 Main St" or "123 N Main Street." Address validation failures are the most common E911 provisioning issue.

🔧 **NOC Tip:** If E911 provisioning fails with an address validation error, try variations: abbreviate "Street" to "St," add or remove directionals (N, S, E, W), check the unit/suite number format. The MSAG database can be queried to find the exact expected format.

### E911 Troubleshooting

**Scenario:** Customer reports 911 calls aren't connecting.

1. **Verify E911 is provisioned** — Check if the number has an E911 address registered
2. **Check the provisioning status** — MSAG validation might have failed silently
3. **Verify the call path** — 911 calls take a special routing path, separate from normal call routing
4. **Escalate immediately** — E911 failures are always high-priority. Lives may depend on it.

## STIR/SHAKEN: Combating Caller ID Spoofing

**STIR/SHAKEN** (Secure Telephone Identity Revisited / Signature-based Handling of Asserted information using toKENs) is a framework to combat robocall spoofing. It cryptographically signs calls with an attestation of the calling number's legitimacy.

### The Three Attestation Levels

- **Full Attestation (A)** — The carrier knows the customer and has authorized them to use this specific calling number. Highest trust.
- **Partial Attestation (B)** — The carrier knows the customer but can't verify they're authorized for this specific number (e.g., the number might be ported from another carrier and routing isn't fully updated).
- **Gateway Attestation (C)** — The carrier received the call from a gateway (like a PSTN interconnect) and can't verify the caller. Lowest trust.

### How It Works Technically

1. The originating carrier signs the SIP INVITE with a **PASSporT** (Personal Assertion Token) — a JWT containing the calling number, called number, and attestation level
2. The signature uses the carrier's private key, with the public key available via a certificate
3. The terminating carrier verifies the signature against the certificate
4. If verification fails or attestation is low, the terminating carrier may mark the call as "Spam Likely" or block it entirely

### Impact on Telnyx Customers

Telnyx signs outbound calls with STIR/SHAKEN attestation. The attestation level depends on whether the customer owns the calling number on Telnyx's platform:

- Number is on the customer's Telnyx account → **Full Attestation (A)**
- Number is recognized but not directly assigned → **Partial Attestation (B)**
- Number is not on Telnyx's platform → **Gateway Attestation (C)**

🔧 **NOC Tip:** If a customer's calls are being flagged as spam by the terminating carrier, check the STIR/SHAKEN attestation level. Calls with C-level attestation are much more likely to be flagged. Ensure the customer is using a calling number that's on their Telnyx account for Full Attestation.

## Toll-Free Number Management

Toll-free numbers (800, 888, 877, etc.) have a separate management ecosystem:

- **RespOrg** (Responsible Organization) — The entity that manages toll-free number routing. Telnyx acts as a RespOrg.
- **SMS/MMS enablement** — Toll-free numbers must be separately registered for messaging (toll-free verification process)
- **Routing control** — Toll-free routing is managed through the SMS/800 database, not the standard LNP system

## Real-World Troubleshooting Scenario

**Scenario:** A customer's outbound calls consistently show "Spam Likely" on the recipient's phone.

**Investigation:**
1. Check STIR/SHAKEN attestation — Is the customer using a number from their Telnyx account? What attestation level are calls receiving?
2. Check CNAM — Is a legitimate business name registered?
3. Check calling patterns — High-volume, short-duration calls trigger carrier spam filters regardless of attestation
4. Check reputation databases — Numbers can be flagged in third-party spam databases (Hiya, TNS, First Orion)

**Resolution:** Ensure Full Attestation (A) by using Telnyx-provisioned numbers, register CNAM, and if the number is in spam databases, work with those providers to request removal. Adjust calling patterns to avoid spam-like behavior.

---

**Key Takeaways:**
1. CNAM is a terminating-side database lookup — the originating carrier doesn't send the name, and propagation takes 24-72 hours
2. E911 is a legal requirement for VoIP providers — MSAG address validation is strict and failures are the most common issue
3. STIR/SHAKEN attestation levels (A/B/C) directly affect whether calls are flagged as spam — Full Attestation requires using numbers from the customer's own account
4. Toll-free numbers have a separate management ecosystem (RespOrg, SMS/800 database)
5. E911 issues are always high-priority — escalate immediately, don't debug leisurely

**Next: Lesson 75 — Number Lookup API — LRN, Carrier, and Caller ID**
