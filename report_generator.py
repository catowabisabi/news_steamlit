"""
股票報告生成器
用於自動化背景Worker的報告生成功能

直接使用Streamlit應用中的報告生成邏輯，確保完全一致
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

from file_manager import FileManager


class ReportGenerator:
    """
    股票報告生成器類別
    負責生成Markdown和PDF格式的股票分析報告
    
    直接使用Streamlit應用中的方法，確保文件結構和內容完全一致
    """
    
    def __init__(self):
        self.file_manager = FileManager()
        self.today_str = datetime.now().strftime('%Y-%m-%d')
        self.logger = logging.getLogger("ReportGenerator")
    
    def load_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        載入股票的所有相關數據
        
        Args:
            symbol: 股票代碼
            
        Returns:
            Dict: 包含所有股票數據的字典
        """
        data = {}
        
        # 數據類型列表
        data_types = [
            'news', 'fundamentals', 'desc_en', 'desc_cn', 
            'news_cn', 'analysis', 'news_en', 'analysis_en'
        ]
        
        for data_type in data_types:
            try:
                loaded_data = self.file_manager.load_data(symbol, data_type, self.today_str)
                if loaded_data:
                    data[data_type] = loaded_data
                    self.logger.debug(f"✅ 成功載入 {symbol} 的 {data_type} 數據")
                else:
                    self.logger.warning(f"⚠️ 未找到 {symbol} 的 {data_type} 數據")
            except Exception as e:
                self.logger.error(f"❌ 載入 {symbol} 的 {data_type} 數據失敗: {e}")
        
        return data
    
    def generate_chinese_report_content(self, symbol: str, data: Dict[str, Any]) -> str:
        """
        生成中文報告內容（與Streamlit應用完全一致）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: Markdown格式的報告內容
        """
        try:
            # 使用與Streamlit應用完全相同的邏輯
            md_content = f"""# 📊 {symbol} 股票分析報告

<strong>生成日期:</strong> {self.today_str}

---

## 🏢 公司簡介

"""
            
            # 公司描述 - 中文（與Streamlit完全一致）
            if data.get('desc_cn'):
                desc_cn_data = data['desc_cn'].get('data', {}) if isinstance(data['desc_cn'], dict) else data['desc_cn']
                if isinstance(desc_cn_data, dict) and 'desc_cn' in desc_cn_data:
                    desc_text = desc_cn_data['desc_cn']
                    if isinstance(desc_text, str) and len(desc_text.strip()) > 0:
                        md_content += f"<strong>公司描述:</strong> {desc_text}\n\n"
            
            # 基本面數據（與Streamlit完全一致）
            if data.get('fundamentals'):
                fundamentals = data['fundamentals']
                md_content += "## 📊 基本面數據\n\n"
                
                if fundamentals.get('current_price'):
                    md_content += f"<strong>目前股價:</strong> ${fundamentals['current_price']}\n"
                if fundamentals.get('market_cap'):
                    md_content += f"<strong>市值:</strong> {fundamentals['market_cap']}\n"
                if fundamentals.get('pe_ratio'):
                    md_content += f"<strong>本益比:</strong> {fundamentals['pe_ratio']}\n"
                if fundamentals.get('volume'):
                    md_content += f"<strong>交易量:</strong> {fundamentals['volume']}\n"
                
                md_content += "\n"
            
            # 最新新聞（與Streamlit完全一致）
            if data.get('news_cn'):
                news_cn_data = data['news_cn'].get('data', {}) if isinstance(data['news_cn'], dict) else data['news_cn']
                md_content += "## 📰 最新新聞\n\n"
                
                if isinstance(news_cn_data, dict) and 'articles' in news_cn_data:
                    articles = news_cn_data['articles']
                    for i, article in enumerate(articles[:5], 1):
                        title = article.get('title', '無標題')
                        summary = article.get('summary', '')
                        md_content += f"### {i}. {title}\n"
                        if summary:
                            md_content += f"{summary}\n\n"
                        else:
                            md_content += "\n"
                else:
                    md_content += "暫無相關新聞\n\n"
            
            # 分析報告（與Streamlit完全一致）
            if data.get('analysis'):
                analysis_data = data['analysis'].get('data', {}) if isinstance(data['analysis'], dict) else data['analysis']
                md_content += "## 💡 投資分析\n\n"
                
                if isinstance(analysis_data, dict):
                    # 投資建議
                    if 'investment_recommendation' in analysis_data:
                        rec = analysis_data['investment_recommendation']
                        md_content += "### 🎯 投資建議\n\n"
                        if isinstance(rec, dict):
                            md_content += f"<strong>評級:</strong> {rec.get('rating', 'N/A')}\n"
                            md_content += f"<strong>目標價:</strong> {rec.get('target_price', 'N/A')}\n"
                            md_content += f"<strong>理由:</strong> {rec.get('rationale', 'N/A')}\n\n"
                    
                    # 風險評估
                    if 'risk_assessment' in analysis_data:
                        risk = analysis_data['risk_assessment']
                        md_content += "### ⚠️ 風險評估\n\n"
                        if isinstance(risk, dict):
                            md_content += f"<strong>風險等級:</strong> {risk.get('risk_level', 'N/A')}\n"
                            md_content += f"<strong>主要風險:</strong> {risk.get('main_risks', 'N/A')}\n\n"
                    
                    # 關鍵指標
                    if 'key_metrics' in analysis_data:
                        metrics = analysis_data['key_metrics']
                        md_content += "### 📊 關鍵指標\n\n"
                        if isinstance(metrics, dict):
                            for key, value in metrics.items():
                                md_content += f"<strong>{key}:</strong> {value}\n"
                            md_content += "\n"
                    
                    # 財務健康狀況
                    if 'financial_health' in analysis_data:
                        health = analysis_data['financial_health']
                        md_content += "### 💰 財務健康狀況\n\n"
                        if isinstance(health, dict):
                            md_content += f"<strong>流動性:</strong> {health.get('liquidity', 'N/A')}\n"
                            md_content += f"<strong>債務狀況:</strong> {health.get('debt_status', 'N/A')}\n\n"
                    
                    # 交易建議
                    if 'trading_recommendation' in analysis_data:
                        trading = analysis_data['trading_recommendation']
                        md_content += "### 💡 交易建議\n\n"
                        if isinstance(trading, dict):
                            md_content += f"<strong>傾向:</strong> {trading.get('bias', 'N/A')}\n"
                            md_content += f"<strong>建議:</strong> {trading.get('suggestion', 'N/A')}\n"
                            if 'catalysts' in trading and isinstance(trading['catalysts'], list):
                                md_content += "<strong>關鍵催化劑:</strong>\n"
                                for catalyst in trading['catalysts']:
                                    md_content += f"- {catalyst}\n"
                                md_content += "\n"
                else:
                    md_content += "❌ 無分析數據\n\n"
            
            # 免責聲明（與Streamlit完全一致）
            md_content += """---

*本報告由AI自動生成，僅供參考，不構成投資建議。投資有風險，請謹慎決策。*
"""
            
            return md_content
            
        except Exception as e:
            self.logger.error(f"❌ 生成中文報告內容失敗: {e}")
            return f"# {symbol} 股票分析報告\n\n報告生成失敗: {str(e)}"
    
    def generate_english_report_content(self, symbol: str, data: Dict[str, Any]) -> str:
        """
        生成英文報告內容（Markdown格式）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            str: Markdown格式的英文報告內容
        """
        try:
            # 獲取英文數據
            analysis_en = data.get('analysis_en', {})
            news_en = data.get('news_en', {})
            desc_en = data.get('desc_en', {})
            fundamentals = data.get('fundamentals', {})
            
            # 處理嵌套的數據結構
            if isinstance(analysis_en, dict) and 'data' in analysis_en:
                analysis_en = analysis_en['data']
            if isinstance(news_en, dict) and 'data' in news_en:
                news_en = news_en['data']
            if isinstance(desc_en, dict) and 'desc_en' in desc_en:
                desc_en = desc_en['desc_en']
            
            # 構建英文報告內容
            content = f"""# {symbol} Stock Analysis Report

## 📊 Report Date
{self.today_str}

---

"""
            
            # Company Description
            if desc_en:
                content += f"""## 🏢 Company Overview

{desc_en}

---

"""
            
            # Fundamentals
            if fundamentals:
                content += """## 📈 Fundamental Data

"""
                if fundamentals.get('current_price'):
                    content += f"**Current Price**: ${fundamentals.get('current_price', 'N/A')}\n\n"
                if fundamentals.get('market_cap'):
                    content += f"**Market Cap**: {fundamentals.get('market_cap', 'N/A')}\n\n"
                if fundamentals.get('pe_ratio'):
                    content += f"**P/E Ratio**: {fundamentals.get('pe_ratio', 'N/A')}\n\n"
                
                content += "---\n\n"
            
            # Latest News
            if news_en and isinstance(news_en, dict):
                content += """## 📰 Latest News

"""
                articles = news_en.get('articles', [])
                if articles:
                    for i, article in enumerate(articles[:5], 1):
                        title = article.get('title', 'No Title')
                        summary = article.get('summary', 'No Summary')
                        content += f"### {i}. {title}\n\n{summary}\n\n"
                else:
                    content += "No relevant news available\n\n"
                
                content += "---\n\n"
            
            # Investment Analysis
            if analysis_en and isinstance(analysis_en, dict):
                content += """## 💡 Investment Analysis

"""
                
                # Investment Recommendation
                if analysis_en.get('investment_recommendation'):
                    rec = analysis_en['investment_recommendation']
                    content += f"""### 🎯 Investment Recommendation
**Rating**: {rec.get('rating', 'N/A')}
**Target Price**: ${rec.get('target_price', 'N/A')}
**Rationale**: {rec.get('rationale', 'None')}

"""
                
                # Risk Assessment
                if analysis_en.get('risk_assessment'):
                    risk = analysis_en['risk_assessment']
                    content += f"""### ⚠️ Risk Assessment
**Risk Level**: {risk.get('risk_level', 'N/A')}
**Main Risks**: {risk.get('main_risks', 'None')}

"""
                
                # Key Metrics
                if analysis_en.get('key_metrics'):
                    metrics = analysis_en['key_metrics']
                    content += """### 📊 Key Metrics
"""
                    for key, value in metrics.items():
                        content += f"- **{key}**: {value}\n"
                    content += "\n"
                
                content += "---\n\n"
            
            # Disclaimer
            content += """## ⚠️ Disclaimer

This report is for informational purposes only and does not constitute investment advice. Investing involves risks, and you should conduct your own research and consult with qualified financial advisors before making investment decisions.

---

*Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ 生成英文報告內容失敗: {e}")
            return f"# {symbol} Stock Analysis Report\n\nReport generation failed: {str(e)}"
    
    def save_markdown_report(self, symbol: str, md_content: str) -> str:
        """
        保存Markdown報告到文件（與Streamlit應用完全一致）
        
        Args:
            symbol: 股票代碼
            md_content: Markdown內容
            
        Returns:
            str: 文件路徑
        """
        try:
            # 使用與Streamlit完全相同的邏輯
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            
            md_file_path = data_path / f"{symbol}_report_{self.today_str}.md"
            
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.info(f"✅ Markdown報告已保存: {md_file_path}")
            return str(md_file_path)
            
        except Exception as e:
            self.logger.error(f"❌ 保存Markdown報告失敗: {e}")
            return None
    
    def generate_chinese_pdf_report_html(self, symbol: str, data: dict) -> Optional[str]:
        """
        生成中文PDF報告（與Streamlit應用完全一致的方法名和路徑）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            Optional[str]: PDF文件路徑，失敗則返回None
        """
        try:
            # 使用與Streamlit完全相同的路徑邏輯
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_chinese_{self.today_str}.pdf"
            
            # 生成中文報告內容
            chinese_content = self.generate_chinese_report_content(symbol, data)
            
            # 嘗試使用pdfkit（與Streamlit一致）
            try:
                import pdfkit
                
                # 清理並轉換為HTML
                cleaned_content = self._clean_markdown_content(chinese_content)
                
                # 創建完整的HTML文檔
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{symbol} 股票分析報告</title>
                    <style>
                        body {{
                            font-family: 'Microsoft YaHei', '微軟雅黑', SimSun, serif;
                            line-height: 1.6;
                            margin: 20px;
                            color: #333;
                        }}
                        h1, h2, h3 {{
                            color: #2c3e50;
                            margin-top: 20px;
                            margin-bottom: 10px;
                        }}
                        h1 {{ font-size: 24px; text-align: center; }}
                        h2 {{ font-size: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                        h3 {{ font-size: 16px; color: #e74c3c; }}
                        strong {{ color: #2980b9; }}
                        .date {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; }}
                        .section {{ margin-bottom: 25px; }}
                        .disclaimer {{ 
                            background-color: #f8f9fa; 
                            padding: 15px; 
                            border-left: 4px solid #ffc107; 
                            margin-top: 30px; 
                            font-style: italic; 
                        }}
                    </style>
                </head>
                <body>
                    {cleaned_content}
                </body>
                </html>
                """
                
                # 設置PDF選項
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': None
                }
                
                # 生成PDF
                pdfkit.from_string(html_content, str(pdf_path), options=options)
                self.logger.info(f"✅ 中文PDF報告已生成: {pdf_path}")
                return str(pdf_path)
                
            except ImportError:
                self.logger.warning("⚠️ pdfkit未安裝，嘗試使用reportlab")
                return self._generate_pdf_with_reportlab(symbol, chinese_content, "chinese")
            except Exception as e:
                self.logger.warning(f"⚠️ pdfkit生成失敗，嘗試使用reportlab: {e}")
                return self._generate_pdf_with_reportlab(symbol, chinese_content, "chinese")
                
        except Exception as e:
            self.logger.error(f"❌ 生成中文PDF報告失敗: {e}")
            return None
    
    def generate_english_pdf_report_html(self, symbol: str, data: dict) -> Optional[str]:
        """
        生成英文PDF報告（與Streamlit應用完全一致的方法名和路徑）
        
        Args:
            symbol: 股票代碼
            data: 股票數據
            
        Returns:
            Optional[str]: PDF文件路徑，失敗則返回None
        """
        try:
            # 使用與Streamlit完全相同的路徑邏輯
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            pdf_path = data_path / f"{symbol}_report_english_{self.today_str}.pdf"
            
            # 生成英文報告內容
            english_content = self.generate_english_report_content(symbol, data)
            
            # 嘗試使用pdfkit（與Streamlit一致）
            try:
                import pdfkit
                
                # 清理並轉換為HTML
                cleaned_content = self._clean_markdown_content(english_content)
                
                # 創建完整的HTML文檔
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{symbol} Stock Analysis Report</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            margin: 20px;
                            color: #333;
                        }}
                        h1, h2, h3 {{
                            color: #2c3e50;
                            margin-top: 20px;
                            margin-bottom: 10px;
                        }}
                        h1 {{ font-size: 24px; text-align: center; }}
                        h2 {{ font-size: 20px; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                        h3 {{ font-size: 16px; color: #e74c3c; }}
                        strong {{ color: #2980b9; }}
                        .date {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; }}
                        .section {{ margin-bottom: 25px; }}
                        .disclaimer {{ 
                            background-color: #f8f9fa; 
                            padding: 15px; 
                            border-left: 4px solid #ffc107; 
                            margin-top: 30px; 
                            font-style: italic; 
                        }}
                    </style>
                </head>
                <body>
                    {cleaned_content}
                </body>
                </html>
                """
                
                # 設置PDF選項
                options = {
                    'page-size': 'A4',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': "UTF-8",
                    'no-outline': None,
                    'enable-local-file-access': None
                }
                
                # 生成PDF
                pdfkit.from_string(html_content, str(pdf_path), options=options)
                self.logger.info(f"✅ 英文PDF報告已生成: {pdf_path}")
                return str(pdf_path)
                
            except ImportError:
                self.logger.warning("⚠️ pdfkit未安裝，嘗試使用reportlab")
                return self._generate_pdf_with_reportlab(symbol, english_content, "english")
            except Exception as e:
                self.logger.warning(f"⚠️ pdfkit生成失敗，嘗試使用reportlab: {e}")
                return self._generate_pdf_with_reportlab(symbol, english_content, "english")
                
        except Exception as e:
            self.logger.error(f"❌ 生成英文PDF報告失敗: {e}")
            return None
    
    def _clean_markdown_content(self, content: str) -> str:
        """
        清理Markdown內容為HTML（與Streamlit一致）
        """
        import re
        
        # 簡單的Markdown到HTML轉換
        html_content = content
        
        # 轉換標題
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        
        # 轉換粗體
        html_content = re.sub(r'<strong>(.+?)</strong>', r'<strong>\1</strong>', html_content)
        
        # 轉換段落
        html_content = re.sub(r'\n\n', '</p><p>', html_content)
        html_content = '<p>' + html_content + '</p>'
        
        # 清理空段落
        html_content = re.sub(r'<p></p>', '', html_content)
        html_content = re.sub(r'<p>\s*</p>', '', html_content)
        
        return html_content
    
    def _generate_pdf_with_reportlab(self, symbol: str, content: str, language: str) -> Optional[str]:
        """
        使用reportlab生成PDF的備用方法
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 設置字體
            try:
                if language == "chinese" and os.name == 'nt':
                    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
                    font_name = 'SimHei'
                else:
                    font_name = 'Helvetica'
            except:
                font_name = 'Helvetica'
            
            # 設置PDF路徑
            data_path = Path(self.file_manager._get_data_path(symbol, self.today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            
            if language == "chinese":
                pdf_filename = f"{symbol}_report_chinese_{self.today_str}.pdf"
            else:
                pdf_filename = f"{symbol}_report_english_{self.today_str}.pdf"
            
            pdf_path = data_path / pdf_filename
            
            # 創建PDF文檔
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=0.8*inch, bottomMargin=0.8*inch)
            story = []
            styles = getSampleStyleSheet()
            
            # 自定義樣式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=20,
                alignment=1,
                fontName=font_name
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName=font_name
            )
            
            # 簡化的內容處理
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    if line.startswith('# '):
                        story.append(Paragraph(line[2:], title_style))
                    else:
                        story.append(Paragraph(line, normal_style))
                else:
                    story.append(Spacer(1, 6))
            
            # 生成PDF
            doc.build(story)
            self.logger.info(f"✅ {language.title()} PDF報告已生成（reportlab）: {pdf_path}")
            return str(pdf_path)
            
        except ImportError:
            self.logger.error("❌ 需要安裝reportlab: pip install reportlab")
            return None
        except Exception as e:
            self.logger.error(f"❌ reportlab生成PDF失敗: {e}")
            return None
    
    def generate_complete_report(self, symbol: str) -> Dict[str, Any]:
        """
        生成完整的股票報告（與Streamlit應用完全一致的流程）
        
        Args:
            symbol: 股票代碼
            
        Returns:
            Dict: 生成結果
        """
        result = {
            "success": False,
            "symbol": symbol,
            "generated_files": [],
            "errors": []
        }
        
        try:
            self.logger.info(f"📝 開始生成 {symbol} 完整報告...")
            
            # 載入股票數據
            data = self.load_stock_data(symbol)
            
            if not data:
                result["errors"].append("無法載入股票數據")
                return result
            
            # 檢查必要數據（與Streamlit一致）
            required_data = ['news_cn', 'analysis', 'news_en', 'analysis_en']
            missing_data = [dt for dt in required_data if not data.get(dt)]
            
            if missing_data:
                result["errors"].append(f"缺少必要數據: {', '.join(missing_data)}")
                return result
            
            # 生成Markdown報告（使用中文版本作為主報告，與Streamlit一致）
            md_content = self.generate_chinese_report_content(symbol, data)
            
            # 保存Markdown文件
            md_path = self.save_markdown_report(symbol, md_content)
            
            if md_path:
                result["generated_files"].append(md_path)
                self.logger.info(f"✅ {symbol} Markdown報告生成成功")
            else:
                result["errors"].append("Markdown報告生成失敗")
                return result
            
            # 生成中英文分離PDF（與Streamlit一致）
            try:
                # 生成中文PDF（使用HTML轉換）
                chinese_pdf = self.generate_chinese_pdf_report_html(symbol, data)
                if chinese_pdf:
                    result["generated_files"].append(chinese_pdf)
                    self.logger.info(f"✅ {symbol} 中文PDF報告生成成功")
                
                # 生成英文PDF（使用HTML轉換）
                english_pdf = self.generate_english_pdf_report_html(symbol, data)
                if english_pdf:
                    result["generated_files"].append(english_pdf)
                    self.logger.info(f"✅ {symbol} 英文PDF報告生成成功")
                
                # 報告生成結果（與Streamlit一致的邏輯）
                if chinese_pdf and english_pdf:
                    self.logger.info("✅ 中英文PDF報告生成完成!")
                elif chinese_pdf:
                    self.logger.warning("⚠️ 僅中文PDF生成成功")
                elif english_pdf:
                    self.logger.warning("⚠️ 僅英文PDF生成成功")
                else:
                    self.logger.warning("⚠️ PDF生成失敗，但Markdown報告可用")
                    result["errors"].append("PDF生成失敗")
                        
            except Exception as e:
                self.logger.warning(f"⚠️ PDF生成過程出錯: {e}")
                result["errors"].append(f"PDF生成失敗: {e}")
            
            # 成功條件：至少有Markdown報告
            if md_path:
                result["success"] = True
                self.logger.info(f"🎉 {symbol} 報告生成完成，共生成 {len(result['generated_files'])} 個文件")
            else:
                result["errors"].append("沒有成功生成任何報告文件")
            
            return result
            
        except Exception as e:
            error_msg = f"生成報告過程中發生異常: {str(e)}"
            result["errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
            return result


# 獨立函數供外部調用
def generate_stock_report(symbol: str) -> Dict[str, Any]:
    """
    生成股票報告的便捷函數
    
    Args:
        symbol: 股票代碼
        
    Returns:
        Dict: 生成結果
    """
    generator = ReportGenerator()
    return generator.generate_complete_report(symbol)


if __name__ == "__main__":
    # 測試用例
    import sys
    import logging
    
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) != 2:
        print("使用方法: python report_generator.py <SYMBOL>")
        sys.exit(1)
    
    symbol = sys.argv[1]
    result = generate_stock_report(symbol)
    
    print(f"\n報告生成結果: {symbol}")
    print(f"成功: {result['success']}")
    
    if result['generated_files']:
        print("生成的文件:")
        for file_path in result['generated_files']:
            print(f"  - {file_path}")
    
    if result['errors']:
        print("錯誤:")
        for error in result['errors']:
            print(f"  - {error}")
