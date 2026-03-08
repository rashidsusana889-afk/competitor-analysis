#!/usr/bin/env python3
"""
通知模块
支持 Discord、Slack、Email 等多种通知方式
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None


class NotificationSender:
    """通知发送器"""
    
    def __init__(self):
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK', '')
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK', '')
        self.email_to = os.environ.get('EMAIL_TO', '')
        self.email_from = os.environ.get('EMAIL_FROM', '')
        self.smtp_server = os.environ.get('SMTP_SERVER', '')
        self.smtp_port = os.environ.get('SMTP_PORT', '587')
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
    
    def send(self, status: str, month: str, report_path: str = ''):
        """发送通知"""
        results = []
        
        # 构建消息
        message = self._build_message(status, month, report_path)
        
        # Discord 通知
        if self.discord_webhook:
            result = self._send_discord(message)
            results.append(('Discord', result))
        
        # Slack 通知
        if self.slack_webhook:
            result = self._send_slack(message)
            results.append(('Slack', result))
        
        # Email 通知
        if self.email_to and self.smtp_server:
            result = self._send_email(message)
            results.append(('Email', result))
        
        return results
    
    def _build_message(self, status: str, month: str, report_path: str):
        """构建通知消息"""
        emoji = '✅' if status == 'success' else '❌'
        status_text = '成功' if status == 'success' else '失败'
        
        message = {
            'title': f'{emoji} 竞品分析报告生成{status_text}',
            'month': month,
            'status': status_text,
            'report_path': report_path,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return message
    
    def _send_discord(self, message: dict) -> bool:
        """发送 Discord 通知"""
        if not requests:
            print('⚠️  requests 库未安装')
            return False
        
        embed = {
            'title': message['title'],
            'color': 65280 if message['status'] == '成功' else 16711680,
            'fields': [
                {'name': '月份', 'value': message['month'], 'inline': True},
                {'name': '状态', 'value': message['status'], 'inline': True},
                {'name': '时间', 'value': message['timestamp'], 'inline': True}
            ]
        }
        
        if message['report_path']:
            embed['fields'].append({
                'name': '报告路径', 
                'value': message['report_path']
            })
        
        try:
            response = requests.post(
                self.discord_webhook,
                json={'embeds': [embed]}
            )
            return response.status_code == 204
        except Exception as e:
            print(f'❌ Discord 通知失败: {e}')
            return False
    
    def _send_slack(self, message: dict) -> bool:
        """发送 Slack 通知"""
        if not requests:
            print('⚠️  requests 库未安装')
            return False
        
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': message['title']
                }
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f'*月份:*\n{message["month"]}'},
                    {'type': 'mrkdwn', 'text': f'*状态:*\n{message["status"]}'},
                    {'type': 'mrkdwn', 'text': f'*时间:*\n{message["timestamp"]}'}
                ]
            }
        ]
        
        if message['report_path']:
            blocks.append({
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': f'*报告路径:*\n{message["report_path"]}'}
            })
        
        try:
            response = requests.post(
                self.slack_webhook,
                json={'blocks': blocks}
            )
            return response.status_code == 200
        except Exception as e:
            print(f'❌ Slack 通知失败: {e}')
            return False
    
    def _send_email(self, message: dict) -> bool:
        """发送邮件通知"""
        if not requests:
            print('⚠️  requests 库未安装')
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = message['title']
            
            body = f"""
            竞品分析报告生成通知
            
            月份: {message['month']}
            状态: {message['status']}
            时间: {message['timestamp']}
            报告路径: {message['report_path']}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, int(self.smtp_port))
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f'❌ Email 通知失败: {e}')
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='发送通知')
    parser.add_argument('--status', required=True, help='任务状态: success 或 failure')
    parser.add_argument('--month', required=True, help='目标月份')
    parser.add_argument('--report', default='', help='报告路径')
    args = parser.parse_args()
    
    sender = NotificationSender()
    results = sender.send(args.status, args.month, args.report)
    
    for platform, success in results:
        emoji = '✅' if success else '❌'
        print(f'{emoji} {platform} 通知: {"成功" if success else "失败"}')


if __name__ == "__main__":
    main()
