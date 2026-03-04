# Lesson 2: Circuit Switching — Dedicated Paths and Why They Mattered
**Module 1 | Section 1.1 — The PSTN: History, Circuit Switching, and SS7**
**⏱ ~8 min read | Prerequisites: Lesson 1**

---

## The Core Idea: Resource Reservation

In Lesson 1, we saw how central offices connected subscribers by physically patching circuits together. Circuit switching formalizes this idea: when you make a call, a **dedicated communication path** is established end-to-end, and **resources are reserved exclusively** for that call for its entire duration — whether you're talking, silent, or on hold.

This is the fundamental difference between circuit switching and packet switching (Lesson 10). In a circuit-switched network, bandwidth is **allocated**, not **shared**. You get a fixed-capacity pipe, and nobody else can use it until you hang up.

To understand why this matters, think about what it guarantees:
- **Zero jitter**: The path is fixed; every sample traverses the same route with the same delay
- **Zero packet loss**: There are no packets to lose — it's a continuous stream
- **Fixed latency**: Propagation delay is constant because the path doesn't change
- **Guaranteed bandwidth**: Your 64 kbps channel is always available

These are exactly the properties that voice communication needs, and exactly the properties that packet switching struggles to provide. Every QoS mechanism in modern VoIP (Lesson 11) is an attempt to approximate what circuit switching gave us for free.

The tradeoff? **Efficiency.** When you're silent (which is roughly 60% of a typical phone call), your reserved bandwidth goes completely unused. Nobody else can use it. This waste is what made packet switching revolutionary — but we're getting ahead of ourselves.

## Time-Division Multiplexing and the DS0

How do you carry multiple simultaneous calls on a single physical link? The answer is **Time-Division Multiplexing (TDM)** — dividing time into fixed slots and assigning each call to a specific slot.

Here's how it works at the most fundamental level:

A single voice channel requires 64 kbps (8,000 samples per second × 8 bits per sample — the math behind this is covered in Lesson 5). This single 64 kbps channel is called a **DS0** (Digital Signal level 0). It is the atomic unit of digital telephony.

TDM takes multiple DS0 channels and interleaves them on a single physical link. The multiplexer grabs one byte (8 bits) from channel 1, then one byte from channel 2, then channel 3, and so on. At the far end, the demultiplexer reverses the process, distributing each byte back to the correct channel based on its position in the frame.

The key insight: **position in the frame determines the channel**. There are no headers, no addressing — just position. Byte 1 always belongs to channel 1, byte 2 to channel 2, etc. This is extremely efficient (zero overhead) but completely rigid.

## T1 and E1 Trunks

The two dominant TDM standards emerged from different sides of the Atlantic:

**T1 (DS1) — North America and Japan:**
- 24 DS0 channels × 64 kbps = 1.536 Mbps + 8 kbps framing = **1.544 Mbps**
- Frame: 193 bits (24 × 8 bits + 1 framing bit)
- 8,000 frames per second (matching the sampling rate)
- Channel 24 is sometimes reserved for signaling (robbed-bit signaling), leaving 23 usable voice channels

**E1 — Europe and most of the world:**
- 32 DS0 channels × 64 kbps = **2.048 Mbps**
- 30 voice channels + 1 signaling channel (timeslot 16) + 1 synchronization channel (timeslot 0)
- Frame: 256 bits (32 × 8 bits)

🔧 **NOC Tip:** When you see references to "a T1" or "a PRI" in customer configurations, understand that this represents a physical link carrying 23 or 24 simultaneous calls (or 30 for E1/PRI). When capacity planning for SIP trunk migrations, each T1 being replaced translates to roughly 23 concurrent call sessions. A customer saying "we have 4 PRIs" means they're provisioned for approximately 92 simultaneous calls.

## The TDM Hierarchy

DS0 channels aggregate into larger and larger pipes:

| Level | Channels | Bandwidth | Typical Medium |
|-------|----------|-----------|----------------|
| DS0 | 1 | 64 kbps | Single voice call |
| DS1 (T1) | 24 | 1.544 Mbps | Copper pairs |
| DS3 (T3) | 672 | 44.736 Mbps | Coaxial cable |
| OC-3 | 2,016 | 155.52 Mbps | Fiber optic |
| OC-48 | 32,256 | 2.488 Gbps | Fiber optic |
| OC-192 | 129,024 | 9.953 Gbps | Fiber optic |

This hierarchy means that when a fiber cut occurs on an OC-48 link, it doesn't affect just one call — it drops **32,256 simultaneous calls**. This is why physical diversity (routing fiber along different geographic paths) is critical for carrier-grade reliability, and why Telnyx's network architecture emphasizes geographic redundancy.

