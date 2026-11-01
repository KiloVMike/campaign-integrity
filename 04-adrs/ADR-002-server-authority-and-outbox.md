# ADR-002 — Server-authoritative workflow with a client outbox

- **Status:** Accepted
- **Date:** 1 November 2026
- **Deciders:** Campaign Integrity team
- **Related requirements:** BR-1, BR-2, BR-6; S2, S4, S6
- **Related tests:** T-06, T-10, T-20, T-21, T-22

---

## Context

The product is mobile-first. Marketers and reviewers work from phones, often on unreliable networks. The app must feel responsive, but the business rule is a safety rule: an unapproved revision must never be scheduled.

There are two tempting extremes:

1. **Client-authoritative, offline-first.** The app owns a local copy of campaign state, lets users approve and schedule offline, and syncs later. This gives excellent perceived performance, but it creates a merge problem for a decision that must be bound to exact content. Two devices can approve different revisions; a schedule can be created locally against a revision the server has already superseded.
2. **Server-authoritative, online-only.** Every action waits for the server, and nothing is cached. This is correct but slow and brittle; a dropped connection loses the user’s input, and the app cannot show a campaign without a round trip.

The design also needs to distinguish **domain state** (what the server has committed) from **user intent** (what the user asked for but the server has not confirmed). Conflating them is the source of false “Approved” labels.

---

## Decision drivers

| Driver | Weight |
|---|---|
| No split-brain approval state | Primary |
| Predictable recovery after timeout or restart | High |
| Mobile usability on poor networks | High |
| Simplicity of conflict handling | High |
| Offline authorisation | Not supported |

---

## Options considered

### Option A — Client-authoritative offline-first

The mobile SQLite database is the primary store; the server is a sync target. Conflicts are resolved by last-write-wins or a merge policy.

**Pros:** works offline; instant UI; no waiting.

**Cons:** the core guarantee becomes a distributed consistency problem. A local approval can be created for a revision the server has superseded. Last-write-wins can silently discard a reviewer’s decision. A schedule can be created locally against content that no longer exists. Rejected.

### Option B — Server-authoritative, no local cache

Every screen fetches; every action posts; nothing is stored locally.

**Pros:** simplest correctness story; no stale cache.

**Cons:** poor mobile experience; lost input on network failure; no pending state; every navigation waits. Rejected as unnecessarily fragile.

### Option C — Server-authoritative with a read cache and a command outbox

The server owns all domain state. The app caches the last confirmed read model and persists each command in an outbox before sending. The UI shows the confirmed state plus a pending overlay.

**Pros:**

- One authority for approvals and schedules.
- The app remains usable for reading and drafting.
- A timeout is represented as “pending”, not “failed” or “approved”.
- Retries are safe because the command carries an idempotency key (ADR-003).
- Conflicts are explicit and resolvable.

**Cons:**

- Approvals and scheduling require server confirmation; the command may be queued offline, but the UI stays pending until the server commits.
- The app needs an outbox, a sync loop, and conflict UI.
- The cache can be stale; the UI must show “last synced”.

**Chosen.**

### Option D — Server-authoritative with a stored status boolean on the client

The server stores `is_approved` and the client mirrors it.

**Pros:** simple to render.

**Cons:** the boolean can drift from the revision and decision. It is the same modelling error as ADR-001, moved to a different layer. Rejected.

---

## Decision

1. **PostgreSQL is the system of record** for campaigns, revisions, decisions, schedules, and audit events.
2. **The mobile SQLite database is a projection** of the last confirmed server state. It is never authoritative for approval or scheduling eligibility.
3. **Every mutating action is a command** persisted to the outbox before any network call. The command carries an idempotency key that is never regenerated.
4. **The UI displays three distinct concepts:**
   - confirmed server state (“Approved by Arjun · 11:02”);
   - pending overlay (“Confirming approval…”);
   - conflict (“Revision 4 is now current”).
