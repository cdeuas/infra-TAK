# infra-TAK Project Status & Logbook

## 📍 Current State (15 May 2026)
- **Version**: infra-TAK **v0.9.22-alpha** (Upgraded from v0.9.11).
- **Architecture**: Project ARES (100% Offline MANET).
- **Networking**: NetBird Mesh Dual-Peer setup. Host (Sauron) and VM (ARES) are separate peers.
- **DNS**: Localized `dnsmasq` nameserver on VM resolving `*.ares.local` to `100.112.85.17`.
- **Proxy**: Caddy v0.9.22 patched for HTTP-only Gateway mode on port 80 (No public ACME).
- **Identity**: Authentik re-aligned to `http://tak.ares.local`.

## 📝 Recent Changes (Logbook)

### 15 May 2026: The v0.9.22 Upgrade & Project ARES Pivot
- **Major Upgrade**: Migrated from v0.9.11-alpha to v0.9.22-alpha.
- **Patch Engine v3**: Developed `patch_modules_v3.py` to handle 2MB+ `app.py` with 9 stable anchors.
- **Architectural Shift**: Reverted public cloud-proxy migration in favor of strict internal `ares.local` domain.
- **DNS Deployment**: Deployed `dnsmasq` on VM mesh interface to provide wildcard resolution for NetBird clients.
- **TLS Hardening**: Disabled Caddy auto-HTTPS and OCSP stapling to prevent handshake errors on the offline mesh.
- **Authentik**: Re-configured all Proxy Providers and Environment variables for the new canonical `ares.local` domain.
- **Validation**: Verified end-to-end connectivity: `takportal.ares.local` (200 OK) over encrypted WireGuard tunnel.

## 🛠 Next Tasks
1. **Edge AI Vision**: Integrate specialized models for DJI M4T and tactical UAS.
2. **Geospatial Pipeline**: finalize WebODM processing offload to Sauron GPU.
3. **Guard Dog**: Audit real-time telemetry for the new Redis task-broker.

## 🌐 Connectivity Details (ARES.local)
- **NetBird IP (VM)**: `100.112.85.17`
- **Nameserver**: `100.112.85.17:53`
- **Dashboard**: `http://takportal.ares.local`
- **Authentik**: `http://tak.ares.local`
- **Frigate**: `http://frigate.ares.local`
- **n8n**: `http://n8n.ares.local`
