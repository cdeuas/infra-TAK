# v0.8.7-alpha — Work Plan

**Headline (and ONLY) feature: Authentik stability — periodic auto-restart**

Make Authentik *quiet* so the operator doesn't have to think about it. v0.8.5 fixed the acute crashes. v0.8.6 fixed the Azure deploy bugs. **v0.8.7 fixes the chronic CPU-pinning that makes the box feel broken even when nothing is technically wrong.**

> **Scope discipline note (Apr 30 2026):** Earlier drafts had rollback as the v0.8.7 headline. **Rollback has been moved to v0.8.8** — operator stability comes first. Authentik must be silent, predictable, and self-healing before we add new operator features. v0.8.7 is Authentik. v0.8.8 is rollback. No mixing.

---

## 1. Periodic Authentik server+worker auto-restart (the main feature)

### Problem

After ~5h of heavy LDAP load on a DataSync/Node-RED box, Authentik's server + postgres CPU pin at sustained 99% / 93% even with **lower** bind volume than baseline (489/5min) and a 96% bind cache hit rate. Bind work is fine. Internal Authentik runtime state has drifted — likely memory growth, query plan cache fragmentation, session tracker drift, or accumulated event-trigger handler state. Symptoms operators see:

- Slow Node-RED UI (Authentik proxy is the bottleneck, not Node-RED).
- DataSync / Tablet Command WebSocket flows go quiet (cold proxy session, silent reconnect failure).
- Console feels sluggish when navigating Authentik-protected pages.
- Occasional SIGABRTs and outpost recursion errors when individual flows hit the Gunicorn 120s timeout.

The spiral monitor (v0.8.5) doesn't fire because there's no spiral signature — no `idle in transaction` flood, no spiral-specific markers in outpost logs. The system is *functional*, just **expensive and unresponsive**.

### Field evidence (tak-10, Apr 30 2026)

A simple `docker compose up -d --no-deps --force-recreate server worker`:

| Metric | Before recreate | After recreate (5-min soak, 60 samples) |
|---|---|---|
| server p50 CPU | **113.5%** (pinned) | **~24%** (bursty) |
| postgres p50 CPU | **107.7%** (pinned) | **~24%** (bursty) |
| SIGABRT count | 2 in 30 min | **0 in 5 min** |
| Outpost spiral markers | 4 in 30 min | **0 in 5 min** |
| Task creation rate | 415 / 5 min | **237 / 5 min** |

Postgres dropped ~5× immediately. Server flipped from "always on" to responder-style "burst then idle". **Zero LDAP impact** (outpost stayed up, cached SA bind survived, ~30s API blip during recreate).

### Design goals

1. **Automatic.** Operator sets it once (or accepts the default), and tak-10-class boxes never accumulate enough state drift to be felt.
2. **Safe by construction.** Skip if a spiral is currently active (let the spiral monitor own that path). Skip if the box was just deployed/updated (no double restart). Skip if a deploy is in progress.
3. **Off-peak.** Schedule the recreate at a quiet local hour (default 04:00). Configurable.
4. **Honest UX.** Show the operator: "Last Authentik server restart: 3 days ago. Next scheduled: in 4 days at 04:00." So nothing happens behind their back.
5. **Manual override.** "Restart Authentik server now" button for on-demand triggering when an operator notices slowness.
6. **No LDAP downtime.** Only `server` and `worker` containers are recreated — `ldap`, `postgresql`, `redis` stay up.

### Implementation

#### Settings (in `settings.json`)

```json
{
  "authentik_periodic_restart": {
    "enabled": true,
    "interval_hours": 168,
    "window_hour_local": 4,
    "last_run_ts": 0,
    "last_run_outcome": "ok",
    "last_run_duration_s": 0,
    "last_run_evidence": {
      "before": { "server_cpu_p50": 113.5, "postgres_cpu_p50": 107.7 },
      "after":  { "server_cpu_p50": 24.0,  "postgres_cpu_p50": 24.0 }
    }
  }
}
```

#### Scheduler thread (`_authentik_periodic_restart_monitor`)

A background daemon thread, started at module load (alongside `_authentik_spiral_monitor`):

