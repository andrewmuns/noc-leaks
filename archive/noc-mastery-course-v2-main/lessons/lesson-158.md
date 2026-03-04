# Lesson 158: Consensus Algorithms - Raft and Paxos Simplified
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~8 min read | Prerequisites: Lesson 140**

---

## The Consensus Problem

Consensus is a fundamental problem in distributed systems: how do multiple independent computers agree on a single value? This sounds simple but is surprisingly hard when nodes can fail, messages can be lost, and networks can partition.

Consensus algorithms enable:
- Distributed configuration management (etcd, Consul)
- Leader election (high availability databases)
- Distributed locking (coordination between services)
- Atomic commits (distributed transactions)

For NOC engineers, understanding consensus explains why systems behave the way they do during failures - and why certain configurations work while others don't.

## Why Consensus Is Hard

Consider three nodes trying to agree on a value. Node A proposes "value=5". But before the others acknowledge, Node A crashes. Now:
- Node A can't confirm if B and C received the proposal
- B and C might have received it (and committed to it)
- Or they might not have received it (and committed to something else)

When a new leader takes over, how does it know what was decided? Without consensus, the system could have different values on different nodes.

## Paxos: The Classic Solution

Paxos, proposed by Leslie Lamport in 1989, was the first widely known consensus algorithm. It's mathematically proven correct but notoriously difficult to understand and implement correctly.

### How Paxos Works (Simplified)

1. **Prepare Phase**: A proposer asks acceptors if they'll accept a proposal
2. **Promise Phase**: Acceptors promise not to accept lower-numbered proposals
3. **Accept Phase**: The proposer sends the value, acceptors accept it
4. **Learn Phase**: Nodes learn the chosen value

### Paxos Issues

- **Complexity**: Hard to understand, harder to implement correctly
- **Performance**: Multiple round trips for each decision
- **Edge cases**: Many corner cases that are easy to get wrong
- **No good open-source implementations** for many years

This is why most production systems moved to Raft.

## Raft: The Understandable Alternative

Raft was designed in 2014 specifically as an alternative to Paxos that would be easier to understand and implement. It provides the same guarantees but with significantly clearer mechanics.

Raft uses a **leader-based** approach where one node acts as the leader and others are followers.

## Raft Core Concepts

### Leader Election

Raft nodes are always in one of three states:
- **Follower**: Accepts log entries from leader, votes in elections
- **Candidate**: Running for leader, requests votes
- **Leader**: Handles all client requests, replicates to followers

**Election process:**
1. If a follower doesn't hear from the leader for a timeout period (150-300ms), it becomes a candidate
2. Candidate increments its term number, votes for itself, requests votes from others
3. Other nodes vote for the first candidate they hear from in this term
4. If a candidate receives majority votes, it becomes leader
5. New leader sends heartbeat to establish authority

The term number prevents "split-brain" - when two leaders exist simultaneously. Higher term wins.

### Log Replication

Once elected, the leader handles all writes:

1. Client sends command to leader
2. Leader appends to its log (uncommitted)
3. Leader replicates to followers via AppendEntries RPC
4. When majority (including leader) have the entry: it's **committed**
5. Leader applies committed entry to state machine
6. Leader tells client success
7. Leader continues replicating to remaining followers

If a follower is slow or down, the leader retries indefinitely.

🔧 **NOC Tip:** When monitoring Raft-based systems (Consul, etcd, Kubernetes), track the "leader" metric. If it fluctuates frequently, investigate network stability between nodes. Unstable leadership causes availability issues since writes require the leader.

## Quorum: The Magic Majority

Quorum is the minimum number of nodes that must agree for an operation to proceed. For a cluster of N nodes:

```
Quorum = floor(N/2) + 1
```

**Examples:**
- 3-node cluster: Quorum = 2
- 5-node cluster: Quorum = 3
- 7-node cluster: Quorum = 4

**Why quorum matters:**
- Any two quorums must overlap (have at least one node in common)
- This guarantees that committed operations are seen by subsequent leaders
- You can't have two majorities without overlap

### Quorum Failure Scenarios

**3-node cluster losing 1 node:** Quorum maintained (2 of 3 available). System continues working.

**3-node cluster losing 2 nodes:** Quorum lost (1 of 3 available). No leader, system refuses writes.

**5-node cluster losing 2 nodes:** Quorum maintained (3 of 5 available). System continues working.

**5-node cluster losing 3 nodes:** Quorum lost (2 of 5 available). System refuses writes.

**Key insight**: A 5-node cluster can survive 2 failures. A 3-node cluster can survive 1 failure.

