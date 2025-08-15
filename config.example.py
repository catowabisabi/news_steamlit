# 股票分析器配置文件示例
# 請複製此文件為 config.py 並填入您的實際配置

# ====== API 配置 ======
# OpenAI API 配置
# 在 https://platform.openai.com/account/api-keys 獲取
OPENAI_API_KEY = "sk-your-openai-api-key-here"

# DeepSeek API 配置  
# 在 https://platform.deepseek.com/api_keys 獲取
DEEPSEEK_API_KEY = "sk-your-deepseek-api-key-here"

# ====== 數據庫配置 ======
# MongoDB 連接字符串 (可選)
# 如果不使用MongoDB，設置為 None 或空字符串
MONGODB_URI = "mongodb://username:password@host:port/database"
# 本地MongoDB示例: "mongodb://localhost:27017/stock_analysis"
# MongoDB Atlas示例: "mongodb+srv://user:pass@cluster.mongodb.net/db"

# ====== 新聞API配置 ======
# 新聞API基礎URL
NEWS_API_BASE_URL = "http://news.enomars.org/api/news"

# ====== 系統配置 ======
# 數據存儲路徑
DATA_BASE_PATH = "./data"

# PDF 生成工具路徑 (Docker環境會自動配置)
WKHTMLTOPDF_PATH = "/usr/bin/wkhtmltopdf"

# ====== LLM 配置 ======
# ChatGPT 模型配置
CHATGPT_MODEL = "gpt-3.5-turbo"  # 或 "gpt-4" (需要相應權限)
CHATGPT_MAX_TOKENS = 4000
CHATGPT_TEMPERATURE = 0.7

# DeepSeek 模型配置
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_MAX_TOKENS = 4000
DEEPSEEK_TEMPERATURE = 0.5

# ====== 緩存配置 ======
# 是否啟用數據緩存
ENABLE_CACHE = True
# 緩存過期時間 (小時)
CACHE_EXPIRE_HOURS = 24

# ====== 日誌配置 ======
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ====== 網絡配置 ======
# 請求超時時間 (秒)
REQUEST_TIMEOUT = 30
# 重試次數
MAX_RETRIES = 3
# 重試間隔 (秒)
RETRY_DELAY = 1

# ====== 提示詞配置 ======
# 新聞分析提示詞
NEWS_ANALYSIS_PROMPT = """
你是一位專業的金融分析師。請分析以下新聞內容，提供結構化的分析報告。

要求：
1. 輸出必須是有效的JSON格式
2. 包含利好因素、風險因素、流動性分析和投資建議
3. 使用繁體中文
4. 保持客觀和專業

新聞內容：
{news_content}

基本面數據：
{fundamentals}

請按照以下JSON格式輸出：
{
    "company": "公司名稱",
    "ticker": "股票代碼", 
    "quarter": "季度",
    "positive_factors": [
        {"title": "利好因素標題", "detail": "詳細說明"}
    ],
    "risks": [
        {"title": "風險因素標題", "detail": "詳細說明"}
    ],
    "liquidity_risk": {
        "cash": "現金狀況分析",
        "burn_rate": "燒錢速度分析",
        "atm_risk": "高/中/低",
        "debt_status": "債務狀況分析"
    },
    "trading_recommendation": {
        "bias": "看多/看空/中性",
        "suggestion": "具體投資建議",
        "catalysts": ["催化劑1", "催化劑2"]
    }
}
"""

# 新聞翻譯為英文的提示詞
news_to_english_prompt = """
請將以下中文新聞內容翻譯成英文，保持原有的結構和格式。

要求：
1. 輸出必須是有效的JSON格式
2. 保持原有的字段結構
3. 翻譯要準確和專業
4. 保持金融術語的準確性

中文新聞內容：
{chinese_news}

請按照以下JSON格式輸出：
{
    "summary": "新聞摘要 (英文)",
    "key_points": ["要點1 (英文)", "要點2 (英文)"],
    "news_en": "完整新聞內容 (英文)"
}
"""

# 分析報告翻譯為英文的提示詞
analysis_to_english_prompt = """
請將以下中文分析報告翻譯成英文，保持原有的結構和格式。

要求：
1. 輸出必須是有效的JSON格式
2. 保持原有的字段結構
3. 翻譯要準確和專業
4. 保持金融術語的準確性
5. 投資建議翻譯：看多=Bullish, 看空=Bearish, 中性=Neutral

中文分析報告：
{chinese_analysis}

請按照以下JSON格式輸出，保持完整的結構：
{
    "company": "Company Name (English)",
    "ticker": "Stock Ticker",
    "quarter": "Quarter",
    "positive_factors": [
        {"title": "Positive Factor Title (English)", "detail": "Detailed Description (English)"}
    ],
    "risks": [
        {"title": "Risk Factor Title (English)", "detail": "Detailed Description (English)"}
    ],
    "liquidity_risk": {
        "cash": "Cash Status Analysis (English)",
        "burn_rate": "Burn Rate Analysis (English)", 
        "atm_risk": "High/Medium/Low",
        "debt_status": "Debt Status Analysis (English)"
    },
    "trading_recommendation": {
        "bias": "Bullish/Bearish/Neutral",
        "suggestion": "Specific Investment Recommendation (English)",
        "catalysts": ["Catalyst 1 (English)", "Catalyst 2 (English)"]
    }
}
"""

# 公司描述翻譯為中文的提示詞
desc_to_chinese_prompt = """
請將以下英文公司描述翻譯成繁體中文，並提供結構化的信息。

要求：
1. 輸出必須是有效的JSON格式
2. 翻譯要準確和專業
3. 保持商業術語的準確性
4. 提供公司的核心業務總結

英文公司描述：
{english_description}

請按照以下JSON格式輸出：
{
    "desc_cn": "完整的公司描述 (繁體中文)",
    "summary": "公司核心業務總結 (繁體中文，2-3句話)",
    "business_type": "業務類型 (如：科技公司、製造業、金融服務等)",
    "key_products": ["主要產品1", "主要產品2", "主要產品3"]
}
"""
