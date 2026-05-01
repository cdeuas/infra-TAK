import os
import html

# Use absolute path to avoid ~/ expansion issues with sudo
app_path = '/home/sauron/infra-TAK/app.py'
if not os.path.exists(app_path):
    # Fallback to current directory
    app_path = os.path.join(os.getcwd(), 'app.py')

with open(app_path, 'r') as f:
    content = f.read()

# 1. Update detect_modules icon
old_detect_frigate = "'icon': '📹', 'icon_url': FRIGATE_LOGO_URL"
new_detect_frigate = "'icon': 'videocam', 'icon_url': FRIGATE_LOGO_URL"
content = content.replace(old_detect_frigate, new_detect_frigate)

# 2. Update sidebar link to use Material Symbol
old_sidebar_frigate = """    frigate = modules.get('frigate', {})
    if frigate.get('installed'):
        parts.append(link('/frigate', f'<img src="{html.escape(FRIGATE_LOGO_URL)}" alt="" class="nav-icon" style="height:24px;width:auto;max-width:72px;object-fit:contain;display:block"><span>Frigate</span>'))"""

new_sidebar_frigate = """    frigate = modules.get('frigate', {})
    if frigate.get('installed'):
        parts.append(link('/frigate', '<span class="nav-icon material-symbols-outlined">videocam</span><span>Frigate</span>'))"""

content = content.replace(old_sidebar_frigate, new_sidebar_frigate)

# 3. Update MARKETPLACE_TEMPLATE to handle frigate symbol
old_marketplace_icons = "{% elif key == 'emailrelay' %}<span class=\"module-icon material-symbols-outlined\" style=\"font-size:28px\">outgoing_mail</span>"
new_marketplace_icons = "{% elif key == 'emailrelay' %}<span class=\"module-icon material-symbols-outlined\" style=\"font-size:28px\">outgoing_mail</span>{% elif key == 'frigate' %}<span class=\"module-icon material-symbols-outlined\" style=\"font-size:28px\">videocam</span>"

content = content.replace(old_marketplace_icons, new_marketplace_icons)

with open(app_path, 'w') as f:
    f.write(content)
