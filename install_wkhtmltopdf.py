"""
自動安裝 wkhtmltopdf 的腳本
"""
import subprocess
import sys
import platform
import os
from pathlib import Path

def install_wkhtmltopdf_windows():
    """Windows系統安裝指南"""
    print("🖥️ Windows系統檢測到")
    print("\n📋 請按照以下步驟安裝 wkhtmltopdf:")
    print("1. 打開瀏覽器訪問: https://wkhtmltopdf.org/downloads.html")
    print("2. 下載 'Windows (MSVC 2015) 64-bit' 版本")
    print("3. 運行下載的 .exe 文件並安裝")
    print("4. 安裝完成後重啟終端")
    
    # 檢查常見安裝路徑
    common_paths = [
        "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe",
        "C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe",
        "C:\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
    ]
    
    print("\n🔍 檢查常見安裝路徑...")
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ 找到 wkhtmltopdf: {path}")
            return path
    
    print("❌ 未找到 wkhtmltopdf，請手動安裝")
    return None

def install_wkhtmltopdf_macos():
    """macOS系統安裝"""
    print("🍎 macOS系統檢測到")
    try:
        print("📦 正在使用 Homebrew 安裝...")
        subprocess.run(["brew", "install", "wkhtmltopdf"], check=True)
        print("✅ wkhtmltopdf 安裝成功!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Homebrew 安裝失敗")
        print("💡 請手動安裝:")
        print("1. 安裝 Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. 運行: brew install wkhtmltopdf")
        return False
    except FileNotFoundError:
        print("❌ 未找到 Homebrew")
        print("💡 請先安裝 Homebrew 或手動下載 wkhtmltopdf")
        return False

def install_wkhtmltopdf_linux():
    """Linux系統安裝"""
    print("🐧 Linux系統檢測到")
    
    # 嘗試不同的包管理器
    commands = [
        ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "wkhtmltopdf"],
        ["sudo", "yum", "install", "-y", "wkhtmltopdf"],
        ["sudo", "dnf", "install", "-y", "wkhtmltopdf"],
        ["sudo", "pacman", "-S", "wkhtmltopdf"]
    ]
    
    for cmd in commands:
        try:
            print(f"📦 嘗試: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            print("✅ wkhtmltopdf 安裝成功!")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("❌ 自動安裝失敗")
    print("💡 請手動安裝:")
    print("Ubuntu/Debian: sudo apt-get install wkhtmltopdf")
    print("CentOS/RHEL: sudo yum install wkhtmltopdf")
    print("Fedora: sudo dnf install wkhtmltopdf")
    print("Arch: sudo pacman -S wkhtmltopdf")
    return False

def check_wkhtmltopdf():
    """檢查 wkhtmltopdf 是否已安裝"""
    try:
        result = subprocess.run(["wkhtmltopdf", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ wkhtmltopdf 已安裝: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ wkhtmltopdf 未安裝或不在PATH中")
        return False

def create_alternative_pdf_solution():
    """創建替代PDF解決方案"""
    print("\n💡 創建無需wkhtmltopdf的替代方案...")
    
    alternative_code = '''
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
'''
    
    with open("alternative_pdf.py", "w", encoding="utf-8") as f:
        f.write(alternative_code)
    
    print("✅ 已創建 alternative_pdf.py")
    print("💡 運行: pip install reportlab")

def main():
    print("🔧 wkhtmltopdf 安裝工具")
    print("=" * 50)
    
    # 檢查當前狀態
    if check_wkhtmltopdf():
        print("🎉 wkhtmltopdf 已正確安裝!")
        return
    
    # 根據系統類型安裝
    system = platform.system().lower()
    
    if system == "windows":
        install_wkhtmltopdf_windows()
    elif system == "darwin":  # macOS
        install_wkhtmltopdf_macos()
    elif system == "linux":
        install_wkhtmltopdf_linux()
    else:
        print(f"❌ 不支持的系統: {system}")
    
    # 創建替代方案
    create_alternative_pdf_solution()
    
    print("\n📋 安裝完成後:")
    print("1. 重啟終端")
    print("2. 運行: wkhtmltopdf --version")
    print("3. 重新運行 Streamlit 應用")

if __name__ == "__main__":
    main()
