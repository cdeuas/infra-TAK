# Project ARES - infra-TAK Offline MANET Guide

This repository contains the Sovereign patches and documentation for the infra-TAK deployment on the Sauron AI Node.

## 🚀 Current Architecture
- **Host**: Sauron (AI/GPU Compute)
- **Guest**: Tactical-VM (C5ISR Stack)
- **Networking**: NetBird Zero-Trust Mesh
- **Domain**: `ares.local` (Offline resolution)

## 🛠 Deployment Workflow
This project follows a **Patch-First** strategy to remain compatible with upstream `takwerx/infra-TAK`.

1. **Sync**: `git pull origin main` (on the VM).
2. **Patch**: `python3 patch_modules_v3.py` (Applies tactical customizations).
3. **Deploy**: `sudo ~/infra-TAK/start.sh`

## 🌐 Local DNS Resolution
The VM runs a mesh-native `dnsmasq` instance on `100.112.85.17:53`. 
To enable resolution on your device:
1. Connect to NetBird.
2. NetBird will automatically use the VM as Nameserver for the `ares.local` domain.
3. Access services via: `http://takportal.ares.local`

## 📂 Custom Modules
- **Frigate NVR**: AI Object detection.
- **n8n**: Tactical automation.
- **WebODM**: Drone imagery processing.
- **Authentik**: Identity management & Proxy protection.
