# Lesson 179: ChatOps — Operating Infrastructure Through Chat
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 108, 162**

---

Picture a traditional NOC incident: an alert fires, the on-call engineer SSHes into a server, runs diagnostic commands, copies output into a notepad, then pastes a summary into Slack. Another engineer asks "what did you find?" and the first engineer types a summary from memory. A third engineer SSHes into the same server to verify. Nobody knows exactly what commands were run or in what order.

Now picture ChatOps: the alert fires and auto-posts to Slack. An engineer types `!check sip-proxy-07 registrations` in the channel. The bot executes the query and posts the result — visible to everyone. Another engineer types `!logs sip-proxy-07 kamailio --last 5m`. The diagnostic data is right there in the channel, timestamped, searchable, and visible to the entire team simultaneously.

That's the difference ChatOps makes. It's not about being clever with bots — it's about making operations **visible, auditable, and collaborative by default**.

## Why ChatOps Works

ChatOps brings three fundamental improvements to NOC operations:

### Shared Context

When an engineer runs a command in chat, everyone in the channel sees the command *and* the result. There's no information asymmetry. The incident commander sees what the troubleshooter found without asking. The engineer who joins the incident 10 minutes late can scroll up and see everything that's happened.

This is transformative during incidents. In Lesson 108, we covered incident management processes — ChatOps is the mechanism that makes those processes work smoothly in practice.

### Built-In Audit Trail

Every chat message is timestamped and attributed to a user. When the post-mortem asks "what happened at 03:47?", you can search the channel. There's no question about what was run, when, or by whom. Compare this to SSH sessions where command history is scattered across individual terminals and may not even be preserved.

### Lower Barrier to Action

Typing `!restart sip-proxy-07` in Slack is psychologically easier than SSHing into a server and running commands directly. The chat interface provides a familiar, safe-feeling environment. More importantly, it forces the engineer to use predefined, tested commands rather than improvising at the command line — reducing the risk of typos and fat-finger errors.

## Building a ChatOps Bot

The core of ChatOps is a bot that listens for commands in chat channels and executes predefined actions. Popular frameworks include:

