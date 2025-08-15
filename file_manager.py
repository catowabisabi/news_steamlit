"""
文件管理器：處理數據的保存、讀取和文件夾結構管理
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path


class FileManager:
    """
    管理數據文件的保存、讀取和文件夾結構
    文件夾結構: data/YYYY-MM-DD/SYMBOL/
    """
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = Path(base_data_dir)
        
    def _get_date_str(self) -> str:
        """獲取今日日期字符串 (YYYY-MM-DD)"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_data_path(self, symbol: str, date_str: str = None) -> Path:
        """
        獲取數據文件夾路徑
        
        Args:
            symbol: 股票代碼
            date_str: 日期字符串，默認為今日
            
        Returns:
            Path: 數據文件夾路徑
        """
        if date_str is None:
            date_str = self._get_date_str()
        
        return self.base_data_dir / date_str / symbol.upper()
    
    def _ensure_directory_exists(self, path: Path) -> None:
        """確保目錄存在，如果不存在則創建"""
        path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, symbol: str, data_type: str, date_str: str = None) -> Path:
        """
        獲取特定數據類型的文件路徑
        
        Args:
            symbol: 股票代碼
            data_type: 數據類型 (news, fundamentals, news_cn, analysis)
            date_str: 日期字符串，默認為今日
            
        Returns:
            Path: 文件路徑
        """
        if date_str is None:
            date_str = self._get_date_str()
            
        data_path = self._get_data_path(symbol, date_str)
        filename = f"{data_type}_{date_str}.json"
        return data_path / filename
    
    def file_exists(self, symbol: str, data_type: str, date_str: str = None) -> bool:
        """
        檢查特定數據文件是否存在
        
        Args:
            symbol: 股票代碼
            data_type: 數據類型 (news, fundamentals, news_cn, analysis)
            date_str: 日期字符串，默認為今日
            
        Returns:
            bool: 文件是否存在
        """
        file_path = self._get_file_path(symbol, data_type, date_str)
        return file_path.exists()
    
    def save_data(self, symbol: str, data_type: str, data: Any, date_str: str = None) -> bool:
        """
        保存數據到文件
        
        Args:
            symbol: 股票代碼
            data_type: 數據類型 (news, fundamentals, news_cn, analysis)
            data: 要保存的數據
            date_str: 日期字符串，默認為今日
            
        Returns:
            bool: 是否保存成功
        """
        try:
            file_path = self._get_file_path(symbol, data_type, date_str)
            self._ensure_directory_exists(file_path.parent)
            
            # 處理特殊數據類型
            processed_data = self._process_data_for_saving(data, data_type)
            
            # 將數據保存為JSON格式
            with open(file_path, 'w', encoding='utf-8') as f:
                if isinstance(processed_data, str):
                    # 如果是字符串，包裝成對象
                    json_data = {
                        "data": processed_data,
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol.upper(),
                        "type": data_type
                    }
                else:
                    # 如果是對象，直接保存
                    json_data = processed_data
                    if isinstance(json_data, dict):
                        json_data["timestamp"] = datetime.now().isoformat()
                        json_data["symbol"] = symbol.upper()
                        json_data["type"] = data_type
                
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ {data_type} 數據已保存: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 保存 {data_type} 數據失敗: {e}")
            return False
    
    def _process_data_for_saving(self, data: Any, data_type: str) -> Any:
        """
        處理保存前的數據格式轉換
        
        Args:
            data: 原始數據
            data_type: 數據類型
            
        Returns:
            Any: 處理後的數據
        """
        if data_type in ["news_cn", "analysis", "news_en", "analysis_en", "desc_cn"]:
            if isinstance(data, str):
                # 嘗試解析JSON字符串為dict
                try:
                    parsed_data = json.loads(data)
                    return {
                        "data": parsed_data,
                        "raw_text": data  # 保留原始文本備用
                    }
                except json.JSONDecodeError:
                    # 如果不是有效JSON，嘗試清理和修復
                    cleaned_data = self._clean_and_fix_json(data)
                    if cleaned_data:
                        return {
                            "data": cleaned_data,
                            "raw_text": data
                        }
                    else:
                        # 作為純文本保存
                        return {
                            "data": {"text": data},
                            "raw_text": data,
                            "format": "text"
                        }
            else:
                return data
        elif data_type == "desc_en":
            # desc_en不需要特殊處理，保持原格式
            return data
        else:
            return data
    
    def _clean_and_fix_json(self, text: str) -> Optional[dict]:
        """
        清理和修復可能不完整的JSON字符串
        
        Args:
            text: 可能不完整的JSON文本
            
        Returns:
            dict: 修復後的JSON對象，如果無法修復則返回None
        """
        try:
            # 移除可能的前後綴
            text = text.strip()
            
            # 如果文本被截斷，嘗試找到最後一個完整的結構
            if not text.endswith('}') and not text.endswith(']'):
                # 找到最後一個完整的對象或數組
                last_brace = text.rfind('}')
                last_bracket = text.rfind(']')
                
                if last_brace > last_bracket:
                    # 嘗試以大括號結尾
                    text = text[:last_brace + 1]
                elif last_bracket > last_brace:
                    # 嘗試以方括號結尾
                    text = text[:last_bracket + 1]
                else:
                    # 如果找不到，嘗試添加結尾
                    if text.count('{') > text.count('}'):
                        text += '}'
                    elif text.count('[') > text.count(']'):
                        text += ']'
            
            # 嘗試解析修復後的JSON
            return json.loads(text)
            
        except Exception as e:
            print(f"⚠️ JSON修復失敗: {e}")
            return None
    
    def load_data(self, symbol: str, data_type: str, date_str: str = None) -> Optional[Any]:
        """
        從文件加載數據
        
        Args:
            symbol: 股票代碼
            data_type: 數據類型 (news, fundamentals, news_cn, analysis)
            date_str: 日期字符串，默認為今日
            
        Returns:
            Any: 加載的數據，如果失敗返回None
        """
        try:
            file_path = self._get_file_path(symbol, data_type, date_str)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ {data_type} 數據已從緩存加載: {file_path}")
            return data
            
        except Exception as e:
            print(f"❌ 加載 {data_type} 數據失敗: {e}")
            return None
    
    def validate_data(self, data: Any, data_type: str) -> bool:
        """
        驗證數據格式是否正確
        
        Args:
            data: 要驗證的數據
            data_type: 數據類型
            
        Returns:
            bool: 數據是否有效
        """
        try:
            if data is None:
                return False
            
            if data_type == "news":
                # 新聞數據應該有articles字段
                return isinstance(data, dict) and ("articles" in data or "data" in data)
            
            elif data_type == "fundamentals":
                # 基本面數據應該有symbol字段
                return isinstance(data, dict) and ("symbol" in data or "data" in data)
            
            elif data_type in ["news_cn", "analysis", "news_en", "analysis_en", "desc_en", "desc_cn"]:
                # 翻譯和分析數據驗證
                if isinstance(data, str):
                    return len(data.strip()) > 0
                elif isinstance(data, dict):
                    if "data" in data:
                        data_content = data["data"]
                        # data可以是dict或非空字符串
                        if isinstance(data_content, dict):
                            return len(data_content) > 0  # dict不為空
                        elif isinstance(data_content, str):
                            return len(data_content.strip()) > 0  # 字符串不為空
                        else:
                            return False
                    # 對於desc_en，檢查是否有desc_en字段
                    elif data_type == "desc_en" and "desc_en" in data:
                        return isinstance(data["desc_en"], str) and len(data["desc_en"].strip()) > 0
                    # 對於desc_cn，檢查是否有desc_cn字段
                    elif data_type == "desc_cn" and "desc_cn" in data:
                        return isinstance(data["desc_cn"], str) and len(data["desc_cn"].strip()) > 0
                    return False
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 驗證 {data_type} 數據格式失敗: {e}")
            return False
    
    def get_or_create_data_directory(self, symbol: str, date_str: str = None) -> str:
        """
        獲取或創建數據目錄
        
        Args:
            symbol: 股票代碼
            date_str: 日期字符串，默認為今日
            
        Returns:
            str: 數據目錄路徑
        """
        data_path = self._get_data_path(symbol, date_str)
        self._ensure_directory_exists(data_path)
        return str(data_path)
    
    def list_available_dates(self, symbol: str = None) -> list:
        """
        列出可用的日期
        
        Args:
            symbol: 股票代碼，如果提供則只返回該股票有數據的日期
            
        Returns:
            list: 可用的日期列表
        """
        dates = []
        if self.base_data_dir.exists():
            for date_dir in self.base_data_dir.iterdir():
                if date_dir.is_dir():
                    if symbol:
                        symbol_dir = date_dir / symbol.upper()
                        if symbol_dir.exists():
                            dates.append(date_dir.name)
                    else:
                        dates.append(date_dir.name)
        return sorted(dates)


# 使用示例
if __name__ == "__main__":
    fm = FileManager()
    
    # 測試文件夾創建
    symbol = "XPON"
    print(f"數據目錄: {fm.get_or_create_data_directory(symbol)}")
    
    # 測試數據保存和加載
    test_data = {"test": "data", "symbol": symbol}
    fm.save_data(symbol, "test", test_data)
    
    loaded_data = fm.load_data(symbol, "test")
    print(f"加載的數據: {loaded_data}")
    
    # 測試文件存在檢查
    print(f"文件是否存在: {fm.file_exists(symbol, 'test')}")
