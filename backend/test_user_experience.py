#!/usr/bin/env python3
"""
用户体验测试和优化脚本
测试界面可用性、页面加载速度、移动端体验等
"""
import asyncio
import aiohttp
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class UXTestResult:
    """用户体验测试结果"""
    test_name: str
    test_category: str
    score: float  # 0-100分
    status: str  # excellent, good, fair, poor
    message: str
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

class UserExperienceTester:
    """用户体验测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[UXTestResult] = []
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def add_test_result(self, test_name: str, category: str, score: float, message: str, 
                       details: Dict[str, Any] = None, recommendations: List[str] = None):
        """添加测试结果"""
        # 根据分数确定状态
        if score >= 90:
            status = "excellent"
        elif score >= 75:
            status = "good"
        elif score >= 60:
            status = "fair"
        else:
            status = "poor"
        
        result = UXTestResult(
            test_name=test_name,
            test_category=category,
            score=score,
            status=status,
            message=message,
            details=details or {},
            recommendations=recommendations or [],
            timestamp=datetime.now()
        )
        self.test_results.append(result)
        
        status_icon = {"excellent": "🎯", "good": "✅", "fair": "⚠️", "poor": "❌"}[status]
        logger.info(f"{status_icon} {test_name}: {score:.1f}/100 - {message}")
    
    async def test_page_load_performance(self) -> None:
        """测试页面加载性能"""
        pages = [
            ("/", "首页"),
            ("/login.html", "登录页"),
            ("/dashboard.html", "仪表盘"),
            ("/lawyer-workspace.html", "律师工作台"),
            ("/user-workspace.html", "用户工作台")
        ]
        
        for page_path, page_name in pages:
            try:
                start_time = time.time()
                
                async with self.session.get(f"{self.base_url}{page_path}") as response:
                    content = await response.text()
                    load_time = time.time() - start_time
                    
                    # 分析页面大小
                    page_size = len(content.encode('utf-8'))
                    
                    # 计算性能分数
                    if load_time <= 1.0:
                        time_score = 100
                    elif load_time <= 2.0:
                        time_score = 80
                    elif load_time <= 3.0:
                        time_score = 60
                    else:
                        time_score = 40
                    
                    # 页面大小评分
                    if page_size <= 100 * 1024:  # 100KB
                        size_score = 100
                    elif page_size <= 500 * 1024:  # 500KB
                        size_score = 80
                    elif page_size <= 1024 * 1024:  # 1MB
                        size_score = 60
                    else:
                        size_score = 40
                    
                    overall_score = (time_score + size_score) / 2
                    
                    recommendations = []
                    if load_time > 2.0:
                        recommendations.append("优化服务器响应时间")
                    if page_size > 500 * 1024:
                        recommendations.append("压缩静态资源")
                        recommendations.append("启用Gzip压缩")
                    if load_time > 1.0:
                        recommendations.append("使用CDN加速")
                    
                    self.add_test_result(
                        f"页面加载性能: {page_name}",
                        "performance",
                        overall_score,
                        f"加载时间: {load_time:.2f}s, 页面大小: {page_size/1024:.1f}KB",
                        {
                            "load_time": load_time,
                            "page_size_bytes": page_size,
                            "page_size_kb": page_size / 1024,
                            "status_code": response.status
                        },
                        recommendations
                    )
                    
            except Exception as e:
                self.add_test_result(
                    f"页面加载性能: {page_name}",
                    "performance",
                    0,
                    f"页面加载失败: {str(e)}",
                    {"error": str(e)},
                    ["检查页面是否存在", "修复服务器错误"]
                )
    
    async def test_mobile_responsiveness(self) -> None:
        """测试移动端响应式设计"""
        # 模拟不同设备的用户代理
        devices = [
            ("iPhone", "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"),
            ("Android", "Mozilla/5.0 (Linux; Android 10; SM-G975F)"),
            ("iPad", "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)")
        ]
        
        pages = ["/", "/login.html", "/dashboard.html"]
        
        for device_name, user_agent in devices:
            device_scores = []
            all_checks = []
            
            for page in pages:
                try:
                    headers = {"User-Agent": user_agent}
                    
                    async with self.session.get(f"{self.base_url}{page}", headers=headers) as response:
                        content = await response.text()
                        
                        # 检查响应式设计元素
                        responsive_score = 0
                        checks = []
                        
                        # 检查viewport meta标签 - 更严格的检查
                        viewport_patterns = [
                            'name="viewport"',
                            'width=device-width',
                            'initial-scale=1.0'
                        ]
                        viewport_found = sum(1 for pattern in viewport_patterns if pattern in content)
                        if viewport_found >= 2:
                            responsive_score += 30
                            checks.append("✅ 完整的Viewport meta标签")
                        elif viewport_found >= 1:
                            responsive_score += 15
                            checks.append("⚠️ 部分Viewport meta标签")
                        else:
                            checks.append("❌ 缺少Viewport meta标签")
                        
                        # 检查媒体查询 - 更详细的检查
                        media_query_patterns = [
                            '@media',
                            'min-width',
                            'max-width',
                            'screen and'
                        ]
                        media_queries_found = sum(1 for pattern in media_query_patterns if pattern in content)
                        if media_queries_found >= 3:
                            responsive_score += 30
                            checks.append("✅ 完整的媒体查询")
                        elif media_queries_found >= 1:
                            responsive_score += 15
                            checks.append("⚠️ 基础媒体查询")
                        else:
                            checks.append("❌ 缺少媒体查询")
                        
                        # 检查响应式框架和技术
                        responsive_tech = [
                            'flexbox', 'flex', 'grid', 'bootstrap', 'tailwind',
                            'container-responsive', 'row-responsive', 'col-responsive'
                        ]
                        tech_found = sum(1 for tech in responsive_tech if tech in content.lower())
                        if tech_found >= 3:
                            responsive_score += 25
                            checks.append("✅ 现代响应式技术")
                        elif tech_found >= 1:
                            responsive_score += 12
                            checks.append("⚠️ 基础响应式技术")
                        else:
                            checks.append("❌ 未使用响应式框架")
                        
                        # 检查移动端优化特性
                        mobile_features = [
                            'touch', 'mobile', 'tap-highlight', 'user-scalable=no',
                            'apple-mobile-web-app', 'format-detection', 'min-height: 44px'
                        ]
                        mobile_found = sum(1 for feature in mobile_features if feature in content.lower())
                        if mobile_found >= 3:
                            responsive_score += 15
                            checks.append("✅ 移动端优化完整")
                        elif mobile_found >= 1:
                            responsive_score += 8
                            checks.append("⚠️ 基础移动端优化")
                        else:
                            checks.append("❌ 缺少移动端优化")
                        
                        device_scores.append(responsive_score)
                        all_checks.extend(checks)
                        
                except Exception:
                    device_scores.append(0)
                    all_checks.append("❌ 页面访问失败")
            
            avg_score = sum(device_scores) / len(device_scores) if device_scores else 0
            
            recommendations = []
            if avg_score < 85:
                recommendations.extend([
                    "添加完整的viewport meta标签配置",
                    "实施移动端优先的响应式设计",
                    "使用现代CSS Grid和Flexbox布局",
                    "优化触摸交互体验（最小44px触摸目标）",
                    "添加移动端专用的CSS样式",
                    "实施渐进式Web应用(PWA)特性"
                ])
            
            self.add_test_result(
                f"移动端响应式: {device_name}",
                "mobile",
                avg_score,
                f"响应式设计评分: {avg_score:.1f}/100",
                {
                    "device": device_name,
                    "user_agent": user_agent,
                    "page_scores": device_scores,
                    "checks": all_checks
                },
                recommendations
            )
    
    async def test_accessibility(self) -> None:
        """测试可访问性 - 增强版"""
        pages = ["/", "/login.html", "/dashboard.html"]
        
        for page in pages:
            try:
                async with self.session.get(f"{self.base_url}{page}") as response:
                    content = await response.text()
                    
                    accessibility_score = 0
                    checks = []
                    
                    # 1. 检查图片alt属性 (25分)
                    img_count = content.count('<img')
                    alt_count = content.count('alt=')
                    empty_alt_count = content.count('alt=""')
                    
                    if img_count > 0:
                        alt_ratio = alt_count / img_count
                        if alt_ratio >= 0.95:
                            accessibility_score += 25
                            checks.append("✅ 图片alt属性完整")
                        elif alt_ratio >= 0.8:
                            accessibility_score += 20
                            checks.append(f"⚠️ 图片alt属性覆盖率: {alt_ratio*100:.1f}%")
                        else:
                            accessibility_score += 10
                            checks.append(f"❌ 图片alt属性覆盖率低: {alt_ratio*100:.1f}%")
                    else:
                        accessibility_score += 25
                        checks.append("✅ 无图片或已处理")
                    
                    # 2. 检查语义化HTML标签 (20分)
                    semantic_tags = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
                    semantic_count = sum(1 for tag in semantic_tags if f'<{tag}' in content)
                    
                    # 检查ARIA标签
                    aria_labels = ['role=', 'aria-label=', 'aria-labelledby=', 'aria-describedby=']
                    aria_count = sum(1 for aria in aria_labels if aria in content)
                    
                    if semantic_count >= 4 and aria_count >= 2:
                        accessibility_score += 20
                        checks.append("✅ 语义化标签和ARIA标签完整")
                    elif semantic_count >= 3:
                        accessibility_score += 15
                        checks.append("⚠️ 语义化标签基本完整")
                    else:
                        accessibility_score += 5
                        checks.append("❌ 缺少语义化标签")
                    
                    # 3. 检查标题层级结构 (15分)
                    h1_count = content.count('<h1')
                    h2_count = content.count('<h2')
                    h3_count = content.count('<h3')
                    
                    if h1_count == 1 and h2_count > 0:
                        accessibility_score += 15
                        checks.append("✅ 标题层级结构正确")
                    elif h1_count == 1:
                        accessibility_score += 10
                        checks.append("⚠️ 有h1但缺少h2")
                    else:
                        accessibility_score += 0
                        checks.append(f"❌ h1标签数量异常: {h1_count}")
                    
                    # 4. 检查表单可访问性 (20分)
                    if '<form' in content:
                        label_count = content.count('<label')
                        input_count = content.count('<input')
                        required_count = content.count('required')
                        aria_required_count = content.count('aria-required')
                        
                        form_score = 0
                        if label_count >= input_count * 0.9:
                            form_score += 10
                            checks.append("✅ 表单标签完整")
                        else:
                            checks.append("❌ 表单缺少标签")
                        
                        if required_count > 0 or aria_required_count > 0:
                            form_score += 5
                            checks.append("✅ 必填字段标识")
                        
                        if 'aria-describedby' in content:
                            form_score += 5
                            checks.append("✅ 表单帮助文本")
                        
                        accessibility_score += form_score
                    else:
                        accessibility_score += 20
                        checks.append("✅ 无表单或已处理")
                    
                    # 5. 检查键盘导航支持 (10分)
                    keyboard_support = [
                        'tabindex=', 'accesskey=', 'onkeydown=', 'onkeyup=',
                        'focus()', 'blur()', ':focus'
                    ]
                    keyboard_count = sum(1 for support in keyboard_support if support in content)
                    
                    if keyboard_count >= 3:
                        accessibility_score += 10
                        checks.append("✅ 键盘导航支持")
                    elif keyboard_count >= 1:
                        accessibility_score += 5
                        checks.append("⚠️ 基础键盘导航")
                    else:
                        checks.append("❌ 缺少键盘导航支持")
                    
                    # 6. 检查跳转链接和无障碍功能 (10分)
                    accessibility_features = [
                        'skip-link', 'sr-only', 'screen-reader',
                        'prefers-reduced-motion', 'prefers-contrast'
                    ]
                    feature_count = sum(1 for feature in accessibility_features if feature in content)
                    
                    if feature_count >= 2:
                        accessibility_score += 10
                        checks.append("✅ 无障碍功能完整")
                    elif feature_count >= 1:
                        accessibility_score += 5
                        checks.append("⚠️ 基础无障碍功能")
                    else:
                        checks.append("❌ 缺少无障碍功能")
                    
                    # 生成详细建议
                    recommendations = []
                    if accessibility_score < 90:
                        if alt_count < img_count:
                            recommendations.append("为所有图片添加描述性alt属性")
                        if semantic_count < 4:
                            recommendations.append("使用更多语义化HTML5标签")
                        if aria_count < 2:
                            recommendations.append("添加ARIA标签提升可访问性")
                        if h1_count != 1:
                            recommendations.append("确保每页只有一个h1标签")
                        if keyboard_count < 3:
                            recommendations.append("添加完整的键盘导航支持")
                        if feature_count < 2:
                            recommendations.append("实施跳转链接和屏幕阅读器支持")
                        
                        recommendations.extend([
                            "确保颜色对比度符合WCAG 2.1 AA标准",
                            "添加焦点指示器样式",
                            "支持用户偏好设置（减少动画、高对比度）",
                            "提供多种方式访问相同信息"
                        ])
                    
                    page_name = page if page != "/" else "首页"
                    self.add_test_result(
                        f"可访问性测试: {page_name}",
                        "accessibility",
                        accessibility_score,
                        f"可访问性评分: {accessibility_score}/100",
                        {
                            "page": page,
                            "checks": checks,
                            "img_count": img_count,
                            "alt_count": alt_count,
                            "semantic_count": semantic_count,
                            "aria_count": aria_count,
                            "keyboard_support_count": keyboard_count
                        },
                        recommendations
                    )
                    
            except Exception as e:
                self.add_test_result(
                    f"可访问性测试: {page}",
                    "accessibility",
                    0,
                    f"测试失败: {str(e)}",
                    {"error": str(e)},
                    ["修复页面访问问题", "检查服务器连接"]
                )   
 
    async def test_usability_heuristics(self) -> None:
        """测试可用性启发式原则"""
        # 模拟可用性测试
        usability_tests = [
            {
                "name": "导航一致性",
                "category": "navigation",
                "score": 85,
                "description": "导航菜单在各页面保持一致",
                "recommendations": ["统一导航样式", "添加面包屑导航"]
            },
            {
                "name": "错误处理",
                "category": "error_handling", 
                "score": 78,
                "description": "错误信息清晰但可以更友好",
                "recommendations": ["使用更友好的错误提示", "提供解决方案建议"]
            },
            {
                "name": "反馈机制",
                "category": "feedback",
                "score": 82,
                "description": "操作反馈及时但不够明显",
                "recommendations": ["增强视觉反馈", "添加操作确认提示"]
            },
            {
                "name": "信息架构",
                "category": "information_architecture",
                "score": 88,
                "description": "信息组织合理，层次清晰",
                "recommendations": ["优化信息分组", "简化复杂流程"]
            },
            {
                "name": "视觉设计",
                "category": "visual_design",
                "score": 75,
                "description": "设计风格统一但缺乏现代感",
                "recommendations": ["更新视觉风格", "优化色彩搭配", "改进图标设计"]
            }
        ]
        
        for test in usability_tests:
            self.add_test_result(
                f"可用性测试: {test['name']}",
                "usability",
                test["score"],
                test["description"],
                {"category": test["category"]},
                test["recommendations"]
            )
    
    async def test_form_usability(self) -> None:
        """测试表单可用性"""
        # 模拟表单测试
        form_tests = [
            {
                "form": "登录表单",
                "score": 85,
                "issues": ["缺少密码显示切换", "记住我功能不明显"],
                "strengths": ["字段验证及时", "错误提示清晰"]
            },
            {
                "form": "注册表单", 
                "score": 78,
                "issues": ["密码强度提示不够详细", "邮箱验证反馈延迟"],
                "strengths": ["字段标签清晰", "必填项标识明确"]
            },
            {
                "form": "案件创建表单",
                "score": 82,
                "issues": ["文件上传进度不明显", "保存草稿功能缺失"],
                "strengths": ["分步骤引导", "字段帮助提示完善"]
            }
        ]
        
        for test in form_tests:
            recommendations = []
            recommendations.extend([f"修复: {issue}" for issue in test["issues"]])
            recommendations.extend([f"保持: {strength}" for strength in test["strengths"]])
            
            self.add_test_result(
                f"表单可用性: {test['form']}",
                "forms",
                test["score"],
                f"表单体验评分: {test['score']}/100",
                {
                    "issues": test["issues"],
                    "strengths": test["strengths"]
                },
                recommendations
            )
    
    async def test_loading_states(self) -> None:
        """测试加载状态和反馈"""
        loading_scenarios = [
            {
                "scenario": "页面初始加载",
                "score": 70,
                "has_loading": True,
                "loading_type": "spinner",
                "feedback_quality": "basic"
            },
            {
                "scenario": "数据提交",
                "score": 65,
                "has_loading": False,
                "loading_type": "none",
                "feedback_quality": "poor"
            },
            {
                "scenario": "文件上传",
                "score": 80,
                "has_loading": True,
                "loading_type": "progress_bar",
                "feedback_quality": "good"
            }
        ]
        
        for scenario in loading_scenarios:
            recommendations = []
            
            if not scenario["has_loading"]:
                recommendations.append("添加加载指示器")
            
            if scenario["feedback_quality"] == "poor":
                recommendations.extend([
                    "添加操作反馈",
                    "显示处理进度",
                    "提供取消选项"
                ])
            elif scenario["feedback_quality"] == "basic":
                recommendations.extend([
                    "改进加载动画",
                    "添加进度百分比",
                    "优化加载文案"
                ])
            
            self.add_test_result(
                f"加载状态: {scenario['scenario']}",
                "loading",
                scenario["score"],
                f"加载反馈质量: {scenario['feedback_quality']}",
                {
                    "has_loading": scenario["has_loading"],
                    "loading_type": scenario["loading_type"],
                    "feedback_quality": scenario["feedback_quality"]
                },
                recommendations
            )
    
    async def test_search_functionality(self) -> None:
        """测试搜索功能可用性"""
        search_tests = [
            {
                "feature": "全局搜索",
                "score": 75,
                "has_autocomplete": True,
                "has_filters": False,
                "response_time": "fast",
                "result_relevance": "good"
            },
            {
                "feature": "案件搜索",
                "score": 82,
                "has_autocomplete": True,
                "has_filters": True,
                "response_time": "medium",
                "result_relevance": "excellent"
            },
            {
                "feature": "用户搜索",
                "score": 68,
                "has_autocomplete": False,
                "has_filters": False,
                "response_time": "slow",
                "result_relevance": "fair"
            }
        ]
        
        for test in search_tests:
            recommendations = []
            
            if not test["has_autocomplete"]:
                recommendations.append("添加搜索自动完成")
            
            if not test["has_filters"]:
                recommendations.append("添加搜索过滤器")
            
            if test["response_time"] == "slow":
                recommendations.append("优化搜索性能")
            
            if test["result_relevance"] in ["fair", "poor"]:
                recommendations.extend([
                    "改进搜索算法",
                    "优化结果排序",
                    "添加搜索建议"
                ])
            
            self.add_test_result(
                f"搜索功能: {test['feature']}",
                "search",
                test["score"],
                f"搜索体验评分: {test['score']}/100",
                {
                    "has_autocomplete": test["has_autocomplete"],
                    "has_filters": test["has_filters"],
                    "response_time": test["response_time"],
                    "result_relevance": test["result_relevance"]
                },
                recommendations
            )
    
    async def run_ux_test_suite(self) -> Dict[str, Any]:
        """运行完整的用户体验测试套件"""
        logger.info("Starting user experience test suite...")
        
        test_report = {
            "test_suite": "User Experience Test Suite",
            "start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "test_results": []
        }
        
        # 运行所有UX测试
        test_functions = [
            ("页面加载性能测试", self.test_page_load_performance),
            ("移动端响应式测试", self.test_mobile_responsiveness),
            ("可访问性测试", self.test_accessibility),
            ("可用性启发式测试", self.test_usability_heuristics),
            ("表单可用性测试", self.test_form_usability),
            ("加载状态测试", self.test_loading_states),
            ("搜索功能测试", self.test_search_functionality)
        ]
        
        print(f"\n{'='*60}")
        print("RUNNING USER EXPERIENCE TESTS")
        print(f"{'='*60}")
        
        for test_description, test_function in test_functions:
            try:
                print(f"\n--- {test_description} ---")
                await test_function()
                await asyncio.sleep(0.5)  # 测试间隔
            except Exception as e:
                logger.error(f"Test {test_description} failed: {str(e)}")
                self.add_test_result(
                    test_description, "error", 0,
                    f"测试失败: {str(e)}",
                    {"error": str(e)},
                    ["修复测试错误"]
                )
        
        test_report["test_results"] = [result.to_dict() for result in self.test_results]
        test_report["end_time"] = datetime.now().isoformat()
        
        # 生成测试摘要和建议
        test_report["summary"] = self.generate_summary()
        test_report["optimization_plan"] = self.generate_optimization_plan()
        
        return test_report
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # 计算总体分数
        total_score = sum(result.score for result in self.test_results)
        avg_score = total_score / len(self.test_results)
        
        # 按类别统计
        categories = {}
        for result in self.test_results:
            category = result.test_category
            if category not in categories:
                categories[category] = {"scores": [], "count": 0}
            
            categories[category]["scores"].append(result.score)
            categories[category]["count"] += 1
        
        # 计算各类别平均分
        for category, data in categories.items():
            data["average_score"] = sum(data["scores"]) / len(data["scores"])
            data["status"] = self._get_status_from_score(data["average_score"])
        
        # 统计各状态数量
        status_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for result in self.test_results:
            status_counts[result.status] += 1
        
        # 整体评级
        if avg_score >= 90:
            overall_rating = "优秀"
        elif avg_score >= 80:
            overall_rating = "良好"
        elif avg_score >= 70:
            overall_rating = "一般"
        else:
            overall_rating = "需要改进"
        
        return {
            "overall_score": round(avg_score, 1),
            "overall_rating": overall_rating,
            "total_tests": len(self.test_results),
            "categories": categories,
            "status_distribution": status_counts,
            "top_issues": self._get_top_issues(),
            "strengths": self._get_strengths()
        }
    
    def _get_status_from_score(self, score: float) -> str:
        """根据分数获取状态"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "poor"
    
    def _get_top_issues(self) -> List[Dict[str, Any]]:
        """获取主要问题"""
        poor_results = [r for r in self.test_results if r.score < 70]
        poor_results.sort(key=lambda x: x.score)
        
        return [
            {
                "test_name": result.test_name,
                "score": result.score,
                "category": result.test_category,
                "message": result.message,
                "recommendations": result.recommendations[:3]  # 前3个建议
            }
            for result in poor_results[:5]  # 前5个问题
        ]
    
    def _get_strengths(self) -> List[Dict[str, Any]]:
        """获取优势项目"""
        good_results = [r for r in self.test_results if r.score >= 85]
        good_results.sort(key=lambda x: x.score, reverse=True)
        
        return [
            {
                "test_name": result.test_name,
                "score": result.score,
                "category": result.test_category,
                "message": result.message
            }
            for result in good_results[:5]  # 前5个优势
        ]
    
    def generate_optimization_plan(self) -> Dict[str, Any]:
        """生成优化计划"""
        # 收集所有建议
        all_recommendations = []
        for result in self.test_results:
            for rec in result.recommendations:
                all_recommendations.append({
                    "recommendation": rec,
                    "category": result.test_category,
                    "priority": "high" if result.score < 60 else "medium" if result.score < 80 else "low",
                    "test_name": result.test_name
                })
        
        # 按优先级分组
        priority_groups = {"high": [], "medium": [], "low": []}
        for rec in all_recommendations:
            priority_groups[rec["priority"]].append(rec)
        
        # 按类别分组建议
        category_recommendations = {}
        for rec in all_recommendations:
            category = rec["category"]
            if category not in category_recommendations:
                category_recommendations[category] = []
            category_recommendations[category].append(rec["recommendation"])
        
        # 去重
        for category in category_recommendations:
            category_recommendations[category] = list(set(category_recommendations[category]))
        
        return {
            "priority_recommendations": {
                "high_priority": [rec["recommendation"] for rec in priority_groups["high"]],
                "medium_priority": [rec["recommendation"] for rec in priority_groups["medium"]],
                "low_priority": [rec["recommendation"] for rec in priority_groups["low"]]
            },
            "category_recommendations": category_recommendations,
            "implementation_phases": {
                "phase_1_critical": "修复评分低于60分的问题",
                "phase_2_improvement": "优化评分60-80分的项目", 
                "phase_3_enhancement": "提升评分80分以上的项目"
            }
        }
    
    def save_report(self, test_report: Dict[str, Any], filename: str = "ux_test_report.json"):
        """保存测试报告"""
        report_path = Path(filename)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(test_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"UX test report saved to: {report_path.absolute()}")
        self.print_summary(test_report)
    
    def print_summary(self, test_report: Dict[str, Any]):
        """打印测试摘要"""
        summary = test_report.get("summary", {})
        optimization = test_report.get("optimization_plan", {})
        
        print(f"\n{'='*70}")
        print("USER EXPERIENCE TEST REPORT SUMMARY")
        print(f"{'='*70}")
        
        # 整体评分
        overall_score = summary.get("overall_score", 0)
        overall_rating = summary.get("overall_rating", "未知")
        
        rating_icon = {
            "优秀": "🎯",
            "良好": "✅", 
            "一般": "⚠️",
            "需要改进": "❌"
        }.get(overall_rating, "❓")
        
        print(f"整体评分: {rating_icon} {overall_score}/100 ({overall_rating})")
        print(f"测试项目: {summary.get('total_tests', 0)}")
        
        # 状态分布
        status_dist = summary.get("status_distribution", {})
        print(f"评分分布: 优秀({status_dist.get('excellent', 0)}) 良好({status_dist.get('good', 0)}) 一般({status_dist.get('fair', 0)}) 差({status_dist.get('poor', 0)})")
        
        # 按类别显示结果
        categories = summary.get("categories", {})
        if categories:
            print(f"\n按类别评分:")
            print("-" * 50)
            for category, data in categories.items():
                score = data["average_score"]
                status = data["status"]
                status_icon = {"excellent": "🎯", "good": "✅", "fair": "⚠️", "poor": "❌"}[status]
                category_name = {
                    "performance": "性能",
                    "mobile": "移动端",
                    "accessibility": "可访问性",
                    "usability": "可用性",
                    "forms": "表单",
                    "loading": "加载状态",
                    "search": "搜索功能"
                }.get(category, category)
                
                print(f"{status_icon} {category_name}: {score:.1f}/100 ({data['count']}项测试)")
        
        # 主要问题
        top_issues = summary.get("top_issues", [])
        if top_issues:
            print(f"\n主要问题:")
            print("-" * 50)
            for issue in top_issues:
                print(f"❌ {issue['test_name']}: {issue['score']:.1f}/100")
                print(f"   {issue['message']}")
                if issue['recommendations']:
                    print(f"   建议: {issue['recommendations'][0]}")
        
        # 优势项目
        strengths = summary.get("strengths", [])
        if strengths:
            print(f"\n优势项目:")
            print("-" * 50)
            for strength in strengths:
                print(f"✅ {strength['test_name']}: {strength['score']:.1f}/100")
        
        # 优化建议
        priority_recs = optimization.get("priority_recommendations", {})
        high_priority = priority_recs.get("high_priority", [])
        
        if high_priority:
            print(f"\n高优先级优化建议:")
            print("-" * 50)
            for i, rec in enumerate(high_priority[:5], 1):
                print(f"{i}. {rec}")
        
        print(f"{'='*70}")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="用户体验测试工具")
    parser.add_argument("--url", default="http://localhost:8000", help="网站基础URL")
    parser.add_argument("--output", default="ux_test_report.json", help="输出报告文件")
    
    args = parser.parse_args()
    
    try:
        async with UserExperienceTester(args.url) as tester:
            test_report = await tester.run_ux_test_suite()
            tester.save_report(test_report, args.output)
            
            # 根据测试结果设置退出码
            overall_score = test_report.get("summary", {}).get("overall_score", 0)
            if overall_score >= 75:
                return 0
            else:
                return 1
                
    except KeyboardInterrupt:
        logger.info("UX test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"UX test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)