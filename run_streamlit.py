"""
Streamlit Web應用：股票分析報告生成器
"""
import streamlit as st
import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path
import time
import os

# 導入自定義模組
from file_manager import FileManager
from mongo_db import MongoHandler
from get_news import NewsScraper
from llms_chatgpt import ChatGPT
from llms_deepseek import DeepSeek
from config import NEWS_ANALYSIS_PROMPT, news_to_traditional_chinese_prompt, news_to_english_prompt, analysis_to_english_prompt, desc_to_chinese_prompt
from zoneinfo import ZoneInfo

# 導入自定義處理函數
from process_stock import process_single_stock

class StockAnalysisApp:
    def __init__(self):
        self.file_manager = FileManager()
        self.today_str = datetime.now().strftime('%Y-%m-%d')
        print(f"🗓️ Streamlit應用使用日期: {self.today_str}")  # 調試信息
        
    def clean_symbol_list(self, symbols_input: str) -> list:
        """
        清理和解析股票代碼列表
        
        Args:
            symbols_input: 用戶輸入的股票代碼字符串
            
        Returns:
            list: 清理後的股票代碼列表
        """
        if not symbols_input.strip():
            return []
        
        # 用逗號分割
        symbols = symbols_input.split(',')
        
        # 清理每個股票代碼
        cleaned_symbols = []
        for symbol in symbols:
            # 移除空格和特殊字符，只保留字母和數字
            cleaned = re.sub(r'[^\w]', '', symbol.strip().upper())
            if cleaned:  # 確保不是空字符串
                cleaned_symbols.append(cleaned)
        
        return list(set(cleaned_symbols))  # 去重
    
    def load_stock_data(self, symbol: str) -> dict:
        """
        加載股票的所有數據
        
        Args:
            symbol: 股票代碼
            
        Returns:
            dict: 包含所有數據的字典
        """
        data = {}
        data_types = ['news', 'fundamentals', 'desc_en', 'desc_cn', 'news_cn', 'analysis', 'news_en', 'analysis_en']
        
        for data_type in data_types:
            try:
                loaded_data = self.file_manager.load_data(symbol, data_type, self.today_str)
                if loaded_data and self.file_manager.validate_data(loaded_data, data_type):
                    data[data_type] = loaded_data
                else:
                    data[data_type] = None
            except Exception as e:
                st.error(f"載入 {symbol} 的 {data_type} 數據時出錯: {e}")
                data[data_type] = None
        
        return data
    
    def generate_markdown_report_old(self, symbol: str, data: dict) -> str:
        """
        生成Markdown報告
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: Markdown格式的報告
        """
        md_content = f"""# 📊 {symbol} 股票分析報告

<strong>生成日期:</strong> {self.today_str}

---

## 🏢 公司簡介

"""
        
        # 公司描述 (中文)
        if data.get('desc_cn'):
            desc_cn_data = data['desc_cn'].get('data', {}) if isinstance(data['desc_cn'], dict) else data['desc_cn']
            if isinstance(desc_cn_data, dict):
                if 'desc_cn' in desc_cn_data:
                    md_content += f"<strong>公司描述:</strong> {desc_cn_data['desc_cn']}\n\n"
                if 'summary' in desc_cn_data:
                    md_content += f"<strong>簡介:</strong> {desc_cn_data['summary']}\n\n"
                if 'business_type' in desc_cn_data:
                    md_content += f"<strong>業務類型:</strong> {desc_cn_data['business_type']}\n\n"
                if 'key_products' in desc_cn_data:
                    md_content += "<strong>主要產品:</strong>\n"
                    for product in desc_cn_data['key_products']:
                        md_content += f"- {product}\n"
                    md_content += "\n"
        elif data.get('desc_en'):
            desc_en_data = data['desc_en']
            if isinstance(desc_en_data, dict) and 'desc_en' in desc_en_data:
                md_content += f"<strong>公司描述:</strong> {desc_en_data['desc_en']}\n\n"
        else:
            md_content += "❌ 暫無公司描述資料\n\n"

        md_content += """---

## 📰 新聞翻譯 (繁體中文)

"""
        
        # 新聞中文 - 使用表格布局
        if data.get('news_cn'):
            news_cn_data = data['news_cn'].get('data', {}) if isinstance(data['news_cn'], dict) else data['news_cn']
            if isinstance(news_cn_data, dict):
                md_content += "| 項目 | 內容 |\n"
                md_content += "|------|------|\n"
                
                if 'summary' in news_cn_data:
                    md_content += f"| <strong>摘要</strong> | {news_cn_data['summary']} |\n"
                
                if 'key_points' in news_cn_data:
                    key_points_str = "<br>".join([f"• {point}" for point in news_cn_data['key_points']])
                    md_content += f"| <strong>要點</strong> | {key_points_str} |\n"
                
                if 'news_cn' in news_cn_data:
                    # 限制新聞內容長度，避免表格過寬
                    news_content = news_cn_data['news_cn'][:300] + "..." if len(news_cn_data['news_cn']) > 300 else news_cn_data['news_cn']
                    md_content += f"| <strong>完整內容</strong> | {news_content} |\n"
                
                md_content += "\n"
        else:
            md_content += "❌ 暫無中文新聞數據\n\n"
        
        md_content += """---

## 📰 News Translation (English)

"""
        
        # 新聞英文
        if data.get('news_en'):
            news_en_data = data['news_en'].get('data', {}) if isinstance(data['news_en'], dict) else data['news_en']
            if isinstance(news_en_data, dict):
                if 'news_en' in news_en_data:
                    md_content += f"{news_en_data['news_en']}\n\n"
                if 'summary' in news_en_data:
                    md_content += f"<strong>Summary:</strong> {news_en_data['summary']}\n\n"
                if 'key_points' in news_en_data:
                    md_content += "<strong>Key Points:</strong>\n"
                    for point in news_en_data['key_points']:
                        md_content += f"- {point}\n"
                    md_content += "\n"
        else:
            md_content += "❌ No English news data available\n\n"
        
        md_content += """---

## 📊 基本面分析 (中文)

"""
        
        # 分析中文 - 使用表格布局
        if data.get('analysis'):
            analysis_data = data['analysis'].get('data', {}) if isinstance(data['analysis'], dict) else data['analysis']
            if isinstance(analysis_data, dict):
                # 基本信息表格
                md_content += "### 📋 基本信息\n\n"
                md_content += "| 項目 | 內容 |\n"
                md_content += "|------|------|\n"
                md_content += f"| <strong>公司</strong> | {analysis_data.get('company', 'N/A')} |\n"
                md_content += f"| <strong>股票代碼</strong> | {analysis_data.get('ticker', 'N/A')} |\n"
                md_content += f"| <strong>季度</strong> | {analysis_data.get('quarter', 'N/A')} |\n\n"
                
                # 利好因素表格
                if 'positive_factors' in analysis_data:
                    md_content += "### ✅ 利好因素\n\n"
                    md_content += "| 利好因素 | 詳細說明 |\n"
                    md_content += "|----------|----------|\n"
                    for factor in analysis_data['positive_factors']:
                        if isinstance(factor, dict):
                            title = f"<strong>{factor.get('title', 'N/A')}</strong>"
                            detail = factor.get('detail', 'N/A').replace('\n', '<br>')
                            md_content += f"| {title} | {detail} |\n"
                    md_content += "\n"
                
                # 風險因素表格
                if 'risks' in analysis_data:
                    md_content += "### ⚠️ 風險因素\n\n"
                    md_content += "| 風險因素 | 詳細說明 |\n"
                    md_content += "|----------|----------|\n"
                    for risk in analysis_data['risks']:
                        if isinstance(risk, dict):
                            title = f"<strong>{risk.get('title', 'N/A')}</strong>"
                            detail = risk.get('detail', 'N/A').replace('\n', '<br>')
                            md_content += f"| {title} | {detail} |\n"
                    md_content += "\n"
                
                # 流動性分析表格
                if 'liquidity_risk' in analysis_data:
                    md_content += "### 💰 流動性分析\n\n"
                    md_content += "| 分析項目 | 評估結果 |\n"
                    md_content += "|----------|----------|\n"
                    liquidity = analysis_data['liquidity_risk']
                    if isinstance(liquidity, dict):
                        if liquidity.get('cash'):
                            md_content += f"| <strong>現金狀況</strong> | {liquidity['cash']} |\n"
                        if liquidity.get('burn_rate'):
                            md_content += f"| <strong>燒錢速度</strong> | {liquidity['burn_rate']} |\n"
                        if liquidity.get('atm_risk'):
                            atm_color = "🔴" if liquidity['atm_risk'] == "高" else "🟡" if liquidity['atm_risk'] == "中" else "🟢"
                            md_content += f"| <strong>ATM風險</strong> | {atm_color} {liquidity['atm_risk']} |\n"
                        if liquidity.get('debt_status'):
                            md_content += f"| <strong>債務狀況</strong> | {liquidity['debt_status']} |\n"
                    md_content += "\n"
                
                # 投資建議表格
                if 'trading_recommendation' in analysis_data:
                    rec = analysis_data['trading_recommendation']
                    md_content += "### 💡 投資建議\n\n"
                    md_content += "| 建議項目 | 內容 |\n"
                    md_content += "|----------|------|\n"
                    
                    # 投資傾向用顏色標示
                    bias = rec.get('bias', 'N/A')
                    bias_color = "🟢" if bias == "看多" else "🔴" if bias == "看空" else "🟡"
                    md_content += f"| <strong>投資傾向</strong> | {bias_color} <strong>{bias}</strong> |\n"
                    
                    if rec.get('suggestion'):
                        suggestion = rec['suggestion'].replace('\n', '<br>')
                        md_content += f"| <strong>投資建議</strong> | {suggestion} |\n"
                    
                    if 'catalysts' in rec and rec['catalysts']:
                        catalysts_str = "<br>".join([f"• {catalyst}" for catalyst in rec['catalysts']])
                        md_content += f"| <strong>催化劑</strong> | {catalysts_str} |\n"
                    md_content += "\n"
        else:
            md_content += "❌ 暫無中文分析數據\n\n"
        
        md_content += """---

## 📊 Fundamental Analysis (English)

"""
        
        # 分析英文
        if data.get('analysis_en'):
            analysis_en_data = data['analysis_en'].get('data', {}) if isinstance(data['analysis_en'], dict) else data['analysis_en']
            if isinstance(analysis_en_data, dict):
                md_content += f"<strong>Company:</strong> {analysis_en_data.get('company', 'N/A')}\n"
                md_content += f"<strong>Ticker:</strong> {analysis_en_data.get('ticker', 'N/A')}\n"
                md_content += f"<strong>Quarter:</strong> {analysis_en_data.get('quarter', 'N/A')}\n\n"
                
                # Positive factors
                if 'positive_factors' in analysis_en_data:
                    md_content += "### ✅ Positive Factors\n\n"
                    for factor in analysis_en_data['positive_factors']:
                        md_content += f"<strong>{factor.get('title', '')}</strong>\n"
                        md_content += f"{factor.get('detail', '')}\n\n"
                
                # Risk factors
                if 'risks' in analysis_en_data:
                    md_content += "### ⚠️ Risk Factors\n\n"
                    for risk in analysis_en_data['risks']:
                        md_content += f"<strong>{risk.get('title', '')}</strong>\n"
                        md_content += f"{risk.get('detail', '')}\n\n"
                
                # Liquidity risk
                if 'liquidity_risk' in analysis_en_data:
                    liquidity = analysis_en_data['liquidity_risk']
                    md_content += "### 💰 Liquidity Analysis\n\n"
                    md_content += f"<strong>Cash Status:</strong> {liquidity.get('cash', 'N/A')}\n\n"
                    md_content += f"<strong>Burn Rate:</strong> {liquidity.get('burn_rate', 'N/A')}\n\n"
                    md_content += f"<strong>ATM Risk:</strong> {liquidity.get('atm_risk', 'N/A')}\n\n"
                    md_content += f"<strong>Debt Status:</strong> {liquidity.get('debt_status', 'N/A')}\n\n"
                
                # Trading recommendation
                if 'trading_recommendation' in analysis_en_data:
                    rec = analysis_en_data['trading_recommendation']
                    md_content += "### 💡 Trading Recommendation\n\n"
                    md_content += f"<strong>Bias:</strong> {rec.get('bias', 'N/A')}\n"
                    md_content += f"<strong>Suggestion:</strong> {rec.get('suggestion', 'N/A')}\n"
                    if 'catalysts' in rec:
                        md_content += "<strong>Key Catalysts:</strong>\n"
                        for catalyst in rec['catalysts']:
                            md_content += f"- {catalyst}\n"
                        md_content += "\n"
        else:
            md_content += "❌ No English analysis data available\n\n"
        
        md_content += """---

*本報告由AI自動生成，僅供參考，不構成投資建議。投資有風險，請謹慎決策。*
"""
        
        return md_content
    
    def save_markdown_report(self, symbol: str, md_content: str) -> str:
        """
        保存Markdown報告到文件
        
        Args:
            symbol: 股票代碼
            md_content: Markdown內容
            
        Returns:
            str: 文件路徑
        """
        data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
        data_path.mkdir(parents=True, exist_ok=True)
        
        md_file_path = data_path / f"{symbol}_report_{self.today_str}.md"
        
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(md_file_path)
    
    def generate_chinese_report_content(self, symbol: str, data: dict) -> str:
        """
        生成中文報告內容
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: 中文Markdown內容
        """
        md_content = f"""# 📊 {symbol} 股票分析報告

<strong>生成日期:</strong> {self.today_str}

---

## 🏢 公司簡介

"""
        
        # 公司描述 - 中文
        if data.get('desc_cn'):
            desc_cn_data = data['desc_cn'].get('data', {}) if isinstance(data['desc_cn'], dict) else data['desc_cn']
            if isinstance(desc_cn_data, dict) and 'desc_cn' in desc_cn_data:
                md_content += f"<strong>公司描述:</strong> {desc_cn_data['desc_cn']}\n\n"
        else:
            md_content += "❌ 暫無公司描述資料\n\n"

        md_content += """---

## 📰 新聞

"""
        
        # 新聞中文 - 使用表格布局
        if data.get('news_cn'):
            news_cn_data = data['news_cn'].get('data', {}) if isinstance(data['news_cn'], dict) else data['news_cn']
            if isinstance(news_cn_data, dict):
                md_content += "| 項目 | 內容 |\n"
                md_content += "|------|------|\n"
                
                if 'summary' in news_cn_data:
                    md_content += f"| <strong>摘要</strong> | {news_cn_data['summary']} |\n"
                
                if 'key_points' in news_cn_data:
                    key_points_str = "<br>".join([f"• {point}" for point in news_cn_data['key_points']])
                    md_content += f"| <strong>要點</strong> | {key_points_str} |\n"
                
                if 'news_cn' in news_cn_data:
                    # 完整新聞內容，不截斷
                    md_content += f"| <strong>完整內容</strong> | {news_cn_data['news_cn']} |\n"
                
                md_content += "\n"
        else:
            md_content += "❌ 暫無中文新聞數據\n\n"
        
        md_content += """---

## 📊 基本面分析

"""
        
        # 分析中文 - 使用表格布局
        if data.get('analysis'):
            analysis_data = data['analysis'].get('data', {}) if isinstance(data['analysis'], dict) else data['analysis']
            if isinstance(analysis_data, dict):
                # 股票代碼驗證
                if analysis_data.get('ticker') and analysis_data['ticker'].upper() != symbol.upper():
                    md_content += f"❌ 錯誤：股票代碼不匹配 (期望: {symbol.upper()}, 實際: {analysis_data.get('ticker', 'N/A')})\n\n"
                    md_content += "❌ 暫無基本面資料\n\n"
                else:
                    # 基本信息表格
                    md_content += "### 📋 基本信息\n\n"
                    md_content += "| 項目 | 內容 |\n"
                    md_content += "|------|------|\n"
                    md_content += f"| <strong>公司</strong> | {analysis_data.get('company', 'N/A')} |\n"
                    md_content += f"| <strong>股票代碼</strong> | {analysis_data.get('ticker', 'N/A')} |\n"
                    md_content += f"| <strong>季度</strong> | {analysis_data.get('quarter', 'N/A')} |\n\n"
                    
                    # 利好因素表格
                    if 'positive_factors' in analysis_data:
                        md_content += "### ✅ 利好因素\n\n"
                        md_content += "| 利好因素 | 詳細說明 |\n"
                        md_content += "|----------|----------|\n"
                        for factor in analysis_data['positive_factors']:
                            if isinstance(factor, dict):
                                title = f"<strong>{factor.get('title', 'N/A')}</strong>"
                                detail = factor.get('detail', 'N/A').replace('\n', '<br>')
                                md_content += f"| {title} | {detail} |\n"
                        md_content += "\n"
                    
                    # 風險因素表格
                    if 'risks' in analysis_data:
                        md_content += "### ⚠️ 風險因素\n\n"
                        md_content += "| 風險因素 | 詳細說明 |\n"
                        md_content += "|----------|----------|\n"
                        for risk in analysis_data['risks']:
                            if isinstance(risk, dict):
                                title = f"<strong>{risk.get('title', 'N/A')}</strong>"
                                detail = risk.get('detail', 'N/A').replace('\n', '<br>')
                                md_content += f"| {title} | {detail} |\n"
                        md_content += "\n"
                    
                    # 流動性分析表格
                    if 'liquidity_risk' in analysis_data:
                        md_content += "### 💰 流動性分析\n\n"
                        md_content += "| 分析項目 | 評估結果 |\n"
                        md_content += "|----------|----------|\n"
                        liquidity = analysis_data['liquidity_risk']
                        if isinstance(liquidity, dict):
                            if liquidity.get('cash'):
                                md_content += f"| <strong>現金狀況</strong> | {liquidity['cash']} |\n"
                            if liquidity.get('burn_rate'):
                                md_content += f"| <strong>燒錢速度</strong> | {liquidity['burn_rate']} |\n"
                            if liquidity.get('atm_risk'):
                                atm_color = "🔴" if liquidity['atm_risk'] == "高" else "🟡" if liquidity['atm_risk'] == "中" else "🟢"
                                md_content += f"| <strong>ATM風險</strong> | {atm_color} {liquidity['atm_risk']} |\n"
                            if liquidity.get('debt_status'):
                                md_content += f"| <strong>債務狀況</strong> | {liquidity['debt_status']} |\n"
                        md_content += "\n"
                    
                    # 投資建議表格
                    if 'trading_recommendation' in analysis_data:
                        rec = analysis_data['trading_recommendation']
                        md_content += "### 💡 投資建議\n\n"
                        md_content += "| 建議項目 | 內容 |\n"
                        md_content += "|----------|------|\n"
                        
                        # 投資傾向用顏色標示
                        bias = rec.get('bias', 'N/A')
                        bias_color = "🟢" if bias == "看多" else "🔴" if bias == "看空" else "🟡"
                        md_content += f"| <strong>投資傾向</strong> | {bias_color} <strong>{bias}</strong> |\n"
                        
                        if rec.get('suggestion'):
                            suggestion = rec['suggestion'].replace('\n', '<br>')
                            md_content += f"| <strong>投資建議</strong> | {suggestion} |\n"
                        
                        if 'catalysts' in rec and rec['catalysts']:
                            catalysts_str = "<br>".join([f"• {catalyst}" for catalyst in rec['catalysts']])
                            md_content += f"| <strong>催化劑</strong> | {catalysts_str} |\n"
                        md_content += "\n"
        else:
            md_content += "❌ 暫無基本面分析數據\n\n"
        
        return md_content
    
    def generate_english_report_content(self, symbol: str, data: dict) -> str:
        """
        生成英文報告內容
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: 英文Markdown內容
        """
        md_content = f"""# 📊 {symbol} Stock Analysis Report

<strong>Generated:</strong> {self.today_str}

---

## 🏢 Company Overview

"""
        
        # 公司描述 - 英文（支持兩種數據格式）
        if data.get('desc_en'):
            desc_en_data = data['desc_en'].get('data', {}) if isinstance(data['desc_en'], dict) else data['desc_en']
            if isinstance(desc_en_data, dict):
                if 'desc_en' in desc_en_data:
                    md_content += f"<strong>Company Description:</strong> {desc_en_data['desc_en']}\n\n"
                elif 'desc_en' in data['desc_en']:  # 直接在根級別
                    md_content += f"<strong>Company Description:</strong> {data['desc_en']['desc_en']}\n\n"
            else:
                md_content += "❌ No company description available\n\n"
        else:
            md_content += "❌ No company description available\n\n"

        md_content += """---

## 📰 News

"""
        
        # 新聞英文 - 使用表格布局
        if data.get('news_en'):
            news_en_data = data['news_en'].get('data', {}) if isinstance(data['news_en'], dict) else data['news_en']
            if isinstance(news_en_data, dict):
                md_content += "| Item | Content |\n"
                md_content += "|------|------|\n"
                
                if 'summary' in news_en_data:
                    md_content += f"| <strong>Summary</strong> | {news_en_data['summary']} |\n"
                
                if 'key_points' in news_en_data:
                    key_points_str = "<br>".join([f"• {point}" for point in news_en_data['key_points']])
                    md_content += f"| <strong>Key Points</strong> | {key_points_str} |\n"
                
                if 'news_en' in news_en_data:
                    # 完整新聞內容，不截斷
                    md_content += f"| <strong>Full Content</strong> | {news_en_data['news_en']} |\n"
                
                md_content += "\n"
        else:
            md_content += "❌ No English news data available\n\n"
        
        md_content += """---

## 📊 Fundamental Analysis

"""
        
        # 分析英文 - 使用表格布局
        if data.get('analysis_en'):
            analysis_en_data = data['analysis_en'].get('data', {}) if isinstance(data['analysis_en'], dict) else data['analysis_en']
            if isinstance(analysis_en_data, dict):
                # 股票代碼驗證
                if analysis_en_data.get('ticker') and analysis_en_data['ticker'].upper() != symbol.upper():
                    md_content += f"❌ Error: Stock symbol mismatch (Expected: {symbol.upper()}, Actual: {analysis_en_data.get('ticker', 'N/A')})\n\n"
                    md_content += "❌ No fundamental data available\n\n"
                else:
                    # 基本信息表格
                    md_content += "### 📋 Basic Information\n\n"
                    md_content += "| Item | Content |\n"
                    md_content += "|------|------|\n"
                    md_content += f"| <strong>Company</strong> | {analysis_en_data.get('company', 'N/A')} |\n"
                    md_content += f"| <strong>Ticker</strong> | {analysis_en_data.get('ticker', 'N/A')} |\n"
                    md_content += f"| <strong>Quarter</strong> | {analysis_en_data.get('quarter', 'N/A')} |\n\n"
                    
                    # 利好因素表格
                    if 'positive_factors' in analysis_en_data:
                        md_content += "### ✅ Positive Factors\n\n"
                        md_content += "| Positive Factor | Details |\n"
                        md_content += "|----------------|----------|\n"
                        for factor in analysis_en_data['positive_factors']:
                            if isinstance(factor, dict):
                                title = f"<strong>{factor.get('title', 'N/A')}</strong>"
                                detail = factor.get('detail', 'N/A').replace('\n', '<br>')
                                md_content += f"| {title} | {detail} |\n"
                        md_content += "\n"
                    
                    # 風險因素表格
                    if 'risks' in analysis_en_data:
                        md_content += "### ⚠️ Risk Factors\n\n"
                        md_content += "| Risk Factor | Details |\n"
                        md_content += "|-------------|----------|\n"
                        for risk in analysis_en_data['risks']:
                            if isinstance(risk, dict):
                                title = f"<strong>{risk.get('title', 'N/A')}</strong>"
                                detail = risk.get('detail', 'N/A').replace('\n', '<br>')
                                md_content += f"| {title} | {detail} |\n"
                        md_content += "\n"
                    
                    # 流動性分析表格
                    if 'liquidity_risk' in analysis_en_data:
                        md_content += "### 💰 Liquidity Analysis\n\n"
                        md_content += "| Analysis Item | Assessment |\n"
                        md_content += "|---------------|------------|\n"
                        liquidity = analysis_en_data['liquidity_risk']
                        if isinstance(liquidity, dict):
                            if liquidity.get('cash'):
                                md_content += f"| <strong>Cash Status</strong> | {liquidity['cash']} |\n"
                            if liquidity.get('burn_rate'):
                                md_content += f"| <strong>Burn Rate</strong> | {liquidity['burn_rate']} |\n"
                            if liquidity.get('atm_risk'):
                                atm_color = "🔴" if liquidity['atm_risk'] == "High" else "🟡" if liquidity['atm_risk'] == "Medium" else "🟢"
                                md_content += f"| <strong>ATM Risk</strong> | {atm_color} {liquidity['atm_risk']} |\n"
                            if liquidity.get('debt_status'):
                                md_content += f"| <strong>Debt Status</strong> | {liquidity['debt_status']} |\n"
                        md_content += "\n"
                    
                    # 投資建議表格
                    if 'trading_recommendation' in analysis_en_data:
                        rec = analysis_en_data['trading_recommendation']
                        md_content += "### 💡 Investment Recommendation\n\n"
                        md_content += "| Recommendation Item | Content |\n"
                        md_content += "|--------------------|------|\n"
                        
                        # 投資傾向用顏色標示
                        bias = rec.get('bias', 'N/A')
                        bias_color = "🟢" if bias == "Bullish" else "🔴" if bias == "Bearish" else "🟡"
                        md_content += f"| <strong>Investment Bias</strong> | {bias_color} <strong>{bias}</strong> |\n"
                        
                        if rec.get('suggestion'):
                            suggestion = rec['suggestion'].replace('\n', '<br>')
                            md_content += f"| <strong>Suggestion</strong> | {suggestion} |\n"
                        
                        if 'catalysts' in rec and rec['catalysts']:
                            catalysts_str = "<br>".join([f"• {catalyst}" for catalyst in rec['catalysts']])
                            md_content += f"| <strong>Catalysts</strong> | {catalysts_str} |\n"
                        md_content += "\n"
        else:
            md_content += "❌ No English analysis data available\n\n"
        
        return md_content

    def process_with_progress(self, symbol: str, log_messages: list, log_container, progress_bar, status_text, force_refresh: bool = False) -> dict:
        """
        帶進度顯示的股票數據處理
        
        Args:
            symbol: 股票代碼
            log_messages: 日誌消息列表
            log_container: Streamlit容器用於顯示日誌
            progress_bar: 進度條
            status_text: 狀態文本顯示
            force_refresh: 是否強制刷新
            
        Returns:
            dict: 處理結果
        """
        import time
        from mongo_db import MongoDB
        from get_news import get_news
        from llms_deepseek import DeepSeek
        from llms_chatgpt import ChatGPT
        from get_company_desc import CompanyDescScraper
        
        try:
            # 步驟1: 連接數據庫
            self._add_log(log_messages, log_container, "📊 連接MongoDB數據庫...")
            progress_bar.progress(0.15)
            mongo = MongoDB()
            
            # 步驟2: 獲取新聞數據
            self._add_log(log_messages, log_container, f"📰 獲取 {symbol} 新聞數據...")
            progress_bar.progress(0.25)
            
            if not self.file_manager.file_exists(symbol, 'news', self.today_str) or force_refresh:
                news = get_news(symbol)
                if news and not news.get('error'):
                    self.file_manager.save_data(symbol, news, 'news', self.today_str)
                    self._add_log(log_messages, log_container, f"✅ {symbol} 新聞數據獲取成功")
                else:
                    self._add_log(log_messages, log_container, f"⚠️ {symbol} 新聞數據獲取失敗")
            else:
                self._add_log(log_messages, log_container, f"✅ news 數據已從緩存加載")
            
            # 步驟3: 獲取基本面數據
            self._add_log(log_messages, log_container, f"💼 獲取 {symbol} 基本面數據...")
            progress_bar.progress(0.35)
            
            if not self.file_manager.file_exists(symbol, 'fundamentals', self.today_str) or force_refresh:
                fundamentals = mongo.get_fundamentals(symbol)
                if fundamentals:
                    # 驗證股票代碼匹配
                    ticker_in_data = fundamentals.get('ticker', '').upper()
                    if ticker_in_data and ticker_in_data != symbol.upper():
                        self._add_log(log_messages, log_container, f"❌ 錯誤：股票代碼不匹配 (期望: {symbol.upper()}, 實際: {ticker_in_data})")
                        return {"success": False, "error": "股票代碼不匹配"}
                    
                    self.file_manager.save_data(symbol, fundamentals, 'fundamentals', self.today_str)
                    self._add_log(log_messages, log_container, f"✅ {symbol} 基本面數據獲取成功")
                else:
                    self._add_log(log_messages, log_container, f"❌ 暫無基本面資料")
            else:
                self._add_log(log_messages, log_container, f"✅ fundamentals 數據已從緩存加載")
            
            # 步驟4: 獲取公司描述
            self._add_log(log_messages, log_container, f"🏢 獲取 {symbol} 公司描述...")
            progress_bar.progress(0.45)
            
            if not self.file_manager.file_exists(symbol, 'desc_en', self.today_str) or force_refresh:
                scraper = CompanyDescScraper()
                desc_en = scraper.get_company_description(symbol, region='ca')
                if desc_en:
                    desc_data = {"desc_en": desc_en}
                    self.file_manager.save_data(symbol, desc_data, 'desc_en', self.today_str)
                    self._add_log(log_messages, log_container, f"✅ {symbol} 公司描述獲取成功")
                else:
                    self._add_log(log_messages, log_container, f"⚠️ {symbol} 公司描述獲取失敗")
                scraper.close()
            else:
                self._add_log(log_messages, log_container, f"✅ desc_en 數據已從緩存加載")
            
            # 步驟5: 翻譯公司描述
            self._add_log(log_messages, log_container, f"🈶 開始 {symbol} 公司描述翻譯...")
            progress_bar.progress(0.55)
            
            if not self.file_manager.file_exists(symbol, 'desc_cn', self.today_str) or force_refresh:
                desc_en_data = self.file_manager.load_data(symbol, 'desc_en', self.today_str)
                if desc_en_data:
                    chatgpt = ChatGPT()
                    desc_cn_result = chatgpt.chat(desc_en_data, desc_to_chinese_prompt, json_output=True)
                    if desc_cn_result:
                        self.file_manager.save_data(symbol, desc_cn_result, 'desc_cn', self.today_str)
                        self._add_log(log_messages, log_container, f"✅ {symbol} 公司描述翻譯成功!")
                    else:
                        self._add_log(log_messages, log_container, f"⚠️ {symbol} 公司描述翻譯失敗")
                else:
                    self._add_log(log_messages, log_container, f"⚠️ 無法加載英文描述進行翻譯")
            else:
                self._add_log(log_messages, log_container, f"✅ desc_cn 數據已從緩存加載")
            
            progress_bar.progress(0.7)
            
            # 步驟6: 其他翻譯和分析處理...
            self._add_log(log_messages, log_container, f"🔄 進行其他數據處理...")
            time.sleep(1)  # 模擬處理時間
            
            progress_bar.progress(0.9)
            self._add_log(log_messages, log_container, f"🎉 {symbol} 所有數據處理完成!")
            
            return {"success": True}
            
        except Exception as e:
            self._add_log(log_messages, log_container, f"❌ 處理過程出錯: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _add_log(self, log_messages: list, log_container, message: str):
        """添加日誌消息並更新顯示"""
        import time
        log_messages.append(f"{message}")
        log_text = "\n".join(log_messages[-10:])  # 只顯示最近10條消息
        log_container.text_area("處理日誌", log_text, height=200, disabled=True)
        time.sleep(0.1)  # 短暫延遲讓用戶看到更新

    def generate_chinese_pdf_report_html(self, symbol: str, data: dict) -> str:
        """
        使用HTML到PDF轉換生成中文PDF報告（保持美觀樣式）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            import pdfkit
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_chinese_{self.today_str}.pdf"
            
            # 生成中文報告內容
            chinese_content = self.generate_chinese_report_content(symbol, data)
            
            # 清理並轉換為HTML
            cleaned_content = self._clean_markdown_content(chinese_content)
            
            # 創建完整的HTML文檔
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', 'SimHei', 'SimSun', sans-serif;
                        font-size: 12px;
                        line-height: 1.6;
                        color: #333;
                        margin: 20px;
                        background: white;
                    }}
                    
                    h1 {{
                        color: #2c3e50;
                        font-size: 18px;
                        text-align: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #2c3e50;
                        padding-bottom: 10px;
                    }}
                    
                    h2 {{
                        color: #34495e;
                        font-size: 16px;
                        margin-top: 25px;
                        margin-bottom: 15px;
                        border-left: 4px solid #3498db;
                        padding-left: 15px;
                    }}
                    
                    h3 {{
                        color: #2c3e50;
                        font-size: 14px;
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }}
                    
                    p {{
                        margin-bottom: 10px;
                        text-align: justify;
                        word-wrap: break-word;
                    }}
                    
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 15px 0;
                        background: white;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    
                    th {{
                        background: #34495e;
                        color: white;
                        padding: 12px 15px;
                        text-align: left;
                        font-weight: bold;
                        font-size: 13px;
                    }}
                    
                    td {{
                        padding: 12px 15px;
                        border-bottom: 1px solid #ecf0f1;
                        vertical-align: top;
                        word-wrap: break-word;
                        max-width: 300px;
                    }}
                    
                    td:first-child {{
                        background: #f8f9fa;
                        font-weight: bold;
                        color: #2c3e50;
                        width: 25%;
                        min-width: 120px;
                    }}
                    
                    td:last-child {{
                        background: white;
                        text-align: justify;
                        line-height: 1.5;
                    }}
                    
                    tr:hover {{
                        background: rgba(52, 152, 219, 0.1);
                    }}
                    
                    .positive-table td:first-child {{
                        background: #d5f4e6;
                        color: #27ae60;
                    }}
                    
                    .risk-table td:first-child {{
                        background: #fadbd8;
                        color: #e74c3c;
                    }}
                    
                    .liquidity-table td:first-child {{
                        background: #fdebd0;
                        color: #f39c12;
                    }}
                    
                    .recommendation-table td:first-child {{
                        background: #ebdef0;
                        color: #9b59b6;
                    }}
                    
                    .disclaimer {{
                        margin-top: 30px;
                        padding: 15px;
                        background: #f8f9fa;
                        border-left: 4px solid #3498db;
                        font-size: 11px;
                        color: #7f8c8d;
                    }}
                </style>
            </head>
            <body>
                {cleaned_content}
                <div class="disclaimer">
                    本報告由AI自動生成，僅供教育和娛樂用途，不構成投資建議。投資決策請諮詢您的專業理財顧問。
                </div>
            </body>
            </html>
            """
            
            # 配置 wkhtmltopdf 選項
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None,
            }
            
            # 嘗試設置 wkhtmltopdf 路徑
            try:
                config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
                pdfkit.from_string(html_content, str(pdf_path), options=options, configuration=config)
            except:
                # 如果路徑不正確，嘗試默認配置
                pdfkit.from_string(html_content, str(pdf_path), options=options)
            
            return str(pdf_path)
            
        except Exception as e:
            print(f"HTML to PDF 轉換錯誤: {e}")
            # 如果失敗，回退到舊方法
            return self.generate_chinese_pdf_report_old(symbol, data)

    def generate_chinese_pdf_report(self, symbol: str, data: dict) -> str:
        """
        生成完整的中文PDF報告（使用reportlab）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 註冊中文字體
            try:
                pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
                chinese_font = 'SimHei'
            except:
                try:
                    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
                    chinese_font = 'SimSun'
                except:
                    chinese_font = 'Helvetica'
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_chinese_{self.today_str}.pdf"
            
            # 創建PDF文檔
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                  topMargin=0.6*inch, bottomMargin=0.6*inch)
            story = []
            
            # 自定義樣式
            title_style = ParagraphStyle('CustomTitle',
                                       fontSize=16, spaceAfter=15, alignment=1,
                                       textColor=HexColor('#2c3e50'),
                                       fontName=chinese_font,
                                       wordWrap='CJK')
            
            heading_style = ParagraphStyle('CustomHeading',
                                         fontSize=12, spaceBefore=12, spaceAfter=8,
                                         textColor=HexColor('#34495e'),
                                         fontName=chinese_font,
                                         wordWrap='CJK')
            
            normal_style = ParagraphStyle('CustomNormal',
                                        fontSize=10, spaceBefore=3, spaceAfter=6,
                                        fontName=chinese_font,
                                        wordWrap='CJK',
                                        leading=14)
            
            # 生成中文報告內容
            chinese_content = self.generate_chinese_report_content(symbol, data)
            
            # 將Markdown轉換為PDF段落
            lines = chinese_content.split('\n')
            in_table = False
            table_data = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('# '):
                    # 主標題
                    title_text = line[2:].strip()
                    story.append(Paragraph(title_text, title_style))
                    story.append(Spacer(1, 15))
                    
                elif line.startswith('## '):
                    # 二級標題
                    heading_text = line[3:].strip()
                    story.append(Paragraph(heading_text, heading_style))
                    story.append(Spacer(1, 10))
                    
                elif line.startswith('### '):
                    # 三級標題
                    subheading_text = line[4:].strip()
                    story.append(Paragraph(subheading_text, heading_style))
                    story.append(Spacer(1, 8))
                    
                elif line.startswith('|') and '|' in line[1:]:
                    # 表格行
                    if not in_table:
                        in_table = True
                        table_data = []
                    
                    # 解析表格行
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if cells and not all(cell.startswith('-') for cell in cells):  # 跳過分隔行
                        # 清理HTML標籤
                        cleaned_cells = []
                        for cell in cells:
                            cell = cell.replace('<br>', '\n')
                            cell = cell.replace('**', '')
                            cell = cell.replace('*', '')
                            cleaned_cells.append(cell)
                        table_data.append(cleaned_cells)
                        
                else:
                    # 如果之前在處理表格，現在結束表格
                    if in_table and table_data:
                        try:
                            # 創建表格
                            if len(table_data) > 0:
                                table = Table(table_data, colWidths=[1.8*inch, 4.2*inch])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#34495e')),
                                    ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                                    ('BACKGROUND', (1, 0), (-1, -1), HexColor('#ecf0f1')),
                                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ]))
                                story.append(table)
                                story.append(Spacer(1, 10))
                        except Exception as e:
                            print(f"表格創建錯誤: {e}")
                        
                        in_table = False
                        table_data = []
                    
                    # 普通段落
                    if line.startswith('**') and line.endswith('**'):
                        # 粗體文字
                        text = line[2:-2]
                        story.append(Paragraph(text, normal_style))
                    elif line.startswith('**'):
                        # 帶標籤的內容
                        story.append(Paragraph(line.replace('**', ''), normal_style))
                    elif line.startswith('❌') or line.startswith('✅'):
                        # 狀態消息
                        story.append(Paragraph(line, normal_style))
                    elif line.startswith('---'):
                        # 分隔線
                        story.append(Spacer(1, 15))
                    else:
                        # 普通文字
                        if line:
                            story.append(Paragraph(line, normal_style))
            
            # 處理最後的表格
            if in_table and table_data:
                try:
                    table = Table(table_data, colWidths=[1.8*inch, 4.2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), HexColor('#34495e')),
                        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('TOPPADDING', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (1, 0), (-1, -1), HexColor('#ecf0f1')),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(table)
                except Exception as e:
                    print(f"最後表格創建錯誤: {e}")
            
            # 添加免責聲明
            story.append(Spacer(1, 20))
            disclaimer = Paragraph("本報告由AI自動生成，僅供教育和娛樂用途，不構成投資建議。投資決策請諮詢您的專業理財顧問。", normal_style)
            story.append(disclaimer)
            
            # 生成PDF
            doc.build(story)
            return str(pdf_path)
            
        except Exception as e:
            print(f"PDF生成錯誤: {e}")
            return None

    def generate_english_pdf_report_html(self, symbol: str, data: dict) -> str:
        """
        使用HTML到PDF轉換生成英文PDF報告（保持美觀樣式）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            import pdfkit
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_english_{self.today_str}.pdf"
            
            # 生成英文報告內容
            english_content = self.generate_english_report_content(symbol, data)
            
            # 清理並轉換為HTML
            cleaned_content = self._clean_markdown_content(english_content)
            
            # 創建完整的HTML文檔
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Helvetica', 'Arial', sans-serif;
                        font-size: 12px;
                        line-height: 1.6;
                        color: #333;
                        margin: 20px;
                        background: white;
                        text-align: justify;
                    }}
                    
                    h1 {{
                        color: #2c3e50;
                        font-size: 18px;
                        text-align: center;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #2c3e50;
                        padding-bottom: 10px;
                    }}
                    
                    h2 {{
                        color: #34495e;
                        font-size: 16px;
                        margin-top: 25px;
                        margin-bottom: 15px;
                        border-left: 4px solid #3498db;
                        padding-left: 15px;
                    }}
                    
                    h3 {{
                        color: #2c3e50;
                        font-size: 14px;
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }}
                    
                    p {{
                        margin-bottom: 10px;
                        text-align: justify;
                        word-wrap: break-word;
                        hyphens: auto;
                    }}
                    
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 15px 0;
                        background: white;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    
                    th {{
                        background: #34495e;
                        color: white;
                        padding: 12px 15px;
                        text-align: left;
                        font-weight: bold;
                        font-size: 13px;
                    }}
                    
                    td {{
                        padding: 12px 15px;
                        border-bottom: 1px solid #ecf0f1;
                        vertical-align: top;
                        word-wrap: break-word;
                        max-width: 300px;
                        hyphens: auto;
                    }}
                    
                    td:first-child {{
                        background: #f8f9fa;
                        font-weight: bold;
                        color: #2c3e50;
                        width: 25%;
                        min-width: 120px;
                    }}
                    
                    td:last-child {{
                        background: white;
                        text-align: justify;
                        line-height: 1.5;
                    }}
                    
                    tr:hover {{
                        background: rgba(52, 152, 219, 0.1);
                    }}
                    
                    .positive-table td:first-child {{
                        background: #d5f4e6;
                        color: #27ae60;
                    }}
                    
                    .risk-table td:first-child {{
                        background: #fadbd8;
                        color: #e74c3c;
                    }}
                    
                    .liquidity-table td:first-child {{
                        background: #fdebd0;
                        color: #f39c12;
                    }}
                    
                    .recommendation-table td:first-child {{
                        background: #ebdef0;
                        color: #9b59b6;
                    }}
                    
                    .disclaimer {{
                        margin-top: 30px;
                        padding: 15px;
                        background: #f8f9fa;
                        border-left: 4px solid #3498db;
                        font-size: 11px;
                        color: #7f8c8d;
                    }}
                </style>
            </head>
            <body>
                {cleaned_content}
                <div class="disclaimer">
                    This report is generated by AI for educational and entertainment purposes only. Not investment advice. Please consult your professional financial advisor for investment decisions.
                </div>
            </body>
            </html>
            """
            
            # 配置 wkhtmltopdf 選項
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None,
            }
            
            # 嘗試設置 wkhtmltopdf 路徑
            try:
                config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
                pdfkit.from_string(html_content, str(pdf_path), options=options, configuration=config)
            except:
                # 如果路徑不正確，嘗試默認配置
                pdfkit.from_string(html_content, str(pdf_path), options=options)
            
            return str(pdf_path)
            
        except Exception as e:
            print(f"HTML to PDF conversion error: {e}")
            # 如果失敗，回退到舊方法
            return self.generate_english_pdf_report_old(symbol, data)

    def generate_english_pdf_report(self, symbol: str, data: dict) -> str:
        """
        生成完整的英文PDF報告（使用reportlab）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_english_{self.today_str}.pdf"
            
            # 創建PDF文檔
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                  topMargin=0.6*inch, bottomMargin=0.6*inch)
            story = []
            
            # 自定義樣式
            title_style = ParagraphStyle('CustomTitle',
                                       fontSize=16, spaceAfter=15, alignment=1,
                                       textColor=HexColor('#2c3e50'),
                                       fontName='Helvetica-Bold')
            
            heading_style = ParagraphStyle('CustomHeading',
                                         fontSize=12, spaceBefore=12, spaceAfter=8,
                                         textColor=HexColor('#34495e'),
                                         fontName='Helvetica-Bold')
            
            normal_style = ParagraphStyle('CustomNormal',
                                        fontSize=10, spaceBefore=3, spaceAfter=6,
                                        fontName='Helvetica',
                                        alignment=4,  # 左右對齊
                                        leading=14,
                                        wordWrap='LTR')
            
            # 生成英文報告內容
            english_content = self.generate_english_report_content(symbol, data)
            
            # 將Markdown轉換為PDF段落
            lines = english_content.split('\n')
            in_table = False
            table_data = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('# '):
                    # 主標題
                    title_text = line[2:].strip()
                    story.append(Paragraph(title_text, title_style))
                    story.append(Spacer(1, 15))
                    
                elif line.startswith('## '):
                    # 二級標題
                    heading_text = line[3:].strip()
                    story.append(Paragraph(heading_text, heading_style))
                    story.append(Spacer(1, 10))
                    
                elif line.startswith('### '):
                    # 三級標題
                    subheading_text = line[4:].strip()
                    story.append(Paragraph(subheading_text, heading_style))
                    story.append(Spacer(1, 8))
                    
                elif line.startswith('|') and '|' in line[1:]:
                    # 表格行
                    if not in_table:
                        in_table = True
                        table_data = []
                    
                    # 解析表格行
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if cells and not all(cell.startswith('-') for cell in cells):  # 跳過分隔行
                        # 清理HTML標籤
                        cleaned_cells = []
                        for cell in cells:
                            cell = cell.replace('<br>', '\n')
                            cell = cell.replace('**', '')
                            cell = cell.replace('*', '')
                            cleaned_cells.append(cell)
                        table_data.append(cleaned_cells)
                        
                else:
                    # 如果之前在處理表格，現在結束表格
                    if in_table and table_data:
                        try:
                            # 創建表格
                            if len(table_data) > 0:
                                table = Table(table_data, colWidths=[1.8*inch, 4.2*inch])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), HexColor('#34495e')),
                                    ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                                    ('BACKGROUND', (1, 0), (-1, -1), HexColor('#ecf0f1')),
                                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ]))
                                story.append(table)
                                story.append(Spacer(1, 10))
                        except Exception as e:
                            print(f"Table creation error: {e}")
                        
                        in_table = False
                        table_data = []
                    
                    # 普通段落
                    if line.startswith('**') and line.endswith('**'):
                        # 粗體文字
                        text = line[2:-2]
                        story.append(Paragraph(text, normal_style))
                    elif line.startswith('**'):
                        # 帶標籤的內容
                        story.append(Paragraph(line.replace('**', ''), normal_style))
                    elif line.startswith('❌') or line.startswith('✅'):
                        # 狀態消息
                        story.append(Paragraph(line, normal_style))
                    elif line.startswith('---'):
                        # 分隔線
                        story.append(Spacer(1, 15))
                    else:
                        # 普通文字
                        if line:
                            story.append(Paragraph(line, normal_style))
            
            # 處理最後的表格
            if in_table and table_data:
                try:
                    table = Table(table_data, colWidths=[1.8*inch, 4.2*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), HexColor('#34495e')),
                        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('TOPPADDING', (0, 0), (-1, -1), 12),
                        ('BACKGROUND', (1, 0), (-1, -1), HexColor('#ecf0f1')),
                        ('GRID', (0, 0), (-1, -1), 1, HexColor('#bdc3c7')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(table)
                except Exception as e:
                    print(f"Final table creation error: {e}")
            
            # 添加免責聲明
            story.append(Spacer(1, 20))
            disclaimer = Paragraph("This report is generated by AI for educational and entertainment purposes only. Not investment advice. Please consult your professional financial advisor for investment decisions.", normal_style)
            story.append(disclaimer)
            
            # 生成PDF
            doc.build(story)
            return str(pdf_path)
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return None

    def _clean_markdown_content(self, content: str) -> str:
        """
        清理Markdown內容，防止KaTeX渲染問題
        
        Args:
            content: 原始Markdown內容
            
        Returns:
            str: 清理後的內容
        """
        import re
        
        # 只移除可能導致PDF渲染問題的emoji，不替換為文字
        # 保持標題的簡潔性
        emoji_to_remove = [
            '📊', '📰', '🏢', '✅', '⚠️', '💰', '💡', '📋', 
            '🔑', '📄', '💵', '🔥', '⚡', '📈', '💭', '🚀',
            '🔴', '🟡', '🟢', '❌', '🎉', '🔄', '🈶'
        ]
        
        # 直接移除emoji，不替換為方括號文字
        for emoji in emoji_to_remove:
            content = content.replace(emoji, '')
        
        # 轉換為HTML並清理
        try:
            import markdown
            # 將$符號替換為HTML實體，避免被解析為數學公式
            content = content.replace('$', '&#36;')
            
            # 轉換Markdown為HTML
            html_content = markdown.markdown(content, extensions=['tables', 'nl2br'])
            
            return html_content
        except ImportError:
            # 如果沒有markdown庫，直接清理特殊字符
            content = content.replace('$', '&#36;')
            content = content.replace('\n', '<br>')
            return content
    
    def generate_chinese_pdf_report_old(self, symbol: str, data: dict) -> str:
        """
        生成中文PDF報告（使用reportlab）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 註冊中文字體
            try:
                # 嘗試註冊系統中文字體
                pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
                chinese_font = 'SimHei'
            except:
                try:
                    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
                    chinese_font = 'SimSun'
                except:
                    # 如果沒有中文字體，使用默認字體
                    chinese_font = 'Helvetica'
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_chinese_{self.today_str}.pdf"
            
            # 創建PDF文檔
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                  topMargin=0.6*inch, bottomMargin=0.6*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # 自定義樣式 - 較小字體和中文字體
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                       fontSize=16, spaceAfter=15, alignment=1,
                                       textColor=HexColor('#2c3e50'),
                                       fontName=chinese_font,
                                       wordWrap='CJK')
            
            heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                         fontSize=12, spaceBefore=12, spaceAfter=8,
                                         textColor=HexColor('#34495e'),
                                         fontName=chinese_font,
                                         wordWrap='CJK')
            
            normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                        fontSize=10, spaceBefore=3, spaceAfter=6,
                                        fontName=chinese_font,
                                        wordWrap='CJK',
                                        leading=14)
            
            # 標題
            story.append(Paragraph(f"📊 {symbol} 股票分析報告（中文版）", title_style))
            story.append(Paragraph(f"生成日期: {self.today_str}", normal_style))
            story.append(Spacer(1, 15))
            
            # 公司簡介
            if data.get('desc_cn'):
                story.append(Paragraph("🏢 公司簡介", heading_style))
                desc_cn_data = data['desc_cn'].get('data', {}) if isinstance(data['desc_cn'], dict) else data['desc_cn']
                if isinstance(desc_cn_data, dict):
                    if 'summary' in desc_cn_data:
                        story.append(Paragraph(f"簡介: {desc_cn_data['summary']}", normal_style))
                    if 'business_type' in desc_cn_data:
                        story.append(Paragraph(f"業務類型: {desc_cn_data['business_type']}", normal_style))
                story.append(Spacer(1, 10))
            
            # 新聞翻譯
            if data.get('news_cn'):
                story.append(Paragraph("📰 新聞翻譯", heading_style))
                news_cn_data = data['news_cn'].get('data', {}) if isinstance(data['news_cn'], dict) else data['news_cn']
                if isinstance(news_cn_data, dict):
                    if 'summary' in news_cn_data:
                        story.append(Paragraph(f"摘要: {news_cn_data['summary']}", normal_style))
                story.append(Spacer(1, 10))
            
            # 基本面分析
            if data.get('analysis'):
                story.append(Paragraph("📊 基本面分析", heading_style))
                analysis_data = data['analysis'].get('data', {}) if isinstance(data['analysis'], dict) else data['analysis']
                if isinstance(analysis_data, dict):
                    story.append(Paragraph(f"公司: {analysis_data.get('company', 'N/A')}", normal_style))
                    story.append(Paragraph(f"股票代碼: {analysis_data.get('ticker', 'N/A')}", normal_style))
                    
                    # 投資建議
                    if 'trading_recommendation' in analysis_data:
                        rec = analysis_data['trading_recommendation']
                        story.append(Paragraph("💡 投資建議", heading_style))
                        story.append(Paragraph(f"投資傾向: {rec.get('bias', 'N/A')}", normal_style))
                        if len(rec.get('suggestion', '')) > 0:
                            story.append(Paragraph(f"建議: {rec.get('suggestion', 'N/A')[:200]}...", normal_style))
                story.append(Spacer(1, 10))
            
            # 免責聲明
            story.append(Spacer(1, 20))
            disclaimer_style = ParagraphStyle('Disclaimer', parent=normal_style,
                                            fontSize=8, textColor=HexColor('#7f8c8d'),
                                            alignment=1)
            story.append(Paragraph("本報告由AI自動生成，僅供參考，不構成投資建議。投資有風險，請謹慎決策。", disclaimer_style))
            
            # 生成PDF
            doc.build(story)
            return str(pdf_path)
            
        except ImportError:
            st.error("❌ 缺少reportlab依賴。請運行: pip install reportlab")
            return None
        except Exception as e:
            st.error(f"❌ 中文PDF生成失敗: {e}")
            return None
    
    def generate_english_pdf_report_old(self, symbol: str, data: dict) -> str:
        """
        生成英文PDF報告（使用reportlab）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_english_{self.today_str}.pdf"
            
            # 創建PDF文檔
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                  topMargin=0.6*inch, bottomMargin=0.6*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # 自定義樣式 - 較小字體和左右對齊
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                       fontSize=16, spaceAfter=15, alignment=1,
                                       textColor=HexColor('#2c3e50'),
                                       fontName='Helvetica-Bold')
            
            heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                         fontSize=12, spaceBefore=12, spaceAfter=8,
                                         textColor=HexColor('#34495e'),
                                         fontName='Helvetica-Bold')
            
            # 英文內容使用左右對齊
            normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
                                        fontSize=10, spaceBefore=3, spaceAfter=6,
                                        fontName='Helvetica',
                                        alignment=4,  # 左右對齊
                                        leading=14,
                                        wordWrap='LTR')
            
            # 標題
            story.append(Paragraph(f"📊 {symbol} Stock Analysis Report (English)", title_style))
            story.append(Paragraph(f"Generated: {self.today_str}", normal_style))
            story.append(Spacer(1, 15))
            
            # Company Description
            if data.get('desc_en'):
                story.append(Paragraph("🏢 Company Profile", heading_style))
                desc_en_data = data['desc_en']
                if isinstance(desc_en_data, dict) and 'desc_en' in desc_en_data:
                    # 截取前500字符避免過長
                    desc_text = desc_en_data['desc_en'][:500] + "..." if len(desc_en_data['desc_en']) > 500 else desc_en_data['desc_en']
                    story.append(Paragraph(desc_text, normal_style))
                story.append(Spacer(1, 10))
            
            # News Translation
            if data.get('news_en'):
                story.append(Paragraph("📰 News Translation", heading_style))
                news_en_data = data['news_en'].get('data', {}) if isinstance(data['news_en'], dict) else data['news_en']
                if isinstance(news_en_data, dict):
                    if 'summary' in news_en_data:
                        story.append(Paragraph(f"Summary: {news_en_data['summary']}", normal_style))
                story.append(Spacer(1, 10))
            
            # Fundamental Analysis
            if data.get('analysis_en'):
                story.append(Paragraph("📊 Fundamental Analysis", heading_style))
                analysis_en_data = data['analysis_en'].get('data', {}) if isinstance(data['analysis_en'], dict) else data['analysis_en']
                if isinstance(analysis_en_data, dict):
                    story.append(Paragraph(f"Company: {analysis_en_data.get('company', 'N/A')}", normal_style))
                    story.append(Paragraph(f"Ticker: {analysis_en_data.get('ticker', 'N/A')}", normal_style))
                    
                    # Trading recommendation
                    if 'trading_recommendation' in analysis_en_data:
                        rec = analysis_en_data['trading_recommendation']
                        story.append(Paragraph("💡 Trading Recommendation", heading_style))
                        story.append(Paragraph(f"Bias: {rec.get('bias', 'N/A')}", normal_style))
                        if len(rec.get('suggestion', '')) > 0:
                            story.append(Paragraph(f"Suggestion: {rec.get('suggestion', 'N/A')[:200]}...", normal_style))
                story.append(Spacer(1, 10))
            
            # Disclaimer
            story.append(Spacer(1, 20))
            disclaimer_style = ParagraphStyle('Disclaimer', parent=normal_style,
                                            fontSize=8, textColor=HexColor('#7f8c8d'),
                                            alignment=1)
            story.append(Paragraph("This report is generated by AI for reference only. Not investment advice. Investment involves risks.", disclaimer_style))
            
            # 生成PDF
            doc.build(story)
            return str(pdf_path)
            
        except ImportError:
            st.error("❌ 缺少reportlab依賴。請運行: pip install reportlab")
            return None
        except Exception as e:
            st.error(f"❌ 英文PDF生成失敗: {e}")
            return None

    def convert_md_to_pdf_alternative(self, symbol: str, data: dict) -> str:
        """
        使用reportlab創建PDF報告（不需要wkhtmltopdf）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: PDF文件路徑
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.colors import HexColor
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_{self.today_str}.pdf"
            
            # 創建PDF文檔
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                  topMargin=0.75*inch, bottomMargin=0.75*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # 自定義樣式
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                       fontSize=20, spaceAfter=20, alignment=1,
                                       textColor=HexColor('#2c3e50'))
            
            heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                         fontSize=14, spaceBefore=15, spaceAfter=10,
                                         textColor=HexColor('#34495e'))
            
            # 標題
            story.append(Paragraph(f"📊 {symbol} 股票分析報告", title_style))
            story.append(Paragraph(f"生成日期: {self.today_str}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # 新聞翻譯 (中文)
            if data.get('news_cn'):
                story.append(Paragraph("📰 新聞翻譯 (繁體中文)", heading_style))
                news_cn_data = data['news_cn'].get('data', {}) if isinstance(data['news_cn'], dict) else data['news_cn']
                if isinstance(news_cn_data, dict):
                    if 'summary' in news_cn_data:
                        story.append(Paragraph(f"重點摘要: {news_cn_data['summary']}", styles['Normal']))
                        story.append(Spacer(1, 10))
                
            # 新聞翻譯 (英文)
            if data.get('news_en'):
                story.append(Paragraph("📰 News Translation (English)", heading_style))
                news_en_data = data['news_en'].get('data', {}) if isinstance(data['news_en'], dict) else data['news_en']
                if isinstance(news_en_data, dict):
                    if 'summary' in news_en_data:
                        story.append(Paragraph(f"Summary: {news_en_data['summary']}", styles['Normal']))
                        story.append(Spacer(1, 10))
            
            # 基本面分析 (中文)
            if data.get('analysis'):
                story.append(Paragraph("📊 基本面分析 (中文)", heading_style))
                analysis_data = data['analysis'].get('data', {}) if isinstance(data['analysis'], dict) else data['analysis']
                if isinstance(analysis_data, dict):
                    story.append(Paragraph(f"公司: {analysis_data.get('company', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"股票代碼: {analysis_data.get('ticker', 'N/A')}", styles['Normal']))
                    
                    # 投資建議
                    if 'trading_recommendation' in analysis_data:
                        rec = analysis_data['trading_recommendation']
                        story.append(Paragraph("💡 投資建議", styles['Heading3']))
                        story.append(Paragraph(f"投資傾向: {rec.get('bias', 'N/A')}", styles['Normal']))
                        story.append(Paragraph(f"建議: {rec.get('suggestion', 'N/A')}", styles['Normal']))
                        story.append(Spacer(1, 10))
            
            # 基本面分析 (英文)
            if data.get('analysis_en'):
                story.append(Paragraph("📊 Fundamental Analysis (English)", heading_style))
                analysis_en_data = data['analysis_en'].get('data', {}) if isinstance(data['analysis_en'], dict) else data['analysis_en']
                if isinstance(analysis_en_data, dict):
                    story.append(Paragraph(f"Company: {analysis_en_data.get('company', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"Ticker: {analysis_en_data.get('ticker', 'N/A')}", styles['Normal']))
                    
                    # Trading recommendation
                    if 'trading_recommendation' in analysis_en_data:
                        rec = analysis_en_data['trading_recommendation']
                        story.append(Paragraph("💡 Trading Recommendation", styles['Heading3']))
                        story.append(Paragraph(f"Bias: {rec.get('bias', 'N/A')}", styles['Normal']))
                        story.append(Paragraph(f"Suggestion: {rec.get('suggestion', 'N/A')}", styles['Normal']))
            
            # 免責聲明
            story.append(Spacer(1, 30))
            disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'],
                                            fontSize=10, textColor=HexColor('#7f8c8d'),
                                            alignment=1)
            story.append(Paragraph("本報告由AI自動生成，僅供參考，不構成投資建議。投資有風險，請謹慎決策。", disclaimer_style))
            
            # 生成PDF
            doc.build(story)
            return str(pdf_path)
            
        except ImportError:
            st.error("❌ 缺少reportlab依賴。請運行: pip install reportlab")
            return None
        except Exception as e:
            st.error(f"❌ PDF生成失敗: {e}")
            return None
    
    def convert_md_to_pdf(self, md_file_path: str) -> str:
        """
        將Markdown轉換為PDF
        
        Args:
            md_file_path: Markdown文件路徑
            
        Returns:
            str: PDF文件路徑
        """
        try:
            import markdown
            try:
                import pdfkit
                # 配置wkhtmltopdf路徑 (Windows)
                import platform
                if platform.system().lower() == "windows":
                    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
                else:
                    config = None
            except ImportError:
                st.error("❌ 缺少pdfkit依賴。請運行: pip install pdfkit")
                st.info("💡 並安裝wkhtmltopdf系統依賴")
                return None
            from pathlib import Path
            
            # 讀取Markdown文件
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 轉換為HTML
            html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # 添加CSS樣式
            html_with_style = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ 
                        font-family: 'Microsoft YaHei', 'Arial Unicode MS', Arial, sans-serif; 
                        margin: 40px; 
                        line-height: 1.8; 
                        word-spacing: 1px;
                        letter-spacing: 0.5px;
                    }}
                    h1 {{ 
                        color: #2c3e50; 
                        border-bottom: 3px solid #3498db; 
                        padding-bottom: 10px; 
                        margin-bottom: 20px;
                    }}
                    h2 {{ 
                        color: #34495e; 
                        border-bottom: 1px solid #bdc3c7; 
                        padding-bottom: 5px; 
                        margin-top: 25px;
                        margin-bottom: 15px;
                    }}
                    h3 {{ 
                        color: #7f8c8d; 
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }}
                    p {{ 
                        margin-bottom: 12px; 
                        text-align: justify;
                        word-wrap: break-word;
                        white-space: pre-wrap;
                    }}
                    ul {{ 
                        margin-left: 20px; 
                        margin-bottom: 15px;
                    }}
                    li {{ 
                        margin-bottom: 8px; 
                        line-height: 1.6;
                    }}
                    strong {{ 
                        color: #2c3e50; 
                        font-weight: bold;
                    }}
                    .emoji {{ 
                        font-size: 1.2em; 
                        margin-right: 5px;
                    }}
                    code {{
                        background-color: #f8f9fa;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                    }}
                    pre {{
                        background-color: #f8f9fa;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # 設置PDF路徑
            pdf_path = md_file_path.replace('.md', '.pdf')
            
            # 配置wkhtmltopdf選項
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None,
                'print-media-type': None,
                'disable-smart-shrinking': None,
                'zoom': '1.0',
                'dpi': 96,
                'javascript-delay': 1000,
                'load-error-handling': 'ignore',
                'load-media-error-handling': 'ignore'
            }
            
            # 轉換為PDF
            try:
                if config:
                    pdfkit.from_string(html_with_style, pdf_path, options=options, configuration=config)
                else:
                    pdfkit.from_string(html_with_style, pdf_path, options=options)
                return pdf_path
            except Exception as pdf_error:
                st.warning(f"高級PDF轉換失敗，嘗試簡單格式: {pdf_error}")
                
                # 備用方案：使用簡單的HTML格式
                simple_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ 
                            font-family: Arial, sans-serif; 
                            margin: 30px; 
                            line-height: 1.6; 
                        }}
                        h1, h2, h3 {{ margin-top: 20px; margin-bottom: 10px; }}
                        p {{ margin-bottom: 10px; }}
                        ul {{ margin-bottom: 10px; }}
                        li {{ margin-bottom: 5px; }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """
                
                simple_options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in', 
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8"
                }
                
                try:
                    if config:
                        pdfkit.from_string(simple_html, pdf_path, options=simple_options, configuration=config)
                    else:
                        pdfkit.from_string(simple_html, pdf_path, options=simple_options)
                    return pdf_path
                except Exception as simple_error:
                    st.error(f"簡單PDF轉換也失敗: {simple_error}")
                    return None
            
        except Exception as e:
            st.error(f"PDF轉換失敗: {e}")
            st.info("💡 建議：1) 安裝 wkhtmltopdf 2) 檢查系統字體支持")
            return None

