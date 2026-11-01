# Verification and Diagnostics

**How we would know the invariant holds — and how we would investigate when it does not**

This is a verification design, not a test report. The test cases are specified; they have not been executed against a running system. The logs and API responses in this pack are illustrative.

That distinction is deliberate. The MAL 4 brief asks for credible test scenarios and diagnostic design; it does not require working code. Claiming executed evidence we do not have would be worse than presenting a precise plan.

---

## 1. Verification strategy

| Layer | What it proves | Tooling | Speed |
|---|---|---|---|
| **Domain unit tests** | The eligibility predicate, hash canonicalisation, state transitions | Vitest / Jest; plain objects; fake clock | Milliseconds |
| **Repository integration tests** | Constraints, row locks, transaction ordering, composite FKs | PostgreSQL via Testcontainers | Seconds |
| **API contract tests** | Request/response shape, error codes, idempotency headers | Supertest against the app + test DB | Seconds |
| **Failure injection** | Lost response, timeout, app kill, duplicate tap | Toxiproxy or a test-only proxy; outbox simulator | Seconds |
| **Concurrency tests** | Two schedules, two reviewers, stale edit races | Parallel requests against a real DB | Seconds |
| **End-to-end (optional)** | The journey on a device | Maestro / Detox | Minutes |
| **Property-based tests** | The invariant holds across random command sequences | fast-check | Seconds–minutes |

The priority order is deliberate: the domain and the database transaction carry the guarantee. UI tests are the least valuable evidence for this problem.

---

## 2. Test matrix

### 2.1 Domain rules

| ID | Setup | Action | Expected | Priority |
|---|---|---|---|---|
| **T-01** | Proposal with zero budget, missing audience, unknown channel | Validate | `VALIDATION_FAILED`; no revision created | P0 |
| **T-02** | Same content with different key order/whitespace | Compute hash | Identical hash; changing budget or audience changes it | P0 |
| **T-03** | Current revision `DRAFT` | `evaluateScheduleEligibility` | `NOT_APPROVED` | P0 |
| **T-04** | Approved decision with a different hash | `evaluateScheduleEligibility` | `APPROVAL_HASH_MISMATCH` | P0 |
| **T-05** | Approved current revision + active schedule | `evaluateScheduleEligibility` | `ALREADY_SCHEDULED` | P0 |
| **T-06** | Approved current revision, no active schedule, valid time | `evaluateScheduleEligibility` | `allowed: true` | P0 |
| **T-35** | Random sequences of create/edit/submit/decide/schedule | Property test | No active schedule without a current approved matching revision; no duplicate audit | P1 |

### 2.2 API and persistence

| ID | Setup | Action | Expected | Priority |
|---|---|---|---|---|
| **T-07** | New campaign | Create → submit → approve → schedule | One revision per step; `APPROVED`; one schedule; audit count matches committed actions | P0 |
| **T-08** | Approved + scheduled revision | Edit budget | New `DRAFT`; old `SUPERSEDED`; approval invalid; schedule `CANCELLED`; two audit events | P0 |
| **T-09** | Approved revision | Edit audience only | Same as T-08 | P0 |
| **T-10** | Revision 3 current, then revision 4 created | Approve revision 3 | `409 REVISION_STALE`; no decision; no audit; no state change | P0 |
| **T-11** | Current revision `DRAFT` | Schedule | `409 APPROVAL_INVALID`; no schedule | P0 |
| **T-12** | Approved current revision | 50 concurrent schedule requests | Exactly one `201`; 49 `409 ALREADY_SCHEDULED`; one schedule row | P0 |
| **T-13** | Approved current revision | Approve twice with same key | One decision; one audit; identical response; `Idempotent-Replay: true` | P0 |
| **T-14** | Same key, different body | Approve | `422 IDEMPOTENCY_KEY_REUSED`; no state change | P0 |
| **T-15** | Marketer tries to decide; reviewer who created the campaign tries to approve; reviewer tries to edit | Call endpoints | `403 FORBIDDEN` / `403 SELF_APPROVAL_FORBIDDEN` / `403 FORBIDDEN` | P0 |
| **T-16** | `CHANGES_REQUESTED` with no reason | Decide | `422 VALIDATION_FAILED`; no decision | P0 |
| **T-17** | Schedule time in the past | Schedule | `422 SCHEDULE_TIME_INVALID`; no schedule | P1 |
| **T-18** | Same reviewer, two approvals on one revision, different keys | Decide | Unique constraint maps to `409`; one decision | P0 |
| **T-24** | Any command | Inspect logs | `requestId`, `campaignId`, `action`, `outcome`, `durationMs` present; no PII | P1 |
| **T-25** | Sequence of commands | Query audit | `count(audit_events) = count(committed actions)`; an edit that also cancels a schedule writes two; every row has a request ID | P0 |
| **T-26** | Schedule rejection | Scrape metrics | `schedule_rejected_total{code="REVISION_STALE"}` increments | P1 |
| **T-36** | 100 campaigns, 10 concurrent users | Read list/detail | p95 under the target; no N+1; pagination stable | P2 |

