#!/usr/bin/env python3
"""
Sovereign infra-TAK Patcher (v3 - Compatible with v0.9.22-alpha)

- Refactored for Caddy-loopback architecture.
- Forces 'tls internal' and NetBird interface binding.
- Injects Frigate, n8n, WebODM, and NetBird Sovereign modules.
- Aligns with v0.9.22-alpha SHA256 anchors.
"""

import os
import sys
import hashlib
import argparse
import html

# ============ VERSION MAP ============
# app.py v0.9.22-alpha
VERSION_MAP = {
    "0.9.22-alpha": "eed1238e39f6a7789c9df282e8d15e8a6c3a68fdc094474d1fcec344e9b4ceb1"
}

# ============ STABLE ANCHORS ============
ANCHOR_CHECKS = [
    ('logo_block', 'AUTHENTIK_LOGO_URL =', 'Logo constant anchor'),
    ('globals_hook', 'guarddog_deploy_log = []', 'Global status anchor'),
    ('module_detect', "modules['nodered'] =", 'Module detection anchor'),
    ('sidebar_builder', "nr = modules.get('nodered', {})", 'Sidebar position anchor'),
    ('marketplace_template', "{% elif key == 'emailrelay' %}", 'Marketplace icon anchor'),
    ('service_domains', "SERVICE_DOMAIN_DEFAULTS = {", 'Service domain map anchor'),
    ('caddy_init', 'lines = [f"# infra-TAK - Auto-generated Caddyfile"', 'Caddyfile generation start'),
    ('caddy_finish', "caddyfile = '\\n'.join(lines)", 'Caddyfile generation end'),
    ('main_entry', '# === Main Entry Point (fallback', 'Route insertion anchor'),
]

# ============ MODULE CONFIGS ============
PATCHES = {
    'frigate': {
        'name': 'Frigate NVR',
        'desc': 'AI-powered NVR with object detection',
        'icon': 'videocam',
        'logo': 'https://frigate.video/img/logo.png',
        'route': '/frigate',
        'priority': 6.5,
        'dir': '~/frigate',
        'port': 5000
    },
    'n8n': {
        'name': 'n8n Tactical Automation',
        'desc': 'Flow-based AI automation & mission reporting',
        'icon': 'robot_2',
        'logo': 'https://raw.githubusercontent.com/n8n-io/n8n/master/assets/n8n-logo.png',
        'route': '/n8n-manage',
        'priority': 7,
        'dir': '~/n8n-tactical',
        'port': 5678
    },
    'webodm': {
        'name': 'WebODM Photogrammetry',
        'desc': 'Drone imagery processing & orthomosaics',
        'icon': 'map',
        'logo': 'https://raw.githubusercontent.com/OpenDroneMap/WebODM/master/webodm/static/img/logo.png',
        'route': '/webodm-manage',
        'priority': 8,
        'dir': '~/webodm',
        'port': 8000
    },
    'netbird': {
        'name': 'Sovereign NetBird',
        'desc': 'Self-hosted NetBird Management with Authentik OIDC',
        'icon': 'hub',
        'logo': None,
        'route': '/netbird-sovereign',
        'priority': 2.5,
        'dir': '~/netbird-sovereign',
        'port': None
    }
}

def find_line_end(content, pos):
    nl = content.find('\n', pos)
    return nl if nl != -1 else len(content)

