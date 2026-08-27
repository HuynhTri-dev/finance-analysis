---
name: cloud_data_principles.md
description: Cloud infrastructure principles for data workloads on AWS and GCP. Covers the AWS Well-Architected Framework 6 pillars, AWS-to-GCP service mapping, network topology design (VPC, subnets, Defense in Depth), compute strategy selection, Disaster Recovery tiers, Cost Optimization tactics, observability requirements, and the Cloud Infrastructure Evaluation Checklist.
---

# Cloud Data Infrastructure Principles

## Part 1 — AWS Well-Architected Framework (6 Pillars)

Use these 6 pillars as the evaluation framework for any cloud architecture.

### Pillar 1 — Operational Excellence
Ability to run and monitor systems, automate changes, and continuously improve processes.
- CI/CD pipelines for infrastructure and application changes
- Infrastructure as Code (CloudFormation, CDK, Terraform, Pulumi)
- Runbooks for operational procedures
- Post-incident reviews and blameless culture

### Pillar 2 — Security
Protecting data, systems, and assets.
- **Least Privilege IAM**: every service/user has only the permissions it needs, nothing more
- Never use root credentials or admin roles for application workloads
- Encryption at rest (EBS, S3, RDS encryption) and in transit (TLS/HTTPS enforced)
- Network isolation: VPC, Security Groups, NACLs, WAF
- Secrets management: AWS Secrets Manager / GCP Secret Manager — never hardcode credentials

### Pillar 3 — Reliability
Ability to recover from failures and meet demand.
- Deploy across at least 2 Availability Zones (AZs) for all critical resources
- Auto-scaling to handle demand spikes
- Health checks and automated recovery (ALB health check, EC2 Auto Recovery)
- Backup and restore strategy with tested recovery procedures

### Pillar 4 — Performance Efficiency
Using computing resources efficiently.
- Right-size instances based on actual CPU/memory utilization metrics
- Choose the correct resource type per workload (compute vs. memory-optimized vs. storage-optimized)
- Leverage managed services instead of self-managing (RDS vs. self-hosted PostgreSQL)
- Use caching layers (ElastiCache, CloudFront) to reduce compute and DB load

### Pillar 5 — Cost Optimization
Avoiding unnecessary costs.
- Right-sizing: periodic review of actual vs. provisioned capacity
- On-Demand for variable/unpredictable workloads
- Reserved Instances / Savings Plans for steady-state workloads (1–3 year commitment)
- Spot Instances for fault-tolerant batch jobs, CI/CD workers, ML training
- S3 Intelligent Tiering or Glacier for cold/archive data
- Egress cost awareness: data transferred OUT of cloud is charged — factor into multi-region designs

### Pillar 6 — Sustainability
Minimizing environmental impact.
- Rightsize resources to avoid idle capacity
- Prefer managed services (serverless, PaaS) which pack workloads more efficiently
- Consider region energy mix when choosing primary region
- Note: this pillar is the least prioritized in most real-world projects but should be documented

---

## Part 2 — AWS to GCP Service Mapping

| Service Group | AWS | GCP |
|---|---|---|
| Virtual Machines | EC2 | Compute Engine |
| Serverless Functions | Lambda | Cloud Functions / Cloud Run |
| Container Orchestration | ECS / EKS | GKE (Google Kubernetes Engine) |
| Object Storage | S3 | Cloud Storage |
| Relational DB (managed) | RDS / Aurora | Cloud SQL / AlloyDB |
| NoSQL Key-value | DynamoDB | Firestore / Bigtable |
| Cache | ElastiCache (Redis / Memcached) | Memorystore |
| Message Queue | SQS | Cloud Pub/Sub |
| Event Streaming | Kinesis / MSK (Kafka) | Pub/Sub / Dataflow |
| CDN | CloudFront | Cloud CDN |
| Load Balancer | ALB (L7) / NLB (L4) | Cloud Load Balancing |
| DNS | Route 53 | Cloud DNS |
| IAM | AWS IAM | Cloud IAM |
| Secrets Management | Secrets Manager / Parameter Store | Secret Manager |
| Data Warehouse | Redshift | BigQuery |
| Data Pipeline | Glue / Step Functions | Dataflow / Cloud Composer |
| IaC | CloudFormation / CDK | Deployment Manager / Terraform |
| Monitoring | CloudWatch | Cloud Monitoring (formerly Stackdriver) |
| Distributed Tracing | X-Ray | Cloud Trace |
| Logging | CloudWatch Logs | Cloud Logging |
| Container Registry | ECR | Artifact Registry |

