# 使用官方Python 3.11基礎鏡像（bullseye）
FROM python:3.11-slim-bullseye

# 工作目錄
WORKDIR /app

# 環境變數
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/home/appuser/.local/bin:$PATH

# 安裝系統依賴和PDF生成工具（用 root）
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    wkhtmltopdf \
    xvfb \
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-noto-color-emoji \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 創建非 root 用戶
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# 切換到非 root
USER appuser

# 複製 requirements
COPY --chown=appuser:appuser requirements.txt .

# 安裝 Python 依賴（user 安裝會放到 $HOME/.local/bin）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY --chown=appuser:appuser . .

# 暴露端口
EXPOSE 8502

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

# 啟動命令
CMD ["streamlit", "run", "run_streamlit.py", "--server.address", "0.0.0.0", "--server.port", "8502", "--server.headless", "true", "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"]
