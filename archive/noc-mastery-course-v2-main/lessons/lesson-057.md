# Lesson 57: ICE — Interactive Connectivity Establishment

**Module 1 | Section 1.15 — WebRTC**
**⏱ ~8 min read | Prerequisites: Lesson 54**

---

## ICE Purpose

ICE finds the best network path between two endpoints, handling NAT traversal automatically. It tries multiple candidates, tests connectivity, and selects the optimal working path.

---

## ICE Candidate Types

### Host Candidates
Local IP addresses on the endpoint:
```
192.168.1.100:50000  (private)
10.0.0.5:50001       (private)
172.16.0.10:50002    (private)
```
Host candidates work only if both endpoints are on the same network (no NAT between them).

### Server Reflexive (srflx) Candidates
Public addresses learned via STUN:
```
203.0.113.5:51234  (public, learned via STUN)
```
The STUN server sees the NAT-mapped address and reports it back. Enables direct connection through NAT (for Cone NAT types).

### Relay (relay) Candidates
TURN server addresses (guaranteed to work):
```
198.51.100.10:60000  (TURN relay address)
```
Traffic goes through the TURN server, relaying to the other party. Works through any NAT, including Symmetric.

### Peer Reflexive (prflx) Candidates
Discovered during connectivity checks:
```
Discovered: 198.51.100.15:52345
```
When a check succeeds from an unexpected address, ICE learns a new candidate dynamically.

---

## ICE Gathering Process

```
Endpoint A                           STUN/TURN
    |                                    |
    |--- STUN Binding Request ---------->|
    |<-- Binding Response: 203.0.113.5 --|
    |                                    |
    |--- TURN Allocate Request --------->|
    |<-- Allocation: 198.51.100.10 -----|
    |                                    |
    |  [Collect host, srflx, relay]     |
```

**Types collected:**
1. Host candidates (all local IPs)
2. Server reflexive (via STUN)
3. Relay candidates (via TURN)

---

## ICE Priorities

Each candidate has a priority:
```
priority = (2^24 * type_preference) + (2^8 * local_preference) + (256 - component_id)
```

### Type Preferences (typical values):
| Type | Preference | Reason |
|------|------------|--------|
| Host | 126 | No NAT = lowest latency |
| Peer Reflexive | 110 | Discovered working path |
| Server Reflexive | 100 | NAT traversal but direct |
| Relay | 0 | Extra hop = highest latency |

**Result:** ICE prefers direct paths over relays.

---

## Connectivity Checks

After exchanging candidates, ICE performs checks:

```
Endpoint A                           Endpoint B
    |                                    |
    |--- STUN Binding Request ---------->|  (to B's candidate)
    |<-- STUN Binding Response ---------|  (if reachable)
    |                                    |
    |<-- STUN Binding Request -----------|  (from B)
    |--- STUN Binding Response -------->|  (if reachable)
    |                                    |
    |  [Both directions work = success] |
```

### Pairing Matrix

Every candidate of A is paired with every candidate of B:

| | B-host | B-srflx | B-relay |
|---|--------|---------|---------|
| **A-host** | Check | Check | Check |
| **A-srflx** | Check | Check | Check |
| **A-relay** | Check | Check | Check |

Up to 9 checks for basic scenarios. More candidates = more pairs.

---

## Candidate Nomination

Once checks complete, ICE nominates the best working pair:

1. **Regular nomination:** Let all checks complete, then pick highest priority
2. **Aggressive nomination:** Nominate first successful pair and use immediately

```
Check results:
- A-host → B-host:        FAILED (different networks)
- A-host → B-srflx:       FAILED (NAT type mismatch)
- A-srflx → B-host:       FAILED (NAT type mismatch)
- A-srflx → B-srflx:      SUCCESS ✓  ← NOMINATED
- A-srflx → B-relay:      SUCCESS (but lower priority)
- A-relay → B-relay:      SUCCESS (lowest priority)
```

Result: srflx ↔ srflx (direct through NAT) is selected.

---

## ICE Roles

| Role | Decision |
|------|----------|
| **Controlling** | Decides which candidate pair to use |
| **Controlled** | Follows controlling agent's nomination |

Typically, the caller is controlling, callee is controlled.

---

## ICE States

```
x                +---------------+
                 |               |
       +--------->|    New        |
       |         |               |
       |         +---------------+
       |                |
       |                | Gathering
       |                v
       |         +---------------+
       |         |               |
       |         |   Gathering   |
       |         |               |
       |         +---------------+
       |                |
       |                | Gathering Complete
       |                v
       |         +---------------+
       |         |               |
       +-------->|   Checking    |<----------+
       |         |               |           |
       |         +---------------+           |
       |                |                    |
       |                | Check Complete     |
       |                v                    |
       |         +---------------+           |
       |         |               |           |
       +-------->|   Connected   |-----------+
       |         |               |  (if new candidates)
       |         +---------------+
       |                |
       |                | Final nomination
       |                v
       |         +---------------+
       |         |               |
       +-------->|  Completed    |
       |         |               |
       |         +---------------+
       |                |
       +----------------+
       (failure paths)
```

🔧 **NOC Tip:** If WebRTC calls fail at "Checking" state, suspect STUN/TURN server reachability. If they reach "Connected" but drop to "Failed," look for aggressive timeouts or Symmetric NAT with broken TURN credentials.

---

## Telnyx TURN Infrastructure

Telnyx provides global TURN servers:
```javascript
iceServers: [
  { urls: 'stun:stun.telnyx.com:3478' },
  {
    urls: 'turn:turn.telnyx.com:3478',
    username: '...',
    credential: '...'
  }
]
```

**Geographic distribution:**
- US East (Ashburn)
- US West (San Jose)
- Europe (Frankfurt)
- APAC (Singapore)

Latency-optimized allocation based on client location.

---

## Key Takeaways

1. **Four candidate types:** Host, Server Reflexive, Relay, Peer Reflexive
2. **Priority hierarchy:** Host > Peer Reflexive > Server Reflexive > Relay
3. **Connectivity checks:** Test every candidate pair, verify bidirectional connectivity
4. **Nomination:** Select highest priority pair that passes both directions
5. **Controlling vs Controlled:** One side decides, other follows
6. **TURN is fallback:** Used only when direct paths fail

---

**Next: Lesson 56 — WebRTC-to-SIP Gateway — Bridging Browser and PSTN**
