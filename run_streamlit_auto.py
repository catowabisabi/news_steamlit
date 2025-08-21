"""
自動化背景Worker：股票分析報告生成器
每半小時自動檢查MongoDB中的新symbols，並自動生成報告和IG POST

作者：AI Assistant
創建日期：2025-01-27
"""

import os
import time
import json
import logging
import schedule
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import traceback
from pathlib import Path
from typing import List, Dict, Set
import threading
import signal
import sys

# 導入自定義模組
from mongo_db import MongoHandler
from process_stock import process_single_stock
from ig_post import IgPostCreator
from file_manager import FileManager
from report_generator import ReportGenerator

class AutoWorker:
    """
    自動化背景Worker類別
    負責定期檢查新symbols並自動生成報告
    """
    
    def __init__(self, log_level=logging.INFO):
        """
        初始化自動化Worker
        
        Args:
            log_level: 日誌級別，默認為INFO
        """
        # 設置日誌
        self.setup_logging(log_level)
        
        # 初始化組件
        self.db_handler = MongoHandler()
        self.ig_creator = IgPostCreator()
        self.file_manager = FileManager()
        self.report_generator = ReportGenerator()
        
        # 運行狀態控制
        self.is_running = False
        self.stop_requested = False
        
        # 追蹤已處理的symbols（用於統計）
        self.processed_symbols = set()
        
        # 配置選項
        self.force_regenerate = False  # 是否強制重新生成已存在的報告
        
        # 工作統計
        self.stats = {
            "total_runs": 0,
            "successful_reports": 0,
            "failed_reports": 0,
            "ig_posts_created": 0,
            "last_run_time": None,
            "last_success_time": None,
            "errors": []
        }
        
        self.logger.info("🤖 AutoWorker初始化完成")
    
    def setup_logging(self, log_level):
        """設置日誌系統"""
        # 創建logs目錄如果不存在
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # 設置日誌格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 設置文件日誌
        log_file = logs_dir / f"auto_worker_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 配置logging
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger("AutoWorker")
    
    def check_connections(self) -> bool:
        """
        檢查所有必要的連接
        
        Returns:
            bool: 所有連接都正常返回True
        """
        try:
            # 檢查MongoDB連接
            if not self.db_handler.is_connected():
                self.logger.error("❌ MongoDB連接失敗")
                return False
            
            self.logger.info("✅ 所有連接檢查通過")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 連接檢查失敗: {e}")
            return False
    
    def get_today_symbols(self) -> List[str]:
        """
        從MongoDB獲取今天的所有symbols
        
        Returns:
            List[str]: 今天的symbols列表
        """
        try:
            ny_today_str = datetime.now(ZoneInfo("America/New_York")).strftime('%Y-%m-%d')
            
            # 從fundamentals_of_top_list_symbols集合中獲取今天的所有symbols
            docs = self.db_handler.find_doc(
                "fundamentals_of_top_list_symbols", 
                {"today_date": ny_today_str}
            )
            
            if not docs:
                self.logger.warning(f"⚠️ 今天({ny_today_str})沒有找到任何symbols")
                return []
            
            symbols = [doc.get("symbol", "").upper() for doc in docs if doc.get("symbol")]
            unique_symbols = list(set(symbols))  # 去重
            
            self.logger.info(f"📊 從MongoDB獲取到 {len(unique_symbols)} 個symbols: {', '.join(unique_symbols)}")
            return unique_symbols
            
        except Exception as e:
            self.logger.error(f"❌ 獲取symbols失敗: {e}")
            return []
    
    def check_new_symbols(self) -> List[str]:
        """
        檢查是否有新的symbols需要處理（使用與Streamlit完全相同的邏輯）
        
        Returns:
            List[str]: 需要處理的symbols列表
        """
        current_symbols = set(self.get_today_symbols())
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        symbols_to_process = []
        
        for symbol in current_symbols:
            # 使用與Streamlit完全相同的文件檢查邏輯
            data_path = Path(self.file_manager._get_data_path(symbol, today_str))
            md_file_path = data_path / f"{symbol}_report_{today_str}.md"
            chinese_pdf_path = data_path / f"{symbol}_report_chinese_{today_str}.pdf"
            english_pdf_path = data_path / f"{symbol}_report_english_{today_str}.pdf"
            ig_file_path = data_path / f"{symbol}_ig_post_{today_str}.txt"
            
            # 檢查是否需要處理
            needs_processing = False
            
            if self.force_regenerate:
                # 強制重新生成模式
                needs_processing = True
                self.logger.debug(f"🔄 {symbol}: 強制重新生成模式")
            else:
                # 與Streamlit相同：檢查報告文件是否存在
                if not (md_file_path.exists() and chinese_pdf_path.exists() and english_pdf_path.exists()):
                    needs_processing = True
                    self.logger.debug(f"📝 {symbol}: 缺少報告文件（MD: {md_file_path.exists()}, CN PDF: {chinese_pdf_path.exists()}, EN PDF: {english_pdf_path.exists()}）")
                
                # 另外檢查IG POST
                if not ig_file_path.exists():
                    needs_processing = True
                    self.logger.debug(f"📱 {symbol}: 缺少IG POST文件")
            
            if needs_processing:
                symbols_to_process.append(symbol)
                
                # 詳細日誌顯示缺少的文件
                missing_files = []
                if not md_file_path.exists():
                    missing_files.append("Markdown報告")
                if not chinese_pdf_path.exists():
                    missing_files.append("中文PDF")
                if not english_pdf_path.exists():
                    missing_files.append("英文PDF")
                if not ig_file_path.exists():
                    missing_files.append("IG POST")
                
                if missing_files and not self.force_regenerate:
                    self.logger.info(f"📋 {symbol} 缺少: {', '.join(missing_files)}")
        
        # 更新已處理列表（用於統計）
        for symbol in symbols_to_process:
            if symbol not in self.processed_symbols:
                self.processed_symbols.add(symbol)
        
        if symbols_to_process:
            self.logger.info(f"🆕 發現 {len(symbols_to_process)} 個需要處理的symbols: {', '.join(symbols_to_process)}")
        else:
            self.logger.info("✅ 所有symbols都已經有完整的報告和IG POST")
        
        return symbols_to_process
    
    def process_symbol_auto(self, symbol: str) -> Dict:
        """
        自動處理單個symbol（生成報告和IG POST）
        
        Args:
            symbol: 股票代碼
            
        Returns:
            Dict: 處理結果
        """
        result = {
            "symbol": symbol,
            "success": False,
            "report_generated": False,
            "ig_post_generated": False,
            "errors": []
        }
        
        try:
            self.logger.info(f"🔄 開始自動處理 {symbol}...")
            
            # 1. 首先處理股票數據（生成所有必要的數據文件）
            stock_result = process_single_stock(symbol, force_refresh=False)
            
            if not stock_result.get("success", False):
                result["errors"].extend(stock_result.get("errors", []))
                self.logger.error(f"❌ {symbol} 股票數據處理失敗")
                return result
            
            self.logger.info(f"✅ {symbol} 股票數據處理成功")
            
            # 2. 檢查是否需要生成報告
            today_str = datetime.now().strftime('%Y-%m-%d')
            data_path = Path(self.file_manager._get_data_path(symbol, today_str))
            md_file_path = data_path / f"{symbol}_report_{today_str}.md"
            
            # 如果報告文件不存在，生成報告
            if not md_file_path.exists():
                self.logger.info(f"📝 開始生成 {symbol} 報告...")
                report_result = self.generate_report(symbol)
                
                if report_result["success"]:
                    result["report_generated"] = True
                    self.logger.info(f"✅ {symbol} 報告生成成功")
                else:
                    result["errors"].extend(report_result.get("errors", []))
                    self.logger.error(f"❌ {symbol} 報告生成失敗")
                    return result
            else:
                result["report_generated"] = True
                self.logger.info(f"✅ {symbol} 報告已存在，跳過生成")
            
            # 3. 檢查是否需要生成IG POST
            ig_file_path = data_path / f"{symbol}_ig_post_{today_str}.txt"
            
            if not ig_file_path.exists():
                self.logger.info(f"📱 開始生成 {symbol} IG POST...")
                ig_result = self.generate_ig_post(symbol)
                
                if ig_result["success"]:
                    result["ig_post_generated"] = True
                    self.logger.info(f"✅ {symbol} IG POST生成成功")
                else:
                    result["errors"].extend(ig_result.get("errors", []))
                    self.logger.error(f"❌ {symbol} IG POST生成失敗")
            else:
                result["ig_post_generated"] = True
                self.logger.info(f"✅ {symbol} IG POST已存在，跳過生成")
            
            result["success"] = True
            self.logger.info(f"🎉 {symbol} 自動處理完成!")
            
        except Exception as e:
            error_msg = f"處理 {symbol} 時發生異常: {str(e)}"
            result["errors"].append(error_msg)
            self.logger.error(f"❌ {error_msg}")
            self.logger.debug(traceback.format_exc())
        
        return result
    
    def generate_report(self, symbol: str) -> Dict:
        """
        生成股票報告（調用報告生成器）
        
        Args:
            symbol: 股票代碼
            
        Returns:
            Dict: 生成結果
        """
        try:
            self.logger.info(f"📝 正在生成 {symbol} 報告...")
            
            # 調用報告生成器
            result = self.report_generator.generate_complete_report(symbol)
            
            if result["success"]:
                self.logger.info(f"✅ {symbol} 報告生成成功，生成了 {len(result['generated_files'])} 個文件")
                return {
                    "success": True,
                    "symbol": symbol,
                    "generated_files": result["generated_files"],
                    "message": f"{symbol} 報告生成成功"
                }
            else:
                self.logger.error(f"❌ {symbol} 報告生成失敗: {result['errors']}")
                return {
                    "success": False,
                    "symbol": symbol,
                    "errors": result["errors"]
                }
            
        except Exception as e:
            error_msg = f"報告生成失敗: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "symbol": symbol,
                "errors": [error_msg]
            }
    
    def generate_ig_post(self, symbol: str) -> Dict:
        """
        生成IG POST（與Streamlit應用完全一致）
        
        Args:
            symbol: 股票代碼
            
        Returns:
            Dict: 生成結果
        """
        try:
            self.logger.info(f"📱 開始生成 {symbol} IG POST...")
            
            # 載入股票數據（與Streamlit一致）
            data = self.report_generator.load_stock_data(symbol)
            
            if not data:
                return {
                    "success": False,
                    "symbol": symbol,
                    "errors": [f"無法載入 {symbol} 的股票數據"]
                }
            
            # 生成中文報告內容作為基礎（與Streamlit完全一致）
            report_content = self.report_generator.generate_chinese_report_content(symbol, data)
            
            # 使用IgPostCreator生成Instagram貼文（與Streamlit一致）
            ig_result = self.ig_creator.create_ig_post(symbol, report_content)
            
            if ig_result["success"]:
                # 保存IG POST到文件（與Streamlit一致的方式）
                filename = self.save_ig_post_streamlit_style(symbol, ig_result)
                
                return {
                    "success": True,
                    "symbol": symbol,
                    "filename": filename,
                    "message": f"{symbol} IG POST生成成功"
                }
            else:
                return {
                    "success": False,
                    "symbol": symbol,
                    "errors": [ig_result.get("error", "IG POST生成失敗")]
                }
                
        except Exception as e:
            return {
                "success": False,
                "symbol": symbol,
                "errors": [f"IG POST生成失敗: {str(e)}"]
            }
    
    def save_ig_post_streamlit_style(self, symbol: str, ig_result: dict) -> str:
        """
        保存Instagram貼文（與Streamlit應用完全一致的方式）
        
        Args:
            symbol: 股票代碼
            ig_result: IG POST結果
            
        Returns:
            str: 保存的文件路徑
        """
        try:
            # 使用與Streamlit完全相同的路徑和格式
            today_str = datetime.now().strftime('%Y-%m-%d')
            data_path = Path(self.file_manager._get_data_path(symbol, today_str))
            data_path.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名（與Streamlit一致）
            filename = data_path / f"{symbol}_ig_post_{today_str}.txt"
            
            # 保存內容（與Streamlit完全一致的格式）
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== INSTAGRAM POST ===\n\n")
                f.write(ig_result['formatted_post'])
                f.write(f"\n\n=== HASHTAGS ===\n\n")
                f.write(ig_result['hashtags'])
                f.write(f"\n\n=== RAW JSON ===\n\n")
                f.write(json.dumps(ig_result['raw_json'], ensure_ascii=False, indent=2))
            
            self.logger.info(f"✅ IG POST已保存: {filename}")
            return str(filename)
            
        except Exception as e:
            self.logger.error(f"❌ 保存IG POST失敗: {e}")
            raise Exception(f"保存Instagram貼文失敗: {str(e)}")
    
    def run_once(self):
        """
        執行一次完整的檢查和處理循環
        """
        self.logger.info("🔄 開始執行自動化任務...")
        self.stats["total_runs"] += 1
        self.stats["last_run_time"] = datetime.now().isoformat()
        
        try:
            # 檢查連接
            if not self.check_connections():
                self.logger.error("❌ 連接檢查失敗，跳過此次執行")
                return
            
            # 獲取新的symbols
            new_symbols = self.check_new_symbols()
            
            if not new_symbols:
                self.logger.info("✅ 沒有新的symbols需要處理")
                return
            
            # 處理每個新symbol
            successful_count = 0
            failed_count = 0
            
            for symbol in new_symbols:
                try:
                    result = self.process_symbol_auto(symbol)
                    
                    if result["success"]:
                        successful_count += 1
                        self.processed_symbols.add(symbol)
                        
                        if result["report_generated"]:
                            self.stats["successful_reports"] += 1
                        
                        if result["ig_post_generated"]:
                            self.stats["ig_posts_created"] += 1
                            
                        self.logger.info(f"✅ {symbol} 處理成功")
                    else:
                        failed_count += 1
                        self.stats["failed_reports"] += 1
                        
                        # 記錄錯誤
                        for error in result.get("errors", []):
                            self.stats["errors"].append({
                                "timestamp": datetime.now().isoformat(),
                                "symbol": symbol,
                                "error": error
                            })
                        
                        self.logger.error(f"❌ {symbol} 處理失敗: {result.get('errors', [])}")
                
                except Exception as e:
                    failed_count += 1
                    error_msg = f"處理 {symbol} 時發生異常: {str(e)}"
                    self.logger.error(error_msg)
                    self.stats["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol,
                        "error": error_msg
                    })
            
            # 更新統計
            if successful_count > 0:
                self.stats["last_success_time"] = datetime.now().isoformat()
            
            self.logger.info(f"📊 本次執行完成: 成功 {successful_count}, 失敗 {failed_count}")
            
        except Exception as e:
            self.logger.error(f"❌ 執行過程中發生異常: {str(e)}")
            self.logger.debug(traceback.format_exc())
    
    def print_stats(self):
        """打印運行統計"""
        self.logger.info("📊 === AutoWorker 運行統計 ===")
        self.logger.info(f"總運行次數: {self.stats['total_runs']}")
        self.logger.info(f"成功生成報告: {self.stats['successful_reports']}")
        self.logger.info(f"失敗次數: {self.stats['failed_reports']}")
        self.logger.info(f"IG POST生成: {self.stats['ig_posts_created']}")
        self.logger.info(f"上次運行時間: {self.stats['last_run_time']}")
        self.logger.info(f"上次成功時間: {self.stats['last_success_time']}")
        self.logger.info(f"已處理symbols: {len(self.processed_symbols)}")
        
        if self.stats["errors"]:
            self.logger.info(f"最近錯誤數量: {len(self.stats['errors'])}")
            # 只顯示最近5個錯誤
            recent_errors = self.stats["errors"][-5:]
            for error in recent_errors:
                self.logger.info(f"  - {error['timestamp']}: {error['symbol']} - {error['error']}")
    
    def setup_schedule(self):
        """設置排程任務"""
        # 每30分鐘執行一次
        schedule.every(30).minutes.do(self.run_once)
        
        # 每小時打印統計（可選）
        schedule.every().hour.do(self.print_stats)
        
        self.logger.info("⏰ 排程設置完成: 每30分鐘執行一次任務")
    
    def signal_handler(self, signum, frame):
        """處理停止信號"""
        self.logger.info(f"📨 收到停止信號 {signum}")
        self.stop_requested = True
    
    def start(self):
        """
        啟動自動化Worker
        """
        self.logger.info("🚀 AutoWorker 啟動中...")
        
        # 設置信號處理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 檢查初始連接
        if not self.check_connections():
            self.logger.error("❌ 初始連接檢查失敗，無法啟動")
            return
        
        # 設置排程
        self.setup_schedule()
        
        # 執行一次初始任務
        self.logger.info("🔄 執行初始任務...")
        self.run_once()
        
        # 標記為運行中
        self.is_running = True
        
        self.logger.info("✅ AutoWorker 已啟動，等待排程執行...")
        self.logger.info("💡 按 Ctrl+C 停止Worker")
        
        # 主循環
        try:
            while not self.stop_requested:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次排程
                
        except KeyboardInterrupt:
            self.logger.info("⌨️ 檢測到鍵盤中斷")
        
        finally:
            self.stop()
    
    def stop(self):
        """
        停止自動化Worker
        """
        self.logger.info("🛑 AutoWorker 停止中...")
        self.is_running = False
        self.stop_requested = True
        
        # 打印最終統計
        self.print_stats()
        
        self.logger.info("✅ AutoWorker 已停止")


def main():
    """
    主函數
    """
    print("🤖 自動化股票分析Worker")
    print("=" * 50)
    
    # 創建並啟動Worker
    worker = AutoWorker()
    
    try:
        worker.start()
    except Exception as e:
        worker.logger.error(f"❌ Worker啟動失敗: {str(e)}")
        worker.logger.debug(traceback.format_exc())
    finally:
        worker.logger.info("👋 程序結束")


if __name__ == "__main__":
    main()
