# Lesson 184: Terraform Basics — Infrastructure Provisioning
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 165**

---

Ansible configures servers that already exist. Terraform creates the servers themselves — along with networks, load balancers, DNS records, firewall rules, and every other piece of infrastructure. While NOC engineers may not write Terraform daily, understanding it is essential because infrastructure changes are a major incident category, and reading a Terraform plan tells you exactly what's about to change.

## Declarative vs. Imperative

Ansible is mostly imperative: "do these steps in order." Terraform is declarative: "make reality match this description." You don't tell Terraform *how* to create a server — you describe what the server should look like, and Terraform figures out the steps.

```hcl
# This declares WHAT should exist, not HOW to create it
resource "aws_instance" "sip_proxy" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.2xlarge"
  
  tags = {
    Name        = "sip-proxy-09"
    Service     = "voice"
    Environment = "production"
  }
}
```

If `sip-proxy-09` doesn't exist, Terraform creates it. If it exists but with the wrong instance type, Terraform modifies (or recreates) it. If it exists and matches, Terraform does nothing.

## The State File: Terraform's Memory

Terraform's most important concept is the **state file** — a JSON file that maps your declared resources to real infrastructure. When you write `resource "aws_instance" "sip_proxy"`, Terraform needs to know: does this already exist? If so, what's its current state?

The state file records:
- Resource IDs (e.g., AWS instance ID `i-0abc123def456789`)
- Current attribute values
- Dependencies between resources
- Metadata for resource management

**This is critical for NOC operations.** The state file is the source of truth for what Terraform manages. If someone modifies infrastructure outside of Terraform (via the AWS console, for example), the state file becomes out of sync — a condition called **drift**. Drift causes unpredictable behavior on the next Terraform run.

🔧 **NOC Tip:** If you're troubleshooting an infrastructure issue and notice something doesn't match what Terraform says should exist, you may be looking at drift. Report it to the infrastructure team — don't manually fix it, as that makes the drift worse.

## Plan and Apply: The Safety Net

Terraform's workflow has two critical steps:

### `terraform plan`
Shows what Terraform *would* do without making changes. This is the review step:

```
$ terraform plan

Terraform will perform the following actions:

  # aws_instance.sip_proxy[9] will be created
  + resource "aws_instance" "sip_proxy" {
      + ami           = "ami-0abcdef1234567890"
      + instance_type = "c5.2xlarge"
      + tags          = {
          + "Name"        = "sip-proxy-09"
          + "Service"     = "voice"
          + "Environment" = "production"
        }
    }

  # aws_security_group_rule.sip_ingress will be updated in-place
  ~ resource "aws_security_group_rule" "sip_ingress" {
      ~ cidr_blocks = [
          - "10.0.0.0/8",
          + "10.0.0.0/8",
          + "172.16.0.0/12",    # New CIDR added
        ]
    }

  # aws_instance.old_proxy will be destroyed
  - resource "aws_instance" "old_proxy" {
      - ami           = "ami-old123" -> null
      - instance_type = "c5.xlarge" -> null
    }

Plan: 1 to add, 1 to change, 1 to destroy.
```

The symbols tell the story:
- **`+` (green)**: Resource will be created
- **`~` (yellow)**: Resource will be modified in-place
- **`-` (red)**: Resource will be destroyed

### `terraform apply`
Executes the plan. Requires confirmation unless `--auto-approve` is used (which should only happen in CI/CD pipelines with proper safeguards).

**Reading Terraform plans is a core NOC skill.** When the infrastructure team says "we're applying a Terraform change," you should be able to read the plan and understand the impact on your services.

🔧 **NOC Tip:** Watch for resources being **destroyed and recreated** (marked with `-/+`). In AWS, changing certain instance attributes requires destroying the old instance and creating a new one — this causes downtime for that resource. A `-/+` on a database instance, for example, is a major concern.

## Providers: The Integration Layer

Terraform uses **providers** to interact with different platforms. Each provider knows how to manage resources for a specific service:

- **AWS provider**: EC2 instances, VPCs, security groups, Route53 DNS
- **GCP provider**: Compute instances, networks, Cloud DNS
- **Cloudflare provider**: DNS records, page rules, load balancers
- **Kubernetes provider**: Deployments, services, configmaps
- **Consul provider**: Key-value pairs, service registrations
- **Telnyx provider**: (If available) Phone numbers, SIP trunks, messaging profiles

