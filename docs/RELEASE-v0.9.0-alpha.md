# v0.9.0-alpha Release Notes

## What ships

Two operator-facing features: custom identification banners and fail2ban brute-force IP blocking.

---

### Feature 1 — Custom Identification Banner

Operators managing multiple infra-TAK instances now have a persistent identity banner at the top of every page. It shows agency-provided free-form text centered between two logo marks, making it impossible to confuse which box you are on.

```
[ Agency Logo ]   REGION 5 OPS CENTER — ALPHA UNIT   [ Agency Logo ]
```

**How it works:**
- The banner is `position:fixed` at the top of every page and is injected via the shared context processor — no individual page templates touched.
- If no agency logo is uploaded, the infra-TAK text mark appears on both sides.
- Configured at `/customization` (new page in sidebar, between Marketplace and Help).

**New settings keys in `settings.json` (`customization` dict):**
- `banner_enabled` — bool
- `banner_text` — string, max 120 chars
- `agency_logo_b64` — base64 data URI (PNG/SVG/JPEG, max 512 KB), nullable

**New routes:**
- `GET /customization` — Customization page
- `GET /api/customization/settings` — read current config (no logo bytes)
- `POST /api/customization/settings` — save `banner_enabled` + `banner_text`
- `POST /api/customization/logo` — upload agency logo (multipart)
- `DELETE /api/customization/logo` — remove agency logo

---

### Feature 2 — Fail2ban Brute-Force Protection

Authentik login failures now trigger automatic IP bans via fail2ban + UFW. This is the host-level brute-force control that was explicitly parked in v0.8.9 pending the trusted-proxy CIDR prerequisite fix.

**Architecture:**
```
Browser → Caddy → Authentik → docker logs → log-forwarder → /var/log/authentik/auth.log
                                                                      ↓
                                                fail2ban filter (login_failed JSON) → ufw ban
```

**What the migration does (`_fail2ban_install_and_configure`):**
1. Guards: requires `authentik_trusted_proxy_cidrs_fix.last_outcome` ∈ `{applied, idempotent-noop}` — will NOT install if v0.8.9 prerequisite not confirmed. Skips silently on non-Authentik installs.
2. Installs `fail2ban` via `apt-get` (or `yum` on non-Debian).
3. Creates `/var/log/authentik/` directory.
4. Writes `/etc/systemd/system/authentik-log-forwarder.service` — tails `docker logs -f authentik-server-1` to the log file.
5. Writes `/etc/fail2ban/filter.d/authentik.conf` — regex matching `login_failed` JSON lines.
6. Writes `/etc/fail2ban/jail.d/infratak-authentik.conf` — default thresholds: 5 failures in 600s → 3600s ban, action: ufw.
7. Enables and starts both services.
8. Records `last_outcome: applied` to `settings.fail2ban_setup`.

**Idempotent:** re-running on an already-configured install is a sub-second no-op.

**Default thresholds (configurable in the UI):**
- `maxretry`: 5 failed logins
- `findtime`: 600 seconds (10-minute window)
- `bantime`: 3600 seconds (1 hour)

**New UI page (`/fail2ban`):**
- Appears in the sidebar between Firewall and Guard Dog (only shown when fail2ban is installed)
- **Stats** — currently banned, currently failed, session totals
- **Currently Banned IPs** — table with Unban button per IP
- **Jail Configuration** — maxretry/findtime/bantime inputs, Save & Reload
- **Activity Log** — last 100 authentik events from `/var/log/fail2ban.log`, auto-refreshes every 30s

**New routes:**
- `GET /fail2ban` — Fail2ban dashboard
- `GET /api/fail2ban/status` — jail status + banned IP list + log forwarder health
- `POST /api/fail2ban/config` — update thresholds + `fail2ban-client reload`
- `POST /api/fail2ban/unban` — `fail2ban-client set authentik unbanip <ip>` (validates IP format)
- `GET /api/fail2ban/log` — last 100 authentik lines from `/var/log/fail2ban.log`