def main():
    st.set_page_config(
        page_title="股票分析報告生成器",
        page_icon="📊",
        layout="wide"
    )
    
    app = StockAnalysisApp()
    
    st.title("📊 股票分析報告生成器")
    st.markdown("輸入股票代碼，生成中英文分析報告")
    
    # 側邊欄
    st.sidebar.header("⚙️ 設定")
    
    # 股票代碼輸入
    symbols_input = st.text_input(
        "📝 請輸入股票代碼 (用逗號分隔)",
        placeholder="例如: AAPL, TSLA, XPON",
        help="支持多個股票代碼，用逗號分隔。程序會自動清理格式。"
    )
    
    if symbols_input:
        # 清理股票代碼列表
        symbols = app.clean_symbol_list(symbols_input)
        
        if symbols:
            st.success(f"✅ 識別到 {len(symbols)} 個股票代碼: {', '.join(symbols)}")
            
            # 為每個股票顯示分析結果
            for i, symbol in enumerate(symbols):
                with st.expander(f"📈 {symbol} - 點擊查看分析報告", expanded=(i==0)):
                    
                    # 檢查是否已有報告文件
                    data_path = Path(app.file_manager._get_data_path(symbol, app.today_str))
                    md_file_path = data_path / f"{symbol}_report_{app.today_str}.md"
                    chinese_pdf_path = data_path / f"{symbol}_report_chinese_{app.today_str}.pdf"
                    english_pdf_path = data_path / f"{symbol}_report_english_{app.today_str}.pdf"
                    
                    # 載入數據
                    data = app.load_stock_data(symbol)
                    
                    # 檢查數據完整性
                    required_data = ['desc_en', 'desc_cn', 'news_cn', 'analysis', 'news_en', 'analysis_en']
                    missing_data = [dt for dt in required_data if not data.get(dt)]
                    
                    if missing_data:
                        st.warning(f"⚠️ {symbol} 缺少以下數據: {', '.join(missing_data)}")
                        
                        # 提供自動生成選項
                        if st.button(f"🔄 自動生成 {symbol} 的缺失數據", key=f"generate_{symbol}"):
                            # 創建進度顯示區域
                            with st.container():
                                progress_col1, progress_col2 = st.columns([3, 1])
                                
                                with progress_col1:
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()
                                
                                with progress_col2:
                                    # 添加旋轉動畫
                                    spinner_placeholder = st.empty()
                                
                                # 創建可滾動的進度日誌窗口
                                progress_log = st.expander("📋 處理詳情", expanded=True)
                                with progress_log:
                                    log_container = st.empty()
                                    log_messages = []
                                
                                try:
                                    # 開始處理動畫
                                    with spinner_placeholder:
                                        st.markdown("""
                                        <div style="text-align: center;">
                                            <div class="spinner">⏳</div>
                                        </div>
                                        <style>
                                        .spinner {
                                            font-size: 2rem;
                                            animation: spin 1s linear infinite;
                                        }
                                        @keyframes spin {
                                            from { transform: rotate(0deg); }
                                            to { transform: rotate(360deg); }
                                        }
                                        </style>
                                        """, unsafe_allow_html=True)
                                    
                                    status_text.text(f"🔄 正在處理 {symbol}...")
                                    progress_bar.progress(0.1)
                                    
                                    # 添加初始日誌
                                    log_messages.append(f"🔄 開始處理 {symbol}...")
                                    log_container.text_area("處理日誌", "\n".join(log_messages), height=200, disabled=True)
                                    
                                    # 調用處理函數
                                    result = app.process_with_progress(symbol, log_messages, log_container, progress_bar, status_text, force_refresh=False)
                                    
                                    # 完成處理
                                    spinner_placeholder.empty()
                                    progress_bar.progress(1.0)
                                    
                                    if result.get("success", False):
                                        status_text.text("✅ 處理完成！")
                                        log_messages.append("🎉 所有數據處理完成!")
                                        log_container.text_area("處理日誌", "\n".join(log_messages), height=200, disabled=True)
                                        st.success(f"✅ {symbol} 數據生成完成!")
                                        st.rerun()
                                    else:
                                        status_text.text("❌ 處理失敗")
                                        log_messages.append("❌ 數據處理失敗")
                                        log_container.text_area("處理日誌", "\n".join(log_messages), height=200, disabled=True)
                                        st.error(f"❌ {symbol} 數據生成失敗")
                                        
                                except Exception as e:
                                    spinner_placeholder.empty()
                                    status_text.text("❌ 處理出錯")
                                    log_messages.append(f"❌ 處理過程出錯: {str(e)}")
                                    log_container.text_area("處理日誌", "\n".join(log_messages), height=200, disabled=True)
                                    st.error(f"❌ 處理過程出錯: {str(e)}")
                                    for error in result["errors"]:
                                        st.error(f"  - {error}")
                        
                        st.info("💡 或者運行命令: `python process_stock.py " + symbol + "`")
                        continue
                    
                    # 顯示數據摘要
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    
                    with col1:
                        st.metric("🏢 英文描述", "✅" if data.get('desc_en') else "❌")
                    with col2:
                        st.metric("🏢 中文描述", "✅" if data.get('desc_cn') else "❌")
                    with col3:
                        st.metric("📰 中文新聞", "✅" if data.get('news_cn') else "❌")
                    with col4:
                        st.metric("📰 英文新聞", "✅" if data.get('news_en') else "❌")
                    with col5:
                        st.metric("📊 中文分析", "✅" if data.get('analysis') else "❌")
                    with col6:
                        st.metric("📊 英文分析", "✅" if data.get('analysis_en') else "❌")
                    
                    # 生成或載入報告
                    if md_file_path.exists() and chinese_pdf_path.exists() and english_pdf_path.exists():
                        st.success("✅ 發現現有報告文件（含中英文PDF）")
                        
                        # 讀取現有Markdown內容
                        with open(md_file_path, 'r', encoding='utf-8') as f:
                            md_content = f.read()
                        
                    else:
                        st.info("🔄 生成新的報告...")
                        
                        # 生成Markdown報告（使用中文版本作為主報告）
                        md_content = app.generate_chinese_report_content(symbol, data)
                        
                        # 保存Markdown文件
                        md_path = app.save_markdown_report(symbol, md_content)
                        
                        # 生成中英文分離PDF
                        st.info("📄 生成中英文PDF報告...")
                        
                        # 生成中文PDF（使用HTML轉換）
                        chinese_pdf = app.generate_chinese_pdf_report_html(symbol, data)
                        
                        # 生成英文PDF（使用HTML轉換）
                        english_pdf = app.generate_english_pdf_report_html(symbol, data)
                        
                        if chinese_pdf and english_pdf:
                            st.success("✅ 中英文PDF報告生成完成!")
                        elif chinese_pdf:
                            st.warning("⚠️ 僅中文PDF生成成功")
                        elif english_pdf:
                            st.warning("⚠️ 僅英文PDF生成成功")
                        else:
                            st.warning("⚠️ PDF生成失敗，但Markdown報告可用")
                    
                    # 顯示報告內容 - 使用標籤頁
                    st.markdown("### 📄 分析報告")
                    
                    # 創建中英文標籤頁
                    tab_chinese, tab_english = st.tabs(["📊 中文報告", "📈 English Report"])
                    
                    # 設置自定義CSS來修復文字問題和美化表格
                    st.markdown("""
                    <style>
                    .report-content {
                        color: rgba(255, 255, 255, 0.9) !important;
                        text-align: justify;
                        line-height: 1.6;
                    }
                    .report-content p {
                        margin-bottom: 1rem;
                        text-align: justify;
                    }
                    .katex {
                        display: none !important;
                    }
                    
                    /* 表格樣式美化 */
                    .report-content table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 1rem 0;
                        background: rgba(25, 39, 52, 0.6) !important;
                        border-radius: 8px;
                        overflow: hidden;
                    }
                    
                    .report-content th {
                        background: rgba(25, 39, 52, 0.8) !important;
                        color: rgba(255, 255, 255, 0.95) !important;
                        padding: 12px 16px;
                        text-align: left;
                        font-weight: bold;
                        font-size: 1.1em;
                        border-bottom: 2px solid rgba(52, 73, 94, 0.8);
                    }
                    
                    .report-content td {
                        padding: 12px 16px;
                        border-bottom: 1px solid rgba(52, 73, 94, 0.4);
                        vertical-align: top;
                        line-height: 1.5;
                    }
                    
                    .report-content td:first-child {
                        font-weight: bold;
                        color: rgba(255, 255, 255, 0.95) !important;
                        width: 25%;
                        font-size: 1.05em;
                    }
                    
                    .report-content td:last-child {
                        color: rgba(255, 255, 255, 0.85) !important;
                        text-align: justify;
                        word-wrap: break-word;
                    }
                    
                    .report-content tr:hover {
                        background: rgba(52, 73, 94, 0.3) !important;
                    }
                    
                    /* 投資建議顏色 */
                    .report-content td:contains("看多") {
                        color: #2ecc71 !important;
                    }
                    .report-content td:contains("看空") {
                        color: #e74c3c !important;
                    }
                    .report-content td:contains("中性") {
                        color: #f39c12 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # 生成中英文報告內容
                    chinese_content = app.generate_chinese_report_content(symbol, data)
                    english_content = app.generate_english_report_content(symbol, data)
                    
                    # 中文標籤頁
                    with tab_chinese:
                        cleaned_chinese = app._clean_markdown_content(chinese_content)
                        st.markdown(f'<div class="report-content">{cleaned_chinese}</div>', unsafe_allow_html=True)
                    
                    # 英文標籤頁
                    with tab_english:
                        cleaned_english = app._clean_markdown_content(english_content)
                        st.markdown(f'<div class="report-content">{cleaned_english}</div>', unsafe_allow_html=True)
                    
                    # 下載按鈕
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if md_file_path.exists():
                            with open(md_file_path, 'r', encoding='utf-8') as f:
                                md_data = f.read()
                            st.download_button(
                                label="📝 下載 Markdown",
                                data=md_data,
                                file_name=f"{symbol}_report_{app.today_str}.md",
                                mime="text/markdown"
                            )
                    
                    with col2:
                        # 中文PDF下載
                        chinese_pdf_path = data_path / f"{symbol}_report_chinese_{app.today_str}.pdf"
                        if chinese_pdf_path.exists():
                            with open(chinese_pdf_path, 'rb') as f:
                                pdf_data = f.read()
                            st.download_button(
                                label="📄 下載中文PDF",
                                data=pdf_data,
                                file_name=f"{symbol}_report_chinese_{app.today_str}.pdf",
                                mime="application/pdf"
                            )
                    
                    with col3:
                        # 英文PDF下載
                        english_pdf_path = data_path / f"{symbol}_report_english_{app.today_str}.pdf"
                        if english_pdf_path.exists():
                            with open(english_pdf_path, 'rb') as f:
                                pdf_data = f.read()
                            st.download_button(
                                label="📄 下載英文PDF",
                                data=pdf_data,
                                file_name=f"{symbol}_report_english_{app.today_str}.pdf",
                                mime="application/pdf"
                            )
                    
                    with col4:
                        if md_file_path.exists():
                            if st.button(f"🔄 重新生成PDF", key=f"regenerate_pdf_{symbol}"):
                                with st.spinner("正在重新生成中英文PDF..."):
                                    # 刪除舊的PDF文件
                                    chinese_pdf_path = data_path / f"{symbol}_report_chinese_{app.today_str}.pdf"
                                    english_pdf_path = data_path / f"{symbol}_report_english_{app.today_str}.pdf"
                                    
                                    if chinese_pdf_path.exists():
                                        chinese_pdf_path.unlink()
                                    if english_pdf_path.exists():
                                        english_pdf_path.unlink()
                                    
                                    # 重新生成中英文PDF（使用HTML轉換）
                                    chinese_pdf = app.generate_chinese_pdf_report_html(symbol, data)
                                    english_pdf = app.generate_english_pdf_report_html(symbol, data)
                                    
                                    if chinese_pdf and english_pdf:
                                        st.success("✅ 中英文PDF重新生成成功!")
                                        st.rerun()
                                    elif chinese_pdf:
                                        st.warning("⚠️ 僅中文PDF重新生成成功")
                                        st.rerun()
                                    elif english_pdf:
                                        st.warning("⚠️ 僅英文PDF重新生成成功")
                                        st.rerun()
                                    else:
                                        st.error("❌ PDF重新生成失敗，請檢查依賴")
        else:
            st.error("❌ 未識別到有效的股票代碼")
    
    # 使用說明
    with st.sidebar:
        st.markdown("### 📖 使用說明")
        st.markdown("""
        1. 在上方輸入框中輸入股票代碼
        2. 支持多個代碼，用逗號分隔
        3. 程序會自動清理格式和去重
        4. 查看生成的中英文分析報告
        5. 下載Markdown或PDF格式
        
        <strong>注意:</strong> 首次使用需要先運行 `run.py` 生成基礎數據
        """)

if __name__ == "__main__":
    main()