def apply_patches(content, dry_run=False):
    msgs = []
    
    # 1. Logos
    for mod, cfg in PATCHES.items():
        const_name = f"{mod.upper()}_LOGO_URL"
        if cfg['logo'] and const_name not in content:
            pos = content.find('AUTHENTIK_LOGO_URL =')
            if pos != -1:
                end = find_line_end(content, pos)
                content = content[:end] + f'\n{const_name} = "{cfg["logo"]}"' + content[end:]
                msgs.append(f"[OK] Added {const_name}")

    # 2. Globals
    for mod in ['frigate', 'n8n', 'webodm']:
        status_var = f"{mod}_deploy_status"
        if status_var not in content:
            pos = content.find('guarddog_deploy_log = []')
            if pos != -1:
                end = find_line_end(content, pos)
                injection = f'\n{mod}_deploy_log = []\n{status_var} = {{"running": False, "complete": False, "error": False}}'
                content = content[:end] + injection + content[end:]
                msgs.append(f"[OK] Added globals for {mod}")

    # 3. Module Detection
    for mod, cfg in PATCHES.items():
        mkey = mod if mod != 'netbird' else 'netbird_sovereign'
        marker = f"modules['{mkey}'] ="
        if marker not in content:
            pos = content.find("modules['nodered'] =")
            if pos != -1:
                # Find start of nodered block to inject BEFORE it
                block_start = content.rfind('\n', 0, pos)
                logo_ref = f"{mod.upper()}_LOGO_URL" if cfg['logo'] else "None"
                
                detect_code = f'''
    # {cfg['name']}
    {mod}_dir = os.path.expanduser("{cfg['dir']}")
    {mod}_installed = os.path.exists({mod}_dir)
    {mod}_running = False
    if {mod}_installed:
        r = subprocess.run('docker ps --filter name={mod} --format "{{{{.Status}}}}" 2>/dev/null', shell=True, capture_output=True, text=True)
        {mod}_running = 'Up' in r.stdout
    modules['{mkey}'] = {{'name': '{cfg['name']}', 'installed': {mod}_installed, 'running': {mod}_running,
        'description': '{cfg['desc']}', 'icon': '{cfg['icon']}', 'icon_url': {logo_ref}, 'route': '{cfg['route']}', 'priority': {cfg['priority']}}}
'''
                content = content[:block_start] + detect_code + content[block_start:]
                msgs.append(f"[OK] Added detection for {cfg['name']}")

    # 4. Sidebar Builder
    sidebar_anchor = "    if nr.get('installed'):"
    if sidebar_anchor in content and "modules.get('frigate')" not in content:
        sidebar_patch = "    if nr.get('installed'):"
        sidebar_patch += f"\n        parts.append(link('/nodered', f'<img src=\"{{html.escape(NODERED_LOGO_URL)}}\" alt=\"\" class=\"nav-icon\" style=\"height:24px;width:auto;max-width:72px;object-fit:contain;display:block\"><span>Node-RED</span>'))"
        
        for mod, cfg in PATCHES.items():
            mkey = mod if mod != 'netbird' else 'netbird_sovereign'
            name_label = cfg['name'].replace('Sovereign ', '').replace(' Tactical Automation', '')
            if cfg['logo']:
                link_html = f"parts.append(link('{cfg['route']}', f'<img src=\"{{html.escape({mod.upper()}_LOGO_URL)}}\" alt=\"\" class=\"nav-icon\" style=\"height:24px;width:auto;max-width:72px;object-fit:contain;display:block\"><span>{name_label}</span>'))"
            else:
                link_html = f"parts.append(link('{cfg['route']}', '<span class=\"nav-icon material-symbols-outlined\">{cfg['icon']}</span><span>{name_label}</span>'))"
            
            sidebar_patch += f'''
    {mkey} = modules.get('{mkey}', {{}})
    if {mkey}.get('installed'):
        {link_html}'''
        
        # We need to replace the whole block starting from nr.get('installed') down to the link append
        old_block = "    if nr.get('installed'):\n        parts.append(link('/nodered', f'<img src=\"{html.escape(NODERED_LOGO_URL)}\" alt=\"\" class=\"nav-icon\" style=\"height:24px;width:auto;max-width:72px;object-fit:contain;display:block\"><span>Node-RED</span>'))"
        content = content.replace(old_block, sidebar_patch)
        msgs.append("[OK] Patched Sidebar builder")

    # 5. Marketplace Icons
    if "{% elif key == 'frigate' %}" not in content:
        icon_patch = ""
        for mod, cfg in PATCHES.items():
            mkey = mod if mod != 'netbird' else 'netbird_sovereign'
            icon_patch += f"{{% elif key == '{mkey}' %}}<span class=\"module-icon material-symbols-outlined\" style=\"font-size:28px\">{cfg['icon']}</span>"
        content = content.replace("{% elif key == 'emailrelay' %}", icon_patch + "{% elif key == 'emailrelay' %}")
        msgs.append("[OK] Patched Marketplace icons")

    # 6. SERVICE_DOMAIN_DEFAULTS
    if "'frigate': 'frigate'" not in content:
        domain_patch = ""
        for mod in ['frigate', 'n8n', 'webodm']:
            domain_patch += f"    '{mod}': '{mod}',\n"
        content = content.replace("SERVICE_DOMAIN_DEFAULTS = {", "SERVICE_DOMAIN_DEFAULTS = {\n" + domain_patch)
        msgs.append("[OK] Patched SERVICE_DOMAIN_DEFAULTS")

    # 7. Caddyfile Snippet (NetBird Services Gateway Mode)
    if "(mesh_tls)" not in content:
        caddy_snippet = f'''    lines = [
        f"# infra-TAK - NetBird Services Gateway Config",
        f"# Base Domain: {{domain}}",
        "{{",
        "    auto_https off",
        "    local_certs",
        "    skip_install_trust",
        "}}",
        "",
        "(mesh_tls) {{",
        "    bind 100.112.85.17",
        "}}",
        "",
        "# Global NetBird IP Entry",
        "http://100.112.85.17 {{",
        "    import mesh_tls",
        "    redir / /takportal/",
        "}}",
        ""
    ]'''
        # v0.9.22 has a hardcoded global block we need to replace entirely
        old_init = '    lines = [f"# infra-TAK - Auto-generated Caddyfile", f"# Base Domain: {domain}", ""]'
        content = content.replace(old_init, caddy_snippet)
        
        # Kill the email block that app.py adds later
        content = content.replace("lines.append(f\"        email {settings.get('email', 'admin@local.host')}\")", "pass # email suppressed")
        content = content.replace("lines.append(\"}\")", "pass # global closing suppressed", 1) 
        
        msgs.append("[OK] Switched to NetBird Services Gateway Mode (HTTP-only)")

    # 8. Caddyfile Site Block Imports (Regex for all blocks)
    import re
    # Force http:// prefix for all blocks
    gen_start = content.find('def generate_caddyfile')
    gen_end = content.find('def ', gen_start + 1)
    if gen_start != -1 and gen_end != -1:
        gen_section = content[gen_start:gen_end]
        new_gen_section = []
        for line in gen_section.split('\n'):
            # Convert lines.append(f"{host} {") to lines.append(f"http://{host} {")
            if 'lines.append(f"' in line and '{' in line and 'http://' not in line:
                if line.strip().endswith('{"') or line.strip().endswith('{{")'):
                    line = line.replace('lines.append(f"', 'lines.append(f"http://')
            
            new_gen_section.append(line)
            # Add mesh_tls import (which now only contains the bind directive)
            if 'lines.append(f"http://' in line and 'import mesh_tls' not in line:
                indent = line[:line.find('lines.append')]
                new_gen_section.append(f'{indent}lines.append("    import mesh_tls")')
        
        content = content[:gen_start] + '\n'.join(new_gen_section) + content[gen_end:]
        
        # Explicitly patch hardcoded aliases
        content = content.replace('lines.append(f"authentik.{fqdn_base} {{")', 'lines.append(f"http://authentik.{fqdn_base} {{")\n            lines.append("    import mesh_tls")')
        content = content.replace('lines.append(f"{ct_video} {{")', 'lines.append(f"http://{ct_video} {{")\n        lines.append("    import mesh_tls")')
        
        msgs.append("[OK] Forced http:// prefix and mesh_tls binding")

    # 9. Custom Caddy Site Blocks (at the end of generate_caddyfile)
    if "# Sovereign Custom Site Blocks" not in content:
        custom_caddy = "\n    # Sovereign Custom Site Blocks\n"
        for mod in ['frigate', 'n8n', 'webodm']:
            cfg = PATCHES[mod]
            custom_caddy += f'''
    {mod} = modules.get('{mod}', {{}})
    if {mod}.get('installed'):
        {mod}_host = sd.get('{mod}', f"{mod}.{{domain}}")
        lines.append(f"{{{mod}_host}} {{{{")
        lines.append("    import mesh_tls")
        lines.append("    reverse_proxy 127.0.0.1:{cfg['port']}")
        lines.append("}}}}")
        lines.append("")
'''
        # New: Replace 127.0.0.1 with server_ip for NetBird alignment
        replacement_logic = """
    caddyfile = '\\n'.join(lines)
    # Sovereign NetBird Alignment: Replace loopback with server_ip for containers bound to wt0
    server_ip = settings.get('server_ip')
    if server_ip:
        caddyfile = caddyfile.replace('127.0.0.1:', f'{server_ip}:')
"""
        content = content.replace("caddyfile = '\\n'.join(lines)", custom_caddy + replacement_logic)
        msgs.append("[OK] Added custom service blocks and NetBird IP alignment")

    # 10. Templates & Routes
    if 'FRIGATE_TEMPLATE' not in content:
        routes_code = "\n# === Sovereign Modules Routes ===\n"
        for mod, cfg in PATCHES.items():
            if mod == 'netbird': continue
            routes_code += f'''
{mod.upper()}_TEMPLATE = \'\'\'<!DOCTYPE html><html><head><title>{cfg['name']}</title><style>{{{{ BASE_CSS }}}}</style></head>
<body>{{{{ sidebar_html | safe }}}}<div class="main"><h1>{cfg['name']}</h1><p>{cfg['desc']}</p>
<div class="card"><a href="https://{mod}.{{{{ settings.get('fqdn') }}}}" class="btn btn-primary" target="_blank">Open {cfg['name']}</a></div>
</div></body></html>\'\'\'

@app.route('{cfg['route']}')
@login_required
def {mod}_page():
    settings = load_settings()
    modules = detect_modules()
    sidebar_html = render_sidebar(modules, '{mod}')
    return render_template_string({mod.upper()}_TEMPLATE, settings=settings, sidebar_html=sidebar_html, BASE_CSS=BASE_CSS)
'''
        content = content.replace('# === Main Entry Point (fallback', routes_code + '\n# === Main Entry Point (fallback')
        msgs.append("[OK] Added Routes and Templates")

    return content, msgs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', default='/home/sauron/infra-TAK/app.py')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.app):
        print(f"Error: {args.app} not found")
        return

    with open(args.app, 'r') as f:
        content = f.read()

    sha = hashlib.sha256(content.encode()).hexdigest()
    print(f"Current SHA: {sha}")
    
    # Anchor Check
    print("\n--- Anchor Check ---")
    all_ok = True
    for name, search, desc in ANCHOR_CHECKS:
        if search in content:
            print(f"  [OK] {name}")
        else:
            print(f"  [!!] {name} NOT FOUND ({search})")
            all_ok = False
    
    if not all_ok:
        print("\nAborting: Not all anchors found. Upstream has changed too much.")
        return

    new_content, msgs = apply_patches(content, args.dry_run)
    for m in msgs:
        print(m)

    if not args.dry_run and new_content != content:
        # Create backup
        import shutil
        shutil.copy2(args.app, args.app + '.bak')
        
        with open(args.app, 'w') as f:
            f.write(new_content)
        print("\nPatches applied successfully. Backup created.")
    else:
        print("\nDry run complete. No changes made.")

if __name__ == '__main__':
    main()
