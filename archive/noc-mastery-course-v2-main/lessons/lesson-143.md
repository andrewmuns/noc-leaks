# Lesson 143: Capacity Planning — Forecasting and Provisioning
**Module 4 | Section 4.6 — Capacity Planning**
**⏱ ~7 min read | Prerequisites: Lesson 126**

---

## Capacity Planning: Preventing Tomorrow's Outage Today

Capacity-related outages are particularly frustrating because they're predictable. If you're running at 85% CPU today and traffic grows 5% monthly, you'll hit 100% in three months. Yet capacity outages remain common because nobody was watching the trend.

NOC engineers are uniquely positioned for capacity planning — you see the real-time metrics, you know the traffic patterns, and you notice when headroom is shrinking.

## Key Capacity Metrics for Telecom

### Calls Per Second (CPS)
CPS measures how many new calls the platform can initiate per second. It's bounded by SIP proxy processing power, database lookup speed, and carrier trunk capacity. A platform rated for 500 CPS will fail unpredictably above that threshold — 503 responses, dropped INVITEs, database timeouts.

### Concurrent Calls
The number of simultaneously active calls. Bounded by media server capacity (CPU for codec processing, memory for RTP buffers) and carrier channel counts. Unlike CPS, concurrent calls grow with Average Call Duration (ACD) — if ACD increases from 3 minutes to 6 minutes, concurrent calls double even with the same CPS.

### Messages Per Second (MPS)
For messaging, throughput is measured in messages per second. Bounded by API processing, queue depth, and carrier submission rate. 10DLC rate limits add per-campaign throughput ceilings.

### System Resources
- **CPU**: Codec transcoding is CPU-intensive. G.711 is cheap; G.729 encoding costs 10x more CPU per stream.
- **Memory**: Each concurrent call consumes memory for SIP dialog state, RTP buffers, and jitter buffers.
- **Network bandwidth**: Each G.711 call consumes ~87 kbps bidirectional. 10,000 concurrent calls need ~1.7 Gbps.
- **Disk I/O**: Call recording, CDR writing, and log generation create I/O load.

🔧 **NOC Tip:** Monitor the relationship between CPS and CPU usage. If CPU per call is increasing over time (new features, more processing), your effective CPS capacity is shrinking even without traffic growth.

## Headroom: The Safety Buffer

Never run at 100% capacity. Headroom — the buffer between peak usage and maximum capacity — serves three purposes:

1. **Absorbing traffic spikes**: Marketing campaigns, flash events, or carrier failovers can cause sudden 20-30% traffic increases
2. **Handling failure**: If one of three servers fails, the remaining two absorb 50% more traffic. Without headroom, this overloads them
3. **Maintenance windows**: Rolling deployments temporarily reduce capacity. Headroom ensures remaining pods handle the load

**Target headroom guidelines:**
- **Critical path services** (SIP proxy, media servers): 40-50% headroom
- **Supporting services** (billing, CDR processing): 20-30% headroom
- **Carrier trunks**: 30% headroom (carrier failover can shift entire traffic load)

### Calculating Headroom

```
Headroom = 1 - (Peak_Usage / Max_Capacity) × 100%

Example:
Peak CPS: 300
Max CPS capacity: 500
Headroom = 1 - (300/500) × 100% = 40% ✓ Good

Peak CPS: 450
Max CPS capacity: 500
Headroom = 1 - (450/500) × 100% = 10% ⚠️ Dangerous
```

## Forecasting Growth

### Linear Trend Projection
The simplest approach: if traffic grew 5% per month for the last 6 months, project it forward.

```
Future_Peak = Current_Peak × (1 + monthly_growth_rate)^months

Example:
Current peak CPS: 300
Monthly growth: 5%
In 6 months: 300 × 1.05^6 = 402 CPS
```

If your capacity is 500 CPS, you have about 12 months before you need more capacity.

### Stepped Growth
Telecom traffic often grows in steps rather than linearly — a large customer onboards and adds 20% traffic overnight. Track the sales pipeline and onboarding schedule to anticipate step changes.

### Seasonal Adjustment
Account for seasonal variation. If Black Friday causes a 50% messaging spike, your capacity must handle that peak, not just average traffic.

🔧 **NOC Tip:** Set up Grafana alerts for capacity thresholds — not just "is the system overloaded now?" but "is peak daily usage consistently above 70% of capacity?" This gives you weeks of warning before a capacity incident.

## Scaling: Adding Capacity

### Horizontal Scaling (Adding More Instances)
- Add more pods in Kubernetes (increase replica count)
- Add more worker nodes to the cluster
- Add more servers to the data center
- **Pro**: Near-linear scaling for stateless services (SIP proxies, API gateways)
- **Con**: Stateful services (databases, message queues) don't scale as simply

### Vertical Scaling (Bigger Instances)
- Increase CPU/memory allocations for existing pods
- Move to larger physical servers
- **Pro**: Simpler — no changes to architecture
- **Con**: Upper limits exist; doesn't improve fault tolerance

### Carrier Capacity
Outbound call capacity is also limited by carrier trunks. Each carrier interconnect has a maximum CPS and concurrent call limit. Adding platform capacity without adding carrier capacity just moves the bottleneck.

## Bottleneck Identification

The system's capacity is determined by its weakest link. A common investigation:

1. **SIP proxy**: Can handle 1,000 CPS ✓
2. **Routing engine**: Can handle 800 CPS ✓
3. **Database**: Can handle 500 queries/second ← **Bottleneck**
4. **Media servers**: Can handle 50,000 concurrent ✓
5. **Carrier trunks**: Can handle 2,000 CPS ✓

The platform's effective capacity is 500 CPS — limited by the database. Scaling SIP proxies won't help. Adding more database read replicas or optimizing queries will.

To find the bottleneck:
- Which component hits high utilization first as traffic increases?
- Which component's metrics correlate with performance degradation?
- During peak hours, which component is closest to its limits?

## Capacity Planning Process

1. **Measure current capacity**: Load test or calculate from resource utilization
2. **Measure current usage**: Peak values from Grafana (use weekly maximums, not averages)
3. **Calculate headroom**: Current headroom percentage
4. **Forecast growth**: Project usage forward using growth trends and known events
5. **Identify when headroom drops below threshold**: This is your "capacity needed by" date
6. **Plan scaling**: Hardware procurement, cluster expansion, or carrier trunk additions
7. **Repeat monthly**: Capacity planning is continuous, not one-time

🔧 **NOC Tip:** Create a monthly capacity report — a simple table showing each critical component's max capacity, current peak usage, headroom percentage, and projected date when headroom drops below 30%. Share it with engineering leadership. This transforms capacity planning from reactive ("we ran out") to proactive ("we need to add capacity by Q3").

---

**Key Takeaways:**
1. Key telecom capacity metrics are CPS, concurrent calls, and MPS — know your platform's limits for each
2. Maintain 30-50% headroom on critical path services to absorb spikes, failures, and maintenance
3. Traffic grows through both gradual trends and sudden step changes from customer onboarding
4. The system's capacity equals its weakest component — identify and address bottlenecks specifically
5. Horizontal scaling works well for stateless services; stateful services require more careful planning
6. Create monthly capacity reports to shift from reactive to proactive capacity management

**Next: Lesson 128 — Maintenance Windows: Safe Deployment Practices**
