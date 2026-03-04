# Lesson 79: 10DLC — A2P Messaging Registration and Compliance

**Module 2 | Section 2.6 — Messaging**
**⏱ ~7 min read | Prerequisites: Lesson 68**

---

## Why 10DLC Exists

Before 10DLC, businesses sent application-to-person (A2P) messages through regular 10-digit long codes (10DLC) — the same numbers used for personal texting. Carriers couldn't distinguish legitimate business messages from spam. The result: massive spam volumes, aggressive carrier filtering that blocked legitimate messages, and a terrible experience for everyone.

10DLC is the US carrier industry's solution: a registration system that identifies who is sending messages, what they're sending, and gives them appropriate throughput based on trust.

## A2P vs. P2P: Why the Distinction Matters

**Person-to-Person (P2P):** Two humans texting each other. Low volume, conversational, no automation.

**Application-to-Person (A2P):** A software application sending messages to people. Appointment reminders, delivery notifications, authentication codes, marketing campaigns. Higher volume, automated, one-directional or semi-automated.

Carriers care about this distinction because A2P traffic is where spam lives. Legitimate A2P traffic is valuable (appointment reminders reduce no-shows, 2FA codes improve security), but illegitimate A2P traffic (spam, phishing, fraud) is a massive consumer problem.

10DLC creates a framework where legitimate A2P senders register, get vetted, and receive appropriate throughput. Unregistered traffic gets throttled or blocked.

## The Registration Hierarchy: Brand → Campaign → Number

```
Brand (who you are)
  └── Campaign (what you're sending)
       └── Number Assignment (which numbers send for this campaign)
```

### Step 1: Brand Registration

The business registers its identity:
- Legal company name, EIN (Tax ID), address
- Company size, industry, website
- Contact information

The brand is vetted by The Campaign Registry (TCR) — the central authority. TCR assigns a **trust score** based on:
- Business size and age
- Public information verification
- Industry risk category
- Previous messaging behavior

Trust scores directly determine throughput limits.

### Step 2: Campaign Registration

Each messaging use case is registered as a separate campaign:
- **Campaign type**: marketing, notifications, two-factor auth, customer care, etc.
- **Description**: what messages will say, who receives them
- **Sample messages**: examples of actual message content
- **Opt-in mechanism**: how did recipients consent to receive these messages?
- **Opt-out mechanism**: how can recipients stop receiving messages? (STOP keyword support is mandatory)

Different campaign types have different throughput allowances and compliance requirements. Marketing campaigns face stricter scrutiny than transactional notifications.

### Step 3: Number Assignment

Phone numbers (10-digit long codes) are assigned to campaigns. A number can only be in one campaign at a time. When a message is sent from that number, carriers verify it belongs to a registered campaign.

## Trust Scores and Throughput Tiers

TCR assigns trust scores that map to throughput:

| Trust Score | Typical Throughput | Typical Business Profile |
|---|---|---|
| Low | 2-5 msg/sec per carrier | Small/new businesses, unverified |
| Medium | 10-25 msg/sec per carrier | Established businesses |
| High | 50-75+ msg/sec per carrier | Large enterprises, excellent reputation |

These are **per carrier** — a medium trust score of 25 msg/sec means 25/sec to T-Mobile, 25/sec to AT&T, 25/sec to Verizon.

🔧 **NOC Tip:** When a customer complains about slow message delivery, check their trust score first. A low trust score with high message volume means messages queue up significantly. The fix isn't technical — it's business process (brand vetting, better registration, requesting trust score review).

## Common Registration Failures

### Brand Registration Rejections

- **EIN mismatch**: the company name doesn't match IRS records for that EIN
- **Incomplete information**: missing website, invalid address
- **Sole proprietor limitations**: sole props get limited trust scores and throughput
- **Foreign entities**: non-US businesses have additional requirements

### Campaign Registration Rejections

- **Inadequate opt-in description**: "users sign up on our website" isn't specific enough — must describe the opt-in flow clearly
- **Missing sample messages**: TCR requires realistic examples
- **Prohibited content**: cannabis, firearms, loans — some content categories have restrictions or outright bans
- **Mixed use case**: trying to combine marketing and transactional in one campaign

🔧 **NOC Tip:** Campaign rejection reasons in TCR are often vague ("Does not meet requirements"). Help customers by: (1) ensuring sample messages match the declared use case, (2) verifying opt-in descriptions are specific and detailed, (3) checking that the brand registration EIN matches exactly.

## Carrier-Specific Enforcement

Each carrier enforces 10DLC differently:

**T-Mobile:** Most aggressive enforcement. Unregistered traffic is blocked or severely throttled. Strict content filtering on top of 10DLC. Quickest to block numbers for violations.

**AT&T:** Enforces 10DLC with surcharges for non-compliance. Messages from unregistered numbers get carrier fees (pass-through surcharges) and reduced throughput.

**Verizon:** Historically less aggressive but increasing enforcement. Moved to requiring 10DLC registration.

This carrier variance is why "my messages work to AT&T but not T-Mobile" is such a common NOC complaint. It's almost always a 10DLC registration issue.

## The Lifecycle of 10DLC Issues in NOC

### Issue 1: "Messages Suddenly Stopped Working"

1. Check if the number's 10DLC campaign was suspended or rejected
2. Check if the number was removed from the campaign assignment
3. Check if the carrier blocked the number (spam complaints, content violation)

### Issue 2: "Messages Are Being Filtered/Blocked"

Even with valid 10DLC registration, carriers apply content filtering:
- URL shorteners (bit.ly etc.) trigger spam filters
- Certain keywords trigger filtering ("free," "winner," "act now")
- Sending the same message to many recipients looks like spam
- High opt-out rates trigger campaign suspension

### Issue 3: "Low Throughput Despite Registration"

- Check the trust score — low scores mean low throughput
- Check if the customer is sending from multiple numbers but the campaign only has one registered
- Check if they're sending to one carrier predominantly (per-carrier limits)

## Opt-Out Handling

Federal law (TCPA) and carrier requirements mandate opt-out support. When a recipient texts STOP to a 10DLC number:
1. Telnyx automatically blocks future messages to that number
2. Telnyx sends a confirmation message ("You have been unsubscribed")
3. The opt-out is reported to the customer via webhook

**Critical:** customers must not message opted-out numbers. Doing so generates carrier complaints that can lead to campaign suspension or number blocking.

## Troubleshooting Scenario: "All Messages to T-Mobile Return Error 30007"

A new customer finished 10DLC registration and started sending messages. AT&T and Verizon work. All T-Mobile messages fail with error 30007 (carrier violation).

**Investigation:**
1. Brand registration: approved ✓
2. Campaign registration: approved ✓
3. Number assignment to campaign: **not completed** ✗
4. The customer registered the brand and campaign but forgot to assign their sending number to the campaign
5. T-Mobile sees unregistered traffic and blocks it

**Resolution:** Customer assigned the number to their campaign via the Telnyx API. After propagation (can take up to 24 hours to T-Mobile), messages started flowing.

---

**Key Takeaways:**
1. 10DLC requires three-level registration: Brand → Campaign → Number Assignment — all three must be complete
2. Trust scores determine throughput limits; low scores severely limit message rates
3. T-Mobile enforces 10DLC most aggressively; messages to T-Mobile fail first when registration is incomplete
4. Campaign rejections are usually due to vague opt-in descriptions or sample messages that don't match the use case
5. Content filtering applies on top of 10DLC — even registered campaigns can have messages blocked for spammy content
6. Opt-out (STOP) handling is mandatory by law; violations lead to campaign suspension

**Next: Lesson 70 — Message Delivery Troubleshooting**
