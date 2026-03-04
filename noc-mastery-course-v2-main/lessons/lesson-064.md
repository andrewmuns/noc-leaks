# Lesson 64: TeXML — XML-Based Call Control

**Module 1 | Section 1.19 — Programmable Voice**
**⏱ ~6min read | Prerequisites: Lesson 50 (SIP Call Flow)**

---

## Introduction

TeXML is Telnyx's XML-based call control language — similar to Twilio's TwiML. It lets developers control calls by returning XML documents from webhooks instead of making sequential API calls. For NOC engineers, TeXML is important because many customers migrate from Twilio and use TeXML as their primary call control mechanism. Understanding how it works helps you debug call flow issues.

---

## TeXML vs Call Control API

Telnyx offers two programmable voice approaches:

```
                    TeXML                    Call Control API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model:              Stateless (webhook)      Stateful (REST commands)
Control flow:       XML response to webhook  API calls per action
Complexity:         Simpler                  More powerful
Migration:          Easy from TwiML          Requires rewrite
Real-time control:  Limited                  Full (mid-call changes)
State management:   In customer's app        In customer's app
Latency:            One round-trip per step  One API call per action
```

### When Customers Use TeXML

- Migrating from Twilio (TwiML → TeXML is nearly 1:1)
- Simple IVR flows (press 1 for sales, press 2 for support)
- Call recording and forwarding
- Conference bridges
- Auto-attendant / voice menus

### When Customers Use Call Control API

- Complex real-time call manipulation
- AI-driven call routing
- Dynamic call transfers mid-conversation
- Programmatic conference management

---

## How TeXML Works

### The Webhook Flow

```
1. Incoming call hits Telnyx number
2. Telnyx POSTs webhook to customer's TeXML URL
3. Customer's server returns XML with instructions
4. Telnyx executes the XML verbs
5. When a verb completes (e.g., Gather timeout), Telnyx webhooks again
6. Customer returns new XML
7. Repeat until call ends
```

```
Incoming Call
    │
    ▼
Telnyx ──POST──> Customer Server
                      │
                      ▼
              Generate XML response
                      │
                      ▼
Telnyx <──XML────── Response
    │
    ▼
Execute verbs (Say, Play, Gather...)
    │
    ▼ (on Gather input or timeout)
Telnyx ──POST──> Customer Server (with digits)
                      │
                      ▼
Telnyx <──XML────── New instructions
```

---

## TeXML Verbs

### Say — Text-to-Speech

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice" language="en-US">
    Welcome to Acme Corporation. Your call is important to us.
  </Say>
</Response>
```

### Play — Audio File

```xml
<Response>
  <Play>https://example.com/audio/hold-music.mp3</Play>
</Response>
```

### Gather — Collect DTMF Input

```xml
<Response>
  <Gather numDigits="1" action="/handle-input" method="POST" timeout="10">
    <Say>Press 1 for sales. Press 2 for support. Press 0 for operator.</Say>
  </Gather>
  <!-- Fallback if no input -->
  <Say>We didn't receive any input. Goodbye.</Say>
  <Hangup/>
</Response>
```

When the caller presses a digit, Telnyx POSTs to `/handle-input` with:

```json
{
  "Digits": "1",
  "CallSid": "call_abc123",
  "From": "+15559876543",
  "To": "+15551234567"
}
```

### Dial — Connect to Another Number

```xml
<Response>
  <Dial callerId="+15551234567" timeout="30" action="/dial-status">
    <Number>+15552223333</Number>
  </Dial>
  <Say>The person you are trying to reach is unavailable.</Say>
</Response>
```

### Record — Record the Call

```xml
<Response>
  <Say>This call may be recorded for quality purposes.</Say>
  <Record maxLength="300" action="/recording-complete" 
          recordingStatusCallback="/recording-status"
          transcribe="true"/>
</Response>
```

### Conference — Multi-Party Calling

```xml
<Response>
  <Dial>
    <Conference beep="true" startConferenceOnEnter="true"
                endConferenceOnExit="false" waitUrl="/hold-music">
      sales-meeting-room-1
    </Conference>
  </Dial>
</Response>
```

### Combined Example — Full IVR

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather numDigits="1" action="/menu-select" timeout="8">
    <Say voice="alice">
      Thank you for calling Acme Health.
      For appointments, press 1.
      For prescriptions, press 2.
      For billing, press 3.
      To speak with an operator, press 0.
    </Say>
  </Gather>
  <Redirect>/menu-timeout</Redirect>
</Response>
```

---

## TeXML Bins

For simple use cases, customers can store TeXML directly in Telnyx without running their own server:

