# Judge Q&A — Architecture Defence

**How to use this:** answer the question in two or three sentences, then point to the evidence. Do not recite the whole design. If a question exposes a limitation, name it and say what you would do next. That is stronger than defending a gap.

---

## The core model

### 1. Why not just store `is_approved` on the campaign?

Because a boolean cannot say **which content** was approved. The campaign row changes; the boolean does not. We derive approval from the current revision and a decision that names that revision and its content hash. A derived value cannot drift out of date.

**Evidence:** ADR-001; `03-low-level-design.md` §2.

### 2. What exactly is an approval?

An immutable record that a specific reviewer approved a specific revision with a specific content hash at a specific time. It is not a status. It is a claim about content.

**Evidence:** `03-low-level-design.md` §2; core journey step 6.

### 3. Why immutable revisions? Isn’t copy-on-write wasteful?

The unit of approval has to be immutable, or the approval can be detached by an edit. Copy-on-write costs one row per edit after submission. For a marketing team, that is negligible. The benefit is that “which version was approved?” has a precise answer forever.

**Evidence:** ADR-001; `03-low-level-design.md` §3.

### 4. Why store a content hash as well as a revision ID? Isn’t that redundant?

It is defence in depth. The revision ID says “this proposal”; the hash says “this content”. If a migration, a bug, or a bypass mutates content without creating a revision, the hash check fails closed. It also makes the approval self-describing in an audit export.

**Evidence:** `03-low-level-design.md` §2, §5.3.

### 5. How do you know the approval is still valid at schedule time?

The schedule transaction locks the campaign row and checks four things: the requested revision is current, it is `APPROVED`, the decision’s revision ID and hash match, and there is no active schedule. All four are evaluated under the same lock. If any fails, the transaction rolls back.

**Evidence:** `03-low-level-design.md` §5; slide 5.

---

## Failure and concurrency

### 6. What if two reviewers approve at the same time?

The campaign row lock serialises the two decisions. Each reviewer gets one decision row; the unique `(revision_id, reviewer_id)` prevents a double decision. In v1, one approval is enough; the second approval would be a separate decision and the revision is already `APPROVED`, so it gets an invalid-state conflict. In the dual-approval version, both decisions count and the quorum is evaluated inside the lock.

**Evidence:** T-18, T-33; `03-low-level-design.md` §6.3.

### 7. What if a reviewer approves a stale revision?

The server compares the requested revision with `campaign.current_revision_id` under the lock. If a newer revision is current, it returns `409 REVISION_STALE` with the current revision summary. No decision, no audit, no state change. The user sees that the campaign changed and can review the current revision.

**Evidence:** failure walkthrough scenario A; T-10.

### 8. What if the network fails after the server commits?

The client cannot tell failure from a lost response, so it does not guess. It shows “Confirming…”, keeps the command in the outbox, and retries with the same idempotency key. The server finds the completed key and replays the stored response. One decision, one audit event.

**Evidence:** failure walkthrough scenario B; T-19; ADR-003.

### 9. What if the app is killed before or after sending?

- **Before send:** the outbox row is `PENDING`; on restart it sends once.
- **After send, before response:** the outbox row is `IN_FLIGHT`; on restart the client calls `GET /commands/:key`. `COMPLETED` applies the stored response; `NOT_FOUND` resends with the same key; `IN_PROGRESS` backs off.

**Evidence:** failure walkthrough scenario C; T-20, T-21.

### 10. What if the client sends the same key with a different body?

The server compares the request hash (method + path + canonical body). A mismatch returns `422 IDEMPOTENCY_KEY_REUSED` before any domain work. A key is bound to one intent.

**Evidence:** `03-low-level-design.md` §9; T-14.

### 11. Why client-generated keys? Why not server-generated?

The key has to exist **before** the network call, so the client can retry after a timeout or a restart. A server-generated key would arrive only after the request succeeded, which is too late for the ambiguous case. The client persists the key in the outbox before sending.

**Evidence:** ADR-003; `03-low-level-design.md` §10.

### 12. What if the idempotency key expires?

Keys live 7 days; the outbox gives up after 24 hours. A very late retry is outside the normal window. Even then, natural unique constraints prevent duplicate decisions and schedules. The one residual risk is a duplicate campaign creation, because there is no natural key for it; we state that limitation and would add a client-generated campaign ID if it mattered.

