# Lesson 25: BGP Mechanics — Sessions, Updates, and Path Selection
**Module 1 | Section 1.6 — BGP**
**⏱ ~9min read | Prerequisites: Lesson 22**
---

Now that you understand Autonomous Systems and why BGP exists, let's look under the hood. How do BGP routers establish sessions? How do they exchange routing information? And when multiple paths exist to the same destination, how does a router pick the best one? These mechanics are essential for understanding NOC incidents involving routing changes, session flaps, and traffic shifts.

## BGP Sessions — TCP Port 179

Unlike IGP protocols that use multicast or broadcast for neighbor discovery, BGP peers must be **explicitly configured**. Each BGP session runs over a **TCP connection on port 179**.

### Session Types

| Type | Description | Typical Use |
|------|-------------|-------------|
| **eBGP** (External BGP) | Between routers in *different* ASes | Telnyx ↔ upstream provider |
| **iBGP** (Internal BGP) | Between routers in the *same* AS | Telnyx router ↔ Telnyx router |

```
┌──────────────────┐          ┌──────────────────┐
│   Telnyx (AS46887)│   eBGP   │  Cogent (AS174)  │
│                  │◄────────►│                  │
│  Border Router   │ TCP:179  │  Border Router   │
└──────────────────┘          └──────────────────┘
        │
        │ iBGP (TCP:179)
        │
┌──────────────────┐
│  Telnyx Internal │
│  Route Reflector │
└──────────────────┘
```

🔧 **NOC Tip:** If a BGP session won't establish, check: (1) TCP 179 connectivity — firewalls often block it, (2) matching AS numbers in the config, (3) correct neighbor IP. Use `telnet <peer-ip> 179` as a quick reachability test.

## BGP Finite State Machine

A BGP session goes through well-defined states:

```
Idle → Connect → OpenSent → OpenConfirm → Established
  ↑                                            │
  └────────────── (on failure) ────────────────┘
```

| State | What's Happening |
|-------|-----------------|
| **Idle** | No connection attempt. Waiting to start |
| **Connect** | TCP connection in progress to peer on port 179 |
| **Active** | TCP failed, retrying (confusingly named — this is a BAD state) |
| **OpenSent** | TCP connected, OPEN message sent, waiting for peer's OPEN |
| **OpenConfirm** | Both OPENs exchanged, waiting for KEEPALIVE |
| **Established** | Session up, routes being exchanged ✅ |

🔧 **NOC Tip:** A session stuck in **Active** state means TCP can't connect — it's a network reachability or firewall issue, not a BGP config issue. A session stuck in **OpenSent** usually means mismatched BGP parameters (wrong ASN, wrong authentication).

## BGP Message Types

BGP uses four message types over the TCP session:

### 1. OPEN

Sent once after TCP connects. Contains:
- BGP version (4)
- Sender's ASN
- Hold time (default 90 seconds)
- Router ID
- Optional capabilities (4-byte ASN, multiprotocol extensions, etc.)

```
OPEN Message:
  Version: 4
  My AS: 46887
  Hold Time: 90
  BGP Identifier: 10.0.0.1
  Capabilities: [4-byte-ASN, MP-BGP-IPv4, MP-BGP-IPv6]
```

### 2. KEEPALIVE

Sent every 1/3 of the hold time (default: every 30 seconds). If no KEEPALIVE or UPDATE is received within the hold time, the session is declared dead.

```
Hold Time: 90 seconds
KEEPALIVE interval: 30 seconds
Miss 3 KEEPALIVEs → session down
```

### 3. UPDATE

The core message — carries routing information. Contains:

- **Withdrawn Routes:** Prefixes being removed
- **Path Attributes:** AS-PATH, NEXT-HOP, LOCAL-PREF, MED, communities, etc.
- **NLRI (Network Layer Reachability Information):** New prefixes being announced

```
UPDATE Message:
  Withdrawn Routes: [none]
  Path Attributes:
    ORIGIN: IGP
    AS-PATH: 46887 174 13335
    NEXT-HOP: 198.51.100.1
    LOCAL-PREF: 100
    COMMUNITIES: 46887:1000
  NLRI:
    1.1.1.0/24
```

### 4. NOTIFICATION

Sent when an error occurs. Immediately tears down the session.

```
NOTIFICATION: Hold Timer Expired
NOTIFICATION: UPDATE Message Error - Invalid AS-PATH
```

## Key Path Attributes

Path attributes are carried in UPDATE messages and are crucial for path selection:

### AS-PATH

The sequence of ASes a route has traversed. Most important attribute for loop prevention and path selection.

```
Prefix: 8.8.8.0/24
AS-PATH: 174 15169        ← traversed AS174 (Cogent) then AS15169 (Google)
AS-PATH length: 2 hops

Alternative path:
AS-PATH: 3356 3257 15169  ← through Lumen, GTT, then Google
AS-PATH length: 3 hops    ← longer = less preferred (by default)
```

### NEXT-HOP

The IP address to forward traffic to for this prefix. In eBGP, this is the peer's IP. In iBGP, this is the eBGP next-hop (unchanged by default).

