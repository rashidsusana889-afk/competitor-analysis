"""
AI 智能分析模块
支持 OpenAI 和 MiniMax 多种 AI 服务商
"""

import json
import os
from typing import Dict, List, Optional


class AIAnalyzer:
    """AI分析器 - 支持多种 AI 服务商"""
    
    def __init__(self, provider: str = 'minimax'):
        """
        初始化 AI 分析器
        
        Args:
            provider: AI 服务商 ('openai' 或 'minimax')
        """
        self.provider = provider
        self.client = None
        
        # 根据服务商初始化客户端
        if provider == 'openai':
            self._init_openai()
        elif provider == 'minimax':
            self._init_minimax()
        else:
            print(f"⚠️  不支持的 AI 服务商: {provider}，将使用默认配置")
            self._init_minimax()
    
    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  未配置 OPENAI_API_KEY")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = 'gpt-4o'
        except ImportError:
            print("⚠️  未安装 openai 库")
    
    def _init_minimax(self):
        """初始化 MiniMax 客户端"""
        self.api_key = os.environ.get('MINIMAX_API_KEY')
        self.group_id = os.environ.get('MINIMAX_GROUP_ID')
        
        if not self.api_key:
            print("⚠️  未配置 MINIMAX_API_KEY")
            return
        
        if not self.group_id:
            print("⚠️  未配置 MINIMAX_GROUP_ID")
            return
        
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "abab6.5s-chat"
    
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
        # 检查是否配置了任何 AI 服务商
        has_openai = bool(os.environ.get('OPENAI_API_KEY'))
        has_minimax = bool(os.environ.get('MINIMAX_API_KEY') and os.environ.get('MINIMAX_GROUP_ID'))
        
        if not has_openai and not has_minimax:
            print("⚠️  未配置 AI 服务商，跳过 AI 分析")
            return raw_data
        
        # 自动选择可用的服务商
        if self.provider == 'openai' and not has_openai:
            print("⚠️  OpenAI 未配置，切换到 MiniMax")
            self._init_minimax()
        elif self.provider == 'minimax' and not has_minimax:
            print("⚠️  MiniMax 未配置，切换到 OpenAI")
            self._init_openai()
        
        try:
            if hasattr(self, 'client') and self.client:
                return self._analyze_with_openai(raw_data, competitors)
            elif hasattr(self, 'api_key') and self.api_key:
                return self._analyze_with_minimax(raw_data, competitors)
        except Exception as e:
            print(f"⚠️  AI 分析失败: {str(e)}")
            return raw_data
        
        return raw_data
    
    def _analyze_with_openai(self, data: Dict, competitors: List[str]) -> Dict:
        """使用 OpenAI 进行分析"""
        
        prompt = self._build_analysis_prompt(data, competitors)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一位专业的运动健身行业分析师。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        analysis = self._parse_analysis_result(analysis_text)
        
        return {
            **data,
            "ai_insights": analysis.get("insights", []),
            "trends": analysis.get("trends", []),
            "recommendations": analysis.get("recommendations", []),
            "analysis_provider": "openai",
            "analysis_model": self.model
        }
    
    def _analyze_with_minimax(self, data: Dict, competitors: List[str]) -> Dict:
        """使用 MiniMax 进行分析"""
        
        try:
            import requests
        except ImportError:
            print("⚠️  未安装 requests 库")
            return data
        
        prompt = self._build_analysis_prompt(data, competitors)
        
        url = f"{self.base_url}/text/chatcompletion_v2?GroupId={self.group_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位专业的运动健身行业分析师，擅长分析竞品动态和行业趋势。请用中文回答。"},
                {"role": "user", "content": prompt}
            ],
            "tokens_to_generate": 2000,
            "temperature": 0.7,
            "top_p": 0.95
        }
        
        print(f"🔄 正在调用 MiniMax API (模型: {self.model})...")
        print(f"📡 API URL: {url}")
        print(f"📝 请求内容长度: {len(prompt)} 字符")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            print(f"📡 API 响应状态: {response.status_code}")
            print(f"📄 响应内容: {response.text[:500]}")
        except requests.exceptions.Timeout:
            print("⚠️  MiniMax API 请求超时")
            return data
        except requests.exceptions.RequestException as e:
            print(f"⚠️  MiniMax API 请求失败: {str(e)}")
            return data
        
        if response.status_code != 200:
            print(f"⚠️  MiniMax API 错误: {response.status_code}")
            print(f"   响应内容: {response.text[:500]}")
            return data
        
        result = response.json()
        
        # 解析响应
        if 'choices' in result and len(result['choices']) > 0:
            analysis_text = result['choices'][0]['message']['content']
            analysis = self._parse_analysis_result(analysis_text)
            
            return {
                **data,
                "ai_insights": analysis.get("insights", []),
                "trends": analysis.get("trends", []),
                "recommendations": analysis.get("recommendations", []),
                "analysis_provider": "minimax",
                "analysis_model": self.model
            }
        
        print(f"⚠️  MiniMax API 返回格式异常: {result}")
        return data
    
    def _build_analysis_prompt(self, data: Dict, competitors: List[str]) -> str:
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
请分析以下{len(competitors)}款运动类App在{month_str}的更新动态，并提供行业洞察。

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
    
    def _parse_analysis_result(self, text: str) -> Dict:
        """解析 AI 返回的分析结果"""
        
        # 尝试解析 JSON
        try:
            # 尝试提取 JSON 块
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            elif '{' in text:
                start = text.find('{')
                end = text.rfind('}') + 1
                text = text[start:end]
            
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # 如果不是 JSON 格式，手动解析
            return self._parse_text_analysis(text)
    
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
            elif current_section and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                # 提取列表项
                item = line.lstrip('-*•').strip()
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
