# Lesson 137: Common Failure Pattern — Service Overload and Cascading Failures
**Module 4 | Section 4.5 — Failure Patterns**
**⏱ ~8 min read | Prerequisites: Lesson 92, 97, 108**

---

## The Domino Effect in Distributed Systems

Cascading failures are the most dangerous failure pattern in any distributed telecom platform. They begin innocently — a single service slows down — and within minutes, they can bring an entire platform to its knees. Understanding this pattern is not optional for NOC engineers; it's the difference between a 5-minute blip and a 2-hour outage.

Let's trace how a cascade unfolds in a real Telnyx-like environment.

## Anatomy of a Cascade

Imagine Service A (the SIP proxy) depends on Service B (the routing engine) to determine where to send calls. Under normal operation, Service A sends a routing query to Service B, gets a response in 5ms, and forwards the SIP INVITE. Simple.

Now Service B starts slowing down. Maybe a database query is taking longer than usual, or a deployment introduced a subtle performance regression. Response times climb from 5ms to 500ms, then to 2 seconds.

Here's where it gets dangerous:

1. **Thread exhaustion**: Service A has a finite number of threads (say 200) to handle concurrent requests. Each thread that's waiting for Service B is occupied, doing nothing useful. As B slows down, threads pile up waiting.

2. **Queue buildup**: Once all 200 threads are occupied, new requests start queuing. Queue depth grows. Memory usage increases.

3. **Timeout accumulation**: Eventually, requests to Service B start timing out. But by now, Service A's threads are all busy handling timeouts and retries.

4. **Service A fails**: With no threads available, Service A can't process any requests — even ones that don't need Service B. Health checks fail. Consul marks Service A as unhealthy.

5. **Upstream impact**: Service C (the API gateway) depends on Service A. Now Service C starts experiencing the same thread exhaustion. The cascade propagates upstream.

What started as a slow database query on Service B has now taken down the entire call processing pipeline.

## Retry Storms: Pouring Gasoline on Fire

Retries are the accelerant in cascading failures. When Service A's request to Service B times out, the natural instinct (and often the default configuration) is to retry. But consider the math:

- Service B is overloaded with 1,000 requests/second
- 50% are timing out, so 500 requests get retried
- Now Service B is handling 1,500 requests/second
- More timeouts occur, more retries fire
- Soon Service B is receiving 3,000+ requests/second — 3x its capacity

Each retry makes the problem worse. The service that was struggling is now being hammered into oblivion. And it's not just Service A retrying — every client of Service B is retrying independently, creating a multiplicative effect.

🔧 **NOC Tip:** When you see a service overloading, the FIRST thing to check is whether retry storms are amplifying the problem. Look for request rates that are significantly higher than normal — if a service normally handles 1,000 req/s and suddenly sees 5,000 req/s, retries are likely the culprit.

## Circuit Breakers: The Emergency Stop

The circuit breaker pattern is the primary defense against cascading failures. Named after electrical circuit breakers, it works the same way — when too much current (failures) flows, the breaker trips and stops the flow.

A circuit breaker has three states:

- **Closed** (normal): Requests flow through normally. The breaker monitors failure rates.
- **Open** (tripped): After crossing a failure threshold (e.g., 50% errors in the last 10 seconds), the breaker "opens" and immediately rejects all requests to the failing service. No more timeouts, no more thread exhaustion.
- **Half-open** (testing): After a cool-down period (e.g., 30 seconds), the breaker allows a single test request through. If it succeeds, the breaker closes. If it fails, it stays open.

When a circuit breaker opens, Service A gets instant failures from Service B instead of slow timeouts. Instant failures are *much* better than slow failures — they don't consume threads, don't build queues, and allow Service A to respond to callers quickly (even if the response is "try again later").

## Back-Pressure: Slowing Down Input

Back-pressure is the complement to circuit breakers. Instead of accepting all incoming requests and failing internally, a service that's nearing capacity signals upstream that it can't handle more load.

Mechanisms include:

