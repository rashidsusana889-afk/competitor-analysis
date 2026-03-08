# 📊 竞品分析报告自动生成工具

定时自动生成运动类App竞品分析报告，支持手动和定时触发。

## ✨ 功能特性

- 🤖 **AI 智能分析** - 使用 GPT-4 分析竞品动态和行业趋势
- ⏰ **定时执行** - 每月最后一天自动生成报告
- 🎯 **手动触发** - 支持网页和 API 手动触发
- 📄 **多格式输出** - Markdown + PDF 双格式
- 🔔 **多渠道通知** - Discord / Slack / Email 通知

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/competitor-analysis.git
cd competitor-analysis
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# OpenAI API (AI 分析功能)
OPENAI_API_KEY=sk-...

# GitHub Token (用于触发工作流)
GITHUB_TOKEN=ghp_...

# 通知配置 (可选)
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
SLACK_WEBHOOK=https://hooks.slack.com/...
```

### 3. 本地测试

```bash
pip install -r requirements.txt
python scripts/generate_report.py --month 2026-02
```

## 📖 使用方式

### 定时触发

每月最后一天北京时间 18:00 自动执行。

### 网页触发

1. 启用 GitHub Pages: Settings → Pages → Source: main branch /public folder
2. 访问 `https://your-username.github.io/competitor-analysis/trigger.html`
3. 填写参数，点击触发

### API 触发

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/OWNER/REPO/dispatches" \
  -d '{
    "event_type": "manual-report-trigger",
    "client_payload": {
      "month": "2026-02",
      "competitors": "Keep,Strava,Garmin",
      "ai_analysis": true
    }
  }'
```

## 📁 项目结构

```
.
├── .github/workflows/     # GitHub Actions 配置
├── scripts/              # Python 脚本
├── competitive_analysis/ # 竞品分析核心模块
├── ai_analyzer/         # AI 分析模块
├── public/              # 网页触发页面
├── reports/             # 生成的报告
└── requirements.txt     # Python 依赖
```

## 🔧 配置说明

详见 [CONFIG.md](CONFIG.md)

## 📝 竞品列表

默认监控的竞品:
- Keep
- Strava
- Garmin Connect
- Zwift
- MyWhoosh
- iGPSPORT
- 行者
- Rouvy

可在触发时自定义竞品列表。

## 📄 许可证

MIT License
