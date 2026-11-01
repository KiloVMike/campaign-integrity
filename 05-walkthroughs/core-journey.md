# Core Journey Walkthrough

**From an idea to a scheduled campaign — and the moment the approval becomes invalid**

This is the journey used in the presentation. It is a structured walkthrough, not a recording of a running prototype. Timestamps, IDs, and hashes are illustrative but internally consistent.

---

## Cast

| ID | Name | Role |
|---|---|---|
| `USR-MKT-1` | Meera Kulkarni | Marketer |
| `USR-REV-1` | Arjun Rao | Reviewer (brand lead) |
| `USR-REV-2` | Priya Shah | Reviewer (finance) — appears only in the change scenario |
| `CMP-1042` | “Diwali Reset” | Campaign for Saffron & Co. |

**Proposal content**

| Revision | Objective | Audience | Channel | Budget | Hash |
|---|---|---|---|---|---|
| `REV-1042-1` | Win back lapsed customers with a festive bundle | All customers in India, 18–55 | `INSTAGRAM` | ₹5,00,000 | `1a2b…1a2b` |
| `REV-1042-2` | Win back lapsed customers with a ₹499 festive bundle | Lapsed customers in Mumbai and Pune, 25–40 | `INSTAGRAM` | ₹5,00,000 | `4b1d…5c7d` |
| `REV-1042-3` | Same as revision 2 | Same as revision 2 | `INSTAGRAM` | ₹8,00,000 | `7f6e…1807` |
| `REV-1042-4` | Same as revision 2 | Lapsed customers in Mumbai, Pune, and Bangalore, 25–40 | `INSTAGRAM` | ₹8,00,000 | `c3d4…c3d4` |

Full hashes are in [`evidence/sample-data.md`](../evidence/sample-data.md).

---

## The journey at a glance

```
10:15  Create CMP-1042 · REV-1 DRAFT
10:22  Submit REV-1 · IN_REVIEW
10:31  Request changes · REV-1 CHANGES_REQUESTED · DEC-9001
10:45  Edit audience/objective · REV-2 DRAFT · REV-1 SUPERSEDED
10:47  Submit REV-2 · IN_REVIEW
11:02  Approve REV-2 · APPROVED · DEC-9002
11:05  Schedule REV-2 for 8 Nov · SCH-7001
11:06  Both users see Approved + Scheduled
```

---

## Step 1 — Create the campaign

**Time:** 10:15 IST  
**Actor:** Meera (`USR-MKT-1`)  
**Command:** `POST /v1/campaigns` with `Idempotency-Key: KEY-CREATE`

```json
{
  "name": "Diwali Reset",
  "objective": "Win back lapsed customers with a festive bundle",
  "audience": "All customers in India, 18–55",
  "channel": "INSTAGRAM",
  "budgetMinor": 50000000,
  "currency": "INR"
}
```

**What happens**

1. The API claims `KEY-CREATE`.
2. It inserts `CMP-1042` with `current_revision_id = null`.
3. It inserts `REV-1042-1` in `DRAFT` with hash `H1`.
4. It sets `CMP-1042.current_revision_id = REV-1042-1`.
5. It appends `REVISION_CREATED` to the audit trail.
6. It stores the `201` response against the key and commits.

**What Meera sees**

> **Diwali Reset**  
> Draft · Revision 1  
> ₹5,00,000 · Instagram · All customers in India, 18–55  
> **Edit**  **Submit for review**

**State:** `REV-1 = DRAFT`, no schedule, no decisions.

---

## Step 2 — Submit for review

**Time:** 10:22 IST  
**Command:** `POST /v1/campaigns/CMP-1042/submit` with `KEY-SUBMIT-1`

```json
{
  "revisionId": "REV-1042-1",
  "expectedContentHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
}
```

**What happens**

1. Lock `CMP-1042`.
2. Check that `REV-1` is current, `DRAFT`, and the hash matches.
3. Set `REV-1.state = IN_REVIEW`, `submitted_at = 10:22`.
4. Append `REVISION_SUBMITTED`.
5. Commit and return the campaign view with `allowedActions: ["VIEW_HISTORY"]` for Meera.

**What Meera sees**

> **In review**  
> Submitted 1 Nov, 10:22  
> Waiting for Arjun Rao

**What Arjun sees in the review queue**

> **Diwali Reset** · Revision 1  
> ₹5,00,000 · Instagram · All customers in India, 18–55  
> Submitted 10:22 · **Review**

**State:** `REV-1 = IN_REVIEW`.

---

## Step 3 — Reviewer requests changes

**Time:** 10:31 IST  
**Actor:** Arjun (`USR-REV-1`)  
**Command:** `POST /v1/campaigns/CMP-1042/decisions` with `KEY-DEC-1`

