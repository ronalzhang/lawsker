# Lawsker备份恢复指南

## 📋 目录

- [备份策略](#备份策略)
- [数据库备份](#数据库备份)
- [文件备份](#文件备份)
- [配置备份](#配置备份)
- [恢复流程](#恢复流程)
- [灾难恢复](#灾难恢复)
- [监控和验证](#监控和验证)

## 🎯 备份策略

### 备份原则
- **3-2-1原则**: 3份副本，2种介质，1份异地
- **定期备份**: 每日增量，每周全量
- **自动化**: 减少人工干预，降低错误率
- **验证**: 定期验证备份完整性

### 备份类型
1. **全量备份**: 完整的数据副本
2. **增量备份**: 自上次备份后的变化
3. **差异备份**: 自上次全量备份后的变化
4. **实时备份**: 关键数据的实时同步

## 🗄️ 数据库备份

### PostgreSQL备份

#### 1. 全量备份
```bash
#!/bin/bash
# 全量备份脚本: scripts/backup-database-full.sh

BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="lawsker"
DB_USER="postgres"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行全量备份
pg_dump -h localhost -U $DB_USER -d $DB_NAME \
    --verbose --clean --no-owner --no-privileges \
    --format=custom \
    --file=$BACKUP_DIR/lawsker_full_$DATE.dump

# 压缩备份文件
gzip $BACKUP_DIR/lawsker_full_$DATE.dump

# 清理7天前的备份
find $BACKUP_DIR -name "lawsker_full_*.dump.gz" -mtime +7 -delete

echo "数据库全量备份完成: lawsker_full_$DATE.dump.gz"
```

#### 2. 增量备份 (WAL归档)
```bash
# 配置PostgreSQL WAL归档
# 在postgresql.conf中添加:
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'
max_wal_senders = 3
```

#### 3. 自动备份脚本
```bash
#!/bin/bash
# 自动备份脚本: scripts/auto-backup.sh

# 每日增量备份
0 2 * * * /opt/lawsker/scripts/backup-database-incremental.sh

# 每周全量备份
0 1 * * 0 /opt/lawsker/scripts/backup-database-full.sh

# 每月备份验证
0 3 1 * * /opt/lawsker/scripts/verify-backup.sh
```

### Redis备份

#### 1. RDB备份
```bash
#!/bin/bash
# Redis备份脚本

BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 触发RDB快照
redis-cli BGSAVE

# 等待备份完成
while [ $(redis-cli LASTSAVE) -eq $(redis-cli LASTSAVE) ]; do
    sleep 1
done

# 复制RDB文件
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 压缩备份
gzip $BACKUP_DIR/redis_$DATE.rdb

echo "Redis备份完成: redis_$DATE.rdb.gz"
```

## 📁 文件备份

### 应用文件备份
```bash
#!/bin/bash
# 应用文件备份脚本: scripts/backup-files.sh

BACKUP_DIR="/backup/files"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/lawsker"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份应用代码
tar -czf $BACKUP_DIR/app_code_$DATE.tar.gz \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    $APP_DIR

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz \
    /opt/lawsker/uploads

# 备份日志文件
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz \
    /var/log/lawsker

echo "文件备份完成"
```

### 配置文件备份
```bash
#!/bin/bash
# 配置文件备份脚本

BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份应用配置
cp /opt/lawsker/.env.production $BACKUP_DIR/env_$DATE
cp /opt/lawsker/backend/alembic.ini $BACKUP_DIR/alembic_$DATE.ini

# 备份NGINX配置
cp /etc/nginx/sites-available/lawsker $BACKUP_DIR/nginx_$DATE.conf

# 备份SSL证书
cp -r /etc/letsencrypt $BACKUP_DIR/ssl_$DATE

# 备份系统配置
cp /etc/systemd/system/lawsker.service $BACKUP_DIR/systemd_$DATE.service

echo "配置文件备份完成"
```

## 🔄 恢复流程

### 数据库恢复

#### 1. 从全量备份恢复
```bash
#!/bin/bash
# 数据库恢复脚本: scripts/restore-database.sh

BACKUP_FILE=$1
DB_NAME="lawsker"
DB_USER="postgres"

if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <backup_file>"
    exit 1
fi

# 停止应用服务
systemctl stop lawsker

# 解压备份文件
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip $BACKUP_FILE
    BACKUP_FILE=${BACKUP_FILE%.gz}
fi

# 删除现有数据库
dropdb -h localhost -U $DB_USER $DB_NAME

# 创建新数据库
createdb -h localhost -U $DB_USER $DB_NAME

# 恢复数据
pg_restore -h localhost -U $DB_USER -d $DB_NAME \
    --verbose --clean --no-owner --no-privileges \
    $BACKUP_FILE

# 启动应用服务
systemctl start lawsker

echo "数据库恢复完成"
```

#### 2. 时间点恢复 (PITR)
```bash
#!/bin/bash
# 时间点恢复脚本

TARGET_TIME=$1
BASE_BACKUP=$2

if [ -z "$TARGET_TIME" ] || [ -z "$BASE_BACKUP" ]; then
    echo "使用方法: $0 <target_time> <base_backup>"
    echo "示例: $0 '2024-01-30 14:30:00' /backup/base_backup.tar"
    exit 1
fi

# 停止PostgreSQL
systemctl stop postgresql

# 清空数据目录
rm -rf /var/lib/postgresql/14/main/*

# 恢复基础备份
tar -xf $BASE_BACKUP -C /var/lib/postgresql/14/main/

# 创建recovery.conf
cat > /var/lib/postgresql/14/main/recovery.conf << EOF
restore_command = 'cp /backup/wal/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# 启动PostgreSQL
systemctl start postgresql

echo "时间点恢复完成，目标时间: $TARGET_TIME"
```

### 文件恢复
```bash
#!/bin/bash
# 文件恢复脚本: scripts/restore-files.sh

BACKUP_FILE=$1
RESTORE_TYPE=$2

case $RESTORE_TYPE in
    "app")
        tar -xzf $BACKUP_FILE -C /opt/lawsker --strip-components=3
        ;;
    "uploads")
        tar -xzf $BACKUP_FILE -C /opt/lawsker/uploads --strip-components=3
        ;;
    "logs")
        tar -xzf $BACKUP_FILE -C /var/log/lawsker --strip-components=3
        ;;
    *)
        echo "恢复类型: app, uploads, logs"
        exit 1
        ;;
esac

echo "文件恢复完成: $RESTORE_TYPE"
```

## 🚨 灾难恢复

### 灾难恢复计划 (DRP)

#### 1. 恢复时间目标 (RTO)
- **关键业务**: 2小时内恢复
- **一般业务**: 4小时内恢复
- **非关键业务**: 24小时内恢复

#### 2. 恢复点目标 (RPO)
- **数据库**: 最多丢失15分钟数据
- **文件**: 最多丢失1小时数据
- **配置**: 最多丢失1天数据

#### 3. 灾难恢复步骤
```bash
#!/bin/bash
# 灾难恢复脚本: scripts/disaster-recovery.sh

echo "开始灾难恢复流程..."

# 1. 评估损坏程度
echo "1. 评估系统状态..."
systemctl status lawsker
systemctl status postgresql
systemctl status redis-server
systemctl status nginx

# 2. 恢复基础设施
echo "2. 恢复基础设施..."
# 重新安装必要的软件包
apt update && apt install -y postgresql redis-server nginx

# 3. 恢复数据库
echo "3. 恢复数据库..."
LATEST_DB_BACKUP=$(ls -t /backup/database/lawsker_full_*.dump.gz | head -1)
./restore-database.sh $LATEST_DB_BACKUP

# 4. 恢复应用文件
echo "4. 恢复应用文件..."
LATEST_APP_BACKUP=$(ls -t /backup/files/app_code_*.tar.gz | head -1)
./restore-files.sh $LATEST_APP_BACKUP app

# 5. 恢复配置文件
echo "5. 恢复配置文件..."
LATEST_CONFIG_BACKUP=$(ls -t /backup/config/ | head -1)
cp /backup/config/env_* /opt/lawsker/.env.production
cp /backup/config/nginx_*.conf /etc/nginx/sites-available/lawsker

# 6. 启动服务
echo "6. 启动服务..."
systemctl enable --now postgresql
systemctl enable --now redis-server
systemctl enable --now nginx
systemctl enable --now lawsker

# 7. 验证恢复
echo "7. 验证系统恢复..."
sleep 30
curl -f http://localhost/health || echo "健康检查失败"

echo "灾难恢复完成"
```

### 异地备份
```bash
#!/bin/bash
# 异地备份脚本: scripts/offsite-backup.sh

REMOTE_HOST="backup.example.com"
REMOTE_USER="backup"
REMOTE_PATH="/backup/lawsker"

# 同步数据库备份
rsync -avz --delete /backup/database/ \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/database/

# 同步文件备份
rsync -avz --delete /backup/files/ \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/files/

# 同步配置备份
rsync -avz --delete /backup/config/ \
    $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/config/

echo "异地备份同步完成"
```

## 📊 监控和验证

### 备份监控脚本
```bash
#!/bin/bash
# 备份监控脚本: scripts/backup-monitor.sh

BACKUP_DIR="/backup"
ALERT_EMAIL="admin@lawsker.com"

# 检查备份文件是否存在
check_backup_exists() {
    local backup_type=$1
    local max_age=$2
    
    latest_backup=$(find $BACKUP_DIR/$backup_type -name "*.gz" -mtime -$max_age | wc -l)
    
    if [ $latest_backup -eq 0 ]; then
        echo "警告: $backup_type 备份超过 $max_age 天未更新" | \
            mail -s "备份警告" $ALERT_EMAIL
        return 1
    fi
    
    return 0
}

# 检查各类备份
check_backup_exists "database" 1
check_backup_exists "files" 1
check_backup_exists "config" 7

# 检查备份文件完整性
verify_backup_integrity() {
    local backup_file=$1
    
    if ! gzip -t $backup_file; then
        echo "错误: 备份文件损坏 $backup_file" | \
            mail -s "备份文件损坏" $ALERT_EMAIL
        return 1
    fi
    
    return 0
}

# 验证最新的数据库备份
latest_db_backup=$(ls -t $BACKUP_DIR/database/lawsker_full_*.dump.gz | head -1)
verify_backup_integrity $latest_db_backup

echo "备份监控检查完成"
```

### 恢复测试脚本
```bash
#!/bin/bash
# 恢复测试脚本: scripts/test-recovery.sh

TEST_DB="lawsker_test_recovery"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "使用方法: $0 <backup_file>"
    exit 1
fi

echo "开始恢复测试..."

# 创建测试数据库
createdb $TEST_DB

# 恢复到测试数据库
pg_restore -d $TEST_DB $BACKUP_FILE

# 验证数据完整性
psql -d $TEST_DB -c "SELECT COUNT(*) FROM users;" > /tmp/user_count.txt
psql -d $TEST_DB -c "SELECT COUNT(*) FROM cases;" > /tmp/case_count.txt

# 清理测试数据库
dropdb $TEST_DB

echo "恢复测试完成，结果保存在 /tmp/"
```

## 📋 备份清单

### 每日备份检查清单
- [ ] 数据库增量备份完成
- [ ] Redis快照备份完成
- [ ] 应用日志备份完成
- [ ] 备份文件完整性验证
- [ ] 异地备份同步完成

### 每周备份检查清单
- [ ] 数据库全量备份完成
- [ ] 应用文件备份完成
- [ ] 配置文件备份完成
- [ ] 备份恢复测试完成
- [ ] 备份存储空间检查

### 每月备份检查清单
- [ ] 灾难恢复演练完成
- [ ] 备份策略评估更新
- [ ] 备份文档更新完成
- [ ] 备份监控告警测试
- [ ] 备份保留策略执行

## 🔧 故障排除

### 常见备份问题

#### 1. 磁盘空间不足
```bash
# 检查磁盘空间
df -h /backup

# 清理旧备份
find /backup -name "*.gz" -mtime +30 -delete

# 压缩备份文件
gzip /backup/database/*.dump
```

#### 2. 备份文件损坏
```bash
# 验证备份文件
gzip -t backup_file.gz

# 如果损坏，使用前一天的备份
ls -t /backup/database/ | head -2
```

#### 3. 恢复失败
```bash
# 检查错误日志
tail -f /var/log/postgresql/postgresql-14-main.log

# 检查权限问题
chown -R postgres:postgres /var/lib/postgresql/14/main/
```

---

**文档版本**: v1.0
**最后更新**: 2024-01-30
**维护人员**: DevOps团队