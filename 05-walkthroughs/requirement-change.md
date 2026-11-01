# Requirement Change Walkthrough

**Future requirement: campaigns above ₹1,00,000 need two distinct approvals**

This is the realistic change used in the presentation. It is deliberately close to the existing design: the revision model already supports multiple decisions per revision. The change tests whether the architecture can absorb a new policy without reopening the core guarantee.

---

## The new rule

> A campaign proposal with a budget of ₹1,00,000 or more must be approved by **two distinct reviewers** before it can be scheduled. Campaigns below the threshold continue to need one approval.

This is a plausible martech policy: higher spend needs finance plus brand sign-off. It is also a useful stress test because it changes:

- the definition of “approved”,
- the schedule’s relationship to decisions,
- the reviewer experience,
- the API response shape,
- the database constraints.

It does **not** change the revision model, the content hash, the idempotency protocol, or the source of truth.

---

## Why revision 4 is the example

Revision 4 has a budget of ₹8,00,000, which is above the ₹1,00,000 threshold. For this walkthrough, imagine it is **submitted after the policy is enabled**, so its policy snapshot is `required_approvals = 2`. Arjun’s single approval would not be enough. The campaign would need:

- `DEC-9003` from Arjun (`USR-REV-1`), brand;
- a second approval from Priya (`USR-REV-2`), finance.

The schedule would be rejected with `APPROVAL_QUORUM_NOT_MET` until both decisions exist for the **same revision** and the **same content hash**.

The actual revision 4 in the v1 fixture was submitted before the policy existed, so it keeps its one-approval snapshot. That is not a loophole; it is the deliberate consequence of Option B and test T-31. A policy change applies to new submissions, not to reviews already in flight.

---

## What changes, and what does not

| Area | Change | Unchanged |
|---|---|---|
| Revision model | Add a policy snapshot to the revision | Immutable revisions; copy-on-write edits |
| Approval model | Multiple `APPROVED` decisions per revision; quorum evaluated | Decision still binds `revision_id` + `content_hash` |
| Schedule model | Schedule records a **set** of decisions, not one | One active schedule per campaign |
| Scheduling check | `hasValidApprovalSet` replaces `findApproved` | Current revision + hash + row lock |
| API | `approvalProgress`; new error code | Envelope, idempotency, status codes |
| Mobile | “1 of 2 approvals” progress; reviewer sees existing approvals | Pending/confirmed/conflict model |
| Audit | One event per decision; schedule metadata lists decision IDs | Append-only, same transaction |
| Idempotency | No change | Same key protocol |
| Source of truth | No change | PostgreSQL |
| Outbox | No change | Same command queue |

The core sentence still holds:

> The campaign that gets scheduled is the campaign that was approved — by enough people.

---

## Design options

### Option A — Evaluate the policy at scheduling time

The schedule transaction reads the campaign’s current budget and asks, “How many approvals does this need now?”

**Pros:** simple; no policy snapshot column.

**Cons:** a policy change can retroactively invalidate an in-flight approval, or retroactively make a campaign schedulable. A reviewer who approved under a one-approval rule may be surprised that a second approval is now required. The goalposts move.

### Option B — Snapshot the policy when the revision is submitted

At submit time, the server records `approval_policy_version` and `required_approvals` on the revision. The quorum is evaluated against that snapshot.

**Pros:** predictable; the reviewer knows the rule that applied when the revision entered review; a later policy change does not rewrite history.

**Cons:** a revision submitted before a policy change may need only one approval even if the policy is stricter now. This is acceptable if the policy is versioned and the change is communicated. It is the same principle as “the approval names the content”: the requirement names the policy.

**Chosen.** The policy is part of the review context, not a floating global.

### Option C — A full workflow engine

Model review stages, roles, quorums, and escalation in a workflow definition.

**Pros:** expressive; supports many policies.

**Cons:** a large new dependency and a new source of truth. The team would spend the day learning the engine instead of defending the invariant. Rejected for v1; the policy seam is enough.

---

## Domain change

### Current

