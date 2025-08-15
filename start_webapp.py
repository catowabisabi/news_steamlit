"""
啟動腳本：啟動Streamlit Web應用
"""
import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """檢查必要的依賴"""
    try:
        import streamlit
        import openai
        import pymongo
        print("✅ 核心依賴檢查通過")
        return True
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("💡 請運行: python install_requirements.py")
        return False

def check_env_file():
    """檢查環境變量文件"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ 未找到 .env 文件")
        print("💡 請創建 .env 文件並設置以下變量:")
        print("CHATGPT_API_KEY=your_openai_api_key")
        print("DEEPSEEK_API_KEY=your_deepseek_api_key") 
        print("MONGODB_URI=your_mongodb_connection_string")
        return False
    else:
        print("✅ .env 文件存在")
        return True

def start_streamlit():
    """啟動Streamlit應用"""
    try:
        print("🚀 啟動 Streamlit 應用...")
        print("🌐 Web應用將在瀏覽器中自動打開")
        print("📱 默認地址: http://localhost:8501")
        print("⏹️ 按 Ctrl+C 停止應用")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "run_streamlit.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 應用已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

def main():
    print("📊 股票分析報告生成器")
    print("=" * 50)
    
    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)
    
    # 檢查環境變量
    check_env_file()
    
    # 啟動應用
    start_streamlit()

if __name__ == "__main__":
    main()