- **HTTP 429 Too Many Requests**: Explicit rate limiting response
- **HTTP 503 Service Unavailable**: Temporary rejection during overload
- **SIP 503 Service Unavailable with Retry-After header**: Tells SIP clients exactly when to try again
- **Queue depth limits**: Rejecting new messages when the queue exceeds a threshold

The key insight: **it's better to reject 10% of requests cleanly than to fail 100% of requests slowly**. A service that sheds load gracefully degrades rather than collapses.

## Recognizing Cascading Failures in Grafana

Cascading failures have a distinctive signature in monitoring:

1. **Latency increase precedes error increase**: You'll see p99 latency climbing for Service B before errors appear. This is your early warning.

2. **Error rates spike across multiple services simultaneously**: If three services all start erroring at the same time, they likely share a dependency that's failing.

3. **Thread/connection pool utilization hits 100%**: Grafana dashboards showing connection pool or thread pool utilization at max indicates threads are blocked waiting.

4. **Request rates exceed normal**: Retry storms show as abnormally high request rates.

🔧 **NOC Tip:** When investigating a multi-service outage, don't start with the service that has the most errors. Start with the service that showed latency increase FIRST. That's usually the root cause. Work downstream from there.

## Real-World Scenario: The Billing Service Cascade

Here's a scenario that plays out in telecom environments:

The billing service depends on a database that runs a slow migration during a maintenance window. The migration locks a table, causing billing queries to take 10 seconds instead of 10ms.

1. The call recording service calls billing to check storage quotas → times out
2. Call recording retries → billing queue grows further
3. The CDR processing service calls billing to rate calls → times out
4. CDR processing backs up → CDR queue grows to millions
5. The API gateway calls billing for account validation → times out
6. API responses slow down → customer dashboards hang
7. Customers can't manage their accounts → support tickets spike

The fix? Put the billing database migration in maintenance mode (Consul) or enable the circuit breaker for billing queries. The call processing pipeline doesn't actually *need* billing in real-time — calls can proceed and be billed later. But without circuit breakers, a non-critical dependency brought down critical call processing.

## Mitigation During an Active Cascade

When you're in the middle of a cascading failure:

1. **Identify the root cause service**: Look for the first service that showed degradation
2. **Break the cascade**: If possible, restart the root cause service or put it in Consul maintenance mode
3. **Shed load**: If the root cause can't be fixed immediately, enable rate limiting or circuit breakers upstream
4. **Stop retries**: If you can adjust retry configuration, reduce or disable retries temporarily
5. **Restart affected services**: Once the root cause is resolved, upstream services may need restarts to clear stuck threads and connections
6. **Monitor recovery**: Watch for "thundering herd" as all clients reconnect simultaneously after recovery

🔧 **NOC Tip:** After resolving a cascading failure, don't just watch the root cause service recover — monitor ALL affected services. Sometimes upstream services get stuck in a bad state (connection pools exhausted, threads deadlocked) and need explicit restarts even after the root cause is fixed.

## Prevention: Building Resilient Systems

Long-term prevention involves:

- **Timeout budgets**: Every inter-service call has an aggressive timeout (e.g., 1-2 seconds, not 30 seconds)
- **Circuit breakers on every dependency**: Especially cross-service and database calls
- **Bulkheads**: Isolating different request types into separate thread pools so a slow dependency only affects related requests
- **Load shedding**: Services proactively reject requests when approaching capacity
- **Async processing**: Decoupling non-critical operations (billing, CDRs) from critical path (call processing)

---

**Key Takeaways:**
1. Cascading failures start with one slow service and propagate through dependencies — they're the most dangerous failure pattern
2. Retry storms amplify overload exponentially; always check for abnormal request rates during incidents
3. Circuit breakers prevent cascade propagation by failing fast instead of failing slow
4. Latency increase precedes error increase — watch p99 latency as your early warning signal
5. When investigating multi-service outages, trace back to the FIRST service that degraded, not the loudest one
6. After resolving the root cause, monitor and potentially restart all affected upstream services

**Next: Lesson 122 — Common Failure Pattern: Database Connection Exhaustion**
