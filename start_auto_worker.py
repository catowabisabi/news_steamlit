#!/usr/bin/env python
"""
自動化Worker啟動腳本
用於啟動背景Worker，自動處理股票分析報告生成

使用方法:
    python start_auto_worker.py [options]

選項:
    --log-level DEBUG|INFO|WARNING|ERROR    設置日誌級別 (默認: INFO)
    --test-run                             執行一次測試運行然後退出
    --help                                顯示此幫助信息

範例:
    python start_auto_worker.py                    # 正常啟動
    python start_auto_worker.py --test-run         # 測試運行
    python start_auto_worker.py --log-level DEBUG  # 詳細日誌
"""

import sys
import argparse
import logging
from run_streamlit_auto import AutoWorker

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        description="自動化股票分析Worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python start_auto_worker.py                    # 正常啟動Worker
  python start_auto_worker.py --test-run         # 執行一次測試然後退出
  python start_auto_worker.py --log-level DEBUG  # 啟用詳細日誌
        """
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='設置日誌級別 (默認: INFO)'
    )
    
    parser.add_argument(
        '--test-run',
        action='store_true',
        help='執行一次測試運行然後退出'
    )
    
    return parser.parse_args()

def main():
    """主函數"""
    # 解析參數
    args = parse_arguments()
    
    # 設置日誌級別
    log_level = getattr(logging, args.log_level.upper())
    
    print("🤖 自動化股票分析Worker")
    print("=" * 50)
    print(f"📊 日誌級別: {args.log_level}")
    
    if args.test_run:
        print("🧪 測試模式: 執行一次然後退出")
    else:
        print("🔄 持續運行模式: 每30分鐘執行一次")
    
    print("=" * 50)
    
    try:
        # 創建Worker
        worker = AutoWorker(log_level=log_level)
        
        if args.test_run:
            # 測試模式：只執行一次
            print("🧪 開始測試運行...")
            worker.run_once()
            print("✅ 測試運行完成")
            worker.print_stats()
        else:
            # 正常模式：持續運行
            print("🚀 啟動Worker...")
            print("💡 按 Ctrl+C 停止")
            worker.start()
            
    except KeyboardInterrupt:
        print("\n⌨️ 用戶中斷")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)
    finally:
        print("👋 程序結束")

if __name__ == "__main__":
    main()
