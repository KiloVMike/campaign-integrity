# Campaign Integrity — One-Page Solution Brief

**Track:** Martech — Campaign review and approval  
**Team:** MAL 4 · 1 November 2026  
**Core Assertion:** A version-aware approval system that guarantees the campaign being scheduled is the exact campaign a reviewer approved.

---

## 1. The Problem: Detached Approval, Not Missing Status

A marketing campaign is a high-stakes proposal comprising an objective, target audience, delivery channel, and financial budget. In standard industry tooling, approval is recorded as a mutable status flag (`status = "APPROVED"`) on the campaign container. That status survives subsequent mutations to the content it was intended to authorise.

### The Silent Mutation Failure
1. **Proposal:** Marketer submits a campaign with a ₹5,00,000 budget and Tier-1 audience.
2. **Authorisation:** Reviewer inspects and approves the proposal.
3. **Mutation:** Marketer silently alters the budget to ₹8,00,000 and expands the audience.
4. **State Drift:** The dashboard continues to display a green **APPROVED** badge.
5. **Execution:** The campaign is scheduled and launched without secondary review.

No error is raised. The approval was authentic, but it validated content that no longer exists. **The root problem is not absent status; it is detached approval.**

---

## 2. Core Invariant & Solution

Campaign Integrity eliminates boolean status drift by binding every approval decision cryptographically and relationally to an immutable revision. Approval is **derived**, never stored as an editable flag.

### The Core Invariant
$$\text{active\_schedule}(c) \implies \text{current\_revision}(c).\text{state} = \text{APPROVED} \land \text{decision}.\text{revision\_id} = \text{current\_revision}(c).\text{id} \land \text{decision}.\text{content\_hash} = \text{current\_revision}(c).\text{content\_hash}$$

Every mutation post-submission executes a **copy-on-write** revision fork. The previous approval remains preserved in historical logs but is immediately invalid for scheduling. If an active schedule exists, editing the campaign automatically revokes and cancels that schedule within the same atomic transaction.

---

## 3. Users and Roles (Separation of Duties)

| Role | Core Responsibilities | Explicit Prohibitions |
|---|---|---|
| **Marketer** | Author proposals, edit drafts, submit for review, revise after feedback, schedule approved revisions, monitor audit trail. | Cannot approve any campaign; cannot bypass review workflow. |
| **Reviewer** | Review current submitted revisions, approve, or request changes with mandatory written feedback. May author their own proposals. | Cannot approve self-authored campaigns; cannot edit proposal content post-submission; cannot approve stale revisions. |
| **System Engine** | Enforce state transitions, compute SHA-256 content hashes, execute row-locked scheduling checks, log tamper-evident audit events. | Cannot interpret network timeouts or disconnects as successful authorizations. |

---

## 4. End-to-End Lifecycle Journey

```
[1. Draft] ──(Submit)──> [2. In Review] ──(Request Changes)──> [3. Changes Requested]
                                │                                      │
                         (Approve Rev 2)                                 │ (Revise: Rev 2 Draft)
                                │                                      ▼
                                ▼                               [4. Resubmit Rev 2]
                         [5. Approved] ──(Schedule)──> [6. Scheduled]
                                │                              │
                                └──(Post-Approval Edit)────────┘
                                               │
                                               ▼
                                 [7. Rev 3 Draft Created]
                            (Approval Invalidated · Schedule Revoked)
```

---

## 5. Architectural Scope Boundaries

### In Scope
- **Domain Entities:** Proposals (objective, audience, channel, budget in paise, display name).
- **Revision Control:** Append-only immutable revision tree; copy-on-write edits upon modification.
- **Verification:** SHA-256 content hashing across material fields (`objective`, `audience`, `channel`, `budget`).
- **Enforcement:** Atomic scheduling eligibility checks under PostgreSQL row locks (`SELECT ... FOR UPDATE`).
- **Auto-Cancellation:** Transactional schedule revocation upon post-approval revision creation.
- **Network Resilience:** Client outbox sync, client-generated UUID idempotency keys, duplicate tap suppression.
- **Observability:** Structured JSON logs, domain metrics, correlation IDs, and runbook investigation queries.

