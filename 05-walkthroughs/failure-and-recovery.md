# Failure and Recovery Walkthrough

**Two failures that matter: a stale revision and a lost response**

This document continues the timeline from [`core-journey.md`](core-journey.md). It is a structured walkthrough. The logs and API responses are illustrative, not captured from a running system.

The claim being defended:

> A timeout is not evidence of failure. A conflict is not a silent success. In every case, the system either commits exactly one effect or explains why it did not.

---

## Timeline

```
11:20  Meera edits budget to ₹8,00,000
       REV-2 SUPERSEDED · REV-3 DRAFT · SCH-7001 CANCELLED

11:22  Meera submits REV-3 · IN_REVIEW

11:25  Arjun opens REV-3

11:26  Meera edits audience
       REV-3 SUPERSEDED · REV-4 DRAFT

11:27  Arjun taps Approve on REV-3
       409 REVISION_STALE · no decision · no audit

11:30  Meera submits REV-4 · IN_REVIEW

11:32  Arjun approves REV-4
       server commits DEC-9003 · response lost

11:32  App shows “Confirming approval…”

11:33  App retries with the same key
       server replays the stored response · no duplicate

11:35  Meera schedules REV-4 · SCH-7002
```

---

## Scenario A — The reviewer acts on a stale revision

### What Arjun sees

At 11:25, Arjun opens the review queue:

> **Diwali Reset** · Revision 3  
> ₹8,00,000 · Instagram · Lapsed customers in Mumbai and Pune, 25–40  
> Submitted 11:22  
> **Approve**  **Request changes**

He reads the proposal. At 11:26, Meera changes the audience on another device. At 11:27, Arjun taps **Approve**.

### What the server does

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: KEY-DEC-STALE
Content-Type: application/json

{
  "revisionId": "REV-1042-3",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "7f6e5d4c3b2a1908f7e6d5c4b3a29180f6e5d4c3b2a1908f7e6d5c4b3a291807"
}
```

1. Claim the key.
2. Lock `CMP-1042`.
3. Load `current_revision_id` → `REV-1042-4`.
4. Compare `command.revisionId = REV-1042-3` with current → **mismatch**.
5. Throw `REVISION_STALE` with the current revision summary.
6. **Roll back the transaction**, including the idempotency key row.

```json
{
  "error": {
    "code": "REVISION_STALE",
    "message": "Revision 3 is no longer current.",
    "details": {
      "currentRevision": {
        "id": "REV-1042-4",
        "revisionNumber": 4,
        "state": "DRAFT"
      }
    },
    "retryable": false
  },
  "meta": {
    "requestId": "req_01JA7Z8N4P2Q6R8S0T2V4W6X8Y",
    "serverTime": "2026-11-01T11:27:14+05:30"
  }
}
```

### What did **not** happen

- No `approval_decisions` row for revision 3.
- No `REV-3.state = APPROVED`.
- No audit event for an approval.
- No idempotency key row committed.

This is important: the failed attempt leaves no trace that could be mistaken for a decision. The audit trail remains a record of what actually happened.

### What Arjun sees

> **This campaign changed while you were reviewing.**  
> Revision 4 is now current. Your approval was for Revision 3, so nothing was changed.  
> **Review Revision 4**  **Dismiss**

The app refreshes the campaign, shows revision 4, and discards the stale screen state.

### The race, in both orders

There are two possible orderings. Both preserve the invariant.

**Order 1 — edit commits first (the case above):**

```
Meera's edit:  REV-3 → SUPERSEDED, REV-4 current
Arjun's tap:   sees current = REV-4 → 409 REVISION_STALE
```

**Order 2 — approval commits first:**

```
Arjun's tap:   REV-3 → APPROVED, a decision recorded
Meera's edit:  REV-3 → SUPERSEDED, REV-4 current
               that decision is historical; no schedule exists