```json
{
  "revisionId": "REV-1042-1",
  "outcome": "CHANGES_REQUESTED",
  "reason": "Audience is too broad and the offer is not stated. Narrow it to lapsed customers in Mumbai and Pune, and name the bundle price.",
  "expectedContentHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
}
```

**What happens**

1. Lock `CMP-1042`.
2. Verify Arjun is a `REVIEWER` and is not the campaign creator.
3. Verify `REV-1` is current, `IN_REVIEW`, and the hash matches.
4. Insert `DEC-9001` with outcome `CHANGES_REQUESTED`, reason, reviewer, timestamp, and hash `H1`.
5. Set `REV-1.state = CHANGES_REQUESTED`.
6. Append `DECISION_CHANGES_REQUESTED`.
7. Commit.

**What Meera sees**

> **Changes requested**  
> “Audience is too broad and the offer is not stated. Narrow it to lapsed customers in Mumbai and Pune, and name the bundle price.”  
> — Arjun Rao · 1 Nov, 10:31  
> **Revise**

**State:** `REV-1 = CHANGES_REQUESTED`, `DEC-9001` recorded.

**Why the revision is terminal:** Arjun’s feedback is bound to revision 1. Meera cannot resubmit the same revision; she must create revision 2. This keeps the feedback, the content, and the next decision aligned.

---

## Step 4 — Revise the proposal

**Time:** 10:45 IST  
**Command:** `PATCH /v1/campaigns/CMP-1042` with `KEY-EDIT-2`

```json
{
  "expectedContentHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
  "objective": "Win back lapsed customers with a ₹499 festive bundle",
  "audience": "Lapsed customers in Mumbai and Pune, 25–40"
}
```

**What happens**

1. Lock `CMP-1042`.
2. Load current revision 1; check the expected hash.
3. Revision 1 is not `DRAFT`, so the edit is copy-on-write:
   - mark `REV-1 = SUPERSEDED`;
   - insert `REV-2` in `DRAFT` with `revision_number = 2` and hash `H2`;
   - set `CMP-1042.current_revision_id = REV-2`.
4. No active schedule exists, so no cancellation.
5. Append `REVISION_CREATED` (metadata: `supersedesRevisionId: REV-1`).
6. Commit.

**What Meera sees**

> **Draft · Revision 2**  
> ₹5,00,000 · Instagram · Lapsed customers in Mumbai and Pune, 25–40  
> “Win back lapsed customers with a ₹499 festive bundle”  
> **Edit**  **Submit for review**  
> Revision 1 is preserved in history.

**State:** `REV-1 = SUPERSEDED`, `REV-2 = DRAFT`, `DEC-9001` still in history.

---

## Step 5 — Resubmit

**Time:** 10:47 IST  
**Command:** `POST /v1/campaigns/CMP-1042/submit` with `KEY-SUBMIT-2`

```json
{
  "revisionId": "REV-1042-2",
  "expectedContentHash": "4b1d0c7a9e2f8a6c3d5e1f0b7c9a2d4e6f8b1c3d5e7a9f0b2c4d6e8f1a3b5c7d"
}
```

**What happens**

1. Lock `CMP-1042`.
2. Verify `REV-2` is current, `DRAFT`, and the hash matches.
3. Set `REV-2 = IN_REVIEW`, `submitted_at = 10:47`.
4. Append `REVISION_SUBMITTED`.
5. Commit.

**State:** `REV-2 = IN_REVIEW`.

---

## Step 6 — Approve the current revision

**Time:** 11:02 IST  
**Actor:** Arjun  
**Command:** `POST /v1/campaigns/CMP-1042/decisions` with `KEY-DEC-2`

```json
{
  "revisionId": "REV-1042-2",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "4b1d0c7a9e2f8a6c3d5e1f0b7c9a2d4e6f8b1c3d5e7a9f0b2c4d6e8f1a3b5c7d"
}
```

**What happens**

1. Lock `CMP-1042`.
2. Verify Arjun is a reviewer and not the creator.
3. Verify `REV-2` is current, `IN_REVIEW`, and the hash matches.
4. Insert `DEC-9002` with outcome `APPROVED`, reviewer `USR-REV-1`, hash `H2`.
5. Set `REV-2 = APPROVED`.
6. Append `DECISION_APPROVED`.
7. Commit.

**What Meera sees**

> **Approved**  
> Arjun Rao · 1 Nov, 11:02  
> Revision 2 · ₹5,00,000 · Instagram  
> **Schedule campaign**  **View history**

**What the system knows**

```
current_revision = REV-1042-2
revision.state   = APPROVED
decision         = DEC-9002
decision.hash    = H2
revision.hash    = H2   ✅
```

