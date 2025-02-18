import streamlit as st
from typing import Any, Callable
import pandas as pd
import hashlib
import json

class CacheManager:
    @staticmethod
    def hash_params(*args, **kwargs) -> str:
        """パラメータからハッシュ値を生成"""
        # 引数を文字列に変換してハッシュ化
        params_str = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(params_str.encode()).hexdigest()

    @staticmethod
    def cache_data(func: Callable) -> Callable:
        """
        データをキャッシュするデコレータ
        
        Args:
            func (Callable): キャッシュ対象の関数
            
        Returns:
            Callable: キャッシュ機能を追加した関数
        """
        def wrapper(*args, **kwargs):
            # キャッシュキーの生成
            cache_key = f"cache_{func.__name__}_{CacheManager.hash_params(*args, **kwargs)}"
            
            # キャッシュからデータを取得
            if cache_key in st.session_state:
                return st.session_state[cache_key]
            
            # データを計算してキャッシュに保存
            result = func(*args, **kwargs)
            st.session_state[cache_key] = result
            return result
            
        return wrapper

    @staticmethod
    def clear_cache():
        """キャッシュをクリア"""
        # キャッシュに関連する項目のみを削除
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("cache_")]
        for key in keys_to_remove:
            del st.session_state[key]

# キャッシュ付きのデータ処理関数のデコレータ
def cached_data(func: Callable) -> Callable:
    """
    データ処理関数用のキャッシュデコレータ
    
    Args:
        func (Callable): キャッシュ対象の関数
        
    Returns:
        Callable: キャッシュ機能を追加した関数
    """
    return st.cache_data(func)

# キャッシュ付きのリソース処理関数のデコレータ
def cached_resource(func: Callable) -> Callable:
    """
    リソース処理関数用のキャッシュデコレータ
    
    Args:
        func (Callable): キャッシュ対象の関数
        
    Returns:
        Callable: キャッシュ機能を追加した関数
    """
    return st.cache_resource(func) 