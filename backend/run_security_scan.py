#!/usr/bin/env python3
"""
安全漏洞扫描脚本
运行综合安全测试并生成报告
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.security_scanner import SecurityScanner, run_security_scan

def create_reports_directory():
    """创建报告目录"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    return reports_dir

def print_scan_summary(results: dict):
    """打印扫描摘要"""
    print("\n" + "="*60)
    print("🔒 LAWSKER系统安全扫描报告")
    print("="*60)
    
    print(f"📅 扫描时间: {results.get('start_time', 'N/A')}")
    print(f"🎯 目标URL: {results.get('target_url', 'N/A')}")
    print(f"📊 扫描状态: {results.get('status', 'N/A')}")
    
    if results.get('status') == 'failed':
        print(f"❌ 错误信息: {results.get('error', 'N/A')}")
        return
    
    print("\n📋 测试结果摘要:")
    print("-" * 40)
    
    total_vulnerabilities = 0
    high_severity = 0
    medium_severity = 0
    low_severity = 0
    
    for test_name, test_result in results.get('tests', {}).items():
        if isinstance(test_result, dict) and 'vulnerabilities' in test_result:
            vuln_count = len(test_result['vulnerabilities'])
            total_vulnerabilities += vuln_count
            
            # 统计严重程度
            for vuln in test_result['vulnerabilities']:
                severity = vuln.get('severity', 'low')
                if severity == 'high':
                    high_severity += 1
                elif severity == 'medium':
                    medium_severity += 1
                else:
                    low_severity += 1
            
            status_icon = "✅" if vuln_count == 0 else "⚠️" if vuln_count < 3 else "❌"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {vuln_count} 个漏洞")
    
    print("\n🎯 漏洞统计:")
    print(f"   🔴 高危: {high_severity}")
    print(f"   🟡 中危: {medium_severity}")
    print(f"   🟢 低危: {low_severity}")
    print(f"   📊 总计: {total_vulnerabilities}")
    
    if total_vulnerabilities == 0:
        print("\n🎉 恭喜！未发现安全漏洞")
    else:
        print(f"\n⚠️  发现 {total_vulnerabilities} 个安全问题，请查看详细报告")

def print_detailed_vulnerabilities(results: dict):
    """打印详细漏洞信息"""
    print("\n" + "="*60)
    print("🔍 详细漏洞信息")
    print("="*60)
    
    vuln_count = 0
    for test_name, test_result in results.get('tests', {}).items():
        if isinstance(test_result, dict) and 'vulnerabilities' in test_result:
            vulnerabilities = test_result['vulnerabilities']
            if vulnerabilities:
                print(f"\n📋 {test_name.replace('_', ' ').title()}:")
                print("-" * 40)
                
                for i, vuln in enumerate(vulnerabilities, 1):
                    vuln_count += 1
                    severity_icon = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(vuln.get('severity', 'low'), '🟢')
                    
                    print(f"{severity_icon} 漏洞 #{vuln_count}")
                    print(f"   类型: {vuln.get('type', 'N/A')}")
                    print(f"   端点: {vuln.get('endpoint', 'N/A')}")
                    print(f"   方法: {vuln.get('method', 'N/A')}")
                    print(f"   严重程度: {vuln.get('severity', 'N/A')}")
                    print(f"   描述: {vuln.get('description', 'N/A')}")
                    
                    if 'payload' in vuln:
                        print(f"   载荷: {vuln['payload']}")
                    
                    print()

