# Lesson 163: Circuit Breakers and Retry Patterns
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~6 min read | Prerequisites: Lesson 139**

---

## Resilience Patterns for Distributed Systems

In distributed systems, failures are inevitable. When Service A calls Service B, and B fails, A must decide how to handle it. Without proper patterns, B's failure cascades to A, then to A's callers, potentially bringing down the entire system. Circuit breakers and retry patterns contain these failures.

## The Circuit Breaker Pattern

Named after electrical circuit breakers, this pattern stops calling a failing service to allow it to recover and prevents cascading failures.

### Circuit Breaker States

**CLOSED (normal):**
- All requests flow through to the downstream service
- Circuit breaker monitors failure rate
- If failures exceed threshold, opens circuit

**OPEN (tripped):**
- All requests immediately fail fast (no waiting)
- Pretends service is down, returns error immediately
- Prevents overwhelming the failing service
- Waits for timeout before checking recovery

**HALF-OPEN (testing):**
- After timeout, allows limited requests through
- If they succeed, closes circuit (recovered)
- If they fail, opens again (still broken)

### Why It Works

Without circuit breaker:
- A calls B, B is slow
- A waits, threads blocked
- A's thread pool exhausts
- A starts failing, cascade continues

With circuit breaker:
- A calls B, B is slow, failures accumulate
- Circuit opens
- A returns error immediately to caller
- A's threads free up, A remains healthy
- B gets relief from load, can recover
- When recovered, circuit closes

🔧 **NOC Tip:** When a downstream service is failing, circuit breaker status explains why your service is erroring even though it should work. Check circuit breaker panels in Grafana. An OPEN circuit on a dependency is intentional protection, not a bug.

## Configuring Circuit Breakers

Key parameters:

```yaml
circuitBreaker:
  # Failure threshold to trip
  failureThreshold: 50%  # Open if more than 50% fail
  
  # Time to wait before testing (half-open)
  timeout: 30s
  
  # Window for failure percentage calculation
  window: 60s  # Last 60 seconds
  
  # Minimum calls before calculating failure rate
  minCalls: 10  # Don't trip on 1/1 failures
  
  # Requests to allow in half-open state
  permitWhenHalfOpen: 3
  
  # Different thresholds for different exceptions
  exceptions:
    TimeoutException:
      threshold: 25%  # Lower threshold for timeouts
    NotFoundException:
      threshold: 100%  # Don't count 404s as failures
```

### Fine-Tuning Parameters

**Failure threshold:**
- Too low (5%): Circuit trips on minor blips, unnecessary impact
- Too high (90%): Circuit slow to protect, cascade happens first
- Sweet spot (30-60%): Protects while tolerating some noise

**Timeout:**
- Too short (5s): May circuit when temporary issue
- Too long (5m): Service stays in OPEN too long after recovery
- Sweet spot: Based on actual recovery time of downstream service

**Window:**
- Short (10s): Reacts fast but jittery
- Long (5m): Smooth but slow to react
- Balance responsiveness with stability

## Retry Patterns

When a transient failure occurs (network glitch, brief overload), retrying often succeeds. But retries must be implemented carefully.

### Simple Retry (Dangerous)
```python
for attempt in range(3):
    try:
        return call_service()
    except Exception:
        continue
raise AllRetriesFailed()
```

Problem: retries immediately, no delay. During outages, this adds load to already failing services.

### Exponential Backoff (Better)
```python
base_delay = 1  # second
for attempt in range(3):
    try:
        return call_service()
    except Exception:
        delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
        time.sleep(delay)
raise AllRetriesFailed()
```

Delays increase exponentially, reducing load on failing services.

### Exponential Backoff with Jitter (Best)
```python
base_delay = 1  # second
for attempt in range(3):
    try:
        return call_service()
    except RetryableException:
        delay = base_delay * (2 ** attempt)
        jitter = random.uniform(0, delay * 0.1)  # 10% jitter
        time.sleep(delay + jitter)
```

Jitter prevents "thundering herd": when many clients fail simultaneously and all retry at exactly the same time after the same delay.

🔧 **NOC Tip:** Watch for thundering herd patterns in Grafana: many clients fail at time T, then all succeed simultaneously at T+backoff as they all retry together. Smooth retry distribution with jitter prevents this.

## Retry vs Circuit Breaker: When to Use Which

| Scenario | Pattern | Reason |
|----------|---------|--------|
| Transient network error | Retry | Likely to succeed on retry |
| Temporary timeout | Retry with backoff | Service might recover |
| Persistent timeouts | Circuit breaker | Service is overwhelmed, stop calling |
| Resource unavailable | Circuit breaker | Not transient, can't retry |
| Authentication failure | Neither | Fix the auth problem |

