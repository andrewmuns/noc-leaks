# Lesson 93: AI/Inference — GPU Monitoring and Failure Modes
**Module 2 | Section 2.12 — Storage/AI**
**⏱ ~6min read | Prerequisites: Lesson 82**
---

## Introduction

GPUs are the heartbeat of Telnyx's AI inference infrastructure. Unlike CPUs, GPUs are thermally aggressive, memory-constrained, and fail in ways that are often silent or delayed. As a NOC engineer, you need to understand what healthy GPU operation looks like so you can instantly recognize when things go wrong — before customers notice degraded inference latency or outright failures.

This lesson covers the critical GPU metrics you'll monitor, the tools you'll use, and the failure modes you'll encounter in production.

---

## GPU Metrics That Matter

### Utilization

GPU utilization measures the percentage of time the GPU's compute cores are active. For inference workloads at Telnyx, healthy utilization typically ranges from 40–80%. Sustained 95%+ utilization means the GPU is saturated and requests are likely queuing.

### GPU Memory (VRAM)

Models must fit entirely in GPU memory. A 7B parameter model in FP16 needs ~14 GB of VRAM. If memory usage approaches the physical limit (e.g., 80 GB on an A100), you'll see out-of-memory (OOM) errors and process crashes.

### Temperature

GPUs throttle performance when they overheat. NVIDIA GPUs typically throttle at 83–90°C depending on the SKU. Sustained temperatures above 80°C warrant investigation — check airflow, fan status, and ambient data center temperature.

### ECC Errors

Modern data center GPUs (A100, H100) have Error-Correcting Code memory. ECC errors come in two flavors:

- **Correctable (CE):** Single-bit errors silently fixed by hardware. A rising count is a warning sign.
- **Uncorrectable (UE):** Multi-bit errors that corrupt data. These are critical — the GPU should be taken out of service.

### Power Draw

Each GPU has a TDP (Thermal Design Power). An A100 draws up to 300W. If power draw drops to near-zero while the GPU should be busy, the GPU may have fallen off the PCIe bus.

---

## nvidia-smi: Your Primary Tool

`nvidia-smi` is the command-line interface for NVIDIA GPU management. You'll use it constantly.

### Basic Status

```bash
nvidia-smi
```

This shows all GPUs, their utilization, memory usage, temperature, power draw, and running processes.

### Continuous Monitoring

```bash
# Refresh every 1 second
nvidia-smi -l 1

# Machine-readable CSV for scripting
nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,ecc.errors.uncorrected.volatile.total --format=csv -l 5
```

### Checking ECC Errors

```bash
# Detailed ECC error counts
nvidia-smi -q -d ECC

# Reset volatile ECC counters (after acknowledging)
nvidia-smi -r -i 0
```

### Process Listing

```bash
# See which processes use which GPUs
nvidia-smi pmon -s um -d 1
```

🔧 **NOC Tip:** When a customer reports slow inference, your first command should be `nvidia-smi` on the inference host. Check for: (1) GPU at 100% utilization (saturated), (2) memory near limit (OOM risk), (3) temperature throttling, (4) any GPU showing 0% utilization when it should be active (fallen off bus).

---

## Xid Errors: Decoding GPU Failures

NVIDIA GPUs report hardware and driver errors as **Xid errors** in the kernel log. These are your primary diagnostic signal for GPU failures.

```bash
# Check for Xid errors
dmesg | grep -i xid

# Example output
# NVRM: Xid (PCI:0000:3b:00): 79, pid=12345, GPU has fallen off the bus
```

### Critical Xid Codes

| Xid Code | Meaning | Severity | Action |
|----------|---------|----------|--------|
| 13 | Graphics engine exception | High | Reset GPU or reboot |
| 31 | GPU memory page fault | High | Check application, possible HW issue |
| 48 | Double-bit ECC error | Critical | Replace GPU |
| 63 | ECC page retirement limit | Critical | Replace GPU |
| 79 | GPU fell off the bus | Critical | Check PCIe, reseat or replace |
| 94 | Contained ECC error | Medium | Monitor — may escalate |
| 95 | Uncontained ECC error | Critical | Drain and replace |

🔧 **NOC Tip:** At Telnyx, Xid 79 ("GPU has fallen off the bus") is the most operationally impactful error. The GPU becomes completely unresponsive. The node must be drained, and often requires a full power cycle (not just a reboot) to recover. Escalate immediately when you see this.

---

## GPU Hangs and Recovery

A GPU hang occurs when the GPU stops responding to commands. Symptoms include:

- Inference requests timing out
- `nvidia-smi` hanging or returning errors
- Kernel log showing Xid errors (commonly 13, 31, or 79)

### Recovery Steps

1. **Check if nvidia-smi responds.** If it hangs, the driver is stuck.
2. **Try GPU reset:**
   ```bash
   nvidia-smi -r -i <gpu_id>
   ```
