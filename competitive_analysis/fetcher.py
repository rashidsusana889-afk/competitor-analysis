#!/usr/bin/env python3
"""
竞品数据抓取模块
从应用商店和网页抓取真实的版本信息和动态内容
"""

import re
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    import aiohttp
    import bs4
    from bs4 import BeautifulSoup
except ImportError:
    aiohttp = None
    bs4 = None
    BeautifulSoup = None


class DataFetcher:
    """数据抓取器"""
    
    # 应用商店 URL 模板
    APP_STORE_URLS = {
        "Keep": {
            "ios": "https://apps.apple.com/cn/app/keep-ai-%E8%BF%90%E5%8A%A8%E6%95%99%E7%BB%83/id952694580",
            "android": "https://play.google.com/store/apps/details?id=com.gotokeep.keep"
        },
        "Strava": {
            "ios": "https://apps.apple.com/cn/app/strava-%E8%B7%91%E6%AD%A5%E9%AA%8E%E9%AA%8E%E8%A1%8C/id426826291",
            "android": "https://play.google.com/store/apps/details?id=com.strava"
        },
        "Garmin Connect": {
            "ios": "https://apps.apple.com/cn/app/garmin-connect/id583723403",
            "android": "https://play.google.com/store/apps/details?id=com.garmin.android.apps.connectmobile"
        },
        "行者": {
            "ios": "https://apps.apple.com/cn/app/%E8%A1%8C%E8%80%85%E6%88%B7%E5%A4%96-%E9%AA%91%E8%A1%8C%E5%BE%92%E6%AD%A5%E8%B7%91%E6%AD%A5%E5%B7%A5%E5%85%B7/id779325629",
            "android": "https://play.google.com/store/apps/details?id=im.xingzhe"
        },
        "Zwift": {
            "ios": "https://apps.apple.com/cn/app/zwift/id1459937296",
            "android": "https://play.google.com/store/apps/details?id=com.zwift.zwift"
        },
        "MyWhoosh": {
            "ios": "https://apps.apple.com/cn/app/mywhoosh/id647374337",
            "android": "https://play.google.com/store/apps/details?id=com.mywhoosh.whooshgame"
        },
        "iGPSPORT": {
            "android": "https://www.igpsport.cn/"
        }
    }
    
    # 官网 URL
    OFFICIAL_WEBSITES = {
        "Keep": "https://www.keep.com/",
        "Strava": "https://www.strava.com/",
        "Garmin Connect": "https://www.garmin.com/en-US/connect/",
        "Zwift": "https://www.zwift.com/",
        "MyWhoosh": "https://mywhoosh.com/",
        "iGPSPORT": "https://www.igpsport.cn/",
        "行者": "https://www.xingzhe.com/",
        "Rouvy": "https://www.rouvy.com/"
    }
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    async def fetch_all(self, competitor: str, year: int, month: int) -> Dict:
        """获取竞品的所有数据"""
        tasks = [
            self.fetch_app_version(competitor),
            self.fetch_news(competitor, year, month)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        version_info = results[0] if not isinstance(results[0], Exception) else {}
        news_info = results[1] if not isinstance(results[1], Exception) else {}
        
        return {
            "versions": version_info,
            "news": news_info
        }
    
    async def fetch_app_version(self, competitor: str) -> List[Dict]:
        """从应用商店获取版本信息"""
        urls = self.APP_STORE_URLS.get(competitor, {})
        versions = []
        
        for platform, url in urls.items():
            try:
                version_info = await self._fetch_single_url(url, platform)
                if version_info and version_info.get('version') and version_info.get('version') != '未知':
                    versions.append(version_info)
            except Exception as e:
                print(f"   ⚠️  获取 {competitor} {platform} 版本失败: {e}")
        
        # 如果直接抓取失败，尝试搜索获取
        if not versions:
            try:
                search_versions = await self._search_app_version(competitor)
                versions.extend(search_versions)
            except Exception as e:
                print(f"   ⚠️  搜索版本失败: {e}")
        
        return versions
    
    async def _search_app_version(self, competitor: str) -> List[Dict]:
        """通过搜索获取版本信息和日期"""
        import requests
        
        versions = []
        
        # 使用 App Store 搜索 API 获取版本和发布日期
        search_url = f"https://itunes.apple.com/search?term={competitor}&entity=software&limit=10"
        
        try:
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for result in data.get('results', [])[:3]:
                    version = result.get('version', '未知')
                    release_date = result.get('currentVersionReleaseDate', '')
                    
                    # 格式化日期
                    if release_date:
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(release_date[:10], '%Y-%m-%d')
                            release_date = date_obj.strftime('%Y-%m-%d')
                        except:
                            release_date = release_date[:10]
                    else:
                        release_date = "未知"
                    
                    versions.append({
                        "platform": "iOS",
                        "url": result.get('trackViewUrl', ''),
                        "version": version,
                        "update_date": release_date,
                        "update_content": []
                    })
        except Exception as e:
            print(f"   ⚠️  搜索版本失败: {e}")
        
        # 同时搜索 Google Play 获取版本
        return versions
    
    async def _fetch_single_url(self, url: str, platform: str) -> Optional[Dict]:
        """抓取单个 URL"""
        if not aiohttp:
            return None
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._parse_version(html, platform, url)
            except Exception as e:
                print(f"   ⚠️  请求失败: {url} - {e}")
        
        return None
    
    def _parse_version(self, html: str, platform: str, url: str) -> Dict:
        """解析版本信息"""
        result = {
            "platform": platform,
            "url": url,
            "version": "未知",
            "update_date": "未知",
            "update_content": []
        }
        
        if not BeautifulSoup:
            return result
        
        soup = BeautifulSoup(html, 'html.parser')
        
        if 'apps.apple.com' in url:
            # App Store - 尝试多种选择器
            version_elem = (
                soup.find('p', class_='whats-new__latest__version') or
                soup.find('dd', class_='information-list__item__definition') or
                soup.find(text=re.compile(r'版本|Version')) 
            )
            if version_elem:
                if hasattr(version_elem, 'get_text'):
                    result["version"] = version_elem.get_text(strip=True)
                else:
                    result["version"] = str(version_elem)
            
            # 更新内容 - 尝试多种选择器
            whats_new = soup.find('div', class_='whats-new__latest__content')
            if not whats_new:
                whats_new = soup.find('div', {'data-testid': 'whats-new'})
            if whats_new:
                items = whats_new.find_all(['p', 'li'])
                result["update_content"] = [item.get_text(strip=True) for item in items[:5]]
        
        elif 'play.google.com' in url:
            # Google Play
            version_elem = soup.find('span', itemprop='softwareVersion')
            if not version_elem:
                version_elem = soup.find(text=re.compile(r'当前版本|Current Version'))
            if version_elem:
                if hasattr(version_elem, 'get_text'):
                    result["version"] = version_elem.get_text(strip=True)
                else:
                    result["version"] = str(version_elem)
            
            # 更新内容
            recent_changes = soup.find('div', itemprop='recentChanges')
            if not recent_changes:
                recent_changes = soup.find(text=re.compile(r'最近更新|Recent Changes'))
            if recent_changes:
                if hasattr(recent_changes, 'find_all'):
                    items = recent_changes.find_all(['p', 'li'])
                    result["update_content"] = [item.get_text(strip=True) for item in items[:5]]
        
        return result
    
    async def fetch_news(self, competitor: str, year: int, month: int) -> List[Dict]:
        """从网页获取动态新闻"""
        news_list = []
        
        # 使用搜索获取新闻
        news_items = await self._search_news(competitor, year, month)
        news_list.extend(news_items)
        
        # 去重并按日期排序
        seen = set()
        unique_news = []
        for news in news_list:
            key = news.get('title', '')[:30]  # 基于标题去重
            if key not in seen:
                seen.add(key)
                unique_news.append(news)
        
        return unique_news[:15]  # 限制返回数量
    
    async def _search_news(self, competitor: str, year: int, month: int) -> List[Dict]:
        """搜索新闻 - 使用 DuckDuckGo HTML 搜索"""
        import requests
        import re
        
        news_list = []
        month_str = f"{year}-{month:02d}"
        
        # 搜索关键词 - 更精确的搜索
        keywords = [
            f"{competitor} App {year}年{month:02d}月 更新",
            f"{competitor} {year}年{month}月 新功能 发布",
            f"{competitor} fitness app {month} 2026 update"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for keyword in keywords[:2]:
            try:
                url = "https://html.duckduckgo.com/html/"
                data = {"q": keyword, "b": ""}
                
                response = requests.post(url, data=data, headers=headers, timeout=15)
                if response.status_code == 200:
                    html = response.text
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 解析搜索结果
                    for result in soup.find_all('a', class_='result__a')[:8]:
                        title = result.get_text(strip=True)
                        if title and len(title) > 8:
                            # 尝试从标题中提取日期
                            date_str = month_str  # 默认使用目标月份
                            desc = ""
                            
                            # 查找父元素中的日期
                            parent = result.find_parent('div', class_='result__body')
                            if parent:
                                # 查找日期元素
                                date_elem = parent.find('span', class_='result__date')
                                if date_elem:
                                    date_text = date_elem.get_text(strip=True)
                                    # 解析日期
                                    date_match = re.search(r'(\d{1,2})\s*(月|/|-)\s*(\d{1,2})', date_text)
                                    if date_match:
                                        date_str = f"{year}-{int(date_match.group(1)):02d}-{int(date_match.group(3)):02d}"
                                
                                # 获取描述
                                desc_elem = parent.find('a', class_='result__snippet')
                                if desc_elem:
                                    desc = desc_elem.get_text(strip=True)
                            
                            news_list.append({
                                "title": title[:100],  # 限制标题长度
                                "description": desc[:200] if desc else "",
                                "date": date_str,
                                "source": competitor
                            })
            except Exception as e:
                print(f"   ⚠️ 搜索失败: {keyword[:20]}...")
        
        return news_list
    
    async def _fetch_website_news(self, url: str, competitor: str) -> List[Dict]:
        """从官网抓取新闻"""
        if not aiohttp:
            return []
        
        news_list = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html = await response.text()
                        news_list = self._parse_website_news(html, competitor)
        except Exception as e:
            print(f"   ⚠️  抓取官网失败: {url}")
        
        return news_list
    
    def _parse_website_news(self, html: str, competitor: str) -> List[Dict]:
        """解析官网新闻"""
        news_list = []
        
        if not BeautifulSoup:
            return news_list
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试找到新闻列表
        news_elements = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'news|blog|update|new', re.I))
        
        for elem in news_elements[:5]:
            title_elem = elem.find(['h2', 'h3', 'h4', 'a'])
            date_elem = elem.find(['time', 'span', 'p'], class_=re.compile(r'date|time', re.I))
            
            if title_elem:
                news_list.append({
                    "title": title_elem.get_text(strip=True),
                    "date": date_elem.get_text(strip=True) if date_elem else "",
                    "source": competitor
                })
        
        return news_list


