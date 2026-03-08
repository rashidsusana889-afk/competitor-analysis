"""
AI 智能分析模块
使用 OpenAI GPT 进行竞品数据分析和洞察
"""

import json
import os
from typing import Dict, List, Optional


class AIAnalyzer:
    """AI分析器 - 使用 OpenAI GPT 进行智能分析"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 AI 分析器
        
        Args:
            api_key: OpenAI API Key，默认从环境变量读取
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️  未安装 openai 库，AI分析功能不可用")
    
    def analyze(
        self, 
        raw_data: Dict, 
        competitors: List[str]
    ) -> Dict:
        """
        对原始数据进行 AI 分析
        
        Args:
            raw_data: 原始竞品数据
            competitors: 竞品列表
        
        Returns:
            包含 AI 分析结果的字典
        """
        if not self.client:
            print("⚠️  未配置 OpenAI API，跳过 AI 分析")
            return raw_data
        
        try:
            # 构建分析提示词
            prompt = self._build_analysis_prompt(raw_data, competitors)
            
            # 调用 GPT 进行分析
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一位专业的运动健身行业分析师，擅长分析竞品动态和行业趋势。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析 AI 返回的分析结果
            analysis_text = response.choices[0].message.content
            
            # 尝试解析 JSON
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，手动解析
                analysis = self._parse_text_analysis(analysis_text)
            
            # 合并分析结果到原始数据
            return {
                **raw_data,
                "ai_insights": analysis.get("insights", []),
                "trends": analysis.get("trends", []),
                "recommendations": analysis.get("recommendations", []),
                "analysis_model": "gpt-4o"
            }
            
        except Exception as e:
            print(f"⚠️  AI 分析失败: {str(e)}")
            return raw_data
    
    def _build_analysis_prompt(
        self, 
        data: Dict, 
        competitors: List[str]
    ) -> str:
        """构建分析提示词"""
        
        # 格式化竞品信息
        competitors_info = []
        for name, info in data.get('competitors', {}).items():
            highlights = info.get('highlights', 'N/A')
            versions = info.get('versions', [])
            version_str = ', '.join(versions) if versions else '暂无版本信息'
            competitors_info.append(
                f"- **{name}**: {highlights} (版本: {version_str})"
            )
        
        competitors_text = '\n'.join(competitors_info)
        month_str = data.get('month_str', '本月')
        
        prompt = f"""
请分析以下{len(competitors)}款运动类App在{month_str}的更新动态，并提供行业洞察：

## 竞品更新信息：
{competitors_text}

## 请提供：
1. **关键洞察 (insights)**：本月行业的3-5个主要发现是什么？
2. **发展趋势 (trends)**：运动健身App行业的3-5个重要趋势？
3. **建议 (recommendations)**：可以借鉴的行业最佳实践和机会点？

请以JSON格式返回分析结果，包含以下字段：
{{
    "insights": ["洞察1", "洞察2", "洞察3"],
    "trends": ["趋势1", "趋势2", "趋势3"],
    "recommendations": ["建议1", "建议2", "建议3"]
}}

只返回JSON，不要其他内容。
"""
        return prompt
    
    def _parse_text_analysis(self, text: str) -> Dict:
        """解析文本格式的分析结果"""
        
        lines = text.strip().split('\n')
        current_section = None
        result = {
            "insights": [],
            "trends": [],
            "recommendations": []
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测章节标题
            if '洞察' in line or 'insight' in line.lower():
                current_section = 'insights'
            elif '趋势' in line or 'trend' in line.lower():
                current_section = 'trends'
            elif '建议' in line or 'recommend' in line.lower():
                current_section = 'recommendations'
            elif current_section and (line.startswith('-') or line.startswith('*')):
                # 提取列表项
                item = line.lstrip('-*').strip()
                if item:
                    result[current_section].append(item)
        
        return result


class LocalAIAnalyzer:
    """本地 AI 分析器 - 使用 Ollama 等本地模型"""
    
    def __init__(self, model: str = "llama3"):
        """
        初始化本地 AI 分析器
        
        Args:
            model: 本地模型名称
        """
        self.model = model
        self.base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    def analyze(
        self, 
        raw_data: Dict, 
        competitors: List[str]
    ) -> Dict:
        """使用本地模型进行分析"""
        
        try:
            import requests
            
            prompt = self._build_prompt(raw_data, competitors)
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                # 解析结果
                return {
                    **raw_data,
                    "ai_insights": self._extract_insights(analysis_text),
                    "trends": self._extract_trends(analysis_text),
                    "recommendations": self._extract_recommendations(analysis_text),
                    "analysis_model": f"local:{self.model}"
                }
        except Exception as e:
            print(f"⚠️  本地 AI 分析失败: {str(e)}")
        
        return raw_data
    
    def _build_prompt(self, data: Dict, competitors: List[str]) -> str:
        """构建提示词"""
        # 类似 OpenAI 版本
        return f"Analyze these fitness apps: {', '.join(competitors)}"
    
    def _extract_insights(self, text: str) -> List[str]:
        """提取洞察"""
        return [text[:200]] if text else []
    
    def _extract_trends(self, text: str) -> List[str]:
        """提取趋势"""
        return []
    
    def _extract_recommendations(self, text: str) -> List[str]:
        """提取建议"""
        return []
