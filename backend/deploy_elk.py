#!/usr/bin/env python3
"""
ELK Stack日志聚合系统部署脚本
自动化部署Elasticsearch、Logstash、Kibana
"""
import asyncio
import json
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.elk_service import elk_service, setup_elk_logging

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("📊 LAWSKER ELK STACK日志聚合系统部署")
    print("=" * 60)
    print(f"📅 部署时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def print_section_header(title: str):
    """打印章节标题"""
    print(f"\n{'='*20} {title} {'='*20}")

def check_prerequisites():
    """检查前置条件"""
    print("🔍 检查前置条件...")
    
    prerequisites = {
        "docker": "docker --version",
        "docker-compose": "docker-compose --version",
    }
    
    missing_tools = []
    
    for tool, command in prerequisites.items():
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"  ✅ {tool}: 已安装")
            else:
                print(f"  ❌ {tool}: 未找到")
                missing_tools.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  ❌ {tool}: 未找到")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n⚠️  缺少工具: {', '.join(missing_tools)}")
        print("请安装缺少的工具后重新运行")
        return False
    
    return True

def create_elk_docker_compose():
    """创建ELK Stack Docker Compose配置"""
    print("🐳 创建ELK Stack Docker Compose配置...")
    
    docker_compose_content = """
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: lawsker-elasticsearch
    restart: unless-stopped
    environment:
      - node.name=elasticsearch
      - cluster.name=lawsker-elk-cluster
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
      - ./config/elasticsearch/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    ports:
      - "9200:9200"
      - "9300:9300"
    networks:
      - elk-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: lawsker-logstash
    restart: unless-stopped
    environment:
      - "LS_JAVA_OPTS=-Xmx512m -Xms512m"
    volumes:
      - ./config/logstash/logstash.yml:/usr/share/logstash/config/logstash.yml
      - ./config/logstash/pipelines.yml:/usr/share/logstash/config/pipelines.yml
      - ./config/logstash/pipeline:/usr/share/logstash/pipeline
      - ./logs:/usr/share/logstash/logs
    ports:
      - "5044:5044"
      - "9600:9600"
      - "5000:5000/tcp"
      - "5000:5000/udp"
    networks:
      - elk-network
    depends_on:
      elasticsearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9600/_node/stats || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: lawsker-kibana
    restart: unless-stopped
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - SERVER_NAME=kibana
      - SERVER_HOST=0.0.0.0
    volumes:
      - ./config/kibana/kibana.yml:/usr/share/kibana/config/kibana.yml
    ports:
      - "5601:5601"
    networks:
      - elk-network
    depends_on:
      elasticsearch:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: lawsker-filebeat
    restart: unless-stopped
    user: root
    volumes:
      - ./config/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/var/log/lawsker:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - filebeat-data:/usr/share/filebeat/data
    networks:
      - elk-network
    depends_on:
      logstash:
        condition: service_healthy
    command: filebeat -e -strict.perms=false

volumes:
  elasticsearch-data:
  filebeat-data:

networks:
  elk-network:
    driver: bridge
"""
    
    with open("docker-compose.elk.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose_content)
    
    print("  ✅ ELK Stack Docker Compose配置已创建: docker-compose.elk.yml")
    return True

def create_elasticsearch_config():
    """创建Elasticsearch配置"""
    print("🔍 创建Elasticsearch配置...")
    
    config_dir = Path("config/elasticsearch")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    elasticsearch_yml = """
cluster.name: "lawsker-elk-cluster"
node.name: "elasticsearch"
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
bootstrap.memory_lock: true

# Security settings
xpack.security.enabled: false
xpack.security.enrollment.enabled: false

# Index settings
action.auto_create_index: true
action.destructive_requires_name: true

# Monitoring
xpack.monitoring.collection.enabled: true

# Machine learning
xpack.ml.enabled: false

# Watcher
xpack.watcher.enabled: false
"""
    
    with open(config_dir / "elasticsearch.yml", "w", encoding="utf-8") as f:
        f.write(elasticsearch_yml)
    
    print(f"  ✅ Elasticsearch配置已创建: {config_dir / 'elasticsearch.yml'}")
    return True

def create_logstash_config():
    """创建Logstash配置"""
    print("📊 创建Logstash配置...")
    
    config_dir = Path("config/logstash")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Logstash主配置
    logstash_yml = """
http.host: "0.0.0.0"
path.config: /usr/share/logstash/pipeline
path.logs: /usr/share/logstash/logs
xpack.monitoring.enabled: false
"""
    
    with open(config_dir / "logstash.yml", "w", encoding="utf-8") as f:
        f.write(logstash_yml)
    
    # Pipeline配置
    pipelines_yml = """
- pipeline.id: lawsker-logs
  path.config: "/usr/share/logstash/pipeline/lawsker.conf"
"""
    
    with open(config_dir / "pipelines.yml", "w", encoding="utf-8") as f:
        f.write(pipelines_yml)
    
    # Pipeline目录
    pipeline_dir = config_dir / "pipeline"
    pipeline_dir.mkdir(exist_ok=True)
    
    # Lawsker日志处理配置
    lawsker_conf = """
input {
  beats {
    port => 5044
  }
  
  tcp {
    port => 5000
    codec => json_lines
  }
  
  udp {
    port => 5000
    codec => json_lines
  }
}

filter {
  # 处理应用日志
  if [fields][log_type] == "application" {
    mutate {
      add_field => { "log_category" => "application" }
    }
    
    # 解析日志级别
    if [message] =~ /ERROR/ {
      mutate { add_field => { "log_level" => "ERROR" } }
    } else if [message] =~ /WARN/ {
      mutate { add_field => { "log_level" => "WARN" } }
    } else if [message] =~ /INFO/ {
      mutate { add_field => { "log_level" => "INFO" } }
    } else if [message] =~ /DEBUG/ {
      mutate { add_field => { "log_level" => "DEBUG" } }
    }
    
    # 提取异常信息
    if [message] =~ /Exception|Error|Traceback/ {
      mutate { add_field => { "has_exception" => "true" } }
    }
  }
  
  # 处理访问日志
  if [fields][log_type] == "access" {
    mutate {
      add_field => { "log_category" => "access" }
    }
    
    # 解析Nginx访问日志格式
    grok {
      match => { 
        "message" => "%{IPORHOST:remote_addr} - %{DATA:remote_user} \\[%{HTTPDATE:time_local}\\] \"%{WORD:method} %{DATA:request} HTTP/%{NUMBER:http_version}\" %{INT:status} %{INT:body_bytes_sent} \"%{DATA:http_referer}\" \"%{DATA:http_user_agent}\" %{NUMBER:request_time}" 
      }
    }
    
    # 转换数据类型
    mutate {
      convert => { 
        "status" => "integer"
        "body_bytes_sent" => "integer"
        "request_time" => "float"
      }
    }
    
    # 添加状态码分类
    if [status] >= 500 {
      mutate { add_field => { "status_category" => "5xx" } }
    } else if [status] >= 400 {
      mutate { add_field => { "status_category" => "4xx" } }
    } else if [status] >= 300 {
      mutate { add_field => { "status_category" => "3xx" } }
    } else if [status] >= 200 {
      mutate { add_field => { "status_category" => "2xx" } }
    }
  }
  
  # 处理安全日志
  if [fields][log_type] == "security" {
    mutate {
      add_field => { "log_category" => "security" }
    }
    
    # 检测安全事件
    if [message] =~ /login.*failed|authentication.*failed|unauthorized|forbidden/ {
      mutate { add_field => { "security_event" => "auth_failure" } }
    } else if [message] =~ /login.*success|authentication.*success/ {
      mutate { add_field => { "security_event" => "auth_success" } }
    } else if [message] =~ /sql.*injection|xss|csrf/ {
      mutate { add_field => { "security_event" => "attack_attempt" } }
    }
  }
  
  # 添加通用字段
  mutate {
    add_field => { 
      "environment" => "${ENVIRONMENT:development}"
      "service" => "lawsker"
    }
  }
  
  # 解析时间戳
  date {
    match => [ "@timestamp", "ISO8601" ]
  }
}

output {
  # 根据日志类型输出到不同索引
  if [log_category] == "application" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "lawsker-app-logs-%{+YYYY.MM.dd}"
      template_name => "lawsker-app-logs"
    }
  } else if [log_category] == "access" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "lawsker-access-logs-%{+YYYY.MM.dd}"
      template_name => "lawsker-access-logs"
    }
  } else if [log_category] == "security" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "lawsker-security-logs-%{+YYYY.MM.dd}"
      template_name => "lawsker-security-logs"
    }
  } else {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "lawsker-general-logs-%{+YYYY.MM.dd}"
    }
  }
  
  # 调试输出（可选）
  # stdout { codec => rubydebug }
}
"""
    
    with open(pipeline_dir / "lawsker.conf", "w", encoding="utf-8") as f:
        f.write(lawsker_conf)
    
    print(f"  ✅ Logstash配置已创建: {config_dir}")
    return True

def create_kibana_config():
    """创建Kibana配置"""
    print("📊 创建Kibana配置...")
    
    config_dir = Path("config/kibana")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    kibana_yml = """
server.name: kibana
server.host: 0.0.0.0
server.port: 5601
elasticsearch.hosts: ["http://elasticsearch:9200"]

# Monitoring
monitoring.ui.container.elasticsearch.enabled: true

# Security
xpack.security.enabled: false
xpack.encryptedSavedObjects.encryptionKey: "lawsker_kibana_encryption_key_32_chars"

# Logging
logging.appenders.file.type: file
logging.appenders.file.fileName: /usr/share/kibana/logs/kibana.log
logging.appenders.file.layout.type: json
logging.root.appenders: [default, file]
logging.root.level: info

# Telemetry
telemetry.enabled: false
telemetry.optIn: false

# Maps
map.includeElasticMapsService: false
"""
    
    with open(config_dir / "kibana.yml", "w", encoding="utf-8") as f:
        f.write(kibana_yml)
    
    print(f"  ✅ Kibana配置已创建: {config_dir / 'kibana.yml'}")
    return True

def create_filebeat_config():
    """创建Filebeat配置"""
    print("📄 创建Filebeat配置...")
    
    config_dir = Path("config/filebeat")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    filebeat_yml = """
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/lawsker/app/*.log
  fields:
    log_type: application
    service: lawsker-api
  fields_under_root: false
  multiline.pattern: '^\\d{4}-\\d{2}-\\d{2}'
  multiline.negate: true
  multiline.match: after

- type: log
  enabled: true
  paths:
    - /var/log/lawsker/access/*.log
  fields:
    log_type: access
    service: lawsker-nginx
  fields_under_root: false

- type: log
  enabled: true
  paths:
    - /var/log/lawsker/security/*.log
  fields:
    log_type: security
    service: lawsker-security
  fields_under_root: false

- type: container
  enabled: true
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
    - add_docker_metadata:
        host: "unix:///var/run/docker.sock"

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: false

setup.template.settings:
  index.number_of_shards: 1
  index.codec: best_compression

setup.kibana:
  host: "kibana:5601"

output.logstash:
  hosts: ["logstash:5044"]

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_docker_metadata: ~
  - add_kubernetes_metadata: ~

logging.level: info
logging.to_files: true
logging.files:
  path: /usr/share/filebeat/logs
  name: filebeat
  keepfiles: 7
  permissions: 0644
"""
    
    with open(config_dir / "filebeat.yml", "w", encoding="utf-8") as f:
        f.write(filebeat_yml)
    
    print(f"  ✅ Filebeat配置已创建: {config_dir / 'filebeat.yml'}")
    return True

def create_log_directories():
    """创建日志目录"""
    print("📁 创建日志目录...")
    
    log_dirs = [
        "logs/app",
        "logs/access", 
        "logs/security",
        "logs/system"
    ]
    
    for log_dir in log_dirs:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ 创建目录: {log_dir}")
    
    return True

def deploy_elk_stack():
    """部署ELK Stack"""
    print("🚀 部署ELK Stack...")
    
    try:
        # 停止现有服务
        print("  🛑 停止现有服务...")
        subprocess.run([
            "docker-compose", "-f", "docker-compose.elk.yml", "down"
        ], capture_output=True)
        
        # 启动服务
        print("  🚀 启动ELK服务...")
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.elk.yml", "up", "-d"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ❌ 服务启动失败: {result.stderr}")
            return False
        
        print("  ✅ ELK服务启动成功")
        
        # 等待服务启动
        print("  ⏳ 等待服务启动...")
        time.sleep(60)  # ELK需要更长时间启动
        
        # 检查服务状态
        print("  🔍 检查服务状态...")
        status_result = subprocess.run([
            "docker-compose", "-f", "docker-compose.elk.yml", "ps"
        ], capture_output=True, text=True)
        
        print("  📊 服务状态:")
        print(status_result.stdout)
        
        return True
        
    except Exception as e:
        print(f"  ❌ 部署失败: {str(e)}")
        return False

