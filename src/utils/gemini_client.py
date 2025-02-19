import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Any

# 環境変数の読み込み
load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set in environment variables")
        
        # Gemini APIの初期化
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def analyze_data(self, data: Dict[str, Any], prompt: str) -> str:
        """
        データ分析を実行し、結果を返す
        
        Args:
            data (Dict[str, Any]): 分析対象のデータ
            prompt (str): 分析プロンプト
        
        Returns:
            str: 分析結果
        """
        try:
            # データと分析プロンプトを組み合わせて完全なプロンプトを作成
            full_prompt = f"""
            以下のデータを分析してください：
            {data}
            
            分析の観点：
            {prompt}
            
            以下の形式で回答してください：
            1. 分析概要
            2. 重要な発見事項
            3. 推奨アクション
            """
            
            # Gemini APIを呼び出し
            response = self.model.generate_content(full_prompt)
            
            return response.text
        
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def validate_prompt(self, prompt: str) -> bool:
        """
        プロンプトのバリデーションを行う
        
        Args:
            prompt (str): 検証するプロンプト
        
        Returns:
            bool: バリデーション結果
        """
        # 最小文字数チェック
        if len(prompt) < 20:
            return False
            
        # 禁止語句チェック
        forbidden_words = ['機密', 'パスワード', 'セキュリティ']
        if any(word in prompt for word in forbidden_words):
            return False
            
        return True 