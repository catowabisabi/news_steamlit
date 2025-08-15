from mongo_db import MongoHandler
from get_news import NewsScraper
from datetime import datetime
from zoneinfo import ZoneInfo
from llms_chatgpt import ChatGPT
from llms_deepseek import DeepSeek
from config import NEWS_ANALYSIS_PROMPT, news_to_traditional_chinese_prompt, news_to_english_prompt, analysis_to_english_prompt, desc_to_chinese_prompt
from file_manager import FileManager
from get_company_desc import CompanyDescScraper
import json
import sys
import time

try:
    from bson import ObjectId
except ImportError:
    # If bson is not available, create a dummy ObjectId class
    class ObjectId:
        pass


def safe_json_dumps(obj, **kwargs):
    """
    Safely convert objects to JSON, handling MongoDB ObjectId and datetime objects
    """
    def default_serializer(o):
        if hasattr(o, '__class__') and 'ObjectId' in str(type(o)):
            return str(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")
    
    return json.dumps(obj, default=default_serializer, **kwargs)


def retry_llm_call(llm_func, max_retries=3, delay=2, expect_json=False):
    """
    重試LLM調用，處理中斷和失敗情況
    
    Args:
        llm_func: LLM調用函數
        max_retries: 最大重試次數
        delay: 重試間隔（秒）
        expect_json: 是否期望JSON格式響應
        
    Returns:
        LLM響應結果
    """
    for attempt in range(max_retries):
        try:
            result = llm_func()
            
            # 檢查結果是否完整
            if result and len(result.strip()) > 10:
                # 如果期望JSON格式，驗證JSON有效性
                if expect_json:
                    try:
                        json.loads(result.strip())
                        print(f"✅ JSON格式驗證通過")
                        return result
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON格式無效 (嘗試 {attempt + 1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            time.sleep(delay)
                            continue
                        else:
                            # 最後一次嘗試，返回原始結果讓file_manager處理
                            print("⚠️ 返回原始結果，讓文件管理器嘗試修復JSON")
                            return result
                else:
                    return result
            else:
                print(f"⚠️ LLM響應過短 (嘗試 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                    
        except Exception as e:
            print(f"⚠️ LLM調用失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            else:
                raise e
    
    # 如果所有重試都失敗
    raise Exception("LLM調用在所有重試後仍然失敗")



def main():
    # 初始化文件管理器
    file_manager = FileManager()
    
    # 設置股票代碼
    symbol = "xpon"
    symbol = symbol.upper()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📁 數據將保存到: {file_manager.get_or_create_data_directory(symbol, today_str)}")
    
    # 初始化數據庫連接
    db_handler = MongoHandler()
    if db_handler.is_connected():
        print("✅ MongoDB 連線成功")
    else:
        print("❌ MongoDB 連線失敗")
        sys.exit(1)

    news_scraper = NewsScraper()

    # === 獲取新聞數據 ===
    print("📰 檢查新聞數據...")
    news = file_manager.load_data(symbol, "news", today_str)
    
    if news is None or not file_manager.validate_data(news, "news"):
        print("🔄 緩存中無新聞數據，開始獲取新聞...")
        news = news_scraper.get_news(symbol)
        
        # Check if news fetching failed
        if "error" in news:
            print(f"⚠️ News fetching failed: {news['error']}")
            print("Continuing with analysis using empty news data...")
            news = {"articles": []}  # Use empty articles for analysis
        
        # 保存新聞數據
        if file_manager.validate_data(news, "news"):
            file_manager.save_data(symbol, "news", news, today_str)
        else:
            print("❌ 新聞數據格式不正確，程序退出")
            sys.exit(1)
    else:
        # 如果是從緩存加載的數據，提取實際內容
        if isinstance(news, dict) and "data" in news:
            news = news["data"]
    
    # 統計新聞數量
    news_count = len(news.get("articles", [])) if isinstance(news, dict) else 0
    print(f"✅ {symbol} 新聞提取成功: 一共有 {news_count} 則新聞")

    # === 獲取基本面數據 ===
    print("💰 檢查基本面數據...")
    doc = file_manager.load_data(symbol, "fundamentals", today_str)
    
    if doc is None or not file_manager.validate_data(doc, "fundamentals"):
        print("🔄 緩存中無基本面數據，開始從數據庫獲取...")
        ny_today_str = datetime.now(ZoneInfo("America/New_York")).strftime('%Y-%m-%d')
        fundamentals = db_handler.find_doc("fundamentals_of_top_list_symbols", {"today_date": ny_today_str, "symbol": symbol})
        # 假設 docs 是你查詢到的文件列表
        filtered_docs = [d for d in fundamentals if d.get("symbol", "").lower() == symbol.lower()]

        if filtered_docs:
            doc = filtered_docs[0]  # 取第一個符合的
            # Remove MongoDB-specific fields and large data
            doc.pop("_id", None)  # Remove ObjectId which is not JSON serializable
            doc.pop("1d_chart_data", None)
            doc.pop("1m_chart_data", None)
            doc.pop("5m_chart_data", None)
            doc.pop("updated_at", None)  # Remove datetime which may cause issues
            
            # 保存基本面數據
            if file_manager.validate_data(doc, "fundamentals"):
                file_manager.save_data(symbol, "fundamentals", doc, today_str)
                print(f"✅ {symbol} 基本面資料提取成功")
            else:
                print("❌ 基本面數據格式不正確，程序退出")
                sys.exit(1)
        else:
            print(f"No document found for symbol '{symbol}'")
            # Create minimal doc for analysis to prevent errors
            doc = {
                "symbol": symbol,
                "error": f"{symbol} 基本面資料不存在"
            }
            file_manager.save_data(symbol, "fundamentals", doc, today_str)
    else:
        # 如果是從緩存加載的數據，提取實際內容
        if isinstance(doc, dict) and "data" in doc:
            doc = doc["data"]
        print(f"✅ {symbol} 基本面資料從緩存加載成功")

    # === 獲取公司描述 ===
    print("🏢 檢查公司描述...")
    desc_en = file_manager.load_data(symbol, "desc_en", today_str)
    
    if desc_en is None or not file_manager.validate_data(desc_en, "desc_en"):
        print("🔄 緩存中無公司描述，開始獲取...")
        try:
            desc_scraper = CompanyDescScraper()
            company_description = desc_scraper.get_company_description(symbol, region="ca")
            desc_scraper.close()
            
            if company_description:
                desc_data = {
                    "desc_en": company_description,
                    "symbol": symbol,
                    "source": "Yahoo Finance"
                }
                
                if file_manager.validate_data(desc_data, "desc_en"):
                    file_manager.save_data(symbol, "desc_en", desc_data, today_str)
                    desc_en = desc_data
                    print(f"✅ {symbol} 公司描述獲取成功")
                else:
                    print("❌ 公司描述格式不正確")
                    desc_en = None
            else:
                print(f"⚠️ 無法獲取 {symbol} 的公司描述")
                desc_en = None
        except Exception as e:
            print(f"❌ 公司描述獲取失敗: {e}")
            desc_en = None
    else:
        print(f"✅ {symbol} 公司描述從緩存加載成功")

    # === ChatGPT 公司描述翻譯 ===
    desc_cn = None
    if desc_en:
        print("🈶 檢查公司描述翻譯...")
        desc_cn = file_manager.load_data(symbol, "desc_cn", today_str)
        
        if desc_cn is None or not file_manager.validate_data(desc_cn, "desc_cn"):
            print("🔄 緩存中無描述翻譯，開始翻譯...")
            try:
                chatgpt = ChatGPT()
                desc_en_text = desc_en.get("desc_en", "") if isinstance(desc_en, dict) else str(desc_en)
                
                def chatgpt_desc_call():
                    return chatgpt.chat(
                        desc_en_text, 
                        use_system_prompt=True, 
                        custom_system_prompt=desc_to_chinese_prompt,
                        json_output=True,
                        max_tokens=2000
                    )
                
                desc_cn_text = retry_llm_call(chatgpt_desc_call, max_retries=3, delay=2, expect_json=True)
                
                if file_manager.validate_data(desc_cn_text, "desc_cn"):
                    file_manager.save_data(symbol, "desc_cn", desc_cn_text, today_str)
                    desc_cn = file_manager.load_data(symbol, "desc_cn", today_str)
                    print(f"✅ {symbol} 公司描述翻譯成功!")
                else:
                    print("❌ 公司描述翻譯格式不正確")
            except Exception as e:
                print(f"❌ ChatGPT 描述翻譯失敗: {e}")
        else:
            print(f"✅ {symbol} 公司描述翻譯從緩存加載成功")

    # === ChatGPT 新聞翻譯 ===
    print("🈶 檢查新聞翻譯...")
    news_cn = file_manager.load_data(symbol, "news_cn", today_str)
    
    if news_cn is None or not file_manager.validate_data(news_cn, "news_cn"):
        print("🔄 緩存中無翻譯數據，開始翻譯新聞...")
        try:
            chatgpt = ChatGPT()
            news_str = safe_json_dumps(news, ensure_ascii=False, indent=2)
            
            # 使用重試機制調用ChatGPT，啟用JSON模式
            def chatgpt_call():
                return chatgpt.chat(
                    news_str, 
                    use_system_prompt=True, 
                    custom_system_prompt=news_to_traditional_chinese_prompt,
                    json_output=True,  # 啟用JSON Output（如果支持）
                    max_tokens=2500
                )
            
            news_cn_text = retry_llm_call(chatgpt_call, max_retries=3, delay=2, expect_json=True)
            
            # 保存翻譯結果
            if file_manager.validate_data(news_cn_text, "news_cn"):
                file_manager.save_data(symbol, "news_cn", news_cn_text, today_str)
                # 重新加載以獲取處理後的格式
                news_cn = file_manager.load_data(symbol, "news_cn", today_str)
                print(f"✅ {symbol} 新聞翻譯成功!")
            else:
                print("❌ 新聞翻譯格式不正確，程序退出")
                sys.exit(1)
        except Exception as e:
            print(f"❌ ChatGPT 翻譯失敗: {e}")
            sys.exit(1)
    else:
        print(f"✅ {symbol} 新聞翻譯從緩存加載成功")

    # === DeepSeek 基本面分析 ===
    print("🤖 檢查基本面分析...")
    report = file_manager.load_data(symbol, "analysis", today_str)
    
    if report is None or not file_manager.validate_data(report, "analysis"):
        print("🔄 緩存中無分析數據，開始分析...")
        try:
            deepseek = DeepSeek()
            user_prompt = safe_json_dumps({
                "news": news,
                "financial_data": doc
            }, ensure_ascii=False, indent=2)
            
            # 使用重試機制調用DeepSeek，啟用JSON Output功能
            def deepseek_call():
                return deepseek.chat(
                    user_prompt, 
                    use_system_prompt=True, 
                    custom_system_prompt=NEWS_ANALYSIS_PROMPT,
                    json_output=True,  # 啟用JSON Output
                    max_tokens=3000    # 增加token數量避免截斷
                )
            
            report_text = retry_llm_call(deepseek_call, max_retries=5, delay=3, expect_json=True)  # DeepSeek更多重試，期望JSON
            
            # 保存分析結果
            if file_manager.validate_data(report_text, "analysis"):
                file_manager.save_data(symbol, "analysis", report_text, today_str)
                # 重新加載以獲取處理後的格式
                report = file_manager.load_data(symbol, "analysis", today_str)
                print(f"✅ {symbol} 基本面分析成功!")
            else:
                print("❌ 基本面分析格式不正確，程序退出")
                sys.exit(1)
        except Exception as e:
            print(f"❌ DeepSeek 分析失敗: {e}")
            sys.exit(1)
    else:
        print(f"✅ {symbol} 基本面分析從緩存加載成功")

    # === ChatGPT 新聞英文翻譯 ===
    print("🇺🇸 檢查新聞英文翻譯...")
    news_en = file_manager.load_data(symbol, "news_en", today_str)
    
    if news_en is None or not file_manager.validate_data(news_en, "news_en"):
        print("🔄 緩存中無英文翻譯數據，開始翻譯新聞...")
        try:
            chatgpt = ChatGPT()
            # 使用中文新聞作為輸入
            if isinstance(news_cn, dict) and "data" in news_cn:
                news_cn_content = news_cn["data"]
            else:
                news_cn_content = news_cn
            news_cn_str = json.dumps(news_cn_content, ensure_ascii=False, indent=2)
            
            # 使用重試機制調用ChatGPT進行英文翻譯
            def chatgpt_en_call():
                return chatgpt.chat(
                    news_cn_str, 
                    use_system_prompt=True, 
                    custom_system_prompt=news_to_english_prompt,
                    json_output=True,
                    max_tokens=2500
                )
            
            news_en_text = retry_llm_call(chatgpt_en_call, max_retries=3, delay=2, expect_json=True)
            
            # 保存英文翻譯結果
            if file_manager.validate_data(news_en_text, "news_en"):
                file_manager.save_data(symbol, "news_en", news_en_text, today_str)
                news_en = file_manager.load_data(symbol, "news_en", today_str)
                print(f"✅ {symbol} 新聞英文翻譯成功!")
            else:
                print("❌ 新聞英文翻譯格式不正確，程序退出")
                sys.exit(1)
        except Exception as e:
            print(f"❌ ChatGPT 英文翻譯失敗: {e}")
            sys.exit(1)
    else:
        print(f"✅ {symbol} 新聞英文翻譯從緩存加載成功")

    # === ChatGPT 分析英文翻譯 ===
    print("🇺🇸 檢查分析英文翻譯...")
    analysis_en = file_manager.load_data(symbol, "analysis_en", today_str)
    
    if analysis_en is None or not file_manager.validate_data(analysis_en, "analysis_en"):
        print("🔄 緩存中無分析英文翻譯數據，開始翻譯分析...")
        try:
            chatgpt = ChatGPT()
            # 使用中文分析作為輸入
            if isinstance(report, dict) and "data" in report:
                report_content = report["data"]
            else:
                report_content = report
            report_str = json.dumps(report_content, ensure_ascii=False, indent=2)
            
            # 使用重試機制調用ChatGPT進行英文翻譯
            def chatgpt_analysis_en_call():
                return chatgpt.chat(
                    report_str, 
                    use_system_prompt=True, 
                    custom_system_prompt=analysis_to_english_prompt,
                    json_output=True,
                    max_tokens=3000
                )
            
            analysis_en_text = retry_llm_call(chatgpt_analysis_en_call, max_retries=3, delay=2, expect_json=True)
            
            # 保存英文翻譯結果
            if file_manager.validate_data(analysis_en_text, "analysis_en"):
                file_manager.save_data(symbol, "analysis_en", analysis_en_text, today_str)
                analysis_en = file_manager.load_data(symbol, "analysis_en", today_str)
                print(f"✅ {symbol} 分析英文翻譯成功!")
            else:
                print("❌ 分析英文翻譯格式不正確，程序退出")
                sys.exit(1)
        except Exception as e:
            print(f"❌ ChatGPT 分析英文翻譯失敗: {e}")
            sys.exit(1)
    else:
        print(f"✅ {symbol} 分析英文翻譯從緩存加載成功")

    # === 顯示結果 ===
    def display_data(data, title):
        """顯示數據內容，處理不同格式"""
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        
        if isinstance(data, dict):
            if "data" in data:
                content = data["data"]
                if isinstance(content, dict):
                    print(json.dumps(content, ensure_ascii=False, indent=2))
                else:
                    print(content)
            else:
                print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(data)
    
    # 顯示分析結果
    display_data(report, f"📊 {symbol} 基本面分析結果 (中文):")
    display_data(analysis_en, f"📊 {symbol} 基本面分析結果 (English):")
    
    # 顯示翻譯結果
    display_data(news_cn, f"📰 新聞翻譯 (繁體中文):")
    display_data(news_en, f"📰 新聞翻譯 (English):")


if __name__ == "__main__":
    main()

