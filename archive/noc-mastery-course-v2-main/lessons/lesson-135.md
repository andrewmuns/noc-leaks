# Lesson 135: Reading PCAPs — Wireshark for SIP and RTP

**Module 4 | Section 4.4 — Network Debug**
**⏱ ~9 min read | Prerequisites: Lessons 29, 39, 48**

---

Packet captures (PCAPs) are the ultimate source of truth for network troubleshooting. When everything else fails — when logs don't match symptoms, when metrics don't explain behavior — a packet capture shows exactly what was on the wire. This lesson teaches how to capture, analyze, and interpret SIP and RTP traffic using tcpdump and Wireshark.

## Capturing Traffic with tcpdump

Before you can analyze packets, you need to capture them. On Linux servers, tcpdump is the standard tool:

### Basic Capture Commands

```bash
# Capture all traffic on interface eth0
tcpdump -i eth0

# Capture to file (for Wireshark analysis)
tcpdump -i eth0 -w capture.pcap

# Filter for SIP (port 5060)
tcpdump -i eth0 port 5060 -w sip-capture.pcap

# Filter for SIP and RTP (port 5060 and 10000-20000 range)
tcpdump -i eth0 -w capture.pcap \(port 5060 or udp portrange 10000-20000\)

# Filter by host
tcpdump -i eth0 host 203.0.113.50 -w host-capture.pcap

# Capture with full payload (don't truncate)
tcpdump -i eth0 -s0 -w full-capture.pcap

# Limit capture size (stop after 100MB)
tcpdump -i eth0 -w capture.pcap -C 100
```

### Capturing During Incidents

During active incidents, capturing without filtering can fill disk quickly. Balance completeness with practicality:

```bash
# Capture SIP signaling + 60 seconds of RTP per call
# (requires scripting to detect call start/end)

# For manual capture: start capture, reproduce issue, stop
tcpdump -i eth0 port 5060 -w issue-capture.pcap
# ... reproduce the issue ...
# Ctrl+C to stop
```

🔧 **NOC Tip:** When capturing RTP for audio quality investigation, capture at least 60 seconds of audio on each side. RTP statistics (loss, jitter) are meaningless on very short captures. Also, capture on the media server or SBC — capturing on the SIP proxy shows signaling but not media.

## Opening PCAPs in Wireshark

Transfer the capture file to your workstation and open in Wireshark:

```bash
scp server:/tmp/capture.pcap .
wireshark capture.pcap
```

Wireshark's interface has three panes:
1. **Packet list**: All captured packets
2. **Packet details**: Expanded view of selected packet
3. **Packet bytes**: Raw hex/ASCII

## Wireshark Display Filters for SIP

Display filters show only matching packets:

```
# All SIP traffic
sip

# SIP by method
sip.Method == "INVITE"
sip.Method == "BYE"
sip.Method == "REGISTER"

# SIP by response code
sip.Status-Code == 200
sip.Status-Code == 503
sip.Status-Code >= 400

# SIP by Call-ID
sip.Call-ID contains "abc123"

# SIP errors only
sip.Status-Code >= 400

# INVITEs with specific From header
sip.From contains "+15551234567"

# Combined filters
sip.Method == "INVITE" && sip.Status-Code == 200
```

### Finding a Specific Call

1. Use the filter: `sip.Call-ID contains "call-id-value"`
2. This shows all SIP messages for that call
3. Right-click any packet → "Follow" → "UDP Stream" to see the complete dialog

### Flow Graph Visualization

Wireshark can visualize the SIP call flow:

1. Statistics → Flow Graph
2. Select "Limit to display filter" (if you filtered to one call)
3. Choose "Flow type: General Flow" or "TCP Flow"

This shows a visual diagram:
```
Client                    Server
  |  INVITE                 |
  |------------------------>|
  |  100 Trying             |
  |<------------------------|
  |  180 Ringing            |
  |<------------------------|
  |  200 OK                 |
  |<------------------------|
  |  ACK                    |
  |------------------------>|
  |  (RTP media)            |
  |<=======================>|
  |  BYE                    |
  |------------------------>|
  |  200 OK                 |
  |<------------------------|
```

🔧 **NOC Tip:** The Flow Graph feature is invaluable for understanding complex SIP scenarios (forked calls, transfers, re-INVITEs). Visual representation makes patterns obvious that are hard to see in packet lists. Use it to verify the complete call flow matches expectations.

## Analyzing SIP Headers in Detail

Click any SIP packet and expand the "Session Initiation Protocol" section:

**Key headers to examine:**

### Via Headers (Response Routing)
```
Via: SIP/2.0/UDP 10.0.1.5:5060;branch=z9hG4bK-abc123
Via: SIP/2.0/UDP 203.0.113.10:5060;branch=z9hG4bK-def456
```
Each proxy adds a Via. Responses follow the Via chain in reverse order.

### Contact Header (NAT Issue Location)
```
Contact: <sip:user@192.168.1.5:5060>
```
Private IP in Contact = NAT traversal issue (Lessons 26-28).

### SDP Body (Click "Session Description Protocol")
```
v=0
o=- 12345 12345 IN IP4 192.168.1.5
c=IN IP4 192.168.1.5   ← Connection address (check for NAT)
m=audio 10000 RTP/AVP 0 8 18
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:18 G729/8000
```