```

In Order 2, the approval succeeded for the content Arjun saw, but it is immediately historical. If a schedule had existed for revision 3, the edit transaction would cancel it. The invariant still holds: an active schedule never points at a superseded revision.

The row lock on `CMP-1042` is what makes the two orderings serial. There is no interleaving in which the approval check sees revision 3 but the insert lands after revision 4 becomes current.

### Why this is better than “last write wins”

A last-write-wins system would either:

- accept the approval and silently attach it to revision 4 (wrong content), or
- overwrite Meera’s edit with Arjun’s older view (lost work).

Both are worse than an explicit conflict. The user can see what changed and decide.

---

## Scenario B — The response is lost after the approval commits

This is the primary failure scenario. It is the one that separates a status field from a reliable workflow.

### The setup

At 11:30, Meera submits revision 4. At 11:32, Arjun taps **Approve** on revision 4. The request reaches the server. The server commits. The response never reaches the phone.

### The timeline

| Time | Client | Network | Server | Database |
|---|---|---|---|---|
| 11:32:00 | Arjun taps Approve | | | |
| 11:32:00 | Outbox row `KEY-DEC-3` written | | | |
| 11:32:01 | Request sent | → | Request received | |
| 11:32:01 | | | Claim key; lock campaign | `idempotency_keys` row `IN_PROGRESS` |
| 11:32:01 | | | Verify current, `IN_REVIEW`, hash | |
| 11:32:02 | | | Insert decision `DEC-9003` | `approval_decisions` row |
| 11:32:02 | | | Set `REV-4 = APPROVED` | revision update |
| 11:32:02 | | | Append `DECISION_APPROVED` | `audit_events` row |
| 11:32:02 | | | Complete key with `200` + body | key `COMPLETED` |
| 11:32:02 | | | **COMMIT** | durable |
| 11:32:02 | | ✕ | Response lost | |
| 11:32:03 | App times out | | | |
| 11:32:03 | Shows “Confirming approval…” | | | |

The commit succeeded. The client does not know.

### What the client does **not** do

- It does not show “Approved”. The server has not confirmed to this client.
- It does not show “Failed”. A timeout is not evidence of failure.
- It does not generate a new key. The intent is the same; the key must be the same.

### What the client does

1. The outbox row moves to `PENDING` with a retry time.
2. The UI shows:

> **Confirming approval…**  
> We’ve sent your approval. We’re waiting for the server to confirm — we won’t send it twice.

3. After a short backoff, the sync engine retries with the **same** `Idempotency-Key`.

### What the server does on retry

1. `insert ... on conflict do nothing` finds the existing key row.
2. The conflicting insert waits for the original transaction to finish (it already has).
3. The server reads the row `FOR UPDATE`.
4. `request_hash` matches.
5. `state = COMPLETED`.
6. Returns the stored `200` response with `Idempotent-Replay: true`.

```http
HTTP/1.1 200 OK
Idempotent-Replay: true
Content-Type: application/json

{
  "data": {
    "decision": {
      "id": "DEC-9003",
      "revisionId": "REV-1042-4",
      "outcome": "APPROVED",
      "reviewerId": "USR-REV-1",
      "decidedAt": "2026-11-01T11:32:02+05:30"
    },
    "campaign": {
      "id": "CMP-1042",
      "currentRevision": { "id": "REV-1042-4", "state": "APPROVED" },
      "allowedActions": ["SCHEDULE", "VIEW_HISTORY"]
    }
  },
  "meta": {
    "requestId": "req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z",
    "serverTime": "2026-11-01T11:33:10+05:30"
  }
}
```

### What Arjun sees

> **Approved**  
> Arjun Rao · 1 Nov, 11:32  
> Revision 4 · ₹8,00,000 · Instagram  
> **Schedule campaign**  **View history**

### What the database contains

Exactly one decision:

```sql
select id, revision_id, reviewer_id, outcome, revision_content_hash
from approval_decisions
where campaign_id = 'CMP-1042' and revision_id = 'REV-1042-4';

-- DEC-9003 | REV-1042-4 | USR-REV-1 | APPROVED | c3d4...c3d4
```

Exactly one audit event for the approval:

```sql
select id, action, from_state, to_state, request_id
from audit_events
where campaign_id = 'CMP-1042' and action = 'DECISION_APPROVED'
order by id;

