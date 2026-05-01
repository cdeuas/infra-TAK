import os
import html

# Use absolute path to avoid ~/ expansion issues with sudo
app_path = '/home/sauron/infra-TAK/app.py'
if not os.path.exists(app_path):
    # Fallback to current directory
    app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r') as f:
    content = f.read()

# Constants
old_const = 'AUTHENTIK_LOGO_URL = "https://raw.githubusercontent.com/goauthentik/authentik/main/web/icons/icon_left_brand.png"'
if old_const in content and 'FRIGATE_LOGO_URL' not in content:
    content = content.replace(old_const, old_const + '\nFRIGATE_LOGO_URL = "https://frigate.video/img/logo.png"')

# Globals
old_globals = 'authentik_deploy_log = []'
if old_globals in content and 'frigate_deploy_log' not in content:
    content = content.replace(old_globals, old_globals + '\nfrigate_deploy_log = []\nfrigate_deploy_status = {"running": False, "complete": False, "error": False}')

# Detection
old_detect = """    modules['nodered'] = {'name': 'Node-RED', 'installed': nodered_installed, 'running': nodered_running,
        'description': 'Flow-based automation & integrations', 'icon': '🔴', 'icon_url': NODERED_LOGO_URL_2, 'route': '/nodered', 'priority': 6}"""

if old_detect in content and "'frigate'" not in content:
    new_detect = old_detect + """
    # Frigate NVR
    frigate_installed = os.path.exists(os.path.expanduser("~/frigate/docker-compose.yml"))
    frigate_running = False
    if frigate_installed:
        r = subprocess.run('docker ps --filter name=frigate --format "{{.Status}}" 2>/dev/null', shell=True, capture_output=True, text=True)
        frigate_running = 'Up' in r.stdout
    modules['frigate'] = {'name': 'Frigate NVR', 'installed': frigate_installed, 'running': frigate_running,
        'description': 'AI-powered NVR with object detection', 'icon': '📹', 'icon_url': FRIGATE_LOGO_URL, 'route': '/frigate', 'priority': 6.5}"""
    content = content.replace(old_detect, new_detect)

# Sidebar
old_sidebar = """    nr = modules.get('nodered', {})
    if nr.get('installed'):
        parts.append(link('/nodered', f'<img src="{html.escape(NODERED_LOGO_URL)}" alt="" class="nav-icon" style="height:24px;width:auto;max-width:72px;object-fit:contain;display:block"><span>Node-RED</span>'))
    email = modules.get('emailrelay', {})"""

if old_sidebar in content and "'/frigate'" not in content:
    new_sidebar = """    nr = modules.get('nodered', {})
    if nr.get('installed'):
        parts.append(link('/nodered', f'<img src="{html.escape(NODERED_LOGO_URL)}" alt="" class="nav-icon" style="height:24px;width:auto;max-width:72px;object-fit:contain;display:block"><span>Node-RED</span>'))
    frigate = modules.get('frigate', {})
    if frigate.get('installed'):
        parts.append(link('/frigate', f'<img src="{html.escape(FRIGATE_LOGO_URL)}" alt="" class="nav-icon" style="height:24px;width:auto;max-width:72px;object-fit:contain;display:block"><span>Frigate</span>'))
    email = modules.get('emailrelay', {})"""
    content = content.replace(old_sidebar, new_sidebar)

