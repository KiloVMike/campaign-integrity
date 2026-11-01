# ADR-003 — Make every mutating command idempotent and audit in the same transaction

- **Status:** Accepted
- **Date:** 1 November 2026
- **Deciders:** Campaign Integrity team
- **Related requirements:** BR-5; S3, S4, S5
- **Related tests:** T-13, T-14, T-18, T-19, T-21, T-23, T-25

---

## Context

A mobile command can fail in three different ways:

1. **Before the server receives it.** The request never happened. Retrying is safe.
2. **After the server receives it, before it commits.** The transaction rolls back. Retrying is safe.
3. **After the server commits, before the client receives the response.** The effect happened, but the client cannot tell.

The third case is the dangerous one. If the client shows “failed” and the user taps again, a naive server creates a second approval, a second schedule, or a second audit event. If the client shows “approved” without confirmation, it may be lying.

The same ambiguity applies to app restarts: a command may be `IN_FLIGHT` with an unknown outcome. The system needs a way to ask “did my command commit?” and get a definitive answer.

There is a second, related requirement: **the audit trail must agree with the state.** If a decision commits but its audit event does not, the system cannot explain who approved what. If the audit event commits but the decision does not, the audit lies.

---

## Decision drivers

| Driver | Weight |
|---|---|
| Exactly one domain effect per user intent | Primary |
| Definitive reconciliation after a timeout or restart | Primary |
| Audit and state cannot disagree | Primary |
| Implementation cost appropriate to a hackathon | High |
| Compatibility with future event-driven architecture | Medium |

---

## Options considered

### Option A — Best-effort retries, no idempotency

Disable the button while the request is in flight; retry on error.

**Pros:** trivial.

**Cons:** a disabled button is a UI state, not a guarantee. An app kill, a second device, or a retry after a timeout bypasses it. Rejected; the brief explicitly warns that a self-disabling button is not duplicate prevention.

### Option B — Natural-key deduplication only

Rely on unique constraints such as `(revision_id, reviewer_id)` for decisions and `(campaign_id) where state = 'SCHEDULED'` for schedules.

**Pros:** strong for decisions and schedules; no extra table.

**Cons:** does not cover campaign creation, revision creation, or audit events. A retried “create campaign” produces two campaigns. A retried edit can produce two revisions. It also cannot return the original response, so the client cannot distinguish “already done” from “conflict”. Rejected as the only mechanism.

### Option C — Client-generated idempotency key + server-side key store + unique constraints

Every user intent gets a UUID. The client persists it before sending. The server stores the key, a hash of the request, and the response in the same transaction as the state change and audit event.

**Pros:**

- Covers every command, including create and edit.
- Returns the original response on replay, so the client can converge.
- Detects key reuse with a different body.
- Natural unique constraints remain as a second line of defence.
- Works with a simple database transaction; no broker required.

**Cons:**

- An extra table and cleanup job.
- The client must persist the key before sending.
- The key is scoped per user; cross-user replay is not a concern because authorisation still applies.

**Chosen.**

### Option D — Exactly-once messaging with an event bus

Publish commands to a broker with deduplication and consume them exactly once.

**Pros:** scales to many consumers; natural for event-driven systems.

**Cons:** overkill for a single modular monolith. “Exactly once” is usually at-least-once plus deduplication, which is Option C with more infrastructure. Rejected for v1.

---

## Decision

1. **Every mutating request carries a client-generated `Idempotency-Key`.** UUIDv7 is recommended because it is time-ordered.
2. **The client writes the command and key to its outbox before the network call.** The key is never regenerated on retry, including after a restart.
3. **The server claims the key inside the same transaction as the domain work:**

```
insert into idempotency_keys (..., state = 'IN_PROGRESS')
on conflict (user_id, key) do nothing
```

- If the insert succeeds, this request owns the key and proceeds.
- If it conflicts, the server reads the existing row `FOR UPDATE`.
  - Same request hash and `COMPLETED` → replay the stored response.
  - Different request hash → `422 IDEMPOTENCY_KEY_REUSED`.
  - `IN_PROGRESS` → the other transaction is still open; return `409 COMMAND_IN_PROGRESS` with `retryable: true` (or block on the row lock until it resolves).

4. **The request hash covers method, path, and a canonical JSON body.** A key is bound to one intent.
5. **On success, the server stores the status and response body against the key and commits.** State change, audit event, and key completion are one transaction.
6. **On a domain error, the whole transaction rolls back, including the key.** A later retry is a fresh attempt against the new state. This is important: a `409 REVISION_STALE` must not be cached forever.
7. **Only 2xx responses are stored.** Errors are statements about the world at a moment; they may become valid or invalid as state changes.
8. **Natural unique constraints remain:** one decision per reviewer per revision, one approval per revision in v1, one active schedule per campaign. If a key expires, these still prevent the most dangerous duplicates.
9. **Audit events are written in the same transaction as the state change.** The application role has insert-only permission on `audit_events`.
10. **A reconciliation endpoint** `GET /v1/commands/:key` returns `COMPLETED` with the stored response, `IN_PROGRESS`, or `NOT_FOUND`. The client uses it after a restart before resending.

