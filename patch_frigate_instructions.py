import os

# Use absolute path to avoid ~/ expansion issues with sudo
app_path = '/home/sauron/infra-TAK/app.py'
if not os.path.exists(app_path):
    # Fallback to current directory
    app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r') as f:
    content = f.read()

# Define the new template with instructions
new_template = '''
# === Frigate NVR Module ===
FRIGATE_TEMPLATE = \'\'\'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Frigate NVR — infra-TAK</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
<style>\'\'\' + BASE_CSS + \'\'\'
.log-box{background:#070a12;border:1px solid var(--border);border-radius:8px;padding:16px;font-family:\\\'JetBrains Mono\\\',monospace;font-size:11px;color:var(--text-dim);max-height:340px;overflow-y:auto;white-space:pre-wrap}
.instruction-step{margin-bottom:20px;padding-left:12px;border-left:2px solid var(--accent)}
.instruction-title{font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:4px}
.instruction-text{font-size:13px;color:var(--text-secondary);line-height:1.5}
.code-inline{font-family:\\\'JetBrains Mono\\\',monospace;background:rgba(255,255,255,0.05);padding:2px 4px;border-radius:4px;font-size:12px}
</style></head>
<body>
{{ sidebar_html }}
<div class="main">
  <div class="page-header"><h1 style="display:flex;flex-direction:column;align-items:flex-start;gap:6px"><span class="nav-icon material-symbols-outlined" style="font-size:32px">videocam</span><span>Frigate NVR</span></h1><p>AI-powered NVR with object detection</p></div>
  
  {% if frigate.running %}<div class="status-banner running"><div class="dot"></div>Frigate is running</div>
  {% elif frigate.installed %}<div class="status-banner stopped"><div class="dot"></div>Frigate is installed but stopped</div>
  {% else %}<div class="status-banner not-installed"><div class="dot"></div>Frigate is not installed</div>{% endif %}
  
  {% if not frigate.installed %}
  <div class="card">
    <div class="card-title">Pre-Deployment Guide</div>
    <div class="instruction-step">
      <div class="instruction-title">1. Stream Source (MediaMTX)</div>
      <div class="instruction-text">Frigate requires an RTSP stream to analyze. By default, this deployment expects a stream at <span class="code-inline">uas_1</span> on your local MediaMTX instance.</div>
    </div>
    <div class="instruction-step">
      <div class="instruction-title">2. Hardware Resources</div>
      <div class="instruction-text">AI object detection is CPU intensive. For production, a <strong>Google Coral TPU</strong> is highly recommended. This deployment uses CPU detection by default.</div>
    </div>
    <div class="instruction-step">
      <div class="instruction-title">3. Storage Space</div>
      <div class="instruction-text">Recordings and snapshots will be stored in <span class="code-inline">~/frigate/storage</span>. Ensure you have enough disk space for your retention policy.</div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Deploy Frigate NVR</div>
    <p style="font-size:13px;color:var(--text-secondary);margin-bottom:20px">Clicking deploy will create the <span class="code-inline">~/frigate</span> directory, generate a starter configuration, and start the Docker container.</p>
    <div class="controls">
      <button class="btn btn-primary" id="deploy-btn" onclick="deployFrigate()">Begin Deployment</button>
    </div>
    <div id="deploy-log-container" style="display:none;margin-top:24px">
      <div class="section-title">Deployment Log</div>
      <div class="log-box" id="deploy-log"></div>
    </div>
  </div>
  {% else %}
  <div class="card">
    <div class="card-title">Frigate Web UI</div>
    <p style="font-size:13px;color:var(--text-secondary);margin-bottom:20px">The Frigate dashboard allows you to view live streams, review events, and tune detection parameters.</p>
    <div class="controls">
      <a href="http://{{ settings.get(\\\'server_ip\\\', \\\'localhost\\\') }}:5000" target="_blank" class="btn btn-success">Open Frigate UI <span class="material-symbols-outlined" style="font-size:16px">open_in_new</span></a>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Management & Customization</div>
    <div class="instruction-step">
      <div class="instruction-title">Configuration File</div>
      <div class="instruction-text">To add cameras or change AI settings, edit: <span class="code-inline">~/frigate/config.yml</span></div>
    </div>
    <div class="instruction-step">
      <div class="instruction-title">Restart Service</div>
      <div class="instruction-text">After changing settings, restart the container via SSH: <br><span class="code-inline">cd ~/frigate && docker compose restart</span></div>
    </div>
    <div style="margin-top:24px;padding-top:20px;border-top:1px solid var(--border)">
      <button class="btn btn-danger" onclick="confirmRemoveFrigate()">Remove Frigate NVR</button>
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
    if (confirm("Permanently remove Frigate NVR? Config and storage folders will be preserved.")) {
        fetch(\\\'/api/frigate/remove\\\', {method:\\\'POST\\\'}).then(() => location.reload());
    }
}
</script>
</body></html>\'\'\'
'''

# Surgical replacement of the old template block
start_marker = "# === Frigate NVR Module ==="
end_marker = "@app.route(\'/frigate\')"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_template.strip() + "\n\n" + content[end_idx:]
    with open(app_path, 'w') as f:
        f.write(new_content)
    print("Template updated successfully")
else:
    print(f"Error: Markers not found. start_idx={start_idx}, end_idx={end_idx}")
