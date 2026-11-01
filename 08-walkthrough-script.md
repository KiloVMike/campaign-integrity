# Six-Minute Structured Walkthrough

**For rehearsal and for the judges’ deeper-dive request**

This is a script for presenting the architecture without a running prototype. It uses the slides, the state tables, and the API examples. Nothing here requires a server. Say clearly that the payloads are illustrative.

**Rule:** point at the **state column**, not at a fictional screen. The state is the product.

---

## Setup

Have these open:

1. [`07-presentation.md`](07-presentation.md) — slides 1–8.
2. [`05-walkthroughs/core-journey.md`](05-walkthroughs/core-journey.md) — the timeline and state table.
3. [`evidence/api-examples.md`](evidence/api-examples.md) — request/response examples.
4. [`03-low-level-design.md`](03-low-level-design.md) §5 — the scheduling transaction.

Optional: a printed one-page state table with the four revisions and their states. It is easier to follow than scrolling.

**Fixtures**

| Thing | Value |
|---|---|
| Campaign | `CMP-1042` “Diwali Reset” |
| Marketer | `USR-MKT-1` Meera |
| Reviewer | `USR-REV-1` Arjun |
| Revision 1 | ₹5,00,000 · All India · `DRAFT` → `CHANGES_REQUESTED` |
| Revision 2 | ₹5,00,000 · Mumbai + Pune · `APPROVED` → `SUPERSEDED` |
| Revision 3 | ₹8,00,000 · Mumbai + Pune · `DRAFT` → `SUPERSEDED` |
| Revision 4 | ₹8,00,000 · Mumbai + Pune + Bangalore · `APPROVED` |
| Schedule 1 | `SCH-7001` for revision 2 · `CANCELLED` at 11:20 |
| Schedule 2 | `SCH-7002` for revision 4 · `SCHEDULED` at 11:35 |

---

## Scene 1 — Create and submit (0:00–1:00)

**Say:**

> “Meera creates a campaign. The server creates revision 1 in `DRAFT`, with a content hash over the objective, audience, channel, and budget. The campaign row points at revision 1.
>
> She submits. The revision becomes `IN_REVIEW`. The content is now frozen. If she edits, the system will not mutate revision 1; it will create revision 2.”

**Show:** the create request and the state table.

```http
POST /v1/campaigns
Idempotency-Key: KEY-CREATE

{
  "name": "Diwali Reset",
  "objective": "Win back lapsed customers with a festive bundle",
  "audience": "All customers in India, 18–55",
  "channel": "INSTAGRAM",
  "budgetMinor": 50000000,
  "currency": "INR"
}
```

**State:** `REV-1 = DRAFT` → `IN_REVIEW`.

**Point to make:** “The hash is the identity of the content. The revision ID is the identity of the proposal. The approval will name both.”

---

## Scene 2 — Request changes and revise (1:00–2:00)

**Say:**

> “Arjun reviews revision 1. He does not approve it. He requests changes, with a reason. That decision is stored against revision 1 and its hash. The revision becomes `CHANGES_REQUESTED`.
>
> Meera cannot resubmit revision 1. She revises. Because revision 1 is no longer a draft, the edit is copy-on-write: revision 1 becomes `SUPERSEDED`, revision 2 is created in `DRAFT` with a new hash, and the campaign pointer moves.
>
> This is the first place the model earns its keep. The reviewer’s feedback stays attached to the content he actually reviewed.”

**Show:** the decision request and the edit response.

```json
{
  "revisionId": "REV-1042-1",
  "outcome": "CHANGES_REQUESTED",
  "reason": "Audience is too broad and the offer is not stated...",
  "expectedContentHash": "1a2b..."
}
```

```json
{
  "revision": { "id": "REV-1042-2", "revisionNumber": 2, "state": "DRAFT" },
  "revisionCreated": true,
  "approvalInvalidated": false,
  "cancelledScheduleId": null
}
```

**State:** `REV-1 = SUPERSEDED`, `REV-2 = DRAFT` → `IN_REVIEW`.

**Point to make:** “A decision is never overwritten. History is append-only in spirit: new revision, new decision.”

---

## Scene 3 — Approve and schedule (2:00–3:00)

**Say:**

> “Arjun approves revision 2. The decision stores revision 2’s ID and hash. The revision becomes `APPROVED`.
>
> Meera schedules. The server locks the campaign row and checks four things: revision 2 is current, it is approved, the decision’s hash matches, and there is no active schedule. All four pass. The schedule, the audit event, and the idempotency response commit in one transaction.
>
> This is the only place where a schedule can be created. There is no second path.”

**Show:** the scheduling transaction from slide 5 / LLD §5.

```
BEGIN
  lock campaign
  if requested revision ≠ current        → 409 REVISION_STALE
  if current state ≠ APPROVED            → 409 APPROVAL_INVALID
  if decision.hash ≠ revision.hash       → 409 CONTENT_HASH_MISMATCH
  if active schedule exists              → 409 ALREADY_SCHEDULED
  insert schedule + audit + key response
COMMIT
```

**State:** `REV-2 = APPROVED`, `SCH-7001 = SCHEDULED`.

**Point to make:** “The guarantee is not the button. It is the transaction.”

---

## Scene 4 — Edit after scheduling (3:00–3:45)

**Say:**