# Template and routes
if 'FRIGATE_TEMPLATE' not in content:
    insertion_point = "# === Main Entry Point"
    frigate_code = '''
# === Frigate NVR Module ===
FRIGATE_TEMPLATE = \'\'\'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Frigate NVR — infra-TAK</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
<style>\'\'\' + BASE_CSS + \'\'\'
.log-box{background:#070a12;border:1px solid var(--border);border-radius:8px;padding:16px;font-family:\\\'JetBrains Mono\\\',monospace;font-size:11px;color:var(--text-dim);max-height:340px;overflow-y:auto;white-space:pre-wrap}
</style></head>
<body>
{{ sidebar_html }}
<div class="main">
  <div class="page-header"><h1 style="display:flex;flex-direction:column;align-items:flex-start;gap:6px"><img src="{{ frigate_logo_url }}" alt="" style="height:32px;width:auto;object-fit:contain"><span>Frigate NVR</span></h1><p>AI-powered NVR with object detection</p></div>
  {% if frigate.running %}<div class="status-banner running"><div class="dot"></div>Frigate is running</div>
  {% elif frigate.installed %}<div class="status-banner stopped"><div class="dot"></div>Frigate is installed but stopped</div>
  {% else %}<div class="status-banner not-installed"><div class="dot"></div>Frigate is not installed</div>{% endif %}
  
  {% if not frigate.installed %}
  <div class="card">
    <div class="card-title">Deploy Frigate NVR</div>
    <p style="font-size:13px;color:var(--text-secondary);margin-bottom:20px">Deploy Frigate as a Docker container to monitor your video streams with AI detection.</p>
    <div class="controls">
      <button class="btn btn-primary" id="deploy-btn" onclick="deployFrigate()">Deploy Frigate</button>
    </div>
    <div id="deploy-log-container" style="display:none;margin-top:20px">
      <div class="section-title">Deployment Log</div>
      <div class="log-box" id="deploy-log"></div>
    </div>
  </div>
  {% else %}
  <div class="card">
    <div class="card-title">Frigate Controls</div>
    <div class="controls">
      <a href="http://{{ settings.get(\\\'server_ip\\\', \\\'localhost\\\') }}:5000" target="_blank" class="btn btn-success">Open Frigate UI</a>
      <button class="btn btn-danger" onclick="confirmRemoveFrigate()">Remove Frigate</button>
    </div>
  </div>
  {% endif %}
</div>
<script>
async function deployFrigate() {
    const btn = document.getElementById(\\\'deploy-btn\\\');
    btn.disabled = true; btn.textContent = \\\'Deploying...\\\';
    document.getElementById(\\\'deploy-log-container\\\').style.display = \\\'block\\\';
    const r = await fetch(\\\'/api/frigate/deploy\\\', {method:\\\'POST\\\'});
    pollLog();
}
async function pollLog() {
    const logBox = document.getElementById(\\\'deploy-log\\\');
    let lastIdx = 0;
    const interval = setInterval(async () => {
        const r = await fetch(\\\'/api/frigate/deploy/log?index=\\\' + lastIdx);
        const d = await r.json();
        d.entries.forEach(e => {
            const div = document.createElement(\\\'div\\\');
            div.textContent = e;
            logBox.appendChild(div);
            logBox.scrollTop = logBox.scrollHeight;
        });
        lastIdx = d.total;
        if (d.complete || d.error) {
            clearInterval(interval);
            if (d.complete) setTimeout(() => location.reload(), 2000);
        }
    }, 1000);
}
function confirmRemoveFrigate() {
    if (confirm("Remove Frigate? Data in ~/frigate/storage will be preserved.")) {
        fetch(\\\'/api/frigate/remove\\\', {method:\\\'POST\\\'}).then(() => location.reload());
    }
}
</script>
</body></html>\'\'\'

@app.route(\'/frigate\')
@login_required
def frigate_page():
    settings = load_settings()
    modules = detect_modules()
    frigate = modules.get(\'frigate\', {})
    sidebar_html = render_sidebar(modules, \'frigate\')
    return render_template_string(FRIGATE_TEMPLATE,
        settings=settings, frigate=frigate, version=VERSION,
        sidebar_html=sidebar_html, frigate_logo_url=FRIGATE_LOGO_URL)

@app.route(\'/api/frigate/deploy\', methods=[\'POST\'])
@login_required
def frigate_deploy():
    if frigate_deploy_status.get(\'running\'):
        return jsonify({\'error\': \'Deployment already in progress\'}), 409
    frigate_deploy_log.clear()
    frigate_deploy_status.update({\'running\': True, \'complete\': False, \'error\': False})
    threading.Thread(target=run_frigate_deploy, daemon=True).start()
    return jsonify({\'success\': True})

@app.route(\'/api/frigate/remove\', methods=[\'POST\'])
@login_required
def frigate_remove():
    frigate_dir = os.path.expanduser(\'~/frigate\')
    subprocess.run(f\'cd {frigate_dir} && docker compose down\', shell=True, capture_output=True)
    if os.path.exists(os.path.join(frigate_dir, \'docker-compose.yml\')):
        os.remove(os.path.join(frigate_dir, \'docker-compose.yml\'))
    return jsonify({\'success\': True})

@app.route(\'/api/frigate/deploy/log\')
@login_required
def frigate_deploy_log_api():
    idx = request.args.get(\'index\', 0, type=int)
    return jsonify({\'entries\': frigate_deploy_log[idx:], \'total\': len(frigate_deploy_log),
        \'running\': frigate_deploy_status[\'running\'], \'complete\': frigate_deploy_status[\'complete\'],
        \'error\': frigate_deploy_status[\'error\']})

def run_frigate_deploy():
    def plog(msg):
        entry = f"[{datetime.now().strftime(\'%H:%M:%S\')}] {msg}"
        frigate_deploy_log.append(entry)
        print(entry, flush=True)
    try:
        frigate_dir = os.path.expanduser(\'~/frigate\')
        os.makedirs(frigate_dir, exist_ok=True)
        compose_content = """
services:
  frigate:
    container_name: frigate
    privileged: true
    restart: unless-stopped
    image: ghcr.io/blakeblackshear/frigate:stable
    shm_size: "64mb"
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config.yml:/config/config.yml
      - ./storage:/media/frigate
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000
    ports:
      - "5000:5000"
      - "8554:8554"
      - "8555:8555"
    environment:
      FRIGATE_RTSP_PASSWORD: "password"
"""
        with open(os.path.join(frigate_dir, \'docker-compose.yml\'), \'w\') as f:
            f.write(compose_content.strip())
        
        settings = load_settings()
        server_ip = settings.get(\'server_ip\', \'127.0.0.1\')
        config_content = """
mqtt:
  enabled: False
cameras:
  uas_1:
    ffmpeg:
      inputs:
        - path: rtsp://{ip}:8554/uas_1
          roles:
            - detect
    detect:
      enabled: True
      width: 1280
      height: 720
""".format(ip=server_ip)
        with open(os.path.join(frigate_dir, \'config.yml\'), \'w\') as f:
            f.write(config_content.strip())
        
        plog("Starting Frigate container...")
        subprocess.run(f\'cd {frigate_dir} && docker compose up -d\', shell=True, capture_output=True, text=True, timeout=300)
        plog("Frigate deployed successfully!")
        frigate_deploy_status.update({\'running\': False, \'complete\': True, \'error\': False})
    except Exception as e:
        plog(f"Error during deployment: {e}")
        frigate_deploy_status.update({\'running\': False, \'error\': True})

'''
    content = content.replace(insertion_point, frigate_code + insertion_point)

with open(app_path, 'w') as f:
    f.write(content)
