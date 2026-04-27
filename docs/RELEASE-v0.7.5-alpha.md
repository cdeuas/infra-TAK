# v0.7.5-alpha Release Notes

---

## ⚠️ Action Required: Resync LDAP to TAK Server

If you haven't already done this, **do it now.**

Go to **TAK Server page → Resync LDAP to TAK Server**.

This fixes password changes taking up to 24 hours to propagate to ATAK/iTAK devices. After Resync, new passwords take effect within 2 minutes. Applies to every existing deployment.

---

## Bug Fixes

### CloudTAK overlays and tiles fail with CORS error (duplicate `Access-Control-Allow-Origin`)

**Symptom:** KMZ overlays, PMTiles overlays, and any file displayed as a map layer fail to render in CloudTAK with "Website Error — Failed to fetch." Browser DevTools shows every tile request to `tiles.<domain>` as a CORS error despite the server returning HTTP 200.

**Root cause:** The generated Caddyfile included `header Access-Control-Allow-Origin *` on the `tiles.<domain>` and `video.<domain>` stanzas. Both the CloudTAK tile server (nginx) and MediaMTX already set this header themselves. Caddy added a second copy, producing `Access-Control-Allow-Origin: *, *` — two values — which browsers reject per the CORS spec.

**Fix:** Removed the three `header Access-Control-Allow-Origin *` directives from the Caddyfile template. Both backends supply the header themselves.

After updating, go to **Caddy SSL → Domains → Save & Reload Caddy** to regenerate your Caddyfile and pick up the fix.

| File | Change |
|------|--------|
| `app.py` | Removed `header Access-Control-Allow-Origin *` from `tiles.<domain>` and `video.<domain>` Caddyfile stanzas |