def generate_html_report(results: dict, output_file: str):
    """生成HTML报告"""
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Lawsker系统安全扫描报告</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }
            .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .summary-card { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007bff; }
            .vulnerability { background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px; }
            .high { border-left: 4px solid #dc3545; }
            .medium { border-left: 4px solid #ffc107; }
            .low { border-left: 4px solid #28a745; }
            .test-section { margin-bottom: 30px; }
            .test-title { background: #007bff; color: white; padding: 10px; border-radius: 5px 5px 0 0; margin: 0; }
            .test-content { border: 1px solid #007bff; border-top: none; padding: 15px; border-radius: 0 0 5px 5px; }
            .no-vulnerabilities { text-align: center; color: #28a745; font-weight: bold; padding: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 Lawsker系统安全扫描报告</h1>
                <p>扫描时间: {scan_time}</p>
                <p>目标URL: {target_url}</p>
            </div>
            
            <div class="summary">
                <div class="summary-card">
                    <h3>总漏洞数</h3>
                    <h2>{total_vulnerabilities}</h2>
                </div>
                <div class="summary-card">
                    <h3>高危漏洞</h3>
                    <h2 style="color: #dc3545;">{high_severity}</h2>
                </div>
                <div class="summary-card">
                    <h3>中危漏洞</h3>
                    <h2 style="color: #ffc107;">{medium_severity}</h2>
                </div>
                <div class="summary-card">
                    <h3>低危漏洞</h3>
                    <h2 style="color: #28a745;">{low_severity}</h2>
                </div>
            </div>
            
            {test_sections}
        </div>
    </body>
    </html>
    """
    
    # 统计漏洞
    total_vulnerabilities = 0
    high_severity = 0
    medium_severity = 0
    low_severity = 0
    
    test_sections = ""
    
    for test_name, test_result in results.get('tests', {}).items():
        if isinstance(test_result, dict) and 'vulnerabilities' in test_result:
            vulnerabilities = test_result['vulnerabilities']
            total_vulnerabilities += len(vulnerabilities)
            
            # 统计严重程度
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'low')
                if severity == 'high':
                    high_severity += 1
                elif severity == 'medium':
                    medium_severity += 1
                else:
                    low_severity += 1
            
            # 生成测试部分HTML
            test_sections += f'<div class="test-section">'
            test_sections += f'<h2 class="test-title">{test_name.replace("_", " ").title()}</h2>'
            test_sections += f'<div class="test-content">'
            
            if vulnerabilities:
                for vuln in vulnerabilities:
                    severity_class = vuln.get('severity', 'low')
                    test_sections += f'<div class="vulnerability {severity_class}">'
                    test_sections += f'<h4>{vuln.get("type", "N/A")} - {vuln.get("severity", "N/A").upper()}</h4>'
                    test_sections += f'<p><strong>端点:</strong> {vuln.get("endpoint", "N/A")}</p>'
                    test_sections += f'<p><strong>方法:</strong> {vuln.get("method", "N/A")}</p>'
                    test_sections += f'<p><strong>描述:</strong> {vuln.get("description", "N/A")}</p>'
                    if 'payload' in vuln:
                        test_sections += f'<p><strong>载荷:</strong> <code>{vuln["payload"]}</code></p>'
                    test_sections += '</div>'
            else:
                test_sections += '<div class="no-vulnerabilities">✅ 未发现漏洞</div>'
            
            test_sections += '</div></div>'
    
    # 填充模板
    html_content = html_template.format(
        scan_time=results.get('start_time', 'N/A'),
        target_url=results.get('target_url', 'N/A'),
        total_vulnerabilities=total_vulnerabilities,
        high_severity=high_severity,
        medium_severity=medium_severity,
        low_severity=low_severity,
        test_sections=test_sections
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

async def main():
    """主函数"""
    print("🚀 启动Lawsker系统安全扫描...")
    
    # 创建报告目录
    reports_dir = create_reports_directory()
    
    # 获取目标URL
    target_url = os.getenv('SCAN_TARGET_URL', 'http://localhost:8000')
    
    try:
        # 运行安全扫描
        results = await run_security_scan(target_url)
        
        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_report = reports_dir / f"security_scan_{timestamp}.json"
        html_report = reports_dir / f"security_scan_{timestamp}.html"
        
        # 保存JSON报告
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # 生成HTML报告
        generate_html_report(results, str(html_report))
        
        # 打印扫描摘要
        print_scan_summary(results)
        
        # 打印详细漏洞信息
        print_detailed_vulnerabilities(results)
        
        print(f"\n📄 详细报告已保存:")
        print(f"   JSON: {json_report}")
        print(f"   HTML: {html_report}")
        
        # 返回退出码
        total_vulnerabilities = sum(
            len(test_result.get('vulnerabilities', []))
            for test_result in results.get('tests', {}).values()
            if isinstance(test_result, dict)
        )
        
        if total_vulnerabilities > 0:
            print(f"\n⚠️  发现 {total_vulnerabilities} 个安全问题")
            sys.exit(1)
        else:
            print("\n✅ 安全扫描通过，未发现问题")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ 安全扫描失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())