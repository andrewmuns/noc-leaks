# Lesson 107: Ingress, Load Balancing, and External Access

**Module 3 | Section 3.2 — Kubernetes**
**⏱ ~6 min read | Prerequisites: Lesson 90**

---

In Lesson 90, we explored how Kubernetes Services enable pod-to-pod communication within the cluster. But how does traffic from the outside world — customer SIP registrations, API calls, webhook responses — actually reach those internal services? That's the job of Ingress resources and external load balancing.

## The Problem: Kubernetes Services Are Internal by Default

A ClusterIP Service gives a pod a stable address *inside* the cluster. But it's invisible to the internet. Customers hitting `sip.telnyx.com` or `api.telnyx.com` need a path from the public internet through the cluster's network boundary to the right service.

Kubernetes provides three mechanisms for external access, each with different tradeoffs.

## NodePort: The Simplest (and Roughest) Approach

A NodePort Service opens a specific port (30000-32767) on *every* node in the cluster. Traffic hitting any node on that port gets routed to the backing pods.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sip-proxy
spec:
  type: NodePort
  ports:
    - port: 5060
      targetPort: 5060
      nodePort: 30060
  selector:
    app: sip-proxy
```

This works but has problems: you expose high-numbered ports (not standard SIP ports), you need external load balancing across nodes, and every node must handle the traffic even if it doesn't run the pod. For production telecom, NodePort is rarely used directly — it's a building block.

## LoadBalancer: Cloud-Integrated External Access

A LoadBalancer Service asks the cloud provider (AWS, GCP, or bare-metal integration like MetalLB) to provision an external load balancer pointing at the NodePorts.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  type: LoadBalancer
  ports:
    - port: 443
      targetPort: 8443
```

The cloud creates an external IP, configures health checks, and distributes traffic. This is how many services get exposed, but each LoadBalancer Service gets its own external IP and cloud load balancer — expensive at scale.

For SIP and RTP traffic, LoadBalancer Services are common because these protocols need direct L4 (TCP/UDP) access. SIP doesn't fit neatly into HTTP routing rules.

## Ingress: HTTP/HTTPS Routing Done Right

Ingress solves the "one load balancer per service" problem for HTTP traffic. A single Ingress Controller (itself exposed via LoadBalancer or NodePort) handles all HTTP/HTTPS traffic and routes based on host and path.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  rules:
    - host: api.telnyx.com
      http:
        paths:
          - path: /v2/calls
            pathType: Prefix
            backend:
              service:
                name: call-control
                port:
                  number: 8080
          - path: /v2/messages
            pathType: Prefix
            backend:
              service:
                name: messaging
                port:
                  number: 8080
    - host: portal.telnyx.com
      http:
        paths:
          - path: /
            backend:
              service:
                name: portal-ui
                port:
                  number: 3000
```

One external IP serves `api.telnyx.com` and `portal.telnyx.com`, routing to different backend services based on hostname and path. This is dramatically more efficient than separate load balancers.

## Ingress Controllers: The Implementation Layer

An Ingress resource is just a *declaration* — "I want traffic for this host/path to go here." The Ingress Controller is the actual reverse proxy that implements the routing. Popular controllers include:

- **NGINX Ingress Controller** — Most widely used, mature, well-documented
- **HAProxy Ingress** — High-performance, excellent for TCP/UDP workloads
- **Traefik** — Auto-discovers services, good TLS support
- **Envoy-based (Contour, Emissary)** — Modern, gRPC-native, observability-rich

The choice matters. For telecom, you need a controller that handles TCP/UDP passthrough (for SIP), supports connection draining (for safe deployments), and provides detailed metrics for monitoring.

## TLS Termination at the Ingress Layer

Ingress controllers typically handle TLS termination — decrypting HTTPS at the edge and forwarding plain HTTP to backend pods. This centralizes certificate management:

```yaml
spec:
  tls:
    - hosts:
        - api.telnyx.com
      secretName: api-tls-cert
```

The certificate is stored as a Kubernetes Secret. When it's renewed, update the Secret and the controller picks it up — no pod restarts needed.

🔧 **NOC Tip:** When customers report TLS errors connecting to APIs, check the Ingress controller's TLS configuration first. Common issues: expired certificates in the Secret, missing intermediate certificates in the chain, or TLS version mismatch (client requires TLS 1.2 but controller is configured for 1.3 only). Use `openssl s_client -connect api.telnyx.com:443 -servername api.telnyx.com` to test the presented certificate from outside.

## External Traffic Policy and Source IP Preservation

By default, Kubernetes uses `externalTrafficPolicy: Cluster`, meaning traffic can bounce between nodes before reaching the pod. This hides the client's real IP address behind the node's IP — devastating for SIP, where IP-based authentication relies on seeing the customer's source IP.

Setting `externalTrafficPolicy: Local` keeps traffic on the node where it arrived:

```yaml
spec:
  externalTrafficPolicy: Local
```

This preserves the source IP but introduces a tradeoff: if a node has no pods for that service, traffic to that node is dropped. Your external load balancer must health-check and only route to nodes with running pods.

🔧 **NOC Tip:** If SIP customers using IP authentication suddenly get 403 Forbidden responses after a Kubernetes migration, check `externalTrafficPolicy`. If it's `Cluster`, the SIP proxy sees the Kubernetes node IP instead of the customer's IP, and authentication fails. Switch to `Local` and ensure external health checks are configured.

## Real-World Troubleshooting Scenario

**Situation:** After a cluster upgrade, 30% of API requests to `api.telnyx.com` are getting 502 Bad Gateway errors.

**Investigation:**
1. Check Ingress controller logs — they show connection refused to backend pods
2. `kubectl get pods -l app=api-gateway` — pods are running but some are on new nodes
3. The Ingress controller's backend configuration still points to old pod IPs
4. The controller hadn't detected the pod IP changes because its sync interval was too long

**Resolution:** Force a resync of the Ingress controller's backend configuration. Set a shorter sync interval to prevent future lag during cluster changes.

**Root cause:** During node rotation, pods got new IPs, but the Ingress controller's endpoint watcher had a stale cache.

## Path-Based vs. Host-Based Routing

Two routing strategies serve different needs:

**Host-based routing** directs traffic by domain name. `api.telnyx.com` → API service, `portal.telnyx.com` → Portal service. Clean separation, each team owns their domain.

**Path-based routing** splits traffic within a domain. `api.telnyx.com/v2/calls` → Call Control, `api.telnyx.com/v2/messages` → Messaging. Single domain, multiple backends. Requires careful path ordering (most specific first).

In practice, Telnyx uses both: host-based routing separates major products, path-based routing splits within the API.

---

**Key Takeaways:**

1. Ingress resources route external HTTP/HTTPS traffic to internal services based on host and path rules
2. Ingress Controllers (NGINX, HAProxy, Traefik) are the actual reverse proxies implementing routing
3. TLS termination at the Ingress layer centralizes certificate management
4. `externalTrafficPolicy: Local` preserves source IPs — critical for SIP IP-based authentication
5. LoadBalancer Services are still needed for non-HTTP protocols like SIP (UDP/TCP on port 5060)
6. During incidents, check Ingress controller logs and backend endpoint sync when seeing 502 errors

**Next: Lesson 92 — Namespaces, Resource Limits, and Multi-Tenancy**
