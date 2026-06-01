#!/bin/bash
# Setup script for Agent Lab Telegram Webhook Bot
# Run as root on the server: bash setup.sh

set -e

echo "=== Agent Lab Bot Setup ==="

# 1. Create directory
mkdir -p /opt/agent-lab-bot
cd /opt/agent-lab-bot

# 2. Copy files
cp "$(dirname "$0")/webhook_server.py" /opt/agent-lab-bot/
cp "$(dirname "$0")/requirements.txt" /opt/agent-lab-bot/

# 3. Create venv and install deps
python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

# 4. Create .env if it doesn't exist
if [ ! -f /opt/agent-lab-bot/.env ]; then
    cat > /opt/agent-lab-bot/.env << 'EOF'
TELEGRAM_BOT_TOKEN=DEIN_BOT_TOKEN
TELEGRAM_CHAT_ID=DEINE_CHAT_ID
GH_PAT=DEIN_GITHUB_PAT
GH_REPO=Hendy0610/agent_lab
WEBHOOK_SECRET=ein-geheimes-passwort
EOF
    echo ""
    echo ">>> WICHTIG: Bitte /opt/agent-lab-bot/.env mit deinen Werten befüllen!"
    echo "    nano /opt/agent-lab-bot/.env"
fi

# 5. Install and enable systemd service
cp "$(dirname "$0")/agent-lab-bot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable agent-lab-bot

echo ""
echo "=== Setup abgeschlossen ==="
echo ""
echo "Nächste Schritte:"
echo "1. nano /opt/agent-lab-bot/.env  — Secrets eintragen"
echo "2. systemctl start agent-lab-bot  — Bot starten"
echo "3. systemctl status agent-lab-bot  — Status prüfen"
echo ""
echo "Danach Webhook registrieren (mit deiner Server-IP):"
echo "  bash $(dirname "$0")/register_webhook.sh <DEINE_IP>"