-- 13 | DECISION_APPROVED | IN_REVIEW | APPROVED | req_01JA7Z9...
```

The retry did **not** append a second event. The replay path returns before any domain work.

### Why the unique constraint is still there

The idempotency key is the first line of defence. The unique index `(revision_id, reviewer_id)` is the second. If the key were lost, expired, or bypassed, a second approval by the same reviewer on the same revision would fail at the database. The system would return a conflict, not a duplicate.

This is deliberate defence in depth: the correctness of the workflow should not depend on one table being available.

---

## Scenario C — The app is killed with a pending command

### Case 1 — Killed before the outbox write

If the app dies before the local transaction commits, no request was sent. On restart, the outbox has no row. The user sees the last confirmed state and can retry. There is nothing to reconcile.

### Case 2 — Killed after the outbox write, before send

The outbox row is `PENDING`. On restart, the sync engine sees it, sends it with the same key, and processes the result. One effect.

### Case 3 — Killed after send, before response

The outbox row is `IN_FLIGHT`. On restart, the sync engine does **not** blindly resend. It calls:

```http
GET /v1/commands/KEY-DEC-3
```

Three outcomes:

| Response | Meaning | Action |
|---|---|---|
| `200 COMPLETED` | The command committed | Apply the stored response; mark `DONE` |
| `404 NOT_FOUND` | The key never committed | Mark `PENDING`; resend with the same key |
| `202 IN_PROGRESS` | Another transaction still holds the key | Keep `IN_FLIGHT`; retry with backoff |

This is why the reconciliation endpoint exists. Without it, the client would have to guess between “resend” and “already done”.

### Case 4 — The key has expired

The key TTL is 7 days; the outbox max age is 24 hours. A retry beyond the TTL is outside the normal window. If it happens:

- A duplicate approval is blocked by `unique (revision_id, reviewer_id)`.
- A duplicate schedule is blocked by `ux_one_active_schedule`.
- A duplicate campaign creation is **not** blocked by a natural key. This is the one case where a very late retry could create a second campaign. The mitigation is the TTL margin and the outbox max age; a future version could add a client-generated campaign ID or a natural dedupe key (creator + name + created-at window).

The limitation is stated rather than hidden.

---

## Failure matrix

| Failure | Detection | User-visible state | System behaviour | Invariant |
|---|---|---|---|---|
| Network drops before request | Client timeout | Pending | Retry same key | No effect yet |
| Network drops after commit, before response | Client timeout | “Confirming…” | Replay by key | One effect |
| Duplicate tap | Button disabled + same outbox row | “Confirming…” | Same key; server replays | One effect |
| App killed before send | Outbox `PENDING` | Pending on restart | Send once | One effect |
| App killed after send | Outbox `IN_FLIGHT` | Pending on restart | Reconcile by key | One effect |
| Stale revision approval | Server current check | “Revision 4 is current” | 409; rollback; no decision | Approval not applied |
| Concurrent schedule requests | Row lock + partial unique index | One success, one conflict | 201 / 409 | One active schedule |
| Edit after approval | Server copy-on-write | “Approval invalidated” | New revision; old superseded | No stale approval |
| Edit after scheduling | Same transaction | “Schedule cancelled” | New revision; schedule cancelled | No active schedule on old revision |
| Same key, different body | Request hash mismatch | Error | 422; no state change | No effect |
| Unauthorised reviewer | Role/ownership check | Forbidden | 403; no decision | No decision |
| Content hash mismatch | Hash comparison | Integrity error | 409 or 500; alert | Fail closed |
| Schedule time in the past | Server clock check | Validation error | 422 | No schedule |
| Audit insert fails | Transaction error | Error | Rollback; no state change | State and audit agree |
| Database deadlock | PostgreSQL `40P01` | Transient error | Retry transaction once with jitter | One effect (same key) |

---

## Recovery principles

1. **Persist intent before sending.** The outbox row and key exist before the network call.
2. **Never equate a timeout with failure.** The outcome is unknown until reconciled.
3. **Never regenerate a key for the same intent.** A new key is a new intent.
4. **Reconcile before resending.** `GET /commands/:key` resolves the unknown.
5. **Let the server be the authority.** The client applies the server’s response; it does not invent state.
6. **Make conflicts explicit.** A 409 is a feature: it tells the user the world changed.
7. **Write evidence with the change.** Audit and state commit together, or neither does.
8. **Fail closed on integrity violations.** A hash mismatch is an incident, not a warning.

---

## What could still go wrong

| Residual risk | Why it remains | Mitigation |
|---|---|---|
| Very late retry after key expiry creates a duplicate campaign | No natural unique key for campaign creation | 7-day TTL vs 24-hour outbox; monitor; future client-generated campaign ID |
| Client bug regenerates the key | The guarantee depends on the client following the protocol | Code review; outbox API does not expose a “regenerate” method; test T-13 |
| A malicious client sends a valid-looking hash | The server compares against its own stored hash | Server never trusts client hash as authority; it only uses it as an expected precondition |
| Clock skew on the device | The device may think a time is valid | Server clock is authoritative; `SCHEDULE_TIME_INVALID` |
| Database restore loses the audit tail | Backup/restore is outside the app | Managed Postgres PITR; audit is not the only copy of state |
| Reviewer identity is shared | Authentication is a stub in v1 | Production OIDC; audit actor; segregation of duties |
| Outbox grows unbounded | A stuck command never resolves | Max age, failed state, user-visible retry, metrics |

---

## Evidence pointers

- **Tests:** T-10 (stale revision), T-13 (duplicate approval), T-19 (lost response), T-21 (restart after send), T-23 (expired key), T-25 (audit count).
- **Illustrative logs:** [`evidence/sample-logs.md`](../evidence/sample-logs.md).
- **API examples:** [`evidence/api-examples.md`](../evidence/api-examples.md).
- **Schema:** [`03-low-level-design.md`](../03-low-level-design.md) §8.
- **Idempotency protocol:** [`03-low-level-design.md`](../03-low-level-design.md) §9.

The next document, [`requirement-change.md`](requirement-change.md), tests whether this design can absorb a realistic new rule without being redesigned.