### 2.3 Recovery

| ID | Setup | Action | Expected | Priority |
|---|---|---|---|---|
| **T-19** | Approval commits, response dropped | Retry same key | Stored response returned; one decision; one audit | P0 |
| **T-20** | Outbox row written, app killed before send | Restart | One request; one effect | P0 |
| **T-21** | Request sent, app killed before response | Restart + reconcile | `GET /commands/:key` resolves; no duplicate | P0 |
| **T-22** | Network offline | Tap Approve | “Confirming…”, not “Approved”; reconnect resolves once | P0 |
| **T-23** | Idempotency key expired | Retry approval/schedule | Natural unique constraint prevents duplicate; explicit conflict | P1 |
| **T-37** | Database deadlock injected | Retry transaction | One effect; same key; no duplicate audit | P2 |

### 2.4 Future change (dual approval)

| ID | Setup | Action | Expected | Priority |
|---|---|---|---|---|
| **T-27** | ₹8,00,000 revision, one approval | Schedule | `409 APPROVAL_QUORUM_NOT_MET`; `approved: 1, required: 2` | P1 |
| **T-28** | Same revision, second distinct reviewer | Approve + schedule | `APPROVED`; schedule succeeds; two `schedule_approvals` rows | P1 |
| **T-29** | Same reviewer twice | Approve | `409`; count remains 1 | P1 |
| **T-30** | One approval + one change request | Decide | `CHANGES_REQUESTED`; schedule blocked | P1 |
| **T-31** | Policy changes after submission | Inspect revision | Snapshot preserved; quorum unchanged | P1 |
| **T-32** | Existing schedule with one decision | Migrate | Join row backfilled; view unchanged | P1 |
| **T-33** | Two reviewers approve concurrently | Parallel requests | Both decisions; quorum 2; one schedule | P1 |
| **T-34** | Content changes between approvals | Edit | New revision; old approvals historical; schedule blocked | P1 |

---

## 3. Example inputs and outcomes

### 3.1 Happy path — schedule revision 4

**Request**

```http
POST /v1/campaigns/CMP-1042/schedule
Idempotency-Key: 019a2f7c-4bfc-726a-9b4d-6e7f8091a2b3
Content-Type: application/json

{
  "revisionId": "REV-1042-4",
  "expectedContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4",
  "scheduledStartAt": "2026-11-08T10:00:00+05:30"
}
```

**Response**

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "data": {
    "schedule": {
      "id": "SCH-7002",
      "campaignId": "CMP-1042",
      "revisionId": "REV-1042-4",
      "approvalDecisionId": "DEC-9003",
      "scheduledStartAt": "2026-11-08T10:00:00+05:30",
      "state": "SCHEDULED"
    },
    "campaign": {
      "id": "CMP-1042",
      "approvalStatus": "APPROVED",
      "scheduleStatus": "SCHEDULED",
      "canSchedule": { "allowed": false, "code": "ALREADY_SCHEDULED" }
    }
  },
  "meta": {
    "requestId": "req_01JA7ZA1B2C3D4E5F6G7H8J9K0",
    "serverTime": "2026-11-01T11:35:02+05:30"
  }
}
```

**Expected database state**

```sql
-- one active schedule
select id, revision_id, approval_decision_id, state
from schedules where campaign_id = 'CMP-1042' and state = 'SCHEDULED';
-- SCH-7002 | REV-1042-4 | DEC-9003 | SCHEDULED

