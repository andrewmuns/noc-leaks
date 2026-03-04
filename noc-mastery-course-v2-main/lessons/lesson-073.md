# Lesson 73: TeXML — TwiML-Compatible Voice Scripting

**Module 2 | Section 2.3 — TeXML**
**⏱ ~7 min read | Prerequisites: Lesson 60**

---

## A Different Programming Model: Documents Instead of Commands

Call Control (Lessons 60-62) uses a command-based model: events arrive as webhooks, your app responds with API commands. TeXML flips this: instead of issuing commands, your application **returns an XML document** that describes what should happen. Telnyx fetches this document and executes it.

This is the same model Twilio popularized with TwiML, and TeXML is designed to be compatible — allowing customers to migrate from Twilio with minimal code changes. Understanding both models matters for NOC engineers because you'll encounter both in customer issues.

## How TeXML Works End-to-End

1. A call arrives at Telnyx for a number configured with a TeXML Application
2. The TeXML Application has a configured **Voice URL** (the customer's HTTP endpoint)
3. Telnyx sends an HTTP request (GET or POST) to that URL with call details (From, To, CallSid, etc.)
4. The customer's server responds with an XML document containing TeXML verbs
5. Telnyx parses the XML and executes each verb sequentially
6. When execution completes (or a verb redirects), Telnyx fetches a new document

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">Welcome to Acme Corp. Please hold while we connect you.</Say>
  <Play>https://example.com/hold-music.mp3</Play>
  <Dial callerId="+15551234567">
    <Number>+15559876543</Number>
  </Dial>
</Response>
```

This document says: speak a greeting, play hold music, then dial a number. Each verb maps to internal Call Control operations.

## Key TeXML Verbs and Their SIP/RTP Reality

### `<Say>` — Text-to-Speech

Maps to the `speak` Call Control command internally. The `voice` attribute selects the TTS voice. Telnyx synthesizes the text to audio, transcodes to the call's negotiated codec, and injects into the RTP stream.

### `<Play>` — Audio File Playback

Maps to `play_audio`. Same requirements: the URL must be accessible from Telnyx infrastructure. Supports WAV, MP3, and other common formats.

### `<Gather>` — Collect User Input

The most complex verb. Combines audio playback (nested `<Say>` or `<Play>`) with DTMF/speech detection.

```xml
<Gather input="dtmf speech" timeout="5" numDigits="1" action="/handle-input">
  <Say>Press 1 for sales, 2 for support, or say your request.</Say>
</Gather>
```

When the caller provides input, Telnyx makes a new HTTP request to the `action` URL with the collected input. The customer's server responds with a new TeXML document for the next step.

🔧 **NOC Tip:** Gather issues are the most common TeXML debugging scenario. If digits aren't being collected, check: (1) Is the DTMF method configured correctly on the SIP trunk? (2) Is the `input` attribute set to include "dtmf"? (3) Is the `timeout` long enough? (4) Is the `action` URL reachable?

### `<Dial>` — Connect to Another Party

Initiates an outbound call and bridges it with the current caller. This is the TeXML equivalent of using Call Control to create an outbound call and then bridge the two legs.

```xml
<Dial timeout="30" callerId="+15551234567">
  <Number>+15559876543</Number>
  <Sip>sip:agent@customer-pbx.com</Sip>
</Dial>
```

`<Dial>` can contain `<Number>` (PSTN), `<Sip>` (SIP URI), `<Client>` (WebRTC), or `<Conference>` (multi-party).

### `<Record>` — Call Recording

Starts recording the call audio. The recording URL is delivered via a webhook to the `recordingStatusCallback` URL when complete.

### `<Conference>` — Multi-Party Calling

Inside `<Dial>`, `<Conference>` joins the caller into a named conference room. Multiple callers dialing into the same conference name are mixed together.

### `<Redirect>` — Fetch New Instructions

Tells Telnyx to immediately fetch a new TeXML document from the specified URL. Used for dynamic call flow branching.

### `<Hangup>` — End the Call

Sends SIP BYE and terminates the call.

## TeXML vs. Call Control: When to Use Each

| Aspect | TeXML | Call Control |
|--------|-------|-------------|
| Programming model | Synchronous document return | Async command/webhook loop |
| Complexity | Simpler for basic IVRs | Better for complex stateful apps |
| Migration from Twilio | Direct compatibility | Requires rewrite |
| Real-time control | Limited (document-based) | Full (individual commands) |
| Debugging | Check XML responses | Check webhook/command logs |

## How TeXML Maps to Call Control Internally

This is key for NOC debugging. TeXML is **not a separate system** — it's a translation layer on top of Call Control. The TeXML interpreter:

1. Fetches the XML document from the customer's URL
2. Parses the verbs
3. Translates each verb into Call Control commands
4. Executes them sequentially
5. When a verb has an `action` URL, fetches the next document

This means TeXML issues show up in the same Call Control logs and Grafana dashboards. The TeXML layer adds potential failure points:
- Fetching the XML document (same issues as webhook delivery — Lesson 62)
- Parsing the XML (malformed XML)
- Interpreting verb attributes (invalid parameters)

🔧 **NOC Tip:** When debugging TeXML issues, check two layers: (1) Was the XML document fetched successfully? (Graylog: search for the TeXML application's voice URL requests) (2) Were the translated Call Control commands executed successfully? (Graylog: search by Call Control ID for command execution logs)

## Twilio Migration Compatibility and Gotchas

TeXML aims for TwiML compatibility, but there are differences:

1. **Verb support:** Most common verbs are supported, but some Twilio-specific extensions may not be
2. **URL parameters:** The HTTP request parameters sent to the voice URL are similar but not identical
3. **Recording formats:** File format and delivery mechanism may differ
4. **Status callbacks:** Timing and payload of status callbacks may vary
5. **SIP headers:** Custom SIP header passthrough syntax may differ

When a Twilio migration customer reports "it worked on Twilio but doesn't work here," the issue is usually in these subtle differences.

## Troubleshooting Scenario: "IVR Plays Greeting Then Goes Silent"

A customer migrated from Twilio. Their IVR plays the initial greeting (`<Say>`) but then goes silent — the `<Gather>` doesn't seem to work.

**Investigation:**
1. Graylog: Search for the TeXML voice URL fetch → Found: initial fetch succeeds, returns valid XML with `<Gather>` containing an `action` URL
2. Check if DTMF input was detected → No DTMF events in logs
3. Check SIP trunk configuration → DTMF method set to "SIP INFO" but customer's PBX sends RFC 2833
4. The `<Gather>` verb was working, but DTMF detection wasn't receiving any digits because of the method mismatch
5. Changed DTMF method to RFC 2833 on the connection → IVR works

The Twilio setup had auto-detected DTMF method. Telnyx requires explicit configuration.

---

**Key Takeaways:**
1. TeXML is a TwiML-compatible XML scripting layer that sits on top of Call Control
2. The execution model is document-based: Telnyx fetches XML, executes verbs, fetches more XML
3. Each TeXML verb maps to internal Call Control commands — same debugging tools apply
4. `<Gather>` is the most common troubleshooting target — DTMF method, timeout, and action URL issues
5. Twilio migration issues usually stem from subtle differences in parameter names, callback formats, or SIP configuration
6. Debug at two layers: XML document fetch (HTTP level) and command execution (Call Control level)

**Next: Lesson 64 — Telnyx WebRTC Architecture: Voice SDK and Proxy**