**Evidence:** ADR-003 consequences; failure walkthrough “What could still go wrong”.

### 13. What if two schedule requests race?

The campaign row lock serialises them. The first inserts the schedule; the second sees the active schedule and returns `409 ALREADY_SCHEDULED`. The partial unique index `ux_one_active_schedule` is the backstop if the lock is ever bypassed.

**Evidence:** T-12; `03-low-level-design.md` §8.

---

## Data and state

### 14. What is the source of truth?

PostgreSQL on the server. The mobile SQLite database is a read cache plus a queue of intentions. Approval eligibility is derived on the server and returned as `canSchedule`; the client never computes it as authority.

**Evidence:** `02-high-level-design.md` §4; ADR-002.

### 15. Why PostgreSQL? Why not Firebase or SQLite?

We need multi-row transactions, row locks, partial unique indexes, and composite foreign keys. PostgreSQL gives all four with a familiar operational model. Firebase’s offline sync is attractive, but the server-side invariant would be harder to enforce and to reason about. SQLite is the mobile cache, not the authority.

**Evidence:** ADR-002; `03-low-level-design.md` §8.

### 16. Why a modular monolith? Why not microservices?

The guarantee needs one transaction across the campaign, revision, decision, schedule, and audit. Microservices would turn that into a distributed saga with more failure modes and less evidence. A modular monolith keeps the boundary clear and the transaction real. We can split later if scaling demands it; the domain interfaces are already separated.

**Evidence:** `02-high-level-design.md` §10; ADR-001/002 context.

### 17. Why not event sourcing?

The audit table gives us the history we need without rebuilding state from events. Full event sourcing adds projection management, replay, and schema evolution costs that are not justified by this scope. If temporal queries or full replay become necessary, the audit table is a stepping stone.

**Evidence:** `02-high-level-design.md` §12.

### 18. How would you scale to 10,000 campaigns?

Reads are indexed and paginated; writes lock only one campaign row, so different campaigns proceed in parallel. The API is stateless and can scale horizontally. The database is the bottleneck; read replicas and audit partitioning are the next steps. At 10,000 campaigns, the current design is comfortably within a single primary.

**Evidence:** `02-high-level-design.md` §7, §9.

### 19. Does the mobile app support offline approvals?

Offline **authorisation** is deliberately not supported. The app can queue commands in the outbox while offline, but approval is a server-authorised decision and only becomes final when the server commits it against the current revision. Draft editing and reading work offline; approvals and scheduling wait for connectivity. If the business required offline authorisation, it would need signed local decisions plus a reconciliation step, and scheduling would stay blocked until reconciliation.

**Evidence:** ADR-002; `03-low-level-design.md` §10.

### 20. What happens if a scheduled campaign is edited?

The edit transaction creates a new revision, supersedes the old one, and cancels the active schedule with reason `REVISION_SUPERSEDED` — all in one transaction. There is no committed window in which an active schedule points at a superseded revision. The UI warns before the edit.

**Evidence:** core journey step 8; T-08.

### 21. Can a reviewer approve their own campaign?

No. A marketer is blocked earlier by the role check (`403 FORBIDDEN`). For a reviewer who is also the campaign creator, the application service checks `reviewer_id ≠ campaign.created_by` and returns `403 SELF_APPROVAL_FORBIDDEN`. Both checks are server-side, not a hidden button.

**Evidence:** `03-low-level-design.md` §14; T-15.

### 22. How do you handle time zones and scheduling in the past?

Store `timestamptz` in UTC; display in IST. The server clock is authoritative. A schedule must be at least 5 minutes ahead and at most 180 days ahead; anything else is `422 SCHEDULE_TIME_INVALID`.

**Evidence:** `03-low-level-design.md` §12.

### 23. What about creative assets — images, video, copy?

Out of scope in v1. The proposal fields are objective, audience, channel, and budget. If assets are added, the content hash must cover asset IDs and versions, not the bytes; the revision remains the unit of approval. That is a deliberate extension point, not a hidden assumption.

**Evidence:** `02-high-level-design.md` §10; ADR-001 revisit triggers.

---

## Change and evolution

### 24. How would you add dual approval?

Snapshot the policy on the revision at submission, drop the single-approval index, allow multiple decisions per revision (the unique reviewer/revision constraint stays), count distinct reviewers in the schedule transaction, and record the approval set in a `schedule_approvals` join table. The API adds `approvalProgress`; the mobile shows “1 of 2”. The core invariant does not change.

