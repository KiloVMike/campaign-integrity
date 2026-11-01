# ADR-001 — Bind approvals to immutable campaign revisions

- **Status:** Accepted
- **Date:** 1 November 2026
- **Deciders:** Campaign Integrity team
- **Related requirements:** BR-1, BR-2, BR-3, BR-4; S2, S6
- **Related tests:** T-03, T-04, T-08, T-09, T-10, T-11

---

## Context

The Martech brief requires that only an approved campaign can be scheduled, and that changing an approved proposal’s budget or audience triggers another review.

The naive model stores approval on the campaign:

```
campaigns(id, name, budget, audience, status, approved_at)
```

A reviewer approves the campaign row. A marketer then updates `budget` or `audience`. The row still says `status = APPROVED`. The approval has become a claim about content that no longer exists.

This is not a UI bug. It is a modelling error: **the approval does not name the thing it approves.** No amount of button-disabling fixes it, because any code path that updates the campaign can leave the status stale.

The design needs a representation in which:

1. the content being reviewed is identifiable and immutable;
2. the decision names that exact content;
3. the scheduling check can prove the two still match;
4. history remains explainable after several revisions.

---

## Decision drivers

| Driver | Weight |
|---|---|
| Correctness of the approval-to-content relationship | Primary |
| Auditability of “who approved what” | High |
| Simplicity of the scheduling check | High |
| Ability to evolve to field-level or dual approval | Medium |
| Storage and implementation cost | Low |

---

## Options considered

### Option A — Mutable campaign with a status enum

```
campaigns.status ∈ {DRAFT, IN_REVIEW, APPROVED, ...}
```

**Pros:** simplest schema; one row per campaign; easy UI.

**Cons:** the status is detached from content. Every update path must remember to reset it. A missed path silently authorises unreviewed content. There is no way to answer “which version was approved?” after an edit. Rejected: it reproduces the exact failure the product exists to prevent.

### Option B — Mutable campaign with an `approved_version` integer

```
campaigns.approved_version = 3
campaigns.current_version  = 4
```

**Pros:** better than A; a version mismatch can be detected.

**Cons:** versions are labels, not content. An in-place update that forgets to increment the version leaves the approval “valid” for changed content. The guarantee depends on developer discipline rather than on the data model. Rejected as the primary mechanism.

### Option C — Immutable revisions with revision-bound approvals

```
campaign_revisions(id, campaign_id, revision_number, content..., content_hash, state)
approval_decisions(id, revision_id, revision_content_hash, reviewer_id, outcome)
campaigns.current_revision_id
```

**Pros:**

- The approval names the exact revision and content hash.
- Edits after submission create a new revision; the old approval is historical, not current.
- The scheduling check is a small, explicit predicate.
- History is natural: every revision and decision remains.
- The model extends to dual approval without changing the revision concept.

**Cons:**

- More rows and a copy-on-write edit path.
- Every edit after submission requires review, including cosmetic edits (see ADR consequence).
- The content hash must be canonical and must be updated when the proposal schema changes.

**Chosen.**

### Option D — Field-level approval scopes

```
approval_scopes(revision_id, field, approved_value_hash)
```

**Pros:** a typo fix in the objective would not require re-approval; precise.

**Cons:** much more complex UI and policy; reviewers would need to understand which fields are material; the audit story becomes “approved budget, not audience” rather than “approved this proposal.” Deferred, not rejected forever.

---

## Decision

We will model a campaign as a sequence of **immutable revisions**.

1. A revision is created in `DRAFT`. A `DRAFT` may be edited in place; no approval exists yet.
2. On submit, the revision becomes `IN_REVIEW` and its content is frozen.
3. Any edit to a non-`DRAFT` revision creates a **new** revision with the next `revision_number`; the previous revision becomes `SUPERSEDED`.
4. An approval decision stores:
   - `revision_id`,
   - `revision_content_hash` at decision time,
   - `reviewer_id`, `outcome`, `reason`, `decided_at`.
5. `campaigns.current_revision_id` points to the only non-superseded revision.
6. Scheduling is allowed only when the requested revision is current, is `APPROVED`, and the decision’s hash matches the revision’s hash.

The invariant:

```
active_schedule(c)
  ⇒ current_revision(c).state = APPROVED
  ∧ decision.revision_id       = current_revision(c).id
  ∧ decision.content_hash      = current_revision(c).content_hash
```

### Content hash scope