```ts
function isApprovalValid(campaign, revision, decision): boolean {
  return decision?.outcome === 'APPROVED'
    && decision.revisionId === revision.id
    && decision.revisionContentHash === revision.contentHash
    && campaign.currentRevisionId === revision.id
    && revision.state === 'APPROVED';
}
```

### New

```ts
export interface ApprovalPolicy {
  version: string;             // e.g. "2026-11-dual-approval"
  requiredApprovals: number;   // 1 or 2
  minimumBudgetMinor: number;  // 0 or 10_000_000 (₹1,00,000)
}

export function requiredApprovalsFor(
  budgetMinor: number,
  policy: ApprovalPolicy,
): number {
  return budgetMinor >= policy.minimumBudgetMinor
    ? policy.requiredApprovals
    : 1;
}

export function hasValidApprovalSet(input: {
  campaign: Campaign;
  revision: CampaignRevision;
  decisions: ApprovalDecision[];
  required: number;
}): boolean {
  if (input.campaign.currentRevisionId !== input.revision.id) return false;
  if (input.revision.state !== 'APPROVED') return false;

  const distinctReviewers = new Set(
    input.decisions
      .filter((d) =>
        d.outcome === 'APPROVED' &&
        d.revisionId === input.revision.id &&
        d.revisionContentHash === input.revision.contentHash)
      .map((d) => d.reviewerId),
  );

  return distinctReviewers.size >= input.required;
}
```

The revision’s state becomes `APPROVED` only when the quorum is met. A single approval on a two-approval revision leaves the revision in `IN_REVIEW` and records a partial approval.

### Revision state with partial approvals

```
IN_REVIEW --first approval--> IN_REVIEW (approvalProgress 1/2)
IN_REVIEW --second approval--> APPROVED
IN_REVIEW --request changes--> CHANGES_REQUESTED (any reviewer can block)
```

A “request changes” decision is terminal for the revision, even if another reviewer has already approved. The marketer must create a new revision. This is the conservative choice: a blocker should not be outvoted by a partial approval.

---

## Data model change

### 1. Policy snapshot on the revision

```sql
alter table campaign_revisions
  add column approval_policy_version text not null default 'v1-single',
  add column required_approvals integer not null default 1
    check (required_approvals between 1 and 5);

-- Existing rows keep one approval.
```

Why on the revision, not the campaign: the policy applies to the review of a specific revision. A later revision may be submitted under a different policy.

### 2. Allow multiple approvals per revision

```sql
drop index ux_one_approval_per_revision;
```

The unique `(revision_id, reviewer_id)` stays. It guarantees distinct reviewers at the database level.

### 3. Record the approval set on the schedule

A schedule can no longer point to a single decision. Add a join table:

```sql
create table schedule_approvals (
  schedule_id uuid not null references schedules(id),
  decision_id uuid not null references approval_decisions(id),
  primary key (schedule_id, decision_id)
);
```

Migrate existing schedules:

```sql
insert into schedule_approvals (schedule_id, decision_id)
select id, approval_decision_id from schedules;
```

Then make `schedules.approval_decision_id` nullable for the transition, and stop writing it. In a later release, drop it.

**Expand/contract sequence:**

1. **Expand:** add `schedule_approvals`, backfill from `approval_decision_id`, keep both columns.
2. **Dual-write:** new schedules write the join rows and, for compatibility, the first decision ID.
3. **Switch reads:** `CampaignView` reads the join table.
4. **Contract:** drop `approval_decision_id` and its composite foreign key.

This avoids a flag day and keeps old schedules explainable.

### 4. Schedule eligibility query

```sql
select count(distinct d.reviewer_id) as approved
from approval_decisions d
where d.revision_id = $1
  and d.outcome = 'APPROVED'
  and d.revision_content_hash = $2;
```

The schedule transaction compares `approved` with `revision.required_approvals`.

---

## Application change

### Decision service

When a reviewer approves:

