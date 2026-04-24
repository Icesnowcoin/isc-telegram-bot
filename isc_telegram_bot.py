#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ice Snow Coin (ISC) Telegram Bot
功能：价格查询、合约信息、社区欢迎、FAQ
部署：VPS (Ubuntu 24.04) + PM2 守护进程
作者：ISC Team
"""

import os
import json
import logging
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import aiohttp

# ==================== 配置 ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ISC_CONTRACT = "0x11229a3f976566FA8a3ba462C432122f3B8876f6"
ISC_SYMBOL = "ISC"
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY", "")
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
PANCAKESWAP_URL = f"https://pancakeswap.finance/swap?outputCurrency={ISC_CONTRACT}"
BSCSCAN_URL = f"https://bscscan.com/token/{ISC_CONTRACT}"
WEBSITE = "https://icesnowcoin.com"
WHITEPAPER = "https://icesnowcoin.org"
X_TWITTER = "https://x.com/IceSnowCoin"
TELEGRAM_GROUP = "https://t.me/IceSnowCoinCommunity"
GITHUB = "https://github.com/Icesnowcoin"
AUDIT_REPORT = "https://github.com/Icesnowcoin/isc-audit-reports"

# 日志配置
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== 数据缓存 ====================
price_cache = {"data": None, "timestamp": 0}
CACHE_DURATION = 60  # 价格缓存60秒

# ==================== 辅助函数 ====================

async def fetch_price():
    """获取 ISC 实时价格"""
    global price_cache
    now = datetime.now().timestamp()
    
    if price_cache["data"] and (now - price_cache["timestamp"]) < CACHE_DURATION:
        return price_cache["data"]
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{DEXSCREENER_API}{ISC_CONTRACT}"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        pair = pairs[0]
                        price_cache = {
                            "data": {
                                "price": pair.get("priceUsd", "N/A"),
                                "priceNative": pair.get("priceNative", "N/A"),
                                "volume24h": pair.get("volume", {}).get("h24", "N/A"),
                                "liquidity": pair.get("liquidity", {}).get("usd", "N/A"),
                                "fdv": pair.get("fdv", "N/A"),
                                "change24h": pair.get("priceChange", {}).get("h24", "N/A"),
                                "url": pair.get("url", "")
                            },
                            "timestamp": now
                        }
                        return price_cache["data"]
    except Exception as e:
        logger.error(f"获取价格失败: {e}")
    
    return None

# ==================== 命令处理器 ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 命令 - 欢迎语"""
      user = update.effective_user
    if user is None:
        user_name = "社区成员"
    else:
        user_name = user.first_name
    
    welcome_text = f"""
❄️ <b>欢迎来到 Ice Snow Coin (ISC) 社区！</b>

你好 {user_name}，我是 ISC 社区助手 Bot。

🔹 <b>关于 ISC</b>
AI 驱动的 GameFi + NFT 生态系统，连接虚拟与现实世界。

🔹 <b>合约地址</b>
<code>{ISC_CONTRACT}</code>

🔹 <b>核心数据</b>
• 总供应量：202,600,000 ISC（固定，无通胀）
• 链：Binance Smart Chain (BEP-20)
• 审计：TechRate（2026年4月，21项检查全部通过）

🔹 <b>安全承诺</b>
✅ 合约所有权已永久放弃
✅ 40% LP 流动性已锁仓（UNCX，1-4年）
✅ 20% 团队代币已锁仓（Team Finance，24个月）

📌 <b>常用命令</b>
/price - 查询实时价格
/contract - 合约详情与链接
/tokenomics - 代币经济学
/security - 安全与审计信息
/roadmap - 项目路线图
/links - 官方链接汇总
/help - 帮助与 FAQ

⚠️ <b>风险提示</b>
加密货币投资具有高风险，请自行进行尽职调查。
    """
    
    keyboard = [
        [InlineKeyboardButton("🌐 官网", url=WEBSITE)],
        [InlineKeyboardButton("📄 白皮书", url=WHITEPAPER)],
        [InlineKeyboardButton("🔄 PancakeSwap 交易", url=PANCAKESWAP_URL)],
        [InlineKeyboardButton("🔍 BSCScan", url=BSCSCAN_URL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/price 命令 - 查询实时价格"""
    msg = await update.message.reply_text("⏳ 正在获取 ISC 实时价格...")
    
    data = await fetch_price()
    
    if data:
        price = data.get("price", "N/A")
        change = data.get("change24h", "N/A")
        volume = data.get("volume24h", "N/A")
        liquidity = data.get("liquidity", "N/A")
        fdv = data.get("fdv", "N/A")
        
        # 格式化数字
        try:
            change_emoji = "🟢" if float(change) >= 0 else "🔴"
            change_str = f"{change_emoji} {change}% (24h)"
        except:
            change_str = f"{change} (24h)"
        
        text = f"""
📊 <b>ISC 实时行情</b>

💰 <b>价格：</b>${price}
{change_str}

📈 <b>24h 成交量：</b>${volume}
💧 <b>流动性：</b>${liquidity}
🏦 <b>完全稀释估值：</b>${fdv}

⏰ 更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} UTC+8

🔗 <a href="{PANCAKESWAP_URL}">PancakeSwap 交易</a>
🔗 <a href="{BSCSCAN_URL}">BSCScan 查看</a>
        """
    else:
        text = f"""
❌ <b>暂时无法获取价格数据</b>

请稍后重试，或直接访问：
🔗 <a href="{PANCAKESWAP_URL}">PancakeSwap</a>
🔗 <a href="https://dexscreener.com/bsc/{ISC_CONTRACT}">DEXScreener</a>
        """
    
    await msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def contract_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/contract 命令 - 合约详情"""
    text = f"""
📋 <b>ISC 合约信息</b>

<b>合约地址：</b>
<code>{ISC_CONTRACT}</code>
（点击可复制）

<b>链：</b>Binance Smart Chain (BEP-20)
<b>标准：</b>UUPS 可升级代理 (EIP-1967)
<b>总供应量：</b>202,600,000 ISC（固定，无通胀）

<b>实现合约：</b>
<code>0xf74F38cb35255b85514C49255f0EA29A013cB618</code>

<b>所有权状态：</b>
✅ 已永久放弃（2026年4月19日）
🔒 当前所有者：0x000...000（零地址）

<b>安全审计：</b>
🛡️ TechRate（2026年4月）
✅ 21 项安全检查全部通过
📄 <a href="{AUDIT_REPORT}">查看审计报告</a>

<b>流动性锁仓：</b>
🔒 40% 已锁仓（UNCX Network）
• 5% 锁 1 年
• 35% 锁 4 年（2030年解锁）

<b>团队归属：</b>
⏳ 20% 锁仓 24 个月（Team Finance）
• 首次释放：2026年5月20日
• 每月释放：~1,688,333 ISC
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 BSCScan 合约", url=BSCSCAN_URL)],
        [InlineKeyboardButton("🛡️ 审计报告", url=AUDIT_REPORT)],
        [InlineKeyboardButton("💧 UNCX 锁仓", url="https://app.uncx.network/lockers/manage/lockers-v3")],
        [InlineKeyboardButton("⏳ Team Finance", url="https://app.team.finance/token-vesting")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def tokenomics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/tokenomics 命令 - 代币经济学"""
    text = f"""
📊 <b>ISC 代币经济学</b>

<b>总供应量：</b>202,600,000 ISC（固定，无通胀）

<b>分配方案：</b>
💧 <b>流动性池 40%</b> — 81,040,000 ISC
   🔒 已锁仓（UNCX，1-4年）

👥 <b>团队分配 20%</b> — 40,520,000 ISC
   ⏳ 锁仓 24 个月（Team Finance）

🌍 <b>社区/生态/营销 30%</b> — 60,780,000 ISC
   ✅ 运营中（研发、空投、营销）

🎁 <b>APY 奖励池 10%</b> — 20,260,000 ISC
   📅 预留（2026年Q3 质押上线）

<b>营销钱包：</b>
<code>0xF8A408495941ea30451Da613dC846Dcae47890f0</code>

<b>预售信息：</b>
📅 2026年4月20日-30日
💰 1 USDT = 2,000 ISC
    """
    
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def security_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/security 命令 - 安全信息"""
    text = f"""
🛡️ <b>ISC 安全与透明度</b>

<b>1. 合约所有权已放弃</b>
✅ 放弃日期：2026年4月19日 19:41 UTC
✅ 交易哈希：0x983aa29b...9e09d7c
✅ 当前所有者：0x000...000（零地址）
🔐 状态：不可逆，无管理员权限

<b>2. 第三方安全审计</b>
🛡️ 审计机构：TechRate
📅 审计日期：2026年4月
✅ 结果：21 项安全检查全部通过
❌ 未发现高/中严重级别漏洞
📄 <a href="{AUDIT_REPORT}">查看完整报告</a>

<b>3. 反巨鲸保护机制</b>
🐋 maxTxAmount：0.5%（1,013,000 ISC）
🎯 目的：防止大额单笔抛售，保护小持有者
⚠️ 流动性池不豁免，所有参与者遵循相同规则

<b>4. 流动性锁仓</b>
🔒 平台：UNCX Network
📊 总量：40%（81,040,000 ISC）
• 5% 锁 1 年
• 35% 锁 4 年（2030年解锁）

<b>5. 团队代币归属</b>
⏳ 平台：Team Finance
📊 总量：20%（40,520,000 ISC）
• 归属期：24 个月
• 首次释放：2026年5月20日
• 每月释放：~1,688,333 ISC

<b>6. 链上验证</b>
所有数据可在 BSCScan 公开验证：
🔗 <a href="{BSCSCAN_URL}">查看合约</a>
    """
    
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def roadmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/roadmap 命令 - 路线图"""
    text = f"""
🗺️ <b>ISC 路线图</b>

✅ <b>已完成（2026年4月）</b>
• 智能合约部署与测试
• 代理合约与实现合约所有权完全释放
• LP 流动性分层锁仓（5% 1年 + 35% 4年）
• 团队资金 20% 已锁仓（24个月）
• 官网与白皮书 v3.0 发布
• TechRate 安全审计完成
• GitHub 审计仓库发布

⏳ <b>进行中（2026年Q2）</b>
• BSCScan 代币 Logo 与信息更新
• ISC 纪念版动态 NFT 合约开发
• GameFi 核心框架开发
• 社区空间基础设施
• 多签财库设置（Safe{{Wallet}}）
• 代币上线申请（CEX & DEX）

📋 <b>计划中（2026年Q3）</b>
• NFT 铸造功能上线
• 社区任务系统与雪花积分部署
• 首次自动化空投分发（反女巫 Agent）
• GameFi 测试版发布
• 社区 DAO 治理启动（Snapshot）
• APY 质押机制部署

🚀 <b>未来（2026年Q4+）</b>
• 跨链部署评估（Ethereum、Base、Arbitrum）
• 高级 GameFi 功能与锦标赛
• 生态合作伙伴（GameFi 工作室、AI 平台）
• 全球社区扩展与区域大使计划
• RWA（现实世界资产）集成试点
    """
    
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/links 命令 - 官方链接汇总"""
    keyboard = [
        [InlineKeyboardButton("🌐 官网", url=WEBSITE),
         InlineKeyboardButton("📄 白皮书", url=WHITEPAPER)],
        [InlineKeyboardButton("🐦 X/Twitter", url=X_TWITTER),
         InlineKeyboardButton("💬 Telegram", url=TELEGRAM_GROUP)],
        [InlineKeyboardButton("🔄 PancakeSwap", url=PANCAKESWAP_URL),
         InlineKeyboardButton("🔍 BSCScan", url=BSCSCAN_URL)],
        [InlineKeyboardButton("📊 DEXScreener", url=f"https://dexscreener.com/bsc/{ISC_CONTRACT}"),
         InlineKeyboardButton("🛡️ 审计报告", url=AUDIT_REPORT)],
        [InlineKeyboardButton("💻 GitHub", url=GITHUB)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔗 <b>ISC 官方链接汇总</b>\n\n点击下方按钮快速访问：",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help 命令 - 帮助与 FAQ"""
    text = f"""
❓ <b>ISC Bot 帮助中心</b>

<b>可用命令：</b>
/start - 欢迎语与项目介绍
/price - 查询 ISC 实时价格
/contract - 合约详情与链上链接
/tokenomics - 代币经济学详情
/security - 安全与审计信息
/roadmap - 项目路线图
/links - 官方链接汇总
/help - 显示此帮助信息

<b>常见问题：</b>

<b>Q: ISC 是什么？</b>
A: Ice Snow Coin (ISC) 是一个 AI 驱动的 GameFi + NFT 生态系统，部署在币安智能链上。

<b>Q: 合约安全吗？</b>
A: ✅ 合约所有权已永久放弃，无管理员权限。✅ 通过 TechRate 安全审计（21项检查全部通过）。✅ 40% LP 已锁仓，20% 团队代币已锁仓。

<b>Q: 如何购买 ISC？</b>
A: 通过 PancakeSwap 交易：{PANCAKESWAP_URL}

<b>Q: 总供应量是多少？会增发吗？</b>
A: 总供应量 202,600,000 ISC，固定无通胀，永不增发。

<b>Q: 团队代币什么时候解锁？</b>
A: 团队 20% 分配已通过 Team Finance 锁仓 24 个月，从 2026年5月20日 开始线性释放。

<b>Q: 如何参与社区贡献？</b>
A: 加入 Telegram 群组，参与任务系统赚取雪花积分（❄️），详情见官网社区板块。

<b>⚠️ 安全提醒：</b>
• 唯一合约地址：<code>{ISC_CONTRACT}</code>
• 警惕假冒代币和钓鱼网站
• 官方不会私信索要私钥或助记词
• 所有公告以官方 X/Telegram 为准

<b>技术支持：</b>
如有问题请联系社区管理员或发送邮件至官方邮箱。
    """
    
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理未知命令"""
    await update.message.reply_text(
        "❓ 未知命令。输入 /help 查看可用命令列表。",
        parse_mode="HTML"
    )


# ==================== 错误处理 ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """全局错误处理"""
    logger.error(f"更新 {update} 导致错误: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ 处理请求时发生错误，请稍后重试。",
            parse_mode="HTML"
        )

# ==================== 主函数 ====================

def main():
    """启动 Bot"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("请设置 BOT_TOKEN 环境变量！")
        print("❌ 错误：请设置 BOT_TOKEN 环境变量")
        print("   export BOT_TOKEN='你的Bot Token'")
        return
    
    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 注册命令处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("contract", contract_command))
    application.add_handler(CommandHandler("tokenomics", tokenomics_command))
    application.add_handler(CommandHandler("security", security_command))
    application.add_handler(CommandHandler("roadmap", roadmap_command))
    application.add_handler(CommandHandler("links", links_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # 未知命令处理
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # 错误处理
    application.add_error_handler(error_handler)
    
    # 启动 Bot
    logger.info("🤖 ISC Bot 已启动！")
    print("🤖 ISC Bot 已启动！按 Ctrl+C 停止")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
