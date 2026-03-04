# Lesson 70: RCS — Rich Communication Services

**Module 1 | Section 1.17 — Messaging**
**⏱ ~5min read | Prerequisites: Lesson 181 (SMS/MMS Fundamentals)**

---

## Introduction

RCS (Rich Communication Services) is the next-generation messaging protocol designed to replace SMS. Think of it as iMessage-level features built into the carrier network — read receipts, typing indicators, rich media, interactive buttons — all delivered natively through the phone's default messaging app. For NOC engineers, RCS introduces new infrastructure dependencies and failure modes.

---

## RCS vs SMS

```
Feature              SMS                RCS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Character limit      160 (GSM-7)        8,000+
Media                MMS (1 MB max)     100 MB+
Read receipts        No                 Yes
Typing indicators    No                 Yes
Group chat           Basic              Full-featured
Buttons/Actions      No                 Yes (suggested actions)
Rich cards           No                 Yes (carousels, images)
Branding             No                 Logo, colors, verified sender
Encryption           No                 Optional (E2E in some clients)
Fallback             N/A                SMS/MMS
Transport            SS7/SMPP           HTTP/SIP (IMS-based)
```

---

## RCS Architecture

### Protocol Stack

```
┌──────────────────────────────────┐
│  RCS Client (Messages app)       │
│  Android Messages / Samsung      │
└──────────┬───────────────────────┘
           │ HTTP / SIP
┌──────────▼───────────────────────┐
│  RCS Platform (Jibe / carrier)   │
│  - Message routing               │
│  - Media storage                 │
│  - Presence/capability exchange  │
└──────────┬───────────────────────┘
           │ RCS Business Messaging API
┌──────────▼───────────────────────┐
│  RBM Platform (Google / Telnyx)  │
│  - Agent management              │
│  - Message delivery              │
│  - Analytics                     │
└──────────────────────────────────┘
```

### Key Infrastructure Components

- **Jibe Cloud** — Google's hosted RCS platform (used by most carriers)
- **IMS (IP Multimedia Subsystem)** — Carrier network layer that transports RCS
- **MaaP (Messaging as a Platform)** — GSMA standard for RCS business messaging
- **RBM (RCS Business Messaging)** — Google's API for A2P RCS messages

---

## RCS Business Messaging (RBM)

### Agent Registration

An RCS "agent" is the business identity that sends messages. Think of it like a verified business profile:

```json
{
  "agent": {
    "displayName": "Acme Health",
    "description": "Appointment reminders and health updates",
    "logoUrl": "https://acme.com/logo-224x224.png",
    "heroImageUrl": "https://acme.com/hero-1440x720.png",
    "color": "#0066CC",
    "phone": "+15551234567",
    "website": "https://acmehealth.com",
    "privacyPolicy": "https://acmehealth.com/privacy",
    "termsOfService": "https://acmehealth.com/terms"
  }
}
```

Agent verification involves:
1. Business identity verification
2. Brand asset review (logo, colors)
3. Use case approval
4. Carrier-level launch approval
5. Regional availability confirmation

🔧 **NOC Tip:** RCS agent registration is a multi-week process similar to short code provisioning. Manage customer expectations — this isn't instant like SMS API setup.

---

## Rich Message Types

### Plain Text with Suggested Actions

```json
{
  "contentMessage": {
    "text": "Your appointment is tomorrow at 2:00 PM. Would you like to confirm?",
    "suggestions": [
      {
        "action": {
          "text": "Confirm",
          "postbackData": "confirm_appt_123"
        }
      },
      {
        "action": {
          "text": "Reschedule",
          "postbackData": "reschedule_appt_123"
        }
      },
      {
        "action": {
          "text": "Call Office",
          "dialAction": {
            "phoneNumber": "+15551234567"
          }
        }
      }
    ]
  }
}
```

### Rich Cards

```json
{
  "contentMessage": {
    "richCard": {
      "standaloneCard": {
        "cardContent": {
          "title": "Order #12345 Shipped!",
          "description": "Your package is on the way. Estimated delivery: Feb 25.",
          "media": {
            "height": "MEDIUM",
            "contentInfo": {
              "fileUrl": "https://acme.com/tracking-map.jpg",
              "forceRefresh": false
            }
          },
          "suggestions": [
            {
              "action": {
                "text": "Track Package",
                "openUrlAction": {
                  "url": "https://acme.com/track/12345"
                }
              }
            }
          ]
        }
      }
    }
  }
}
```

### Carousels

