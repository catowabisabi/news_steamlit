# 1. get all symbols of today from mongo db

# 2. for each symbol, create the report if not exist

# 3. save the english and chinese report to the local folder, and also generate ig post

"""
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
                    
                    # 檢查數據完整性 - 公司描述為可選項
                    required_data = ['news_cn', 'analysis', 'news_en', 'analysis_en']
                    optional_data = ['desc_en', 'desc_cn']
                    missing_data = [dt for dt in required_data if not data.get(dt)]
                    missing_optional = [dt for dt in optional_data if not data.get(dt)]
                    
                    if missing_data:
                        st.warning(f"⚠️ {symbol} 缺少以下必要數據: {', '.join(missing_data)}")
                        
                        # 提供自動生成選項 (只有缺少必要數據時才提供)
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
                                    # 修復：檢查 result 是否存在且有 errors 屬性
                                    if 'result' in locals() and result and isinstance(result, dict) and "errors" in result:
                                        for error in result["errors"]:
                                            st.error(f"  - {error}")
                        
                        st.info("💡 或者運行命令: `python process_stock.py " + symbol + "`")
                        continue  # 只有在缺少必要數據時才跳過報告生成
                    
                    # 顯示可選數據缺失信息（不阻止報告生成）
                    if missing_optional:
                        st.info(f"ℹ️ {symbol} 缺少以下可選數據（不影響報告生成）: {', '.join(missing_optional)}")
                    
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
                    
                    # 添加重新下載新聞按鈕
                    st.markdown("---")
                    col_refresh1, col_refresh2 = st.columns([1, 3])
                    
                    with col_refresh1:
                        if st.button(f"📰 重新下載 {symbol} 新聞", key=f"refresh_news_{symbol}", help="重新獲取新聞並重新處理所有數據"):
                            with st.spinner(f"正在重新下載 {symbol} 的新聞並重新處理..."):
                                try:
                                    # 創建進度顯示
                                    progress_container = st.container()
                                    with progress_container:
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        log_container = st.empty()
                                        log_messages = []
                                        
                                        # 調用處理函數，force_refresh=True 會重新下載所有數據
                                        status_text.text(f"🔄 重新處理 {symbol} 所有數據...")
                                        result = app.process_with_progress(symbol, log_messages, log_container, progress_bar, status_text, force_refresh=True)
                                        
                                        if result.get("success", False):
                                            st.success(f"✅ {symbol} 新聞重新下載並處理完成!")
                                            st.rerun()  # 重新加載頁面以顯示新數據
                                        else:
                                            st.error(f"❌ {symbol} 重新處理失敗")
                                            if result.get("errors"):
                                                for error in result["errors"]:
                                                    st.error(f"  - {error}")
                                except Exception as e:
                                    st.error(f"❌ 重新處理過程出錯: {str(e)}")
                                    
                                    """

# from 5am to 8pm EST, run the script every 15 minutes