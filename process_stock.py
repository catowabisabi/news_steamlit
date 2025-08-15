"""
單股票處理模組：為Streamlit應用提供單股票數據處理功能
"""
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from mongo_db import MongoHandler
from get_news import NewsScraper
from llms_chatgpt import ChatGPT
from llms_deepseek import DeepSeek
from config import NEWS_ANALYSIS_PROMPT, news_to_traditional_chinese_prompt, news_to_english_prompt, analysis_to_english_prompt, desc_to_chinese_prompt
from file_manager import FileManager
from get_company_desc import CompanyDescScraper
from run import safe_json_dumps, retry_llm_call

def process_single_stock(symbol: str, force_refresh: bool = False) -> dict:
    """
    處理單個股票的完整分析流程
    
    Args:
        symbol: 股票代碼
        force_refresh: 是否強制刷新所有數據
        
    Returns:
        dict: 包含處理結果和錯誤信息的字典
    """
    result = {
        "success": False,
        "symbol": symbol.upper(),
        "errors": [],
        "data_status": {}
    }
    
    try:
        # 初始化
        file_manager = FileManager()
        symbol = symbol.upper()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        print(f"🔄 開始處理 {symbol}...")
        
        # 檢查數據狀態
        data_types = ['news', 'fundamentals', 'desc_en', 'desc_cn', 'news_cn', 'analysis', 'news_en', 'analysis_en']
        for data_type in data_types:
            exists = file_manager.file_exists(symbol, data_type, today_str)
            result["data_status"][data_type] = exists
            if not exists or force_refresh:
                print(f"📝 需要生成 {data_type} 數據")
        
        # 初始化API連接
        try:
            db_handler = MongoHandler()
            if not db_handler.is_connected():
                result["errors"].append("MongoDB連線失敗")
                return result
            
            news_scraper = NewsScraper()
            chatgpt = ChatGPT()
            deepseek = DeepSeek()
        except Exception as e:
            result["errors"].append(f"API初始化失敗: {e}")
            return result
        
        # === 1. 獲取新聞數據 ===
        if not result["data_status"]["news"] or force_refresh:
            try:
                news = news_scraper.get_news(symbol)
                if "error" in news:
                    news = {"articles": []}
                
                if file_manager.validate_data(news, "news"):
                    file_manager.save_data(symbol, "news", news, today_str)
                    result["data_status"]["news"] = True
                    print(f"✅ {symbol} 新聞數據獲取成功")
            except Exception as e:
                result["errors"].append(f"新聞獲取失敗: {e}")
        
        # === 2. 獲取基本面數據 ===
        if not result["data_status"]["fundamentals"] or force_refresh:
            try:
                ny_today_str = datetime.now(ZoneInfo("America/New_York")).strftime('%Y-%m-%d')
                fundamentals = db_handler.find_doc("fundamentals_of_top_list_symbols", {"today_date": ny_today_str, "symbol": symbol})
                filtered_docs = [d for d in fundamentals if d.get("symbol", "").lower() == symbol.lower()]

                if filtered_docs:
                    doc = filtered_docs[0]
                    # 清理MongoDB特定字段
                    doc.pop("_id", None)
                    doc.pop("1d_chart_data", None)
                    doc.pop("1m_chart_data", None)
                    doc.pop("5m_chart_data", None)
                    doc.pop("updated_at", None)
                    
                    if file_manager.validate_data(doc, "fundamentals"):
                        file_manager.save_data(symbol, "fundamentals", doc, today_str)
                        result["data_status"]["fundamentals"] = True
                        print(f"✅ {symbol} 基本面數據獲取成功")
                else:
                    # 創建空的基本面數據
                    doc = {"symbol": symbol, "error": f"{symbol} 基本面資料不存在"}
                    file_manager.save_data(symbol, "fundamentals", doc, today_str)
                    result["data_status"]["fundamentals"] = True
            except Exception as e:
                result["errors"].append(f"基本面數據獲取失敗: {e}")
        
        # === 3. 獲取公司描述 ===
        print("🏢 檢查公司描述...")
        if force_refresh or not file_manager.file_exists(symbol, "desc_en", today_str):
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
                        result["data_status"]["desc_en"] = True
                        print(f"✅ {symbol} 公司描述獲取成功")
                    else:
                        print("❌ 公司描述格式不正確")
                        result["data_status"]["desc_en"] = False
                else:
                    print(f"⚠️ 無法獲取 {symbol} 的公司描述")
                    result["data_status"]["desc_en"] = False
            except Exception as e:
                print(f"❌ 公司描述獲取失敗: {e}")
                result["data_status"]["desc_en"] = False
        else:
            result["data_status"]["desc_en"] = True
            print(f"✅ {symbol} 公司描述從緩存加載成功")

        # === 4. 公司描述翻譯 ===
        print("🈶 檢查公司描述翻譯...")
        if force_refresh or not file_manager.file_exists(symbol, "desc_cn", today_str):
            print("🔄 緩存中無描述翻譯，開始翻譯...")
            try:
                chatgpt = ChatGPT()
                desc_en_data = file_manager.load_data(symbol, "desc_en", today_str)
                
                if desc_en_data:
                    desc_en_text = desc_en_data.get("desc_en", "") if isinstance(desc_en_data, dict) else str(desc_en_data)
                    
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
                        result["data_status"]["desc_cn"] = True
                        print(f"✅ {symbol} 公司描述翻譯成功!")
                    else:
                        print("❌ 公司描述翻譯格式不正確")
                        result["data_status"]["desc_cn"] = False
                else:
                    print("❌ 無公司描述可翻譯")
                    result["data_status"]["desc_cn"] = False
            except Exception as e:
                print(f"❌ ChatGPT 描述翻譯失敗: {e}")
                result["data_status"]["desc_cn"] = False
        else:
            result["data_status"]["desc_cn"] = True
            print(f"✅ {symbol} 公司描述翻譯從緩存加載成功")

        # === 5. 生成中文翻譯 ===
        if not result["data_status"]["news_cn"] or force_refresh:
            try:
                news = file_manager.load_data(symbol, "news", today_str)
                if news:
                    news_str = safe_json_dumps(news, ensure_ascii=False, indent=2)
                    
                    def chatgpt_cn_call():
                        return chatgpt.chat(
                            news_str, 
                            use_system_prompt=True, 
                            custom_system_prompt=news_to_traditional_chinese_prompt,
                            json_output=True,
                            max_tokens=2500
                        )
                    
                    news_cn_text = retry_llm_call(chatgpt_cn_call, max_retries=3, delay=2, expect_json=True)
                    
                    if file_manager.validate_data(news_cn_text, "news_cn"):
                        file_manager.save_data(symbol, "news_cn", news_cn_text, today_str)
                        result["data_status"]["news_cn"] = True
                        print(f"✅ {symbol} 中文翻譯完成")
            except Exception as e:
                result["errors"].append(f"中文翻譯失敗: {e}")
        
        # === 6. 生成基本面分析 ===
        if not result["data_status"]["analysis"] or force_refresh:
            try:
                news = file_manager.load_data(symbol, "news", today_str)
                doc = file_manager.load_data(symbol, "fundamentals", today_str)
                
                if news and doc:
                    user_prompt = safe_json_dumps({
                        "news": news,
                        "financial_data": doc
                    }, ensure_ascii=False, indent=2)
                    
                    def deepseek_call():
                        return deepseek.chat(
                            user_prompt, 
                            use_system_prompt=True, 
                            custom_system_prompt=NEWS_ANALYSIS_PROMPT,
                            json_output=True,
                            max_tokens=3000
                        )
                    
                    report_text = retry_llm_call(deepseek_call, max_retries=5, delay=3, expect_json=True)
                    
                    if file_manager.validate_data(report_text, "analysis"):
                        file_manager.save_data(symbol, "analysis", report_text, today_str)
                        result["data_status"]["analysis"] = True
                        print(f"✅ {symbol} 基本面分析完成")
            except Exception as e:
                result["errors"].append(f"基本面分析失敗: {e}")
        
        # === 7. 生成英文新聞翻譯 ===
        if not result["data_status"]["news_en"] or force_refresh:
            try:
                news_cn = file_manager.load_data(symbol, "news_cn", today_str)
                if news_cn:
                    if isinstance(news_cn, dict) and "data" in news_cn:
                        news_cn_content = news_cn["data"]
                    else:
                        news_cn_content = news_cn
                    news_cn_str = json.dumps(news_cn_content, ensure_ascii=False, indent=2)
                    
                    def chatgpt_en_call():
                        return chatgpt.chat(
                            news_cn_str, 
                            use_system_prompt=True, 
                            custom_system_prompt=news_to_english_prompt,
                            json_output=True,
                            max_tokens=2500
                        )
                    
                    news_en_text = retry_llm_call(chatgpt_en_call, max_retries=3, delay=2, expect_json=True)
                    
                    if file_manager.validate_data(news_en_text, "news_en"):
                        file_manager.save_data(symbol, "news_en", news_en_text, today_str)
                        result["data_status"]["news_en"] = True
                        print(f"✅ {symbol} 英文新聞翻譯完成")
            except Exception as e:
                result["errors"].append(f"英文新聞翻譯失敗: {e}")
        
        # === 8. 生成英文分析翻譯 ===
        if not result["data_status"]["analysis_en"] or force_refresh:
            try:
                report = file_manager.load_data(symbol, "analysis", today_str)
                if report:
                    if isinstance(report, dict) and "data" in report:
                        report_content = report["data"]
                    else:
                        report_content = report
                    report_str = json.dumps(report_content, ensure_ascii=False, indent=2)
                    
                    def chatgpt_analysis_en_call():
                        return chatgpt.chat(
                            report_str, 
                            use_system_prompt=True, 
                            custom_system_prompt=analysis_to_english_prompt,
                            json_output=True,
                            max_tokens=3000
                        )
                    
                    analysis_en_text = retry_llm_call(chatgpt_analysis_en_call, max_retries=3, delay=2, expect_json=True)
                    
                    if file_manager.validate_data(analysis_en_text, "analysis_en"):
                        file_manager.save_data(symbol, "analysis_en", analysis_en_text, today_str)
                        result["data_status"]["analysis_en"] = True
                        print(f"✅ {symbol} 英文分析翻譯完成")
            except Exception as e:
                result["errors"].append(f"英文分析翻譯失敗: {e}")
        
        # 檢查所有數據是否完整 - 公司描述為可選項
        required_data_types = ['news', 'fundamentals', 'news_cn', 'analysis', 'news_en', 'analysis_en'] 
        optional_data_types = ['desc_en', 'desc_cn']
        
        required_complete = all(result["data_status"].get(dt, False) for dt in required_data_types)
        result["success"] = required_complete
        
        if required_complete:
            print(f"🎉 {symbol} 所有必要數據處理完成!")
            # 檢查可選數據
            missing_optional = [dt for dt in optional_data_types if not result["data_status"].get(dt, False)]
            if missing_optional:
                print(f"ℹ️ {symbol} 缺少可選數據: {', '.join(missing_optional)} (不影響分析)")
        else:
            missing_required = [dt for dt in required_data_types if not result["data_status"].get(dt, False)]
            print(f"⚠️ {symbol} 缺少必要數據: {', '.join(missing_required)}")
        
        return result
        
    except Exception as e:
        result["errors"].append(f"處理過程中發生錯誤: {e}")
        return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python process_stock.py <SYMBOL>")
        sys.exit(1)
    
    symbol = sys.argv[1]
    result = process_single_stock(symbol)
    
    print(f"\n處理結果: {symbol}")
    print(f"成功: {result['success']}")
    if result['errors']:
        print("錯誤:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print("數據狀態:")
    for data_type, status in result['data_status'].items():
        print(f"  {data_type}: {'✅' if status else '❌'}")
