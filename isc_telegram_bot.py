#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ice Snow Coin (ISC) Telegram Bot v2.0
功能：价格查询、合约信息、FAQ知识库、关键词自动回复、防骗提醒、新成员欢迎
部署：VPS (Ubuntu 24.04) + systemd 守护进程
"""

import os
import logging
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters
)
import aiohttp

# ==================== 配置 ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ISC_CONTRACT = "0x11229a3f976566FA8a3ba462C432122f3B8876f6"
ISC_SYMBOL = "ISC"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/tokens/"
PANCAKESWAP_URL = f"https://pancakeswap.finance/swap?outputCurrency={ISC_CONTRACT}"
BSCSCAN_URL = f"https://bscscan.com/token/{ISC_CONTRACT}"
WEBSITE = "https://icesnowcoin.com"
WHITEPAPER = "https://icesnowcoin.org"
X_TWITTER = "https://x.com/IceSnowCoin"
TELEGRAM_GROUP = "https://t.me/IceSnowCoinCommunity"
TELEGRAM_CHAT = "https://t.me/IceSnowCoinChat"
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
CACHE_DURATION = 60

# ==================== FAQ 知识库 ====================
FAQ_KEYWORDS = {
    "合约": """📋 <b>ISC 合约地址</b>
<code>0x11229a3f976566FA8a3ba462C432122f3B8876f6</code>

链：Binance Smart Chain (BEP-20)
标准：UUPS 可升级代理 (EIP-1967)

🔍 <a href="{BSCSCAN_URL}">BSCScan 查看</a>
🔄 <a href="{PANCAKESWAP_URL}">PancakeSwap 交易</a>""",

    "地址": """📋 <b>ISC 合约地址</b>
<code>0x11229a3f976566FA8a3ba462C432122f3B8876f6</code>

⚠️ 请仔细核对地址，警惕假冒代币！

🔍 <a href="{BSCSCAN_URL}">BSCScan 验证</a>""",

    "contract": """📋 <b>ISC Contract Address</b>
<code>0x11229a3f976566FA8a3ba462C432122f3B8876f6</code>

Chain: Binance Smart Chain (BEP-20)

🔍 <a href="{BSCSCAN_URL}">View on BSCScan</a>""",

    "价格": """💰 <b>ISC 价格查询</b>

请使用命令 /price 获取实时价格

或访问：
📊 <a href="https://dexscreener.com/bsc/{ISC_CONTRACT}">DEXScreener</a>
🔄 <a href="{PANCAKESWAP_URL}">PancakeSwap</a>""",

    "price": """💰 <b>ISC Price</b>

Use /price command for real-time price

Or visit:
📊 <a href="https://dexscreener.com/bsc/{ISC_CONTRACT}">DEXScreener</a>""",

    "买": """🛒 <b>如何购买 ISC</b>

1️⃣ 打开 <a href="{PANCAKESWAP_URL}">PancakeSwap</a>
2️⃣ 连接钱包（MetaMask / Trust Wallet）
3️⃣ 确保网络为 BSC（币安智能链）
4️⃣ 输入合约地址导入 ISC
5️⃣ 用 BNB 或 USDT 兑换

⚠️ 滑点建议设置 0.5% - 1%
⚠️ 务必核对合约地址！""",

    "购买": """🛒 <b>如何购买 ISC</b>

1️⃣ 打开 <a href="{PANCAKESWAP_URL}">PancakeSwap</a>
2️⃣ 连接钱包（MetaMask / Trust Wallet）
3️⃣ 确保网络为 BSC（币安智能链）
4️⃣ 输入合约地址导入 ISC
5️⃣ 用 BNB 或 USDT 兑换

⚠️ 滑点建议设置 0.5% - 1%""",

    "swap": """🛒 <b>How to Buy ISC</b>

1️⃣ Open <a href="{PANCAKESWAP_URL}">PancakeSwap</a>
2️⃣ Connect wallet (MetaMask / Trust Wallet)
3️⃣ Ensure BSC network
4️⃣ Import ISC with contract address
5️⃣ Swap BNB or USDT for ISC

