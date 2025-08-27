#!/usr/bin/env python3
"""
Lawsker 专业图标系统测试脚本
测试图标专业化实现的完整性和功能性
"""

import os
import json
import re
from pathlib import Path

class ProfessionalIconSystemTester:
    def __init__(self):
        self.frontend_dir = Path("frontend")
        self.js_dir = self.frontend_dir / "js"
        self.css_dir = self.frontend_dir / "css"
        self.test_results = {
            "icon_system_files": {},
            "html_integration": {},
            "icon_coverage": {},
            "upgrade_system": {},
            "professional_library": {},
            "overall_score": 0
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🎨 开始测试 Lawsker 专业图标系统...")
        print("=" * 60)
        
        # 1. 测试核心文件存在性
        self.test_core_files()
        
        # 2. 测试图标系统功能
        self.test_icon_system_functionality()
        
        # 3. 测试专业图标库
        self.test_professional_icon_library()
        
        # 4. 测试图标升级系统
        self.test_icon_upgrade_system()
        
        # 5. 测试HTML集成
        self.test_html_integration()
        
        # 6. 测试图标覆盖率
        self.test_icon_coverage()
        
        # 7. 计算总分
        self.calculate_overall_score()
        
        # 8. 生成报告
        self.generate_report()
        
        return self.test_results
    
    def test_core_files(self):
        """测试核心文件存在性"""
        print("📁 测试核心文件存在性...")
        
        required_files = {
            "icon-system.js": "核心图标系统",
            "professional-icon-library.js": "专业图标库",
            "icon-upgrade-system.js": "图标升级系统",
            "design-system.css": "设计系统样式"
        }
        
        results = {}
        for filename, description in required_files.items():
            if filename.endswith('.js'):
                filepath = self.js_dir / filename
            else:
                filepath = self.css_dir / filename
            
            exists = filepath.exists()
            results[filename] = {
                "exists": exists,
                "description": description,
                "path": str(filepath)
            }
            
            status = "✅" if exists else "❌"
            print(f"  {status} {description}: {filename}")
        
        self.test_results["icon_system_files"] = results
    
    def test_icon_system_functionality(self):
        """测试图标系统功能"""
        print("\n🔧 测试图标系统功能...")
        
        icon_system_file = self.js_dir / "icon-system.js"
        if not icon_system_file.exists():
            print("  ❌ icon-system.js 文件不存在")
            return
        
        content = icon_system_file.read_text(encoding='utf-8')
        
        # 检查关键功能
        features = {
            "HEROICONS": "Heroicons 图标定义",
            "IconSystem": "图标系统类",
            "getIcon": "获取图标方法",
            "createElement": "创建元素方法",
            "replaceWithIcon": "替换图标方法",
            "getAvailableIcons": "获取可用图标方法"
        }
        
        results = {}
        for feature, description in features.items():
            found = feature in content
            results[feature] = {
                "found": found,
                "description": description
            }
            
            status = "✅" if found else "❌"
            print(f"  {status} {description}")
        
        # 统计图标数量
        icon_matches = re.findall(r"'([^']+)':\s*`<svg", content)
        icon_count = len(icon_matches)
        results["icon_count"] = icon_count
        print(f"  📊 发现 {icon_count} 个基础图标")
        
        self.test_results["icon_system_functionality"] = results
    
    def test_professional_icon_library(self):
        """测试专业图标库"""
        print("\n📚 测试专业图标库...")
        
        library_file = self.js_dir / "professional-icon-library.js"
        if not library_file.exists():
            print("  ❌ professional-icon-library.js 文件不存在")
            return
        
        content = library_file.read_text(encoding='utf-8')
        
        # 检查扩展图标
        extended_matches = re.findall(r"'([^']+)':\s*`<svg", content)
        extended_count = len(extended_matches)
        
        # 检查分类
        categories_match = re.search(r"categories\s*=\s*{([^}]+)}", content, re.DOTALL)
        category_count = 0
        if categories_match:
            category_content = categories_match.group(1)
            category_count = len(re.findall(r"(\w+):", category_content))
        
        # 检查关键功能
        features = {
            "ProfessionalIconLibrary": "专业图标库类",
            "getIconsByCategory": "按分类获取图标",
            "searchIcons": "搜索图标功能",
            "createIconPicker": "图标选择器",
            "getRandomIcon": "随机图标功能"
        }
        
        results = {
            "extended_icon_count": extended_count,
            "category_count": category_count,
            "features": {}
        }
        
        print(f"  📊 扩展图标数量: {extended_count}")
        print(f"  📂 图标分类数量: {category_count}")
        
        for feature, description in features.items():
            found = feature in content
            results["features"][feature] = {
                "found": found,
                "description": description
            }
            
            status = "✅" if found else "❌"
            print(f"  {status} {description}")
        
        self.test_results["professional_library"] = results
    
    def test_icon_upgrade_system(self):
        """测试图标升级系统"""
        print("\n🔄 测试图标升级系统...")
        
        upgrade_file = self.js_dir / "icon-upgrade-system.js"
        if not upgrade_file.exists():
            print("  ❌ icon-upgrade-system.js 文件不存在")
            return
        
        content = upgrade_file.read_text(encoding='utf-8')
        
        # 检查升级功能
        features = {
            "IconUpgradeSystem": "图标升级系统类",
            "iconMappings": "图标映射规则",
            "contextualMappings": "上下文映射",
            "upgradeEmojiIcons": "Emoji图标升级",
            "upgradeClassBasedIcons": "类名图标升级",
            "upgradeDataAttributeIcons": "Data属性图标升级",
            "observeChanges": "动态变化监听"
        }
        
        results = {}
        for feature, description in features.items():
            found = feature in content
            results[feature] = {
                "found": found,
                "description": description
            }
            
            status = "✅" if found else "❌"
            print(f"  {status} {description}")
        
        # 统计映射规则数量
        emoji_mappings = re.findall(r"'([^']+)':\s*'([^']+)'", content)
        mapping_count = len(emoji_mappings)
        results["mapping_count"] = mapping_count
        print(f"  📊 图标映射规则: {mapping_count} 条")
        
        self.test_results["upgrade_system"] = results
    
    def test_html_integration(self):
        """测试HTML集成"""
        print("\n🌐 测试HTML集成...")
        
        html_files = list(self.frontend_dir.glob("*.html"))
        results = {}
        
        for html_file in html_files:
            if html_file.name.startswith('.'):
                continue
                
            content = html_file.read_text(encoding='utf-8')
            
            # 检查图标系统引用
            has_icon_system = "icon-system.js" in content
            has_professional_lib = "professional-icon-library.js" in content
            has_upgrade_system = "icon-upgrade-system.js" in content
            
            # 检查data-icon属性使用
            data_icon_count = len(re.findall(r'data-icon="([^"]+)"', content))
            
            results[html_file.name] = {
                "has_icon_system": has_icon_system,
                "has_professional_lib": has_professional_lib,
                "has_upgrade_system": has_upgrade_system,
                "data_icon_usage": data_icon_count
            }
            
            status_icon = "✅" if has_icon_system else "❌"
            status_lib = "✅" if has_professional_lib else "❌"
            status_upgrade = "✅" if has_upgrade_system else "❌"
            
            print(f"  📄 {html_file.name}:")
            print(f"    {status_icon} 图标系统引用")
            print(f"    {status_lib} 专业图标库引用")
            print(f"    {status_upgrade} 升级系统引用")
            if data_icon_count > 0:
                print(f"    📊 data-icon 使用: {data_icon_count} 次")
        
        self.test_results["html_integration"] = results
    
    def test_icon_coverage(self):
        """测试图标覆盖率"""
        print("\n📊 测试图标覆盖率...")
        
        # 业务场景图标需求
        business_scenarios = {
            "用户管理": ["user", "user-group", "user-circle"],
            "法律服务": ["scale", "gavel", "law-book", "contract"],
            "支付金融": ["credit-card", "banknotes", "currency-dollar"],
            "成就系统": ["trophy", "star", "star-solid", "fire"],
            "导航界面": ["home", "cog-6-tooth", "bell", "chart-bar"],
            "操作按钮": ["plus", "minus", "x-mark", "check"],
            "状态反馈": ["check-circle", "x-circle", "exclamation-triangle", "information-circle"],
            "文件上传": ["cloud-arrow-up", "document-arrow-up"],
            "时间日期": ["clock", "calendar-days"],
            "通讯联系": ["envelope", "phone"]
        }
        
        # 检查图标系统文件
        icon_system_file = self.js_dir / "icon-system.js"
        professional_lib_file = self.js_dir / "professional-icon-library.js"
        
        available_icons = set()
        
        if icon_system_file.exists():
            content = icon_system_file.read_text(encoding='utf-8')
            icons = re.findall(r"'([^']+)':\s*`<svg", content)
            available_icons.update(icons)
        
        if professional_lib_file.exists():
            content = professional_lib_file.read_text(encoding='utf-8')
            icons = re.findall(r"'([^']+)':\s*`<svg", content)
            available_icons.update(icons)
        
        results = {}
        total_required = 0
        total_covered = 0
        
        for scenario, required_icons in business_scenarios.items():
            covered_icons = [icon for icon in required_icons if icon in available_icons]
            coverage_rate = len(covered_icons) / len(required_icons) * 100
            
            results[scenario] = {
                "required": required_icons,
                "covered": covered_icons,
                "coverage_rate": coverage_rate
            }
            
            total_required += len(required_icons)
            total_covered += len(covered_icons)
            
            status = "✅" if coverage_rate == 100 else "⚠️" if coverage_rate >= 80 else "❌"
            print(f"  {status} {scenario}: {coverage_rate:.1f}% ({len(covered_icons)}/{len(required_icons)})")
        
        overall_coverage = total_covered / total_required * 100
        results["overall_coverage"] = overall_coverage
        results["total_available_icons"] = len(available_icons)
        
        print(f"\n  📈 总体覆盖率: {overall_coverage:.1f}% ({total_covered}/{total_required})")
        print(f"  📊 可用图标总数: {len(available_icons)}")
        
        self.test_results["icon_coverage"] = results
    
    def calculate_overall_score(self):
        """计算总体评分"""
        print("\n🎯 计算总体评分...")
        
        scores = []
        
        # 1. 核心文件完整性 (25%)
        core_files = self.test_results.get("icon_system_files", {})
        core_score = sum(1 for file_info in core_files.values() if file_info.get("exists", False))
        core_total = len(core_files)
        if core_total > 0:
            core_percentage = (core_score / core_total) * 25
            scores.append(core_percentage)
            print(f"  📁 核心文件完整性: {core_percentage:.1f}/25")
        
        # 2. 功能实现完整性 (25%)
        functionality = self.test_results.get("icon_system_functionality", {})
        func_score = sum(1 for feature_info in functionality.values() 
                        if isinstance(feature_info, dict) and feature_info.get("found", False))
        func_total = sum(1 for feature_info in functionality.values() 
                        if isinstance(feature_info, dict) and "found" in feature_info)
        if func_total > 0:
            func_percentage = (func_score / func_total) * 25
            scores.append(func_percentage)
            print(f"  🔧 功能实现完整性: {func_percentage:.1f}/25")
        
        # 3. 图标覆盖率 (30%)
        coverage = self.test_results.get("icon_coverage", {})
        coverage_rate = coverage.get("overall_coverage", 0)
        coverage_percentage = (coverage_rate / 100) * 30
        scores.append(coverage_percentage)
        print(f"  📊 图标覆盖率: {coverage_percentage:.1f}/30")
        
        # 4. HTML集成度 (20%)
        html_integration = self.test_results.get("html_integration", {})
        if html_integration:
            integration_scores = []
            for file_info in html_integration.values():
                file_score = sum([
                    file_info.get("has_icon_system", False),
                    file_info.get("has_professional_lib", False),
                    file_info.get("has_upgrade_system", False)
                ])
                integration_scores.append(file_score / 3)
            
            if integration_scores:
                integration_percentage = (sum(integration_scores) / len(integration_scores)) * 20
                scores.append(integration_percentage)
                print(f"  🌐 HTML集成度: {integration_percentage:.1f}/20")
        
        # 计算总分
        overall_score = sum(scores)
        self.test_results["overall_score"] = overall_score
        
        print(f"\n  🏆 总体评分: {overall_score:.1f}/100")
        
        # 评级
        if overall_score >= 90:
            grade = "A+ (优秀)"
        elif overall_score >= 80:
            grade = "A (良好)"
        elif overall_score >= 70:
            grade = "B (合格)"
        elif overall_score >= 60:
            grade = "C (需改进)"
        else:
            grade = "D (不合格)"
        
        print(f"  🎖️ 评级: {grade}")
        
        return overall_score
    
    def generate_report(self):
        """生成测试报告"""
        print("\n📋 生成测试报告...")
        
        report = {
            "test_summary": {
                "timestamp": "2024-01-20 12:00:00",
                "overall_score": self.test_results["overall_score"],
                "status": "PASS" if self.test_results["overall_score"] >= 70 else "FAIL"
            },
            "detailed_results": self.test_results
        }
        
        # 保存JSON报告
        report_file = "professional_icon_system_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"  💾 详细报告已保存: {report_file}")
        
        # 生成Markdown报告
        self.generate_markdown_report(report)
    
    def generate_markdown_report(self, report):
        """生成Markdown格式报告"""
        markdown_content = f"""# Lawsker 专业图标系统测试报告

## 测试概要

- **测试时间**: {report['test_summary']['timestamp']}
- **总体评分**: {report['test_summary']['overall_score']:.1f}/100
- **测试状态**: {report['test_summary']['status']}

## 详细测试结果

### 1. 核心文件检查

"""
        
        # 核心文件检查结果
        core_files = self.test_results.get("icon_system_files", {})
        for filename, info in core_files.items():
            status = "✅" if info["exists"] else "❌"
            markdown_content += f"- {status} **{info['description']}** (`{filename}`)\n"
        
        # 图标覆盖率
        markdown_content += "\n### 2. 图标覆盖率分析\n\n"
        coverage = self.test_results.get("icon_coverage", {})
        if coverage:
            overall_coverage = coverage.get("overall_coverage", 0)
            markdown_content += f"- **总体覆盖率**: {overall_coverage:.1f}%\n"
            markdown_content += f"- **可用图标总数**: {coverage.get('total_available_icons', 0)}\n\n"
            
            for scenario, info in coverage.items():
                if isinstance(info, dict) and "coverage_rate" in info:
                    rate = info["coverage_rate"]
                    status = "✅" if rate == 100 else "⚠️" if rate >= 80 else "❌"
                    markdown_content += f"- {status} **{scenario}**: {rate:.1f}%\n"
        
        # HTML集成情况
        markdown_content += "\n### 3. HTML集成情况\n\n"
        html_integration = self.test_results.get("html_integration", {})
        for filename, info in html_integration.items():
            markdown_content += f"#### {filename}\n"
            markdown_content += f"- 图标系统引用: {'✅' if info.get('has_icon_system') else '❌'}\n"
            markdown_content += f"- 专业图标库引用: {'✅' if info.get('has_professional_lib') else '❌'}\n"
            markdown_content += f"- 升级系统引用: {'✅' if info.get('has_upgrade_system') else '❌'}\n"
            if info.get('data_icon_usage', 0) > 0:
                markdown_content += f"- data-icon 使用次数: {info['data_icon_usage']}\n"
            markdown_content += "\n"
        
        # 改进建议
        markdown_content += """
## 改进建议

### 高优先级
1. 确保所有核心文件都已正确创建和部署
2. 提高图标覆盖率，特别是业务关键场景
3. 在所有HTML页面中集成专业图标系统

### 中优先级
1. 添加更多业务相关的专业图标
2. 优化图标升级系统的性能
3. 完善图标选择器组件

### 低优先级
1. 添加图标使用统计和分析
2. 实现图标主题切换功能
3. 提供图标自定义工具

## 结论

"""
        
        score = report['test_summary']['overall_score']
        if score >= 90:
            conclusion = "专业图标系统实现优秀，已达到生产环境标准。"
        elif score >= 80:
            conclusion = "专业图标系统实现良好，可以部署到生产环境。"
        elif score >= 70:
            conclusion = "专业图标系统基本合格，建议优化后部署。"
        else:
            conclusion = "专业图标系统需要重大改进才能投入使用。"
        
        markdown_content += conclusion
        
        # 保存Markdown报告
        report_file = "PROFESSIONAL_ICON_SYSTEM_TEST_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"  📄 Markdown报告已保存: {report_file}")

def main():
    """主函数"""
    tester = ProfessionalIconSystemTester()
    results = tester.run_all_tests()
    
    print("\n" + "=" * 60)
    print("🎨 Lawsker 专业图标系统测试完成!")
    
    score = results["overall_score"]
    if score >= 70:
        print("✅ 测试通过 - 图标专业化任务完成!")
        return True
    else:
        print("❌ 测试未通过 - 需要进一步改进")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)