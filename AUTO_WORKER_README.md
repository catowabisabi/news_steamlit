# 自動化股票分析Worker使用指南

## 📖 概述

`run_streamlit_auto.py` 是一個自動化背景Worker，能夠：

- 🔄 每30分鐘自動檢查MongoDB中的新symbols
- 📊 自動生成完整的股票分析報告（中英文）
- 📱 自動創建Instagram投資貼文
- 📝 詳細的運行日誌和錯誤追蹤
- ⚠️ 強健的錯誤處理和重試機制

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 檢查配置

確保以下文件已正確配置：
- `.env` - MongoDB連接字符串和其他環境變量
- `config.py` - AI模型配置和提示詞

### 3. 啟動Worker

```bash
# 正常啟動（持續運行）
python start_auto_worker.py

# 測試運行（執行一次然後退出）
python start_auto_worker.py --test-run

# 詳細日誌模式
python start_auto_worker.py --log-level DEBUG
```

## 📋 功能詳細說明

### 🔄 自動化流程

1. **檢查新Symbols**
   - 從MongoDB的 `fundamentals_of_top_list_symbols` 集合中獲取今天的所有symbols
   - 與已處理的symbols比較，識別新的symbols

2. **處理每個新Symbol**
   - 調用 `process_single_stock()` 生成所有必要的數據文件
   - 生成完整的股票分析報告（中英文Markdown和PDF）
   - 創建Instagram投資貼文

3. **文件輸出**
   - `{SYMBOL}_report_{DATE}.md` - 中文Markdown報告
   - `{SYMBOL}_report_english_{DATE}.md` - 英文Markdown報告
   - `{SYMBOL}_report_chinese_{DATE}.pdf` - 中文PDF報告
   - `{SYMBOL}_report_english_{DATE}.pdf` - 英文PDF報告
   - `{SYMBOL}_ig_post_{DATE}.txt` - Instagram貼文

### 📊 運行統計

Worker會追蹤以下統計信息：
- 總運行次數
- 成功生成的報告數量
- 失敗次數
- IG POST生成數量
- 最近的錯誤記錄

### 📝 日誌系統

- **文件日誌**: `logs/auto_worker_{YYYYMMDD}.log`
- **控制台輸出**: 實時顯示處理狀態
- **日誌級別**: DEBUG, INFO, WARNING, ERROR

## ⚙️ 配置選項

### 環境變量

在 `.env` 文件中設置：

```env
# MongoDB配置
MONGODB_CONNECTION_STRING=mongodb://your-connection-string
MONGO_DBNAME=TradeZero_Bot

# AI模型API密鑰
OPENAI_API_KEY=your-openai-key
DEEPSEEK_API_KEY=your-deepseek-key
```

### 排程設置

在 `run_streamlit_auto.py` 中的 `setup_schedule()` 方法：

```python
# 每30分鐘執行一次（可自定義）
schedule.every(30).minutes.do(self.run_once)

# 每小時打印統計
schedule.every().hour.do(self.print_stats)
```

## 🛠️ 故障排除

### 常見問題

1. **MongoDB連接失敗**
   ```
   ❌ MongoDB連接失敗
   ```
   - 檢查 `.env` 中的 `MONGODB_CONNECTION_STRING`
   - 確認MongoDB服務正在運行
   - 檢查網絡連接

2. **報告生成失敗**
   ```
   ❌ {SYMBOL} 報告生成失敗
   ```
   - 檢查是否有必要的數據文件
   - 查看詳細日誌了解具體錯誤
   - 確認AI API密鑰有效

3. **PDF生成失敗**
   ```
   ⚠️ PDF生成失敗（但Markdown成功）
   ```
   - 安裝reportlab: `pip install reportlab`
   - 在Windows上確保中文字體可用
   - 檢查文件權限

### 日誌分析

查看日誌文件 `logs/auto_worker_{date}.log`：

```bash
# 查看最新日誌
tail -f logs/auto_worker_$(date +%Y%m%d).log

# 搜索錯誤
grep "ERROR" logs/auto_worker_*.log

# 搜索特定symbol的處理記錄
grep "AAPL" logs/auto_worker_*.log
```

## 📂 文件結構

```
project/
├── run_streamlit_auto.py      # 主Worker程序
├── start_auto_worker.py       # 啟動腳本
├── report_generator.py        # 報告生成模組
├── process_stock.py          # 股票數據處理
├── ig_post.py               # Instagram貼文生成
├── mongo_db.py              # MongoDB操作
├── file_manager.py          # 文件管理
├── logs/                    # 日誌目錄
│   └── auto_worker_*.log
└── data/                    # 數據輸出目錄
    └── {DATE}/
        └── {SYMBOL}/
            ├── *_report_*.md
            ├── *_report_*.pdf
            └── *_ig_post_*.txt
```

## 🔧 自定義配置

### 修改執行頻率

編輯 `run_streamlit_auto.py` 中的 `setup_schedule()` 方法：

```python
# 每15分鐘執行一次
schedule.every(15).minutes.do(self.run_once)

# 每2小時執行一次
schedule.every(2).hours.do(self.run_once)

# 每天上午9點執行
schedule.every().day.at("09:00").do(self.run_once)
```

### 添加自定義處理邏輯

在 `process_symbol_auto()` 方法中添加額外的處理步驟：

```python
# 自定義處理邏輯
if result["success"]:
    # 發送通知
    self.send_notification(symbol)
    
    # 上傳到雲端存儲
    self.upload_to_cloud(symbol)
    
    # 更新數據庫狀態
    self.update_database_status(symbol)
```

## 📊 監控和維護

### 性能監控

Worker會自動追蹤：
- 處理時間
- 成功率
- 錯誤頻率
- 資源使用情況

### 定期維護

建議定期：
1. 清理舊日誌文件（保留最近30天）
2. 檢查磁盤空間使用情況
3. 監控MongoDB連接狀態
4. 驗證生成的報告質量

## 🆘 支援

如遇到問題：

1. 查看日誌文件獲取詳細錯誤信息
2. 使用 `--test-run` 模式進行故障排除
3. 檢查所有依賴是否正確安裝
4. 確認環境變量配置正確

## 📈 發展藍圖

未來可能的改進：
- [ ] 添加Web控制面板
- [ ] 支持多個數據源
- [ ] 添加報告質量評分
- [ ] 集成更多社交媒體平台
- [ ] 添加實時監控儀表板
- [ ] 支持自定義報告模板

---

*最後更新: 2025-01-27*