⚠️ Set slippage to 0.5% - 1%""",

    "审计": """🛡️ <b>ISC 安全审计</b>

审计机构：TechRate
审计日期：2026年4月
结果：✅ 21 项安全检查全部通过

📄 <a href="{AUDIT_REPORT}">查看完整审计报告</a>

安全亮点：
✅ 合约所有权已永久放弃
✅ 40% LP 流动性已锁仓（UNCX）
✅ 20% 团队代币已锁仓（Team Finance）
✅ 0.5% 反巨鲸保护机制""",

    "audit": """🛡️ <b>ISC Security Audit</b>

Auditor: TechRate
Date: April 2026
Result: ✅ 21/21 checks passed

📄 <a href="{AUDIT_REPORT}">Full Audit Report</a>

Security Highlights:
✅ Ownership renounced
✅ 40% LP locked (UNCX)
✅ 20% team tokens vested (Team Finance)
✅ 0.5% anti-whale protection""",

    "安全": """🔐 <b>ISC 安全保障</b>

1. 合约所有权已放弃 → 零地址管理
2. TechRate 审计通过 → 21项检查
3. LP 流动性锁仓 → 40% 锁定1-4年
4. 团队代币归属 → 20% 锁定24个月
5. 反巨鲸机制 → 单笔上限 0.5%

🔗 <a href="{AUDIT_REPORT}">审计报告</a>
🔗 <a href="https://app.uncx.network">UNCX 锁仓验证</a>
🔗 <a href="https://app.team.finance">Team Finance 归属验证</a>""",

    "锁仓": """🔒 <b>ISC 锁仓信息</b>

<b>流动性池锁仓（UNCX Network）</b>
总量：40%（81,040,000 ISC）
• 5% 锁 1 年
• 35% 锁 4 年（2030年解锁）

<b>团队代币归属（Team Finance）</b>
总量：20%（40,520,000 ISC）
• 归属期：24 个月
• 首次释放：2026年5月20日
• 每月释放：~1,688,333 ISC

🔗 <a href="https://app.uncx.network/lockers/manage/lockers-v3">验证 LP 锁仓</a>
🔗 <a href="https://app.team.finance/token-vesting">验证团队归属</a>""",

    "锁定": """🔒 <b>ISC 锁仓信息</b>

流动性池：40% 已锁（UNCX）
团队代币：20% 已锁（Team Finance）

验证链接：
🔗 <a href="https://app.uncx.network">UNCX</a>
🔗 <a href="https://app.team.finance">Team Finance</a>""",

    "流动性": """💧 <b>ISC 流动性</b>

40% 总供应量已注入流动性池
• 5% 短期锁仓（1年）
• 35% 长期锁仓（4年，2030年解锁）

平台：PancakeSwap V3
交易对：ISC/USDT

💧 <a href="https://app.uncx.network/lockers/manage/lockers-v3">查看锁仓详情</a>""",

    "总量": """📊 <b>ISC 代币经济学</b>

总供应量：202,600,000 ISC
状态：固定，无通胀，永不增发

分配：
💧 流动性池 40%
👥 团队分配 20%（锁24个月）
🌍 社区/生态/营销 30%
🎁 APY 奖励池 10%

📄 详情见 /tokenomics 命令""",

    "供应": """📊 <b>ISC Supply</b>

Total: 202,600,000 ISC
Status: Fixed, no inflation

Allocation:
💧 Liquidity 40%
👥 Team 20% (locked 24mo)
🌍 Community 30%
🎁 APY Rewards 10%""",

    "团队": """👥 <b>ISC 团队</b>

由网络安全专家、AI 爱好者和 GameFi 开发者组成。

<b>团队承诺：</b>
✅ 所有前期成本由创始团队承担
✅ 20% 团队分配通过 Team Finance 锁仓 24 个月
✅ 无预挖、无隐藏分配、无后门

<b>营销钱包：</b>
<code>0xF8A408495941ea30451Da613dC846Dcae47890f0</code>

