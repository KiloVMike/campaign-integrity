import os
import subprocess
import sys

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

BASE_CSS = """
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: #0b0f19;
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.08) 0%, transparent 40%),
      radial-gradient(circle at 90% 80%, rgba(99, 102, 241, 0.07) 0%, transparent 40%),
      linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 100% 100%, 100% 100%, 28px 28px, 28px 28px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #f1f5f9;
    padding: 24px 32px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 18px;
  }
  .title-group h1 {
    font-size: 22pt;
    font-weight: 850;
    letter-spacing: -0.5px;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .title-group h1 .tag {
    font-size: 9.5pt;
    font-weight: 700;
    color: #60a5fa;
    background: rgba(37,99,235,0.18);
    border: 1px solid rgba(96,165,250,0.35);
    padding: 3px 9px;
    border-radius: 5px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
  }
  .title-group p {
    font-size: 10.5pt;
    color: #94a3b8;
    margin-top: 3px;
    font-weight: 500;
  }
  .meta-badges {
    text-align: right;
    display: flex;
    gap: 8px;
  }
  .meta-badge {
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 8pt;
    color: #cbd5e1;
    font-weight: 600;
  }
  .meta-badge.highlight {
    background: rgba(30, 58, 138, 0.4);
    border-color: #3b82f6;
    color: #93c5fd;
  }
  .card-title {
    font-size: 10pt;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #94a3b8;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .card-title .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #3b82f6;
    display: inline-block;
  }
  .footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid rgba(255,255,255,0.1);
    font-size: 8.5pt;
    color: #64748b;
  }
"""

