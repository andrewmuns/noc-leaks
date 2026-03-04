# Lesson 81: RCS — Rich Communication Services

**Module 2 | Section 2.6 — Messaging**
**⏱ ~5 min read | Prerequisites: Lesson 68**

---

## SMS's Long-Overdue Successor

SMS was designed in the 1980s. Its 160-character limit, plain text format, and lack of read receipts feel archaic compared to WhatsApp, iMessage, or Telegram. RCS (Rich Communication Services) is the carrier industry's attempt to modernize — bringing app-like messaging features to the native messaging app on every phone.

Think of RCS as "iMessage for everyone" — rich media, typing indicators, read receipts, and interactive elements, all delivered through the carrier network rather than an OTT app.

## What RCS Enables

**Rich Cards:** Structured content with images, titles, descriptions, and action buttons. Instead of "Your order shipped! Track at http://...", you get a card with the product image, order number, tracking button, and contact support button.

**Carousels:** Multiple cards that users swipe through. Product catalogs, menu options, appointment slots — all presented visually in the message thread.

**Suggested Actions:** Buttons that trigger actions — call a number, open a URL, share location, add a calendar event. Instead of "Reply YES to confirm," the user taps a "Confirm" button.

**Suggested Replies:** Quick-reply chips that the user can tap instead of typing. "Yes / No / Maybe later" — one tap instead of typing a response.

**File Sharing:** Send and receive larger files (images, videos, documents) without the MMS size constraints.

**Typing Indicators & Read Receipts:** The sender knows when the message was delivered, read, and when the recipient is typing a reply.

## RCS Business Messaging (RBM)

For businesses (A2P messaging), RCS uses a specific framework called RCS Business Messaging:

### Agent Registration

A business registers as an RBM "agent" — essentially a verified business identity. The registration includes:
- Business verification (legal entity, website, contact info)
- Brand assets (logo, colors, description)
- Messaging use case and categories
- Launch countries and carriers

The agent appears as a branded sender in the user's messaging app — with logo, verified badge, and business name — instead of just a phone number.

### Message Flow

```
Business App → Telnyx RBM API → Google Jibe Cloud (RCS hub) → Carrier → User's Messages App
```

Most RCS infrastructure runs through Google's Jibe platform, which acts as the RCS hub for many carriers. This is different from SMS, which goes carrier-direct.

## The Fallback Problem

RCS only works when:
1. The sender supports RCS (via Telnyx or another provider)
2. The carrier supports RCS
3. The recipient's phone supports RCS
4. The recipient's messaging app has RCS enabled
5. The recipient has a data connection (RCS uses IP, not circuit-switched)

If any of these conditions aren't met, the message **must fall back to SMS/MMS**. This fallback is critical — businesses can't just not deliver a message because RCS isn't available.

The fallback logic:
1. Attempt RCS delivery
2. If recipient isn't RCS-capable (checked via capability API), immediately fall back to SMS
3. If RCS delivery fails (timeout, error), fall back to SMS
4. If RCS message is delivered but not read within a timeout, optionally send SMS reminder

🔧 **NOC Tip:** "Customer says some users get rich messages and some get plain SMS" — this is expected behavior, not a bug. RCS availability varies by carrier, device, and user settings. The fallback to SMS ensures universal delivery. Check RCS capability for specific numbers using the capability API to verify whether a recipient supports RCS.

## Delivery Receipts in RCS

Unlike SMS's unreliable DLRs (Lesson 68), RCS provides granular status:
- **Sent**: message left the platform
- **Delivered**: message arrived on the device
- **Read**: user opened/viewed the message
- **Failed**: delivery failed (with reason)

This is significantly more reliable than SMS DLRs because RCS operates over IP with application-level acknowledgments.

## RCS vs. OTT Messaging (WhatsApp Business, etc.)

| Feature | RCS | WhatsApp Business |
|---------|-----|-------------------|
| Reach | Native messaging app (Android, growing iOS) | WhatsApp users only |
| App install needed | No | Yes (WhatsApp) |
| Rich messages | Yes | Yes |
| End-to-end encryption | In progress (varies by implementation) | Yes (default) |
| Carrier dependency | Yes | No (OTT) |
| Global reach | Growing but uneven | 2B+ users globally |
| Fallback | SMS/MMS | None (WhatsApp only) |

RCS's advantage is native integration — no app install required. Its disadvantage is carrier fragmentation and slower global rollout. Apple's adoption of RCS on iOS (starting 2024) is a major accelerator.

## NOC Implications

RCS issues you'll encounter:

**1. Capability Check Failures:** The RCS capability API returns incorrect information — user shows as RCS-capable but delivery fails, or shows as incapable but actually supports RCS.

**2. Delivery Delays:** RCS goes through Google Jibe and carrier infrastructure. More hops = more potential latency. Time-sensitive messages (OTP codes) may experience unacceptable delay.

**3. Fallback Failures:** RCS fails but the fallback to SMS also fails (10DLC issue, number blocked, etc.). The customer gets no message at all.

**4. Rich Content Rendering:** Different phones render RCS cards differently. A carousel that looks perfect on a Samsung may render oddly on a Pixel. Testing across devices is necessary.

## Troubleshooting Scenario: "RCS Messages Showing as Plain Text"

A customer's RCS agent is registered and approved, but all messages arrive as plain SMS.

**Investigation:**
1. Check RCS capability for recipient numbers → recipients show as RCS-capable
2. Check the message sending logs → messages are being sent via RCS path
3. Check delivery status → RCS delivery fails with timeout, falls back to SMS
4. Check Jibe Cloud connectivity → Telnyx's connection to Google Jibe is healthy
5. The customer's RCS agent was registered for the US but they're sending to Canadian numbers → agent not launched in Canada

**Resolution:** Customer submitted their RCS agent for launch in Canada. After carrier approval, Canadian recipients received rich messages.

---

**Key Takeaways:**
1. RCS adds rich messaging (cards, carousels, buttons, read receipts) to the native phone messaging app
2. Fallback to SMS/MMS is essential because RCS availability depends on carrier, device, and user settings
3. RBM agents must be registered and verified — like 10DLC but for rich messaging
4. RCS status reporting (delivered, read) is more reliable than SMS DLRs
5. RCS infrastructure typically routes through Google Jibe Cloud, adding a dependency
6. Regional launch requirements mean an agent approved in one country may not work in another

**Next: Lesson 72 — Number Provisioning: Ordering, Searching, and Assigning**