### LOCAL-PREF

Used within an AS (iBGP) to indicate preference. **Higher = more preferred.**

```
Path via Cogent:   LOCAL-PREF 200  ← preferred
Path via HE:       LOCAL-PREF 100  ← backup
```

🔧 **NOC Tip:** At Telnyx, network engineering uses LOCAL-PREF to control which upstream we prefer for outbound traffic. If you see a sudden traffic shift between upstreams, check if someone changed LOCAL-PREF values.

### MED (Multi-Exit Discriminator)

Sent to an eBGP peer to suggest which entry point to use. **Lower = more preferred.** Only compared between paths from the *same* neighboring AS.

### Communities

Tags attached to routes for policy signaling. Formatted as `ASN:value`:

```
46887:1000  → "Learned from transit"
46887:2000  → "Learned from peering"
46887:9000  → "Blackhole this prefix"
```

Communities enable powerful automation — a single tag can trigger filtering, preference changes, or blackholing across the entire network.

## The BGP Path Selection Algorithm

When a router has multiple paths to the same prefix, it uses this ordered algorithm (Cisco/standard):

```
1. Highest LOCAL-PREF                    ← policy preference
2. Shortest AS-PATH                      ← fewer hops preferred
3. Lowest ORIGIN type                    ← IGP < EGP < INCOMPLETE
4. Lowest MED                            ← from same neighbor AS only
5. eBGP over iBGP                        ← prefer external routes
6. Lowest IGP metric to NEXT-HOP         ← closest exit point
7. Oldest route (most stable)            ← prevent flapping
8. Lowest Router ID                      ← tiebreaker
9. Lowest peer IP address                ← final tiebreaker
```

### Example: Which Path Wins?

```
Path A: LOCAL-PREF 200, AS-PATH: 174 15169 (len 2)
Path B: LOCAL-PREF 100, AS-PATH: 15169 (len 1)

Winner: Path A — LOCAL-PREF is checked first (step 1), 200 > 100
```

Even though Path B has a shorter AS-PATH, LOCAL-PREF takes precedence. This is how operators override "natural" shortest-path routing.

🔧 **NOC Tip:** During an incident where traffic is taking a suboptimal path, the first thing to check is LOCAL-PREF. It overrides everything else. The second thing to check is AS-PATH prepending — where extra copies of an ASN are added to make a path look longer:

```
Normal:    AS-PATH: 46887
Prepended: AS-PATH: 46887 46887 46887  ← looks like 3 hops, discouraging use
```

## BGP in Practice — Router Commands

On Cisco IOS / FRRouting (common in Telnyx infrastructure):

```bash
# Show BGP summary — are sessions up?
show bgp summary

# Output:
# Neighbor        AS    MsgRcvd  MsgSent  State/PfxRcd
# 198.51.100.1    174   152384   148293   950000    ← Established, receiving ~950K prefixes
# 203.0.113.1     6939  0        0        Active    ← NOT established — stuck in Active

# Show all paths to a specific prefix
show bgp 8.8.8.0/24

# Show the best path and why
show bgp 8.8.8.0/24 bestpath-compare

# Show routes with a specific community
show bgp community 46887:1000
```

## Real-World Scenario: BGP Session Flap

**Alert:** "BGP session with AS174 (Cogent) is flapping — up/down every 2 minutes"

**Investigation:**
```bash
# Check session state and last error
show bgp neighbor 198.51.100.1

# Look for NOTIFICATION messages in logs
grep "NOTIFICATION" /var/log/bgp.log

# Common causes:
# - Hold timer expired → possible link congestion or CPU overload
# - UPDATE error → malformed routes from peer
# - Physical link issues → check interface errors
show interface GigabitEthernet0/0 | include errors
```

**Impact:** Every time the session drops, all routes learned from Cogent are withdrawn. Traffic shifts to other upstreams, potentially causing congestion. When the session comes back, ~950K routes flood in, spiking CPU.

🔧 **NOC Tip:** For flapping sessions, check if **BGP dampening** is configured. Dampening suppresses routes that flap frequently, but it can also prevent legitimate routes from being reinstalled quickly. It's a double-edged sword.

## Key Takeaways

1. **BGP runs over TCP port 179** — sessions are explicitly configured, not auto-discovered
2. **Four message types:** OPEN (establish), KEEPALIVE (heartbeat), UPDATE (routes), NOTIFICATION (errors)
3. **AS-PATH** prevents loops and influences path selection — shorter paths are preferred by default
4. **LOCAL-PREF overrides everything** in the path selection algorithm — it's the primary policy tool
5. **Communities** are powerful tags that drive automation and policy across networks
6. **The path selection algorithm** has ~9 steps, evaluated in strict order — know the first three (LOCAL-PREF, AS-PATH, ORIGIN) and you'll understand 90% of routing decisions
7. **Session flaps** cause route churn, traffic shifts, and CPU spikes — they're high-priority NOC events

---

**Next: Lesson 24 — Peering, Transit, and Internet Exchange Points**
