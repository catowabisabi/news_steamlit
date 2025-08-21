# 📊 自動化Worker流程說明

## 🔄 完整的自動化流程

### 1. **背景監控階段**
```
每30分鐘自動執行：
┌─────────────────────────────────────────────┐
│ 1. 連接MongoDB                               │
│ 2. 獲取今天的所有symbols                      │
│ 3. 比較已處理的symbols列表                    │
│ 4. 識別新的symbols                          │
└─────────────────────────────────────────────┘
```

### 2. **新Symbol處理階段**
```
對每個新symbol執行：
┌─────────────────────────────────────────────┐
│ Step 1: 股票數據處理                          │
│   ├── 調用 process_single_stock()           │
│   ├── 獲取新聞數據                           │
│   ├── 獲取基本面數據                         │
│   ├── 生成中英文翻譯                         │
│   └── 生成分析報告                           │
│                                             │
│ Step 2: 報告生成                             │
│   ├── 生成Markdown報告                       │
│   ├── 生成中文PDF報告                        │
│   └── 生成英文PDF報告                        │
│                                             │
│ Step 3: IG Post生成                         │
│   ├── 使用中文報告內容作為基礎                │
│   ├── 調用IgPostCreator生成貼文              │
│   ├── 生成Instagram格式內容和hashtags        │
│   └── 保存為與Streamlit一致的格式            │
└─────────────────────────────────────────────┘
```

## 📁 文件結構詳解

### **與Streamlit應用完全一致**

```
project_root/
├── data/                           # 數據目錄
│   └── 2025-01-27/                # 日期目錄
│       ├── AAPL/                  # 股票代碼目錄
│       │   ├── news_2025-01-27.json              # 原始新聞數據
│       │   ├── fundamentals_2025-01-27.json      # 基本面數據
│       │   ├── desc_en_2025-01-27.json          # 英文公司描述
│       │   ├── desc_cn_2025-01-27.json          # 中文公司描述
│       │   ├── news_cn_2025-01-27.json          # 中文新聞翻譯
│       │   ├── news_en_2025-01-27.json          # 英文新聞翻譯
│       │   ├── analysis_2025-01-27.json         # 中文分析報告
│       │   ├── analysis_en_2025-01-27.json      # 英文分析報告
│       │   ├── AAPL_report_2025-01-27.md        # 主要Markdown報告
│       │   ├── AAPL_report_chinese_2025-01-27.pdf  # 中文PDF報告
│       │   ├── AAPL_report_english_2025-01-27.pdf  # 英文PDF報告
│       │   └── AAPL_ig_post_2025-01-27.txt      # Instagram貼文（格式化內容+hashtags+raw JSON）
│       ├── TSLA/                  # 另一個股票的目錄
│       │   └── ...                # 相同的文件結構
│       └── ...
└── logs/                          # 日誌目錄
    └── auto_worker_20250127.log   # 每日日誌文件
```

## 🔗 與Streamlit的整合

### **完美兼容**

1. **相同的FileManager**: 使用相同的`FileManager`類別
2. **相同的路徑邏輯**: `data/{YYYY-MM-DD}/{SYMBOL}/`
3. **相同的文件命名**: 與Streamlit應用完全一致
4. **相同的數據格式**: JSON和Markdown格式完全匹配

### **Streamlit檢測邏輯**

當你打開Streamlit應用時：

```python
# Streamlit應用會檢查這些文件是否存在
data_path = Path(app.file_manager._get_data_path(symbol, app.today_str))
md_file_path = data_path / f"{symbol}_report_{app.today_str}.md"
chinese_pdf_path = data_path / f"{symbol}_report_chinese_{app.today_str}.pdf"
english_pdf_path = data_path / f"{symbol}_report_english_{app.today_str}.pdf"

# 如果文件存在，直接顯示
if md_file_path.exists():
    # 顯示已存在的報告
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
```

## ⚙️ 核心組件說明

### **AutoWorker** (`run_streamlit_auto.py`)
- 主要的背景服務
- 處理排程和監控
- 協調各個組件

### **ReportGenerator** (`report_generator.py`)
- 負責報告生成
- 與Streamlit應用使用相同的邏輯
- 支持中英文PDF生成

### **IgPostCreator** (`ig_post.py`)
- Instagram貼文生成器
- 基於分析報告創建社交媒體內容

### **MongoHandler** (`mongo_db.py`)
- MongoDB操作
- 獲取最新的symbols數據

### **FileManager** (`file_manager.py`)
- 文件管理和路徑處理
- 確保與Streamlit完全一致

## 📊 數據流說明

```
MongoDB (symbols) 
    ↓
AutoWorker (檢測新symbols)
    ↓
process_single_stock() (生成基礎數據)
    ↓
ReportGenerator (生成報告)
    ↓
IgPostCreator (生成貼文)
    ↓
文件保存到 data/ 目錄
    ↓
Streamlit應用自動檢測並顯示
```

## 🎯 關鍵優勢

1. **零干預**: 完全自動化，無需手動操作
2. **完美整合**: 與現有Streamlit應用無縫銜接
3. **一致性**: 文件格式和路徑完全一致
4. **可見性**: Streamlit中立即可見自動生成的報告
5. **可靠性**: 強健的錯誤處理和重試機制

## 🔧 自定義配置

### **修改執行頻率**
在 `run_streamlit_auto.py` 中：
```python
# 每15分鐘執行一次
schedule.every(15).minutes.do(self.run_once)

# 每2小時執行一次
schedule.every(2).hours.do(self.run_once)
```

### **修改工作時間**
根據你的需求（原始註釋提到從5am到8pm EST）：
```python
# 只在工作時間運行
def should_run():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    est_time = datetime.now(ZoneInfo("America/New_York"))
    return 5 <= est_time.hour <= 20

if should_run():
    self.run_once()
```

## 🎉 使用效果

**啟動Worker後**：
1. ✅ Worker在背景默默運行
2. ✅ 每30分鐘自動檢查新symbols
3. ✅ 自動生成完整報告和貼文
4. ✅ 打開Streamlit即可看到最新報告
5. ✅ 無需任何手動操作

**完美的自動化體驗！** 🚀
