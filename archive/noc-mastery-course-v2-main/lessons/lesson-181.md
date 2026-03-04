# Lesson 181: Infrastructure as Code — Ansible Basics for NOC
**Module 5 | Section 5.4 — Automation**
**⏱ ~8 min read | Prerequisites: Lesson 156, 158**

---

Imagine you need to update a TLS certificate on 47 SIP proxy servers. You could SSH into each one, copy the certificate, update the configuration, and restart the service. That's 47 × 4 steps = 188 manual operations. On server 31, you realize you made a typo on servers 12-15. How do you fix just those? How do you even know which servers have the correct config and which don't?

Infrastructure as Code (IaC) solves this class of problem. Instead of manually configuring servers, you define the desired state in version-controlled files and use tools to enforce that state. Ansible is the most approachable IaC tool for NOC engineers because it's agentless (uses SSH), uses human-readable YAML, and doesn't require installing anything on target hosts.

## Why Ansible for NOC Engineers

NOC engineers aren't developers — you're not building applications. But you manage infrastructure, respond to incidents, and maintain system configurations. Ansible fits perfectly because:

1. **Agentless**: Uses SSH, which is already set up on every server
2. **YAML syntax**: Readable without programming experience
3. **Push-based**: You run it when needed, not a daemon running constantly
4. **Idempotent**: Running the same playbook twice is safe — it only changes what needs changing

That last point — idempotency — is crucial. If you run a shell script that appends a line to a config file, running it twice adds the line twice. An Ansible task that ensures a line exists in a config file does nothing on the second run. This means you can always run the playbook to enforce the desired state without fear of breaking things.

## The Inventory: Defining Your Infrastructure

Ansible's inventory defines what hosts exist and how they're organized:

```ini
# inventory/production.ini

[sip_proxies]
sip-proxy-01 ansible_host=10.0.1.11
sip-proxy-02 ansible_host=10.0.1.12
sip-proxy-03 ansible_host=10.0.1.13

[media_servers]
media-01 ansible_host=10.0.2.11
media-02 ansible_host=10.0.2.12

[databases]
db-primary ansible_host=10.0.3.11
db-replica-01 ansible_host=10.0.3.12
db-replica-02 ansible_host=10.0.3.13

[us_east:children]
sip_proxies
media_servers

[all:vars]
ansible_user=noc-admin
ansible_ssh_private_key_file=~/.ssh/noc-key
```

Groups let you target operations precisely. `ansible sip_proxies -m ping` checks all SIP proxies. Groups can contain other groups (`us_east` includes both `sip_proxies` and `media_servers`). Variables can be set at group or host level.

🔧 **NOC Tip:** Keep your inventory in Git alongside your playbooks. When someone asks "what servers do we have?", the inventory is the single source of truth — not a spreadsheet or someone's memory.

## Playbooks: Defining Desired State

A playbook is a YAML file describing tasks to execute on target hosts:

```yaml
# playbooks/update-tls-cert.yml
---
- name: Update TLS certificates on SIP proxies
  hosts: sip_proxies
  become: yes

  vars:
    cert_source: files/certs/telnyx-sip-2024.pem
    key_source: files/certs/telnyx-sip-2024.key
    cert_dest: /etc/kamailio/tls/server.pem
    key_dest: /etc/kamailio/tls/server.key

  tasks:
    - name: Copy TLS certificate
      copy:
        src: "{{ cert_source }}"
        dest: "{{ cert_dest }}"
        owner: kamailio
        group: kamailio
        mode: '0644'
      notify: restart kamailio

    - name: Copy TLS private key
      copy:
        src: "{{ key_source }}"
        dest: "{{ key_dest }}"
        owner: kamailio
        group: kamailio
        mode: '0600'
      notify: restart kamailio

    - name: Verify certificate validity
      command: openssl x509 -in {{ cert_dest }} -noout -dates
      register: cert_dates
      changed_when: false

    - name: Display certificate expiry
      debug:
        msg: "Certificate valid: {{ cert_dates.stdout }}"

  handlers:
    - name: restart kamailio
      service:
        name: kamailio
        state: restarted
```

Let's break down why this works:

- **`hosts: sip_proxies`**: Targets only the SIP proxy group
- **`become: yes`**: Executes with sudo privileges
- **`copy` module**: Copies files only if they've changed (idempotent)
- **`notify`**: Triggers the handler only if the task made a change
- **`handler`**: Restarts Kamailio only if a certificate was actually updated
- **`changed_when: false`**: The verification command doesn't count as a change

Run it: `ansible-playbook -i inventory/production.ini playbooks/update-tls-cert.yml`

