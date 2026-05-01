import os
import sys

# Targeting the core app.py
app_path = '/home/sauron/infra-TAK/app.py'
if not os.path.exists(app_path):
    app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r') as f:
    content = f.read()

# 1. Add NetBird Sovereign Module Detection
# This pattern adds NetBird to the modules list without overwriting others
netbird_detect = """
    # Sovereign NetBird
    netbird_dir = os.path.expanduser("~/netbird-sovereign")
    netbird_installed = os.path.exists(os.path.join(netbird_dir, "docker-compose.yml"))
    netbird_running = False
    if netbird_installed:
        r = subprocess.run('docker ps --filter name=netbird-management --format "{{.Status}}" 2>/dev/null', shell=True, capture_output=True, text=True)
        netbird_running = 'Up' in r.stdout
    modules['netbird_sovereign'] = {'name': 'Sovereign NetBird', 'installed': netbird_installed, 'running': netbird_running,
        'description': 'Self-hosted NetBird Management with Authentik OIDC', 'icon': '🕸️', 'route': '/netbird-sovereign', 'priority': 2.5}
"""

# Find a safe place to inject detection (after Authentik detection)
if "modules['authentik']" in content and "modules['netbird_sovereign']" not in content:
    content = content.replace("modules['authentik'] = {", netbird_detect + "    modules['authentik'] = {")

# 2. Add Sidebar Link
sidebar_hook = "    authentik = modules.get('authentik', {})"
netbird_sidebar = """    netbird_sovereign = modules.get('netbird_sovereign', {})
    if netbird_sovereign.get('installed'):
        parts.append(link('/netbird-sovereign', '<span class="nav-icon material-symbols-outlined">hub</span><span>NetBird Local</span>'))
"""
if sidebar_hook in content and "netbird_sovereign" not in content:
    content = content.replace(sidebar_hook, netbird_sidebar + sidebar_hook)

with open(app_path, 'w') as f:
    f.write(content)
print("Sovereign NetBird patches applied to app.py")