class WebSearchFetcher:
    """网页搜索数据抓取器"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    async def search(self, keyword: str, num_results: int = 10) -> List[Dict]:
        """
        搜索关键词
        
        实际使用时需要接入搜索 API，例如:
        - SerpAPI (Google)
        - Bing Search API
        - Exa.ai
        - DuckDuckGo
        """
        
        # 尝试使用 DuckDuckGo 搜索
        try:
            return await self._search_duckduckgo(keyword, num_results)
        except Exception as e:
            print(f"   ⚠️  搜索失败: {e}")
            return []
    
    async def _search_duckduckgo(self, keyword: str, num_results: int) -> List[Dict]:
        """使用 DuckDuckGo 搜索"""
        if not aiohttp:
            return []
        
        results = []
        url = "https://html.duckduckgo.com/html/"
        data = {"q": keyword, "b": str(num_results)}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        results = self._parse_ddg_results(html)
        except Exception as e:
            print(f"   ⚠️  DuckDuckGo 搜索失败: {e}")
        
        return results
    
    def _parse_ddg_results(self, html: str) -> List[Dict]:
        """解析 DuckDuckGo 搜索结果"""
        results = []
        
        if not BeautifulSoup:
            return results
        
        soup = BeautifulSoup(html, 'html.parser')
        
        for result in soup.find_all('a', class_='result__a'):
            title = result.get_text(strip=True)
            url = result.get('href', '')
            
            # 找到描述
            desc_elem = result.find_parent('div', class_='result__body').find('a', class_='result__snippet') if result.find_parent('div', class_='result__body') else None
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            results.append({
                "title": title,
                "url": url,
                "description": description
            })
        
        return results


async def fetch_competitor_data(competitor: str, year: int, month: int) -> Dict:
    """获取竞品数据的异步入口函数"""
    fetcher = DataFetcher()
    return await fetcher.fetch_all(competitor, year, month)


def fetch_competitor_data_sync(competitor: str, year: int, month: int) -> Dict:
    """获取竞品数据的同步入口函数"""
    return asyncio.run(fetch_competitor_data(competitor, year, month))


if __name__ == "__main__":
    # 测试
    async def test():
        fetcher = DataFetcher()
        result = await fetcher.fetch_all("Keep", 2026, 2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    asyncio.run(test())
