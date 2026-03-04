# Lesson 63: SIP Multiparty — Conferencing and the Focus Model

**Module 1 | Section 1.16 — SIP Multiparty: Conferencing and the Focus Model**
**⏱ ~6min read | Prerequisites: Lesson 42, Lesson 59**

---

## 1. Introduction to SIP Conferencing

Conferencing is a fundamental feature of modern unified communications, enabling multiple participants to join a single conversation. Unlike simple two-party calls, conferences require specialized handling of media mixing, participant management, and signaling coordination.

In SIP, conferencing is modeled using the concept of a **Focus**, defined in RFC 4353. A Focus is a SIP User Agent (UA) that maintains a dialog with each participant in a conference and coordinates the conference state. This centralized model separates the concerns of signaling management from media handling.

Conferences can be broadly categorized by their architecture:

- **Mesh/Multicast**: Each participant sends media to all other participants directly
- **Centralized**: A dedicated conference bridge (mixer) handles all media
- **Hybrid**: Point-to-multipoint distribution with selective forwarding

The centralized model with a conference bridge is the most common implementation in enterprise and carrier environments due to its scalability and ease of management.

---

## 2. The Focus Model

The Focus model, defined in RFC 4353 and extended by RFC 4579, provides a framework for representing conference state and management in SIP.

### Focus UA vs Participant

A conference involves two types of entities:

**Focus UA (Conference Server)**:
- Maintains a separate dialog with each participant
- Manages conference membership and state
- Coordinates media mixing or switching
- Handles signaling for joining, leaving, and modifying conferences

**Participants**:
- Are standard SIP UAs (phones, soft clients)
- Have a single dialog with the Focus
- Send and receive media through the conference bridge
- Subscribe to conference state for participant information

```
                    +------------------+
                    |   Focus UA       |
                    | (Conference      |
                    |   Server)        |
                    +--------+---------+
                             |
            +----------------+----------------+
            |                |                |
    Dialog 1|         Dialog 2|         Dialog 3|
            |                |                |
      +-----+-----+    +-----+-----+    +-----+-----+
      | Participant|    | Participant|    | Participant|
      |     A      |    |     B      |    |     C      |
      +------------+    +------------+    +------------+
```

### The Conference URI

Each conference has a unique Conference URI that participants use to join:

```
sip:conf-12345@conference.example.com
sip:12345@conf.telnyx.com;transport=tls
sip:weekly-sales-meeting@meetings.company.com
```

When a participant sends an INVITE to the Conference URI, the Focus creates a new dialog and adds the participant to the conference.

---

## 3. Mixing vs Switching Architecture

Conference bridges can handle media through two primary mechanisms: mixing and switching. Understanding the difference is crucial for capacity planning and troubleshooting.

### Mixing Architecture (Audio Bridge)

In a mixing architecture, the bridge receives audio streams from all participants, mixes them together, and sends the mixed stream back to each participant.

```
Participant A audio ----\
Participant B audio -----> [Audio Bridge] ----> Mixed audio to A
Participant C audio ----/                      Mixed audio to B
                                               Mixed audio to C
```

**Advantages**:
- Works with any SIP endpoint
- No special requirements on participant devices
- Handles heterogeneous codecs uniformly

**Disadvantages**:
- Higher CPU utilization (decode + mix + encode)
- Latency introduced by mixing
- Limited scalability per bridge instance

### Switching Architecture (Video Selective Forwarding)

In a switching architecture (common in video conferences), the bridge forwards selected streams without decoding/mixing. Each participant receives multiple individual streams.

```
Participant A video ----\
Participant B video -----> [Video SFU] ----> B's video to A, C's video to A
Participant C video ----/                    A's video to B, C's video to B
                                             A's video to C, B's video to C
```

**Advantages**:
- Lower latency (no decoding/encoding)
- Better video quality (no transcoding loss)
- Higher scalability

**Disadvantages**:
- Requires more bandwidth on participant side
- Participant device must handle multiple streams
- Some devices may not support receiving multiple video streams

### Hybrid Approaches

Modern conference systems often use hybrid approaches:
- Audio is mixed (lower bandwidth, universal compatibility)
- Video is switched using Selective Forwarding Units (SFUs)
- Presentation streams may be handled separately