1. Insert the decision (unique per reviewer/revision).
2. Count distinct approvals for the revision.
3. If `count >= required_approvals`, set revision `APPROVED`; otherwise leave it `IN_REVIEW`.
4. Append `DECISION_APPROVED` with `approvalProgress: { approved, required }`.
5. Return the campaign view with progress.

When a reviewer requests changes:

1. Insert the decision.
2. Set revision `CHANGES_REQUESTED` immediately, regardless of other approvals.
3. Append `DECISION_CHANGES_REQUESTED`.

### Schedule service

Replace:

```ts
const decision = await decisions.findApproved(tx, revision.id);
if (!decision) throw new DomainError('APPROVAL_INVALID', 409);
```

with:

```ts
const approvals = await decisions.listApproved(tx, revision.id);
const distinct = new Set(approvals.map((d) => d.reviewerId));
if (distinct.size < revision.requiredApprovals) {
  throw new DomainError('APPROVAL_QUORUM_NOT_MET', 409, {
    approved: distinct.size,
    required: revision.requiredApprovals,
  });
}
if (!approvals.every((d) => d.revisionContentHash === revision.contentHash)) {
  throw new DomainError('CONTENT_HASH_MISMATCH', 409);
}
```

Then insert the schedule and the `schedule_approvals` rows in the same transaction.

### Segregation of duties

The existing rule `reviewer_id ≠ campaign.created_by` still applies. The new rule adds `distinct reviewer_id`; the same reviewer cannot satisfy two approvals. The unique constraint enforces it.

A future extension could require different **roles** (brand + finance), not just different people. That is a policy dimension, not a schema redesign: add `required_role` to the policy and check it in `hasValidApprovalSet`.

---

## API change

### Decision response

```json
{
  "data": {
    "decision": {
      "id": "DEC-9003",
      "revisionId": "REV-1042-4",
      "outcome": "APPROVED",
      "reviewerId": "USR-REV-1"
    },
    "approvalProgress": {
      "approved": 1,
      "required": 2,
      "state": "IN_REVIEW"
    },
    "campaign": { "...": "..." }
  }
}
```

### Schedule rejection

```json
{
  "error": {
    "code": "APPROVAL_QUORUM_NOT_MET",
    "message": "This campaign needs 2 approvals; 1 has been recorded.",
    "details": {
      "approved": 1,
      "required": 2,
      "currentRevision": { "id": "REV-1042-4", "state": "IN_REVIEW" }
    },
    "retryable": false
  }
}
```

### Campaign view

```json
{
  "approvalStatus": "IN_REVIEW",
  "approvalProgress": { "approved": 1, "required": 2 },
  "canSchedule": {
    "allowed": false,
    "code": "NOT_APPROVED",
    "message": "Waiting for 1 more approval."
  },
  "allowedActions": ["VIEW_HISTORY"]
}
```

The client does not need a new endpoint. It renders the progress object.

---

## Mobile change

| Screen | Change |
|---|---|
| Campaign detail | “Approval 1 of 2” chip; reviewer names and timestamps |
| Review queue | Shows partial approvals; a second reviewer can see who has approved |
| Decision sheet | After approving, the button becomes “Approval recorded — waiting for 1 more” |
| Schedule button | Disabled with “Waiting for 1 more approval” |
| History | Each decision is a separate row; the schedule shows the approval set |
| Conflict | Unchanged: stale revision, lost response, pending command |

The pending/confirmed/conflict model from ADR-002 is unchanged. A partial approval is a confirmed server state, not a pending one.

---

## Verification plan

| ID | Scenario | Expected |
|---|---|---|
| **T-27** | ₹8,00,000 revision, one approval | Revision stays `IN_REVIEW`; `approvalProgress 1/2`; schedule → `409 APPROVAL_QUORUM_NOT_MET` |
| **T-28** | Same revision, second distinct reviewer approves | Revision `APPROVED`; schedule succeeds; `schedule_approvals` has two rows |
| **T-29** | Same reviewer tries to approve twice | `409` from unique `(revision_id, reviewer_id)`; count remains 1 |
| **T-30** | One reviewer approves, another requests changes | Revision `CHANGES_REQUESTED`; schedule blocked; history shows both decisions |
| **T-31** | Policy changes after submission | Revision keeps its snapshot; quorum does not move |
| **T-32** | Existing single-approval schedule migrated | `schedule_approvals` backfilled with one row; view still works |
| **T-33** | Concurrent second approvals | Row lock serialises; both decisions recorded; quorum reaches 2; one schedule |
| **T-34** | Content changes between the two approvals | New revision; both old approvals historical; schedule blocked |