```
TeXML Bin = Hosted XML snippet stored on Telnyx

Customer creates a bin with static XML
  → Assigns bin URL to their phone number
  → Incoming calls execute the bin's XML
  → No customer server needed
```

```bash
# Create a TeXML bin
curl -X POST https://api.telnyx.com/v2/texml/bins \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "Simple Forwarding",
    "content": "<?xml version=\"1.0\"?><Response><Dial><Number>+15552223333</Number></Dial></Response>"
  }'
```

🔧 **NOC Tip:** If a customer's TeXML endpoint is down, their calls fail. TeXML bins are a quick fix — you can create a static bin that forwards calls to a backup number. This is useful during customer server outages.

---

## Migration from Twilio TwiML

TeXML is designed for easy migration from TwiML. Most verbs are identical:

```
TwiML Verb          TeXML Equivalent     Differences
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<Say>               <Say>                Same
<Play>              <Play>               Same
<Gather>            <Gather>             Same
<Dial>              <Dial>               Same
<Record>            <Record>             Same
<Conference>        <Conference>         Same
<Hangup>            <Hangup>             Same
<Redirect>          <Redirect>           Same
<Pause>             <Pause>              Same
<Enqueue>           <Enqueue>            Telnyx queue system
<Pay>               Not supported        Telnyx doesn't have Pay
```

### Key Migration Differences

```
1. Endpoint URL:  Change from api.twilio.com to api.telnyx.com
2. Auth:          Twilio uses AccountSid/AuthToken; Telnyx uses API key
3. Webhook params: Slightly different parameter names
   Twilio: "CallSid"  →  Telnyx: "CallSid" (compatible)
   Twilio: "AccountSid" → Telnyx: "AccountSid" (mapped)
4. Voice names:   Different TTS voice options
5. Recording URLs: Different storage location
```

🔧 **NOC Tip:** When a customer migrates from Twilio to Telnyx and calls break, the most common issue is the webhook URL still pointing to Twilio's endpoint or the authentication not being updated. Check the TeXML application's webhook URL in Mission Control.

---

## Troubleshooting TeXML

### Common Failures

```
Problem: Call connects but immediately hangs up
Cause:   TeXML endpoint returns non-200 HTTP status or invalid XML
Check:   curl the customer's webhook URL — does it return valid XML?

Problem: "We didn't receive any input" plays immediately
Cause:   Gather timeout too short, or DTMF detection issue
Check:   Is the customer sending RFC 2833 DTMF? Check SIP codec negotiation.

Problem: Dial verb connects but no audio
Cause:   Media path issue (NAT, firewall)
Check:   Same as standard SIP troubleshooting — check RTP flow

Problem: Say verb sounds robotic or wrong language
Cause:   Wrong voice or language attribute
Check:   Verify voice="alice" and language="en-US" in the XML
```

### Debugging with Webhook Logs

```bash
# Check TeXML webhook delivery logs
curl "https://api.telnyx.com/v2/texml/call_events?filter[call_control_id]=call_abc123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

🔧 **NOC Tip:** Enable TeXML debugging in Mission Control for the customer's connection. This logs the full XML response from their server, making it easy to spot malformed XML or wrong verb parameters without needing access to their server.

---

## Real-World NOC Scenario

**Scenario:** Customer migrated from Twilio last week. All inbound calls hear silence for 10 seconds, then disconnect.

**Investigation:**

1. Check the TeXML application webhook URL — is it reachable?
2. `curl -X POST https://customer.example.com/voice/inbound` — returns 502 Bad Gateway
3. Customer's server is returning errors, so Telnyx gets no XML instructions
4. With no instructions, the call times out and disconnects
5. **Quick fix:** Create a TeXML bin with a forwarding number as backup
6. **Root cause:** Customer's webhook server expects Twilio-format POST params that differ slightly from Telnyx format

---

## Key Takeaways

1. **TeXML is stateless webhook-driven call control** — customer returns XML, Telnyx executes it
2. **Verbs mirror TwiML** — Say, Play, Gather, Dial, Record, Conference all work similarly
3. **TeXML bins** are hosted XML snippets — useful for simple flows or emergency forwarding
4. **Migration from Twilio is mostly 1:1** but watch for auth, webhook params, and voice name differences
5. **If the webhook URL is down, the call fails** — always have a fallback plan
6. **Debug by curling the customer's webhook** — most TeXML issues are bad XML or server errors
7. **Gather requires proper DTMF setup** — RFC 2833 must be negotiated in SIP

---

**Next: Lesson 190 — Microsoft Teams and Zoom Phone Integration**
