#!/bin/bash

# 啟動腳本：同時運行Streamlit和自動化Worker
# 用於Docker容器中同時運行兩個服務

echo "🚀 開始啟動股票分析服務..."

# 設置日誌目錄權限
chmod -R 777 /app/data
chmod -R 777 /app/logs

# 創建日誌目錄（如果不存在）
mkdir -p /app/logs
mkdir -p /app/data

echo "📂 目錄權限設置完成"

# 啟動自動化Worker（背景運行）
echo "🤖 啟動自動化Worker..."
python start_auto_worker.py &
WORKER_PID=$!

echo "📊 自動化Worker已啟動 (PID: $WORKER_PID)"

# 等待幾秒確保Worker啟動
sleep 5

# 啟動Streamlit應用
echo "🌐 啟動Streamlit應用..."
exec streamlit run run_streamlit.py \
    --server.address=0.0.0.0 \
    --server.port=8502 \
    --server.headless=true \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false

# 如果Streamlit退出，也停止Worker
echo "🛑 Streamlit已停止，正在停止Worker..."
kill $WORKER_PID 2>/dev/null
