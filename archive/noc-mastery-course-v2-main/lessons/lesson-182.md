# Lesson 182: Ansible for NOC — Practical Playbooks
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 165**

---

In Lesson 165, we covered Ansible fundamentals — inventory, playbooks, idempotency. Now we build practical playbooks that NOC engineers use daily: rolling restarts, configuration management with handlers, secrets with Vault, and ad-hoc commands for quick investigations.

## Rolling Restarts: The Serial Keyword

Restarting a service across a cluster requires care. Restart everything at once and you have an outage. Ansible's `serial` keyword controls how many hosts are updated simultaneously:

```yaml
# playbooks/rolling-restart-kamailio.yml
---
- name: Rolling restart of Kamailio SIP proxies
  hosts: sip_proxies
  become: yes
  serial: 1  # One host at a time

  tasks:
    - name: Drain host from Consul
      command: consul maint -enable -service=sip-proxy -reason="rolling-restart"
      delegate_to: localhost

    - name: Wait for active calls to complete
      shell: |
        for i in $(seq 1 30); do
          active=$(curl -s http://{{ ansible_host }}:8080/metrics | grep active_calls | awk '{print $2}')
          if [ "$active" -eq 0 ]; then exit 0; fi
          sleep 2
        done
        exit 1
      register: drain_result
      failed_when: drain_result.rc != 0

    - name: Restart Kamailio
      service:
        name: kamailio
        state: restarted

    - name: Wait for service to be healthy
      uri:
        url: "http://{{ ansible_host }}:8080/health"
        status_code: 200
      retries: 10
      delay: 3
      register: health_check

    - name: Re-enable in Consul
      command: consul maint -disable -service=sip-proxy
      delegate_to: localhost

    - name: Wait for registrations to recover
      shell: |
        baseline={{ expected_registrations | default(2000) }}
        threshold=$(( baseline * 70 / 100 ))
        for i in $(seq 1 60); do
          current=$(curl -s http://{{ ansible_host }}:8080/metrics | grep registration_count | awk '{print $2}')
          if [ "$current" -ge "$threshold" ]; then exit 0; fi
          sleep 5
        done
        exit 1
      register: reg_recovery
      failed_when: reg_recovery.rc != 0
```

The flow per host: drain → wait for calls to finish → restart → verify health → re-enable → wait for registrations to recover → move to next host. If any step fails, Ansible stops and doesn't proceed to the next host, preventing a cascade of failures.

🔧 **NOC Tip:** Use `serial: "25%"` for large clusters. On a 20-node cluster, this restarts 5 at a time — faster than one-at-a-time while maintaining 75% capacity. Adjust based on your redundancy level.

## Handlers: Restart Only When Needed

Handlers are Ansible's way of triggering actions conditionally. A handler only runs when the task that notifies it actually makes a change:

```yaml
- name: Configure Kamailio logging level
  hosts: sip_proxies
  become: yes

  tasks:
    - name: Set log level to 2 (info)
      lineinfile:
        path: /etc/kamailio/kamailio.cfg
        regexp: '^debug='
        line: 'debug=2'
      notify: reload kamailio

    - name: Configure log facility
      lineinfile:
        path: /etc/kamailio/kamailio.cfg
        regexp: '^log_facility='
        line: 'log_facility=LOG_LOCAL0'
      notify: reload kamailio

    - name: Set max TCP connections
      lineinfile:
        path: /etc/kamailio/kamailio.cfg
        regexp: '^tcp_max_connections='
        line: 'tcp_max_connections=4096'
      notify: restart kamailio  # TCP changes require full restart

  handlers:
    - name: reload kamailio
      service:
        name: kamailio
        state: reloaded

    - name: restart kamailio
      service:
        name: kamailio
        state: restarted
```

If the log level is already `2` and the facility is already `LOG_LOCAL0`, neither handler fires — no unnecessary restarts. If only the TCP setting changed, only the restart handler fires. Handlers run once at the end of all tasks, even if notified multiple times.

This is powerful for configuration management. You can define dozens of configuration tasks, and the service only restarts when something actually changed. Compare this to a shell script that always restarts "just in case."

## Ansible Vault: Managing Secrets

NOC playbooks often need credentials — database passwords, API keys, TLS private keys. Ansible Vault encrypts sensitive data:

```bash
# Create an encrypted variables file
ansible-vault create vars/secrets.yml

# Edit it later
ansible-vault edit vars/secrets.yml
```

Inside `vars/secrets.yml`:
```yaml
db_password: "s3cur3_p4ssw0rd_h3r3"
telnyx_api_key: "KEY01234567890ABCDEF"
grafana_admin_password: "gr4f4n4_s3cur3"
```

Use in playbooks:
```yaml
- name: Configure database connection
  hosts: app_servers
  become: yes
  vars_files:
    - vars/secrets.yml

  tasks:
    - name: Deploy database config
      template:
        src: templates/db-config.j2
        dest: /etc/app/database.yml
        mode: '0600'
```

The template (`db-config.j2`) references the encrypted variables:
```yaml
database:
  host: db-primary.internal
  port: 5432
  password: {{ db_password }}
```

