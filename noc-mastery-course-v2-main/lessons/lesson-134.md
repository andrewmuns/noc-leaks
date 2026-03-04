# Lesson 134: Traceroute and MTR — Deep Dive

**Module 4 | Section 4.4 — Network Debug**
**⏱ ~7 min read | Prerequisites: Lesson 51**

---

Network problems are the root cause of many telecom incidents: latency spikes, packet loss, unreachable destinations. Traceroute and MTR (My Traceroute) are the primary tools for diagnosing network path issues. But these tools have nuances that lead to misinterpretation if not understood. This lesson goes deep into how they work and how to read them correctly.

## How Traceroute Works

Traceroute exploits the TTL (Time To Live) field in IP headers:

1. Send a packet with TTL=1
2. The first router decrements TTL to 0, sends back ICMP Time Exceeded
3. Now you know the first hop's IP address

4. Send a packet with TTL=2
5. The second router decrements to 0, sends back ICMP Time Exceeded
6. Now you know the second hop's IP

7. Continue incrementing TTL until you reach the destination

```bash
traceroute 203.0.113.50

 1  10.0.1.1 (10.0.1.1)  0.5 ms  0.3 ms  0.4 ms
 2  172.16.0.1 (172.16.0.1)  1.2 ms  1.1 ms  1.0 ms
 3  203.0.113.1 (carrier-gw.example.net)  5.3 ms  5.1 ms  5.4 ms
 4  * * *
 5  203.0.113.50 (dest.example.com)  15.2 ms  14.8 ms  15.1 ms
```

Each line shows: hop number, IP/hostname, and three latency samples (three probes per hop).

### The UDP vs. ICMP vs. TCP Variants

**Default traceroute (UDP):**
- Sends UDP packets to high-numbered ports (33434+)
- Most common, works for most networks
- Some firewalls block outbound UDP to unknown ports

**ICMP traceroute (-I flag):**
- Sends ICMP Echo Request (like ping) with incrementing TTL
- Works better through some firewalls
- Some routers prioritize ICMP differently than UDP

**TCP traceroute (-T flag):**
- Sends TCP SYN packets to specified port (default 80)
- Useful when UDP/ICMP are blocked
- Shows path as seen by TCP traffic to that port

```bash
# TCP traceroute to SIP port
traceroute -T -p 5060 carrier.sip.com

# ICMP traceroute
traceroute -I carrier.sip.com
```

🔧 **NOC Tip:** If a standard traceroute shows incomplete paths but you know the destination is reachable, try different traceroute modes. Some networks block UDP traceroute but allow ICMP. Others rate-limit ICMP responses, making hops appear as `* * *`. TCP traceroute to port 5060 shows the path SIP traffic takes, which may differ from the default path.

## The ICMP Rate Limiting Trap

Here's a common misinterpretation:

```
 5  * * *
 6  203.0.113.10  10.2 ms  10.5 ms  10.3 ms
 7  203.0.113.50  15.1 ms  14.9 ms  15.0 ms
```

Hop 5 shows `* * *` — but hops 6 and 7 respond fine. Is hop 5 down?

**Likely: NO.** Many routers rate-limit ICMP Time Exceeded messages. They're too busy forwarding traffic to respond to every traceroute probe. The router at hop 5 is forwarding packets fine (proven by hops 6 and 7 responding), it just didn't bother replying to your diagnostic packets.

**Key insight:** If hops AFTER a non-responding hop DO respond, the non-responding hop is probably fine — just rate-limiting ICMP. If hops after ALSO show loss, then there's real packet loss at that point.

## MTR: Continuous Traceroute with Statistics

MTR combines traceroute and ping into a single tool, continuously probing each hop:

```bash
mtr -r -c 100 203.0.113.50
```

Sample output:
```
HOST: source            Loss%   Snt   Last   Avg  Best  Wrst StDev
  1. 10.0.1.1            0.0%   100    0.5   0.4   0.3   1.2   0.1
  2. 172.16.0.1          0.0%   100    1.1   1.0   0.9   1.5   0.1
  3. carrier-gw.net      1.0%   100    5.3   5.2   4.8   8.2   0.5
  4. ???                100.0   100    0.0   0.0   0.0   0.0   0.0
  5. transit.net        15.0%   100   12.5  12.8  10.2  25.3   3.2
  6. dest.example.com    0.0%   100   15.2  15.0  14.5  18.2   0.6
```

### Reading MTR Columns

| Column | Meaning |
|--------|---------|
| **Loss%** | Percentage of probes that got no response |
| **Snt** | Number of probes sent |
| **Last** | Latency of most recent probe |
| **Avg** | Average latency |
| **Best** | Lowest latency observed |
| **Wrst** | Worst (highest) latency observed |
| **StDev** | Standard deviation (jitter indicator) |

