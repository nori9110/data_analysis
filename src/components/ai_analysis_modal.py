import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd
from utils.ai_analyzer import AIAnalyzer
from utils.prompt_manager import PromptManager

class AIAnalysisModal:
    """AI分析ポップアップコンポーネント"""
    
    def __init__(self):
        self.analyzer = AIAnalyzer()
        self.prompt_manager = PromptManager()
        self._init_session_state()
        self._init_templates()

    def _init_session_state(self):
        """セッション状態の初期化"""
        if "analysis_state" not in st.session_state:
            st.session_state.analysis_state = {
                "is_visible": False,
                "prompt": "",
                "template": "カスタム入力",
                "is_analyzing": False,
                "has_error": False,
                "error_message": ""
            }

    def _init_templates(self):
        """分析テンプレートの初期化"""
        self.default_templates = {
            "売上分析": "月間の売上トレンドと主要な変動要因を分析してください",
            "商品分析": "商品カテゴリー別の売上状況と改善点を分析してください",
            "顧客分析": "顧客セグメント別の購買傾向を分析してください",
            "地域分析": "地域別の売上傾向と特徴的なパターンを分析してください",
            "時系列分析": "売上の時系列パターンと季節性を分析してください"
        }

    def render(self, data: Dict[str, Any]):
        """AI分析ポップアップをレンダリング"""
        if not st.session_state.analysis_state["is_visible"]:
            return

        # ヘッダー
        col1, col2 = st.columns([10, 1])
        with col1:
            st.subheader("🤖 AI分析")
        with col2:
            if st.button("✕", key="close_popup"):
                st.session_state.analysis_state["is_visible"] = False
                st.experimental_rerun()
        
        st.markdown("---")
        
        # メインコンテンツ
        if not st.session_state.analysis_state["has_error"]:
            self._render_analysis_form(data)
        else:
            st.error(st.session_state.analysis_state["error_message"])

    def _setup_styles(self):
        """スタイル設定（最小限のスタイルのみ維持）"""
        st.markdown("""
        <style>
        div.ai-analysis-popup .stButton button {
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)

    def _render_analysis_form(self, data: Dict[str, Any]):
        """分析フォームのレンダリング"""
        try:
            if not data or 'df' not in data:
                st.error("分析対象のデータが設定されていません")
                return
            
            df = data['df']
            metrics = data['metrics']
            analysis_type = data.get('analysis_type', 'comprehensive')
            
            # テンプレート選択
            template_options = ["カスタム入力"] + list(self.default_templates.keys())
            selected_template = st.selectbox(
                "分析テンプレート",
                options=template_options,
                key="prompt_template"
            )
            
            # プロンプト入力
            if selected_template == "カスタム入力":
                prompt = st.text_area(
                    "分析の観点を入力",
                    height=100,
                    key="custom_prompt",
                    help="具体的な分析の観点や確認したいポイントを入力してください（10文字以上）"
                )
            else:
                prompt = self.default_templates[selected_template]
                st.text_area(
                    "選択されたテンプレート",
                    value=prompt,
                    height=100,
                    disabled=True
                )

            # 分析実行ボタン
            if st.button("分析開始", key="start_analysis", use_container_width=True):
                if not prompt or len(prompt.strip()) < 10:
                    st.error("分析の観点を10文字以上で入力してください")
                    return

                try:
                    with st.spinner("分析を実行中..."):
                        analysis_data = {
                            "data": df.to_dict(),
                            "metrics": metrics,
                            "type": analysis_type
                        }
                        result = self.analyzer.analyze_sales_data(analysis_data, prompt)
                        self._display_analysis_results(result)
                except Exception as api_error:
                    if "429" in str(api_error):
                        st.error("API利用制限に達しました。しばらく時間をおいて再度お試しください。")
                    else:
                        st.error(f"分析中にエラーが発生しました: {str(api_error)}")
                
        except Exception as e:
            st.session_state.analysis_state["has_error"] = True
            st.session_state.analysis_state["error_message"] = f"エラーが発生しました: {str(e)}"
            st.error(st.session_state.analysis_state["error_message"])

    def _display_analysis_results(self, result: Dict[str, Any]):
        """分析結果の表示"""
        st.markdown("---")
        st.subheader("分析結果")
        
        # 分析概要
        with st.expander("📊 分析概要", expanded=True):
            st.markdown(result.get("summary", ""))
        
        # 重要な発見事項
        with st.expander("🔍 重要な発見事項", expanded=True):
            for finding in result.get("findings", []):
                st.markdown(f"- {finding}")
        
        # 推奨アクション
        with st.expander("✨ 推奨アクション", expanded=True):
            for action in result.get("recommendations", []):
                st.markdown(f"- {action}")

    def _display_results(self, result: Dict[str, Any]):
        """
        分析結果を表示
        
        Args:
            result (Dict[str, Any]): 分析結果
        """
        # 概要
        st.subheader("分析概要")
        st.write(result.get("summary", ""))
        
        # 重要な発見事項
        st.subheader("重要な発見事項")
        for finding in result.get("findings", []):
            st.markdown(f"- {finding}")
        
        # 推奨アクション
        st.subheader("推奨アクション")
        for action in result.get("recommendations", []):
            st.markdown(f"- {action}")
            
        # 結果の保存ボタン
        if st.button("結果を保存", key="save_results"):
            # TODO: 結果の保存機能を実装
            st.success("分析結果を保存しました") 