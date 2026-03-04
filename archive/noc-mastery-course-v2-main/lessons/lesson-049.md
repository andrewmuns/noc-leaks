# Lesson 49: Call Hold, Resume, and Re-INVITE
**Module 1 | Section 1.11 — SIP Call Flows**
**⏱ ~6 min read | Prerequisites: Lesson 44**

---

## Modifying a Call in Progress

A SIP call isn't static. After the initial INVITE/200/ACK establishes the session, either party may need to change it: put the call on hold, change codecs, add video, or update media addresses. The **re-INVITE** is SIP's mechanism for modifying an active session.

A re-INVITE is simply an INVITE sent *within an existing dialog*. It carries a new SDP offer that proposes changes to the session. The other party responds with a new SDP answer, and the session is updated.

---

## Call Hold

### How Hold Works

When Alice puts Bob on hold, her phone sends a re-INVITE with modified SDP:

```
Alice                    Telnyx B2BUA                    Bob
  |------- re-INVITE ------>|                            |
  | (a=sendonly)             |------- re-INVITE --------->|
  |                          | (a=sendonly)               |
  |                          |<------ 200 OK -------------|
  |<------ 200 OK ----------|  (a=recvonly)               |
  |------- ACK ------------->|------- ACK --------------->|
  |                          |                            |
  |  (Hold music plays)      |======= RTP (music) ======>|
```

The SDP direction attributes signal the hold state:

| Attribute | Meaning |
|-----------|---------|
| `a=sendrecv` | Normal bidirectional media (default) |
| `a=sendonly` | I will send but not receive — **hold** (I'm sending hold music) |
| `a=recvonly` | I will receive but not send — response to `sendonly` |
| `a=inactive` | No media in either direction — **silent hold** |

### sendonly vs. inactive

The choice between `sendonly` and `inactive` depends on whether the holding party plays hold music:
- **`sendonly`**: "I'll send you hold music, but I'm not listening to you" — the common case
- **`inactive`**: "Complete silence in both directions" — used when the PBX plays hold music locally or not at all

🔧 **NOC Tip:** If a customer reports "no hold music," check the SDP direction attribute. If the re-INVITE uses `a=inactive`, no media flows in either direction — the PBX might be playing hold music locally to the holder but not sending anything to the held party. If `a=sendonly` but still no music, the RTP stream exists but might not contain actual music (check the PBX hold music configuration).

---

## Call Resume

Resume is the reverse: another re-INVITE that restores `a=sendrecv`:

```
Alice                    Telnyx B2BUA                    Bob
  |------- re-INVITE ------>|                            |
  | (a=sendrecv)             |------- re-INVITE --------->|
  |                          | (a=sendrecv)               |
  |                          |<------ 200 OK -------------|
  |<------ 200 OK ----------|  (a=sendrecv)               |
  |------- ACK ------------->|------- ACK --------------->|
  |                          |                            |
  |<======== RTP ==========>|<======== RTP ============>|
```

Both sides are back to normal bidirectional media.

---

## Other Re-INVITE Use Cases

### Codec Change
A re-INVITE can propose different codecs mid-call. Common scenario: the call started with G.711 (good quality, high bandwidth), but network conditions degraded, so a re-INVITE proposes switching to G.729 (lower bandwidth). The answerer can accept or reject the change.

### Adding Video
A voice call can add video by including a new `m=video` media line in the re-INVITE SDP. The answerer accepts (with their video parameters) or rejects (by setting the video port to 0).

### IP Address Change
If an endpoint's IP changes mid-call (mobile network handover, VPN reconnect), a re-INVITE with the new connection address (c= line) updates the media path.

### Session Timer Refresh
RFC 4028 defines session timers — periodic re-INVITEs (or UPDATEs) to confirm both sides are still alive. This prevents ghost calls (Lesson 41). The `Session-Expires` header defines the interval, and the `refresher` parameter determines which side sends the refresh.

---

## The Glare Problem

**Glare** occurs when both sides send a re-INVITE simultaneously. Neither side has received the other's re-INVITE yet, so both think they're modifying the session.

```
Alice ---re-INVITE---> <---re-INVITE--- Bob
        (GLARE!)
```

SIP handles this with **491 Request Pending** — when a UAS receives a re-INVITE while its own re-INVITE is pending, it responds 491. The rules:

- The **owner of the Call-ID** (the party that generated it — the original caller) waits 2.1-4 seconds before retrying
- The **non-owner** waits 0-2 seconds before retrying

This ensures they don't retry at the same time, resolving the glare.

🔧 **NOC Tip:** Repeated 491 responses in a SIP trace indicate glare. Usually self-resolving, but if you see persistent 491 loops (dozens of retries), one side's timer implementation is broken — they're retrying at the same interval. Check for buggy firmware versions.

---

## The UPDATE Method

**UPDATE** (RFC 3311) is an alternative to re-INVITE for modifying sessions. The key difference: UPDATE can modify a session *before* it's fully established (during early dialog), while re-INVITE can only modify confirmed dialogs.

Use cases for UPDATE:
- Changing codecs during early media (before 200 OK)
- Session timer refresh (less overhead than re-INVITE)
- Updating preconditions

UPDATE is simpler than re-INVITE — it doesn't involve the three-way handshake, just a request-response. However, not all endpoints support it.

---

## B2BUA Considerations

In Telnyx's B2BUA architecture, re-INVITEs on one leg may need to be relayed to the other leg. The B2BUA decides:

- **Hold/Resume:** Usually relayed — if Alice holds, Bob should know (and hear hold music or silence)
- **Codec change:** May or may not be relayed — the B2BUA might handle transcoding on one leg without changing the other
- **Session timer refresh:** Handled independently on each leg — the B2BUA maintains separate timers
- **IP change:** Not relayed — the B2BUA is the media anchor, so the other leg doesn't care

This independence is a key advantage: a re-INVITE failure on one leg doesn't necessarily affect the other.

---

## Real-World Troubleshooting Scenario

**Problem:** Customers report that after resuming from hold, they can hear the other party but the other party can't hear them (one-way audio post-resume).

**Investigation:**
1. SIP trace shows: re-INVITE (hold, `a=sendonly`) → 200 OK → ACK → ... → re-INVITE (resume, `a=sendrecv`) → 200 OK → ACK
2. The resume re-INVITE's SDP shows a *different* media port than the original
3. The far-end firewall had opened a pinhole for the original port, but the new port isn't in the firewall's state table
4. RTP from the resuming party is blocked by the far-end firewall

**Root cause:** Changing media ports on resume is technically valid but breaks through restrictive firewalls that track port bindings.

**Fix:** Configure the endpoint to reuse the same media port across re-INVITEs (most SIP stacks support this). Alternatively, ensure the firewall or SBC tracks SDP changes and updates its pinholes dynamically.

---

**Key Takeaways:**
1. Re-INVITE modifies an active session — used for hold, resume, codec changes, and session refresh
2. Hold is signaled by changing SDP direction: `a=sendonly` (hold with music) or `a=inactive` (silent hold)
3. Resume restores `a=sendrecv` for normal bidirectional media
4. Glare (simultaneous re-INVITEs) is resolved with 491 Request Pending and staggered retry timers
5. UPDATE can modify sessions before they're established (early dialog) — re-INVITE cannot
6. Session timers (periodic re-INVITE/UPDATE) prevent ghost calls by confirming both sides are alive
7. Changing media ports during re-INVITE can break firewall pinholes — prefer port reuse

**Next: Lesson 48 — SDP Structure — Offer/Answer Model**
