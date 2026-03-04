---
title: "Call Transfer — REFER and Replaces"
description: "Learn about call transfer — refer and replaces"
module: "Module 1: Foundations"
lesson: "48"
difficulty: "Advanced"
duration: "7 minutes"
objectives:
  - Understand Blind transfer uses REFER with a simple Refer-To target — the B2BUA calls the target and bridges to the existing party
  - Understand Attended transfer uses REFER with a Replaces parameter — connecting an existing consultation call to the held party
  - Understand NOTIFY messages report transfer progress using SIP fragments — check these to determine why transfers fail
  - Understand Transfer is the most common SIP interoperability problem — vendor implementations vary significantly
  - Understand In B2BUA architectures, the B2BUA handles the transfer internally — media re-bridging is critical
slug: "call-transfer"
---

## Why Transfers Are Complex

Call transfer seems simple: move a call from one person to another. But in SIP's distributed architecture, it's surprisingly complex. There's no central switch that can just "reconnect the wires." Instead, transfer involves coordinating multiple independent SIP dialogs, each with their own state, and getting them to stitch together seamlessly.

Transfer is also the SIP feature most likely to break across different vendor implementations. The spec is clear, but edge cases abound.

---

## Blind Transfer (Unattended Transfer)

Alice is talking to Bob. Alice wants to transfer Bob to Carol without talking to Carol first.

### The REFER Method

```
Alice                    Telnyx B2BUA                    Bob
  |<======== RTP ==========>|<======== RTP ============>|
  |                          |                            |
  |------- REFER ----------->|                            |
  | Refer-To: carol@...      |                            |
  |<------ 202 Accepted -----|                            |
  |                          |                            |
  |                          |------- INVITE ------------>| Carol
  |                          |<------ 200 OK -------------|
  |                          |------- ACK --------------->|
  |                          |                            |
  |<------ NOTIFY -----------|                            |
  | (sipfrag: SIP/2.0 200)   |                            |
  |------- 200 OK (NOTIFY)->|                            |
  |                          |                            |
  |------- BYE ------------->|  (Alice disconnects)       |
  |<------ 200 OK -----------|                            |
```

**Step by step:**
1. Alice sends **REFER** within the existing dialog to Telnyx, with `Refer-To: <sip:carol@example.com>` header
2. Telnyx responds **202 Accepted** — "I'll try to do what you asked"
3. Telnyx creates a **new INVITE** to Carol (this is a new call leg)
4. Telnyx bridges Bob's existing media to Carol's new media
5. Telnyx sends **NOTIFY** to Alice reporting the outcome (using SIP fragment — the response code from the INVITE to Carol)
6. Alice hangs up (BYE)

The **NOTIFY** messages use the "refer" event package — they carry SIP fragments that tell Alice whether the transfer succeeded or failed. The `sipfrag` body might contain `SIP/2.0 180 Ringing` (transfer in progress) or `SIP/2.0 200 OK` (transfer succeeded).

### B2BUA Transfer Handling

In Telnyx's B2BUA model, transfers are handled internally. The B2BUA receives the REFER, creates the new call to Carol, and re-bridges the media paths. The customer's PBX doesn't need to know about the B2BUA's internal routing — it just sends REFER and gets NOTIFY updates.
slug: "call-transfer"
---

## Attended Transfer (Consultative Transfer)

Alice is talking to Bob. Alice puts Bob on hold, calls Carol to discuss the transfer, then connects Bob and Carol.

### The Flow

```
Phase 1: Alice holds Bob, calls Carol
  Alice ---hold (re-INVITE a=sendonly)---> Telnyx <---> Bob (on hold)
  Alice ---INVITE---> Carol (new dialog)
  Alice <---200 OK--- Carol
  (Alice talks to Carol)

Phase 2: Alice transfers
  Alice ---REFER---> Telnyx (on Alice-Bob dialog)
    Refer-To: <carol@...?Replaces=dialog-id>
  Telnyx bridges Bob <---> Carol
  Alice ---BYE---> (disconnects from both)
```

The key difference from blind transfer is the **Replaces** header parameter in the Refer-To URI. This tells Telnyx: "Don't create a new call to Carol — take the *existing* call with Carol and connect it to Bob."

### The Replaces Header

`Replaces` identifies an existing dialog by its Call-ID, From-tag, and To-tag:
```
Refer-To: <sip:carol@example.com?Replaces=call-id%3Bto-tag%3Dx%3Bfrom-tag%3Dy>
```