-- one audit event
select action, from_state, to_state
from audit_events
where campaign_id = 'CMP-1042' and action = 'SCHEDULE_CREATED';
-- SCHEDULE_CREATED | NULL | SCHEDULED
```

### 3.2 Stale revision — approve revision 3 after revision 4 is current

**Request**

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-5c0d-737b-8c5e-7f8091a2b3c4
Content-Type: application/json

{
  "revisionId": "REV-1042-3",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "7f6e5d4c3b2a1908f7e6d5c4b3a29180f6e5d4c3b2a1908f7e6d5c4b3a291807"
}
```

**Response**

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

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

**Expected database state:** no new `approval_decisions` row; no `DECISION_APPROVED` audit event; `REV-1042-3` remains `SUPERSEDED`.

### 3.3 Lost response — retry the approval with the same key

**First request** (response lost)

```http
POST /v1/campaigns/CMP-1042/decisions
Idempotency-Key: 019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2
Content-Type: application/json

{
  "revisionId": "REV-1042-4",
  "outcome": "APPROVED",
  "reason": null,
  "expectedContentHash": "c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
}
```

**Retry** — identical method, path, key, and body

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
      "approvalStatus": "APPROVED",
      "allowedActions": ["SCHEDULE", "VIEW_HISTORY"]
    }
  },
  "meta": {
    "requestId": "req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z",
    "serverTime": "2026-11-01T11:33:10+05:30"
  }
}
```

**Expected database state:** one `approval_decisions` row; one `DECISION_APPROVED` audit event; one `idempotency_keys` row with `state = COMPLETED`.

---

## 4. Invariant checks

These are the assertions that matter more than any individual test.

The SQL uses the readable aliases from [`evidence/sample-data.md`](evidence/sample-data.md). Substitute the corresponding UUIDs when running it against the schema in `03-low-level-design.md` §8.

### 4.1 No active schedule without a valid approval

```sql
select s.id, s.campaign_id, s.revision_id
from schedules s
join campaigns c on c.id = s.campaign_id
join campaign_revisions r on r.id = c.current_revision_id
left join approval_decisions d
  on d.revision_id = r.id
 and d.outcome = 'APPROVED'
 and d.revision_content_hash = r.content_hash
where s.state = 'SCHEDULED'
  and (
    s.revision_id <> c.current_revision_id
    or r.state <> 'APPROVED'
    or d.id is null
  );
-- Expected: 0 rows
```

### 4.2 At most one active schedule per campaign

```sql
select campaign_id, count(*)
from schedules
where state = 'SCHEDULED'
group by campaign_id
having count(*) > 1;
-- Expected: 0 rows (also enforced by ux_one_active_schedule)
```

### 4.3 At most one active revision per campaign

```sql
select campaign_id, count(*)
from campaign_revisions
where state <> 'SUPERSEDED'
group by campaign_id
having count(*) > 1;
-- Expected: 0 rows (also enforced by ux_one_active_revision)
```

### 4.4 Every committed domain action has an audit event

The audit table records **actions**, not raw row diffs. One action may change more than one row; the event metadata names the affected entities. The invariant is that no committed action is missing from the trail.

```sql
-- Illustrative: compare decisions to decision audit events
select d.id as decision_id
from approval_decisions d
left join audit_events a
  on a.campaign_id = d.campaign_id
 and a.action in ('DECISION_APPROVED', 'DECISION_CHANGES_REQUESTED')
 and a.metadata->>'decisionId' = d.id::text