> “Now the moment the product exists for. Meera changes the budget from ₹5 lakh to ₹8 lakh.
>
> The edit transaction marks revision 2 `SUPERSEDED`, creates revision 3 in `DRAFT`, moves the pointer, and cancels schedule 1 — all in one transaction. The response tells the UI exactly what happened: `revisionCreated: true`, `approvalInvalidated: true`, `cancelledScheduleId: SCH-7001`.
>
> There is no committed state in which schedule 1 is active and revision 2 is superseded. The invariant holds at every commit boundary.”

**Show:** the edit response.

```json
{
  "revision": { "id": "REV-1042-3", "state": "DRAFT", "budgetMinor": 80000000 },
  "revisionCreated": true,
  "approvalInvalidated": true,
  "cancelledScheduleId": "SCH-7001"
}
```

**State:** `REV-2 = SUPERSEDED`, `REV-3 = DRAFT`, `SCH-7001 = CANCELLED`.

**Point to make:** “The old approval is still in history. It is simply no longer current. That distinction is the whole design.”

---

## Scene 5 — The stale reviewer (3:45–4:30)

**Say:**

> “Meera submits revision 3. Arjun opens it. Before he taps approve, Meera changes the audience on another device. Revision 4 becomes current; revision 3 is superseded.
>
> Arjun taps approve on revision 3. The server locks the campaign, compares the requested revision with the current one, and returns `409 REVISION_STALE` with the current revision snapshot. No decision is written. No audit event is written. The transaction rolls back, including the idempotency key.
>
> The user sees: ‘Revision 4 is now current. Your approval was for Revision 3, so nothing was changed.’ That is a conflict, not a silent success and not a lost update.”

**Show:** the 409 body.

```json
{
  "error": {
    "code": "REVISION_STALE",
    "message": "Revision 3 is no longer current.",
    "details": {
      "currentRevision": { "id": "REV-1042-4", "revisionNumber": 4, "state": "DRAFT" }
    },
    "retryable": false
  }
}
```

**State:** `REV-3 = SUPERSEDED`, `REV-4 = DRAFT`, no decision for revision 3.

**Point to make:** “If the approval had committed first, the edit would supersede it. Either order is safe. The row lock makes the order serial.”

---

## Scene 6 — The lost response (4:30–5:30)

**Say:**

> “Meera submits revision 4. Arjun approves it. The server commits: decision `DEC-9003`, revision 4 `APPROVED`, audit event written, idempotency key completed. Then the response is lost.
>
> The phone cannot tell whether the request failed or the reply vanished. It does not guess. It shows ‘Confirming approval…’, keeps the command in the outbox, and retries with the same key.
>
> The server sees the key, finds the stored response, and replays it. One decision. One audit event. The app shows Approved.
>
> If the app was killed, the same reconciliation happens on restart: `GET /commands/:key` returns the stored outcome, or `NOT_FOUND` if it never committed. The client never generates a new key for the same intent.”

**Show:** the timeline and the replay response.

```
11:32:02  COMMIT DEC-9003
11:32:02  response lost
11:32:03  “Confirming approval…”
11:33:10  retry same key → 200 Idempotent-Replay: true
```

**State:** `REV-4 = APPROVED`, `DEC-9003` once, one audit event.

**Point to make:** “A timeout is not evidence of failure. The idempotency key is how the client asks the server what happened.”

---

## Scene 7 — Close (5:30–6:00)

**Say:**

> “That is the whole system. One invariant, enforced in one transaction. Immutable revisions, revision-bound approvals, derived eligibility, idempotent commands, append-only audit.
>
> The design is small on purpose. It is small enough to finish, and explicit enough to defend.
>
> If the business adds dual approval above ₹1 lakh, we change a policy, add a join table, and show ‘1 of 2’. We do not change the foundation.
>
> The campaign that gets scheduled is the campaign that was approved.”

---

## If the judges ask for a deeper walkthrough

Go in this order:

1. **State machine** — `03-low-level-design.md` §3. Explain why `CHANGES_REQUESTED` is terminal and why `APPROVED` can only be superseded.
2. **Schema** — §8. Point at the partial unique indexes, composite foreign keys, and the frozen-hash trigger.
3. **Scheduling transaction** — §5. Explain the lock order and why the audit and idempotency response are in the same transaction.
4. **Idempotency protocol** — §9. Explain `INSERT … ON CONFLICT`, the request hash, and why only 2xx responses are stored.
5. **Outbox** — §10. Explain `IN_FLIGHT` reconciliation and per-campaign ordering.
6. **Dual approval** — `05-walkthroughs/requirement-change.md`. Explain the policy snapshot and the join table.

Do **not** start with the UI. The UI is a projection.

---

## Reset script

If you need to run the walkthrough twice, reset the fixture state:

| Entity | Reset to |
|---|---|
| `CMP-1042` | `current_revision_id = REV-1042-1` |
| `REV-1042-1` | `DRAFT` |
| `REV-1042-2..4` | deleted (or not created) |
| `approval_decisions` | none |
| `schedules` | none |
| `audit_events` | truncated for the demo campaign |
| `idempotency_keys` | truncated for the demo users |

In a real demo, use a fresh database per run. Never reset by editing audit rows; truncate the whole demo schema or use a new campaign ID.

---

## What to say if there is no prototype

> “The brief makes a prototype optional. We chose to spend the time on the parts a prototype would not prove: the transaction boundary, the conflict semantics, and the recovery protocol. The walkthrough is a simulation of the contract, and the test matrix is how we would verify it. We are not claiming executed results.”

That is a stronger answer than a thin demo that avoids the failure cases.
