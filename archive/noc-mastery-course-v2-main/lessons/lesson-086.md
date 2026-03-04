# Lesson 86: Verify API — Phone Number Verification
**Module 2 | Section 2.8 — Lookup/Verify**
**⏱ ~5 min read | Prerequisites: Lesson 68, Lesson 75**

---

## The Trust Problem

How do you prove a user actually controls a phone number? This question underpins login security, account creation, and fraud prevention across the internet. The answer is phone number verification — sending a code to the number and asking the user to repeat it. Simple in concept, surprisingly complex in execution.

## OTP Verification: The Standard Flow

The most common verification method is **OTP (One-Time Password)** delivered via SMS or voice call:

### The Lifecycle

1. **Request** — The application calls Telnyx's Verify API with the phone number to verify
2. **Generate** — Telnyx generates a random code (typically 4-6 digits) with an expiration time (usually 5-10 minutes)
3. **Deliver** — Telnyx sends the code via SMS (preferred) or voice call (fallback)
4. **Submit** — The user enters the code in the application
5. **Verify** — The application sends the user-submitted code to Telnyx's Verify API
6. **Result** — Telnyx compares the submitted code against the generated code and returns success or failure

### Why SMS Is Preferred

SMS delivery is faster, cheaper, and more reliable than voice calls for OTP. However, SMS has limitations:

- **Landlines can't receive SMS** — The Verify API should check number type (Lesson 75) and fall back to voice for landlines
- **Delivery isn't guaranteed** — SMS can be delayed or filtered by carriers
- **SMS interception** — SIM swapping and SS7 attacks can intercept SMS, making it less secure than often assumed

Voice call verification reads the code aloud using TTS. It's slower and more expensive but works with any phone number, including landlines.

🔧 **NOC Tip:** When a customer reports "verification codes aren't arriving," check the SMS delivery path first (Lesson 70). Common causes: number type is landline (SMS won't work), carrier filtering (high-volume OTP traffic triggers spam filters), or 10DLC compliance issues (Lesson 69). Check MDRs (Message Detail Records) to see if the SMS was accepted by the carrier.

## Rate Limiting and Fraud Prevention

Verification APIs are prime targets for abuse. Without protection, an attacker could:

- **SMS pumping** — Trigger thousands of SMS messages to premium numbers, generating revenue for the attacker at the customer's expense
- **Brute force** — Try all possible codes (10,000 combinations for a 4-digit code)
- **Enumeration** — Use the verification API to test which phone numbers are registered in the application

### Built-in Protections

Telnyx's Verify API includes several anti-abuse mechanisms:

- **Rate limiting per phone number** — Maximum N verification requests per number per hour
- **Rate limiting per IP** — Maximum N requests from a single IP address
- **Code expiration** — Codes expire after a set time (prevents delayed brute force)
- **Attempt limiting** — Maximum N incorrect code submissions before the verification is invalidated
- **Cooldown periods** — After failed verifications, increasing delays before retries are allowed

🔧 **NOC Tip:** If a customer reports a sudden spike in Verify API usage and corresponding SMS costs, suspect SMS pumping fraud. Check if the verification requests target international or premium-rate numbers. Help the customer implement geographic restrictions and CAPTCHA on their verification flow.

## Flash Calling Verification

**Flash calling** is a newer verification method that avoids SMS entirely:

1. The application requests a flash call verification
2. Telnyx places a very brief call (1-2 rings) to the user's phone from a specific number
3. The application reads the incoming call's caller ID (the "from" number)
4. The last N digits of the calling number ARE the verification code
5. The call is automatically missed — the user doesn't need to answer

### Advantages

- **No SMS costs** — Flash calls are cheaper than SMS in many markets
- **Automatic** — The application can read the caller ID programmatically (on mobile apps with appropriate permissions), requiring no user interaction
- **Faster** — No waiting for SMS delivery

### Limitations

- **Requires phone permissions** — The app needs permission to read incoming call information
- **Caller ID availability** — Some carriers suppress or modify caller ID
- **Not universally supported** — Doesn't work on all devices and networks

## Silent Network Authentication (SNA)

The most seamless verification method is **Silent Network Authentication**, which verifies the phone number at the carrier level without any user interaction:

1. The application initiates an SNA request with the phone number
2. The request goes to the mobile carrier's authentication infrastructure
3. The carrier verifies that the device currently using data on that number matches the claimed number
4. The carrier returns a success/failure response
5. The user sees nothing — no SMS, no call, no code to enter

### How It Works Technically

SNA leverages the fact that mobile carriers know which phone number is associated with each active data connection. When a device makes a data request, the carrier can verify the MSISDN (phone number) associated with that connection.

This requires **carrier partnerships** — Telnyx must have agreements with mobile carriers to access their authentication infrastructure. Coverage varies by carrier and country.

### Advantages

- **Zero friction** — The user does nothing
- **Highly secure** — Can't be intercepted via SMS or SIM swap
- **Fast** — Verification completes in seconds

### Limitations

- **Mobile data required** — Doesn't work over WiFi (the carrier can't verify the connection)
- **Carrier support** — Not all carriers support SNA
- **Mobile only** — Doesn't work for landlines or VoIP numbers

## Real-World Troubleshooting Scenario

**Scenario:** A customer's verification success rate drops from 95% to 60% over a week.

**Investigation:**
1. **Check SMS delivery rates** — Are messages being sent but not delivered? Pull MDRs for verification messages.
2. **Check carrier rejection codes** — Are carriers filtering the traffic? High-volume OTP can trigger spam filters.
3. **Check 10DLC compliance** — If the customer's campaign registration lapsed, carriers may start blocking traffic.
4. **Check for fraud patterns** — Is the drop correlated with a spike in requests to unusual destinations (SMS pumping)?
5. **Check the sender number** — Was it recently flagged as spam?

**Resolution:** If carrier filtering is the cause, the customer may need to register a new campaign, use a dedicated short code for OTP, or rotate sender numbers. If fraud is the cause, implement geographic restrictions and tighter rate limiting.

---

**Key Takeaways:**
1. OTP verification via SMS/voice is the standard but has security limitations (SIM swap, SS7 interception)
2. Rate limiting and fraud prevention are essential — SMS pumping can generate massive costs quickly
3. Flash calling offers a cheaper, faster alternative to SMS OTP but requires phone permissions
4. Silent Network Authentication (SNA) provides zero-friction verification at the carrier level but requires mobile data and carrier partnerships
5. Verification delivery failures often trace back to the same SMS pipeline issues covered in Lessons 68-70

**Next: Lesson 77 — Fax over IP — T.38 and G.711 Passthrough**