---

## Changes shipped

### `app.py`

- **VERSION**: `0.8.9-alpha` → `0.9.0-alpha`
- **New `render_custom_banner(settings)`** — returns `position:fixed` banner HTML + style injection; empty string when disabled. Prepended to `sidebar_html` in the context processor — zero template changes.
- **Context processor extended** — calls `render_custom_banner()` and prepends result to `sidebar_html`.
- **New `render_sidebar()` entry** — Customization link after Marketplace; Fail2ban link between Firewall and Guard Dog (conditional on `/etc/fail2ban` existing).
- **New `_fail2ban_install_and_configure(plog)`** — idempotent migration, wired into `_startup_migrations` and `_post_update_auto_deploy` after the v0.8.9 block.
- **New customization routes** — `/customization`, `/api/customization/settings` (GET/POST), `/api/customization/logo` (POST/DELETE).
- **New fail2ban routes** — `/fail2ban`, `/api/fail2ban/status`, `/api/fail2ban/config`, `/api/fail2ban/unban`, `/api/fail2ban/log`.
- **New `CUSTOMIZATION_TEMPLATE`** — full-page template with banner preview, toggle, text input, logo upload/remove.
- **New `FAIL2BAN_TEMPLATE`** — security dashboard with stats, banned-IP table, config sliders, activity log.

---

## Operator acceptance checks

### Banner

```bash
# 1. Navigate to /customization, enable banner, set text, save
# 2. Reload any page — banner appears fixed at the top
# 3. Upload agency PNG — both sides update to agency logo
# 4. Verify settings
sudo cat /root/infra-TAK/.config/settings.json | python3 -c "
import json, sys; d = json.load(sys.stdin)
print('customization:', json.dumps(d.get('customization', {}), indent=2))"
```

Expected: `customization.banner_enabled: true`, `customization.banner_text: <your text>`

### Fail2ban

```bash
# 1. Confirm v0.8.9 prerequisite is met
sudo cat /root/infra-TAK/.config/settings.json | python3 -c "
import json, sys; d = json.load(sys.stdin)
print('proxy fix:', d.get('authentik_trusted_proxy_cidrs_fix', {}).get('last_outcome'))"

# 2. Confirm fail2ban migration outcome
sudo cat /root/infra-TAK/.config/settings.json | python3 -c "
import json, sys; d = json.load(sys.stdin)
print('fail2ban_setup:', json.dumps(d.get('fail2ban_setup', {}), indent=2))"

# 3. Confirm jail is active
sudo fail2ban-client status authentik

# 4. Confirm log forwarder is running
sudo systemctl status authentik-log-forwarder

# 5. Confirm auth.log is being populated
sudo tail -f /var/log/authentik/auth.log
```

Expected: `fail2ban_setup.last_outcome: "applied"`, jail status shows `authentik` jail enabled.

---

## What was explicitly NOT shipped

- **Authentik Reputation policy** — deferred to v0.9.1. fail2ban handles the immediate brute-force need at the host level. Reputation policy adds flow-level blocking within Authentik and requires blueprint diff + healing migration.
- **SSH fail2ban jail** — only Authentik login events in v0.9.0. SSH hardening is a separate planning item.
- **TAK Server rollback** — parked since v0.8.8, still deferred.
- **Node-RED flow changes** — not in scope.

---

## Cardinal rules upheld

- **Idempotent migrations.** Both `_fail2ban_install_and_configure` and the banner storage are safe to re-run; they no-op if already applied.
- **Prerequisite-gated.** fail2ban install is blocked if `authentik_trusted_proxy_cidrs_fix` is not confirmed. This prevents the v0.8.9 DoS scenario (banning `172.18.0.1`) on unpatched installs.
- **No template surgery.** Banner injection uses the existing context processor pattern — one change, all pages covered.
- **Audit trail in `settings.json`.** `fail2ban_setup` and `customization` keys record all config for every box.