The hash covers `objective`, `audience`, `channel`, `budgetMinor`, and `currency`. It excludes the campaign `name`, which is a display label. Text is NFC-normalised, trimmed, and whitespace-collapsed before hashing. Money is stored as integer paise.

If a future proposal adds a field, the field is added to the canonical object. Existing revisions keep their stored hash; new revisions use the new schema. The hash is stored, not recomputed on read, so old approvals remain verifiable.

---

## Consequences

### Positive

- The core business rule is enforced by data shape, not by a convention.
- “Which campaign was approved?” has a precise answer: the revision with the matching decision and hash.
- Stale approvals become detectable and explainable, not silent.
- The audit trail can show the full sequence: revision created with `supersedesRevisionId`, submitted, decision, scheduled, cancelled.
- The model supports dual approval later: multiple decisions can point at one revision.

### Negative

- Every edit after submission creates a row. For a marketing team this is negligible; for a high-volume editor it would matter.
- A cosmetic change (a typo in the objective) requires a new revision and a new review. This is stricter than the brief’s “budget or audience” rule. It is deliberate: it avoids a materiality policy that reviewers would have to interpret under time pressure.
- The UI must explain why an edit invalidates approval and cancels a schedule. This is handled with explicit copy, not a silent transition.
- The content hash is a compatibility surface. Changing canonicalisation would invalidate old comparisons unless the stored hash is versioned. The design stores the hash and never recomputes it for old revisions; a future canonicalisation change needs a `hash_version` column.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| A developer updates a revision in place after submission | Trigger rejects `content_hash` changes on non-`DRAFT` rows; service only exposes `updateDraft` |
| Two revisions become current | Partial unique index on `(campaign_id) where state <> 'SUPERSEDED'` |
| A decision points at another campaign’s revision | Composite foreign key `(revision_id, campaign_id)` |
| The hash is computed differently on client and server | Server is the only writer; the client never computes an authoritative hash |
| Cosmetic edits overload reviewers | Revisit trigger below; field-level scopes are the escape hatch |

---

## Enforcement points

| Layer | Enforcement |
|---|---|
| Schema | `ux_one_active_revision`; composite FKs; `content_hash` check; trigger on frozen hash |
| Domain | `isCurrentRevision`, `isApprovalValid`, `evaluateScheduleEligibility` |
| Application service | Edit supersedes before insert; schedule reads under `FOR UPDATE`; decision checks current revision |
| API | `expectedContentHash` on edit, submit, decide, and schedule |
| UI | Shows “Revision N” on every decision and schedule; warns before an edit invalidates approval |
| Tests | T-03, T-04, T-08, T-09, T-10, T-11 |

---

## Verification

- **T-08:** approve revision 2, edit the budget, assert revision 3 is `DRAFT`, revision 2 is `SUPERSEDED`, the approval no longer authorises scheduling, and the active schedule is `CANCELLED`.
- **T-09:** the same for an audience-only change.
- **T-10:** approve revision 3 after revision 4 is current; assert `409 REVISION_STALE` and no decision row.
- **T-11:** schedule a revision that is current but `DRAFT`; assert `409 APPROVAL_INVALID`.
- **Invariant query:** after any test sequence, assert that no `SCHEDULED` row joins to a revision that is not current and approved with a matching hash.

---

## When we would revisit this decision

1. **Review fatigue:** if cosmetic edits dominate review volume, introduce a materiality policy or field-level scopes (Option D). The revision model remains; only the trigger for a new revision changes.
2. **Creative assets:** if approvals must cover images or video, the hash must include asset IDs and versions. The revision remains the unit, but the content hash becomes a Merkle root over proposal fields and asset versions.
3. **Collaborative editing:** if multiple marketers edit the same draft concurrently, add optimistic concurrency at the field level. Submitted revisions remain immutable.
4. **Hash canonicalisation change:** add `hash_version` and keep old comparisons valid; do not silently recompute.
5. **Regulated approval evidence:** if the audit must be cryptographically verifiable, sign decision records and anchor them in an append-only store. The current audit table is tamper-resistant by permissions, not cryptographic.

---

## Related decisions

- [ADR-002](ADR-002-server-authority-and-outbox.md) — why the server, not the client, owns revision state.
- [ADR-003](ADR-003-idempotent-commands-and-audit.md) — why a retried approval cannot create a second decision.
- [`05-walkthroughs/requirement-change.md`](../05-walkthroughs/requirement-change.md) — how dual approval extends this model.
