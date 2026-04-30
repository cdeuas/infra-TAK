# v0.8.8-alpha — Work Plan

**Headline (and primary) feature: Rollback**

The ability to revert to the previous working version of infra-TAK from the console, without SSH. Operator safety net. Originally planned for v0.8.7 but **deferred one release** so v0.8.7 could focus exclusively on Authentik stability (the more pressing field pain). Now that v0.8.7 has Authentik humming, rollback is the next-most-valuable operator feature.

> **Prerequisite:** v0.8.7 (Authentik periodic auto-restart) shipped and validated on tak-10 + ssdnodes for at least one full week with zero LDAP incidents and confirmed before/after CPU evidence captured.

---

## 1. Rollback (the primary feature)

### Problem

Today's Update Now is one-directional. It runs `git fetch && git checkout --force origin/main` and restarts the console. If the new version has a regression (bad Authentik deploy, broken UI, startup crash), the operator has no recovery path from the console — they must SSH in, find the previous commit hash, and manually `git checkout <hash>` + restart. Non-technical operators on production boxes cannot do this, and experienced operators shouldn't have to.

This was uncomfortable through v0.8.5/v0.8.6/v0.8.7. With v0.8.7's auto-restart in place, future regressions are statistically less likely to be Authentik-related — but they can still come from any other code path (UI, deploy scripts, dashboard, Node-RED build, etc.). Rollback is the universal safety net.

### Design goals

1. **One-click rollback from the console** — clearly labeled "Rollback to v0.8.x-alpha" button that undoes the last update.
2. **Before any update, snapshot the current state** — at minimum the current git commit hash, so rollback always knows where to go back to.
3. **Safe and idempotent** — rollback runs the same start-up path as a normal install (no special teardown). Services end up in the same state as a clean install of the previous version.
4. **Minimal footprint** — store the rollback snapshot in `settings.json` (already used for migration forensics). No new daemon, no new files.

### Implementation

#### Pre-update snapshot (in `_run_update_now()`)

Before `git fetch + force-checkout`, record the current state in `settings.json`:

```json
{
  "rollback_snapshot": {
    "ts": 1777500000,
    "version": "0.8.7-alpha",
    "git_commit": "abc1234",
    "git_branch": "main"
  }
}
```

#### Rollback function (`_run_rollback()`)

1. Read `settings.json → rollback_snapshot`.
2. If no snapshot or snapshot is the current commit → surface "No rollback available" message.
3. Run `git checkout <git_commit> -- .` (checkout specific commit, not a branch).
4. Restart the console service (same as Update Now finish).
5. Clear the snapshot after rollback (avoid rollback-of-rollback confusion).

#### Console UI

- Under "Update Now" button: small secondary button **"Rollback to v0.8.7-alpha"** (only visible if a snapshot exists and differs from current version).
- Confirmation modal: "This will revert infra-TAK to v0.8.7-alpha (commit abc1234). Continue?"
- Progress feedback identical to Update Now.

### Scope / boundaries

