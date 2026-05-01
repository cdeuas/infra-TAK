import os
import sys

# Targeting the core app.py
app_path = '/home/sauron/infra-TAK/app.py'
if not os.path.exists(app_path):
    app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r') as f:
    content = f.read()

# 1. Add n8n Module Detection
n8n_detect = """
    # n8n Tactical Automation
    n8n_dir = os.path.expanduser("~/n8n-tactical")
    n8n_installed = os.path.exists(os.path.join(n8n_dir, "docker-compose.yml"))
    n8n_running = False
    if n8n_installed:
        r = subprocess.run('docker ps --filter name=n8n-tactical --format "{{.Status}}" 2>/dev/null', shell=True, capture_output=True, text=True)
        n8n_running = 'Up' in r.stdout
    modules['n8n'] = {'name': 'n8n Automation', 'installed': n8n_installed, 'running': n8n_running,
        'description': 'Flow-based AI automation & mission reporting', 'icon': '🤖', 'route': '/n8n', 'priority': 7}
"""

# Find a safe place to inject detection (before Node-RED or after Frigate)
if "modules['nodered']" in content and "modules['n8n']" not in content:
    content = content.replace("modules['nodered'] = {", n8n_detect + "    modules['nodered'] = {")

# 2. Add Sidebar Link
sidebar_hook = "    nr = modules.get('nodered', {})"
n8n_sidebar = """    n8n = modules.get('n8n', {})
    if n8n.get('installed'):
        parts.append(link('/n8n', '<span class="nav-icon material-symbols-outlined">auto_settings</span><span>n8n AI</span>'))
"""
if sidebar_hook in content and "n8n" not in content:
    content = content.replace(sidebar_hook, n8n_sidebar + sidebar_hook)

with open(app_path, 'w') as f:
    f.write(content)
print("n8n automation patches applied to app.py")