### Out of Scope (Deliberate Non-Goals)
- Third-party ad-platform publishing (Meta, Google Ads) — system governs eligibility, not ad delivery.
- Creative media rendering, storage, or CDN pipeline.
- Payment gateway integrations, billing reconciliation, and spend tracking.
- External notification transports (email, SMS, push) — client polling / UI notifications used.
- Dual multi-party approvals (architected as a clean extension point in ADR-001).

---

## 6. Business Rules

| Rule ID | Statement | Enforcement Mechanism |
|---|---|---|
| **BR-1** | Only campaigns in an approved state are eligible for scheduling. | `ScheduleService` database transaction under exclusive row lock. |
| **BR-2** | Approval must explicitly reference the current active revision and match its SHA-256 content hash. | Composite domain verification: `revision_id` + `content_hash` equality check. |
| **BR-3** | Modifying an approved or submitted proposal invalidates prior approval for scheduling. | Copy-on-write revisioning: marks prior revision superseded; spawns fresh `DRAFT`. |
| **BR-4** | Every proposal field is material in v1; any field edit generates a new revision. | Canonical content serialization + SHA-256 hash comparison. |
| **BR-5** | Network retries and duplicate user actions must yield exactly one domain effect and audit record. | Idempotency keys backed by database unique constraints (`request_id`). |
| **BR-6** | Reviewers are strictly forbidden from approving campaigns they authored (separation of duties). | Service-layer authorization check: `actor_id != campaign.creator_id`. |

---

## 7. Measurable Success Conditions

| ID | Target Metric / Guarantee | Validation Method |
|---|---|---|
| **S1** | Complete lifecycle (create $\to$ request changes $\to$ revise $\to$ approve $\to$ schedule) under 2 minutes. | Timed end-to-end walkthrough (`08-walkthrough-script.md`). |
| **S2** | Zero active schedules associated with non-current, superseded, or unapproved revisions. | PostgreSQL invariant test, concurrent race conditions, direct SQL assert. |
| **S3** | Exactly-once state mutation and audit trail emission under retried commands. | Idempotency stress tests (`T-13`, `T-19`) with duplicate payloads. |
| **S4** | Client termination (crash/kill) mid-flight recovers cleanly without state inconsistency. | Process-kill recovery simulation (`T-20`, `T-21`) via local SQLite outbox. |
| **S5** | 100% committed transitions attributable to actor, timestamp, revision, and correlation ID. | Append-only `audit_events` table query in incident runbook. |
| **S6** | Outdated reviewer actions produce deterministic conflict responses (`409 Conflict`), never silent writes. | Stale revision review test (`T-10`). |
| **S7** | Seamless architectural traceability from UI badges to API contracts down to DB relational schemas. | Presentation walkthrough and `03-low-level-design.md` schema verification. |

---

## 8. Defensibility & Technology Foundation

- **Single Atomic Gate:** Scheduling verification and schedule creation happen in one atomic PostgreSQL transaction under row lock (`SELECT FOR UPDATE`). No external race window exists.
- **Derived, Not Stored:** Approval is computed from `(current_revision, active_decision, matching_hash)`. Eliminates boolean flag drift entirely.
- **Resilient Mobile Protocol:** React Native + SQLite outbox with exponential backoff ensures zero lost actions during offline transitions or abrupt client termination.
- **Honest System Boundaries:** Clear separation between approval integrity (owned) and ad serving (external).
- **Core Technology Stack:** React Native + Expo + TypeScript (Mobile UI/Local Outbox) · Node.js + TypeScript (Modular Monolith API) · PostgreSQL (ACID System of Record).

> **"The campaign that gets scheduled is the campaign that was approved."**
