# Lesson 194: Capstone — Full Incident Simulation: Multi-Site Voice Outage

**Module 6 | Section 6.4 — Capstone**
**⏱ ~10 min read | Prerequisites: All Previous**

---

## Scenario: 08:47 UTC — Partial Voice Outage

### The Alert

```
PagerDuty Alert: CRITICAL
Host: noc-paging@telnyx.com
Time: 08:47 UTC

Alert: "voice-quality: ASR drop detected as-voice-proxy-api-prod
        ASR fell from 0.68 to 0.45 in 5 minutes
        Sites affected: ORD (Chicago), LON (London)"
```

**What you notice immediately:**
- ASR (Answer Seizure Ratio) dropped significantly — calls failing
- Two sites affected: Chicago (ORD) and London (LON)
- Not global — Ashburn (IAD) and Frankfurt (FRA) not mentioned

---

## Phase 1: Triage (0-5 minutes)

### Step 1: Acknowledge and Verify

```bash
# Check ops channel for any chatter
# Look at Grafana dashboard: voice.asr.by_site

gh api repos/team-telnyx/monitors/issues --jq '.[] | select(.title | contains("voice outage"))'
```

**Finding:** No planned maintenance. This is unexpected.

### Step 2: Scope the Impact

Dashboard checks:
```
┌─────────────────┬────────┬────────┬──────────┐
│ Site            │ Normal │ Now    │ Status   │
├─────────────────┼────────┼────────┼──────────┤
│ Ashburn (IAD)   │ 0.70   │ 0.69   │ OK       │
│ Chicago (ORD)   │ 0.68   │ 0.45   │ DEGRADED │
│ London (LON)    │ 0.69   │ 0.42   │ DEGRADED │
│ Frankfurt (FRA) │ 0.71   │ 0.70   │ OK       │
│ Singapore (SIN) │ 0.70   │ 0.71   │ OK       │
└─────────────────┴────────┴────────┴──────────┘
```

**Hypothesis:** Something affects ORD and LON specifically. Common element?

### Step 3: Check for Correlated Events

```bash
# Check recent commits
curl -s "https://deploy.telnyx.com/api/releases?service=voice-api&hours=4" | jq '.[] | {version, deployed_at, site}'

# Check Consul health
consul info | grep health
consul catalog services | grep voice

# Check if any infrastructure events
# - BGP announcements withdrawn?
# - Certificate expiry?
# - DNS changes?
```

**Finding:** deploy-voice-api-prod released `voice-api:v3.4.2` at 08:40 UTC — 7 minutes ago.

---

## Phase 2: Investigation (5-20 minutes)

### Step 4: Correlate with Deployment

```bash
# What was in that deploy?
git -C ~/repos/deploy-voice-api-prod log --oneline v3.4.1..v3.4.2

# Output:
# a1b2c3d Update SIP library to handle T.38 reinvite
# b2c3d4e Modify Redis connection pooling
# c3d4e5f Increase voice-worker replicas
```

The Redis connection change looks suspicious.

### Step 5: Examine Logs

```bash
# Graylog search
source:voice-api-prod AND (site:ord OR site:lon) AND exception

# Finding:
2025-02-23 08:40:15 voice-api-prod-ord-01 ERROR RedisConnectionPool: 
  "Connection timeout to redis-cluster.ord.prod:6379"
  
2025-02-23 08:40:15 voice-api-prod-lon-01 ERROR RedisConnectionPool: 
  "Connection timeout to redis-cluster.lon.prod:6379"
```

### Step 6: Infrastructure Check

Each site has its own Redis cluster:
```bash
# Check Redis status
kubectl -n ord-prod logs redis-cluster-0

# Output:
"ERROR: RDB save failed: Service unavailable"
"WARNING: memory usage > 95%"
```

**Root cause identified:** Redis cluster in both ORD and LON hit memory limits due to change in connection pooling that increased connection count, exhausting memory.

---

