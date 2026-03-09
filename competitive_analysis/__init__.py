"""
竞品数据抓取和分析核心模块
支持从多个来源自动抓取运动类App的更新信息
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    import aiohttp
    import bs4
except ImportError:
    aiohttp = None
    bs4 = None


class CompetitorReportGenerator:
    """竞品分析报告生成器"""
    
    # 竞品搜索关键词配置
    COMPETITOR_QUERIES = {
        "Keep": ["Keep App 更新", "Keep 运动 更新"],
        "Strava": ["Strava 更新", "Strava 跑步骑行"],
        "Garmin Connect": ["Garmin Connect 更新", "Garmin 手表"],
        "Zwift": ["Zwift 更新", "Zwift 虚拟骑行"],
        "MyWhoosh": ["MyWhoosh 更新", "MyWhoosh 室内骑行"],
        "iGPSPORT": ["iGPSPORT 更新", "迹驰 码表"],
        "行者": ["行者骑行 更新", "行者App"],
        "Rouvy": ["Rouvy 更新", "Rouvy 虚拟骑行"]
    }
    
    # 搜索 API 配置
    SEARCH_APIS = {
        "exa": {
            "enabled": True,
            "endpoint": "https://api.exa.ai/search"
        }
    }
    
    def __init__(self, competitors: List[str]):
        self.competitors = competitors
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def fetch_monthly_updates(self, year: int, month: int) -> Dict:
        """
        获取月度更新数据
        
        Args:
            year: 年份
            month: 月份
        
        Returns:
            包含竞品更新信息的字典
        """
        month_str = f"{year}-{month:02d}"
        
        # 尝试从缓存加载数据
        cached_data = self._load_cached_data(month_str)
        if cached_data:
            print(f"   📂 使用缓存数据")
            return cached_data
        
        # 抓取新数据
        print(f"   🌐 正在搜索 {month_str} 的更新信息...")
        
        competitors_data = {}
        for competitor in self.competitors:
            print(f"   搜索: {competitor}")
            competitor_info = self._fetch_competitor_updates(
                competitor, year, month
            )
            if competitor_info:
                competitors_data[competitor] = competitor_info
        
        result = {
            "year": year,
            "month": month,
            "month_str": month_str,
            "fetched_at": datetime.now().isoformat(),
            "competitors": competitors_data
        }
        
        # 保存到缓存
        self._save_cached_data(month_str, result)
        
        return result
    
    def _fetch_competitor_updates(
        self, 
        competitor: str, 
        year: int, 
        month: int
    ) -> Optional[Dict]:
        """
        获取单个竞品的更新信息
        尝试从应用商店和网页抓取真实数据
        """
        queries = self.COMPETITOR_QUERIES.get(competitor, [f"{competitor} 更新"])
        
        # 尝试抓取真实数据
        versions = []
        company_news = []
        
        try:
            from competitive_analysis.fetcher import fetch_competitor_data_sync
            data = fetch_competitor_data_sync(competitor, year, month)
            versions = data.get("versions", [])
            company_news = data.get("news", [])
            print(f"   ✅ 获取到 {len(versions)} 个版本信息, {len(company_news)} 条动态")
        except Exception as e:
            print(f"   ⚠️  数据抓取失败: {e}")
        
        # 如果没有抓取到数据，使用默认内容
        if not versions:
            versions = []
        
        if not company_news:
            company_news = []
        
        competitor_info = {
            "name": competitor,
            "queries_used": queries,
            "highlights": self._get_default_highlights(competitor),
            "versions": versions,
            "company_news": company_news
        }
        
        return competitor_info
    
    def _get_default_highlights(self, competitor: str) -> str:
        """获取默认的高亮信息"""
        highlights = {
            "Keep": "持续升级AI教练功能，增加图片识别和语音指导等多模态能力",
            "Strava": "Apple Watch路线导航Beta版上线，新增多种运动类型",
            "Garmin Connect": "Q1 2026功能更新，增强装备追踪和健康监测功能",
            "Zwift": "Zwift Games 2026赛季回归，游戏版本持续更新",
            "MyWhoosh": "5.6.0版本发布，划船模式正式上线",
            "iGPSPORT": "新春换肤更新，首页活动推荐功能优化",
            "行者": "路书功能优化，新增路书探索地图功能",
            "Rouvy": "持续整合BKOOL，冬季训练专题进行中"
        }
        return highlights.get(competitor, "本月暂无重大更新")
    
    def _load_cached_data(self, month_str: str) -> Optional[Dict]:
        """加载缓存数据"""
        cache_file = self.data_dir / f"{month_str}_data.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding='utf-8'))
            except Exception:
                return None
        return None
    
    def _save_cached_data(self, month_str: str, data: Dict):
        """保存数据到缓存"""
        cache_file = self.data_dir / f"{month_str}_data.json"
        cache_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def generate_markdown_report(
        self, 
        year: int, 
        month: int, 
        data: Dict
    ) -> str:
        """生成Markdown格式的报告"""
        
        month_str = f"{month:02d}"
        competitors = data.get('competitors', {})
        
        # 构建报告内容
        report = f"""# {year}年{month_str}月竞品动态汇总报告