3. **If reset fails, drain the node** from the load balancer and reboot:
   ```bash
   # Drain from inference pool first
   kubectl cordon <node-name>
   kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
   
   # Then reboot
   sudo reboot
   ```
4. **If reboot doesn't recover the GPU,** a full power cycle (IPMI) is required:
   ```bash
   ipmitool -H <bmc-ip> -U admin -P <pass> chassis power cycle
   ```
5. **If the GPU fails after power cycle,** mark it for hardware replacement.

🔧 **NOC Tip:** Always drain the node from the inference pool before attempting recovery. At Telnyx, inference traffic is load-balanced across multiple GPU nodes — removing one node is far better than letting it serve errors.

---

## Monitoring GPUs in Grafana

Telnyx uses the **DCGM Exporter** (Data Center GPU Manager) to expose GPU metrics to Prometheus, which feeds Grafana dashboards.

### Key Dashboard Panels

- **GPU Utilization (%)** — per GPU, per node
- **GPU Memory Used (MB)** — watch for creeping toward limits
- **GPU Temperature (°C)** — alert threshold at 82°C
- **ECC Error Rate** — both correctable and uncorrectable
- **Power Draw (W)** — sudden drops indicate GPU failure
- **SM Clock (MHz)** — drops indicate thermal throttling
- **Inference Latency (p99)** — the customer-facing metric that ties it all together

### Alert Rules

```yaml
# Example Prometheus alert for uncorrectable ECC errors
- alert: GPUUncorrectableECC
  expr: DCGM_FI_DEV_ECC_DBE_VOL_TOTAL > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Uncorrectable ECC error on {{ $labels.gpu }} at {{ $labels.instance }}"
    runbook: "Drain node, replace GPU"

# Thermal throttling alert
- alert: GPUThermalThrottle
  expr: DCGM_FI_DEV_GPU_TEMP > 82
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "GPU {{ $labels.gpu }} at {{ $labels.instance }} exceeding 82°C"
```

🔧 **NOC Tip:** The single most useful correlation in Grafana is overlaying **inference p99 latency** with **GPU utilization**. When utilization spikes to 100% and latency climbs, you have a capacity problem. When utilization drops to 0% and latency spikes, you have a GPU failure.

---

## Multi-GPU Failure Scenarios

Telnyx inference nodes often have 4–8 GPUs. Failures can be partial or total.

### Single GPU Failure

The inference framework (e.g., vLLM, Triton) may detect the bad GPU and continue serving on remaining GPUs. However, throughput drops proportionally. If 1 of 8 GPUs fails, capacity drops ~12.5%.

**NOC Response:** Drain specific GPU from the pool if possible. If not, drain the entire node and schedule replacement.

### NVLink/NVSwitch Failure

For models that shard across multiple GPUs using NVLink, an NVLink failure is catastrophic for that model — inter-GPU communication fails or slows dramatically.

```bash
# Check NVLink status
nvidia-smi nvlink -s
nvidia-smi nvlink -e
```

**NOC Response:** The entire NVLink domain (typically all GPUs on that switch) must be drained. This can take out 4+ GPUs at once.

### Full Node GPU Failure

If the NVIDIA driver crashes or all GPUs fall off the bus, the entire node goes dark for inference.

**NOC Response:** Cordon immediately. Power cycle via IPMI. If GPUs don't recover, escalate to hardware team.

---

## Putting It All Together: A Real Scenario

**Scenario:** Grafana alert fires — inference p99 latency jumped from 200ms to 2s on node `gpu-chi-04`.

1. **Check nvidia-smi:** GPU 3 shows 0% utilization, 0 MB memory used. Other GPUs at 90%+.
2. **Check dmesg:** `Xid 79` for GPU 3 — "GPU has fallen off the bus."
3. **Immediate action:** Cordon node, drain inference pods.
4. **Attempt recovery:** `nvidia-smi -r -i 3` → fails. Full reboot → GPU 3 still missing.
5. **Power cycle via IPMI:** GPU 3 returns but with ECC errors.
6. **Decision:** Node back in service with GPU 3 excluded. Hardware ticket for GPU replacement.

The entire incident from alert to mitigation should take under 15 minutes.

---

## Key Takeaways

1. **GPU utilization, memory, temperature, and ECC errors** are your four core GPU metrics — monitor all of them continuously.
2. **nvidia-smi** is your primary diagnostic tool; learn its flags for querying specific metrics and continuous monitoring.
3. **Xid errors in dmesg** tell you exactly what went wrong with a GPU — Xid 48, 79, and 95 are critical and demand immediate action.
4. **GPU hangs require escalating recovery:** software reset → reboot → power cycle → hardware replacement.
5. **DCGM Exporter + Grafana** gives you real-time GPU visibility across the fleet; correlate GPU metrics with inference latency.
6. **Multi-GPU failures** (especially NVLink) can cascade — know the blast radius before draining.
7. **Always drain before recovering** — let the load balancer redirect traffic while you fix the problem.

---

**Next: Lesson 84 — AI/Inference: Scaling and Auto-scaling Inference**
