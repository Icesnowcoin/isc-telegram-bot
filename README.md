# ISC Telegram Bot

## 部署步骤

1. 在 Telegram 搜索 @BotFather 创建机器人，获取 Token
2. 在 VPS 终端执行以下命令：

git clone https://github.com/Icesnowcoin/isc-telegram-bot.git /opt/isc-bot
cd /opt/isc-bot
bash deploy_bot.sh
export BOT_TOKEN="你的Token"
python3 isc_telegram_bot.py
