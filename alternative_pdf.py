
"""
替代PDF生成方案 - 使用報表庫
"""
def create_simple_pdf_report(symbol: str, data: dict, output_path: str):
    """
    使用 reportlab 創建簡單PDF報告
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        # 創建PDF文檔
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # 添加標題
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # 居中
        )
        
        story.append(Paragraph(f"{symbol} 股票分析報告", title_style))
        story.append(Spacer(1, 20))
        
        # 添加內容
        if data.get('analysis'):
            analysis = data['analysis'].get('data', {}) if isinstance(data['analysis'], dict) else data['analysis']
            if isinstance(analysis, dict):
                story.append(Paragraph("基本面分析", styles['Heading2']))
                story.append(Paragraph(f"公司: {analysis.get('company', 'N/A')}", styles['Normal']))
                story.append(Paragraph(f"股票代碼: {analysis.get('ticker', 'N/A')}", styles['Normal']))
        
        # 生成PDF
        doc.build(story)
        return True
        
    except ImportError:
        print("需要安裝: pip install reportlab")
        return False
    except Exception as e:
        print(f"PDF生成失敗: {e}")
        return False

# 使用示例:
# create_simple_pdf_report("AAPL", data, "report.pdf")