所有支出透明，每月报告发布于 X 和 Telegram。""",

    "创始人": """👥 <b>ISC 创始团队</b>

致力于构建安全且去中心化的数字未来。

核心承诺：
✅ 合约所有权永久放弃
✅ 第三方安全审计（TechRate）
✅ 流动性与团队代币长期锁仓
✅ 完全透明的链上运营

📄 <a href="{WHITEPAPER}">白皮书</a>""",

    "空投": """🎁 <b>ISC 空投计划</b>

<b>三阶段空投（10% / 35% / 55%）</b>

阶段1：持仓0天 → 1,000 ISC
阶段2：持仓15天 → 3,000 ISC  
阶段3：持仓30天 → 6,000 ISC

<b>反女巫保护：</b>
🛡️ 通过反女巫 Agent 自动筛选真实用户
🛡️ 多维度链上行为分析
🛡️ X 账号画像验证

⏳ 首次自动化空投：2026年Q3
📄 详情见 /roadmap 命令""",

    "airdrop": """🎁 <b>ISC Airdrop</b>

3-Stage Airdrop (10% / 35% / 55%):
• Stage 1: Day 0 → 1,000 ISC
• Stage 2: Day 15 → 3,000 ISC
• Stage 3: Day 30 → 6,000 ISC

Anti-Sybil Protection:
🛡️ Automated screening via Anti-Sybil Agent
🛡️ Multi-dimensional on-chain analysis
🛡️ X account verification

⏳ First automated airdrop: Q3 2026""",

    "NFT": """🎨 <b>ISC 纪念版动态 NFT</b>

总量：2,026 枚（纪念 2026 年）
类型：动态 SVG 动画
设计：基于 ISC 官方 Logo
支付：ISC 代币（2,026 ISC/枚）

<b>权益：</b>
🎮 GameFi 优先访问权
🎁 专属空投
🗳️ 治理投票加成

⏳ 铸造功能上线：2026年Q3
📄 详情见 /roadmap 命令""",

    "nft": """🎨 <b>ISC Commemorative NFT</b>

Supply: 2,026 NFTs (commemorating 2026)
Type: Dynamic SVG Animation
Price: 2,026 ISC per NFT

Benefits:
🎮 GameFi priority access
🎁 Exclusive airdrops
🗳️ Governance voting bonus

⏳ Minting: Q3 2026""",

    "质押": """🏦 <b>ISC APY 质押</b>

<b>APY 奖励池：10%</b>（20,260,000 ISC）

预计年化收益：5% - 15%
预计上线：2026年Q3

质押机制：
• 单币质押 ISC
• LP 流动性挖矿
• 锁仓时间越长，收益越高

⏳ 合约部署中，详见 /roadmap""",

    "staking": """🏦 <b>ISC Staking</b>

APY Rewards Pool: 10% (20,260,000 ISC)
Expected APY: 5% - 15%
Launch: Q3 2026

Options:
• Single-asset ISC staking
• LP liquidity mining
• Longer lock = higher yield

⏳ Contract under development""",

    "APY": """🏦 <b>ISC APY Rewards</b>

Pool Size: 10% of total supply
Expected Return: 5% - 15% APY
Launch: Q3 2026

📄 See /roadmap for details""",

    "路线图": """🗺️ <b>ISC 路线图</b>

✅ <b>已完成（2026年4月）</b>
• 合约部署 + 所有权放弃
• LP 锁仓 + 团队归属
• 官网 + 白皮书 v3.0
• TechRate 审计

⏳ <b>进行中（Q2 2026）</b>
• BSCScan Logo 申请
• NFT 合约开发
• GameFi 框架
• CEX/DEX 上线申请

📋 <b>计划中（Q3 2026）</b>
• NFT 铸造上线
• 社区任务系统
• 首次自动化空投
• GameFi Beta
• DAO 治理
• APY 质押

🚀 <b>未来（Q4 2026+）</b>
• 跨链部署
• 高级 GameFi
• RWA 集成