where a.id is null;
-- Expected: 0 rows
```

The same check applies to schedules (`metadata->>'scheduleId'`) and revisions (`revision_id`). An edit that creates a revision and cancels a schedule writes two events in one transaction; a create writes one event for the campaign and its first revision. Compare against committed **actions**, not row updates.

### 4.5 No duplicate decision per reviewer per revision

```sql
select revision_id, reviewer_id, count(*)
from approval_decisions
group by revision_id, reviewer_id
having count(*) > 1;
-- Expected: 0 rows (also enforced by the unique index)
```

### 4.6 Property-based test

Generate a random sequence of commands against a model of the domain. After every step, assert:

- the invariant query returns zero rows;
- `audit_events` count equals the number of committed actions (an edit that also cancels a schedule counts twice);
- replaying any command with the same key does not change state or audit count;
- a schedule rejection leaves no schedule row.

This catches ordering bugs that hand-written tests miss. It is P1 because it complements, not replaces, the specific cases.

---

## 5. Diagnostics

### 5.1 Log schema

Every request emits one structured JSON line at completion, plus one line per significant domain event.

| Field | Example | Purpose |
|---|---|---|
| `ts` | `2026-11-01T11:32:02.418+05:30` | Event time |
| `level` | `info`, `warn`, `error` | Severity |
| `service` | `campaign-api` | Service |
| `env` | `prod` | Environment |
| `event` | `http.request.completed`, `domain.event` | Line type |
| `requestId` | `req_01JA7...` | Logical command ID; reused on replay so the audit event and retry correlate |
| `traceId` | `4bf92f...` | Physical request trace (OpenTelemetry); a retry gets a new trace |
| `actorId` | `USR-REV-1` | Who acted |
| `actorRole` | `REVIEWER` | Role |
| `campaignId` | `CMP-1042` | Domain scope |
| `revisionId` | `REV-1042-4` | Revision scope |
| `action` | `DECISION_APPROVED` | Domain action |
| `outcome` | `committed`, `rejected`, `replayed` | Result |
| `status` | `200`, `409` | HTTP status, on request lines |
| `code` | `REVISION_STALE` | Error code, when rejected |
| `durationMs` | `38` | Server processing time |
| `idempotencyKey` | `019a2f...` | Retry correlation |
| `idempotentReplay` | `true` | Replay marker |
| `auditEventId` | `13` | Audit row, on domain-event lines |
| `fromState` / `toState` | `IN_REVIEW` / `APPROVED` | Transition, on domain-event lines |

**Privacy:** logs never include the campaign objective, audience text, reviewer reason, email, or token. They include IDs and counts. Free text stays in the audit record, which has stricter access control.

### 5.2 Audit vs logs

| | Audit events | Logs |
|---|---|---|
| Purpose | Domain truth: who changed what | Diagnosis: why a request behaved as it did |
| Storage | PostgreSQL, append-only | Log sink, retention 30 days |
| Access | Application query + investigator | Engineering |
| Contents | Actor, action, states, decision ID, request ID, reason | IDs, timings, error codes |
| Mutability | Insert-only for app role | Append-only stream |
| Used for | “What happened?” | “Why did it happen?” |

The audit table answers the business question. Logs answer the operational question. Neither replaces the other.

### 5.3 Metrics

| Metric | Type | Labels | Why |
|---|---|---|---|
| `campaign_command_total` | counter | `type`, `outcome` | Volume and success rate |
| `campaign_command_duration_ms` | histogram | `type` | Tail latency |
| `schedule_rejected_total` | counter | `code` | Conflict pressure |
| `approval_conflict_total` | counter | `reason` | Stale-review frequency |
| `idempotency_replay_total` | counter | `endpoint` | Retry storm or lost responses |
| `outbox_pending_age_seconds` | gauge | `command_type` | Stuck mobile commands |
| `outbox_failed_total` | counter | `command_type` | Client-side failures |
| `db_transaction_retry_total` | counter | `reason` | Deadlocks/serialisation |
| `audit_write_failures_total` | counter | — | Must stay zero |
| `integrity_violation_total` | counter | `kind` | Must stay zero; pages |

### 5.4 Traces

One trace per command:

```
HTTP POST /schedule
  ├─ auth.verify
  ├─ idempotency.claim
  ├─ campaign.lock
  ├─ eligibility.evaluate
  ├─ schedule.insert
  ├─ audit.append
  └─ idempotency.complete
