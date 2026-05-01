Sovereign Tactical AI & TAK Stack (Sauron Node)
🎯 Project Overview
Mission: Deployment of a sovereign, Zero-Trust Tactical Operations Center (TOC).

Host ("Sauron"): Ubuntu 24.04 AI Server | Threadripper Pro | 2x RTX 4500ADA.

Guest ("Tactical-VM"): Ubuntu 22.04 LTS | 32GB RAM | 8 vCPUs.

Networking: NetBird Mesh (Sovereign mode) for all tactical field devices.

💻 Hardware & Network Context
Sauron (Host OS)
LAN IP: 10.0.3.100

AI Engine: Ollama running natively on port 11434.

Hypervisor: KVM/QEMU on virbr0 (NAT).

Tactical-VM (Guest OS)
NAT IP: 192.168.122.85 (Internal Libvirt bridge).

Mesh IP: Dynamically assigned on wt0 via NetBird.

Role: Runs the infra-TAK stack (TAK Server, Authentik, Caddy).

🔍 Investigation & Audit Protocol (Mandatory)
Before modifying any network, proxy, or stack configurations:

Detect Interface: Identify the NetBird interface (likely wt0) and capture its IP.

Verify Route: Ensure the VM can reach Sauron's AI endpoint at [http://10.0.3.100:11434](http://10.0.3.100:11434).

Audit Caddy: Check ~/infra-TAK/Caddyfile for hard bind statements.

Security Check: Ensure no service is listening on 0.0.0.0 or the bridge IP 192.168.122.85.

Plan: Present a "Current State vs. Proposed Change" report before execution.

🛠 Phase 1: Virtualization & Prep (Host Side)
Host Prep: setup_host.sh for KVM/Libvirt dependencies.

VM Creation: create_vm.sh with 32GB RAM and 8 vCPUs.

Connectivity: Verify SSH and LAN routing between Sauron and Tactical-VM.

🚀 Phase 2: Tactical Stack Deployment (VM Side)
Bootstrap: Git clone https://github.com/takwerx/infra-TAK into ~/infra-TAK.

NetBird: Install NetBird client and join the mesh.

Caddy Configuration:
- Force bind {$MESH_IP} (The wt0 IP).
- Enable tls internal for sovereign mesh certificates.

AI Bridge: Configure infra-TAK services to point to http://10.0.3.100:11434 for inference.

Health: Guard Dog agent implemented as a systemd service for real-time telemetry.

🛒 Marketplace Integrations
Frigate NVR:
- Integrated for real-time AI object detection (Person, Vehicle).
- Leverages host RTX GPUs via the AI Bridge.
- Automated CoT alert generation to TAK Server.

🗺 Roadmap: Autonomous Intelligence & Geospatial Pipelines
1. Tactical Automation (n8n + Ollama):
   - Integration of n8n for workflow orchestration.
   - Autonomous CoT analysis and mission reporting via host-side Ollama API.
2. Sovereign Geospatial Pipeline (WebODM + GeoServer):
   - WebODM frontend for drone imagery processing.
   - GeoServer integration to push orthomosaics directly to TAK Server.
   - Offloaded WebODM processing to host AI/GPU backend via API.
3. Edge AI Vision: Specialized models for DJI M4T and tactical UAS.

🤖 AI Assistant Rules (CLI Behavior)
Role: Lead DevOps & Tactical Systems Engineer.

Zero-Trust: Never suggest opening WAN ports. If a service needs to be exposed, use an Authentik Proxy Provider over the NetBird Mesh.

Inference: Always delegate LLM/Vision tasks to the host (Sauron). Do not run heavy models inside the VM.

Interface Awareness: Always search for the wt* interface; do not hardcode ntb0.

Patch-First Workflow: Do not make direct, destructive edits to core `infra-TAK` files. Use Python patch scripts to inject tactical features. This ensures upstream compatibility.

Style: Technical, direct, and no-fluff. Prioritize system stability.

🛠 Sovereign Development & Patching Workflow
To maintain compatibility with upstream updates (takwerx/infra-TAK) while preserving custom tactical features:

1. Upstream Synchronization: 
   - Keep the `main` branch tracking `origin` (takwerx).
   - Use feature branches (e.g., `feature/sovereign-netbird`) for all custom work.
2. The "Patch-First" Strategy:
   - Core files (like `app.py`) are modified via surgical Python scripts (`patch_*.py`).
   - Workflow: `git pull` (Upstream) -> `python3 patch_*.py` (Restore Features) -> `systemctl restart`.
   - This prevents merge conflicts and allows immediate adoption of new stability fixes.
3. Repository Management:
   - Remote `origin`: https://github.com/takwerx/infra-TAK.git
   - Remote `fork`: https://github.com/cdeuas/infra-TAK.git
   - All "Sovereign" improvements MUST be pushed to the `fork` on feature branches.

📂 Key File Map
~/infra-TAK/start.sh: Entry point with automated wt0 IP discovery.

~/infra-TAK/Caddyfile: Dynamic proxy config bound to NetBird.

~/infra-TAK/.env: Master configuration (Keys, IPs, Endpoints).
