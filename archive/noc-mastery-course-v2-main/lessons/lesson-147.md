# Lesson 147: Firewalls — Stateful Inspection and Rule Management
**Module 5 | Section 5.1 — Network Security**
**⏱ ~7 min read | Prerequisites: Lesson 12-16**

---

## Firewalls in a Telecom Context

Firewalls are the gatekeepers of network traffic. For telecom platforms, they're both essential and treacherous — essential for security, but a frequent source of voice quality issues when misconfigured. Understanding how firewalls interact with SIP and RTP is a critical NOC skill.

## Stateful vs. Stateless Inspection

### Stateless Firewalls
A stateless firewall evaluates each packet independently against a ruleset. It has no memory of previous packets. To allow a TCP connection, you need rules for both directions:

```
ALLOW TCP from 203.0.113.5:* to 10.0.1.5:5060    # Inbound SIP
ALLOW TCP from 10.0.1.5:5060 to 203.0.113.5:*     # Return traffic
```

This is tedious and error-prone, especially for UDP where "connections" don't formally exist.

### Stateful Firewalls
A stateful firewall tracks connection state. When it sees an outbound TCP SYN, it creates a state table entry and automatically allows the return traffic. You only need one rule:

```
ALLOW TCP from 203.0.113.5:* to 10.0.1.5:5060    # Allow inbound SIP
# Return traffic is automatically allowed via state tracking
```

For TCP, this works elegantly. For UDP, it's more complex.

## The UDP Problem: Pseudo-Connections

TCP has explicit connection setup (SYN/SYN-ACK/ACK) and teardown (FIN/FIN-ACK). Stateful firewalls can track the exact lifecycle.

UDP has no connection concept. Stateful firewalls create **pseudo-connections** for UDP: when they see a UDP packet from A→B, they create a state entry allowing B→A responses. But without explicit teardown, these entries are governed by **timers**.

Common UDP timeout values:
- Default: 30-60 seconds
- After seeing bidirectional traffic: 120-180 seconds

### Why This Matters for RTP

An RTP media stream is bidirectional UDP. As long as both sides are sending audio, the firewall sees regular bidirectional traffic and keeps the state entry alive.

But consider call hold (Lesson 47): one side sends `a=sendonly` and stops transmitting audio. The firewall sees one-directional traffic for 30 seconds, then the state entry times out. When the call resumes, the formerly-held party's audio can't pass through the firewall. Result: **one-way audio after hold.**

🔧 **NOC Tip:** If you see one-way audio reports specifically after hold/resume, suspect firewall UDP timeout. The fix is either increasing the firewall UDP timeout (to 300+ seconds) or ensuring comfort noise/silence packets are sent during hold to keep the firewall state alive.

## Firewall Rules for VoIP

A properly configured VoIP firewall needs:

### SIP Signaling
```
ALLOW UDP/TCP 5060 (SIP)
ALLOW TCP 5061 (SIPS/TLS)
```

### RTP Media
```
ALLOW UDP 10000-20000 (RTP media range)
```

The RTP port range is intentionally wide — each call uses a different port pair, and the specific ports are negotiated dynamically in SDP. A firewall that blocks any part of this range will cause intermittent no-audio issues.

### STUN/TURN
```
ALLOW UDP 3478 (STUN)
ALLOW TCP 443 (TURN over TLS)
ALLOW UDP 49152-65535 (TURN relay ports)
```

## Common Firewall Misconfigurations That Break VoIP

### 1. SIP ALG Enabled
Many consumer and business routers include a SIP Application Layer Gateway (ALG) that inspects and modifies SIP packets. The intention is to fix NAT issues, but SIP ALGs frequently mangle SIP headers, corrupt SDP, and cause more problems than they solve.

Symptoms of SIP ALG interference:
- One-way audio (ALG rewrites Contact/SDP with wrong IP)
- Registration failures (ALG modifies Via header)
- Call setup failures (ALG changes ports)

**Fix:** Disable SIP ALG on the customer's router. This resolves the issue in most cases.

🔧 **NOC Tip:** When a customer reports intermittent call issues and they're behind a consumer-grade router (Netgear, Linksys, etc.), SIP ALG is the first thing to check. It's enabled by default on most consumer routers.

### 2. Asymmetric Routing
If inbound SIP arrives through one firewall and the response exits through a different firewall, the second firewall has no state entry for the connection and drops the response.

### 3. Insufficient RTP Port Range
Firewall allows UDP 10000-10100 instead of 10000-20000. Works for a few concurrent calls but fails when port allocation exceeds the allowed range.

### 4. Connection Limits
Enterprise firewalls often have connection tracking limits. Each SIP registration and RTP stream consumes a connection tracking entry. A busy PBX with 500 concurrent calls might exceed the firewall's connection table capacity.

## Reading Firewall Logs

When investigating blocked traffic:

```bash
# iptables — check for dropped packets
iptables -L -v -n | grep DROP

# Check connection tracking table size
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# View active connections tracked
conntrack -L | grep 5060
conntrack -L | grep udp | wc -l
```

Key log fields:
- **Action**: ACCEPT, DROP, REJECT
- **Source/Destination IP and Port**: Identifies the traffic
- **Protocol**: TCP, UDP, ICMP
- **Interface**: Which network interface (inbound vs. outbound)

A spike in DROP entries for UDP traffic to the RTP port range indicates the firewall is blocking media. A growing conntrack count approaching conntrack_max indicates connection table exhaustion.

## Firewall Best Practices for Telecom

1. **Disable SIP ALG** on all intermediate network devices
2. **Set UDP timeout to 300+ seconds** for VoIP-carrying interfaces
3. **Allow the full RTP port range** (don't restrict to a subset)
4. **Size connection tracking tables** for expected concurrent calls (2 entries per call — SIP + RTP)
5. **Monitor firewall CPU and connection table utilization** — overloaded firewalls silently drop packets
6. **Log dropped packets** — but rate-limit logging to avoid log-induced performance issues
7. **Test firewall changes** during low-traffic periods and monitor for impact

🔧 **NOC Tip:** When troubleshooting audio issues for a customer, have them run a traceroute and check if they're behind a firewall or NAT. Ask them to verify SIP ALG is disabled and the RTP port range is open. These three checks resolve 60% of customer-side audio issues.

---

**Key Takeaways:**
1. Stateful firewalls track UDP via timeout-based pseudo-connections — these timers directly affect call hold and media stability
2. SIP ALG is the #1 firewall-related cause of VoIP issues — disable it on customer routers
3. RTP requires a wide UDP port range (10000-20000) — partial ranges cause intermittent failures
4. Firewall connection table exhaustion silently drops packets — monitor conntrack utilization
5. UDP timeouts should be 300+ seconds for VoIP to survive call hold and silence periods
6. Always check firewall logs for DROP entries when investigating no-audio or one-way audio issues

**Next: Lesson 132 — DDoS Attacks and Mitigation**