```

The trace makes the transaction visible: if `audit.append` is slow or fails, it is obvious which span is responsible. The `requestId` is attached to every span.

### 5.5 Example log lines (illustrative)

```json
{"ts":"2026-11-01T11:32:02.418+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z","traceId":"4bf92f3577b34da6a3ce929d0e0e4736","actorId":"USR-REV-1","actorRole":"REVIEWER","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"DECISION_APPROVED","outcome":"committed","status":200,"durationMs":38,"idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","idempotentReplay":false}
```

```json
{"ts":"2026-11-01T11:27:14.102+05:30","level":"warn","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z8N4P2Q6R8S0T2V4W6X8Y","traceId":"9f2c1a3b4c5d6e7f8a9b0c1d2e3f4a5b","actorId":"USR-REV-1","actorRole":"REVIEWER","campaignId":"CMP-1042","revisionId":"REV-1042-3","action":"DECISION_APPROVED","outcome":"rejected","code":"REVISION_STALE","status":409,"durationMs":21,"idempotencyKey":"019a2f7c-5c0d-737b-8c5e-7f8091a2b3c4"}
```

```json
{"ts":"2026-11-01T11:33:10.664+05:30","level":"info","service":"campaign-api","env":"prod","event":"http.request.completed","requestId":"req_01JA7Z9P5Q3R7S9T1V3W5X7Y9Z","traceId":"a4c8e2f6b1d93570c2e4a6f8013b5d79","actorId":"USR-REV-1","actorRole":"REVIEWER","campaignId":"CMP-1042","revisionId":"REV-1042-4","action":"DECISION_APPROVED","outcome":"replayed","status":200,"durationMs":4,"idempotencyKey":"019a2f7c-3aeb-715f-8a3c-5d6e7f8091a2","idempotentReplay":true}
```

The first and third lines share a `requestId` because they are the same logical command; the third has a new `traceId` because the retry is a new HTTP request. The second line has no accompanying `domain.event` line — the rejection rolled back before any domain work.

Full examples: [`evidence/sample-logs.md`](evidence/sample-logs.md).

---

## 6. Investigation runbook

### Symptom: “The schedule button was rejected”

1. **Identify the campaign and revision.** Ask for the campaign ID and the time. If the user has a request ID, start there.
2. **Read the audit trail.**

```sql
select occurred_at, actor_id, actor_role, action, from_state, to_state, metadata
from audit_events
where campaign_id = 'CMP-1042'
order by id;
```

3. **Compare current revision and approval.**

```sql
select c.current_revision_id, r.revision_number, r.state, r.content_hash,
       d.id as decision_id, d.outcome, d.revision_content_hash
from campaigns c
join campaign_revisions r on r.id = c.current_revision_id
left join approval_decisions d
  on d.revision_id = r.id and d.outcome = 'APPROVED'
where c.id = 'CMP-1042';
```

4. **Check for an active schedule.**

```sql
select id, revision_id, state, scheduled_start_at
from schedules
where campaign_id = 'CMP-1042' and state = 'SCHEDULED';
```

5. **Check the idempotency key.**

```sql
-- The key is scoped by user; this returns every row with the key.
select user_id, key, endpoint, state, response_status, created_at, completed_at
from idempotency_keys
where key = '019a2f7c-4bfc-726a-9b4d-6e7f8091a2b3';
```

6. **Search logs by request ID.**

```
requestId = "req_01JA7..." OR idempotencyKey = "019a2f..."
```

7. **Decide the class of problem:**

| Observation | Likely cause | Action |
|---|---|---|
| `REVISION_STALE` | A newer revision exists | Expected; user reviews current |
| `APPROVAL_INVALID` | Revision not approved | Expected; submit for review |
| `CONTENT_HASH_MISMATCH` | Corruption or a bypass | Incident; compare hashes; page |
| `ALREADY_SCHEDULED` | Duplicate intent | Expected; show existing schedule |
| Key `COMPLETED` but client saw failure | Lost response | Replay; no incident |
| Key missing after a successful-looking request | Key expiry or wrong environment | Check TTL and env; natural constraints |
| Audit row missing | Transaction bug | Page; `integrity_violation_total` |

### Symptom: “I approved, but the app still says pending”

1. Query the idempotency key. If `COMPLETED`, the approval committed; the client should reconcile.
2. Query `approval_decisions` for the revision. If the row exists, the server state is correct.
3. Check the outbox row on the device (debug build): `state = IN_FLIGHT` with an old `updated_at` means the client is stuck.
4. Check `GET /v1/commands/:key`. `200 COMPLETED` should resolve it; `404` means resend with the same key.

### Symptom: “Two schedules exist”

This should be impossible because of `ux_one_active_schedule`. If it happens:

1. Check whether one is `CANCELLED`; that is correct.
2. If two are `SCHEDULED`, the index is missing or the database was restored incorrectly. Page; do not delete rows manually until the audit is captured.
3. Rebuild the index after deduplicating with a documented script.

---

## 7. Dashboard and alerts

### Dashboard panels

1. **Command volume and outcome** — create/edit/submit/decide/schedule, committed vs rejected.
2. **Schedule rejection reasons** — `REVISION_STALE`, `APPROVAL_INVALID`, `ALREADY_SCHEDULED`.
3. **Approval conflict rate** — stale reviews per 100 decisions.
4. **Idempotent replays** — rate and endpoint; a spike suggests lost responses or client retries.
5. **Outbox pending age** — p50/p95 by command type; a rising p95 means clients are stuck.
6. **Integrity violations** — must be zero; any value pages.

### Alerts

| Condition | Severity | Why |
|---|---|---|
| `audit_write_failures_total > 0` | Page | State may commit without evidence |
| `integrity_violation_total > 0` | Page | The invariant was violated |
| `schedule_rejected_total{code="CONTENT_HASH_MISMATCH"} > 0` | Page | Possible corruption or bypass |
| `outbox_pending_age_seconds > 300` | Warn | Users are stuck |
| `idempotency_replay_total / campaign_command_total > 0.2` | Warn | Retry storm or network issue |
| `campaign_command_duration_ms{p95} > 1000` | Warn | Database contention |
| `db_transaction_retry_total` rising | Warn | Lock contention or deadlocks |

Thresholds are starting points, not measured baselines. They would be tuned after the first week.

---

## 8. What we would verify first with code

If the team had another day, the order would be:

1. **Pure domain tests** for `isApprovalValid`, `evaluateScheduleEligibility`, and `contentHash` (T-02…T-06). No database, no UI.
2. **Integration tests** for the edit and schedule transactions against PostgreSQL (T-07…T-12). These are the guarantee.
3. **Failure injection** for the lost response and restart (T-19…T-21). This is the demo that convinces judges.
4. **Audit and invariant queries** (T-25, §4). This is the evidence.
5. **UI tests** last. The interface is not where the rule lives.

The optional Measure SDK integration would instrument the schedule transaction and the approval round-trip. The interesting metric is the p95 of `campaign_command_duration_ms{type="schedule"}` and the age of pending outbox rows — not launch time. A before/after comparison would be meaningful only after a real optimisation; we do not claim one.

---

## 9. Limitations of this verification design

- No test has been executed; the matrix is a plan.
- No performance baseline exists. The p95 targets are placeholders.
- Failure injection requires a proxy or a test hook; the design describes the scenario, not a harness.
- The property-based model is only as good as its model of the domain; it must share the same state machine, not re-implement it differently.
- The audit queries assume the metadata keys (`decisionId`) are populated consistently; a contract test should enforce that.
- Mobile outbox tests need a device or a simulator with the ability to kill the process mid-request; a unit test of the sync loop is not enough.

These limitations are stated so the judges can distinguish “designed” from “verified”. The design is complete; the evidence is the next step.
