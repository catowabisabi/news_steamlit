"""
安裝必要的系統依賴
"""
import subprocess
import sys
import platform

def install_wkhtmltopdf():
    """安裝wkhtmltopdf系統依賴"""
    system = platform.system().lower()
    
    print("🔧 正在安裝PDF生成依賴...")
    
    try:
        if system == "windows":
            print("📋 Windows系統檢測到")
            print("請手動下載並安裝 wkhtmltopdf:")
            print("https://wkhtmltopdf.org/downloads.html")
            print("選擇 Windows (64-bit) 版本")
            
        elif system == "darwin":  # macOS
            print("🍎 macOS系統檢測到")
            subprocess.run(["brew", "install", "wkhtmltopdf"], check=True)
            print("✅ wkhtmltopdf 安裝完成")
            
        elif system == "linux":
            print("🐧 Linux系統檢測到")
            # 嘗試不同的包管理器
            try:
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "wkhtmltopdf"], check=True)
            except:
                try:
                    subprocess.run(["sudo", "yum", "install", "-y", "wkhtmltopdf"], check=True)
                except:
                    subprocess.run(["sudo", "dnf", "install", "-y", "wkhtmltopdf"], check=True)
            print("✅ wkhtmltopdf 安裝完成")
            
        else:
            print(f"❌ 不支持的系統: {system}")
            return False
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安裝失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 安裝過程中出錯: {e}")
        return False

def install_python_packages():
    """安裝Python包"""
    print("📦 正在安裝Python依賴...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python包安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Python包安裝失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 開始安裝依賴...")
    
    # 安裝Python包
    if not install_python_packages():
        sys.exit(1)
    
    # 安裝系統依賴
    if not install_wkhtmltopdf():
        print("⚠️ PDF功能可能無法正常工作")
    
    print("🎉 安裝完成!")
    print("\n📋 使用說明:")
    print("1. 運行 Streamlit 應用: streamlit run run_streamlit.py")
    print("2. 處理單個股票: python process_stock.py AAPL")
    print("3. 處理多個股票: python run.py")
