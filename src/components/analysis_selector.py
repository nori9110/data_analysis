import streamlit as st
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

class AnalysisSelector:
    def __init__(self):
        """分析対象選択コンポーネント"""
        self.analysis_types = {
            "sales": "売上分析",
            "product": "商品分析",
            "customer": "顧客分析"
        }

    def render(self) -> Tuple[str, Dict[str, Any]]:
        """
        分析対象選択UIをレンダリング
        
        Returns:
            Tuple[str, Dict[str, Any]]: 選択された分析タイプと期間設定
        """
        # 分析タイプの選択
        analysis_type = st.selectbox(
            "分析タイプを選択",
            options=list(self.analysis_types.keys()),
            format_func=lambda x: self.analysis_types[x],
            key="analysis_type_selector"
        )
        
        # 期間設定
        st.subheader("期間設定")
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "開始日",
                value=datetime.now() - timedelta(days=30),
                key="analysis_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "終了日",
                value=datetime.now(),
                key="analysis_end_date"
            )
        
        # 追加のフィルター設定
        with st.expander("詳細設定"):
            filters = self._render_filters(analysis_type)
        
        return analysis_type, {
            "start_date": start_date,
            "end_date": end_date,
            "filters": filters
        }

    def _render_filters(self, analysis_type: str) -> Dict[str, Any]:
        """
        分析タイプに応じたフィルターUIをレンダリング
        
        Args:
            analysis_type (str): 分析タイプ
        
        Returns:
            Dict[str, Any]: フィルター設定
        """
        filters = {}
        
        if analysis_type == "sales":
            filters["min_amount"] = st.number_input(
                "最小売上額",
                value=0,
                step=1000
            )
            filters["exclude_outliers"] = st.checkbox(
                "異常値を除外",
                value=True
            )
            
        elif analysis_type == "product":
            filters["categories"] = st.multiselect(
                "商品カテゴリー",
                options=["スポーツ", "食品", "家電", "ファッション", "その他"]
            )
            filters["min_stock"] = st.number_input(
                "最小在庫数",
                value=0
            )
            
        elif analysis_type == "customer":
            filters["segments"] = st.multiselect(
                "顧客セグメント",
                options=["セグメントA", "セグメントB", "セグメントC"]
            )
            filters["active_only"] = st.checkbox(
                "アクティブな顧客のみ",
                value=True
            )
        
        return filters 