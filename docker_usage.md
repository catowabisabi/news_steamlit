# 🚀 Docker 使用指南

本指南詳細介紹如何在TrueNAS Scale和其他Linux系統上使用Docker運行股票分析報告生成器。

## 📋 目錄

- [快速開始](#快速開始)
- [TrueNAS Scale 部署](#truenas-scale-部署)
- [配置說明](#配置說明)
- [使用方法](#使用方法)
- [數據管理](#數據管理)
- [監控和日誌](#監控和日誌)
- [故障排除](#故障排除)
- [進階配置](#進階配置)

## 🏃‍♂️ 快速開始

### 一鍵部署

```bash
# 1. 下載項目文件
curl -O https://raw.githubusercontent.com/your-repo/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/your-repo/main/start.sh
chmod +x start.sh

# 2. 創建配置文件
cat > config.py << 'EOF'
# API 配置
OPENAI_API_KEY = "your_openai_api_key_here"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"

# MongoDB 配置 (可選)
MONGODB_URI = "your_mongodb_uri_here"
EOF

# 3. 一鍵啟動
./start.sh

# 4. 訪問應用
echo "🌐 請訪問: http://localhost:8501"
```

### 手動部署

```bash
# 1. 創建項目目錄
mkdir stock-analyzer && cd stock-analyzer

# 2. 創建docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  stock-analyzer:
    image: your-registry/stock-analyzer:latest
    container_name: stock-analyzer
    restart: unless-stopped
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./config.py:/app/config.py:ro
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Hong_Kong
EOF

# 3. 啟動服務
docker-compose up -d

# 4. 查看狀態
docker-compose ps
```

## 🏠 TrueNAS Scale 部署

### 方法一：使用TrueNAS Apps（推薦）

1. **準備工作**
   ```bash
   # 在TrueNAS Shell中創建應用目錄
   mkdir -p /mnt/tank/apps/stock-analyzer
   cd /mnt/tank/apps/stock-analyzer
   ```

2. **配置文件準備**
   ```bash
   # 創建配置文件
   cat > config.py << 'EOF'
   OPENAI_API_KEY = "sk-your-openai-key"
   DEEPSEEK_API_KEY = "sk-your-deepseek-key"
   MONGODB_URI = "mongodb://localhost:27017"
   
   # 其他配置保持默認
   EOF
   
   # 創建必要目錄
   mkdir -p data logs
   chmod -R 755 data logs
   ```

3. **Docker Compose 配置**
   ```yaml
   # docker-compose.yml for TrueNAS Scale
   version: '3.8'
   
   services:
     stock-analyzer:
       image: your-registry/stock-analyzer:latest
       container_name: stock-analyzer
       restart: unless-stopped
       ports:
         - "8501:8501"
       volumes:
         # 使用TrueNAS持久化存儲
         - /mnt/tank/apps/stock-analyzer/data:/app/data
         - /mnt/tank/apps/stock-analyzer/config.py:/app/config.py:ro
         - /mnt/tank/apps/stock-analyzer/logs:/app/logs
       environment:
         - TZ=Asia/Hong_Kong
         - PYTHONUNBUFFERED=1
       networks:
         - stock-analyzer-net
       deploy:
         resources:
           limits:
             memory: 2G
             cpus: '1.0'
           reservations:
             memory: 512M
             cpus: '0.25'
   
   networks:
     stock-analyzer-net:
       driver: bridge
   ```

4. **啟動和管理**
   ```bash
   # 啟動服務
   docker-compose up -d
   
   # 檢查狀態
   docker-compose ps
   
   # 查看日誌
   docker-compose logs -f
   ```

### 方法二：TrueNAS Apps界面部署

1. **導航到Apps**
   - 登錄TrueNAS Scale Web界面
   - 點擊左側菜單的"Apps"

2. **安裝Custom App**
   - 點擊"Launch Docker Image"
   - 填寫以下信息：
     - **Application Name**: `stock-analyzer`
     - **Image repository**: `your-registry/stock-analyzer`
     - **Image Tag**: `latest`

3. **網絡配置**
   - **Port**: `8501`
   - **Protocol**: `TCP`
   - **Host Port**: `8501`

4. **存儲配置**
   ```
   Host Path: /mnt/tank/apps/stock-analyzer/data
   Mount Path: /app/data
   
   Host Path: /mnt/tank/apps/stock-analyzer/config.py
   Mount Path: /app/config.py
   Read Only: ✓
   
   Host Path: /mnt/tank/apps/stock-analyzer/logs
   Mount Path: /app/logs
   ```

5. **環境變數**
   ```
   TZ=Asia/Hong_Kong
   PYTHONUNBUFFERED=1
   ```

## ⚙️ 配置說明

### 基本配置文件 (config.py)

```python
# config.py 完整配置示例

# ====== API 配置 ======
# OpenAI API 配置
OPENAI_API_KEY = "sk-your-openai-key-here"

# DeepSeek API 配置  
DEEPSEEK_API_KEY = "sk-your-deepseek-key-here"

# ====== 數據庫配置 ======
# MongoDB 連接 (可選)
MONGODB_URI = "mongodb://username:password@host:port/database"

# ====== 新聞API配置 ======
NEWS_API_BASE_URL = "http://news.enomars.org/api/news"

# ====== 系統配置 ======
# 數據存儲路徑
DATA_BASE_PATH = "./data"

# PDF 生成配置
WKHTMLTOPDF_PATH = "/usr/bin/wkhtmltopdf"  # Docker中自動配置

# ====== LLM 配置 ======
# ChatGPT 模型配置
CHATGPT_MODEL = "gpt-3.5-turbo"
CHATGPT_MAX_TOKENS = 4000
CHATGPT_TEMPERATURE = 0.7

# DeepSeek 模型配置
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_MAX_TOKENS = 4000
DEEPSEEK_TEMPERATURE = 0.5

# ====== 緩存配置 ======
ENABLE_CACHE = True
CACHE_EXPIRE_HOURS = 24

# ====== 日誌配置 ======
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 環境變數配置

```bash
# .env 文件 (可選，優先級高於config.py)
OPENAI_API_KEY=sk-your-openai-key
DEEPSEEK_API_KEY=sk-your-deepseek-key
MONGODB_URI=mongodb://localhost:27017
TZ=Asia/Hong_Kong
LOG_LEVEL=INFO
```

### Docker Compose 高級配置

```yaml
version: '3.8'

services:
  stock-analyzer:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - PYTHON_VERSION=3.11
    container_name: stock-analyzer
    hostname: stock-analyzer
    restart: unless-stopped
    
    # 網絡配置
    ports:
      - "8501:8501"
    networks:
      - stock-net
    
    # 存儲配置
    volumes:
      - ./data:/app/data:rw
      - ./config.py:/app/config.py:ro
      - ./logs:/app/logs:rw
      - /etc/localtime:/etc/localtime:ro
    
    # 環境配置
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONIOENCODING=utf-8
      - TZ=Asia/Hong_Kong
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - STREAMLIT_SERVER_PORT=8501
    
    # 資源限制
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    
    # 健康檢查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    # 安全配置
    user: "1000:1000"
    read_only: false
    tmpfs:
      - /tmp
    
    # 日誌配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  stock-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 📱 使用方法

### 1. 啟動服務

```bash
# 使用啟動腳本 (推薦)
./start.sh

# 或手動啟動
docker-compose up -d

# 檢查啟動狀態
docker-compose ps
```

### 2. 訪問應用

```bash
# 本地訪問
http://localhost:8501

# 局域網訪問 (將IP替換為實際IP)
http://192.168.1.100:8501

# TrueNAS Scale訪問
http://truenas-ip:8501
```

### 3. 使用Web界面

1. **輸入股票代碼**
   ```
   單個股票: AAPL
   多個股票: AAPL, TSLA, MSFT
   ```

2. **查看分析報告**
   - 中文報告標籤頁
   - 英文報告標籤頁
   - 實時處理進度

3. **下載報告**
   - PDF格式下載
   - Markdown格式下載

### 4. 數據管理

```bash
# 查看數據結構
ls -la data/
# 輸出示例:
# data/
# ├── 2025-01-15/
# │   ├── AAPL/
# │   │   ├── news_2025-01-15.json
# │   │   ├── analysis_2025-01-15.json
# │   │   └── *.pdf
# │   └── TSLA/
# └── 2025-01-14/

# 清理舊數據 (7天前)
find data/ -type d -mtime +7 -exec rm -rf {} \;
```

## 📊 監控和日誌

### 容器狀態監控

```bash
# 查看容器狀態
docker ps -f name=stock-analyzer

# 查看資源使用
docker stats stock-analyzer

# 查看容器詳細信息
docker inspect stock-analyzer

# 健康檢查狀態
docker inspect --format='{{.State.Health.Status}}' stock-analyzer
```

### 日誌管理

```bash
# 查看實時日誌
docker logs -f stock-analyzer

# 查看最近100行日誌
docker logs --tail 100 stock-analyzer

# 查看特定時間日誌
docker logs --since="2025-01-15T10:00:00" stock-analyzer

# 查看應用日誌文件
tail -f logs/app.log
```

### 性能監控

```bash
# 監控腳本 (monitor.sh)
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    docker stats --no-stream stock-analyzer
    echo "Memory usage:"
    docker exec stock-analyzer free -h
    echo "Disk usage:"
    docker exec stock-analyzer df -h
    echo "========================"
    sleep 60
done
```

## 🔧 故障排除

### 常見問題及解決方案

#### 1. 容器無法啟動

```bash
# 檢查容器狀態
docker ps -a -f name=stock-analyzer

# 查看啟動日誌
docker logs stock-analyzer

# 常見原因:
# - 端口被占用
# - 配置文件錯誤
# - 權限問題
# - 資源不足

# 解決方案:
# 檢查端口
netstat -tlnp | grep 8501

# 檢查配置
docker exec stock-analyzer cat /app/config.py

# 檢查權限
ls -la data/ logs/
```

#### 2. 無法訪問Web界面

```bash
# 檢查端口映射
docker port stock-analyzer

# 檢查防火牆
sudo ufw status
sudo ufw allow 8501/tcp

# 檢查網絡
docker network ls
docker network inspect stock-analyzer_stock-analyzer-network

# TrueNAS Scale 檢查
# 確保在TrueNAS網絡設置中允許該端口
```

#### 3. API調用失敗

```bash
# 檢查API密鑰配置
docker exec stock-analyzer python -c "
import config
print('OpenAI key configured:', bool(config.OPENAI_API_KEY))
print('DeepSeek key configured:', bool(config.DEEPSEEK_API_KEY))
"

# 測試網絡連接
docker exec stock-analyzer curl -I https://api.openai.com
docker exec stock-analyzer curl -I https://api.deepseek.com

# 檢查DNS解析
docker exec stock-analyzer nslookup api.openai.com
```

#### 4. PDF生成失敗

```bash
# 檢查wkhtmltopdf安裝
docker exec stock-analyzer which wkhtmltopdf
docker exec stock-analyzer wkhtmltopdf --version

# 檢查字體
docker exec stock-analyzer fc-list | grep -i chinese

# 測試PDF生成
docker exec stock-analyzer python -c "
import pdfkit
print('PDF generation test...')
pdfkit.from_string('Hello World', '/tmp/test.pdf')
print('PDF test successful!')
"
```

#### 5. 內存不足問題

```bash
# 檢查內存使用
docker stats stock-analyzer

# 調整資源限制 (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'

# 重啟服務
docker-compose restart
```

### TrueNAS Scale 特殊問題

#### 1. 持久化存儲問題

```bash
# 確保數據在正確的存儲池上
ls -la /mnt/tank/apps/stock-analyzer/

# 檢查權限
sudo chown -R 1000:1000 /mnt/tank/apps/stock-analyzer/
sudo chmod -R 755 /mnt/tank/apps/stock-analyzer/
```

#### 2. 網絡配置問題

```bash
# 檢查TrueNAS網絡設置
ip route show
ip addr show

# 檢查Docker網絡
docker network inspect bridge
```

## 🎛️ 進階配置

### 1. 反向代理配置 (Nginx)

```nginx
# /etc/nginx/sites-available/stock-analyzer
server {
    listen 80;
    server_name stock-analyzer.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### 2. SSL/HTTPS配置

```yaml
# docker-compose-ssl.yml
version: '3.8'

services:
  stock-analyzer:
    # ... 其他配置 ...
    
  nginx:
    image: nginx:alpine
    container_name: stock-analyzer-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - stock-analyzer
    networks:
      - stock-analyzer-network
```

### 3. 自動備份配置

```bash
#!/bin/bash
# backup.sh - 自動備份腳本

BACKUP_DIR="/mnt/tank/backups/stock-analyzer"
DATE=$(date +%Y%m%d_%H%M%S)

# 創建備份目錄
mkdir -p $BACKUP_DIR

# 備份數據
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# 備份配置
cp config.py $BACKUP_DIR/config_$DATE.py

# 清理7天前的備份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "config_*.py" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### 4. 自動更新配置

```bash
#!/bin/bash
# update.sh - 自動更新腳本

echo "Pulling latest image..."
docker-compose pull

echo "Recreating containers..."
docker-compose up -d

echo "Cleaning up old images..."
docker image prune -f

echo "Update completed!"
```

### 5. 監控和告警

```bash
# healthcheck.sh - 健康檢查腳本
#!/bin/bash

CONTAINER_NAME="stock-analyzer"
WEBHOOK_URL="your-webhook-url"

if ! docker ps | grep -q $CONTAINER_NAME; then
    curl -X POST $WEBHOOK_URL \
         -H 'Content-Type: application/json' \
         -d '{"text":"🚨 Stock Analyzer container is down!"}'
    
    # 嘗試重啟
    docker-compose restart
fi

# 檢查Web服務
if ! curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    curl -X POST $WEBHOOK_URL \
         -H 'Content-Type: application/json' \
         -d '{"text":"⚠️ Stock Analyzer web service is not responding!"}'
fi
```

## 📞 支持和維護

### 日常維護任務

```bash
# 每日任務
./start.sh status          # 檢查服務狀態
docker logs --tail 50 stock-analyzer  # 檢查日誌

# 每週任務
docker system prune -f     # 清理未使用資源
./backup.sh               # 執行備份

# 每月任務
./update.sh               # 更新鏡像
docker system df          # 檢查磁盤使用
```

### 獲取支持

1. **查看日誌**: 首先檢查容器和應用日誌
2. **檢查配置**: 確認所有配置文件正確
3. **測試網絡**: 驗證網絡連接和DNS解析
4. **社區支持**: 提交Issue到GitHub項目

---

<div align="center">
  <strong>🐳 現在您已經掌握了Docker部署股票分析器的完整流程！ 🚀</strong>
</div>