- **Hubot** (GitHub's original ChatOps bot, Node.js)
- **Errbot** (Python-based, extensible)
- **Slack Bolt** / **Discord.js** (platform-native SDKs)
- **Custom bots** using webhook APIs

A minimal ChatOps bot needs:

1. **Command parser**: recognizes commands (usually prefixed with `!` or `/`)
2. **Authorization layer**: checks if the user can run this command
3. **Execution engine**: runs the underlying script or API call
4. **Response formatter**: presents results clearly in chat

Here's the conceptual flow:

```
Engineer types: !status sip-proxy-07

Bot receives message → parses command ("status") and args ("sip-proxy-07")
→ checks authorization (is this user in the "noc-engineers" group?)
→ executes: curl http://sip-proxy-07:8080/health
→ formats response and posts to channel:

🟢 sip-proxy-07 Status:
  Service: kamailio (active, pid 2847, uptime 14d 7h)
  Registrations: 2,341
  Active Calls: 187
  CPU: 34% | Memory: 62% | Disk: 41%
  Consul: healthy, 3 health checks passing
```

## Essential ChatOps Commands for NOC

Design your command set around the operations your team performs daily:

**Diagnostic commands** (read-only, safe for anyone):
- `!status <service> <node>` — health check and key metrics
- `!logs <service> <node> --last <duration>` — recent log entries
- `!metrics <node> <metric-name>` — specific metric query
- `!check customer <id>` — customer status and recent call quality
- `!trace <call-id>` — trace a specific call across systems

**Action commands** (require elevated permissions):
- `!restart <service> <node>` — service restart with safety checks
- `!drain <node>` — remove from load balancer pool
- `!undrain <node>` — return to load balancer pool
- `!scale <service> <count>` — adjust replica count

**Incident commands** (covered in Lesson 164):
- `!incident create <title>` — declare an incident
- `!page <team>` — page a team
- `!timeline` — show incident timeline

🔧 **NOC Tip:** Start with read-only diagnostic commands. They're safe, immediately useful, and build team confidence in ChatOps before you add commands that modify infrastructure.

## Access Control

This is where ChatOps gets serious. Not everyone should be able to restart production services from chat. Implement role-based access control:

**Level 1 (all NOC engineers):** diagnostic commands, status checks
**Level 2 (senior NOC engineers):** service restarts, drain/undrain with confirmation
**Level 3 (NOC leads/SRE):** scaling, configuration changes, emergency procedures

For dangerous commands, implement a confirmation step:

```
Engineer: !restart kamailio sip-proxy-07

Bot: ⚠️ This will restart kamailio on sip-proxy-07.
     Current active calls: 187
     Node will be drained for 30 seconds before restart.
     Type `!confirm restart-a7f3` within 60 seconds to proceed.

Engineer: !confirm restart-a7f3

Bot: ✅ Restart initiated on sip-proxy-07
     [03:47:12] Enabling maintenance mode in Consul
     [03:47:42] Draining complete. Active calls: 0
     [03:47:43] Restarting kamailio...
     [03:47:51] Service started. Health check: passing
     [03:48:12] Registration count recovering: 847/2341
     [03:49:02] Registration count: 2,290/2341 ✅ Recovery complete
```

The confirmation token (`restart-a7f3`) is random and short-lived, preventing accidental re-execution from command history.

## Integration with Existing Tools

ChatOps becomes powerful when integrated with your monitoring and automation stack:

- **Grafana**: `!graph sip-proxy-07 cpu --last 1h` renders a chart and posts it as an image
- **Consul**: `!consul services sip-proxy` shows all instances and their health
- **Kubernetes**: `!kubectl get pods -n voice` shows pod status
- **Graylog/Loki**: `!logs` queries your log aggregation platform
- **Telnyx API**: `!check number +15551234567` looks up number configuration and recent call history

At Telnyx, integrating ChatOps with the internal API platform means engineers can quickly check customer configurations, trace calls through the system, and verify routing without switching contexts between multiple tools.

🔧 **NOC Tip:** Add a `!help` command that lists all available commands with brief descriptions. Make it context-aware — show only commands the current user is authorized to run.

## Real-World Scenario: Investigating a Quality Complaint

A customer reports poor call quality. Here's how ChatOps accelerates investigation:

```
Engineer: !check customer telnyx-cust-4821
Bot: 📊 Customer telnyx-cust-4821 (Acme Corp)
     Active SIP trunks: 2 (trunk-us-east, trunk-us-west)
     Current calls: 12
     ASR (24h): 87.3% (normal range)
     ACD (24h): 3m 42s (normal range)
     Quality alerts (24h): 3 ⚠️

Engineer: !quality telnyx-cust-4821 --last 4h
Bot: 📉 Quality Summary (last 4h):
     Total calls: 847
     Calls with MOS < 3.5: 23 (2.7%)
     Affected destinations: +44* (UK) — 19 of 23 poor-quality calls
     Common codec: G.711 μ-law
     Avg jitter on affected calls: 47ms (vs 8ms baseline)

Engineer: !trace call-id-abc123def
Bot: 🔍 Call Trace: call-id-abc123def
     Caller: +15551234567 → +442071234567
     Route: customer → sip-proxy-03 → carrier-gw-uk-01 → BT
     Duration: 2m 14s
     RTP stats: loss 3.2%, jitter 52ms, MOS 2.8
     Issue: High jitter on carrier-gw-uk-01 → BT leg
```

In five minutes, with three commands, the engineer has isolated the problem to a specific carrier route to the UK. No SSH. No switching between Grafana, Graylog, and the customer portal. Everything visible to the team.

## Anti-Patterns to Avoid

**Too many bots**: One bot with a clear command namespace beats five competing bots.

**Chatty bots**: Don't post every alert to the main channel. Use dedicated alert channels and let engineers query when needed.

**No error handling**: When a command fails, the bot should explain why — not silently fail or crash.

**Ignoring latency**: Commands that take more than a few seconds should show a "working..." indicator. Commands that take more than 30 seconds should run asynchronously and notify when complete.

---

**Key Takeaways:**
1. ChatOps makes operations visible, auditable, and collaborative by default — everyone sees commands and results
2. Start with read-only diagnostic commands before adding write/action commands
3. Implement role-based access control and confirmation prompts for dangerous operations
4. Integrate with existing tools (Grafana, Consul, Kubernetes, logs) for maximum value
5. The audit trail from chat history is invaluable for incident timelines and post-mortems
6. Avoid anti-patterns: too many bots, chatty notifications, and poor error handling

**Next: Lesson 164 — ChatOps for Incident Management**