📄 完整路线图：/roadmap""",

    "roadmap": """🗺️ <b>ISC Roadmap</b>

✅ <b>Completed (Apr 2026)</b>
• Contract deployment
• Ownership renounced
• LP & team locks
• Website & whitepaper
• TechRate audit

⏳ <b>In Progress (Q2 2026)</b>
• BSCScan Logo
• NFT contract
• GameFi framework
• Exchange listings

📋 <b>Planned (Q3 2026)</b>
• NFT minting
• Community tasks
• First airdrop
• GameFi Beta
• DAO governance
• APY staking

🚀 <b>Future (Q4 2026+)</b>
• Cross-chain
• Tournaments
• RWA integration""",

    "白皮书": """📄 <b>ISC 白皮书</b>

版本：v3.0（2026年4月）
语言：英文 + 中文

内容：
• 项目概述与愿景
• 技术架构（UUPS 代理）
• 代币经济学
• 生态系统与应用场景
• 社区治理模型
• 安全审计报告
• 路线图

🔗 <a href="{WHITEPAPER}">icesnowcoin.org</a>""",

    "whitepaper": """📄 <b>ISC Whitepaper v3.0</b>

Languages: English + Chinese
Published: April 2026

Contents:
• Project overview
• Technical architecture
• Tokenomics
• Ecosystem
• Governance
• Security audit
• Roadmap

🔗 <a href="{WHITEPAPER}">icesnowcoin.org</a>""",

    "官网": """🌐 <b>ISC 官方网站</b>

地址：icesnowcoin.com

板块：
• 实时价格与数据
• 代币经济学
• 安全与透明度
• 生态系统
• 路线图
• 社区入口

🔗 <a href="{WEBSITE}">icesnowcoin.com</a>""",

    "website": """🌐 <b>ISC Official Website</b>

URL: icesnowcoin.com

Sections:
• Real-time price
• Tokenomics
• Security & transparency
• Ecosystem
• Roadmap
• Community

🔗 <a href="{WEBSITE}">Visit Website</a>""",

    "BSCScan": """🔍 <b>BSCScan 信息</b>

合约已验证：✅ 完全匹配
审计状态：✅ TechRate 通过
所有权：✅ 已放弃（零地址）

Logo 申请：⏳ 审核中（预计 1-3 个工作日）

🔗 <a href="{BSCSCAN_URL}">查看合约</a>""",

    "logo": """🎨 <b>BSCScan Logo</b>

Status: ⏳ Under review
Expected: 1-3 business days

Contract: ✅ Verified
Audit: ✅ TechRate passed
Ownership: ✅ Renounced

All requirements met. Waiting for BSCScan approval.

🔗 <a href="{BSCSCAN_URL}">View Contract</a>""",

    "税": """💰 <b>ISC 税率</b>

买入税：0%
卖出税：0%
转账税：0%

<b>滑点建议：</b>
• 普通交易：0.5% - 1%
• 大额交易：1% - 2%

⚠️ 注意：0.5% maxTxAmount 限制单笔最大交易量
（保护小持有者免受巨鲸抛售）""",

    "税率": """💰 <b>ISC Tax Rate</b>

Buy Tax: 0%
Sell Tax: 0%
Transfer Tax: 0%

<b>Slippage Recommendation:</b>
• Normal: 0.5% - 1%
• Large amounts: 1% - 2%

⚠️ Note: 0.5% maxTxAmount limit per transaction""",

    "滑点": """💰 <b>ISC 滑点设置</b>

由于 0.5% maxTxAmount 反巨鲸机制：

• 小额交易（< 500K ISC）：滑点 0.5%
• 中额交易（500K - 1M ISC）：滑点 1%
• 大额交易（接近 1M ISC）：滑点 1% - 2%

⚠️ 单笔上限：1,013,000 ISC（总供应量的 0.5%）""",

    "放弃": """🔐 <b>合约所有权放弃</b>

<b>状态：</b>✅ 已永久放弃，不可逆

<b>详情：</b>
• 日期：2026年4月19日 19:41 UTC
• 交易哈希：0x983aa29b...9e09d7c
• 当前所有者：0x000...000（零地址）

