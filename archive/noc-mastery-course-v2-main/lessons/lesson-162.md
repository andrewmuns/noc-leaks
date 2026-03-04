# Lesson 162: Message Queues and Event-Driven Architecture
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~8 min read | Prerequisites: Lesson 139**

---

## Decoupling Services with Message Queues

In synchronous communication, the caller waits for a response. In asynchronous communication via message queues, the sender puts a message on a queue and immediately continues, unconcerned with when or how the receiver processes it.

This decoupling enables:
- Services can fail independently without cascading
- Work can be processed when resources are available
- Multiple consumers can share the workload
- Systems can handle traffic spikes without immediate processing

## Why Telecom Platforms Use Message Queues

**Call Detail Record (CDR) Processing:**
Every call generates detailed records. Writing these directly to the database during call completion would slow down call teardown. Instead:
1. Call completes
2. CDR enqueued immediately
3. Call teardown finishes quickly
4. Background workers process CDRs from queue

**Billing Events:**
Billing calculations are complex. Instead of calculating synchronously:
1. Significant billing event occurs
2. Event enqueued
3. Service continues
4. Billing workers process events

**Webhook Delivery:**
Customer webhooks must be delivered reliably. Queue provides:
- Retry on failure
- Rate limiting
- Ordering guarantees
- Dead-lettering for failed deliveries

## Kafka: The Distributed Log

Kafka is a distributed, partitioned, replicated commit log. It looks like a queue but has important differences.

### Topics and Partitions

**Topic**: A stream of records, like a queue name ("billing-events")

**Partition**: Topics are split into partitions. Each partition is an ordered, immutable log.

```
Topic: billing-events
Partition 0: [event1] [event2] [event3] [event4]
Partition 1: [event5] [event6] [event7]
Partition 2: [event8] [event9]
```

Ordering is guaranteed within a partition, but not across partitions. If you need strict ordering, use a single partition or partition by ordering key (e.g., customer_id).

### Producers and Consumers

**Producer** writes to a topic. Messages include a key (used to determine partition) and value.

**Consumer** reads from topic. Consumers are grouped into **consumer groups**:
- Each message goes to one consumer in the group
- Partitions assigned to specific consumers
- Adding consumers rebalances partitions

**Multiple consumer groups:** See the same messages independently. Useful for parallel processing (billing group calculates, analytics group stores).

### Replication and Durability

Each partition has replicas across brokers. Configurable replication factor (typically 3).

**Acknowledgment levels:**
- `acks=0`: Fire-and-forget, fastest, may lose messages
- `acks=1`: Leader confirms, good balance
- `acks=all`: All replicas confirm, safest, slowest

For billing CDRs, use `acks=all`. For metrics, `acks=1` is acceptable.

## RabbitMQ: Flexible Routing

RabbitMQ uses exchanges and queues with flexible routing:

### Model
- **Exchange**: Receives messages, routes to queues
- **Queue**: Stores messages
- **Binding**: Rules connecting exchanges to queues

### Exchange Types

**Direct**: Route by exact routing key
```
exchange: notifications
routing_key: "email" -> queue: email-queue
routing_key: "sms" -> queue: sms-queue
```

**Topic**: Route by pattern matching
```
exchange: events
routing_key: "billing.charge.success" -> billing-success queue
routing_key: "billing.charge.failed" -> billing-failed queue
routing_key: "auth.login.success" -> audit-log queue
```

**Fanout**: Broadcast to all bound queues

**Headers**: Route based on message headers, not routing key

## When to Use Which

| Aspect | Kafka | RabbitMQ |
|--------|-------|----------|
| Throughput | Very high (millions/sec) | High (50k-100k/sec) |
| Message persistence | Long retention (days/weeks) | Per-queue TTL |
| Ordering | Within partition | Within queue |
| Replay | Re-read from beginning | Consumed messages gone |
| Routing | Simple (by key) | Complex (exchanges) |
| Use case | Event streaming, logging | Task queues, RPC |

**Rule of thumb:**
- **Event streaming** (CDRs, logs, metrics): Kafka
- **Task queues** (jobs, callbacks, RPC): RabbitMQ

## Consumer Groups and Parallel Processing

### How Consumer Groups Work

Topic has 6 partitions. Consumer group has 3 consumers. Assignment:
- Consumer A: partitions 0, 1
- Consumer B: partitions 2, 3
- Consumer C: partitions 4, 5

Each consumer processes half the partitions, sharing the workload.

**Adding consumers:** Add a 4th consumer, partitions rebalance:
- Consumer A: partitions 0, 1
- Consumer B: partitions 2
- Consumer C: partitions 3, 4
- Consumer D: partitions 5

More consumers = more parallelism, up to the number of partitions.