```json
{
  "contentMessage": {
    "richCard": {
      "carouselCard": {
        "cardWidth": "MEDIUM",
        "cardContents": [
          {
            "title": "Basic Plan - $9.99/mo",
            "description": "5GB data, unlimited calls",
            "suggestions": [{ "action": { "text": "Select", "postbackData": "plan_basic" }}]
          },
          {
            "title": "Pro Plan - $19.99/mo",
            "description": "25GB data, unlimited everything",
            "suggestions": [{ "action": { "text": "Select", "postbackData": "plan_pro" }}]
          },
          {
            "title": "Enterprise - $49.99/mo",
            "description": "Unlimited everything + priority",
            "suggestions": [{ "action": { "text": "Select", "postbackData": "plan_enterprise" }}]
          }
        ]
      }
    }
  }
}
```

---

## Fallback to SMS

RCS isn't universally available. Fallback is critical:

```
Send RCS message
  → Check device capability (RCS supported?)
    → YES: Deliver via RCS
    → NO: Fallback to SMS/MMS
  → Delivery timeout (e.g., 30 seconds)
    → Not delivered via RCS? → Fallback to SMS/MMS
```

### Capability Check

Before sending RCS, the platform checks if the recipient supports it:

```bash
# Check RCS capability for a number
curl -X GET "https://api.telnyx.com/v2/rcs/capabilities/+15559876543" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```json
{
  "data": {
    "phone_number": "+15559876543",
    "rcs_enabled": true,
    "features": ["RICHCARD_STANDALONE", "ACTION_CREATE_CALENDAR_EVENT", "ACTION_DIAL"],
    "fallback_required": false
  }
}
```

🔧 **NOC Tip:** RCS capability can change — a user switching from Android to iPhone loses RCS Business Messaging support (Apple uses its own iMessage, not carrier RCS for business). Always implement SMS fallback. Monitor your RCS-to-SMS fallback ratio; a sudden spike might indicate a carrier RCS platform outage.

---

## Telnyx RCS API

### Sending an RCS Message with Fallback

```bash
curl -X POST https://api.telnyx.com/v2/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "from": "acme_health_agent",
    "to": "+15559876543",
    "messaging_profile_id": "...",
    "type": "RCS",
    "content": {
      "text": "Your prescription is ready for pickup.",
      "suggestions": [
        { "action": { "text": "Get Directions", "openUrlAction": { "url": "https://maps.google.com/..." }}}
      ]
    },
    "fallback": {
      "type": "SMS",
      "text": "Your prescription is ready for pickup at Acme Pharmacy."
    },
    "fallback_timeout_ms": 30000
  }'
```

---

## Current RCS Landscape (2026)

```
Platform support:
  ✅ Android (Google Messages) — Primary RCS client
  ✅ Samsung Messages — Via carrier/Jibe
  ⚠️  Apple iMessage — RCS support added in iOS 18 (2024) but limited
  ❌ Feature phones — No RCS support

Carrier support (US):
  ✅ T-Mobile — Full RCS via Jibe
  ✅ AT&T — RCS via Jibe  
  ✅ Verizon — RCS via Jibe
  
Business messaging:
  ✅ Google RBM — Primary A2P RCS platform
  ✅ Telnyx — RCS via partnership/direct integration
```

🔧 **NOC Tip:** RCS delivery rates vary significantly by market. In the US, expect ~60-70% RCS capability among recipients (Android users with RCS enabled). Always track your RCS delivery rate vs fallback rate to measure real-world reach.

---

## Real-World NOC Scenario

**Scenario:** Customer reports RCS messages are all falling back to SMS despite recipients being on Android.

**Investigation:**

1. Check RCS agent status — is it verified and launched?
2. Run capability checks on sample recipient numbers
3. Check if Jibe/carrier RCS platform has an ongoing incident
4. Verify the agent's carrier launch status (must be approved per-carrier)
5. Check if fallback timeout is too aggressive (< 10 seconds)

---

## Key Takeaways

1. **RCS is SMS's successor** — rich cards, buttons, branding, read receipts, all via the native messaging app
2. **Agent registration is required** — similar to short code provisioning, takes weeks
3. **Always implement SMS fallback** — RCS reach is ~60-70% at best
4. **Capability checks** prevent wasted RCS attempts on unsupported devices
5. **Carousels and suggested actions** enable interactive business messaging without apps
6. **Monitor fallback ratios** — a spike indicates RCS platform issues
7. **Apple's RCS support is consumer-only** — business RCS (RBM) still primarily reaches Android

---

**Next: Lesson 186 — Number Lookup and Caller Identity (CNAM)**