---

## Part 3 — Network Topology Design

### VPC Segmentation

Mandatory separation between public-facing and private resources:

```
VPC (e.g., 10.0.0.0/16)
│
├── Public Subnet (10.0.1.0/24) — per AZ
│   ├── Load Balancer (ALB / NLB)
│   └── NAT Gateway (for outbound internet from private subnet)
│
└── Private Subnet (10.0.2.0/24) — per AZ
    ├── Application servers (EC2, ECS tasks)
    └── Databases (RDS, ElastiCache)
```

Rules:
- Public subnet: resources that must accept inbound internet traffic
- Private subnet: application servers and databases — no direct internet access
- NAT Gateway allows private subnet to make outbound requests (OS updates, external API calls)

### Defense in Depth (Multi-layer Security)

```
Internet
    │
WAF (OWASP Top 10 rules, rate limiting)
    │
Load Balancer
    │
Security Group (stateful, instance-level: allow port 443 from LB only)
    │
Network ACL (stateless, subnet-level: explicit allow/deny rules)
    │
Application Server
    │
Security Group (DB layer: allow port 5432 from app servers only)
    │
Database (RDS / ElastiCache)
```

Each layer provides independent protection. A failure or bypass at one layer
does not automatically expose the next.

### High Availability

Deploy all critical resources across at least 2 Availability Zones (AZs):

```
Region (e.g., ap-southeast-1)
├── AZ-a
│   ├── App Server instances
│   └── RDS Primary
└── AZ-b
    ├── App Server instances
    └── RDS Standby (Multi-AZ Standby for automatic failover)
```

A single AZ outage does not take down the system.

---

## Part 4 — Compute Strategy Selection

| Model | Best fit | Trade-offs |
|---|---|---|
| VM (EC2 / Compute Engine) | Continuous workloads requiring OS-level control, licensed software | Manual patching, scaling, AMI management |
| Container (ECS / EKS / GKE) | Microservices, portable deployments, independent scaling | Requires orchestration layer (Kubernetes or ECS) |
| Serverless (Lambda / Cloud Functions) | Event-driven, irregular traffic, minimize ops overhead | Cold start latency, execution time limits, vendor lock-in |
| PaaS / Managed Service (RDS, ElastiCache, DynamoDB) | Reduce operational burden for databases and middleware | Less control, potential cost premium at scale |

Decision rule: prefer managed services and serverless unless there is a specific reason
to operate at a lower abstraction level. Apply KISS/YAGNI — don't over-engineer compute.

---

## Part 5 — Disaster Recovery Tiers

Four DR strategies, ordered by increasing cost and decreasing RTO/RPO:

| Strategy | Description | RTO | RPO | Cost |
|---|---|---|---|---|
| Backup & Restore | Periodic backups to S3/GCS. Restore from backup on disaster. | Hours | Hours to days | Lowest |
| Pilot Light | Core services (DB replicas) running at minimal scale in DR region. Infrastructure code ready to deploy. | Tens of minutes | Minutes | Low |
| Warm Standby | Full scaled-down replica of production running in DR region. Can scale up quickly on failover. | Minutes | Seconds to minutes | Medium |
| Multi-site Active-Active | Full production capacity in multiple regions simultaneously. Traffic routed by DNS/load balancer. | Near zero | Near zero | Highest |

**RTO (Recovery Time Objective)**: maximum acceptable downtime
**RPO (Recovery Point Objective)**: maximum acceptable data loss

Choose the tier that matches the business's actual RTO/RPO requirements.
Over-engineering DR is expensive; under-engineering it is risky.

---

## Part 6 — Cost Optimization Tactics

### Right-sizing Process
1. Deploy with a reasonable initial estimate
2. Collect 2–4 weeks of actual CPU/Memory/Network utilization data from CloudWatch / Cloud Monitoring
3. Identify instances consistently below 20% CPU utilization → candidates for downsizing
4. Resize during a maintenance window and validate performance

### Pricing Model Selection

