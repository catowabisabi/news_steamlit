# 使用官方Python 3.11基礎鏡像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安裝系統依賴和PDF生成工具
RUN apt-get update && apt-get install -y \
    # 基本工具
    wget \
    curl \
    git \
    build-essential \
    # wkhtmltopdf和依賴
    wkhtmltopdf \
    xvfb \
    # 字體支持
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-noto-color-emoji \
    # 其他依賴
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    # 清理緩存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 創建非root用戶
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 複製requirements文件
COPY --chown=appuser:appuser requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY --chown=appuser:appuser . .

# 創建數據目錄
RUN mkdir -p /app/data && chmod 755 /app/data

# 暴露端口
EXPOSE 8502

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

# 啟動命令
CMD ["streamlit", "run", "run_streamlit.py", "--server.address", "0.0.0.0", "--server.port", "8502", "--server.headless", "true", "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"]
