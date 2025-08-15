#!/bin/bash

# Stock Analyzer Docker 啟動腳本
# 適用於TrueNAS Scale和其他Linux系統

set -e

# 顏色設置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 項目信息
PROJECT_NAME="stock-analyzer"
CONTAINER_NAME="stock-analyzer"
PORT="8501"

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查Docker是否安裝
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝。請先安裝Docker。"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安裝。請先安裝Docker Compose。"
        exit 1
    fi
    
    log_success "Docker 環境檢查通過"
}

# 檢查權限
check_permissions() {
    if ! docker ps &> /dev/null; then
        log_error "當前用戶沒有Docker權限。請將用戶添加到docker組或使用sudo運行。"
        exit 1
    fi
    log_success "Docker 權限檢查通過"
}

# 創建必要目錄
create_directories() {
    log_info "創建必要目錄..."
    
    mkdir -p data
    mkdir -p logs
    
    # 設置權限
    chmod 755 data logs
    
    log_success "目錄創建完成"
}

# 停止現有容器
stop_existing() {
    log_info "檢查並停止現有容器..."
    
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log_info "停止現有容器..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        log_success "現有容器已停止並移除"
    else
        log_info "沒有發現運行中的容器"
    fi
}

# 構建和啟動
build_and_start() {
    log_info "構建並啟動Stock Analyzer..."
    
    # 使用docker-compose或docker compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # 構建鏡像
    log_info "構建Docker鏡像..."
    $COMPOSE_CMD build --no-cache
    
    # 啟動服務
    log_info "啟動服務..."
    $COMPOSE_CMD up -d
    
    log_success "Stock Analyzer 已啟動"
}

# 等待服務就緒
wait_for_service() {
    log_info "等待服務啟動..."
    
    for i in {1..30}; do
        if curl -s http://localhost:$PORT/_stcore/health > /dev/null 2>&1; then
            log_success "服務已就緒！"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    log_warning "服務可能需要更長時間啟動，請手動檢查"
    return 1
}

# 顯示狀態
show_status() {
    echo ""
    echo "========================================"
    echo "  📊 Stock Analyzer 部署完成"
    echo "========================================"
    echo ""
    echo "🌐 Web界面: http://localhost:$PORT"
    echo "🌐 局域網訪問: http://$(hostname -I | awk '{print $1}'):$PORT"
    echo ""
    echo "📋 常用命令:"
    echo "  查看日誌: docker logs -f $CONTAINER_NAME"
    echo "  停止服務: docker stop $CONTAINER_NAME"
    echo "  重啟服務: docker restart $CONTAINER_NAME"
    echo ""
    echo "📂 數據目錄: $(pwd)/data"
    echo "📂 日誌目錄: $(pwd)/logs"
    echo ""
}

# 主函數
main() {
    echo "========================================"
    echo "  📊 Stock Analyzer Docker 啟動器"
    echo "========================================"
    echo ""
    
    # 檢查系統環境
    check_docker
    check_permissions
    
    # 準備環境
    create_directories
    stop_existing
    
    # 構建和啟動
    build_and_start
    
    # 等待服務就緒
    wait_for_service
    
    # 顯示狀態
    show_status
    
    log_success "部署完成！請訪問 http://localhost:$PORT 開始使用"
}

# 處理參數
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        log_info "停止Stock Analyzer..."
        docker stop $CONTAINER_NAME 2>/dev/null || true
        docker rm $CONTAINER_NAME 2>/dev/null || true
        log_success "Stock Analyzer 已停止"
        ;;
    "restart")
        log_info "重啟Stock Analyzer..."
        docker restart $CONTAINER_NAME
        log_success "Stock Analyzer 已重啟"
        ;;
    "logs")
        log_info "顯示實時日誌 (Ctrl+C退出)..."
        docker logs -f $CONTAINER_NAME
        ;;
    "status")
        if docker ps -f name=$CONTAINER_NAME | grep -q $CONTAINER_NAME; then
            log_success "Stock Analyzer 正在運行"
            docker ps -f name=$CONTAINER_NAME
        else
            log_warning "Stock Analyzer 未運行"
        fi
        ;;
    "help")
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  start   - 啟動服務 (默認)"
        echo "  stop    - 停止服務"
        echo "  restart - 重啟服務"
        echo "  logs    - 查看實時日誌"
        echo "  status  - 查看服務狀態"
        echo "  help    - 顯示此幫助"
        ;;
    *)
        log_error "未知命令: $1"
        echo "使用 '$0 help' 查看可用命令"
        exit 1
        ;;
esac