Check:
- Is `c=` address reachable (not private if calling from outside)?
- Are codecs what you expect?
- Is the port in the expected range?

## Analyzing RTP in Wireshark

RTP packets carry the actual audio. Wireshark can analyze quality:

### Viewing RTP Streams

1. Telephony → RTP → RTP Streams
2. Shows all RTP streams detected in the capture
3. Click a stream → "Analyze" for detailed statistics

### RTP Stream Analysis

The analysis shows:

| Metric | Meaning |
|--------|---------|
| **Packets** | Total RTP packets in stream |
| **Lost** | Packets missing (sequence number gaps) |
| **Out of order** | Packets received after later packets |
| **Jitter (ms)** | Interarrival jitter in milliseconds |
| **Delta max** | Maximum time between packets |
| **Delta mean** | Average time between packets |

### Detecting Packet Loss

Sequence numbers reveal loss:
```
Seq: 100, 101, 102, 105, 106, 107
                  ↑
            Missing 103, 104
```

In Wireshark's RTP analysis, gaps in sequence numbers appear as "Lost packets."

### Detecting Jitter

Jitter = variation in packet interarrival times:
- Ideal: packets arrive exactly 20ms apart (for 20ms packetization)
- Jitter 0ms = perfectly spaced
- Jitter 50ms = significant variation, may cause choppy audio

Jitter >30ms typically causes audible quality issues.

## RTP Player: Listening to Captured Audio

Wireshark can play captured audio (for unencrypted RTP only):

1. Telephony → RTP → RTP Streams
2. Select the stream
3. Click "Analyze"
4. Click "Play" (or "Save" to export audio)

**Limitations:**
- Only works for G.711 (ulaw/alaw) and some other codecs
- SRTP (encrypted) audio can't be played without decryption
- Audio quality in playback reflects actual captured quality (including loss/jitter)

## Using tshark for Command-Line Analysis

For server-side or automated analysis, use tshark (Wireshark's CLI):

```bash
# Count SIP response codes
tshark -r capture.pcap -Y "sip" -T fields -e sip.Status-Code | sort | uniq -c

# Extract all Call-IDs
tshark -r capture.pcap -Y "sip" -T fields -e sip.Call-ID | sort -u

# Find SIP errors
tshark -r capture.pcap -Y "sip.Status-Code >= 400" -T fields -e frame.time -e ip.src -e ip.dst -e sip.Status-Code -e sip.Call-ID

# RTP statistics
tshark -r capture.pcap -Y "rtp" -T fields -e rtp.seq -e rtp.timestamp -e rtp.ssrc

# Extract SDP connection addresses
tshark -r capture.pcap -Y "sdp.connection_info" -T fields -e sdp.connection_info
```

## Real-World Troubleshooting Scenario

**Customer report:** "Calls to carrier X have one-way audio. They hear us, we don't hear them."

**Investigation:**

1. Capture SIP + RTP at our SBC:
```bash
tcpdump -i eth0 "port 5060 or udp portrange 10000-20000" -w oneway.pcap
```

2. Reproduce issue (make test call), stop capture.

3. Open in Wireshark, filter for Call-ID:
```
sip.Call-ID contains "test-call-123"
```

4. Check SDP in 200 OK from carrier:
```
c=IN IP4 203.0.113.50  ← Carrier's media IP
m=audio 20000 RTP/AVP 0
```

5. Check RTP streams:
```
Telephony → RTP → RTP Streams
```

Results:
- Stream 1: Our IP → 203.0.113.50:20000 (outbound) — Packets sent: 500
- Stream 2: ??? → Our IP (inbound) — No packets received

6. Check if we're receiving ANY packets from carrier's IP:
```
ip.src == 203.0.113.50 && rtp
```
Result: No packets.

7. Conclusion: Carrier is not sending RTP to us, OR carrier is sending from a different IP/port than advertised in SDP.

8. Check for "late" RTP arriving from unexpected IPs:
```
rtp && ip.src != 203.0.113.50
```
Result: Nothing.

9. **Root cause:** Carrier's media server isn't sending RTP. This is a carrier-side issue.

10. **Escalate to carrier:** Provide capture showing our INVITE with SDP, their 200 OK with SDP, our RTP to their advertised IP:port, but no RTP received from them.

---

**Key Takeaways:**

1. Capture with tcpdump: `tcpdump -i eth0 port 5060 -w capture.pcap`
2. Wireshark SIP filters: `sip.Method`, `sip.Status-Code`, `sip.Call-ID`
3. Flow Graph (Statistics → Flow Graph) visualizes SIP call flows
4. Check SDP `c=` address for NAT issues (private IPs = problem)
5. RTP Stream Analysis (Telephony → RTP → RTP Streams) shows loss, jitter, and packet counts
6. Packet loss appears as sequence number gaps; jitter as interarrival time variation
7. tshark enables command-line packet analysis for automation or server-side investigation
8. One-way audio diagnosis: capture at both ends, compare RTP streams, check if sender is actually sending

**Next: Lesson 120 — Advanced PCAP Analysis — RTP Quality and Media Issues**