5. **Approval eligibility is derived on the server** and returned as `canSchedule` and `allowedActions`. The client does not compute it from status strings.
6. **Offline authorisation is not supported.** A user may queue an approval or schedule command while offline, but it is not approved or scheduled until the server commits it. Draft editing and reading are supported offline. This is a deliberate scope decision, not an oversight.

### State ownership

| State | Owner |
|---|---|
| Revision and schedule state | Server |
| Pending command | Client outbox |
| Confirmed read model | Server, cached by client |
| Approval eligibility | Server, derived |
| “Last synced” indicator | Client |

---

## Consequences

### Positive

- There is exactly one place where a revision becomes `APPROVED`: the server transaction.
- A network timeout cannot produce a false approval label.
- Conflicts are explicit; the client never silently merges a decision.
- The same API can serve a future web client without changing the authority model.
- The outbox gives a natural recovery path after an app kill.

### Negative

- A reviewer cannot get an approval confirmed on a plane. The command can be queued, but the decision waits for the server. For this product, that is acceptable: approval is a high-risk action that benefits from fresh content.
- The client is more complex: outbox schema, ordering, retry, reconciliation.
- The cache can be stale. The UI must be honest about it; “last synced 2 min ago” is part of the design, not a polish item.
- A pending command blocks later commands for the same campaign. This is intentional ordering, but it can feel slow; the UI explains why.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| User believes a pending approval succeeded | UI never shows “Approved” until confirmed; live region announces “Confirming…” |
| App killed after send, before response | On restart, query `GET /commands/:key` before resending; same key |
| App killed before outbox write | No request was sent; user retries; no duplicate |
| Conflicting edit on another device | Server returns `EDIT_CONFLICT`; client reloads and shows the difference |
| Cache serves an old revision | Every command carries `expectedContentHash`; server rejects stale content |
| Outbox grows forever | Max age 24 h; `FAILED` rows surfaced to the user; completed rows pruned |
| User switches devices | Pending commands are device-local; the server state is authoritative; the other device sees the confirmed result |

---

## Enforcement points

| Layer | Enforcement |
|---|---|
| Mobile repository | No method sets revision state; only `putCampaign(view)` from the server |
| Outbox | Command persisted before send; key immutable |
| Sync engine | Per-campaign ordering; reconcile `IN_FLIGHT` on start |
| API | Server computes `allowedActions` and `canSchedule`; validates every command |
| Domain | `evaluateScheduleEligibility` is server-only authority |
| Tests | T-20, T-21, T-22; conflict tests T-10, T-12 |

---

## Verification

- **T-20:** write an outbox row, kill the app before sending, restart; assert one request and one effect.
- **T-21:** send, kill the app before the response, restart; assert `GET /commands/:key` resolves the outcome and no duplicate decision exists.
- **T-22:** disable the network, tap Approve; assert the UI shows “Confirming…”, not “Approved”; reconnect; assert the confirmed state appears once.
- **T-10:** two devices, one stale; assert the stale device receives `REVISION_STALE` and does not change state.

---

## When we would revisit this decision

1. **Long offline field work:** if reviewers routinely work without connectivity, move to a local-first model with explicit conflict resolution and a server-side merge policy. The approval invariant would still need a server check at schedule time.
2. **Real-time collaboration:** if multiple reviewers need live presence and simultaneous decisions, add a subscription channel. The server remains the authority; the channel is a latency optimisation.
3. **Multi-device pending commands:** if users expect a draft started on one device to continue on another, move the outbox to the server as a “command journal”. This is a bigger change; it turns the outbox into a server-side workflow.
4. **Regulated offline authorisation:** if the business requires offline approval decisions, they must be signed locally, reconciled with the server, and scheduling must still be blocked until reconciliation. This is a product decision, not just a technical one.

---

## Related decisions

- [ADR-001](ADR-001-revision-bound-approvals.md) — what the server is authoritative about.
- [ADR-003](ADR-003-idempotent-commands-and-audit.md) — how the outbox retries safely.
- [`03-low-level-design.md`](../03-low-level-design.md) §10 — outbox schema and sync loop.
