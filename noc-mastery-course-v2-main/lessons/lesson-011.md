# Lesson 11: Voice Quality Metrics — MOS, PESQ, POLQA, and R-Factor
**Module 1 | Section 1.2 — Digital Voice: Sampling, Quantization, and Codecs**
**⏱ ~7 min read | Prerequisites: Lessons 6, 7, 8**

---

## Why We Measure Voice Quality

You can't improve what you can't measure. In a NOC environment, "the call sounded bad" isn't actionable. You need **quantitative metrics** that tell you *how bad*, *what kind of bad*, and *where in the call path the problem originated*.

Voice quality measurement spans a spectrum from purely subjective (asking humans) to purely algorithmic (computing a score from signal characteristics). Understanding these metrics and how to read them in dashboards is a core NOC skill.

## Mean Opinion Score (MOS)

The **MOS** is a number from **1 to 5** representing subjective voice quality:

| MOS | Quality | Description |
|-----|---------|-------------|
| 5 | Excellent | Imperceptible distortion |
| 4 | Good | Perceptible but not annoying |
| 3 | Fair | Slightly annoying |
| 2 | Poor | Annoying |
| 1 | Bad | Very annoying |

Originally, MOS was determined by having a panel of listeners rate audio samples — literally asking people "how does this sound?" on a 1-5 scale. This is **subjective MOS** and is the gold standard for quality assessment, but it's obviously impractical for real-time monitoring.

In practice, when you see "MOS" in a dashboard, it's always an **estimated MOS** computed algorithmically. There are two fundamentally different approaches to this estimation.

## PESQ and POLQA — Intrusive Measurement

**PESQ** (Perceptual Evaluation of Speech Quality, ITU-T P.862) and its successor **POLQA** (Perceptual Objective Listening Quality Analysis, ITU-T P.863) are **intrusive** (or "full-reference") methods.

They work by comparing the degraded audio to the original:

1. Send a known reference signal through the system
2. Capture the output at the far end
3. Algorithmically compare the output to the reference
4. Compute a MOS-equivalent score based on perceptual differences

These methods are highly accurate because they have the original signal to compare against. POLQA supports wideband and super-wideband measurement (important for G.722 and Opus), while the older PESQ is limited to narrowband.

**Limitation:** Intrusive methods require injecting test signals — they can't measure live calls without disrupting them. They're primarily used for:
- Lab testing codec implementations
- Periodic service quality auditing
- Comparing codec configurations

## The E-Model and R-Factor — Non-Intrusive Estimation

For real-time monitoring of live calls, you need a **non-intrusive** method that estimates quality from measurable network parameters without requiring a reference signal. This is the **E-Model** (ITU-T G.107).

The E-Model computes an **R-Factor** (0-100) based on a formula:

```
R = R₀ - Is - Id - Ie-eff + A
```

Where:
- **R₀** = Base signal-to-noise ratio (default ~94)
- **Is** = Simultaneous impairments (noise, quantization distortion, loudness)
- **Id** = Delay impairments (one-way delay, echo)
- **Ie-eff** = Equipment impairment (codec distortion, packet loss effects)
- **A** = Advantage factor (user tolerance for mobile/satellite — they accept lower quality)

The R-Factor maps to MOS:

| R-Factor | MOS | Quality |
|----------|-----|---------|
| 90-100 | 4.3-4.5 | Excellent |
| 80-90 | 4.0-4.3 | Good |
| 70-80 | 3.6-4.0 | Fair |
| 60-70 | 3.1-3.6 | Poor |
| <60 | <3.1 | Bad |

### What Feeds Into the R-Factor

**Codec impairment (Ie):** Each codec has a baseline impairment value. G.711 has Ie=0 (reference quality). G.729 has Ie=11. Higher compression = higher baseline impairment.

**Packet loss (Ie-eff adjusted):** Loss dramatically increases the effective equipment impairment. G.729 with 0% loss has Ie-eff=11; with 5% loss, Ie-eff jumps to ~30+. Loss impact varies by codec — codecs with PLC handle loss better than those without.

**One-way delay (Id):** Below 150 ms, delay impairment is minimal. Between 150-400 ms, it increases linearly. Above 400 ms, conversation becomes awkward (constant interruptions from "conversational overlap").

**Jitter buffer discard:** Late packets that arrive after the jitter buffer's playout deadline are effectively lost, contributing to the loss component.

