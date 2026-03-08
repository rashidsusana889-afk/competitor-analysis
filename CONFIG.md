# ⚙️ 配置说明

## GitHub Secrets 配置

在 GitHub 仓库的 Settings → Secrets and variables → Actions 中配置以下 secrets:

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API Key，用于 AI 分析功能 |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token (repo 权限) |
| `DISCORD_WEBHOOK` | ❌ | Discord Webhook URL |
| `SLACK_WEBHOOK` | ❌ | Slack Incoming Webhook URL |
| `EMAIL_SMTP_*` | ❌ | 邮件通知配置 |

## GitHub Actions 配置

### 工作流触发条件

1. **定时触发**: 每月最后一天 18:00 (北京时间)
2. **手动触发**: GitHub 网页上手动运行
3. **API 触发**: 调用 GitHub REST API

### 输入参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `month` | string | 当前年月 | 目标月份 (YYYY-MM) |
| `competitors` | string | (默认列表) | 竞品列表，逗号分隔 |
| `ai_analysis` | boolean | true | 是否启用 AI 分析 |

## 竞品搜索配置

在 `competitive_analysis/__init__.py` 中可以修改搜索关键词:

```python
COMPETITOR_QUERIES = {
    "Keep": ["Keep App 更新", "Keep 运动 更新"],
    # 添加更多...
}
```

## 报告输出配置

生成的报告保存在:
- Markdown: `reports/YYYY年MM月运动类App竞品更新分析报告.md`
- PDF: `reports/pdf/YYYY年MM月运动类App竞品更新分析报告.pdf`

## 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
pytest tests/
```

### 本地生成报告

```bash
python scripts/generate_report.py --month 2026-02 --ai-analysis true
```

## 常见问题

### Q: 如何修改默认竞品列表?
A: 在触发时修改 `competitors` 参数，或修改 `scripts/generate_report.py` 中的默认值。

### Q: AI 分析失败了怎么办?
A: 检查 `OPENAI_API_KEY` 是否正确配置，报告仍会生成但不含 AI 洞察。

### Q: 如何只生成报告不发送通知?
A: 不配置通知相关的 secrets 即可。
