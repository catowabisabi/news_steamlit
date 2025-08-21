"""
自動化Worker測試腳本
用於測試自動化Worker的基本功能
"""

import logging
from run_streamlit_auto import AutoWorker

def test_worker():
    """測試Worker基本功能"""
    print("🧪 測試自動化Worker...")
    print("=" * 50)
    
    try:
        # 創建Worker實例
        worker = AutoWorker(log_level=logging.INFO)
        
        # 測試連接
        print("🔌 測試連接...")
        if worker.check_connections():
            print("✅ 連接測試通過")
        else:
            print("❌ 連接測試失敗")
            return False
        
        # 測試獲取symbols
        print("\n📊 測試獲取symbols...")
        symbols = worker.get_today_symbols()
        if symbols:
            print(f"✅ 找到 {len(symbols)} 個symbols: {', '.join(symbols[:5])}")
            if len(symbols) > 5:
                print(f"   ... 還有 {len(symbols) - 5} 個symbols")
        else:
            print("⚠️ 沒有找到symbols")
        
        # 測試檢查新symbols
        print("\n🆕 測試檢查新symbols...")
        new_symbols = worker.check_new_symbols()
        if new_symbols:
            print(f"✅ 找到 {len(new_symbols)} 個新symbols: {', '.join(new_symbols[:3])}")
        else:
            print("ℹ️ 沒有新symbols需要處理")
        
        # 運行統計
        print("\n📊 測試統計功能...")
        worker.print_stats()
        
        print("\n🎉 所有測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    success = test_worker()
    if success:
        print("\n✅ Worker準備就緒，可以開始使用！")
        print("\n使用方法:")
        print("  python start_auto_worker.py --test-run  # 執行一次測試")
        print("  python start_auto_worker.py            # 啟動持續運行")
    else:
        print("\n❌ Worker測試失敗，請檢查配置")
