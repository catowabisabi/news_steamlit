# 🤖 自動化Worker - 快速使用指南

## 🎯 功能概述

您現在有了一個完整的自動化背景Worker系統，它會：

✅ **每半小時自動檢查MongoDB中的新symbols**  
✅ **自動生成完整的股票分析報告（中英文）**  
✅ **自動創建Instagram投資貼文**  
✅ **提供詳細的日誌和錯誤處理**  
✅ **與Streamlit應用完全一致的文件結構和格式**

## 🚀 立即開始

### 1. 測試系統
```bash
# 測試Worker是否正常工作
python test_auto_worker.py
```

### 2. 執行一次性測試
```bash
# 執行一次完整流程然後退出
python start_auto_worker.py --test-run
```

### 3. 啟動持續運行
```bash
# 開始自動化服務（每30分鐘運行一次）
python start_auto_worker.py
```

## 📋 生成的文件

對於每個新的symbol，系統會自動生成：

```
data/2025-01-27/AAPL/
├── AAPL_report_2025-01-27.md           # 主要Markdown報告（中文）
├── AAPL_report_chinese_2025-01-27.pdf  # 中文PDF報告
├── AAPL_report_english_2025-01-27.pdf  # 英文PDF報告
└── AAPL_ig_post_2025-01-27.txt        # Instagram貼文
```

**與Streamlit應用完全一致**：
- 文件路徑結構：`data/{YYYY-MM-DD}/{SYMBOL}/`
- 文件命名格式與Streamlit應用相同
- 報告內容和格式完全匹配
- **智能重複檢測**：使用與Streamlit相同的文件檢查邏輯
- **當你打開Streamlit時，會自動看到已生成的報告**

## 📊 監控和日誌

- **日誌文件**: `logs/auto_worker_YYYYMMDD.log`
- **運行統計**: 每小時自動打印到日誌
- **實時狀態**: 控制台輸出顯示處理進度

## ⚙️ 主要配置

### 執行頻率（可修改）
```python
# 在 run_streamlit_auto.py 中
schedule.every(30).minutes.do(self.run_once)  # 每30分鐘
```

### 日誌級別
```bash
python start_auto_worker.py --log-level DEBUG  # 詳細日誌
python start_auto_worker.py --log-level INFO   # 標準日誌（默認）
```

## 🔧 故障排除

### 常見問題

1. **MongoDB連接失敗**
   - 檢查 `.env` 文件中的 `MONGODB_CONNECTION_STRING`

2. **沒有找到新symbols**
   - 確認MongoDB中有當天的數據
   - 檢查 `fundamentals_of_top_list_symbols` 集合

3. **報告生成失敗**
   - 確認AI API密鑰有效（OpenAI, DeepSeek）
   - 檢查網絡連接

### 查看日誌
```bash
# 實時查看日誌
tail -f logs/auto_worker_$(date +%Y%m%d).log

# 搜索錯誤
grep "ERROR" logs/auto_worker_*.log
```

## 🎉 您現在可以：

1. ✅ **完全自動化** - 無需手動干預，系統會自動處理新symbols
2. ✅ **定時執行** - 每30分鐘檢查一次新數據
3. ✅ **生成報告** - 自動生成中英文分析報告
4. ✅ **創建貼文** - 自動生成Instagram投資貼文
5. ✅ **監控運行** - 詳細日誌追蹤所有活動

## 📞 需要幫助？

- 查看 `AUTO_WORKER_README.md` 獲取詳細文檔
- 運行 `python test_auto_worker.py` 診斷問題
- 檢查 `logs/` 目錄中的日誌文件

---
🎯 **目標達成！您的自動化股票分析系統已準備就緒！** 🎯