**Partition count matters:** If topic has only 2 partitions, maximum parallelism is 2 consumers. Additional consumers sit idle.

🔧 **NOC Tip:** During incidents with queue backlogs, you can increase consumers to parallelize processing. But check partition count first - if you have 3 partitions and 3 consumers already, adding more won't help. You need to add partitions (requires topic reconfiguration) or parallelize within the consumer.


Backpressure: When Consumers Can't Keep Up

What happens when producers write faster than consumers process?

### Buffering
- Queue buffers messages in memory and disk
- Configurable retention (time or size based)
- Eventually fills up

### Backpressure Signaling
When buffer fills, system must decide:

**Reject new messages:**
- Producer gets error
- Producer must handle rejection (retry, skip, alert)
- Preserves system stability

**Drop old messages:**
- Keep newest, discard oldest
- Good for time-sensitive data (metrics)
- Bad for must-not-lose data (billing)

**Block producers:**
- Stop accepting new messages until space available
- Synchronizes producer and consumer speed
- Risk: producer blocks, downstream services wait

#### Consumer Scaling (Horizontal)
Add more consumers to process faster, up to partition limit.

🔧 **NOC Tip:** Queue depth is a critical metric:
```promql
kafka_consumer_lag{consumer_group="billing-workers"}
rabbitmq_queue_messages{queue="webhook-delivery"}
```
- Sudden spike → traffic surge or consumer failure
- Gradual climb → consumer processing slower than production
- Flat at high level → consumers can't keep up, need more instances

Alert on queue depth alerts before it causes OOM or message loss.

## Dead Letter Queues: Handling Failures

When a consumer fails to process a message:
1. Retry N times (with backoff)
2. If all retries fail, send to **dead letter queue (DLQ)**
3. Main queue continues processing
4. Human or separate process examines DLQ later

**Why DLQs matter:**
- Poison messages don't block the queue
- Failed messages can be analyzed and retried
- Prevents infinite retry loops
- Provides audit trail of failures

### DLQ Monitoring
```promql
# DLQ rate for billing-events
rate(kafka_consumer_records_consumed_total{topic="billing-events-dlq"}[5m])

# Alert if DLQ grows
kafka_consumer_lag{topic="billing-events-dlq"} > 1000
```

DLQ messages indicate consumer bugs, malformed messages, or downstream failures. Investigate any sustained DLQ growth.

## Event-Driven Architecture Patterns

### Event Sourcing
Instead of storing current state, store every event that led to it:
- Current balance = sum of all transactions
- Current config = all config change events applied
- Replay events to reconstruct any point in time

Benefits: auditability, time-travel debugging, no data loss
Trade-offs: Storage growth, replay time for large histories

### CQRS (Command Query Responsibility Segregation)
Separate read and write models:
- **Write model**: Optimized for consistency, validations
- **Read model**: Optimized for queries, denormalized
- Events synchronize between them

Example: Write billing events to Kafka; read model materializes views for dashboards.

### Saga Pattern
Long-running transactions across services:
1. Execute step 1
2. Emit event
3. Another service executes step 2
4. Continue until complete

If step fails, compensate (reverse previous steps). Used for distributed transactions without ACID.

## Real-World Scenario: The CDR Backup

**The problem:**
CDR database is down for 2 hours during maintenance. But calls keep happening, generating CDRs.

**With Kafka:**
- CDRs produced to Kafka
- Consumers can't write to dead database
- CDRs accumulate in Kafka (72-hour retention)
- Database comes back online
- Consumers resume, process the 2-hour backlog
- No CDRs lost

**Without queue:**
- CDR write fails synchronously
- Call teardown must decide: fail the call or lose the CDR
- Either way, data loss or service degradation

**Lesson:** Kafka decouples CDR production from processing. Database maintenance doesn't affect call handling. Backlog processes when systems recover.

🔧 **NOC Tip:** During queue catch-up after downtime, monitor consumer lag. Large backlogs take time to process. If lag is shrinking, you're recovering. If lag isn't shrinking or growing, investigate consumer performance. Don't declare "recovered" just because service is online - verify lag returns to normal levels.

---

**Key Takeaways:**
1. Message queues decouple producers from consumers, enabling independent scaling and failure isolation
2. Kafka provides high-throughput, durable event streaming with partition-based ordering
3. RabbitMQ provides flexible routing with exchanges for complex message distribution patterns
4. Consumer groups share partitions among consumers for parallel processing - you can't have more active consumers than partitions
5. Monitor consumer lag (queue depth) - sudden spikes indicate consumer failure, gradual growth indicates insufficient capacity
6. Dead letter queues prevent poison messages from blocking processing and enable post-failure analysis

**Next: Lesson 147 - Circuit Breakers and Retry Patterns**