When Telnyx receives this REFER, it:
1. Finds the existing dialog with Carol (identified by the Replaces parameters)
2. Sends a new INVITE to Carol with a `Replaces` header pointing to the existing dialog
3. Carol's UA replaces the old dialog with the new one
4. Telnyx bridges Bob and Carol's media

> **💡 NOC Tip:** tended transfer failures often come from URL encoding issues in the `Replaces` header. The Call-ID, semicolons, and tags must be properly escaped. If transfers work for blind but fail for attended, check the REFER message for properly encoded Replaces parameters.

---

## Transfer Failures: What Goes Wrong

### Common Failure Modes

| Symptom | Likely Cause |
|---------|-------------|
| REFER gets 403 | Transfer not permitted by policy or configuration |
| REFER gets 501 | The UAS doesn't support REFER |
| NOTIFY shows 4xx/5xx | The new INVITE to the transfer target failed |
| Transfer completes but no audio | Media re-bridging failed — SDP negotiation issue on new leg |
| One party hears silence after transfer | Hold resume failed, or media path not updated |
| Transfer to external number fails | B2BUA routing issue for the new outbound call |

### Interoperability Issues

Transfer is the #1 interop headache in SIP. Different vendors implement REFER differently:
- Some PBXes send REFER to the B2BUA (correct)
- Some try to send REFER directly to the remote party (doesn't work through a B2BUA)
- Some don't support the `Replaces` mechanism for attended transfer
- Some expect the transferor to stay on the call until the transfer completes; others disconnect immediately

> **💡 NOC Tip:** en a customer reports "transfers don't work," first determine the transfer type (blind vs. attended) and the phone model/PBX vendor. Then check:
1. Is REFER being sent? (Some phones use a proprietary method instead)
2. Is the Refer-To URI correct? (Does it contain the right target?)
3. What does the NOTIFY sequence show? (Did the new INVITE succeed?)
4. Is media flowing after transfer? (Check RTP streams post-transfer)
slug: "call-transfer"
---

## Transfer in Telnyx's Architecture

Because Telnyx operates as a B2BUA, it has unique advantages for handling transfers:

1. **Topology hiding:** Neither party sees the other's real address during or after transfer
2. **Media continuity:** Telnyx can maintain media anchoring through the transfer, preventing audio gaps
3. **CDR accuracy:** Telnyx can properly track the transfer for billing — the original call, the consultation call (if attended), and the resulting connected call
4. **Feature injection:** Telnyx can add hold music during the transfer setup phase

However, the B2BUA must correctly correlate the REFER with the target dialog (for attended transfer) and properly re-bridge media paths. Bugs in this correlation logic cause failed transfers.

---

## Real-World Scenario

**Problem:** A call center using Telnyx SIP trunking reports that attended transfers to external numbers work, but attended transfers between internal extensions fail with the callee hearing silence.

**Investigation:**
1. SIP traces show REFER with Replaces is being sent correctly
2. The new INVITE to the target extension succeeds (200 OK)
3. RTP analysis shows media flowing from the transferred party but not reaching the target
4. The SDP in the new INVITE contains the B2BUA's media address, but the internal PBX is trying to send media directly (bypassing the B2BUA)
5. The PBX has "direct media" or "media bypass" enabled for internal calls

**Root cause:** The PBX is configured to send RTP directly between extensions (bypassing SIP proxy/B2BUA). After transfer, the B2BUA's media address in the SDP doesn't match where the PBX sends RTP.

**Fix:** Disable direct media for calls involving external trunks, or ensure the PBX routes all media through its own media engine when Telnyx trunks are involved.
slug: "call-transfer"
---

**Key Takeaways:**
1. Blind transfer uses REFER with a simple Refer-To target — the B2BUA calls the target and bridges to the existing party
2. Attended transfer uses REFER with a Replaces parameter — connecting an existing consultation call to the held party
3. NOTIFY messages report transfer progress using SIP fragments — check these to determine why transfers fail
4. Transfer is the most common SIP interoperability problem — vendor implementations vary significantly
5. In B2BUA architectures, the B2BUA handles the transfer internally — media re-bridging is critical
6. Replaces header encoding issues are a frequent cause of attended transfer failures
7. "Direct media" PBX configurations often conflict with B2BUA-mediated transfers

**Next: Lesson 47 — Call Hold, Resume, and Re-INVITE**
