#!/usr/bin/env python3
"""
生成触发页面
将模板页面中的占位符替换为实际配置
"""

import os
import re
from pathlib import Path


def get_github_info():
    """获取 GitHub 配置信息"""
    # 从环境变量读取
    owner = os.environ.get('GITHUB_OWNER', '')
    repo = os.environ.get('GITHUB_REPO', '')
    token = os.environ.get('GITHUB_TOKEN', '')
    
    return {
        'owner': owner,
        'repo': repo,
        'token': token[:20] + '...' if token else ''  # 只显示 token 前20位
    }


def generate_trigger_page():
    """生成触发页面"""
    
    # 读取模板
    template_path = Path(__file__).parent.parent / "public" / "index.html"
    template = template_path.read_text(encoding='utf-8')
    
    # 获取 GitHub 配置
    github_info = get_github_info()
    
    # 替换占位符
    replacements = {
        '{{GITHUB_OWNER}}': github_info['owner'] or 'your-username',
        '{{GITHUB_REPO}}': github_info['repo'] or 'your-repo',
        '{{GITHUB_TOKEN}}': 'YOUR_GITHUB_TOKEN'
    }
    
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    # 写入生成的文件
    output_path = Path(__file__).parent.parent / "public" / "trigger.html"
    output_path.write_text(result, encoding='utf-8')
    
    print(f"✅ 触发页面已生成: {output_path}")
    print(f"   请配置以下信息后使用:")
    print(f"   - GITHUB_OWNER: {github_info['owner'] or 'your-username'}")
    print(f"   - GITHUB_REPO: {github_info['repo'] or 'your-repo'}")
    print(f"   - GITHUB_TOKEN: 在 GitHub Settings > Developer settings > Personal access tokens 生成")


if __name__ == "__main__":
    generate_trigger_page()