### The Loss% Interpretation Rule

**ICMP rate limiting appears as loss at intermediate hops, but final hop is fine:**

```
  4. ???                100.0%   100    ← Rate limiting (final hop OK)
  5. transit.net        15.0%    100    ← Real loss? Check final hop
  6. dest.example.com   0.0%     100    ← Final hop OK → hops 4-5 are rate limiting
```

**Real packet loss appears at the failing hop AND all subsequent hops:**

```
  4. hop4.net           0.0%     100
  5. transit.net        45.0%    100    ← Real loss starts here
  6. dest.example.com   45.0%    100    ← Final hop also affected
```

If loss% is the same from hop 5 through the final hop, the loss is occurring at or before hop 5.

🔧 **NOC Tip:** Always check the final hop's loss% first. If it's 0%, ignore loss at intermediate hops — that's ICMP rate limiting. If final hop shows loss, trace back to the first hop where loss appears — that's where the problem starts.

## Forward vs. Reverse Path Asymmetry

The path from A to B is not necessarily the same as B to A.

```
Forward path (A → B):
A → hop1 → hop2 → hop3 → B

Reverse path (B → A):
B → hop4 → hop5 → hop6 → A
```

Traceroute from A shows the forward path only. To see the reverse path, you'd need to run traceroute from B to A.

**Why this matters for NOC:**
- A customer reports latency, but your traceroute looks fine
- The return path might be the problem
- You can't diagnose reverse path issues from one side

**What to do:**
1. Ask the remote side to traceroute back to you
2. Use looking glass servers at various points on the internet
3. Check if latency is symmetric (ping both directions)

## MTR Flags for NOC Work

```bash
# Report mode (outputs summary, exits)
mtr -r -c 100 destination

# Continuous mode (live updates, Ctrl+C to stop)
mtr destination

# TCP mode to specific port
mtr -T -P 5060 destination

# Set interval between probes (faster)
mtr -i 0.1 destination

# Show AS numbers (helpful for identifying carriers)
mtr -z destination
```

The `-z` flag shows AS numbers:
```
  3. AS174. carrier-gw.net    5.2 ms
  5. AS3356. level3.net      12.8 ms
  6. AS46450. telnyx.net     15.0 ms
```

Knowing which AS is involved helps identify which carrier has the issue.

## Real-World Scenario

**Customer report:** "Latency to your SIP server is 500ms, causing call quality issues."

**Investigation:**

1. Run MTR from Telnyx to customer's IP:
```bash
mtr -r -c 100 -T -P 5060 customer-ip
```

Result: Latency 15ms, no loss. Path looks fine.

2. Ask customer to run MTR back:
```
Customer's MTR to Telnyx shows:
  8. their-transit.net    5.0%
  9. congested-hop.net    45.0%   320ms  350ms  280ms  500ms  45.0
 10. our-transit.net      45.0%   350ms
 11. telnyx-sip.com        0.0%    15ms
```

Wait — the final hop shows 15ms, but intermediate hops show 350ms? That's physically impossible. Let's re-examine.

**Correction:** If the final hop shows 15ms, those 350ms intermediate hops are rate-limited ICMP responses (delayed processing), not actual traffic latency. The real traffic latency is 15ms.

**But wait:** Customer says latency is 500ms. Let's check differently.

3. Check with TCP probes on port 5060:
```
Customer's TCP MTR to port 5060:
  8. their-transit.net     0.0%    10ms
  9. congested-hop.net    15.0%   450ms  ← Real latency spike
 10. telnyx-sip.com       15.0%   500ms  ← Final hop confirms
```

**Root cause:** ICMP traceroute was misleading (rate limiting). TCP traceroute to port 5060 shows real SIP path latency — 450-500ms through congested-hop.net.

**Resolution:** Identify the network at congested-hop.net (check AS number), engage that carrier or route around them.

---

**Key Takeaways:**

1. Traceroute works by incrementing TTL; each router that expires TTL sends ICMP Time Exceeded back
2. `* * *` at intermediate hops with responding later hops = ICMP rate limiting, not real loss
3. Real loss shows at failing hop AND all subsequent hops
4. MTR provides statistics (loss%, avg, best, worst, stdev) for each hop over time
5. Always check final hop's loss% first — if it's 0%, intermediate loss is ICMP rate limiting
6. Forward and reverse paths are asymmetric — diagnose from both ends
7. Use TCP traceroute (-T -P port) for path as seen by application traffic, not just ICMP

**Next: Lesson 119 — Reading PCAPs — Wireshark for SIP and RTP**