| Workload type | Recommended pricing model |
|---|---|
| Unpredictable, variable traffic | On-Demand |
| Steady-state workloads (web servers, databases) | Reserved Instances / Savings Plans (1–3 year) |
| Batch jobs, fault-tolerant processing, ML training | Spot Instances / Preemptible VMs |
| Serverless | Pay-per-use (Lambda, Cloud Functions) |

### Storage Tiering

| Access frequency | Storage tier |
|---|---|
| Frequent access | S3 Standard / Cloud Storage Standard |
| Infrequent access (30+ days) | S3 Standard-IA / Nearline |
| Rare access (90+ days) | S3 Glacier Instant / Coldline |
| Archive (180+ days, retrieval hours acceptable) | S3 Glacier Deep Archive / Archive |

### Data Transfer Cost Awareness
- Ingress (data INTO cloud): usually free
- Egress (data OUT of cloud): charged per GB — easily overlooked
- Cross-AZ transfer within same region: small but non-zero cost (factor in for high-traffic multi-AZ architectures)
- Cross-region transfer: significant cost — design data locality carefully in multi-region systems

---

## Part 7 — Observability Requirements

A production data system must have all three pillars of observability:

### Logging
- Centralized log aggregation: CloudWatch Logs / Cloud Logging
- Log structured output (JSON) for queryability
- Log retention policy (compliance + cost balance)
- Sensitive data must not appear in logs (PII, credentials)

### Metrics
- Resource utilization: CPU, memory, disk, network
- Application metrics: request latency (p50, p90, p99), error rate, throughput
- Database metrics: query latency, connection pool usage, replication lag, slow queries
- Cache metrics: hit rate, miss rate, eviction rate

### Distributed Tracing
- Required when a single user request spans multiple microservices
- Tools: AWS X-Ray, Google Cloud Trace, OpenTelemetry (vendor-neutral)
- Trace sampling rate: typically 5–10% in production (adjust based on volume and cost)

### Alerting
- Alert on actionable signals, not every metric spike
- Use SLO-based alerts (e.g., "error rate > 1% for 5 minutes")
- PagerDuty / OpsGenie for on-call escalation
- Avoid alert fatigue — tune thresholds and suppress non-actionable noise

---

## Part 8 — Cloud Infrastructure Evaluation Checklist

Use this checklist when reviewing an existing architecture or proposing a new one.

### Data Layer
- [ ] Schema is appropriately normalized for the use case (OLTP vs OLAP)?
- [ ] Each microservice has its own database — no cross-service direct DB access?
- [ ] Consistency model (strong vs. eventual) is explicitly chosen for each data flow?
- [ ] Indexes are designed based on actual query patterns (no over-indexing, no missing indexes)?

### Cloud Infrastructure
- [ ] Network has clear Public/Private subnet separation?
- [ ] Critical resources are deployed Multi-AZ?
- [ ] There is a Disaster Recovery strategy appropriate to the business's RTO/RPO?
- [ ] IAM roles follow least-privilege — no root/admin credentials used by services?
- [ ] Optimal pricing model is applied per workload (Reserved for steady-state, Spot for batch)?
- [ ] Egress costs have been factored into the architecture design?

### Caching and Performance
- [ ] Cache tier and pattern are explicitly identified for hot data paths?
- [ ] Cache invalidation strategy exists (TTL + active invalidation)?
- [ ] Cache stampede mitigation is in place for hot keys?
- [ ] Back-of-envelope capacity estimation has been done to justify resource sizing?

### Observability
- [ ] Centralized logging is configured (CloudWatch Logs / Cloud Logging)?
- [ ] Distributed tracing is available for requests spanning multiple services?
- [ ] SLO-based alerting is configured for key metrics (latency, error rate, saturation)?
- [ ] Database slow query logging is enabled and monitored?

### Diagram Limitation Note

Mermaid (`erDiagram`, `flowchart`, `graph`) can be rendered directly in Markdown/chat
and is suitable for ERD and logic flow diagrams. However, **Mermaid does not support
official AWS/GCP architecture icons**. Infrastructure diagrams in Mermaid use text
labels and boxes only — they are not compliant with AWS Architecture Icons standards.

For stakeholder-facing cloud topology diagrams with official icons, use:
- draw.io (free, supports AWS/GCP icon sets)
- Lucidchart
- Excalidraw (informal but fast)
- AWS Application Composer

Always note this limitation when producing cloud topology diagrams in Markdown.