**Evidence:** `05-walkthroughs/requirement-change.md`; T-27…T-34.

### 25. What if the policy changes while a revision is in review?

The revision keeps the policy snapshot it was submitted under. A later policy change does not move the goalposts for that review. New revisions use the new policy. This is the same principle as “the approval names the content”: the requirement names the policy.

**Evidence:** requirement change, Option B; T-31.

### 26. Why not a workflow engine?

Two roles and five states do not justify a new dependency and a second source of truth. The policy seam is a function and a snapshot; a workflow engine would add configuration, versioning, and operational overhead without improving the guarantee. Revisit if approvals become multi-stage and per-brand.

**Evidence:** requirement change, Option C.

### 27. What is the biggest weakness of this design?

The residual duplicate-campaign risk after an idempotency key expires, because campaign creation has no natural unique key. It is bounded by the 7-day key TTL versus the 24-hour outbox, but it is real. The second weakness is review fatigue from treating every edit as material; that is a deliberate v1 choice, and field-level scopes are the escape hatch.

**Evidence:** ADR-001 consequences; ADR-003 consequences.

---

## Security and operations

### 28. How do you prevent a malicious client from bypassing the rule?

The client is never trusted. Every command is validated and authorised server-side; eligibility is computed server-side; the database constraints are the final backstop. A forged client can at most send a command that the server rejects. It cannot write directly to PostgreSQL.

**Evidence:** `02-high-level-design.md` §8; `03-low-level-design.md` §14.

### 29. What about secrets and PII?

No secrets in the repository; environment/secret manager only. The app stores a display name and work email; the audience is a segment description, not a list of people. Logs carry IDs and counts, not free text or tokens. Audit records hold the reviewer’s reason under stricter access.

**Evidence:** `02-high-level-design.md` §8; `06-verification-and-diagnostics.md` §5.1.

### 30. What happens if the audit table is unavailable?

The transaction fails and rolls back. State does not commit without evidence. `audit_write_failures_total` pages. This is a deliberate fail-closed choice: a decision without an audit row is worse than a failed request.

**Evidence:** ADR-003; `06-verification-and-diagnostics.md` §7.

### 31. What if the database is restored to an earlier point?

The audit tail after the restore point is lost, and in-flight idempotency keys may replay against older state. The design assumes managed PostgreSQL with point-in-time recovery and treats restore as an incident. After a restore, the invariant query must be run before serving traffic; the audit is not the only copy of state.

**Evidence:** failure walkthrough “What could still go wrong”.

### 32. How do you test the invariant?

Three ways: a direct SQL query that returns zero rows; integration tests that exercise edit/approve/schedule races; and a property-based test over random command sequences. The query is the one we would run first after any change.

**Evidence:** `06-verification-and-diagnostics.md` §4.

---

## The honest questions

### 33. What did you not verify?

Everything is design-level. No code, no executed tests, no measured performance. The logs and API responses are illustrative. The test matrix is specified so it can be implemented directly. We are not claiming guarantees we have not verified.

**Evidence:** README “Read this first”; `06-verification-and-diagnostics.md`.

### 34. What would you build first with more time?

The pure domain tests and the scheduling transaction against PostgreSQL, then the lost-response failure injection. Those three prove the core. The UI is last. If there were time after that, the Measure SDK instrumentation of the schedule transaction — not more features.

**Evidence:** `06-verification-and-diagnostics.md` §8.

### 35. Why three ADRs? What about the other decisions?

The three ADRs cover the decisions that enforce the core guarantee: revision-bound approvals, server authority with an outbox, and idempotent commands with transactional audit. The other choices — modular monolith, PostgreSQL, single approver, no creative assets — are recorded as trade-offs in the HLD, because they are scope decisions rather than invariant decisions.

**Evidence:** `02-high-level-design.md` §10; `04-adrs/`.

### 36. What is the one thing you want us to remember?

**The campaign that gets scheduled is the campaign that was approved.** Everything else — the state machine, the transaction, the idempotency key, the audit — exists to keep that sentence true when the network fails, the user retries, and the content changes.

---

## If you do not know

Say:

> “We did not design that. Here is the closest decision we made, and here is how we would approach it.”

Then use the nearest ADR or the change walkthrough. Do not invent a guarantee. The judges are testing whether you understand the boundary, not whether you have an answer for everything.