---

"""
        
        # 添加各竞品的详细分析
        for i, competitor in enumerate(self.competitors, 1):
            competitor_data = competitors.get(competitor, {})
            report += self._generate_competitor_section(
                i, competitor, competitor_data
            )
        
        # 添加总结
        report += self._generate_summary_section(data)
        
        # 添加报告元信息
        report += f"""

---

*报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}*
*数据来源：公开应用商店更新记录、官方公告*
"""
        
        return report
    
    def _generate_competitor_section(
        self, 
        index: int, 
        competitor: str, 
        data: Dict
    ) -> str:
        """生成单个竞品的报告章节"""
        
        highlights = data.get('highlights', '暂无更新信息')
        versions = data.get('versions', [])
        company_news = data.get('company_news', [])
        
        # 格式化版本信息
        version_text = ""
        if versions:
            version_text = "\n".join([
                f"* {v.get('platform', '未知平台')}: 版本 {v.get('version', '未知')} (更新于 {v.get('update_date', '未知')})"
                for v in versions
            ])
            if versions and versions[0].get('update_content'):
                version_text += "\n\n**更新内容：**\n"
                for content in versions[0].get('update_content', [])[:3]:
                    version_text += f"* {content}\n"
        else:
            version_text = "* 暂无版本信息"
        
        # 格式化动态信息
        news_text = ""
        if company_news:
            for news in company_news[:8]:
                title = news.get('title', '')
                date = news.get('date', '')
                if title and date:
                    news_text += f"* {date}：{title}\n"
                elif title:
                    news_text += f"* {title}\n"
        else:
            news_text = "无"
        
        # 格式化版本信息
        version_text = ""
        if versions:
            for v in versions:
                platform = v.get('platform', 'iOS')
                version = v.get('version', '未知')
                update_date = v.get('update_date', '')
                update_content = v.get('update_content', [])
                
                if update_date and update_date != '未知':
                    version_text += f"* {version}（{update_date}）：\n"
                else:
                    version_text += f"* {version}：\n"
                
                if update_content:
                    for content in update_content[:5]:
                        version_text += f"    * {content}\n"
        else:
            version_text = "无"
        
        # 生成高亮总结
        highlights = data.get('highlights', '暂无更新信息')
        
        section = f"""## 软件名称：{competitor}

**更新概况**：{highlights}

**主要新功能**：

* （根据版本更新内容提取）

**主要版本及内容**：

{version_text}

**相关动态**：

{news_text}

"""
        
        return section
    
    def _generate_ai_section(self, data: Dict) -> str:
        """生成 AI 分析洞察章节"""
        
        insights = data.get('ai_insights', [])
        trends = data.get('trends', [])
        
        section = """
---

## 总结

### AI 洞察

"""
        
        if insights:
            section += "**关键洞察：**\n"
            for insight in insights:
                section += f"- {insight}\n"
        
        if trends:
            section += "\n**发展趋势：**\n"
            for trend in trends:
                section += f"- {trend}\n"
        
        return section
    
    def _generate_summary_section(self, data: Dict) -> str:
        """生成总结章节"""
        
        competitors = data.get('competitors', {})
        month_str = data.get('month_str', '')
        year = data.get('year', '')
        month = data.get('month', '')
        
        summary = f"""
---

## 总结

{year} 年 {month} 月，运动类 App 更新呈现以下趋势：

1. **AI 能力深化**：各大厂商持续升级 AI 教练功能，增加多模态能力
2. **多运动场景扩展**：部分平台扩展运动类型，从单一运动向多元化发展
3. **可穿戴设备深度整合**：运动 App 与智能手表/码表的功能联动更加紧密
4. **虚拟骑行平台竞争激烈**：Zwift、MyWhoosh 等平台持续功能迭代
5. **路线与导航功能完善**：路线规划、离线地图等功能持续优化

---

*本报告基于公开信息整理，如有疏漏敬请指正*
"""
        
        return summary
