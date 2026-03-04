# Lesson 141: Common Failure Pattern — Network Partition and Split Brain
**Module 4 | Section 4.5 — Failure Patterns**
**⏱ ~7 min read | Prerequisites: Lesson 97, 84**

---

## When the Network Splits

A network partition occurs when two parts of your infrastructure lose the ability to communicate with each other while both remain internally functional. Unlike a server crash (which is obvious), a partition is subtle — both sides think they're fine and the other side is broken.

In a multi-datacenter telecom platform, partitions happen when the network link between sites fails. Each site can still process calls locally, but they can't coordinate with the other site. This creates the conditions for the most dangerous failure pattern in distributed systems: split brain.

## Understanding Partitions

Consider Telnyx operating two data centers: DC-East and DC-West. Under normal operation, they share state through Consul, replicate databases, and coordinate load balancing.

When the network link between DC-East and DC-West fails:

- **DC-East** sees all DC-West services as unhealthy (Consul health checks fail across the partition)
- **DC-West** sees all DC-East services as unhealthy
- Each side is fully functional internally
- Neither side knows whether the other has actually failed or is just unreachable

This ambiguity is the core problem. Is DC-West down, or is just the network between them down? The correct response differs dramatically:
- If DC-West is down: DC-East should absorb all traffic
- If the network is partitioned: both sites should be cautious about assuming full responsibility

## Split Brain: Two Leaders

Split brain occurs when a partition causes both sides to elect themselves as the authoritative leader. This is catastrophic for systems that require a single leader:

### Database Split Brain
If a PostgreSQL primary is in DC-East and a replica is in DC-West, and the network partitions, DC-West might promote its replica to primary (thinking DC-East is dead). Now both sites have a writable primary database. Both accept writes. When the partition heals, the databases have diverged — conflicting data that can't be automatically merged.

### Consul Split Brain
Consul uses the Raft consensus algorithm (Lesson 142) which requires a majority (quorum) to elect a leader. In a 5-node Consul cluster with 3 nodes in DC-East and 2 in DC-West:

- DC-East has 3/5 nodes — it has quorum, elects a leader, continues operating normally
- DC-West has 2/5 nodes — it lacks quorum, cannot elect a leader, becomes read-only

This is by design. Raft prevents split brain by requiring a majority. The minority side sacrifices availability to maintain consistency (a CP tradeoff — Lesson 140).

But what if the cluster is split 2/3 and 2/3 with one node that crashed? Or what if you have an even number of nodes? These edge cases are where split brain can emerge.

🔧 **NOC Tip:** Always deploy Consul (and etcd, ZooKeeper) clusters with an odd number of nodes — 3 or 5. Even numbers (4 or 6) can split evenly, making quorum ambiguous. With 5 nodes, a partition always has a clear majority.

## How Partitions Manifest in Telecom

### SIP Processing
Each data center runs SIP proxies and media servers. During a partition:
- Calls arriving at DC-East are processed normally
- Calls arriving at DC-West are processed normally
- But calls that require coordination (transfer between sites, shared conference bridges, centralized number lookup) fail
- Both sites might route outbound calls through the same carrier trunk, potentially exceeding carrier capacity limits

### Service Discovery
Consul in the minority partition can't elect a leader. Services relying on Consul for configuration or service discovery start failing. Even though the services themselves are running fine, they can't resolve their dependencies through Consul.

### Database Replication
PostgreSQL streaming replication breaks across the partition. The replica in the remote site falls behind. If automatic failover triggers (Patroni), you get split brain. If it doesn't trigger, the remote site loses write capability.

## Detecting Partitions

Partitions have a distinctive signature in monitoring:

1. **Consul health**: Large number of services simultaneously marked critical — especially all services in one site
2. **Cross-site latency/loss**: Network monitoring shows 100% loss to remote site IPs
3. **Asymmetric health**: All services in one site are healthy, all services in the other appear failed
4. **Consul leader changes**: Frequent leader elections or leadership gaps in Consul

```bash
# Check Consul cluster status
consul operator raft list-peers

# Check which nodes are alive
consul members

# Check if there's a leader
consul operator raft list-peers | grep leader

# Check cross-site connectivity
ping dc-west-node-01
traceroute dc-west-node-01
```

🔧 **NOC Tip:** The key differentiator between "a bunch of services crashed" and "network partition" is the pattern. If ALL services in one site simultaneously go critical while all services in another site are fine, it's almost certainly a network partition, not independent service failures.

## Recovery: Healing the Partition

When the network link is restored:

1. **Consul converges**: The Raft cluster reunites. If the minority side hasn't done anything destructive, state converges automatically.

2. **Database reconciliation**: If no split brain occurred (automatic failover was properly fenced), the replica reconnects and catches up from the WAL stream. If split brain occurred, manual intervention is required to identify the authoritative primary and discard or merge divergent writes.

3. **Service reconnection**: Services re-register with Consul, health checks pass, and load balancing resumes across both sites.

4. **Traffic rebalancing**: DNS/load balancer changes that diverted traffic during the partition need to be reverted. GeoDNS should re-enable the recovered site.

### The Thundering Herd Problem
When a partition heals, everything reconnects simultaneously. Consul floods with re-registrations. Databases replay backed-up replication. DNS queries spike. This sudden reconnection surge can itself cause problems.

🔧 **NOC Tip:** After a partition heals, monitor for 15-30 minutes. The reconnection surge can cause temporary service degradation. If possible, re-enable the recovered site gradually rather than all at once.

## Prevention and Preparation

### Network Redundancy
- Multiple independent network paths between data centers
- Different physical routes (not just different fibers in the same conduit)
- Different carriers for cross-site connectivity
- Monitoring of all network paths independently

### Quorum Design
- Odd-numbered consensus clusters (3 or 5 nodes)
- Nodes distributed across failure domains but with majority in the primary site
- Witness/tiebreaker nodes in a third location for 2-site deployments

### Fencing
- Automated failover systems must use fencing (STONITH — Shoot The Other Node In The Head) to prevent split brain
- Before a replica is promoted, the old primary must be confirmed dead or explicitly shut down
- Patroni uses DCS (Distributed Configuration Store, e.g., Consul) for leader election with fencing

### Partition Testing
- Regularly test partition scenarios in staging environments
- Use network simulation tools (tc, iptables) to create artificial partitions
- Verify that consensus systems behave correctly during and after partitions

---

**Key Takeaways:**
1. Network partitions occur when infrastructure segments lose connectivity while remaining internally functional
2. Split brain — two leaders emerging during a partition — is the most dangerous consequence and can cause data divergence
3. Odd-numbered consensus clusters (3 or 5 nodes) prevent ambiguous quorum splits
4. The pattern signature is ALL services in one site going critical simultaneously while the other site is healthy
5. After partition healing, monitor for thundering herd effects from simultaneous reconnection
6. Fencing mechanisms prevent split brain by ensuring only one primary exists at any time

**Next: Lesson 126 — Traffic Patterns: Daily, Weekly, and Seasonal Cycles**
