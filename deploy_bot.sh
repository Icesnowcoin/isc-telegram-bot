#!/bin/bash
echo "🤖 开始部署 ISC Telegram Bot..."
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git
mkdir -p /opt/isc-bot && cd /opt/isc-bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install python-telegram-bot aiohttp
echo "✅ 环境准备完成！"
echo "下一步：export BOT_TOKEN='你的Token' && python3 isc_telegram_bot.py"