Run with: `ansible-playbook playbook.yml --ask-vault-pass` or store the vault password in a file (protected by filesystem permissions).

🔧 **NOC Tip:** Never put passwords or API keys in plain-text playbooks or inventory files. If it's in Git without Vault encryption, assume it's compromised. Rotate credentials and encrypt them properly.

## Ad-Hoc Commands: Quick Investigations

Not everything needs a playbook. Ansible's ad-hoc mode runs one-off commands across multiple hosts:

```bash
# Check disk space on all SIP proxies
ansible sip_proxies -i inventory/production.ini -a "df -h /var/log"

# Check Kamailio service status
ansible sip_proxies -m service -a "name=kamailio"

# Find which hosts have high memory usage
ansible all -a "free -m" | grep -A 2 "Mem:"

# Check certificate expiry across all SIP proxies
ansible sip_proxies -a "openssl x509 -in /etc/kamailio/tls/server.pem -noout -enddate"

# Collect Kamailio version on all hosts
ansible sip_proxies -a "kamailio -v"

# Check NTP sync status
ansible all -a "timedatectl status" | grep "synchronized"
```

Ad-hoc commands are invaluable during investigations. Instead of SSHing into hosts one by one to check something, a single command checks all of them simultaneously and presents results together.

## Practical Playbook: Health Check and Report

A playbook that generates a cluster health report — useful for shift handoffs or regular health reviews:

```yaml
# playbooks/cluster-health-report.yml
---
- name: Generate SIP cluster health report
  hosts: sip_proxies
  gather_facts: yes

  tasks:
    - name: Get service status
      service_facts:

    - name: Get registration count
      uri:
        url: "http://{{ ansible_host }}:8080/metrics"
        return_content: yes
      register: metrics
      failed_when: false

    - name: Get active call count
      shell: "echo '{{ metrics.content }}' | grep active_calls | awk '{print $2}'"
      register: active_calls
      changed_when: false
      when: metrics.status == 200

    - name: Compile host report
      set_fact:
        host_status:
          hostname: "{{ inventory_hostname }}"
          kamailio: "{{ ansible_facts.services['kamailio.service'].state | default('unknown') }}"
          uptime: "{{ ansible_uptime_seconds | int // 86400 }} days"
          cpu_cores: "{{ ansible_processor_vcpus }}"
          memory_mb: "{{ ansible_memtotal_mb }}"
          memory_free_mb: "{{ ansible_memfree_mb }}"
          disk_used: "{{ ansible_mounts | selectattr('mount', 'equalto', '/') | map(attribute='size_total') | first }}"
          active_calls: "{{ active_calls.stdout | default('N/A') }}"

    - name: Display report
      debug:
        msg: "{{ host_status }}"
```

Run this before shift handoff: `ansible-playbook cluster-health-report.yml`. Every host's status in one view.

## Real-World Scenario: Certificate Expiry Emergency

It's Friday afternoon. Someone notices TLS certificates expire Monday. 47 servers need new certs by EOD:

**Without Ansible**: SSH into each server, copy cert, update config, restart service. At 10 minutes per server (being generous), that's nearly 8 hours. Someone will make a mistake. The weekend is ruined.

**With Ansible**:

1. Place new certs in the playbook's `files/` directory
2. Run: `ansible-playbook update-tls-cert.yml --check --diff` (5 min review)
3. Run: `ansible-playbook update-tls-cert.yml` (15 min execution with rolling restart)
4. Verify: `ansible sip_proxies -a "openssl x509 -in /etc/kamailio/tls/server.pem -noout -enddate"` (30 seconds)

Total time: 20 minutes. Zero mistakes. Full audit trail. Weekend saved.

## Organizing Your Playbooks

As your collection grows, structure matters:

```
ansible/
├── inventory/
│   ├── production.ini
│   └── staging.ini
├── playbooks/
│   ├── rolling-restart.yml
│   ├── update-tls-cert.yml
│   ├── cluster-health-report.yml
│   └── emergency-patches/
│       └── cve-2024-xxxx.yml
├── roles/
│   ├── kamailio/
│   └── monitoring/
├── vars/
│   ├── common.yml
│   └── secrets.yml  (vault encrypted)
├── templates/
│   └── kamailio.cfg.j2
└── files/
    └── certs/
```

Version control everything (except vault passwords). Tag releases so you can reference "the playbook we used for the March cert update."

---

**Key Takeaways:**
1. Use `serial` for rolling restarts — never restart an entire cluster simultaneously
2. Handlers trigger only when tasks make changes, preventing unnecessary service disruptions
3. Ansible Vault encrypts secrets — never store credentials in plaintext files
4. Ad-hoc commands are invaluable for quick multi-host investigations during incidents
5. Structure playbooks in Git with clear organization — inventory, playbooks, vars, templates
6. A 20-minute Ansible run replaces 8 hours of manual SSH work with zero human error

**Next: Lesson 167 — CI/CD Pipelines — Understanding the Deployment Pipeline**