**Golden rule:** Retry for transient failures, circuit breaker for persistent problems.

### Combined Approach
```python
def resilient_call():
    if circuit_breaker.is_open():
        raise CircuitOpenException()
    
    try:
        for attempt in range(3):
            try:
                result = call_service()
                circuit_breaker.record_success()
                return result
            except TransientException:
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(2 ** attempt + jitter())
                continue
            except PersistentException:
                circuit_breaker.record_failure()
                raise
    except Exception as e:
        circuit_breaker.record_failure()
        raise
```

## Implementation in Practice

### Hystrix (Java)
Netflix's Hystrix was the pioneer:
- Thread pools for isolation
- Circuit breaker built-in
- Metrics and dashboards
- Now in maintenance mode, replaced by Resilience4j

### Polly (.NET)
```csharp
var retryPolicy = Policy
    .Handle<HttpRequestException>()
    .WaitAndRetryAsync(3, retryAttempt =>
        TimeSpan.FromSeconds(Math.Pow(2, retryAttempt)));

var circuitBreakerPolicy = Policy
    .Handle<HttpRequestException>()
    .CircuitBreakerAsync(5, TimeSpan.FromSeconds(30));

var combined = Policy.WrapAsync(retryPolicy, circuitBreakerPolicy);
```

### Python Tenacity
```python
from tenacity import retry, stop_after_attempt, wait_exponential
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_service():
    return requests.get("http://service/api")
```

## Real-World Scenario: The Retry Storm

A billing service API experiences a brief database overload, causing 90% of requests to timeout.

**Without retry limits:**
- 1000 clients request billing data
- 900 fail with timeout
- 900 immediately retry (with immediate retry)
- 810 fail, retry again
- 729 fail, retry again
- Total requests: 1000 + 900 + 810 + 729 = 3439 requests
- Billing service receives 3.4x normal load while already failing

**With circuit breaker:**
- First 50 failures recorded
- Circuit opens
- Remaining 950 requests fail fast (no backend call)
- Billing service gets relief
- After 30s, half-open allows 5 test requests
- If recovered, circuit closes
- If still failing, stays open

**Result:** Circuit breaker prevents cascade, gives service recovery time, reduces overload from 3.4x to 1.05x.

🔧 **NOC Tip:** When diagnosing high load on a failing service, check client retry behavior. High retry counts multiply load. If retry attempts >3, investigate why failures aren't triggering circuit breakers. Excessive retry is often the difference between recoverable incident and cascade failure.

## Monitoring Resilience

### Circuit Breaker Metrics
```promql
# Circuit state (0=closed, 1=half-open, 2=open)
circuit_breaker_state{service="billing-api"}

# Failure rate over window
rate(circuit_breaker_failures_total[5m]) / 
rate(circuit_breaker_calls_total[5m])

# Time circuit has been open
time() - circuit_breaker_last_state_change_timestamp
```

### Retry Metrics
```promql
# Retry attempts per call
rate(retry_attempts_total[5m]) / rate(retry_calls_total[5m])

# Distribution of successful attempt (1st, 2nd, 3rd)
histogram_quantile(0.5, rate(retry_success_on_attempt_bucket[5m]))
```

### Alert on Bad Patterns
- Circuit OPEN >10 min: Service not recovering
- Retry rate >3x: Transient failures not transient
- Multiple circuits OPEN: Cascading failure in progress

## NOC Action During Circuit Breaker Alerts

1. **Check downstream service**: Why is it failing?
2. **Check circuit configuration**: Threshold too sensitive?
3. **Force close** (if false positive): Manually reset circuit
4. **Extend timeout** (if recovery is slow): Give more time before retry
5. **Monitor lag**: Queue builds up while circuit is open
6. **Prepare for catch-up wave**: When circuit closes, flood of requests arrive

🔧 **NOC Tip:** Don't force-close circuit breakers without investigating. Opening is the system's way of protecting itself and the downstream service. Fix the root cause instead. Manual resets just lead to immediate re-opening if service is still broken.

---

**Key Takeaways:**
1. Circuit breakers stop calling failing services to prevent cascade failures and allow recovery
2. Three states: CLOSED (normal), OPEN (failing fast), HALF-OPEN (testing recovery)
3. Exponential backoff with jitter prevents thundering herd - all clients retrying simultaneously
4. Retry for transient failures, circuit breaker for persistent problems
5. Combined approach provides resilience: retry handles blips, circuit breaker handles outages
6. Monitor circuit state and retry rates - multiple open circuits indicate cascading failure in progress

**Next: Lesson 148 - Relational Database Fundamentals: PostgreSQL**