🔧 **NOC Tip:** In Grafana dashboards, R-Factor is often more useful than MOS because it separates impairment sources. If you see a low R-Factor, look at the individual components: Is the delay component high (routing/path issue)? Is the packet loss component high (network congestion)? Is the base codec impairment high (G.729 when G.711 would work)? This decomposition points you directly at the root cause.

## Reading Quality Metrics in Dashboards

When monitoring call quality in Telnyx's dashboards, you'll typically see:

**Per-call metrics (from RTCP):**
- Packet loss percentage
- Jitter (interarrival variation in ms)
- Round-trip time (from RTCP SR/RR timestamps)
- Estimated MOS (computed from the above using E-Model)

**Aggregate metrics (across calls):**
- Average MOS across all active calls
- Percentage of calls below MOS threshold (e.g., <3.5)
- MOS distribution histogram
- Loss/jitter trends over time

**What to look for:**

1. **Sudden MOS drop across many calls** → Network event (congestion, route change, hardware failure)
2. **Low MOS on specific routes/destinations** → Interconnect quality issue with a specific carrier
3. **Low MOS for a specific customer** → Customer's network (last mile) problem
4. **Gradual MOS degradation over time** → Capacity issue (growing traffic approaching limits)
5. **MOS varies by time of day** → Congestion during peak hours

## A Real Troubleshooting Scenario

**Scenario:** The NOC dashboard shows average MOS dropped from 4.2 to 3.6 starting at 14:00 UTC. The drop affects approximately 30% of calls but not all.

**Analysis:**
1. Filter the affected calls — what do they have in common?
2. Common carrier? → Interconnect issue with that carrier
3. Common geography? → Regional network problem
4. Common media server? → Server-side issue (CPU, network interface)

**Investigation steps:**
- Check which media servers are handling the affected calls — if they're concentrated on one server, check that server's CPU and NIC metrics
- Check RTCP loss/jitter for the affected calls — high jitter suggests network congestion; high loss suggests drops
- Check if a BGP route change occurred around 14:00 — a new path might have higher latency or traverse a congested link
- Check the specific carriers involved — if all affected calls traverse a single carrier interconnect, the problem is there

**What you'd find:** In this hypothetical, the affected calls all traverse a transit provider that experienced a partial fiber cut, causing traffic rerouting through a longer, more congested path. The 30% of calls affected are those whose routes go through this provider. The remaining 70% use different paths and are unaffected.

🔧 **NOC Tip:** Always baseline your quality metrics. Know what "normal" MOS looks like for different call types: internal calls should be 4.3+, PSTN calls 4.0+, international calls 3.8+, WebRTC calls vary more. Without a baseline, you can't distinguish a real problem from normal variation. Set alerts at thresholds that are meaningful for each call type.

## Quality Metrics Limitations

No quality metric is perfect:

- **E-Model MOS** doesn't capture all impairments (e.g., echo, background noise, distortion)
- **RTCP-reported jitter** is an exponentially-weighted average — it smooths over spikes that might be perceptible
- **Packet loss percentage** doesn't distinguish between random loss (mild impact) and burst loss (severe impact)
- **Aggregate metrics** can hide problems — 95% of calls at MOS 4.5 and 5% at MOS 2.0 averages to 4.375, which looks fine but 5% of callers are suffering

Always combine metrics with human reports. If a customer says "calls sound terrible" but metrics look fine, trust the customer — there may be an impairment the metrics don't capture.

---

**Key Takeaways:**
1. MOS (1-5) is the universal voice quality scale; in dashboards, it's always algorithmically estimated, not subjectively measured
2. PESQ/POLQA (intrusive) compare output to reference for high accuracy; the E-Model (non-intrusive) estimates quality from network parameters for real-time monitoring
3. The R-Factor (0-100) decomposes quality into delay, loss, and codec impairments — use this decomposition to identify root causes
4. Key thresholds: MOS >4.0 good, 3.5-4.0 acceptable, <3.5 investigate; packet loss <1% good, >3% problematic; delay <150ms good, >400ms unusable
5. Always baseline quality metrics by call type and set meaningful alert thresholds — aggregate averages can mask significant quality problems

**Next: Lesson 10 — Packet Switching — Store-and-Forward and Statistical Multiplexing**