---

## 4. Joining and Creating Conferences

### Creating a New Conference

There are several methods to create conferences in SIP:

**1. Pre-provisioned Conferences**:
Conferences are created in advance with a known URI.

```
INVITE sip:conf-12345@conference.example.com SIP/2.0
Via: SIP/2.0/TLS 192.168.1.100:5061;branch=z9hG4bKx123
From: <sip:user@example.com>;tag=xy123
To: <sip:conf-12345@conference.example.com>
Call-ID: conference-join@192.168.1.100
CSeq: 1 INVITE
Contact: <sip:user@192.168.1.100:5061;transport=tls>
Content-Type: application/sdp
Content-Length: 147

v=0
o=user 12345 12345 IN IP4 192.168.1.100
s=Conference Join
c=IN IP4 192.168.1.100
t=0 0
m=audio 10000 RTP/AVP 0 8 101
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:101 telephone-event/8000
```

**2. Ad-hoc Conferencing (RFC 4579)**:
Using the `isfocus` feature tag to indicate conference creation intent.

```
INVITE sip:carol@chicago.example.com SIP/2.0
Via: SIP/2.0/UDP alice.example.com:5060;branch=z9hG4bK123
From: <sip:alice@example.com>;tag=abc123
To: <sip:carol@chicago.example.com>
Call-ID: adhoc-conf@alice.example.com
CSeq: 1 INVITE
Contact: <sip:alice@example.com;isfocus>
Subject: Starting conference
Content-Type: application/sdp
Content-Length: 142

v=0
o=alice 2890844526 2890844527 IN IP4 alice.example.com
s=Ad-hoc Conference
c=IN IP4 alice.example.com
t=0 0
m=audio 49172 RTP/AVP 0
a=rtpmap:0 PCMU/8000
```

The `isfocus` parameter in the Contact header indicates that Alice's UA is acting as a Focus.

**3. Three-way Calling via REFER to Join**:
Combining existing calls into a conference using REFER.

### Joining an Existing Conference

Once a conference exists, participants join by INVITE to the conference URI:

```
INVITE sip:weekly-sales@conference.company.com SIP/2.0
Via: SIP/2.0/TLS participant.example.com:5061;branch=z9hG4bKjoin1
From: <sip:employee@company.com>;tag=join123
To: <sip:weekly-sales@conference.company.com>
Call-ID: join-conf@participant.example.com
CSeq: 1 INVITE
Contact: <sip:employee@participant.example.com;transport=tls>
Content-Type: application/sdp
Content-Length: 150

v=0
o=employee 54321 54321 IN IP4 participant.example.com
s=Joining Sales Meeting
c=IN IP4 participant.example.com
t=0 0
m=audio 20000 RTP/AVP 0 8 101
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:101 telephone-event/8000
a=sendrecv
```

---

## 5. Conference State with SUBSCRIBE/NOTIFY

Participants and administrators often need real-time information about conference state: who's in the conference, who's speaking, and conference capabilities. RFC 4575 defines a conference event package for this purpose.

### Subscribing to Conference State

```
SUBSCRIBE sip:sales-meeting@conference.example.com SIP/2.0
Via: SIP/2.0/TLS client.example.com:5061;branch=z9hG4bKsub1
From: <sip:admin@example.com>;tag=sub123
To: <sip:sales-meeting@conference.example.com>
Call-ID: conf-sub@client.example.com
CSeq: 1 SUBSCRIBE
Contact: <sip:admin@client.example.com;transport=tls>
Event: conference
Accept: application/conference-info+xml
Expires: 3600
Content-Length: 0
```

```
SIP/2.0 200 OK
Via: SIP/2.0/TLS client.example.com:5061;branch=z9hG4bKsub1
From: <sip:admin@example.com>;tag=sub123
To: <sip:sales-meeting@conference.example.com>;tag=conf-focus1
Call-ID: conf-sub@client.example.com
CSeq: 1 SUBSCRIBE
Contact: <sip:focus@conference.example.com;transport=tls>
Expires: 3600
Content-Length: 0
```

### Conference State Notification

The Focus sends NOTIFY with conference state updates:

```
NOTIFY sip:admin@client.example.com SIP/2.0
Via: SIP/2.0/TLS conference.example.com:5061;branch=z9hG4bKnot1
From: <sip:sales-meeting@conference.example.com>;tag=conf-focus1
To: <sip:admin@example.com>;tag=sub123
Call-ID: conf-sub@client.example.com
CSeq: 1 NOTIFY
Event: conference
Subscription-State: active;expires=3500
Content-Type: application/conference-info+xml
Content-Length: 854

<?xml version="1.0" encoding="UTF-8"?>
<conference-info xmlns="urn:ietf:params:xml:ns:conference-info" 
                 entity="sip:sales-meeting@conference.example.com"
                 state="full" version="1">
  <conference-description>
    <subject>Weekly Sales Meeting</subject>
    <display-text>Sales Team Conference</display-text>
  </conference-description>
  <users state="full">
    <user entity="sip:alice@example.com" state="full">
      <display-text>Alice Johnson</display-text>
      <endpoint entity="sip:alice@192.168.1.10">
        <status>connected</status>
        <joining-method>dialed-in</joining-method>
        <joining-info>
          <when>2024-01-15T09:00:00Z</when>
        </joining-info>
        <media id="1">
          <type>audio</type>
          <label>main-audio</label>
          <src-id>12345</src-id>
          <status>sendrecv</status>
        </media>
      </endpoint>
    </user>
    <user entity="sip:bob@example.com" state="full">
      <display-text>Bob Smith</display-text>
      <endpoint entity="sip:bob@192.168.1.11">
        <status>connected</status>
        <joining-method>invited</joining-method>
        <media id="1">
          <type>audio</type>
          <status>sendrecv</status>
        </media>
      </endpoint>
    </user>
  </users>
</conference-info>
```

🔧 **NOC Tip:** Conference state notifications can generate significant traffic in large conferences. A 50-participant conference sending full state updates to all subscribers creates substantial overhead. Look for configuration options like `partial-state` notifications or throttling mechanisms in your conference server. Some platforms support `application/pidf+xml` for simpler presence-style updates.

---

## 6. Adding and Removing Participants

### Adding a New Participant

The Focus can add participants by sending INVITEs:

```
INVITE sip:newparticipant@example.com SIP/2.0
Via: SIP/2.0/TLS conference.example.com:5061;branch=z9hG4bKadd1
From: <sip:sales-meeting@conference.example.com>;tag=add123
To: <sip:newparticipant@example.com>
Call-ID: add-user@conference.example.com
CSeq: 1 INVITE
Contact: <sip:focus@conference.example.com;isfocus>
Subject: Invitation to Weekly Sales Meeting
Referred-By: <sip:admin@example.com>
Content-Type: application/sdp
Content-Length: 142

v=0
o=focus 0 0 IN IP4 conference.example.com
s=Sales Meeting Invite
c=IN IP4 conference.example.com
t=0 0
m=audio 10000 RTP/AVP 0
a=rtpmap:0 PCMU/8000
```

Alternatively, an existing participant can invite someone using REFER:

```
REFER sip:focus@conference.example.com SIP/2.0
Via: SIP/2.0/TLS participant.example.com:5061;branch=z9hG4bKref1
From: <sip:alice@example.com>;tag=alice123
To: <sip:focus@conference.example.com>;tag=focus456
Call-ID: invite-others@participant.example.com
CSeq: 2 REFER
Refer-To: <sip:newparticipant@example.com>
Referred-By: <sip:alice@example.com>
Content-Length: 0
```

### Removing a Participant

The Focus can terminate a participant's dialog:

```
BYE sip:alice@192.168.1.10:5060 SIP/2.0
Via: SIP/2.0/TLS conference.example.com:5061;branch=z9hG4bKbye1
From: <sip:sales-meeting@conference.example.com>;tag=focus-abc
To: <sip:alice@example.com>;tag=alice-xyz
Call-ID: alice-dialog@conference.example.com
CSeq: 1 BYE
Reason: SIP ;cause=200 ;text="Removed by moderator"
Content-Length: 0
```

Or a participant can leave by sending BYE to the Focus:

```
BYE sip:focus@conference.example.com SIP/2.0
Via: SIP/2.0/TLS participant.example.com:5061;branch=z9hG4bKleave1
From: <sip:alice@example.com>;tag=alice123
To: <sip:focus@conference.example.com>;tag=focus456
Call-ID: alice-dialog@conference.example.com
CSeq: 3 BYE
Content-Length: 0
```

---

## 7. Conference-Specific Features

### Floor Control

Floor control determines who can speak or present in a conference. It's managed through additional protocols like BFCP (Binary Floor Control Protocol) alongside SIP.

### Conference Recording

```
INVITE sip:recorder@recording.example.com SIP/2.0
Via: SIP/2.0/TLS conference.example.com:5061;branch=z9hG4bKrec1
From: <sip:sales-meeting@conference.example.com>;tag=rec123
To: <sip:recorder@recording.example.com>
Call-ID: recording@conference.example.com
CSeq: 1 INVITE
Subject: Recording: Weekly Sales Meeting
Content-Type: application/sdp
Content-Length: 145

v=0
o=focus 0 0 IN IP4 conference.example.com
s=Recording Session
c=IN IP4 conference.example.com
t=0 0
m=audio 15000 RTP/AVP 0
a=rtpmap:0 PCMU/8000
a=label:conference-audio
```

### DTMF Control

Conferences often use DTMF for participant controls:

```
*1 - Mute/unmute self
*2 - Lock/unlock conference
*3 - Eject last participant
*4 - Record start/stop
*5 - Decrease volume
*6 - Increase volume
*# - Roll call (announce participant count)
```

---

## 8. Modern Conference Scenarios

### Video Conferencing with Simulcast

Modern video conferencing uses Simulcast where each participant sends multiple quality layers:

```
m=video 10000 RTP/AVP 96 97 98
a=rtpmap:96 VP8/90000
a=rtpmap:97 VP8/90000
a=rtpmap:98 VP8/90000
a=simulcast:send 1;2;3
a=rid:1 send pt=96;max-width=1280;max-height=720
a=rid:2 send pt=97;max-width=640;max-height=360
a=rid:3 send pt=98;max-width=320;max-height=180
```

The SFU forwards the appropriate quality layer to each receiver based on their bandwidth.

### Large Conferences (Webinar Mode)

For large conferences (100+ participants), the architecture changes:

- **Presenter mode**: 1-3 presenters send audio/video, audience receives only
- **Moderated Q&A**: Audience members can request to speak
- **Breakout rooms**: Sub-conferences created from main conference

### Conferencing Troubleshooting Commands

```bash
# Monitor conference participants
sngrep -r -k INVITE,BYE,NOTIFY port 5060 | grep "conference.example.com"

# Check conference state subscriptions
tshark -r conference.pcap -Y "sip.Event == \"conference\""

# Analyze media streams in conference
rtpstat -f conference.pcap

# Check for DTMF events during conference
tshark -r conference.pcap -Y "rtp.event"
```

---

## 9. Key Takeaways

1. **Focus Model**: Conferences use a Focus UA that maintains separate dialogs with each participant, handling signaling coordination while media is processed by a bridge.

2. **Mixing vs Switching**: Audio conferences typically use mixing (decoding, mixing, encoding), while video conferences often use switching/SFU (forwarding selected streams) for scalability.

3. **Conference URI**: Each conference has a unique URI that participants use to join via INVITE. The Focus responds and creates a dedicated dialog for each participant.

4. **State Notifications**: Use SUBSCRIBE with Event: conference to receive participant lists and status updates via NOTIFY with application/conference-info+xml bodies.

5. **Adding Participants**: New participants join by INVITE to the Conference URI, or can be added by the Focus sending INVITEs or via REFER from existing participants.

6. **Leaving Conferences**: Participants exit by sending BYE to the Focus, or the Focus can remove participants by terminating their dialog.

7. **Scalability Considerations**: Consider the trade-offs between mixing quality and CPU load, SUBSCRIBE/NOTIFY overhead, and Simulcast for video bandwidth optimization.

8. **DTMF Control**: Most conference systems use DTMF codes for participant self-service features like mute, volume control, and recording.

---

Next: Lesson 61 — SIP Identity and Security Fundamentals
