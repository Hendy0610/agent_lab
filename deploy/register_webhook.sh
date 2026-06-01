#!/bin/bash
# Register Telegram Webhook
# Usage: bash register_webhook.sh <SERVER_IP>

set -e

if [ -z "$1" ]; then
    echo "Usage: bash register_webhook.sh <SERVER_IP>"
    exit 1
fi

SERVER_IP="$1"
source /opt/agent-lab-bot/.env

WEBHOOK_URL="http://${SERVER_IP}:8443/webhook"

echo "Registriere Webhook: $WEBHOOK_URL"

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -d "url=${WEBHOOK_URL}" \
    -d "secret_token=${WEBHOOK_SECRET}" \
    | python3 -m json.tool

echo ""
echo "Webhook-Status prüfen:"
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" \
    | python3 -m json.tool
