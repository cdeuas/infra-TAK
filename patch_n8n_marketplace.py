import os
import sys

# Absolute path for VM environment
app_path = '/home/sauron/infra-TAK/app.py'
if not os.path.exists(app_path):
    app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r') as f:
    content = f.read()

# 1. Constants and Status Globals
if 'N8N_LOGO_URL' not in content:
    const_hook = 'FRIGATE_LOGO_URL = "https://frigate.video/img/logo.png"'
    n8n_consts = const_hook + '\nN8N_LOGO_URL = "https://raw.githubusercontent.com/n8n-io/n8n/master/assets/n8n-logo.png"'
    content = content.replace(const_hook, n8n_consts)

if 'n8n_deploy_log = []' not in content:
    global_hook = 'frigate_deploy_log = []'
    n8n_globals = global_hook + '\nn8n_deploy_log = []\nn8n_deploy_status = {"running": False, "complete": False, "error": False}'
    content = content.replace(global_hook, n8n_globals)

# 2. Marketplace Icon Logic
# This adds the 🤖 icon to the marketplace view
old_market_icons = "{% elif key == 'frigate' %}<span class=\"module-icon material-symbols-outlined\" style=\"font-size:28px\">videocam</span>"
new_market_icons = old_market_icons + "{% elif key == 'n8n' %}<span class=\"module-icon material-symbols-outlined\" style=\"font-size:28px\">robot_2</span>"
if old_market_icons in content and 'key == \'n8n\'' not in content:
    content = content.replace(old_market_icons, new_market_icons)

# 3. Dedicated n8n Management Page Template
if 'N8N_TEMPLATE' not in content:
    n8n_template_code = '''
# === n8n Automation Module ===
N8N_TEMPLATE = \'\'\'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>n8n Automation — infra-TAK</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
<style>\'\'\' + BASE_CSS + \'\'\'
.log-box{background:#070a12;border:1px solid var(--border);border-radius:8px;padding:16px;font-family:\\\'JetBrains Mono\\\',monospace;font-size:11px;color:var(--text-dim);max-height:340px;overflow-y:auto;white-space:pre-wrap}
</style></head>
<body>
{{ sidebar_html }}
<div class="main">
  <div class="page-header"><h1 style="display:flex;flex-direction:column;align-items:flex-start;gap:6px"><span class="nav-icon material-symbols-outlined" style="font-size:32px">robot_2</span><span>n8n Tactical Automation</span></h1><p>Flow-based AI automation & mission reporting</p></div>
  
  {% if n8n.running %}<div class="status-banner running"><div class="dot"></div>n8n is running</div>
  {% elif n8n.installed %}<div class="status-banner stopped"><div class="dot"></div>n8n is installed but stopped</div>
  {% else %}<div class="status-banner not-installed"><div class="dot"></div>n8n is not installed</div>{% endif %}
  
  {% if not n8n.installed %}
  <div class="card">
    <div class="card-title">Deploy n8n Automation</div>
    <p style="font-size:13px;color:var(--text-secondary);margin-bottom:20px">Deploy n8n as a Docker container to automate tactical workflows and AI analysis.</p>
    <div class="controls">
      <button class="btn btn-primary" id="deploy-btn" onclick="deployN8n()">Deploy n8n</button>
    </div>
    <div id="deploy-log-container" style="display:none;margin-top:20px">
      <div class="section-title">Deployment Log</div>
      <div class="log-box" id="deploy-log"></div>
    </div>
  </div>
  {% else %}
  <div class="card">
    <div class="card-title">n8n Controls</div>
    <div class="controls">
      <a href="/n8n" target="_blank" class="btn btn-success">Open n8n Dashboard</a>
      <button class="btn btn-danger" onclick="confirmRemoveN8n()">Remove n8n</button>
    </div>
  </div>
  {% endif %}
</div>
<script>
async function deployN8n() {
    const btn = document.getElementById(\\\'deploy-btn\\\');
    btn.disabled = true; btn.textContent = \\\'Deploying...\\\';
    document.getElementById(\\\'deploy-log-container\\\').style.display = \\\'block\\\';
    const r = await fetch(\\\'/api/n8n/deploy\\\', {method:\\\'POST\\\'});
    pollLog();
}
async function pollLog() {
    const logBox = document.getElementById(\\\'deploy-log\\\');
    let lastIdx = 0;
    const interval = setInterval(async () => {
        const r = await fetch(\\\'/api/n8n/deploy/log?index=\\\' + lastIdx);
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
function confirmRemoveN8n() {
    if (confirm("Remove n8n? Data in ~/n8n-tactical/data will be preserved.")) {
        fetch(\\\'/api/n8n/remove\\\', {method:\\\'POST\\\'}).then(() => location.reload());
    }
}
</script>
</body></html>\'\'\'
'''
    # Inject before the Main Entry Point
    content = content.replace("# === Main Entry Point", n8n_template_code + "\n\n# === Main Entry Point")