- **Code rollback only.** No config backup/restore in v0.8.8 (that's a separate feature for a future release if needed).
- Rollback does NOT re-run migrations or undeploy Authentik — it only reverts the `app.py` code. If the bad version touched `~/authentik/docker-compose.yml`, the operator may still need a manual fix. Document this limitation clearly in the UI.
- No rollback chain (rollback of rollback). One level deep. Simple and safe.

### Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| git detached-HEAD confusion | After rollback, branch is detached at the commit. "Update Now" re-attaches to `origin/main`. Document this. |
| Snapshot gets stale (multiple updates without rollback use) | Overwrite snapshot on every update. Only one level of rollback supported. |
| Console restart mid-rollback | Same risk as Update Now. systemd restarts the service automatically. Rollback is idempotent. |
| Version banner shows wrong version in detached state | Read `VERSION` from `app.py` after checkout, not from git. Already how it works. |
| Rollback past v0.8.7's auto-restart settings → back to v0.8.6 chronic pain | Document. Operators rolling back to pre-v0.8.7 should expect the heavy-box CPU drift to return. Suggested workflow: rollback only when actively recovering from a regression, then return to current main once fixed. |

---

## 2. v0.8.8 acceptance criteria

- [ ] "Rollback to v0.8.7-alpha" (or current previous version) button appears in console after an update is applied.
- [ ] Clicking rollback returns `app.py` to the previous version (verified by `grep '^VERSION'`).
- [ ] Confirmation modal shows previous version string and commit hash.
- [ ] After rollback, Update Now works normally and returns to current main.
- [ ] If no snapshot exists, the rollback button is hidden (not just greyed out).
- [ ] Snapshot survives a console restart (stored in `settings.json`, not in-memory).
- [ ] Tested on Azure (tak-test-3) — rollback from a dummy v0.8.8 bump back to v0.8.7.
- [ ] Tested on tak-10 (production-like load) — rollback completes cleanly without disturbing Authentik or LDAP outpost.

---

## 3. Smaller items that may ride along (only if zero risk)

These are pre-existing minor items. Include only if they're trivial and don't slow down rollback shipping. **Anything that needs more than a 30-line diff defers to v0.8.9.**

### 3a. Speed test: restore read MB/s display

The manual disk speed test computes both read and write but the current display only shows write. Read was accidentally dropped in v0.8.6. Show both:

```
Disk speed test (256 MiB):  210 MB/s write  /  1331 MB/s read
```

~5 line change. Safe.

### 3b. NSG ARM template — integrate into `start.sh` advisory

`docs/azure-nsg-infra-tak.json` exists but is not linked from `start.sh` output. When `start.sh` detects an Azure environment (public IP ≠ private IP), print a one-line advisory:

```
Azure detected — ensure NSG allows: 443, 5001, 8089, 8443, 8446
See docs/azure-nsg-infra-tak.json for the ARM template.
```

~10 line change. Safe.

---

## 4. Out of scope for v0.8.8

- **Config backup/restore** (Caddy / CoreConfig.xml / UserAuthenticationFile.xml snapshots). → v0.8.9 or v0.9.0 if there's enough demand. Until then, "Restart Authentik server now" + the existing manual restore paths cover most "bad save" scenarios.
- **Dashboard CPU per-core breakdown.** → v0.8.9 or later.
- **Authentik deploy: wait for all containers healthy before API poll.** → v0.8.9 or later (low risk, low priority).

---

## 5. Why rollback shipped second instead of first

The earlier draft of v0.8.7 had rollback as the headline. We moved it to v0.8.8 because:

1. **Operator stability comes before operator safety nets.** Authentik-CPU-pinning was an everyday felt-pain on heavy-load boxes (tak-10). Rollback is a "when something goes wrong" feature. Fix the everyday pain first.

2. **v0.8.7 (Authentik) was a smaller, more isolated change** with strong field validation already done (Apr 30 2026 on tak-10). Rollback touches the update path, the UI, and `settings.json` schema — bigger surface area, more validation needed. Better to ship the smaller, validated fix first.

3. **v0.8.7 reduces the *need* for rollback.** Many of the "bad update" scenarios that rollback would protect against were Authentik-flavored (acute spiral, chronic CPU drift). v0.8.5/6/7 progressively close those holes. The remaining regression risk is non-Authentik (UI, deploy scripts, Node-RED) — still valuable to cover with rollback, just less acute.

4. **One major feature per release.** Mixing rollback + Authentik auto-restart in a single release would dilute both. Each gets a clean release with focused validation.

---

## 6. Notes from v0.8.7 post-release (placeholder)

To be filled in after v0.8.7 ships and is validated on the production fleet. Expected entries:

- Auto-restart fired N times across {tak-10, ssdnodes, responder} during the first week.
- Average before/after CPU p50 drop measured at: server X% → Y%, postgres X% → Y%.
- Zero LDAP incidents during/after restart windows.
- Operator feedback on the dashboard "Last restart / Next scheduled" UX.
- Any rough edges discovered → folded into v0.8.8 if low-risk, otherwise tracked as v0.8.9 hardening.
