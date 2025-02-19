import streamlit as st
from typing import Optional, Callable, Any

class Modal:
    def __init__(self, title: str, key: str):
        """
        モーダル風コンポーネント
        
        Args:
            title (str): タイトル
            key (str): 一意のキー
        """
        self.title = title
        self.key = key
        
        # セッション状態の初期化
        if f"modal_{key}_open" not in st.session_state:
            st.session_state[f"modal_{key}_open"] = False

    def open(self):
        """モーダルを開く"""
        st.session_state[f"modal_{self.key}_open"] = True

    def close(self):
        """モーダルを閉じる"""
        st.session_state[f"modal_{self.key}_open"] = False

    def is_open(self) -> bool:
        """
        モーダルが開いているかどうかを確認
        
        Returns:
            bool: モーダルの状態
        """
        return st.session_state[f"modal_{self.key}_open"]

    def render(self, content_callback: Callable[[], Any]):
        """
        モーダルの内容をレンダリング
        
        Args:
            content_callback (Callable[[], Any]): モーダルの内容を生成するコールバック関数
        """
        if self.is_open():
            # モーダル用のコンテナを作成
            with st.container():
                # モーダルの外枠
                st.markdown("""
                    <div class="modal-wrapper">
                        <div class="modal-window">
                """, unsafe_allow_html=True)
                
                # ヘッダー部分
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"### {self.title}")
                with col2:
                    if st.button("×", key=f"close_x_{self.key}", help="閉じる"):
                        self.close()
                        st.rerun()
                
                # 区切り線
                st.markdown("<hr>", unsafe_allow_html=True)
                
                # コンテンツ部分
                content_container = st.container()
                with content_container:
                    content_callback()
                
                # フッター部分
                st.markdown("<hr>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("閉じる", key=f"close_{self.key}", use_container_width=True):
                        self.close()
                        st.rerun()
                
                # モーダルの閉じタグ
                st.markdown("""
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    def inject_custom_css(self):
        """カスタムCSSを注入"""
        st.markdown("""
        <style>
        /* モーダルのスタイル */
        .modal-wrapper {
            margin: -1rem -1rem 1rem -1rem;
            padding: 1rem;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .modal-window {
            padding: 1rem;
        }
        
        /* ボタンのスタイル調整 */
        .stButton > button {
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        
        /* 閉じるボタンのスタイル */
        button[kind="secondary"] {
            background: none;
            border: none;
            color: #666;
            font-size: 1.2rem;
            padding: 0.2rem 0.5rem;
        }
        
        button[kind="secondary"]:hover {
            color: #333;
            background: rgba(0, 0, 0, 0.05);
        }
        
        hr {
            margin: 1rem 0;
            border: 0;
            border-top: 1px solid rgba(0, 0, 0, 0.1);
        }
        </style>
        """, unsafe_allow_html=True) 