## Why Odd Numbers Matter

Consider a 4-node cluster vs. 5-node:

**4-node cluster:**
- Quorum = 3
- Can survive losing 1 node (3 available)
- Cannot survive losing 2 nodes (2 available < 3 quorum)

**5-node cluster:**
- Quorum = 3
- Can survive losing 2 nodes (3 available)
- Cannot survive losing 3 nodes (2 available < 3 quorum)

Both have quorum of 3, but 5-node can survive one more failure. The extra node in the 4-node cluster doesn't improve availability because quorum must be majority.

**Rule of thumb**: Use odd numbers of nodes - 3 or 5. Even numbers (like 4) waste hardware for no availability benefit.

🔧 **NOC Tip:** Check your Consul and etcd cluster sizes. If you have 4 or 6 nodes, you're wasting hardware. Scale to 5 or 7 for better availability, or down to 3 for efficiency. 5 nodes is the practical maximum for most use cases - more nodes add overhead without proportional benefit.

## Log Consistency

Raft maintains these properties:

**Leader Append-Only**: Leaders never overwrite or delete entries in their log. They only append.

**Log Matching**: If two entries in different logs have the same index and term, the logs are identical up to that point.

**Leader Completeness**: If a log entry is committed, it will be present in future leaders' logs.

**State Machine Safety**: If a node has applied a log entry at a given index, no other node will apply a different entry for that index.

These guarantees are why Raft (and systems built on it) can survive failures without data loss or inconsistency.

## Failure Recovery

### Leader Failure

1. Followers stop receiving heartbeats
2. Timeout expires, follower becomes candidate
3. New term election, new leader elected
4. New leader commits no-op to establish authority
5. System continues (typically under 1 second downtime)

### Follower Failure

1. Leader tries to replicate to failed follower
2. Follower unavailable
3. Leader continues with quorum majority (other followers)
4. Operation succeeds without waiting for failed follower
5. When follower recovers, leader backfills missed entries

### Network Partition

During a partition, the side with quorum continues. The side without quorum stops accepting writes (CP behavior - Lesson 140).

When partition heals:
1. Leader with lower term steps down
2. Leader with higher term continues
3. Followers from minority catch up on missed entries
4. System converges

## Real-World Scenario: The Consul Outage

A 5-node Consul cluster spans Site A (3 nodes) and Site B (2 nodes).

**Normal operation:**
- Leader likely in Site A (majority)
- All writes succeed
- Site B replicas catch up

**Network partition (Site A and B disconnected):**
- Site A (3 nodes): Has quorum (3 >= 3), continues accepting writes
- Site B (2 nodes): No quorum (2 < 3), stops accepting writes, returns errors
- Applications in Site B can't get updated config, can't register new services

**Customer impact:**
Applications in Site B appear "down" because they can't reach Consul, even though those applications are running fine. This is confusing to diagnose.

**The fix:**
1. Recognize this is correct behavior, not a bug
2. Fix the network partition if possible
3. If partition is prolonged, consider adding a node to Site B (making it 3 nodes)
4. Or use a "witness" node in a third location to provide tiebreaker

**Lesson:** Understanding Raft explains why the "minority side down" symptom occurs. Don't restart Consul on Site B - it's correctly keeping consistency by refusing writes.

🔧 **NOC Tip:** When diagnosing Consul etcd issues during network problems, check the cluster member status on multiple nodes: `consul members` or `etcdctl member list`. If each side shows different leader information, you're partitioned. The side with fewer members is the minority and should be refusing writes.

## From Theory to Practice

Systems using Raft:
- **etcd**: Kubernetes configuration store
- **Consul**: Service discovery and configuration
- **Kafka**: Distributed log (uses similar consensus)
- **TiKV**: Distributed key-value store
- **CockroachDB**: Distributed SQL database

When these systems are "down" or refusing writes, understanding Raft helps you determine if it's a real problem or expected behavior during partitions.

---

**Key Takeaways:**
1. Raft is a leader-based consensus algorithm that's easier to understand than Paxos
2. Leader election uses term numbers to prevent split-brain - higher term always wins
3. Quorum is majority (floor(N/2)+1) - it ensures any two quorums overlap
4. Use odd numbers of nodes (3 or 5) - even numbers waste hardware without improving availability
5. During network partition, the majority side continues, minority side refuses writes to maintain consistency
6. Don't restart "failed" consensus nodes during partitions - they're protecting data consistency

**Next: Lesson 143 - Distributed Locking and Leader Election in Practice**
