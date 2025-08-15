# 🐳 Docker 安裝指南

本指南將幫助您在TrueNAS Scale和其他Linux系統上安裝Docker和Docker Compose，以便運行股票分析報告生成器。

## 📋 目錄

- [TrueNAS Scale 安裝](#truenas-scale-安裝)
- [Ubuntu/Debian 安裝](#ubuntudebian-安裝)
- [CentOS/RHEL 安裝](#centosrhel-安裝)
- [Arch Linux 安裝](#arch-linux-安裝)
- [安裝驗證](#安裝驗證)
- [故障排除](#故障排除)

## 🏠 TrueNAS Scale 安裝

### 方法一：使用TrueNAS Scale內置Apps
1. **登錄TrueNAS Scale Web界面**
2. **導航到Apps頁面**
3. **安裝Docker應用**：
   - 點擊 "Discover Apps"
   - 搜索並安裝官方Docker應用
   - 按照向導完成安裝

### 方法二：命令行安裝（高級用戶）

```bash
# 1. 啟用Docker服務
sudo systemctl enable docker
sudo systemctl start docker

# 2. 添加用戶到docker組
sudo usermod -aG docker $USER

# 3. 重新登錄以應用組更改
newgrp docker

# 4. 安裝Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### TrueNAS Scale 特殊配置

```bash
# 1. 創建應用目錄
sudo mkdir -p /mnt/tank/apps/stock-analyzer
cd /mnt/tank/apps/stock-analyzer

# 2. 設置權限
sudo chown -R $USER:$USER /mnt/tank/apps/stock-analyzer

# 3. 配置防火牆（如果需要）
sudo ufw allow 8501/tcp
```

## 🐧 Ubuntu/Debian 安裝

### 自動安裝腳本

```bash
#!/bin/bash
# Ubuntu/Debian Docker 一鍵安裝腳本

# 更新包索引
sudo apt-get update

# 安裝必要的包
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加Docker官方GPG密鑰
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker倉庫
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新包索引
sudo apt-get update

# 安裝Docker Engine
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 安裝Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 添加當前用戶到docker組
sudo usermod -aG docker $USER

# 啟動Docker服務
sudo systemctl enable docker
sudo systemctl start docker

echo "✅ Docker 安裝完成！請重新登錄以應用組更改。"
```

### 手動安裝步驟

```bash
# 1. 移除舊版本
sudo apt-get remove docker docker-engine docker.io containerd runc

# 2. 更新包索引
sudo apt-get update

# 3. 安裝必要包
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 4. 添加Docker GPG密鑰
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 5. 設置倉庫
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 6. 安裝Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io

# 7. 安裝Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 8. 配置用戶權限
sudo usermod -aG docker $USER

# 9. 啟動服務
sudo systemctl enable docker
sudo systemctl start docker
```

## 🎩 CentOS/RHEL 安裝

### CentOS 8/RHEL 8

```bash
# 1. 移除舊版本
sudo dnf remove docker \
                docker-client \
                docker-client-latest \
                docker-common \
                docker-latest \
                docker-latest-logrotate \
                docker-logrotate \
                docker-engine

# 2. 安裝dnf-plugins-core
sudo dnf install -y dnf-plugins-core

# 3. 添加Docker倉庫
sudo dnf config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# 4. 安裝Docker Engine
sudo dnf install docker-ce docker-ce-cli containerd.io

# 5. 安裝Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 6. 啟動Docker
sudo systemctl enable docker
sudo systemctl start docker

# 7. 添加用戶到docker組
sudo usermod -aG docker $USER
```

### CentOS 7/RHEL 7

```bash
# 1. 移除舊版本
sudo yum remove docker \
                docker-client \
                docker-client-latest \
                docker-common \
                docker-latest \
                docker-latest-logrotate \
                docker-logrotate \
                docker-engine

# 2. 安裝必要包
sudo yum install -y yum-utils

# 3. 添加Docker倉庫
sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# 4. 安裝Docker Engine
sudo yum install docker-ce docker-ce-cli containerd.io

# 5. 安裝Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 6. 啟動Docker
sudo systemctl enable docker
sudo systemctl start docker

# 7. 添加用戶到docker組
sudo usermod -aG docker $USER
```

## 🏛️ Arch Linux 安裝

```bash
# 1. 更新系統
sudo pacman -Syu

# 2. 安裝Docker
sudo pacman -S docker docker-compose

# 3. 啟動並啟用Docker服務
sudo systemctl enable docker.service
sudo systemctl start docker.service

# 4. 添加用戶到docker組
sudo usermod -aG docker $USER

# 5. 重新登錄
newgrp docker
```

## ✅ 安裝驗證

### 基本驗證

```bash
# 1. 檢查Docker版本
docker --version
# 輸出示例: Docker version 24.0.0, build 1234567

# 2. 檢查Docker Compose版本
docker-compose --version
# 或者 (新版本)
docker compose version
# 輸出示例: Docker Compose version v2.20.0

# 3. 檢查Docker服務狀態
sudo systemctl status docker

# 4. 運行測試容器
docker run hello-world
```

### 權限驗證

```bash
# 1. 不使用sudo運行Docker命令
docker ps

# 2. 如果出現權限錯誤，檢查用戶組
groups $USER

# 3. 如果沒有docker組，重新添加並重新登錄
sudo usermod -aG docker $USER
newgrp docker
```

### 高級驗證

```bash
# 1. 檢查Docker信息
docker info

# 2. 檢查Docker存儲位置
docker system df

# 3. 測試網絡功能
docker network ls

# 4. 測試卷功能
docker volume ls
```

## 🔧 故障排除

### 常見問題及解決方案

#### 1. 權限被拒絕錯誤
```bash
# 錯誤: permission denied while trying to connect to the Docker daemon
# 解決方案:
sudo usermod -aG docker $USER
newgrp docker
# 或者重新登錄
```

#### 2. Docker服務未啟動
```bash
# 檢查服務狀態
sudo systemctl status docker

# 啟動服務
sudo systemctl start docker

# 啟用開機自啟
sudo systemctl enable docker
```

#### 3. Docker Compose命令不存在
```bash
# 檢查安裝位置
which docker-compose

# 如果不存在，重新安裝
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 添加到PATH (如果需要)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 4. 網絡連接問題
```bash
# 檢查防火牆設置
sudo ufw status

# 允許Docker端口
sudo ufw allow 8501/tcp

# 檢查Docker網絡
docker network ls
```

#### 5. 存儲空間不足
```bash
# 檢查Docker空間使用
docker system df

# 清理未使用的資源
docker system prune

# 清理所有未使用的資源（慎用）
docker system prune -a
```

### TrueNAS Scale 特殊問題

#### 1. 持久化存儲配置
```bash
# 確保數據目錄在持久化存儲上
mkdir -p /mnt/tank/apps/stock-analyzer/data
mkdir -p /mnt/tank/apps/stock-analyzer/logs

# 設置正確的權限
sudo chown -R 1000:1000 /mnt/tank/apps/stock-analyzer/
```

#### 2. 網絡訪問問題
```bash
# 檢查TrueNAS網絡設置
ip addr show

# 確保端口8501可訪問
netstat -tlnp | grep 8501
```

## 🚀 下一步

安裝完成後，請查看 [docker_usage.md](docker_usage.md) 了解如何使用Docker運行股票分析器。

### 快速啟動
```bash
# 1. 克隆項目
git clone <your-repo-url>
cd news_steamlit

# 2. 配置API密鑰
cp config.py.example config.py
# 編輯config.py添加您的API密鑰

# 3. 啟動應用
./start.sh

# 4. 訪問應用
open http://localhost:8501
```

## 📞 支持

如果遇到安裝問題：

1. **檢查系統兼容性**: 確保系統滿足最低要求
2. **查看日誌**: 使用 `sudo journalctl -u docker` 查看Docker日誌
3. **官方文檔**: 參考 [Docker官方安裝文檔](https://docs.docker.com/engine/install/)
4. **社區支持**: 搜索Stack Overflow或Docker社區

---

<div align="center">
  <strong>🐳 Docker安裝完成後，您就可以輕鬆部署股票分析器了！ 🚀</strong>
</div>