1. Loop every 10 minutes.
2. Read settings → check if `enabled`. If not, sleep.
3. Compute `now_local_hour` and `hours_since_last_run`.
4. Gate checks (all must pass):
   - `hours_since_last_run >= interval_hours`
   - `now_local_hour == window_hour_local` (within a 1h window)
   - `_detect_authentik_ldap_spiral()` returns `False` (don't restart during a spiral)
   - No deploy/update lockfile present
   - Authentik server container has been up for >= 1 hour (don't restart something that just started)
5. If all gates pass, run `_authentik_perform_recreate(plog)`:
   - Sample server + postgres CPU p50 over 30 seconds (the "before").
   - `cd ~/authentik && docker compose up -d --no-deps --force-recreate server worker`.
   - Wait up to 90s for both containers to report `health: starting` → `healthy`.
   - Sample server + postgres CPU p50 over 30 seconds (the "after").
   - Persist outcome to `settings.json`.
6. Log every gate decision to `~/infra-TAK/log/authentik-restart.log` so operators can see what's happening even when nothing fires.

#### Console UI

Single small section under the Authentik status block:

```
Authentik server health
  Last restart: 3 days ago (auto, p50 CPU 113% → 24%)
  Next scheduled: in 4 days at 04:00 local
  [ Restart Authentik server now ]   [ Disable auto-restart ]
```

The "Restart Authentik server now" button:
- Confirmation modal: "This will recreate `authentik-server-1` and `authentik-worker-1`. LDAP, postgres, and the LDAP outpost are NOT affected. Estimated outage: 30s of API requests. Continue?"
- Streams progress identical to other one-shot operations.

The "Disable auto-restart" toggle flips `authentik_periodic_restart.enabled` to false. (Operators on small boxes that don't need it can opt out.)

### Hooks

- Start the monitor thread at module load (line ~end of file, alongside spiral monitor).
- Hook `_authentik_perform_recreate` into:
  - The new console button (manual trigger).
  - The scheduler thread (automatic trigger).
  - Post-update migration (if a v0.8.7-introduced setting needs the recreate to take effect — likely not, but the hook is cheap).

### Default settings on fresh deploy

```json
{
  "enabled": true,
  "interval_hours": 168,
  "window_hour_local": 4
}
```

Weekly at 04:00 local. Conservative default. Operators with very heavy load can drop to 72h. Operators with very light load can disable.

### Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Restart fires during an unnoticed active LDAP burst → brief outage felt by users | The 30s API blip is not enough to break LDAP sessions (cached SA bind survives). Outpost continues serving cached binds. Worst case: a single user re-auth. |
| Container fails to come back up after recreate (image pull issue, volume problem) | Health check loop in `_authentik_perform_recreate` waits 90s and reports failure to settings.json. Operator sees "last_run_outcome: failed" in dashboard. Spiral monitor still runs as fallback. |
| Operator on small/light box doesn't need this and finds the weekly blip annoying | "Disable auto-restart" toggle. Off-peak window (04:00 default) minimizes likelihood of being noticed. |
| Schedule races with `Update Now` (operator triggers update at 04:00) | Scheduler checks for deploy/update lockfile and skips. Update Now finishes its own restart anyway. |
| Two scheduler threads created somehow (module reloaded twice) | PID-checked lockfile (same pattern as spiral monitor). Reused, not invented. |
| Multiple boxes restart at exactly 04:00 across a fleet → support spike if something goes wrong | Fleet boxes are independent; no shared state. The window is 1 hour wide, so jitter naturally spreads them. Plus this is single-tenant per box anyway. |

---

## 2. Smaller Authentik-stability items (ride along)

These are scoped tightly. They ship alongside the auto-restart only if they don't slow down v0.8.7. Otherwise → v0.8.8 or v0.8.9.

### 2a. Node-RED: upstream-health-check pattern for WebSocket / mTLS flows

**Field evidence (tak-10, Apr 30 2026):** Tablet Command AVL feed showed no data after Node-RED container restart. Resolved when the operator logged into Node-RED through the Authentik proxy (warmed the upstream session). The flow itself was fine — its WebSocket connect had silently failed because the Authentik proxy session was cold while server CPU was pinned.

**Once item 1 (auto-restart) is in place, this should disappear**, because Authentik server CPU won't be pinned long enough for proxy sessions to go cold during a deploy. But for defense in depth:

- Add a 60s upstream health-check inject pattern to `nodered/build-flows.js` for flows with persistent upstream connections (DataSync, Tablet Command, Mission API).
- If health check fails, trigger a reconnect.
- Document the pattern in `nodered/README.md`.

Defer if it adds risk to the v0.8.7 ship. The auto-restart fix in item 1 is the upstream root cause, so item 2a is belt-and-suspenders.

### 2b. TAK Server webadmin admin-role final verifier

**Field evidence (tak-10, Apr 30 2026):** After "Resync LDAP webadmin", the TAK Server WebUI redirected webadmin to **WebTAK (operator UI)** instead of the **Admin Console**. A second "Resync LDAP webadmin" fixed it.

**Proposed:**
- Add a final verifier to the resync flow that confirms webadmin appears in `/opt/tak/UserAuthenticationFile.xml` with `role="ADMIN"` before reporting success.
- If missing, automatically run the admin-role apply step (idempotent).
- Log the verifier result to `settings.json → webadmin_admin_role_check`.

Small diff (~30 lines). Safe to include.

### 2c. Authentik deploy: wait for all containers healthy before API poll

Confirmed root cause of v0.8.6's deploy-on-Azure issue was the `elif needs_pg_update:` scope bug, not poll timing. But on very slow disk (< 100 MB/s), a health-gate loop before the API poll adds 0-5s on fast boxes and prevents edge-case races. Low risk.

Defer if it bloats the diff. Item 1 is the priority.

---

## 3. v0.8.7 acceptance criteria

- [ ] Periodic auto-restart fires once on tak-10 (force the schedule with a temporary `interval_hours: 0` to validate live).
- [ ] Before/after CPU evidence persisted to `settings.json → authentik_periodic_restart.last_run_evidence` and visible in the dashboard.
- [ ] LDAP outpost stays up across the entire restart window (zero outpost recursion markers in logs during the restart).
- [ ] Manual "Restart Authentik server now" button works from console with no SSH required.
- [ ] Schedule respects the `enabled: false` toggle (proven by setting it false and watching the monitor skip).
- [ ] Schedule respects the spiral gate (artificially trigger spiral detection once and confirm restart is skipped that cycle).
- [ ] Tested on at least two production boxes (tak-10 + ssdnodes) for a full week.
- [ ] No LDAP incidents during the test week. Spiral monitor still firing every 10 min as before.

---

## 4. Out of scope for v0.8.7 (moved to v0.8.8 or later)

These were considered but moved out to keep this release focused on Authentik stability:

- **Rollback feature** (one-click revert from console). → **v0.8.8 headline.** See `docs/PLAN-v0.8.8.md`.
- **Dashboard CPU per-core breakdown.** → v0.8.9 or later.
- **Speed test: read MB/s display.** → v0.8.9 or later (data still collected, just not rendered).
- **NSG ARM template advisory in start.sh.** → v0.8.9 or later.

---

## 5. Why ship v0.8.7 fast as Authentik-stability-only

Three reasons:

1. **The chronic pain is the one driving the operator nuts.** v0.8.5 fixed the acute crashes, but tak-10 still goes into "expensive and sluggish" mode every few hours. That's the felt-it-every-day problem. Fix it first.

2. **Auto-restart is the smallest possible change with the biggest possible win.** The mechanism is already field-validated (Apr 30 2026 on tak-10). It's ~150 lines of code: scheduler thread, recreate function, settings, one console button. Plus zero new dependencies. Plus rollback isn't a prerequisite for shipping it — the change is so isolated that even if it has an edge case, it's an in-place fix.

3. **Rollback can wait one release.** If v0.8.7's auto-restart has a rough edge, the worst case is the operator runs the existing manual `force-recreate` command. They already know how. Rollback would be nice-to-have, but it's not blocking Authentik peace of mind.

---

## 6. Notes from v0.8.6 post-release (kept for context)

- All four v0.8.6 fixes confirmed working on Azure tak-test-3 (D8as_v5, P10 64 GiB, ~145 MB/s).
- v0.8.5 production fleet (tak-10, ssdnodes, responder) is stable on acute health metrics (zero SIGABRT, zero recursion, zero idle-in-trans).
- Apr 30 2026: discovered the v0.8.5 fix protects against the *acute* failure but not the *chronic* state-drift symptom on heavy-load boxes. v0.8.7 closes that gap.
- v0.8.6 dev→main selective merge uses the pattern in `docs/COMMANDS.md`.
