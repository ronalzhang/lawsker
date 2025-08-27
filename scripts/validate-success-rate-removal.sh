#!/bin/bash

# 验证成功率承诺移除脚本
# 检查代码中是否还存在成功率承诺相关内容

echo "🔍 验证企业服务成功率承诺移除情况..."
echo "================================================"

# 检查前端文件中的成功率承诺
echo "📱 检查前端文件..."

# 检查是否还有未处理的成功率承诺
success_rate_promises=$(grep -r "保证.*成功率\|承诺.*成功率\|guarantee.*success" frontend/ --include="*.html" --include="*.js" || true)

if [ -n "$success_rate_promises" ]; then
    echo "❌ 发现未处理的成功率承诺:"
    echo "$success_rate_promises"
    echo ""
else
    echo "✅ 前端文件中未发现成功率承诺"
fi

# 检查成功率显示是否添加了免责声明
echo ""
echo "📊 检查成功率显示免责声明..."

# 检查是否有直接显示成功率而没有免责声明的情况
success_rate_displays=$(grep -r "成功率[^*]" frontend/ --include="*.html" | grep -v "仅供参考\|历史数据\|不构成承诺\|historical_data\|completion_rate\|识别率\|disclaimer\|//" || true)

if [ -n "$success_rate_displays" ]; then
    echo "⚠️  发现可能需要添加免责声明的成功率显示:"
    echo "$success_rate_displays"
    echo ""
else
    echo "✅ 所有成功率显示都已添加免责声明"
fi

# 检查后端API是否有免责声明
echo ""
echo "🔧 检查后端API免责声明..."

api_disclaimers=$(grep -r "disclaimer\|免责声明" backend/app/api/ --include="*.py" | wc -l)

if [ "$api_disclaimers" -gt 0 ]; then
    echo "✅ 后端API包含 $api_disclaimers 处免责声明"
else
    echo "⚠️  后端API可能缺少免责声明"
fi

# 检查服务类是否有免责声明
echo ""
echo "🛠️  检查服务类免责声明..."

service_disclaimers=$(grep -r "仅供参考\|不构成.*承诺\|disclaimer" backend/app/services/ --include="*.py" | wc -l)

if [ "$service_disclaimers" -gt 0 ]; then
    echo "✅ 服务类包含 $service_disclaimers 处免责声明"
else
    echo "⚠️  服务类可能缺少免责声明"
fi

# 检查文档是否更新
echo ""
echo "📚 检查文档更新..."

if [ -f "docs/ENTERPRISE_SERVICE_DISCLAIMER.md" ]; then
    echo "✅ 企业服务免责声明文档已创建"
else
    echo "❌ 缺少企业服务免责声明文档"
fi

if [ -f "docs/SERVICE_UPDATE_NOTICE.md" ]; then
    echo "✅ 服务更新通知文档已创建"
else
    echo "❌ 缺少服务更新通知文档"
fi

# 检查FAQ是否更新
faq_updated=$(grep -c "不承诺.*成功率\|仅供参考" docs/FAQ.md || echo "0")

if [ "$faq_updated" -gt 0 ]; then
    echo "✅ FAQ文档已更新免责说明"
else
    echo "⚠️  FAQ文档可能需要更新"
fi

echo ""
echo "================================================"
echo "🎯 验证总结:"

# 计算总体评分
total_checks=6
passed_checks=0

# 检查各项是否通过
[ -z "$success_rate_promises" ] && ((passed_checks++))
[ -z "$success_rate_displays" ] && ((passed_checks++))
[ "$api_disclaimers" -gt 0 ] && ((passed_checks++))
[ "$service_disclaimers" -gt 0 ] && ((passed_checks++))
[ -f "docs/ENTERPRISE_SERVICE_DISCLAIMER.md" ] && ((passed_checks++))
[ "$faq_updated" -gt 0 ] && ((passed_checks++))

success_rate=$((passed_checks * 100 / total_checks))

echo "通过检查: $passed_checks/$total_checks"
echo "完成度: ${success_rate}%"

if [ "$success_rate" -ge 90 ]; then
    echo "✅ 企业服务成功率承诺移除工作基本完成"
    exit 0
elif [ "$success_rate" -ge 70 ]; then
    echo "⚠️  企业服务成功率承诺移除工作大部分完成，需要完善细节"
    exit 1
else
    echo "❌ 企业服务成功率承诺移除工作需要继续完善"
    exit 2
fi