All 47 servers get the correct certificate. Kamailio restarts only on servers where the cert changed. If you run it again, nothing happens because the certs are already correct.

## Understanding Idempotency

Idempotency is the property that makes Ansible safe. Here's the difference:

**Non-idempotent (shell script):**
```bash
echo "listen=udp:10.0.1.11:5060" >> /etc/kamailio/kamailio.cfg
# Running twice = duplicate line = broken config
```

**Idempotent (Ansible):**
```yaml
- name: Ensure listen directive exists
  lineinfile:
    path: /etc/kamailio/kamailio.cfg
    line: "listen=udp:10.0.1.11:5060"
    state: present
# Running twice = line exists = no change
```

Ansible modules like `copy`, `template`, `lineinfile`, `service`, and `package` are all idempotent by design. The `command` and `shell` modules are not — they always run — so use them only when no built-in module exists, and pair them with `creates` or `changed_when` to make them safe.

🔧 **NOC Tip:** Before running any playbook on production, use `--check` (dry-run) and `--diff` to see what would change:
```
ansible-playbook playbook.yml --check --diff
```

## Modules You'll Use Daily

Ansible has hundreds of modules. NOC engineers need about a dozen:

| Module | Purpose | Example |
|--------|---------|---------|
| `ping` | Test connectivity | Verify all hosts are reachable |
| `command` | Run a command | Check disk space, service status |
| `service` | Manage services | Start, stop, restart, enable |
| `copy` | Copy files | Deploy configs, certificates |
| `template` | Copy with variables | Config files with host-specific values |
| `lineinfile` | Edit single lines | Add/modify config directives |
| `package` | Install packages | Ensure software is installed |
| `user` | Manage users | Create service accounts |
| `file` | Manage files/dirs | Set permissions, create directories |
| `uri` | HTTP requests | Health check APIs |
| `wait_for` | Wait for conditions | Wait for port to be open after restart |

## Real-World Scenario: Emergency Configuration Update

A security vulnerability is discovered in Kamailio's SIP parser. The fix is a configuration change that needs to be applied to all SIP proxies immediately:

```yaml
# playbooks/emergency-sip-parser-fix.yml
---
- name: Apply emergency SIP parser security fix
  hosts: sip_proxies
  become: yes
  serial: 2  # Two hosts at a time

  tasks:
    - name: Check current config version
      command: grep "# CONFIG_VERSION" /etc/kamailio/kamailio.cfg
      register: config_version
      changed_when: false
      failed_when: false

    - name: Skip if already patched
      meta: end_host
      when: "'v2.4.7-security1' in config_version.stdout"

    - name: Apply security patch to config
      blockinfile:
        path: /etc/kamailio/kamailio.cfg
        insertafter: "# SECURITY SETTINGS"
        block: |
          # CONFIG_VERSION v2.4.7-security1
          # CVE-2024-XXXX mitigation
          max_uri_length = 2048
          max_header_size = 8192
        marker: "# {mark} SECURITY PATCH CVE-2024-XXXX"
      notify: reload kamailio

    - name: Verify service health after reload
      uri:
        url: "http://{{ ansible_host }}:8080/health"
        status_code: 200
      retries: 5
      delay: 3

  handlers:
    - name: reload kamailio
      service:
        name: kamailio
        state: reloaded
```

Key safety features: `serial: 2` applies to only two hosts at a time (not all at once), the skip-if-patched check ensures idempotency, and health verification after each batch catches problems before proceeding.

## Connecting Ansible to NOC Operations

Ansible integrates with the tools from previous lessons:

- **ChatOps (Lesson 163)**: `!ansible run update-tls-cert --limit sip-proxy-07` triggers playbooks from Slack
- **Automated runbooks (Lesson 162)**: Ansible playbooks *are* automated runbooks with better safety
- **Consul (from monitoring lessons)**: Use Consul's inventory plugin to dynamically discover hosts instead of maintaining static lists

The progression: manual SSH → shell scripts → Ansible playbooks → ChatOps-triggered Ansible → fully automated remediation.

---

**Key Takeaways:**
1. Ansible is agentless (SSH-based), YAML-driven, and idempotent — perfect for NOC engineers
2. Inventory files define your infrastructure as code — version control them
3. Playbooks describe desired state; Ansible figures out what changes are needed
4. Idempotency means running a playbook twice is safe — it only changes what needs changing
5. Always use `--check --diff` before production runs to preview changes
6. Combine Ansible with ChatOps for team-visible, auditable infrastructure operations

**Next: Lesson 166 — Ansible for NOC — Practical Playbooks**