# ==============================================================================
# DIAGRAM 1: SYSTEM CONTEXT & BOUNDARIES
# ==============================================================================
html_d1 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .layout-grid {{
    display: grid;
    grid-template-columns: 2.3fr 1fr;
    gap: 18px;
  }}
  .context-canvas {{
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .actors-row {{
    display: flex;
    justify-content: space-around;
    gap: 16px;
  }}
  .actor-box {{
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 10px;
    padding: 14px 20px;
    width: 48%;
    text-align: center;
  }}
  .actor-icon {{ font-size: 22pt; margin-bottom: 4px; }}
  .actor-name {{ font-size: 12pt; font-weight: 850; color: #ffffff; }}
  .actor-desc {{ font-size: 8.5pt; color: #94a3b8; margin-top: 4px; line-height: 1.3; }}
  
  .core-flow-box {{
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid #2563eb;
    border-radius: 12px;
    padding: 18px;
    box-shadow: 0 0 30px rgba(37, 99, 235, 0.15);
  }}
  .flow-diagram {{
    display: grid;
    grid-template-columns: 1fr 45px 1.2fr 45px 1fr;
    align-items: center;
    gap: 8px;
    margin: 10px 0;
  }}
  .node-box {{
    background: rgba(30, 41, 59, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 16px 12px;
    text-align: center;
  }}
  .node-box.mobile {{
    border-color: #3b82f6;
    background: linear-gradient(180deg, rgba(37,99,235,0.18) 0%, rgba(15,23,42,0.95) 100%);
  }}
  .node-box.api {{
    border-color: #8b5cf6;
    background: linear-gradient(180deg, rgba(139,92,246,0.18) 0%, rgba(15,23,42,0.95) 100%);
  }}
  .node-box.db {{
    border-color: #10b981;
    background: linear-gradient(180deg, rgba(16,185,129,0.18) 0%, rgba(15,23,42,0.95) 100%);
  }}
  .node-title {{ font-size: 11pt; font-weight: 850; color: #ffffff; margin-bottom: 5px; }}
  .node-sub {{ font-size: 8.2pt; color: #94a3b8; line-height: 1.25; }}
  .arrow-conn {{
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #60a5fa;
    font-size: 7.5pt;
    font-weight: 700;
    text-align: center;
  }}
  .arrow-conn .arr {{ font-size: 16pt; line-height: 1; }}
  .sub-components {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 14px;
  }}
  .sub-card {{
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 8.5pt;
    line-height: 1.3;
  }}
  .sub-card strong {{ color: #60a5fa; display: block; margin-bottom: 2px; }}
  .boundaries-col {{ display: flex; flex-direction: column; gap: 14px; }}
  .scope-box {{ border-radius: 8px; padding: 14px 16px; font-size: 8.8pt; }}
  .scope-box.in {{ background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); }}
  .scope-box.out {{ background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); }}
  .scope-title {{ font-weight: 850; margin-bottom: 8px; font-size: 9.5pt; display: flex; align-items: center; gap: 6px; }}
  .scope-box.in .scope-title {{ color: #34d399; }}
  .scope-box.out .scope-title {{ color: #f87171; }}
  .scope-list {{ list-style: none; line-height: 1.5; color: #cbd5e1; }}
  .scope-list li {{ margin-bottom: 4px; position: relative; padding-left: 14px; }}
  .scope-box.in li::before {{ content: "✓"; position: absolute; left: 0; color: #10b981; font-weight: bold; }}
  .scope-box.out li::before {{ content: "✕"; position: absolute; left: 0; color: #ef4444; font-weight: bold; }}
</style>
</head>
<body style="width: 1600px; height: 820px;">
  <div class="header">
    <div class="title-group">
      <h1>HLD Diagram 01: System Context & Boundaries <span class="tag">Architecture Overview</span></h1>
      <p>Campaign Integrity — Version-Aware Campaign Approval & Scheduling Engine</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">Track: Martech</div>
      <div class="meta-badge">Team: MAL 4</div>
      <div class="meta-badge">1 Nov 2026</div>
    </div>
  </div>

  <div class="layout-grid">
    <div class="context-canvas">
      <div class="actors-row">
        <div class="actor-box">
          <div class="actor-icon">👤</div>
          <div class="actor-name">Marketer Role</div>
          <div class="actor-desc">Authors proposals, edits drafts, submits for review, revises upon feedback, initiates atomic schedule requests.</div>
        </div>
        <div class="actor-box">
          <div class="actor-icon">🛡️</div>
          <div class="actor-name">Reviewer Role</div>
          <div class="actor-desc">Reviews current revisions, signs approval bound to SHA-256 hash, or requests changes. Strictly prohibited from self-review.</div>
        </div>
      </div>

      <div class="core-flow-box">
        <div class="card-title"><span class="dot"></span> End-to-End System Integration Flow</div>
        <div class="flow-diagram">
          <div class="node-box mobile">
            <div class="node-title">Mobile App</div>
            <div class="node-sub">React Native + Expo<br/>Local SQLite Read Cache<br/>Command Outbox Sync</div>
          </div>
          <div class="arrow-conn">
            <span>HTTPS</span>
            <span class="arr">➔</span>
            <span>JSON</span>
          </div>
          <div class="node-box api">
            <div class="node-title">Campaign Integrity API</div>
            <div class="node-sub">Modular Monolith<br/>Transaction Boundaries<br/>Idempotency & Invariants</div>
          </div>
          <div class="arrow-conn">
            <span>ACID</span>
            <span class="arr">➔</span>
            <span>SQL</span>
          </div>
          <div class="node-box db">
            <div class="node-title">PostgreSQL Database</div>
            <div class="node-sub">System of Record<br/>Row Locks (FOR UPDATE)<br/>Append-only Audit Log</div>
          </div>
        </div>

        <div class="sub-components">
          <div class="sub-card">
            <strong>Client-Side Outbox Pattern</strong>
            Every user action is written to local SQLite first with an Idempotency-Key UUID. Background sync guarantees delivery across process kills and network drops.
          </div>
          <div class="sub-card">
            <strong>Observability & Diagnostics</strong>
            Stateless API emits structured JSON logs with correlation IDs, domain state metrics, and audit entries to monitoring sinks for rapid incident troubleshooting.
          </div>
        </div>
      </div>
    </div>

    <div class="boundaries-col">
      <div class="scope-box in">
        <div class="scope-title"><span>✓</span> In Scope (Owned & Guaranteed)</div>
        <ul class="scope-list">
          <li>Immutable revision control tree & copy-on-write</li>
          <li>SHA-256 cryptographic content verification</li>
          <li>Single atomic schedule gate (PostgreSQL row lock)</li>
          <li>Automatic schedule cancellation on post-approval edit</li>
          <li>Local SQLite outbox & idempotent command sync</li>
          <li>Tamper-evident append-only audit trail</li>
          <li>Strict segregation of duties enforcement</li>
        </ul>
      </div>

      <div class="scope-box out">
        <div class="scope-title"><span>✕</span> Out of Scope (Honest Non-Goals)</div>
        <ul class="scope-list">
          <li>Ad network publishing (Meta Ads, Google Ads)</li>
          <li>Creative media rendering, video CDN, asset store</li>
          <li>Payment gateway billing & spend reconciliation</li>
          <li>Push notifications / email delivery transport</li>
          <li>SSO & multi-tenant enterprise isolation</li>
          <li>Dual multi-party approvals (deferred to ADR-001)</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Campaign Integrity Architecture:</strong> "The campaign that gets scheduled is the exact campaign that was approved."</div>
    <div>System Context Blueprint · High-Level Design Section 2</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# DIAGRAM 2: CONTAINERS & COMPONENTS
# ==============================================================================
html_d2 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .layout-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  .container-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .container-card.mobile {{
    border-color: #3b82f6;
    box-shadow: 0 0 25px rgba(37,99,235,0.12);
  }}
  .container-card.server {{
    border-color: #8b5cf6;
    box-shadow: 0 0 25px rgba(139,92,246,0.12);
  }}
  .container-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
  }}
  .container-title {{ font-size: 12.5pt; font-weight: 850; color: #ffffff; }}
  .container-tech {{
    font-size: 8.5pt;
    color: #94a3b8;
    background: rgba(255,255,255,0.06);
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
  }}
  .layer-stack {{
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}
  .layer-box {{
    background: rgba(30, 41, 59, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 9px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .layer-info strong {{ display: block; font-size: 9.5pt; color: #f1f5f9; }}
  .layer-info span {{ font-size: 8pt; color: #94a3b8; line-height: 1.2; }}
  .layer-role {{
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 4px;
    white-space: nowrap;
  }}
  .role-ui {{ background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }}
  .role-app {{ background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); }}
  .role-domain {{ background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }}
  .role-data {{ background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }}

  .bridge-box {{
    grid-column: 1 / -1;
    background: rgba(15, 23, 42, 0.95);
    border: 1px solid #3b82f6;
    border-radius: 10px;
    padding: 12px 18px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    font-size: 8.8pt;
  }}
  .bridge-item {{ display: flex; align-items: center; gap: 8px; color: #cbd5e1; }}
  .bridge-item strong {{ color: #60a5fa; }}
  .dep-banner {{
    background: rgba(30, 41, 59, 0.6);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 8.5pt;
    color: #cbd5e1;
    border-left: 3px solid #10b981;
  }}
</style>
</head>
<body style="width: 1600px; height: 960px;">
  <div class="header">
    <div class="title-group">
      <h1>HLD Diagram 02: Containers & Components <span class="tag">Clean Architecture</span></h1>
      <p>Clean Separation of Duties, Domain Isolation & Dependency Rules</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">Modular Monolith</div>
      <div class="meta-badge">Offline-First Outbox</div>
      <div class="meta-badge">HLD Section 3</div>
    </div>
  </div>

  <div class="layout-grid">
    <div class="container-card mobile">
      <div class="container-header">
        <div class="container-title">📱 Mobile Client Container</div>
        <div class="container-tech">React Native · Expo · TypeScript</div>
      </div>
      <div class="layer-stack">
        <div class="layer-box">
          <div class="layer-info">
            <strong>Screens & UI Components</strong>
            <span>Campaign dashboard, revision comparison, review drawer, action triggers</span>
          </div>
          <span class="layer-role role-ui">Presentation</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>View Models & Use Cases</strong>
            <span>Orchestrates reads, handles form state, dispatches commands to repositories</span>
          </div>
          <span class="layer-role role-app">Application</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>Mobile Domain Helpers</strong>
            <span>Pure TypeScript display logic & local form validations (never decides approval)</span>
          </div>
          <span class="layer-role role-domain">Pure Logic</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>Local Repositories</strong>
            <span>Abstracts storage, queries local read projection, enqueues to outbox</span>
          </div>
          <span class="layer-role role-data">Data Port</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>SQLite Read Cache & Outbox Sync Engine</strong>
            <span>Persists command intent before network send; handles retries & process kill recovery</span>
          </div>
          <span class="layer-role role-data">Persistence</span>
        </div>
      </div>
      <div class="dep-banner">
        <strong>Mobile Rule:</strong> Client never locally advances state to APPROVED. UI only displays "Confirming approval..." until server confirms.
      </div>
    </div>

    <div class="container-card server">
      <div class="container-header">
        <div class="container-title">⚙️ Server API Container</div>
        <div class="container-tech">Node.js · Express · TypeScript · PostgreSQL</div>
      </div>
      <div class="layer-stack">
        <div class="layer-box">
          <div class="layer-info">
            <strong>HTTP Transport & Middleware Layer</strong>
            <span>JWT / role auth, schema parsing, Idempotency-Key extraction, error envelopes</span>
          </div>
          <span class="layer-role role-ui">Transport</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>Application Services</strong>
            <span>Transaction management, command orchestration, authorization & audit emission</span>
          </div>
          <span class="layer-role role-app">Application</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>Domain Model (Core Invariants)</strong>
            <span>State machine, eligibility predicate, canonical SHA-256 hash, copy-on-write fork</span>
          </div>
          <span class="layer-role role-domain">Domain Core</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>Server Persistence Repositories</strong>
            <span>SQL queries, row-level locking (SELECT FOR UPDATE), constraint error mapping</span>
          </div>
          <span class="layer-role role-data">Data Adapter</span>
        </div>
        <div class="layer-box">
          <div class="layer-info">
            <strong>PostgreSQL ACID System of Record</strong>
            <span>Immutable revision log, append-only audit_events, idempotency_keys table</span>
          </div>
          <span class="layer-role role-data">Database</span>
        </div>
      </div>
      <div class="dep-banner">
        <strong>Dependency Rule:</strong> Domain imports NOTHING from Express, SQL, or React. Presentation ➔ Application ➔ Domain ➔ Data implements ports.
      </div>
    </div>

    <div class="bridge-box">
      <div class="bridge-item">
        <span>📤</span>
        <span><strong>Outbox Command Sync:</strong> Client sends <code>POST /v1/...</code> with <code>Idempotency-Key: &lt;UUID&gt;</code></span>
      </div>
      <div class="bridge-item">
        <span>📥</span>
        <span><strong>Confirmed Projection:</strong> Server returns authoritative snapshot; client writes directly to SQLite</span>
      </div>
      <div class="bridge-item">
        <span>🛡️</span>
        <span><strong>Deterministic Conflict:</strong> Stale revision or hash mismatch returns <code>409 Conflict</code> (never silent overwrite)</span>
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Design Integrity:</strong> Modular monolith guarantees one atomic transaction for state transitions, eliminating distributed sagas.</div>
    <div>Container and Component Blueprint · High-Level Design Section 3</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# DIAGRAM 3: MAJOR DATA FLOWS & ATOMIC TRANSACTIONS
# ==============================================================================
html_d3 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .seq-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
  }}
  .seq-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 16px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .seq-card.primary {{ border-top: 3px solid #3b82f6; }}
  .seq-card.warning {{ border-top: 3px solid #f59e0b; }}
  .seq-card.success {{ border-top: 3px solid #10b981; }}

  .seq-title {{ font-size: 11pt; font-weight: 850; color: #ffffff; margin-bottom: 4px; }}
  .seq-sub {{ font-size: 8pt; color: #94a3b8; margin-bottom: 12px; line-height: 1.25; }}
  .timeline {{ display: flex; flex-direction: column; gap: 8px; }}
  .time-step {{
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 8pt;
    line-height: 1.25;
  }}
  .time-step strong {{ color: #60a5fa; display: block; font-size: 8.5pt; margin-bottom: 2px; }}
  .time-step.db {{ background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.25); }}
  .time-step.db strong {{ color: #34d399; }}
  .time-step.warn {{ background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.25); }}
  .time-step.warn strong {{ color: #fbbf24; }}
  .time-step.danger {{ background: rgba(239, 68, 68, 0.08); border-color: rgba(239, 68, 68, 0.25); }}
  .time-step.danger strong {{ color: #f87171; }}
  .highlight-rule {{
    margin-top: 10px;
    padding: 6px 8px;
    background: rgba(0,0,0,0.3);
    border-radius: 4px;
    border-left: 2px solid #3b82f6;
    font-size: 7.8pt;
    color: #cbd5e1;
  }}
</style>
</head>
<body style="width: 1600px; height: 960px;">
  <div class="header">
    <div class="title-group">
      <h1>HLD Diagram 03: Major Data Flows & Atomic Transactions <span class="tag">Sequence Verification</span></h1>
      <p>Idempotent Command Execution, Copy-on-Write Invalidation & Single Atomic Gate</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">PostgreSQL Row-Locks</div>
      <div class="meta-badge">SHA-256 Hashing</div>
      <div class="meta-badge">HLD Section 5</div>
    </div>
  </div>

  <div class="seq-grid">
    <div class="seq-card primary">
      <div>
        <div class="seq-title">5.1 Create, Submit & Decide</div>
        <div class="seq-sub">Standard review cycle bound cryptographically to revision hash</div>
        <div class="timeline">
          <div class="time-step">
            <strong>1. Marketer ➔ API: Create</strong>
            <code>POST /v1/campaigns</code> with Idempotency-Key.
          </div>
          <div class="time-step db">
            <strong>2. Transaction: Claim Key & Insert</strong>
            Inserts Campaign + Revision 1 (DRAFT) + Audit row.
          </div>
          <div class="time-step">
            <strong>3. Marketer ➔ API: Submit</strong>
            <code>POST /v1/.../submit</code> locks row, transitions Rev 1 ➔ IN_REVIEW.
          </div>
          <div class="time-step warn">
            <strong>4. Reviewer: Request Changes</strong>
            Mandatory note logged; Marketer edits (Rev 2 DRAFT created & submitted).
          </div>
          <div class="time-step db">
            <strong>5. Transaction: Approval Binding</strong>
            Locks row, validates current Rev 2 in IN_REVIEW, computes SHA-256 hash.
          </div>
          <div class="time-step db">
            <strong>6. Commit: Bound Decision</strong>
            Inserts Decision row bound to Rev 2 ID + Hash. Rev 2 ➔ APPROVED.
          </div>
        </div>
      </div>
      <div class="highlight-rule">
        <strong>Rule BR-2:</strong> Decision records exact revision ID and content hash. Approval cannot exist without an immutable revision target.
      </div>
    </div>

    <div class="seq-card warning">
      <div>
        <div class="seq-title">5.2 Edit Post-Approval / Schedule</div>
        <div class="seq-sub">Copy-on-write mutation atomically revokes schedule & approval</div>
        <div class="timeline">
          <div class="time-step">
            <strong>1. Marketer Edits Approved Campaign</strong>
            <code>PATCH /v1/campaigns/CMP-1042</code> (e.g. Budget ₹5L ➔ ₹8L).
          </div>
          <div class="time-step db">
            <strong>2. BEGIN Transaction: Exclusive Lock</strong>
            <code>SELECT * FROM campaigns FOR UPDATE</code>.
          </div>
          <div class="time-step warn">
            <strong>3. Invalidate Previous State</strong>
            Revision 2 marked SUPERSEDED. Prior approval invalid for scheduling.
          </div>
          <div class="time-step db">
            <strong>4. Copy-on-Write Fork</strong>
            Inserts Revision 3 DRAFT with new budget; updates current_revision_id.
          </div>
          <div class="time-step danger">
            <strong>5. Revoke Active Schedule</strong>
            Cancels schedule SCH-7001 (reason: REVISION_SUPERSEDED).
          </div>
          <div class="time-step db">
            <strong>6. Atomic COMMIT</strong>
            Emits 2 audit events. Returns 200: approvalInvalidated=true.
          </div>
        </div>
      </div>
      <div class="highlight-rule">
        <strong>Rule BR-3:</strong> Edit and schedule cancellation execute in the SAME transaction. Zero window where a schedule targets superseded content.
      </div>
    </div>

    <div class="seq-card success">
      <div>
        <div class="seq-title">5.3 Single Atomic Schedule Gate</div>
        <div class="seq-sub">Four strict eligibility checks evaluated under PostgreSQL row lock</div>
        <div class="timeline">
          <div class="time-step">
            <strong>1. Marketer Initiates Schedule</strong>
            <code>POST /v1/.../schedule</code> with revision ID, hash & launch time.
          </div>
          <div class="time-step db">
            <strong>2. BEGIN: Exclusive Lock</strong>
            <code>SELECT campaign FOR UPDATE</code>; claims Idempotency-Key.
          </div>
          <div class="time-step db">
            <strong>3. Check 1: Current Revision?</strong>
            Verifies <code>req.revisionId == campaign.current_rev_id</code>.
          </div>
          <div class="time-step db">
            <strong>4. Check 2 & 3: Approved & Hash Match?</strong>
            Verifies state=APPROVED and decision.hash == revision.hash.
          </div>
          <div class="time-step db">
            <strong>5. Check 4: Uniqueness?</strong>
            Verifies no active SCHEDULED row exists for campaign.
          </div>
          <div class="time-step db">
            <strong>6. COMMIT or ROLLBACK</strong>
            If all pass: inserts schedule + audit. Else: ROLLBACK + 409 Conflict.
          </div>
        </div>
      </div>
      <div class="highlight-rule">
        <strong>Rule BR-1 & Invariant:</strong> active_schedule(c) ⇒ current_rev.state=APPROVED ∧ decision.rev_id=current_rev.id ∧ decision.hash=current_rev.hash.
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Concurrency Guarantee:</strong> Exclusive row locks prevent double scheduling and eliminate review/edit race conditions.</div>
    <div>Data Flows & Sequence Blueprint · High-Level Design Section 5</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# DIAGRAM 4: DEPLOYMENT TOPOLOGY & SECURITY
# ==============================================================================
html_d4 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .layout-grid {{
    display: grid;
    grid-template-columns: 1.8fr 1.2fr;
    gap: 18px;
  }}
  .topo-canvas {{
    background: rgba(15, 23, 42, 0.85);
    border: 1.5px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .tier-box {{
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .tier-label {{
    font-size: 8.5pt;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #60a5fa;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .tier-items {{
    display: flex;
    justify-content: space-around;
    gap: 10px;
  }}
  .tier-node {{
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 10px 12px;
    flex: 1;
    text-align: center;
  }}
  .tier-node strong {{ display: block; font-size: 9.5pt; color: #ffffff; margin-bottom: 2px; }}
  .tier-node span {{ font-size: 7.8pt; color: #94a3b8; }}
  .tier-arrow {{
    text-align: center;
    color: #3b82f6;
    font-size: 13pt;
    line-height: 1;
  }}

  .sec-panel {{
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .sec-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px 14px;
  }}
  .sec-card-title {{
    font-size: 9.2pt;
    font-weight: 800;
    color: #f1f5f9;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .sec-card-body {{
    font-size: 8.2pt;
    color: #94a3b8;
    line-height: 1.35;
  }}
</style>
</head>
<body style="width: 1600px; height: 820px;">
  <div class="header">
    <div class="title-group">
      <h1>HLD Diagram 04: Deployment Topology & Security Model <span class="tag">Production Architecture</span></h1>
      <p>Stateless API Tier, ACID System of Record & Defense-in-Depth</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">TLS / OIDC / JWT</div>
      <div class="meta-badge">Insert-Only Audit</div>
      <div class="meta-badge">HLD Section 7 & 8</div>
    </div>
  </div>

  <div class="layout-grid">
    <div class="topo-canvas">
      <div class="tier-box">
        <div class="tier-label"><span>📱</span> Client Tier (Participant Devices)</div>
        <div class="tier-items">
          <div class="tier-node">
            <strong>iOS / Android Device</strong>
            <span>React Native + Expo UI</span>
          </div>
          <div class="tier-node">
            <strong>Local SQLite Engine</strong>
            <span>Read Cache + Command Outbox</span>
          </div>
        </div>
      </div>

      <div class="tier-arrow">⬇ HTTPS / TLS 1.3 · Bearer JWT · Idempotency-Key UUID ⬇</div>

      <div class="tier-box">
        <div class="tier-label"><span>☁️</span> Cloud Ingress & Compute Tier</div>
        <div class="tier-items">
          <div class="tier-node">
            <strong>HTTPS Load Balancer</strong>
            <span>TLS termination, rate limiting</span>
          </div>
          <div class="tier-node">
            <strong>API Node 1 (Stateless)</strong>
            <span>Express · Node.js · Modular Monolith</span>
          </div>
          <div class="tier-node">
            <strong>API Node 2 (Stateless)</strong>
            <span>Express · Node.js · Modular Monolith</span>
          </div>
        </div>
      </div>

      <div class="tier-arrow">⬇ Connection Pooling · Row-Locks (SELECT FOR UPDATE) ⬇</div>

      <div class="tier-box">
        <div class="tier-label"><span>🗄️</span> Data & Observability Tier</div>
        <div class="tier-items">
          <div class="tier-node" style="border-color: #10b981;">
            <strong style="color: #34d399;">Managed PostgreSQL</strong>
            <span>Primary System of Record + Automated Backup</span>
          </div>
          <div class="tier-node" style="border-color: #8b5cf6;">
            <strong style="color: #c4b5fd;">Append-Only Audit Log</strong>
            <span>INSERT-only permission; UPDATE/DELETE revoked</span>
          </div>
          <div class="tier-node">
            <strong>Structured Observability</strong>
            <span>JSON logs, domain metrics, correlation traces</span>
          </div>
        </div>
      </div>
    </div>

    <div class="sec-panel">
      <div class="sec-card">
        <div class="sec-card-title">🔐 Segregation of Duties</div>
        <div class="sec-card-body">Enforced in the application service layer: <code>actor_id ≠ campaign.creator_id</code>. Reviewers cannot approve their own campaigns. Authors cannot review their own proposals.</div>
      </div>

      <div class="sec-card">
        <div class="sec-card-title">🛡️ Replay & Crash Defense</div>
        <div class="sec-card-body">Client-generated UUID idempotency keys stored with request hash and response payload. Duplicate or retried requests replay the exact response without re-executing side effects.</div>
      </div>

      <div class="sec-card">
        <div class="sec-card-title">📜 Tamper-Evident Audit Trail</div>
        <div class="sec-card-body">Every committed state transition inserts an <code>audit_events</code> row with actor ID, timestamp, revision ID, SHA-256 hash, and correlation ID within the same ACID transaction.</div>
      </div>

      <div class="sec-card">
        <div class="sec-card-title">🔒 Concurrency Protection</div>
        <div class="sec-card-body">PostgreSQL row-level locks (<code>SELECT FOR UPDATE</code>) serialize concurrent reviews and schedule requests. Partial unique index guarantees zero duplicate active schedules.</div>
      </div>
    </div>
  </div>

  <div class="footer">
    <div><strong>Deployment Foundation:</strong> Stateless API horizontally scales freely; coordination and consistency are maintained by PostgreSQL ACID guarantees.</div>
    <div>Deployment and Security Blueprint · High-Level Design Section 7 & 8</div>
  </div>
</body>
</html>
"""

# ==============================================================================
# DIAGRAM 5: MASTER ARCHITECTURE BOARD
# ==============================================================================
html_d5 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  {BASE_CSS}
  .master-board {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-top: 14px;
  }}
  .invariant-banner {{
    background: linear-gradient(135deg, #0b1329 0%, #1e293b 100%);
    border: 1.5px solid #3b82f6;
    border-radius: 8px;
    padding: 10px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
  }}
  .inv-left {{ font-weight: 850; font-size: 11pt; color: #60a5fa; text-transform: uppercase; }}
  .inv-center {{ font-family: monospace; font-size: 9pt; color: #ffffff; background: rgba(255,255,255,0.08); padding: 4px 12px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.15); }}
  .inv-right {{ font-style: italic; font-size: 9.5pt; color: #cbd5e1; }}
  .board-card {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .board-card h3 {{
    font-size: 11pt;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #60a5fa;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 6px;
  }}
  .board-content {{
    font-size: 8.8pt;
    color: #cbd5e1;
    line-height: 1.4;
  }}
  .board-content strong {{ color: #ffffff; }}
  .item-list {{ list-style: none; padding: 0; }}
  .item-list li {{
    margin-bottom: 8px;
    padding-left: 14px;
    position: relative;
  }}
  .item-list li::before {{
    content: "■";
    position: absolute;
    left: 0;
    font-size: 6pt;
    top: 3px;
    color: #3b82f6;
  }}
  .pill-tech {{
    display: inline-block;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    padding: 2px 7px;
    border-radius: 3px;
    font-size: 7.5pt;
    margin-right: 4px;
    color: #94a3b8;
  }}
</style>
</head>
<body style="width: 2200px; height: 1020px; padding: 26px 36px;">
  <div class="header">
    <div class="title-group">
      <h1>Campaign Integrity — Master Architecture Blueprint <span class="tag">High-Level Design</span></h1>
      <p>Version-Aware Approval Architecture & Single Atomic Gate for Enterprise Marketing Systems</p>
    </div>
    <div class="meta-badges">
      <div class="meta-badge highlight">Track: Martech Approval</div>
      <div class="meta-badge">Team: MAL 4</div>
      <div class="meta-badge">Architecture-First Submission</div>
      <div class="meta-badge">1 Nov 2026</div>
    </div>
  </div>

  <div class="invariant-banner">
    <div class="inv-left">The Core Invariant</div>
    <div class="inv-center">active_schedule(c) ⇒ current_rev(c).state = APPROVED ∧ decision.rev_id = current_rev(c).id ∧ decision.content_hash = current_rev(c).content_hash</div>
    <div class="inv-right">“The campaign that gets scheduled is the exact campaign that was approved.”</div>
  </div>

  <div class="master-board">
    <div class="board-card">
      <h3>1. System Context & Roles</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Marketer Role:</strong> Authors proposals, edits drafts, submits for review, revises after feedback, schedules approved campaigns. Strictly separated from approval permissions.</li>
          <li><strong>Reviewer Role:</strong> Inspects submitted content, signs approval bound to SHA-256 content hash, or requests changes. Strictly prohibited from approving self-authored proposals.</li>
          <li><strong>System Engine:</strong> Enforces state machine, computes hashes, executes atomic row-locked scheduling checks, and records append-only audit events.</li>
        </ul>
        <div style="margin-top: 10px;">
          <span class="pill-tech">React Native</span>
          <span class="pill-tech">SQLite Cache</span>
          <span class="pill-tech">Command Outbox</span>
        </div>
      </div>
    </div>

    <div class="board-card">
      <h3>2. Containers & Clean Architecture</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Mobile App (React Native + Expo):</strong> UI Screens ➔ ViewModels ➔ Mobile Domain Helpers ➔ Repositories ➔ SQLite Outbox Engine.</li>
          <li><strong>API Modular Monolith (Node.js + TS):</strong> HTTP Layer (JWT/Schema validation) ➔ Application Services (Tx boundary) ➔ Domain Model (Invariants) ➔ Persistence Repositories.</li>
          <li><strong>PostgreSQL ACID Engine:</strong> Campaigns, Revisions, Decisions, Schedules, AuditEvents, and IdempotencyKeys tables.</li>
          <li><strong>Dependency Inversion:</strong> Domain core imports nothing from Express or SQL. Data layer implements domain repository ports.</li>
        </ul>
      </div>
    </div>

    <div class="board-card">
      <h3>3. Source of Truth Matrix</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>PostgreSQL:</strong> Sole system of record for campaigns, immutable revisions, decisions, schedules, and audit events.</li>
          <li><strong>Client SQLite:</strong> Read projection cache + intent outbox queue. Client is never authoritative.</li>
          <li><strong>Approval Eligibility:</strong> Dynamically <strong>derived</strong> from (current_revision + decision + matching_hash). Never stored as a mutable boolean flag.</li>
          <li><strong>Observability:</strong> Structured JSON logs, domain metrics, and correlation IDs for runtime diagnostics.</li>
        </ul>
      </div>
    </div>

    <div class="board-card">
      <h3>4. Copy-on-Write Lifecycle</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>Proposal Submission:</strong> Rev 1 created in DRAFT ➔ locked in IN_REVIEW.</li>
          <li><strong>Changes Requested:</strong> Reviewer notes feedback ➔ Marketer revises ➔ Copy-on-Write forks Rev 2 DRAFT (Rev 1 superseded).</li>
          <li><strong>Bound Approval:</strong> Reviewer approves Rev 2 ➔ Decision bound to Rev 2 ID + SHA-256 hash.</li>
          <li><strong>Single Atomic Gate:</strong> <code>SELECT FOR UPDATE</code> verifies revision state, hash match, and schedule uniqueness before inserting schedule.</li>
          <li><strong>Post-Approval Guard:</strong> Any edit post-approval forks Rev 3 DRAFT and atomically cancels active schedules.</li>
        </ul>
      </div>
    </div>

    <div class="board-card">
      <h3>5. Architectural Business Rules</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>BR-1 Eligibility Gate:</strong> Only campaigns in approved state are eligible for scheduling.</li>
          <li><strong>BR-2 Revision & Hash Bound:</strong> Decision explicitly matches revision ID and exact SHA-256 content hash.</li>
          <li><strong>BR-3 Copy-on-Write Mutation:</strong> Editing supersedes prior revision and revokes active schedule atomically.</li>
          <li><strong>BR-4 Materiality:</strong> In v1, objective, audience, channel, and budget are material; any change generates a new revision.</li>
          <li><strong>BR-5 Idempotency:</strong> Client UUID keys guarantee exactly-once execution across network retries.</li>
          <li><strong>BR-6 Separation of Duties:</strong> Author cannot review own proposal (service authorization check).</li>
        </ul>
      </div>
    </div>

    <div class="board-card">
      <h3>6. Scope Boundaries & Defensibility</h3>
      <div class="board-content">
        <ul class="item-list">
          <li><strong>In Scope:</strong> Proposals, immutable revisions, SHA-256 verification, row-locked scheduling transaction, SQLite outbox sync, append-only audit trail.</li>
          <li><strong>Honest Non-Goals:</strong> Ad publishing to third parties, creative asset CDN, billing/payments, push notification transport.</li>
          <li><strong>Crash & Network Proof:</strong> SQLite outbox with exponential backoff prevents duplicate taps and reconciles after app kill.</li>
          <li><strong>Evolvability (ADR-001):</strong> Designed for dual multi-party approvals above budget thresholds without altering core invariant.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="footer" style="margin-top: 18px;">
    <div><strong>Campaign Integrity HLD Master Blueprint:</strong> Architecture-First deliverable for MAL Hackathon 2026.</div>
    <div>Complete High-Level Architecture Board · Sections 1 through 12</div>
  </div>
</body>
</html>
"""

diagrams = [
    {
        "name": "hld_01_system_context",
        "html": html_d1,
        "width": 1600,
        "height": 690
    },
    {
        "name": "hld_02_container_components",
        "html": html_d2,
        "width": 1600,
        "height": 730
    },
    {
        "name": "hld_03_transactional_dataflows",
        "html": html_d3,
        "width": 1600,
        "height": 740
    },
    {
        "name": "hld_04_deployment_security",
        "html": html_d4,
        "width": 1600,
        "height": 680
    },
    {
        "name": "hld_master_architecture_board",
        "html": html_d5,
        "width": 2200,
        "height": 690
    }
]

print("Starting generation of HLD diagram images...")
generated_files = []

for diag in diagrams:
    html_filename = f"{diag['name']}.html"
    png_filename = f"{diag['name']}.png"
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(diag["html"])
    
    html_abs = os.path.abspath(html_filename)
    png_abs = os.path.abspath(png_filename)
    
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--screenshot={png_abs}",
        f"--window-size={diag['width']},{diag['height']}",
        html_abs
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(png_abs):
        size = os.path.getsize(png_abs)
        print(f"Generated {png_filename} ({diag['width']}x{diag['height']}) - {size} bytes")
        generated_files.append((png_filename, size))
    else:
        print(f"ERROR: Failed to generate {png_filename}")

print(f"\nCompleted! Generated {len(generated_files)} HLD images successfully in one run.")