# 4. API Endpoints for n8n Management
if "@app.route('/n8n')" not in content:
    n8n_routes = '''
@app.route('/n8n-manage')
@login_required
def n8n_page():
    settings = load_settings()
    modules = detect_modules()
    n8n = modules.get('n8n', {})
    sidebar_html = render_sidebar(modules, 'n8n')
    return render_template_string(N8N_TEMPLATE,
        settings=settings, n8n=n8n, version=VERSION,
        sidebar_html=sidebar_html)

@app.route('/api/n8n/deploy', methods=['POST'])
@login_required
def n8n_deploy():
    if n8n_deploy_status.get('running'):
        return jsonify({'error': 'Deployment already in progress'}), 409
    n8n_deploy_log.clear()
    n8n_deploy_status.update({'running': True, 'complete': False, 'error': False})
    threading.Thread(target=run_n8n_deploy, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/n8n/remove', methods=['POST'])
@login_required
def n8n_remove():
    n8n_dir = os.path.expanduser('~/n8n-tactical')
    subprocess.run(f'cd {n8n_dir} && docker compose down', shell=True, capture_output=True)
    # Note: We don't delete docker-compose.yml here to allow re-deploy to see it's "not installed" properly 
    # but we remove the marker for detect_modules
    if os.path.exists(os.path.join(n8n_dir, 'docker-compose.yml')):
        os.rename(os.path.join(n8n_dir, 'docker-compose.yml'), os.path.join(n8n_dir, 'docker-compose.yml.bak'))
    return jsonify({'success': True})

@app.route('/api/n8n/deploy/log')
@login_required
def n8n_deploy_log_api():
    idx = request.args.get('index', 0, type=int)
    return jsonify({'entries': n8n_deploy_log[idx:], 'total': len(n8n_deploy_log),
        'running': n8n_deploy_status['running'], 'complete': n8n_deploy_status['complete'],
        'error': n8n_deploy_status['error']})

def run_n8n_deploy():
    def plog(msg):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        n8n_deploy_log.append(entry)
        print(entry, flush=True)
    try:
        n8n_dir = os.path.expanduser('~/n8n-tactical')
        os.makedirs(n8n_dir, exist_ok=True)
        os.makedirs(os.path.join(n8n_dir, 'data'), exist_ok=True)
        # Fix permissions
        subprocess.run(f'sudo chown -R 1000:1000 {n8n_dir}/data', shell=True)
        
        compose_content = """
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n-tactical
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=infratak.infra-tak-vm.netbird.cloud
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://infratak.infra-tak-vm.netbird.cloud/n8n/
      - OLLAMA_HOST=http://10.0.3.100:11434
    volumes:
      - ./data:/home/node/.n8n
    networks:
      - infratak
networks:
  infratak:
    external: true
"""
        with open(os.path.join(n8n_dir, 'docker-compose.yml'), 'w') as f:
            f.write(compose_content.strip())
        
        plog("Pulling n8n image...")
        subprocess.run(f'cd {n8n_dir} && docker compose pull', shell=True, capture_output=True)
        plog("Starting n8n container...")
        subprocess.run(f'cd {n8n_dir} && docker compose up -d', shell=True, capture_output=True)
        plog("n8n deployed successfully!")
        n8n_deploy_status.update({'running': False, 'complete': True, 'error': False})
    except Exception as e:
        plog(f"Error during deployment: {e}")
        n8n_deploy_status.update({'running': False, 'error': True})
'''
    content = content.replace("# === Main Entry Point", n8n_routes + "\n\n# === Main Entry Point")

# 5. Fix detect_modules to use the management route
if "modules['n8n'] = {" in content:
    # Update route from /n8n (direct) to /n8n-manage (console control)
    content = content.replace("'route': '/n8n'", "'route': '/n8n-manage'")
    # Ensure it uses the robot icon consistently
    content = content.replace("'icon': '🤖'", "'icon': 'robot_2'")

with open(app_path, 'w') as f:
    f.write(content)
print("Marketplace n8n patches applied")
