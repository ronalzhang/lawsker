#!/usr/bin/env python3
"""
前端UI现代化测试脚本
验证现代化设计系统和用户体验改进
"""

import os
import sys
import json
import re
from pathlib import Path

class UIModernizationTester:
    """UI现代化测试器"""
    
    def __init__(self):
        self.frontend_path = Path("frontend")
        self.test_results = []
        
    def run_ui_tests(self):
        """运行UI现代化测试"""
        print("🎨 开始前端UI现代化测试...")
        print("🎯 验证: 专业图标、现代化设计、响应式布局")
        print("="*60)
        
        try:
            # 1. 测试设计系统
            self._test_design_system()
            
            # 2. 测试图标系统
            self._test_icon_system()
            
            # 3. 测试现代化组件
            self._test_modern_components()
            
            # 4. 测试响应式设计
            self._test_responsive_design()
            
            # 5. 测试游戏化元素
            self._test_gamification_elements()
            
            # 6. 测试数据可视化
            self._test_data_visualization()
            
            # 7. 测试无障碍访问
            self._test_accessibility()
            
            # 生成测试报告
            self._generate_ui_test_report()
            
            return self._calculate_ui_coverage()
            
        except Exception as e:
            print(f"❌ UI测试执行失败: {str(e)}")
            return False
    
    def _test_design_system(self):
        """测试设计系统"""
        print("\n1️⃣ 测试设计系统...")
        
        design_system_file = self.frontend_path / "css" / "design-system.css"
        
        if design_system_file.exists():
            content = design_system_file.read_text()
            
            # 检查设计系统要素
            design_elements = [
                ':root',  # CSS变量
                '--primary-color',  # 主色彩
                '--font-family-sans',  # 字体系统
                '--shadow-',  # 阴影系统
                '--radius-',  # 圆角系统
                'color-palette',  # 色彩系统
                'typography',  # 字体排版
                'spacing'  # 间距系统
            ]
            
            found_elements = []
            for element in design_elements:
                if element in content:
                    found_elements.append(element)
            
            coverage = (len(found_elements) / len(design_elements)) * 100
            
            self.test_results.append({
                'test_name': '设计系统',
                'passed': coverage >= 80,
                'coverage': coverage,
                'details': f'{len(found_elements)}/{len(design_elements)}个设计元素存在'
            })
            
            print(f"   ✅ 设计系统文件存在: {design_system_file}")
            print(f"   📊 设计元素覆盖率: {coverage:.1f}%")
        else:
            self.test_results.append({
                'test_name': '设计系统',
                'passed': False,
                'coverage': 0,
                'details': '设计系统文件不存在'
            })
            print(f"   ❌ 设计系统文件不存在: {design_system_file}")
    
    def _test_icon_system(self):
        """测试图标系统"""
        print("\n2️⃣ 测试图标系统...")
        
        icon_system_file = self.frontend_path / "js" / "icon-system.js"
        
        if icon_system_file.exists():
            content = icon_system_file.read_text()
            
            # 检查专业图标库
            icon_libraries = [
                'heroicons',
                'feather',
                'lucide',
                'tabler',
                'phosphor'
            ]
            
            found_libraries = []
            for library in icon_libraries:
                if library.lower() in content.lower():
                    found_libraries.append(library)
            
            # 检查图标映射
            icon_mappings = [
                'IconMap',
                'user',
                'lawyer', 
                'case',
                'payment',
                'credits',
                'level',
                'rating'
            ]
            
            found_mappings = []
            for mapping in icon_mappings:
                if mapping in content:
                    found_mappings.append(mapping)
            
            library_coverage = (len(found_libraries) / len(icon_libraries)) * 100 if icon_libraries else 0
            mapping_coverage = (len(found_mappings) / len(icon_mappings)) * 100
            overall_coverage = (library_coverage + mapping_coverage) / 2
            
            self.test_results.append({
                'test_name': '图标系统',
                'passed': overall_coverage >= 70,
                'coverage': overall_coverage,
                'details': f'图标库: {len(found_libraries)}, 映射: {len(found_mappings)}'
            })
            
            print(f"   ✅ 图标系统文件存在: {icon_system_file}")
            print(f"   📊 图标系统覆盖率: {overall_coverage:.1f}%")
        else:
            self.test_results.append({
                'test_name': '图标系统',
                'passed': False,
                'coverage': 0,
                'details': '图标系统文件不存在'
            })
            print(f"   ❌ 图标系统文件不存在: {icon_system_file}")
    
    def _test_modern_components(self):
        """测试现代化组件"""
        print("\n3️⃣ 测试现代化组件...")
        
        modern_files = [
            "unified-auth-modern.html",
            "lawyer-workspace-modern.html", 
            "credits-management-modern.html",
            "index-modern.html"
        ]
        
        existing_files = []
        modern_features = []
        
        for filename in modern_files:
            file_path = self.frontend_path / filename
            if file_path.exists():
                existing_files.append(filename)
                
                content = file_path.read_text()
                
                # 检查现代化特征
                features = [
                    'class=".*modern.*"',  # 现代化CSS类
                    'data-.*=',  # 数据属性
                    'aria-.*=',  # 无障碍属性
                    'role=',  # 角色属性
                    'transition',  # 过渡动画
                    'transform',  # 变换效果
                    'gradient',  # 渐变效果
                    'shadow',  # 阴影效果
                    'rounded',  # 圆角
                    'flex',  # Flexbox布局
                    'grid'  # Grid布局
                ]
                
                file_features = []
                for feature in features:
                    if re.search(feature, content, re.IGNORECASE):
                        file_features.append(feature)
                
                modern_features.extend(file_features)
        
        file_coverage = (len(existing_files) / len(modern_files)) * 100
        feature_coverage = min(100, len(modern_features) * 10)  # 每个特征10分
        overall_coverage = (file_coverage + feature_coverage) / 2
        
        self.test_results.append({
            'test_name': '现代化组件',
            'passed': overall_coverage >= 75,
            'coverage': overall_coverage,
            'details': f'{len(existing_files)}个现代化文件, {len(modern_features)}个现代化特征'
        })
        
        print(f"   📁 现代化文件: {len(existing_files)}/{len(modern_files)}")
        print(f"   🎨 现代化特征: {len(modern_features)}个")
        print(f"   📊 现代化组件覆盖率: {overall_coverage:.1f}%")
    
    def _test_responsive_design(self):
        """测试响应式设计"""
        print("\n4️⃣ 测试响应式设计...")
        
        responsive_file = self.frontend_path / "css" / "responsive-fixes.css"
        
        if responsive_file.exists():
            content = responsive_file.read_text()
            
            # 检查响应式特征
            responsive_features = [
                '@media',  # 媒体查询
                'max-width',  # 最大宽度
                'min-width',  # 最小宽度
                'mobile',  # 移动端
                'tablet',  # 平板端
                'desktop',  # 桌面端
                'flex-wrap',  # 弹性换行
                'grid-template',  # 网格模板
                'viewport',  # 视口
                'responsive'  # 响应式
            ]
            
            found_features = []
            for feature in responsive_features:
                if feature in content.lower():
                    found_features.append(feature)
            
            coverage = (len(found_features) / len(responsive_features)) * 100
            
            self.test_results.append({
                'test_name': '响应式设计',
                'passed': coverage >= 70,
                'coverage': coverage,
                'details': f'{len(found_features)}/{len(responsive_features)}个响应式特征'
            })
            
            print(f"   ✅ 响应式设计文件存在: {responsive_file}")
            print(f"   📊 响应式特征覆盖率: {coverage:.1f}%")
        else:
            self.test_results.append({
                'test_name': '响应式设计',
                'passed': False,
                'coverage': 0,
                'details': '响应式设计文件不存在'
            })
            print(f"   ❌ 响应式设计文件不存在: {responsive_file}")
    
    def _test_gamification_elements(self):
        """测试游戏化元素"""
        print("\n5️⃣ 测试游戏化元素...")
        
        gamification_files = [
            ("css/gamification.css", "样式"),
            ("css/enhanced-gamification.css", "增强样式"),
            ("js/gamification.js", "脚本"),
            ("js/enhanced-gamification.js", "增强脚本")
        ]
        
        existing_files = []
        gamification_features = []
        
        for filename, file_type in gamification_files:
            file_path = self.frontend_path / filename
            if file_path.exists():
                existing_files.append(filename)
                
                content = file_path.read_text()
                
                # 检查游戏化特征
                features = [
                    'level',  # 等级
                    'points',  # 积分
                    'badge',  # 徽章
                    'progress',  # 进度
                    'achievement',  # 成就
                    'leaderboard',  # 排行榜
                    'reward',  # 奖励
                    'animation',  # 动画
                    'celebration',  # 庆祝
                    'upgrade'  # 升级
                ]
                
                for feature in features:
                    if feature.lower() in content.lower():
                        gamification_features.append(f"{feature}({file_type})")
        
        file_coverage = (len(existing_files) / len(gamification_files)) * 100
        feature_coverage = min(100, len(gamification_features) * 5)  # 每个特征5分
        overall_coverage = (file_coverage + feature_coverage) / 2
        
        self.test_results.append({
            'test_name': '游戏化元素',
            'passed': overall_coverage >= 60,
            'coverage': overall_coverage,
            'details': f'{len(existing_files)}个游戏化文件, {len(gamification_features)}个游戏化特征'
        })
        
        print(f"   🎮 游戏化文件: {len(existing_files)}/{len(gamification_files)}")
        print(f"   🏆 游戏化特征: {len(gamification_features)}个")
        print(f"   📊 游戏化元素覆盖率: {overall_coverage:.1f}%")
    
    def _test_data_visualization(self):
        """测试数据可视化"""
        print("\n6️⃣ 测试数据可视化...")
        
        viz_files = [
            ("css/data-visualization.css", "样式"),
            ("js/data-visualization.js", "脚本")
        ]
        
        existing_files = []
        viz_features = []
        
        for filename, file_type in viz_files:
            file_path = self.frontend_path / filename
            if file_path.exists():
                existing_files.append(filename)
                
                content = file_path.read_text()
                
                # 检查数据可视化特征
                features = [
                    'chart',  # 图表
                    'graph',  # 图形
                    'dashboard',  # 仪表盘
                    'metric',  # 指标
                    'visualization',  # 可视化
                    'canvas',  # 画布
                    'svg',  # SVG
                    'd3',  # D3.js
                    'echarts',  # ECharts
                    'chartjs'  # Chart.js
                ]
                
                for feature in features:
                    if feature.lower() in content.lower():
                        viz_features.append(f"{feature}({file_type})")
        
        file_coverage = (len(existing_files) / len(viz_files)) * 100
        feature_coverage = min(100, len(viz_features) * 10)  # 每个特征10分
        overall_coverage = (file_coverage + feature_coverage) / 2
        
        self.test_results.append({
            'test_name': '数据可视化',
            'passed': overall_coverage >= 50,
            'coverage': overall_coverage,
            'details': f'{len(existing_files)}个可视化文件, {len(viz_features)}个可视化特征'
        })
        
        print(f"   📊 可视化文件: {len(existing_files)}/{len(viz_files)}")
        print(f"   📈 可视化特征: {len(viz_features)}个")
        print(f"   📊 数据可视化覆盖率: {overall_coverage:.1f}%")
    
    def _test_accessibility(self):
        """测试无障碍访问"""
        print("\n7️⃣ 测试无障碍访问...")
        
        accessibility_files = [
            ("css/accessibility.css", "样式"),
            ("js/accessibility-fixes.js", "脚本")
        ]
        
        existing_files = []
        a11y_features = []
        
        for filename, file_type in accessibility_files:
            file_path = self.frontend_path / filename
            if file_path.exists():
                existing_files.append(filename)
                
                content = file_path.read_text()
                
                # 检查无障碍特征
                features = [
                    'aria-',  # ARIA属性
                    'role=',  # 角色属性
                    'tabindex',  # Tab索引
                    'alt=',  # 替代文本
                    'label',  # 标签
                    'focus',  # 焦点
                    'contrast',  # 对比度
                    'screen-reader',  # 屏幕阅读器
                    'keyboard',  # 键盘导航
                    'accessibility'  # 无障碍
                ]
                
                for feature in features:
                    if feature.lower() in content.lower():
                        a11y_features.append(f"{feature}({file_type})")
        
        file_coverage = (len(existing_files) / len(accessibility_files)) * 100
        feature_coverage = min(100, len(a11y_features) * 10)  # 每个特征10分
        overall_coverage = (file_coverage + feature_coverage) / 2
        
        self.test_results.append({
            'test_name': '无障碍访问',
            'passed': overall_coverage >= 40,
            'coverage': overall_coverage,
            'details': f'{len(existing_files)}个无障碍文件, {len(a11y_features)}个无障碍特征'
        })
        
        print(f"   ♿ 无障碍文件: {len(existing_files)}/{len(accessibility_files)}")
        print(f"   🔍 无障碍特征: {len(a11y_features)}个")
        print(f"   📊 无障碍访问覆盖率: {overall_coverage:.1f}%")
    
    def _calculate_ui_coverage(self):
        """计算UI覆盖率"""
        if not self.test_results:
            return False
        
        total_coverage = sum(result.get('coverage', 0) for result in self.test_results)
        overall_coverage = total_coverage / len(self.test_results)
        
        return overall_coverage >= 70  # UI测试要求70%覆盖率
    
    def _generate_ui_test_report(self):
        """生成UI测试报告"""
        print("\n" + "="*60)
        print("📊 前端UI现代化测试报告")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        
        if total_tests > 0:
            total_coverage = sum(result.get('coverage', 0) for result in self.test_results)
            overall_coverage = total_coverage / total_tests
        else:
            overall_coverage = 0
        
        print(f"\n📈 UI测试结果:")
        print(f"   测试项目数: {total_tests}")
        print(f"   通过项目数: {passed_tests}")
        print(f"   失败项目数: {total_tests - passed_tests}")
        print(f"   UI覆盖率: {overall_coverage:.1f}%")
        
        print(f"\n📋 详细测试结果:")
        for result in self.test_results:
            status = "✅ 通过" if result['passed'] else "❌ 失败"
            coverage = result.get('coverage', 0)
            print(f"   {status} {result['test_name']}: {coverage:.1f}% - {result['details']}")
        
        # UI验收标准检查
        print(f"\n🎯 UI验收标准检查:")
        
        # 现代化设计
        design_result = next((r for r in self.test_results if r['test_name'] == '设计系统'), None)
        if design_result and design_result['passed']:
            print(f"   ✅ 现代化设计系统: {design_result['coverage']:.1f}%")
        else:
            print(f"   ❌ 现代化设计系统: 需要改进")
        
        # 专业图标
        icon_result = next((r for r in self.test_results if r['test_name'] == '图标系统'), None)
        if icon_result and icon_result['passed']:
            print(f"   ✅ 专业图标系统: {icon_result['coverage']:.1f}%")
        else:
            print(f"   ❌ 专业图标系统: 需要改进")
        
        # 响应式设计
        responsive_result = next((r for r in self.test_results if r['test_name'] == '响应式设计'), None)
        if responsive_result and responsive_result['passed']:
            print(f"   ✅ 响应式设计: {responsive_result['coverage']:.1f}%")
        else:
            print(f"   ❌ 响应式设计: 需要改进")
        
        # 游戏化元素
        gamification_result = next((r for r in self.test_results if r['test_name'] == '游戏化元素'), None)
        if gamification_result and gamification_result['passed']:
            print(f"   ✅ 游戏化元素: {gamification_result['coverage']:.1f}%")
        else:
            print(f"   ⚠️ 游戏化元素: {gamification_result['coverage']:.1f}% (可选)")
        
        # 最终判定
        if overall_coverage >= 70 and passed_tests >= total_tests * 0.7:
            print(f"\n🎉 UI测试结论: 前端UI现代化达标，用户体验良好！")
            return True
        else:
            print(f"\n💥 UI测试结论: 前端UI现代化不足，需要改进！")
            
            # 提供改进建议
            print(f"\n🔧 UI改进建议:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   - 改进 {result['test_name']}")
            
            return False


def main():
    """主函数"""
    print("🎨 Lawsker 前端UI现代化测试")
    print("🎯 验证: 专业图标、现代化设计、响应式布局")
    print("="*60)
    
    try:
        tester = UIModernizationTester()
        success = tester.run_ui_tests()
        
        if success:
            print("\n🎊 前端UI现代化验证通过！")
            print("\n💡 UI状态:")
            print("   ✅ 现代化设计系统完整")
            print("   ✅ 专业图标库集成")
            print("   ✅ 响应式设计适配")
            print("   ✅ 用户体验优化")
            return 0
        else:
            print("\n💥 前端UI现代化验证失败！")
            print("\n🔧 需要改进:")
            print("   1. 完善设计系统规范")
            print("   2. 集成专业图标库")
            print("   3. 优化响应式设计")
            print("   4. 提升用户体验")
            return 1
            
    except Exception as e:
        print(f"\n💥 UI测试执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)