## Trunk Groups and Capacity Planning

A **trunk group** is a collection of circuits (DS0 channels) between two switches that share a common purpose — for example, all circuits between Telnyx's gateway in Ashburn and a PSTN tandem switch in New York.

The key capacity planning question is: **how many trunks do I need?** Too few, and calls get blocked (busy). Too many, and you're paying for idle capacity.

This is where **traffic engineering** and the **Erlang** models come in.

### The Erlang B Formula

Voice traffic is measured in **Erlangs**. One Erlang represents one circuit occupied continuously for one hour. If 30 people each make one call that lasts 6 minutes during the busy hour, that's:

30 calls × (6/60) hours = **3 Erlangs** of traffic

The **Erlang B formula** calculates the **blocking probability** — the chance that a new call attempt will be rejected because all circuits are busy — given a number of trunks and offered traffic load.

For example:
- 10 trunks carrying 5 Erlangs → ~1.8% blocking (roughly 1 in 55 calls blocked)
- 15 trunks carrying 5 Erlangs → ~0.006% blocking (virtually no blocking)
- 10 trunks carrying 9 Erlangs → ~22% blocking (1 in 5 calls blocked — unacceptable)

The industry standard target is typically **P.01** (1% blocking) or **P.001** (0.1% blocking) during the busy hour.

🔧 **NOC Tip:** Erlang models remain directly relevant to SIP trunk capacity planning. When a customer asks "how many concurrent calls can my SIP trunk handle?", you're solving the same problem — just without fixed physical circuits. Telnyx's SIP trunking typically allows configurable concurrent call limits per trunk. If a customer is hitting their concurrent call limit during peak hours, they're experiencing the SIP equivalent of trunk group blocking. Check call volume patterns in Grafana to determine if they need a higher limit.

## A Real Troubleshooting Scenario

**Scenario:** A customer migrating from 6 × T1 PRIs to Telnyx SIP trunking reports that they're seeing 503 responses during their morning peak (9:00-10:00 AM).

**Analysis:** 
- 6 T1 PRIs = 138 concurrent call capacity (6 × 23 channels)
- Their SIP trunk was provisioned with a 100 concurrent call limit (a common default)
- During the busy hour, they're attempting more than 100 simultaneous calls

**What you'd see in monitoring:** 
- A spike in 503 (Service Unavailable) responses correlating with times when concurrent call count approaches 100
- The 503s would be generated by Telnyx's SBC when the customer's concurrent call limit is reached
- Call attempts per second (CAPS) and concurrent calls metrics in Grafana would show the ceiling being hit

**Resolution:** Increase the customer's concurrent call limit to at least 138 (matching their previous capacity), ideally with some headroom. Verify they're not also hitting calls-per-second (CAPS) limits, which is a separate constraint.

## Why Circuit Switching Still Matters

You might think circuit switching is obsolete. It's not — for two important reasons:

**1. The PSTN still uses it.** The last-mile connection to many telephone subscribers is still a circuit-switched analog line or ISDN. When a Telnyx customer calls a landline, the call transitions from packet-switched (SIP/RTP) to circuit-switched (TDM) at a media gateway. Understanding both worlds is essential for debugging calls that cross the boundary.

**2. The concepts transfer directly.** Capacity planning, blocking probability, trunk groups — these concepts apply directly to SIP trunking. A SIP trunk with a concurrent call limit of 100 behaves like a trunk group with 100 circuits. The math is the same; only the physical implementation differs.

The transition from circuit switching to packet switching (Lesson 10) was driven by one powerful idea: **statistical multiplexing** — the realization that you don't need to reserve resources you're not using. But that transition came with costs: jitter, packet loss, and complexity. Every lesson in this course, in some way, deals with the consequences of that tradeoff.

---

**Key Takeaways:**
1. Circuit switching reserves a dedicated 64 kbps channel (DS0) for each call — guaranteeing zero jitter and zero loss, but wasting bandwidth during silence
2. TDM multiplexes multiple DS0s onto shared physical links using time slots — position in the frame determines the channel (no headers needed)
3. T1 carries 24 channels (1.544 Mbps), E1 carries 32 channels (2.048 Mbps) — these map directly to SIP trunk concurrent call planning
4. The Erlang B formula calculates blocking probability and remains directly relevant to SIP trunk capacity planning
5. Trunk group concepts (capacity, blocking, busy-hour engineering) apply identically to SIP trunks with concurrent call limits

**Next: Lesson 3 — SS7 Signaling — The Brain of the PSTN**