async def configure_elk_stack():
    """配置ELK Stack"""
    print("⚙️  配置ELK Stack...")
    
    try:
        # 等待ELK服务完全启动
        print("  ⏳ 等待ELK服务完全启动...")
        max_retries = 60
        for i in range(max_retries):
            try:
                status = await elk_service.get_elk_status()
                if (status.get("elasticsearch", {}).get("connected") and 
                    status.get("kibana", {}).get("connected")):
                    print("  ✅ ELK服务已启动")
                    break
            except:
                pass
            
            if i == max_retries - 1:
                print("  ❌ ELK服务启动超时")
                return False
            
            time.sleep(10)
        
        # 设置ELK配置
        print("  📊 设置ELK配置...")
        setup_result = await setup_elk_logging()
        
        if setup_result.get("status") == "success":
            print("  ✅ ELK配置设置成功")
            
            # 显示结果摘要
            elasticsearch = setup_result.get("elasticsearch", {})
            kibana = setup_result.get("kibana", {})
            indices = setup_result.get("indices", [])
            dashboards = setup_result.get("dashboards", [])
            
            print(f"    🔍 Elasticsearch: {elasticsearch.get('cluster_status', 'unknown')}")
            print(f"    📊 Kibana: {kibana.get('overall_status', 'unknown')}")
            print(f"    📋 索引模板: {len([i for i in indices if i['status'] == 'created'])} 个")
            print(f"    📈 仪表盘: {len([d for d in dashboards if d['status'] == 'created'])} 个")
            
            return True
        else:
            print(f"  ❌ ELK配置失败: {setup_result.get('errors', [])}")
            return False
            
    except Exception as e:
        print(f"  ❌ 配置失败: {str(e)}")
        return False