### Key lifetime

- Idempotency keys are retained for **7 days**.
- The client outbox discards or fails commands after **24 hours**.
- The key lifetime is therefore comfortably longer than the retry window.
- A cleanup job deletes completed rows older than 7 days. It runs outside the request path and is monitored.

---

## Consequences

### Positive

- A timeout is no longer ambiguous: the client can reconcile by key.
- A duplicate tap, a retry after app kill, and a second device using the same intent (rare) converge on one effect.
- The audit trail cannot disagree with state for committed changes.
- The design works with a single PostgreSQL transaction; no broker, no saga.
- The same key can be used by a future background sync worker without changing the API.

### Negative

- The idempotency table grows; it needs a TTL and a cleanup job.
- The client must persist the key before sending. If it generates the key after the network call, the guarantee is lost.
- A key reused with a different body is an error the client must handle; it usually means a bug.
- Storing responses duplicates some data (e.g. a campaign view). This is acceptable for a short TTL.
- A `409 COMMAND_IN_PROGRESS` adds a retry path; the client should back off, not spin.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Client regenerates the key on retry | Key is generated once at enqueue and stored in the outbox; sync engine never calls the generator |
| Key expires before a retry | Natural unique constraints protect decisions and schedules; outbox max age is 24 h vs 7-day TTL |
| Same key, different body | Request hash comparison returns `422` before any domain work |
| Audit insert fails | The transaction rolls back; no state change without evidence |
| Duplicate audit event | Audit is written once per committed command; replay returns the stored response and does not append |
| Concurrent duplicates | The unique key insert blocks the second transaction; the row lock serialises the read |
| Cleanup deletes a key still needed | TTL is 7 days; cleanup is monitored; outbox max age is 24 h |
| A 5xx after partial work | The transaction rolls back; retry with the same key is safe |

---

## Enforcement points

| Layer | Enforcement |
|---|---|
| Mobile outbox | Key generated once, persisted before send, reused on every attempt |
| API middleware | Requires `Idempotency-Key` on all mutating routes |
| Application service | Claims the key first; completes it last, in the same transaction |
| Database | Primary key `(user_id, key)`; `completion_consistent` check; unique domain constraints |
| Audit | Insert-only grant; same transaction as state |
| Reconciliation | `GET /v1/commands/:key` |
| Tests | T-13, T-14, T-18, T-19, T-21, T-23, T-25 |

---

## Verification

- **T-13:** send the same approval twice with the same key; assert one decision, one audit event, identical response, `Idempotent-Replay: true`.
- **T-14:** same key, different body; assert `422`, no decision, no audit.
- **T-19:** commit an approval, drop the response, retry with the same key; assert the original response is returned and no duplicate exists.
- **T-21:** kill the app after send, before response; restart; assert reconciliation by key.
- **T-23:** simulate an expired key; assert the natural unique constraint still prevents a duplicate decision or schedule.
- **T-25:** after a sequence of commands, assert `count(audit_events) = count(committed actions)` — an edit that also cancels a schedule counts twice — and every audit row has a request ID.

---

## When we would revisit this decision

1. **Event-driven architecture:** if commands move to a broker, keep the key as the deduplication ID and make consumers idempotent. The database table may become a consumer-side inbox.
2. **Multi-service commands:** if a command spans services, the single-transaction guarantee no longer holds. Use a saga with idempotent steps and a durable command log; do not pretend it is still one transaction.
3. **Very high write volume:** partition `idempotency_keys` by time or user; move cleanup to a scheduled job with metrics. The semantics do not change.
4. **External partners:** if partners call the API, issue scoped keys and enforce a maximum retention window in the contract.
5. **Audit regulations:** if audit must be tamper-evident, add hash chaining or signing. The current design is tamper-resistant by permissions, not cryptographic.

---

## Related decisions

- [ADR-001](ADR-001-revision-bound-approvals.md) — what state the audit is recording.
- [ADR-002](ADR-002-server-authority-and-outbox.md) — where the key lives on the client.
- [`03-low-level-design.md`](../03-low-level-design.md) §9 — claim/complete protocol and schema.
- [`05-walkthroughs/failure-and-recovery.md`](../05-walkthroughs/failure-and-recovery.md) — lost-response timeline.