<b>意义：</b>
✅ 无管理员权限
✅ 无法修改合约规则
✅ 无法增发代币
✅ 无法冻结账户

🔗 <a href="{BSCSCAN_URL}">链上验证</a>""",

    "renounce": """🔐 <b>Ownership Renounced</b>

Status: ✅ Permanently renounced

Details:
• Date: April 19, 2026
• Tx Hash: 0x983aa29b...9e09d7c
• Current Owner: 0x000...000

Implications:
✅ No admin privileges
✅ Cannot modify rules
✅ Cannot mint new tokens
✅ Cannot freeze accounts

🔗 <a href="{BSCSCAN_URL}">Verify on-chain</a>""",

    "所有权": """🔐 <b>合约所有权</b>

已放弃 → 零地址
状态：不可逆

这意味着：
✅ 项目完全去中心化
✅ 社区治理
✅ 代码即法律

🔗 <a href="{BSCSCAN_URL}">验证</a>""",
}

# 防骗关键词
SCAM_KEYWORDS = ["私钥", "private key", "助记词", "seed phrase", "seed", "转账给我", "send me", "打钱", "给我转", "充值", "investment plan", "guaranteed return", "翻倍", "保本"]

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
                                "change24h": pair.get("priceChange", {}).get("h24", "N/A"),
                                "volume24h": pair.get("volume", {}).get("h24", "N/A"),
                                "liquidity": pair.get("liquidity", {}).get("usd", "N/A"),
                                "fdv": pair.get("fdv", "N/A"),
                            },
                            "timestamp": now
                        }
                        return price_cache["data"]
    except Exception as e:
        logger.error(f"获取价格失败: {e}")

    return None


# ==================== 命令处理器 ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 命令"""
    user = update.effective_user
    user_name = user.first_name if user else "社区成员"

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
/faq - 常见问题解答
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
    """/price 命令"""
    msg = await update.message.reply_text("⏳ 正在获取 ISC 实时价格...")

    data = await fetch_price()

    if data:
        price = data.get("price", "N/A")
        change = data.get("change24h", "N/A")
        volume = data.get("volume24h", "N/A")
        liquidity = data.get("liquidity", "N/A")
        fdv = data.get("fdv", "N/A")

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
    """/contract 命令"""
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
    """/tokenomics 命令"""
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
    """/security 命令"""
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
    """/roadmap 命令"""
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


async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/faq 命令 - 常见问题菜单"""
    text = f"""
❓ <b>ISC 常见问题 (FAQ)</b>

<b>快速提问指南：</b>
直接在群里或私聊输入关键词，Bot 会自动回复：

<b>🔍 基础信息</b>
• "合约" / "地址" → 合约地址
• "价格" / "price" → 价格查询指引
• "买" / "购买" / "swap" → 购买教程
• "总量" / "供应" → 代币经济学

<b>🛡️ 安全相关</b>
• "审计" / "audit" / "安全" → 审计报告
• "锁仓" / "锁定" / "流动性" → 锁仓详情
• "放弃" / "renounce" / "所有权" → 所有权状态
• "税" / "税率" / "滑点" → 0% 税率说明

<b>🚀 项目进展</b>
• "路线图" / "roadmap" → 发展路线图
• "空投" / "airdrop" → 空投计划
• "NFT" / "nft" → 纪念版 NFT
• "质押" / "staking" / "APY" → 质押收益
• "BSCScan" / "logo" → Logo 申请状态

<b>📄 文档</b>
• "白皮书" / "whitepaper" → 白皮书链接
• "官网" / "website" → 官网链接
• "团队" / "创始人" → 团队信息

<b>💬 社区</b>
• "群组" / "讨论" → {TELEGRAM_CHAT}
• "频道" / "公告" → {TELEGRAM_GROUP}

<b>⚠️ 防骗提醒</b>
Bot 会自动检测"私钥"、"助记词"、"转账给我"等诈骗关键词并发出警告。