def print_deployment_summary():
    """打印部署摘要"""
    print("\n" + "="*60)
    print("📋 ELK Stack部署摘要")
    print("="*60)
    print("🎉 ELK Stack日志聚合系统部署完成！")
    print("\n📊 访问地址:")
    print("  🔍 Elasticsearch: http://localhost:9200")
    print("  📊 Kibana: http://localhost:5601")
    print("  📄 Logstash: http://localhost:9600")
    print("\n📋 日志类型:")
    print("  📱 应用日志: lawsker-app-logs-*")
    print("  🌐 访问日志: lawsker-access-logs-*")
    print("  🔒 安全日志: lawsker-security-logs-*")
    print("\n📋 后续步骤:")
    print("  1. 访问Kibana并检查索引模式")
    print("  2. 配置日志收集器指向Logstash")
    print("  3. 创建自定义仪表盘和可视化")
    print("  4. 设置日志告警规则")
    print("  5. 配置日志保留策略")
    print("  6. 设置备份和恢复策略")

async def check_deployment_status():
    """检查部署状态"""
    print("🔍 检查ELK Stack部署状态...")
    
    try:
        # 检查Docker服务
        print("\n📊 Docker服务状态:")
        result = subprocess.run([
            "docker-compose", "-f", "docker-compose.elk.yml", "ps"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("  ❌ 无法获取Docker服务状态")
        
        # 检查ELK状态
        print("\n📊 ELK Stack状态:")
        elk_status = await elk_service.get_elk_status()
        
        for service, status in elk_status.items():
            if status.get("connected"):
                print(f"  ✅ {service.capitalize()}: 连接正常")
                if service == "elasticsearch":
                    print(f"    集群状态: {status.get('status', 'unknown')}")
                    print(f"    节点数量: {status.get('number_of_nodes', 0)}")
                elif service == "kibana":
                    print(f"    版本: {status.get('version', 'unknown')}")
                    print(f"    状态: {status.get('status', 'unknown')}")
            else:
                print(f"  ❌ {service.capitalize()}: 连接失败")
                if "error" in status:
                    print(f"    错误: {status['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 状态检查失败: {str(e)}")
        return False

def show_help():
    """显示帮助信息"""
    print("ELK Stack日志聚合系统部署工具")
    print("\n用法:")
    print("  python deploy_elk.py [选项]")
    print("\n选项:")
    print("  --deploy, -d    完整部署ELK Stack")
    print("  --config, -c    仅创建配置文件")
    print("  --status, -s    检查部署状态")
    print("  --help, -h      显示此帮助信息")

async def main():
    """主函数"""
    print_banner()
    
    # 解析命令行参数
    args = sys.argv[1:]
    
    if not args or "--help" in args or "-h" in args:
        show_help()
        return
    
    try:
        if "--deploy" in args or "-d" in args:
            # 完整部署
            success = True
            
            # 检查前置条件
            if not check_prerequisites():
                success = False
            
            # 创建配置文件
            if success:
                print_section_header("创建配置文件")
                success = (
                    create_elk_docker_compose() and
                    create_elasticsearch_config() and
                    create_logstash_config() and
                    create_kibana_config() and
                    create_filebeat_config() and
                    create_log_directories()
                )
            
            # 部署ELK Stack
            if success:
                print_section_header("部署ELK Stack")
                success = deploy_elk_stack()
            
            # 配置ELK Stack
            if success:
                print_section_header("配置ELK Stack")
                success = await configure_elk_stack()
            
            if success:
                print_deployment_summary()
                print("\n✅ ELK Stack部署成功")
            else:
                print("\n❌ ELK Stack部署失败")
            
        elif "--config" in args or "-c" in args:
            # 仅创建配置文件
            print_section_header("创建配置文件")
            success = (
                create_elk_docker_compose() and
                create_elasticsearch_config() and
                create_logstash_config() and
                create_kibana_config() and
                create_filebeat_config() and
                create_log_directories()
            )
            
            if success:
                print("\n✅ 配置文件创建完成")
            else:
                print("\n❌ 配置文件创建失败")
                
        elif "--status" in args or "-s" in args:
            # 检查状态
            success = await check_deployment_status()
            
        else:
            print("❌ 未知选项，使用 --help 查看帮助")
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())