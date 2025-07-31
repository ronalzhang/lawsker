# Lawsker技术文档

## 📚 文档索引

欢迎使用Lawsker技术文档！这里包含了系统的完整技术文档，帮助开发者、运维人员和用户更好地理解和使用系统。

## 🏗️ 架构和设计

### [系统架构文档](./SYSTEM-ARCHITECTURE.md)
- 系统概述和技术栈
- 整体架构设计
- 微服务架构说明
- 数据流和部署架构

### [数据库设计文档](./DATABASE-DESIGN.md)
- 数据库概述和设计原则
- 完整的表结构设计
- 索引和性能优化
- 数据关系和备份策略

## 🔧 开发指南

### [开发指南](./DEVELOPMENT-GUIDE.md)
- 开发环境搭建
- 项目结构说明
- 开发规范和最佳实践
- Git工作流和测试指南

### [API接口文档](./API-DOCUMENTATION.md)
- 完整的API接口说明
- 认证机制和错误处理
- 请求响应格式
- 接口使用示例

### [组件使用指南](./COMPONENT-GUIDE.md)
- 通用组件库
- 业务组件说明
- 图表和表单组件
- 开发规范和最佳实践

## 🚀 部署和运维

### [Git部署指南](./GIT_DEPLOYMENT_GUIDE.md)
- Git部署方案详解
- 服务器环境配置
- 自动化部署脚本
- 日常更新和维护流程

### [代码更新工作流程](./CODE_UPDATE_WORKFLOW.md)
- 开发到部署的完整流程
- Bug修复和版本发布
- 回滚操作和故障排除
- 团队协作最佳实践

### [生产环境部署指南](../PRODUCTION-DEPLOYMENT.md)
- 系统要求和环境准备
- 完整的部署流程
- SSL证书配置
- 监控和备份策略
- 应用部署步骤
- 数据库和NGINX配置
- 维护操作指南

### [运维手册](../docs/operations-runbook.md)
- 故障响应流程
- 常见问题处理
- 监控和告警
- 维护计划

### [故障排除指南](./TROUBLESHOOTING-GUIDE.md)
- 常见问题和解决方案
- 服务器和数据库问题
- 性能和安全问题
- 紧急处理流程

## 📊 监控和优化

### [灰度发布指南](../CANARY-DEPLOYMENT.md)
- 灰度发布策略
- 监控和回滚机制
- 用户反馈收集
- 最佳实践

### 性能优化文档
- [性能监控脚本](../scripts/performance-monitor.sh)
- [系统监控脚本](../scripts/system-monitor.sh)
- [安全监控脚本](../scripts/security-monitor.sh)

## 🔒 安全文档

### 安全配置
- [安全增强说明](../backend/app/services/README_security_enhancements.md)
- [加密和认证机制](../backend/app/core/encryption.py)
- [安全中间件配置](../backend/app/middlewares/)

## 📋 规范和标准

### 代码规范
- Python代码规范 (PEP 8)
- TypeScript/Vue.js规范
- 数据库设计规范
- API设计规范

### 文档规范
- 技术文档编写标准
- API文档格式
- 代码注释规范
- 版本控制规范

## 🆕 更新日志

### 最近更新
- 2024-01-30: 完善技术文档体系
- 2024-01-29: 添加灰度发布指南
- 2024-01-28: 更新部署和运维文档
- 2024-01-27: 完善API接口文档

## 📞 技术支持

### 联系方式
- **技术负责人**: tech-lead@lawsker.com
- **开发团队**: dev-team@lawsker.com
- **运维支持**: devops@lawsker.com

### 问题反馈
- GitHub Issues: [项目地址](https://github.com/your-org/lawsker)
- 技术讨论群: 微信群/钉钉群
- 文档改进建议: docs@lawsker.com

## 🎯 快速导航

### 新手入门
1. [开发环境搭建](./DEVELOPMENT-GUIDE.md#开发环境搭建)
2. [项目结构了解](./DEVELOPMENT-GUIDE.md#项目结构)
3. [API接口调用](./API-DOCUMENTATION.md)
4. [组件使用方法](./COMPONENT-GUIDE.md)

### 部署上线
1. [服务器准备](./DEPLOYMENT-GUIDE.md#服务器配置)
2. [应用部署](./DEPLOYMENT-GUIDE.md#应用部署)
3. [监控配置](../PRODUCTION-DEPLOYMENT.md#监控和日志)
4. [上线验证](../scripts/post-golive-validation.sh)

### 问题处理
1. [常见问题](./TROUBLESHOOTING-GUIDE.md#常见问题)
2. [日志查看](./TROUBLESHOOTING-GUIDE.md#监控和日志)
3. [性能优化](./TROUBLESHOOTING-GUIDE.md#性能问题)
4. [紧急处理](./TROUBLESHOOTING-GUIDE.md#紧急处理)

---

**注意**: 本文档持续更新中，如有疑问或建议，请及时反馈。