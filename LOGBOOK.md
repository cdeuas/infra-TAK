# infra-TAK Project Status & Logbook

## 📍 Current State (1 May 2026)
- **Version**: infra-TAK **v0.8.8-alpha** (Upgraded from v0.5.9).
- **Architecture**: Zero-Trust Tactical VM on Sauron Host.
- **Security**: NetBird Mesh strictly bound to `wt0`; `tls internal` enabled.
- **Database**: Postgres tuned with `idle_in_transaction_session_timeout=300s` for stability.
- **Identity**: Authentik LDAP flow recursion fixed; performance tuned (4 workers, 600s cache).
- **Marketplace**: Frigate NVR integrated with customized UI and CoT alerts.

## 📝 Recent Changes (Logbook)
- **Upgrade**: Successfully upgraded core stack to **v0.8.8-alpha**. 
- **Migration**: Applied automated Postgres and LDAP stability fixes.
- **Customization**: Re-applied and verified Frigate NVR UI patches and Material Symbol integrations.
- **Validation**: Confirmed AI Bridge (Ollama) and NetBird Mesh connectivity post-upgrade.
- **Performance**: Console transitioned to Gunicorn with hardened security headers.

## 🛠 Next Tasks
1. **Automation**: Begin integration of n8n and link to Ollama API.
2. **Geospatial**: Setup WebODM frontend and GeoServer integration.
3. **Compute Offload**: Configure WebODM to use host GPU for processing.

## 🌐 Connectivity Details
- **NetBird IP (VM)**: `100.112.85.17`
- **NetBird IP (Host)**: `100.112.249.186`
- **Dashboard**: `https://100.112.85.17`
- **Authentik**: `https://100.112.85.17:9443` (Direct) or via Caddy.