## Phase 3: Remediation (20-35 minutes)

### Step 7: Immediate Recovery

```bash
# Option 1: Rollback (fastest)
kubectl -n ord-prod set image deployment/voice-api voice-api=telnyx/voice-api:v3.4.1
kubectl -n lon-prod set image deployment/voice-api voice-api=telnyx/voice-api:v3.4.1

# Option 2: Scale Redis (better long-term)
kubectl -n ord-prod apply -f redis-scale-up.yaml
kubectl -n lon-prod apply -f redis-scale-up.yaml
```

**Decision:** Rollback first for immediate relief. Scale Redis after.

### Step 8: Verify Recovery

```bash
# Watch ASR recover
watch -n 30 "curl -s http://voice-metrics.telnyx.com/api/asr | jq '.sites'

# Output after 5 minutes:
{"Ord": 0.67, "Lon": 0.69}  # Back to normal
```

PagerDuty clears: "Resolved: ASR back to normal range"

### Step 9: Customer Communication

```
Status Page Update - incident ID 2025-0023

08:35 UTC - Issue identified affecting voice calls in Chicago and London regions
08:47 UTC - Alert fired, investigation began
08:55 UTC - Root cause identified: Redis memory exhaustion from recent deployment
09:02 UTC - Rollback initiated
09:08 UTC - Service fully restored
09:15 UTC - Monitoring confirms stable operation

Impact: Low ASR (0.45) in Chicago and London for 33 minutes
Resolution: Deployment rolled back, Redis scaling in progress
```

---

## Phase 4: Post-Mortem (Same Day + Follow-up)

### Timeline

| Time | Event | Delta |
|------|-------|-------|
| 08:40 | Deploy v3.4.2 | - |
| 08:41 | Redis memory climbs | +1 min |
| 08:47 | Alert fires | +7 min |
| 08:55 | Root cause identified | +15 min |
| 09:02 | Rollback initiated | +22 min |
| 09:08 | Recovery complete | +28 min |

**MTTR: 28 minutes** (Acceptable for P1, aim for <15)
**Detection lag: 7 minutes** (Acceptable)

### Root Cause Analysis (5 Whys)

1. **Why did ASR drop?**
   - Voice API couldn't cache session state

2. **Why couldn't it cache?**
   - Redis connections were timing out

3. **Why were connections timing out?**
   - Redis was hitting out-of-memory errors

4. **Why did memory run out?**
   - Connection pooling change quadrupled connections

5. **Why wasn't this caught?**
   - Load testing was done separately per component, not integrated
   - Redis memory monitoring alert threshold too high (95% vs alert at 90%)

### Action Items

| Owner | Action | Due |
|-------|--------|-----|
| Platform | Add Redis memory alerts at 80% not 95% | +1 day |
| Voice Team | Update connection pooling test for Redis load | +3 days |
| Platform | Horizontal scaling for Redis clusters defined | +1 week |
| Platform | Canary deploys for voice-api with 5-min metrics | +2 weeks |

---

## Lessons Applied

| Skill Used | How |
|------------|-----|
| Correlation | Connected deploy time to incident start |
| Log analysis | Found Redis connection errors in Graylog |
| Architecture knowledge | Knew site-specific Redis clusters |
| Remediation decision | Chose rollback over fix for MTTR |
| Communication | Status page update with timeline |
| Post-mortem | 5 Whys RCA with action items |

---

## Key Takeaways

1. **Deployment correlation** — Always check recent deploys first
2. **Site-specific patterns** — ORD + LON but not others = shared resource or deployment
3. **Redis memory** — Connection pooling changes have outsized memory impact
4. **Rollback readiness** — Pre-approved rollback procedures save minutes
5. **MTTR targets** — 28 min is acceptable, <15 min is aspirational
6. **Post-mortem discipline** — 5 Whys + action items prevents recurrence

---

**Next: Lesson 179 — Capstone — Cascading Infrastructure Failure**