<b>🤖 完整命令列表：</b>
/start /price /contract /tokenomics /security /roadmap /links /help
    """

    keyboard = [
        [InlineKeyboardButton("🌐 官网", url=WEBSITE),
         InlineKeyboardButton("📄 白皮书", url=WHITEPAPER)],
        [InlineKeyboardButton("💬 讨论群组", url=TELEGRAM_CHAT),
         InlineKeyboardButton("📢 公告频道", url=TELEGRAM_GROUP)],
        [InlineKeyboardButton("🔄 PancakeSwap", url=PANCAKESWAP_URL),
         InlineKeyboardButton("🔍 BSCScan", url=BSCSCAN_URL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/links 命令"""
    keyboard = [
        [InlineKeyboardButton("🌐 官网", url=WEBSITE),
         InlineKeyboardButton("📄 白皮书", url=WHITEPAPER)],
        [InlineKeyboardButton("🐦 X/Twitter", url=X_TWITTER),
         InlineKeyboardButton("💬 讨论群组", url=TELEGRAM_CHAT)],
        [InlineKeyboardButton("📢 公告频道", url=TELEGRAM_GROUP),
         InlineKeyboardButton("💻 GitHub", url=GITHUB)],
        [InlineKeyboardButton("🔄 PancakeSwap", url=PANCAKESWAP_URL),
         InlineKeyboardButton("🔍 BSCScan", url=BSCSCAN_URL)],
        [InlineKeyboardButton("📊 DEXScreener", url=f"https://dexscreener.com/bsc/{ISC_CONTRACT}"),
         InlineKeyboardButton("🛡️ 审计报告", url=AUDIT_REPORT)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔗 <b>ISC 官方链接汇总</b>

点击下方按钮快速访问：",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help 命令"""
    text = f"""
❓ <b>ISC Bot 帮助中心</b>

<b>可用命令：</b>
/start - 欢迎语与项目介绍
/price - 查询 ISC 实时价格
/contract - 合约详情与链上链接
/tokenomics - 代币经济学详情
/security - 安全与审计信息
/roadmap - 项目路线图
/faq - 常见问题解答（含关键词指南）
/links - 官方链接汇总
/help - 显示此帮助信息

<b>关键词自动回复：</b>
直接输入关键词，Bot 会自动回答：
合约、价格、买、审计、锁仓、总量、团队、空投、NFT、质押、路线图、白皮书、官网、BSCScan、税、放弃

<b>常见问题：</b>

<b>Q: ISC 是什么？</b>
A: Ice Snow Coin (ISC) 是一个 AI 驱动的 GameFi + NFT 生态系统，部署在币安智能链上。

<b>Q: 合约安全吗？</b>
A: ✅ 合约所有权已永久放弃。✅ TechRate 安全审计通过（21项检查）。✅ 40% LP 已锁仓，20% 团队代币已锁仓。

<b>Q: 如何购买 ISC？</b>
A: 通过 PancakeSwap 交易，详见"买"关键词回复。

<b>Q: 总供应量是多少？会增发吗？</b>
A: 202,600,000 ISC，固定无通胀，永不增发。

<b>Q: 团队代币什么时候解锁？</b>
A: 团队 20% 分配已通过 Team Finance 锁仓 24 个月，从 2026年5月20日 开始线性释放。

<b>⚠️ 安全提醒：</b>
• 唯一合约地址：<code>{ISC_CONTRACT}</code>
• 警惕假冒代币和钓鱼网站
• 官方不会私信索要私钥或助记词
• 所有公告以官方 X/Telegram 为准

<b>💬 社区支持：</b>
讨论群组：{TELEGRAM_CHAT}
公告频道：{TELEGRAM_GROUP}
    """

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


# ==================== FAQ 关键词处理器 ====================

async def keyword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息中的关键词"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    chat_type = update.message.chat.type

    # 防骗检测
    for scam_word in SCAM_KEYWORDS:
        if scam_word.lower() in text:
            await update.message.reply_text(
                f"""🚨 <b>防骗警告</b>

检测到敏感词：<code>{scam_word}</code>

⚠️ <b>安全提醒：</b>
• 官方永远不会索要您的私钥或助记词
• 官方永远不会要求您转账到某个地址
• 警惕假冒管理员和钓鱼链接
• 所有官方活动以 X/Telegram 公告为准

<b>唯一合约地址：</b>
<code>{ISC_CONTRACT}</code>

如有疑问，请联系官方社区管理员。
""",
                parse_mode="HTML"
            )
            return

    # FAQ 关键词匹配
    matched = False
    for keyword, response in FAQ_KEYWORDS.items():
        if keyword.lower() in text:
            # 替换变量
            response = response.replace("{ISC_CONTRACT}", ISC_CONTRACT)
            response = response.replace("{BSCSCAN_URL}", BSCSCAN_URL)
            response = response.replace("{PANCAKESWAP_URL}", PANCAKESWAP_URL)
            response = response.replace("{WEBSITE}", WEBSITE)
            response = response.replace("{WHITEPAPER}", WHITEPAPER)
            response = response.replace("{AUDIT_REPORT}", AUDIT_REPORT)
            response = response.replace("{TELEGRAM_CHAT}", TELEGRAM_CHAT)
            response = response.replace("{TELEGRAM_GROUP}", TELEGRAM_GROUP)

            await update.message.reply_text(
                response,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            matched = True
            break

    # 如果没有匹配到关键词，不做任何回复（避免刷屏）
    if not matched:
        logger.info(f"未匹配关键词: {text[:50]}")


# ==================== 新成员欢迎处理器 ====================

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """新成员进群自动欢迎"""
    if not update.chat_member:
        return

    new_member = update.chat_member.new_chat_member
    old_member = update.chat_member.old_chat_member

    # 只处理新加入的成员
    if new_member.status == ChatMember.MEMBER and old_member.status == ChatMember.LEFT:
        user = new_member.user
        user_name = user.first_name if user.first_name else "新成员"

        welcome_text = f"""
🎉 <b>欢迎 {user_name} 加入 ISC 社区！</b>

❄️ <b>Ice Snow Coin (ISC)</b>
AI 驱动的 GameFi + NFT 生态系统

📌 <b>快速开始：</b>
• 发送 /start 查看项目介绍
• 发送 /price 查询实时价格
• 发送 /faq 查看常见问题
• 直接输入关键词（如"合约"、"审计"）获取信息

<b>合约地址：</b>
<code>{ISC_CONTRACT}</code>

⚠️ <b>安全提醒：</b>
• 警惕假冒代币和钓鱼网站
• 官方不会私信索要私钥或助记词
• 务必核对合约地址

💬 <b>社区链接：</b>
• 讨论群组：{TELEGRAM_CHAT}
• 公告频道：{TELEGRAM_GROUP}
• X/Twitter：{X_TWITTER}
        """

        keyboard = [
            [InlineKeyboardButton("📄 白皮书", url=WHITEPAPER)],
            [InlineKeyboardButton("🔄 PancakeSwap 交易", url=PANCAKESWAP_URL)],
            [InlineKeyboardButton("🔍 BSCScan", url=BSCSCAN_URL)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                chat_id=update.chat_member.chat.id,
                text=welcome_text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"发送欢迎消息失败: {e}")


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
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # 命令处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("contract", contract_command))
    application.add_handler(CommandHandler("tokenomics", tokenomics_command))
    application.add_handler(CommandHandler("security", security_command))
    application.add_handler(CommandHandler("roadmap", roadmap_command))
    application.add_handler(CommandHandler("faq", faq_command))
    application.add_handler(CommandHandler("links", links_command))
    application.add_handler(CommandHandler("help", help_command))

    # 新成员欢迎
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    # 关键词处理器（处理所有文本消息，但排除命令）
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_handler))

    # 错误处理
    application.add_error_handler(error_handler)

    logger.info("🤖 ISC Bot v2.0 已启动！FAQ + 防骗 + 欢迎功能就绪")
    print("🤖 ISC Bot v2.0 已启动！")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