The critical invariant test becomes:

```
active_schedule(c)
  ⇒ current_revision(c).state = APPROVED
  ∧ count(distinct approved reviewers for current_revision) ≥ required_approvals
  ∧ every approval hash = current_revision.content_hash
```

---

## Migration plan

| Step | Action | Risk | Rollback |
|---|---|---|---|
| 1 | Add `approval_policy_version`, `required_approvals` with defaults | Low; defaults preserve v1 | Drop columns |
| 2 | Add `schedule_approvals`; backfill from `approval_decision_id` | Low; idempotent insert | Drop table |
| 3 | Dual-write new schedules | Medium; two writes in one transaction | Feature flag off |
| 4 | Switch reads to `schedule_approvals` | Medium; verify counts | Flag back |
| 5 | Drop `ux_one_approval_per_revision` | Medium; allows multiple approvals | Recreate index after dedupe |
| 6 | Enable policy for new submissions | Medium; reviewer training | Set threshold to a high value |
| 7 | Drop `approval_decision_id` | Low after reads switch | Restore from join table |

The expand/contract sequence means no step requires downtime. The policy flag is evaluated at submit time and snapshotted, so in-flight revisions are unaffected.

---

## Effort estimate

For a team that already has the v1 domain and schema:

| Work | Estimate |
|---|---|
| Domain policy + quorum predicate | 2–3 hours |
| Schema migration + backfill | 2–3 hours |
| Decision/schedule services | 3–4 hours |
| API response changes | 1–2 hours |
| Mobile progress UI | 3–4 hours |
| Tests (T-27…T-34) | 4–5 hours |
| **Total** | **~2 days** |

In a hackathon, a thinner version (policy hard-coded at ₹1,00,000, no expand/contract) could be demonstrated in 4–6 hours. The point is that the **shape** of the change is small: a policy function, a count, a join table, and a progress field. The core does not move.

---

## What this change proves

1. **The revision model generalises.** Multiple decisions already fit; only the “one approval” constraint was v1-specific.
2. **The hash binding generalises.** Every approval in the set must match the same revision hash.
3. **The source of truth does not move.** PostgreSQL still decides; the client still displays progress.
4. **Idempotency does not change.** Each reviewer’s approval is a separate command with its own key.
5. **The audit trail remains explainable.** Each decision is an event; the schedule records the set.
6. **The change is local.** No microservices, no workflow engine, no event bus.

---

## Risks introduced by the change

| Risk | Mitigation |
|---|---|
| A reviewer approves, then the policy changes | Snapshot at submission; the revision keeps its rule |
| Two reviewers approve different revisions | Each decision binds `revision_id`; only the current revision counts |
| A blocker is outvoted | Any `CHANGES_REQUESTED` is terminal for the revision |
| Reviewer collusion / same person with two accounts | Identity is an auth concern; audit actor; future role requirement |
| Quorum never reached | Review queue shows pending approvals; escalation is future work |
| Schedule records only one decision | Join table; expand/contract migration |
| Old clients do not understand `approvalProgress` | Additive field; old clients can ignore it; `canSchedule` remains authoritative |

---

## When we would revisit this change

- If policies become per-channel or per-brand, add a policy table and a resolver, not more `if` statements.
- If approvals need stages (brand then finance), the revision state machine grows a stage dimension; the hash binding stays.
- If reviewers can delegate, the decision records the delegator and the actor; quorum counts the delegator once.
- If the policy must be changed without deployment, store it in a versioned table with an effective date and snapshot the version on submit.

The change is a seam, not a rewrite. That is the test of the architecture.
