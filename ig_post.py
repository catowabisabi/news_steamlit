"""
Instagram Post Creator for Stock Analysis Reports
基於已生成的報告內容創建 Instagram 投資貼文
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional
from llms_chatgpt import ChatGPT


class IgPostCreator:
    """
    Instagram 貼文創建器
    基於現有的股票分析報告生成 Instagram 格式的投資貼文
    """
    
    def __init__(self):
        self.chatgpt = ChatGPT()
        self.disclaimer = """
⚠️ DISCLAIMER: This is NOT financial advice. All information is for educational purposes only. Always do your own research and consult with a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.
"""
    
    def create_ig_post(self, symbol: str, report_content: str) -> Dict[str, Any]:
        """
        基於報告內容創建 Instagram 貼文
        
        Args:
            symbol: 股票代碼
            report_content: 已生成的報告文字內容
            
        Returns:
            Dict: 包含格式化貼文和原始JSON的字典
        """
        try:
            # 構建給 ChatGPT 的提示
            prompt = self._build_prompt(symbol, report_content)
            
            # 調用 ChatGPT 生成 JSON
            response = self.chatgpt.chat(
                prompt,
                use_system_prompt=False,
                json_output=True,
                max_tokens=1000
            )
            
            # 解析 JSON 響應
            if isinstance(response, str):
                ig_data = json.loads(response)
            else:
                ig_data = response
            
            # 格式化成 Instagram 貼文
            formatted_post = self._format_ig_post(symbol, ig_data)
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "raw_json": ig_data,
                "formatted_post": formatted_post,
                "hashtags": self._generate_hashtags(symbol)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "symbol": symbol.upper()
            }
    
    def _build_prompt(self, symbol: str, report_content: str) -> str:
        """
        構建給 ChatGPT 的提示詞
        """
        today = datetime.now().strftime('%Y/%m/%d')
        
        prompt = f"""
基於以下的股票分析報告，為 {symbol.upper()} 創建一個 Instagram 投資貼文。

報告內容：
{report_content}

請嚴格按照以下 JSON 格式回應，並確保所有信息都來自提供的報告內容，不要添加任何不存在於報告中的信息：

{{
  "title": "{symbol.upper()} Quick Update ({today})",
  "bullish_highlights": [
    "基於報告的利好因素1",
    "基於報告的利好因素2",
    "基於報告的利好因素3"
  ],
  "key_risks": [
    "基於報告的風險因素1",
    "基於報告的風險因素2",
    "基於報告的風險因素3"
  ],
  "trading_view": {{
    "bias": "Bullish/Bearish/Neutral",
    "suggestion": "基於報告的交易建議"
  }},
  "catalysts": [
    "短期催化劑1",
    "短期催化劑2"
  ]
}}

重要要求：
1. 只使用報告中提到的具體數據和信息
2. 不要編造任何財務數字或事件
3. 如果報告中沒有某個部分的信息，請標註 "數據不足" 或省略該部分
4. 保持專業和客觀的語調
5. 確保輸出是有效的 JSON 格式
6. 請用英文回應
"""
        return prompt
    
    def _format_ig_post(self, symbol: str, ig_data: Dict[str, Any]) -> str:
        """
        將 JSON 數據格式化為 Instagram 貼文格式
        """
        post = f"📊 {ig_data.get('title', f'{symbol.upper()} Quick Update')}\n\n"
        
        # 利好因素
        if ig_data.get('bullish_highlights'):
            post += "✅ Bullish Highlights\n\n"
            for highlight in ig_data['bullish_highlights']:
                post += f"• {highlight}\n\n"
        
        # 風險因素
        if ig_data.get('key_risks'):
            post += "⚠️ Key Risks\n\n"
            for risk in ig_data['key_risks']:
                post += f"• {risk}\n\n"
        
        # 交易觀點
        if ig_data.get('trading_view'):
            trading_view = ig_data['trading_view']
            post += "💡 Trading View\n\n"
            if trading_view.get('bias'):
                post += f"Bias: {trading_view['bias']}\n\n"
            if trading_view.get('suggestion'):
                post += f"{trading_view['suggestion']}\n\n"
        
        # 催化劑
        if ig_data.get('catalysts'):
            post += "📌 Short-Term Catalysts\n\n"
            for catalyst in ig_data['catalysts']:
                post += f"• {catalyst}\n\n"
        
        # 添加免責聲明
        post += self.disclaimer
        
        # 添加 hashtags
        post += f"\n\n{self._generate_hashtags(symbol)}"
        
        return post
    
    def _generate_hashtags(self, symbol: str) -> str:
        """
        生成 hashtags
        """
        base_hashtags = [
            "#stockmarket", "#growthstocks", "#daytrading", "#swingtrading", 
            "#stockupdate", "#tradingtips", "#investors", "#financialnews", 
            "#stockanalysis", "#traders", "#shortselling"
        ]
        
        # 添加股票代碼的 hashtag
        symbol_hashtag = f"#{symbol.lower()}"
        base_hashtags.append(symbol_hashtag)
        
        return " ".join(base_hashtags)
    
    def save_post(self, post_data: Dict[str, Any], filename: str = None) -> str:
        """
        保存貼文到文件
        
        Args:
            post_data: 貼文數據
            filename: 文件名，默認為 symbol_ig_post_YYYY-MM-DD.txt
            
        Returns:
            str: 保存的文件路徑
        """
        if not filename:
            today = datetime.now().strftime('%Y-%m-%d')
            symbol = post_data.get('symbol', 'UNKNOWN')
            filename = f"{symbol}_ig_post_{today}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== INSTAGRAM POST ===\n\n")
                f.write(post_data['formatted_post'])
                f.write(f"\n\n=== HASHTAGS ===\n\n")
                f.write(post_data['hashtags'])
                f.write(f"\n\n=== RAW JSON ===\n\n")
                f.write(json.dumps(post_data['raw_json'], ensure_ascii=False, indent=2))
            
            return filename
            
        except Exception as e:
            raise Exception(f"保存文件失敗: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 示例使用
    creator = IgPostCreator()
    
    # 模擬報告內容
    sample_report = """
    PPSI 股票分析報告
    
    基本面分析：
    - Q2 營收同比增長 147% 至 840 萬美元
    - H1 營收同比增長 125% 至 1510 萬美元
    - 與美國主要 EV 充電提供商簽署 1000 萬美元多年期 e-Boost 合約
    - FY2025 營收指引維持在 2700-2900 萬美元
    - 現金 1800 萬美元，無銀行債務
    
    風險因素：
    - Q2 營運虧損 170 萬美元
    - 毛利率從 18.9% 下降至 15.7%
    - 現金儲備從 4160 萬美元降至 1800 萬美元
    """
    
    # 創建貼文
    result = creator.create_ig_post("PPSI", sample_report)
    
    if result["success"]:
        print("=== 生成的 Instagram 貼文 ===")
        print(result["formatted_post"])
        print("\n=== Hashtags ===")
        print(result["hashtags"])
        
        # 保存到文件
        filename = creator.save_post(result)
        print(f"\n貼文已保存到: {filename}")
    else:
        print(f"生成失敗: {result['error']}")