This means a single Terraform configuration can provision an AWS server, configure its DNS in Cloudflare, register it in Consul, and set up monitoring — all as one atomic operation.

## Terraform in NOC Context

### Understanding Infrastructure Changes

When infrastructure changes cause incidents, you need to understand what changed:

```bash
# What was the last Terraform apply?
# Check CI/CD pipeline logs for the terraform plan output

# What does Terraform currently manage?
terraform state list
# → aws_instance.sip_proxy[0]
# → aws_instance.sip_proxy[1]
# → aws_security_group.sip_ingress
# → aws_route53_record.sip_dns
# ...

# What are the details of a specific resource?
terraform state show aws_instance.sip_proxy[3]
# → Shows all attributes: IP, instance type, security groups, etc.
```

### Reading State for Troubleshooting

During incidents, Terraform state can answer questions like:
- "What security group rules are applied to the SIP proxies?" → `terraform state show aws_security_group.sip_ingress`
- "What DNS records point to our SIP cluster?" → `terraform state show aws_route53_record.sip_dns`
- "How many instances are in the SIP proxy autoscaling group?" → `terraform state show aws_autoscaling_group.sip_proxy`

### Applying Pre-Approved Changes

Some NOC operations involve Terraform:
- Scaling up infrastructure during traffic spikes
- Updating DNS records for failover
- Modifying firewall rules to block attack traffic

For these, pre-written Terraform configurations with variable inputs let NOC engineers make infrastructure changes safely:

```bash
# Scale SIP proxy cluster from 8 to 12 instances
terraform apply -var="sip_proxy_count=12" -target=aws_autoscaling_group.sip_proxy
```

## Real-World Scenario: The Security Group Incident

2 AM alert: SIP registrations from a major customer suddenly dropping. Investigation shows the customer's SIP traffic is being rejected at the network level — packets aren't reaching the SIP proxies.

The NOC engineer checks recent changes:
```
[01:30] Terraform apply: security group update for sip-proxy cluster
```

Checking the Terraform plan from that apply reveals:
```hcl
~ resource "aws_security_group_rule" "sip_customer_ingress" {
    ~ cidr_blocks = [
        "203.0.113.0/24",
      - "198.51.100.0/24",    # This CIDR was REMOVED
        "192.0.2.0/24",
      ]
  }
```

The customer's IP range (`198.51.100.0/24`) was accidentally removed from the security group. The fix:

```bash
# Revert to previous Terraform state
# (The infra team reverts the code change in Git, then applies)
terraform apply
```

Without understanding Terraform, the NOC engineer might have spent hours checking SIP configurations, DNS, and application logs — when the problem was a firewall rule change visible in the Terraform plan.

## Terraform vs. Ansible: When to Use Each

| Aspect | Terraform | Ansible |
|--------|-----------|---------|
| Purpose | Create/destroy infrastructure | Configure existing infrastructure |
| Approach | Declarative (desired state) | Mostly imperative (ordered tasks) |
| State | Maintains state file | Stateless (checks each run) |
| Scope | Cloud resources, networking | OS configuration, application deployment |
| Typical user | DevOps/SRE | NOC/DevOps |

They complement each other: Terraform provisions a server, Ansible configures it. In practice, many organizations use Terraform for infrastructure and Ansible for configuration, with CI/CD pipelines coordinating both.

🔧 **NOC Tip:** When someone says "we're making an infrastructure change," ask: "Is it a Terraform change or an Ansible change?" Terraform changes affect infrastructure (servers, networks, DNS). Ansible changes affect configuration (services, files, packages). The troubleshooting approach differs significantly.

---

**Key Takeaways:**
1. Terraform is declarative — you describe desired state, Terraform figures out the changes needed
2. The state file maps Terraform resources to real infrastructure — drift between them causes problems
3. `terraform plan` shows what would change; reading plans is a core NOC skill
4. Watch for destroy-and-recreate operations (`-/+`) which cause resource downtime
5. Terraform state is a powerful troubleshooting tool for understanding current infrastructure configuration
6. Terraform provisions infrastructure; Ansible configures it — they complement each other

**Next: Lesson 169 — Technical Communication — Writing Clear Status Updates**
