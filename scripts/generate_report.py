#!/usr/bin/env python3
"""
竞品分析报告自动生成脚本 (AI增强版)
支持定时和手动触发，自动抓取竞品更新信息并生成报告
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from competitive_analysis import CompetitorReportGenerator
from ai_analyzer import AIAnalyzer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='竞品分析报告自动生成工具'
    )
    parser.add_argument(
        '--month',
        type=str,
        default='',
        help='目标月份 (YYYY-MM)，为空则自动获取当月'
    )
    parser.add_argument(
        '--competitors',
        type=str,
        default='Keep,Strava,Garmin Connect,Zwift,MyWhoosh,iGPSPORT,行者,Rouvy',
        help='竞品列表 (逗号分隔)'
    )
    parser.add_argument(
        '--ai-analysis',
        type=lambda x: x.lower() == 'true',
        default=True,
        help='是否启用AI分析'
    )
    return parser.parse_args()


def determine_target_month(month_str: str) -> tuple:
    """确定目标年份和月份"""
    if month_str:
        year, month = map(int, month_str.split('-'))
    else:
        today = datetime.now()
        year, month = today.year, today.month
    return year, month


def main():
    """主函数"""
    args = parse_args()
    
    # 确定目标月份
    year, month = determine_target_month(args.month)
    competitors = [c.strip() for c in args.competitors.split(',')]
    ai_enabled = args.ai_analysis
    
    # 打印配置信息
    print("=" * 60)
    print("📊 竞品分析报告生成器")
    print("=" * 60)
    print(f"📅 目标月份: {year}年{month}月")
    print(f"📱 竞品数量: {len(competitors)} 款")
    print(f"📋 竞品列表: {', '.join(competitors)}")
    print(f"🤖 AI分析: {'启用' if ai_enabled else '禁用'}")
    print("=" * 60)
    
    try:
        # 1. 初始化报告生成器
        print("\n📥 步骤1: 抓取竞品更新数据...")
        generator = CompetitorReportGenerator(competitors)
        
        # 2. 抓取本月数据
        raw_data = generator.fetch_monthly_updates(year, month)
        print(f"   ✅ 成功抓取 {len(raw_data.get('competitors', {}))} 个竞品数据")
        
        # 3. AI 智能分析 (可选)
        if ai_enabled:
            print("\n🤖 步骤2: 进行AI智能分析...")
            # 检查是否配置了 AI 服务商
            has_openai = bool(os.environ.get('OPENAI_API_KEY'))
            has_minimax = bool(os.environ.get('MINIMAX_API_KEY') and os.environ.get('MINIMAX_GROUP_ID'))
            
            if has_openai or has_minimax:
                analyzer = AIAnalyzer()
                analyzed_data = analyzer.analyze(raw_data, competitors)
                print("   ✅ AI分析完成")
            else:
                print("   ⚠️  未配置 AI 服务商 (MINIMAX 或 OPENAI)，跳过AI分析")
                analyzed_data = raw_data
        else:
            print("\n⏭️  步骤2: AI分析已禁用")
            analyzed_data = raw_data
        
        # 4. 生成Markdown报告
        print("\n📝 步骤3: 生成Markdown报告...")
        report_content = generator.generate_markdown_report(year, month, analyzed_data)
        
        # 5. 保存报告
        output_dir = Path(__file__).parent.parent / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        month_str = f"{month:02d}"
        filename = f"{year}年{month_str}月运动类App竞品更新分析报告.md"
        output_path = output_dir / filename
        
        output_path.write_text(report_content, encoding='utf-8')
        print(f"   ✅ 报告已保存: {output_path}")
        
        # 6. 输出摘要
        print("\n" + "=" * 60)
        print("✅ 报告生成完成!")
        print(f"📄 文件路径: {output_path}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