**State:** `REV-2 = APPROVED`, `DEC-9002` recorded.

---

## Step 7 — Schedule the approved revision

**Time:** 11:05 IST  
**Command:** `POST /v1/campaigns/CMP-1042/schedule` with `KEY-SCHED-1`

```json
{
  "revisionId": "REV-1042-2",
  "expectedContentHash": "4b1d0c7a9e2f8a6c3d5e1f0b7c9a2d4e6f8b1c3d5e7a9f0b2c4d6e8f1a3b5c7d",
  "scheduledStartAt": "2026-11-08T10:00:00+05:30"
}
```

**What happens**

1. Claim `KEY-SCHED-1`.
2. Lock `CMP-1042`.
3. Check current revision = `REV-2` ✅
4. Check `REV-2.state = APPROVED` ✅
5. Check `DEC-9002.revision_id = REV-2` and `DEC-9002.hash = H2 = REV-2.hash` ✅
6. Check no active schedule ✅
7. Insert `SCH-7001` with `revision_id = REV-2`, `approval_decision_id = DEC-9002`, `scheduled_start_at = 2026-11-08 10:00 IST`, state `SCHEDULED`.
8. Append `SCHEDULE_CREATED`.
9. Store the `201` response against the key and commit.

**What both users see**

> **Approved · Scheduled**  
> Revision 2 · 8 Nov 2026, 10:00 IST  
> Approved by Arjun Rao · 1 Nov, 11:02

**State:** `REV-2 = APPROVED`, `SCH-7001 = SCHEDULED`.

**The invariant holds:**

```
active_schedule(CMP-1042) = SCH-7001
  ⇒ current_revision = REV-2
  ⇒ REV-2.state = APPROVED
  ⇒ DEC-9002.revision_id = REV-2
  ⇒ DEC-9002.hash = REV-2.hash
```

---

## Step 8 — The moment the approval becomes invalid

**Time:** 11:20 IST  
**Command:** `PATCH /v1/campaigns/CMP-1042` with `KEY-EDIT-3`

```json
{
  "expectedContentHash": "4b1d0c7a9e2f8a6c3d5e1f0b7c9a2d4e6f8b1c3d5e7a9f0b2c4d6e8f1a3b5c7d",
  "budgetMinor": 80000000
}
```

**What happens — one transaction**

1. Lock `CMP-1042`.
2. Load current revision 2; check the expected hash.
3. `REV-2` is `APPROVED`, so the edit is copy-on-write:
   - mark `REV-2 = SUPERSEDED`;
   - insert `REV-3` in `DRAFT` with budget ₹8,00,000 and hash `H3`;
   - set `current_revision_id = REV-3`.
4. Find active schedule `SCH-7001`; cancel it:
   - `state = CANCELLED`;
   - `cancelled_at = 11:20`;
   - `cancellation_reason = REVISION_SUPERSEDED`.
5. Append `REVISION_CREATED` and `SCHEDULE_CANCELLED` (same transaction).
6. Commit.

**What Meera sees**

> **Revision 3 created**  
> The approval for Revision 2 is no longer valid.  
> The schedule for 8 Nov, 10:00 has been cancelled.  
> Submit Revision 3 for review to schedule it again.

**State:** `REV-2 = SUPERSEDED`, `REV-3 = DRAFT`, `SCH-7001 = CANCELLED`, `DEC-9002` still in history but no longer current.

**Why this is the product**

The dashboard never showed a stale “Approved”. The moment the content changed, the system made the consequence explicit: the approval is historical, the schedule is cancelled, and a new review is required.

---

## What the judge should notice

| Observation | Where it is enforced |
|---|---|
| The approval names a revision and a hash, not a campaign status | `approval_decisions.revision_id`, `revision_content_hash` |
| An edit after approval creates a new revision | `PATCH` copy-on-write branch |
| The old approval remains in history but cannot authorise the new revision | `isApprovalValid` checks current revision |
| A scheduled campaign cannot be edited without cancelling the schedule | Same edit transaction |
| The schedule is cancelled in the same transaction as the revision creation | No committed window with an invalid active schedule |
| Every step is auditable | `audit_events` in the same transaction |

---

## Where the journey continues

The next document, [`failure-and-recovery.md`](failure-and-recovery.md), picks up at 11:20 and walks through:

1. A reviewer acting on a stale revision (11:25–11:27).
2. A lost response after an approval commit (11:32–11:33).
3. An app restart with a pending command.

The change document, [`requirement-change.md`](requirement-change.md), asks what would happen if campaigns above ₹1,00,000 needed two distinct approvals — exactly the situation revision 4 would create.
