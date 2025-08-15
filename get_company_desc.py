"""
Yahoo Finance 公司描述獲取器
"""
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Optional
import re


class CompanyDescScraper:
    """
    從Yahoo Finance獲取公司描述信息
    """
    
    def __init__(self):
        self.session = requests.Session()
        # 設置User-Agent來模擬真實瀏覽器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_company_description(self, symbol: str, region: str = "ca") -> Optional[str]:
        """
        獲取公司描述
        
        Args:
            symbol: 股票代碼
            region: 地區代碼 (ca, us, etc.)
            
        Returns:
            str: 公司描述，如果獲取失敗則返回None
        """
        try:
            # 構建URL
            url = f"https://{region}.finance.yahoo.com/quote/{symbol.upper()}/profile/"
            
            print(f"🔍 正在獲取 {symbol} 的公司描述...")
            print(f"URL: {url}")
            
            # 添加隨機延遲避免被封IP
            time.sleep(random.uniform(1, 3))
            
            # 發送請求
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 方法1: 尋找 data-testid="description" 的元素
            desc_element = soup.find(attrs={"data-testid": "description"})
            
            if desc_element:
                # 查找其中的 <p> 標籤
                p_tag = desc_element.find('p')
                if p_tag:
                    description = p_tag.get_text(strip=True)
                    if description:
                        print(f"✅ 成功獲取描述 (方法1)")
                        return self._clean_description(description)
            
            # 方法2: 備用方案 - 尋找包含公司描述的其他可能元素
            alternative_selectors = [
                'span[data-testid="description"]',
                'div[data-testid="description"] p',
                '.quote-sub-section p',
                '.asset-profile-container p',
                '.Mt\\(15px\\) p'
            ]
            
            for selector in alternative_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and len(text) > 50:  # 確保是實質性的描述
                            print(f"✅ 成功獲取描述 (備用方案: {selector})")
                            return self._clean_description(text)
                except Exception:
                    continue
            
            # 方法3: 搜索包含關鍵詞的段落
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text(strip=True)
                # 檢查是否像公司描述（包含關鍵詞且長度合適）
                if (len(text) > 100 and 
                    any(keyword in text.lower() for keyword in 
                        ['company', 'corporation', 'business', 'operates', 'provides', 'engages', 'develops'])):
                    print(f"✅ 成功獲取描述 (關鍵詞匹配)")
                    return self._clean_description(text)
            
            print(f"❌ 未找到 {symbol} 的公司描述")
            return None
            
        except requests.RequestException as e:
            print(f"❌ 網絡請求失敗: {e}")
            return None
        except Exception as e:
            print(f"❌ 解析失敗: {e}")
            return None
    
    def _clean_description(self, description: str) -> str:
        """
        清理描述文本
        
        Args:
            description: 原始描述
            
        Returns:
            str: 清理後的描述
        """
        # 移除多餘的空白字符
        description = re.sub(r'\s+', ' ', description)
        
        # 移除可能的HTML殘留
        description = re.sub(r'<[^>]+>', '', description)
        
        # 去除首尾空白
        description = description.strip()
        
        return description
    
    def get_multiple_descriptions(self, symbols: list, region: str = "ca") -> dict:
        """
        批量獲取多個公司的描述
        
        Args:
            symbols: 股票代碼列表
            region: 地區代碼
            
        Returns:
            dict: {symbol: description} 的字典
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            print(f"\n📋 處理 {i+1}/{len(symbols)}: {symbol}")
            
            description = self.get_company_description(symbol, region)
            results[symbol.upper()] = description
            
            # 添加延遲避免被限制
            if i < len(symbols) - 1:
                delay = random.uniform(2, 5)
                print(f"⏳ 等待 {delay:.1f} 秒...")
                time.sleep(delay)
        
        return results
    
    def close(self):
        """關閉session"""
        self.session.close()


# 測試用例
if __name__ == "__main__":
    scraper = CompanyDescScraper()
    
    try:
        print("🚀 Yahoo Finance 公司描述獲取器測試")
        print("=" * 50)
        
        # 測試單個股票
        test_symbol = "XPON"
        print(f"\n🧪 測試 1: 獲取 {test_symbol} 的描述")
        description = scraper.get_company_description(test_symbol)
        
        if description:
            print(f"\n📝 {test_symbol} 公司描述:")
            print("-" * 30)
            print(description)
            print(f"\n📊 描述長度: {len(description)} 字符")
        else:
            print(f"❌ 無法獲取 {test_symbol} 的描述")
        
        # 測試多個股票
        test_symbols = ["AAPL", "TSLA", "MSFT"]
        print(f"\n🧪 測試 2: 批量獲取描述")
        print(f"測試股票: {', '.join(test_symbols)}")
        
        descriptions = scraper.get_multiple_descriptions(test_symbols)
        
        print(f"\n📋 批量獲取結果:")
        print("-" * 50)
        for symbol, desc in descriptions.items():
            if desc:
                print(f"\n✅ {symbol}:")
                print(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
            else:
                print(f"\n❌ {symbol}: 獲取失敗")
        
        # 統計結果
        success_count = sum(1 for desc in descriptions.values() if desc)
        print(f"\n📊 成功率: {success_count}/{len(test_symbols)} ({success_count/len(test_symbols)*100:.1f}%)")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷操作")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
    finally:
        scraper.close()
        print("\n🏁 測試完成")