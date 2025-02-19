import os
from typing import Dict, Any, List
import json
from datetime import datetime
import logging
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st

# 環境変数の読み込み
load_dotenv()

class AIAnalyzer:
    def __init__(self):
        """AI分析クライアントの初期化"""
        self.logger = logging.getLogger(__name__)
        self._setup_client()

    def _setup_client(self):
        """APIクライアントの設定"""
        # モデルプロバイダーの選択
        self.provider = os.getenv("MODEL_PROVIDER", "openai")
        
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.error("OpenAI APIキーが設定されていません。.envファイルを確認してください。")
                raise ValueError("OpenAI APIキーが必要です")
            
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("GPT_MODEL", "gpt-4-turbo-preview")
        # else:
        #     import google.generativeai as genai
        #     genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        #     self.client = genai
        #     self.model = self.client.GenerativeModel('gemini-pro')

    def analyze_sales_data(self, data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """
        売上データの分析を実行
        
        Args:
            data (Dict[str, Any]): 分析対象のデータ
            prompt (str): 分析プロンプト
        
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # プロンプトの構築
            system_prompt = """
            あなたは優秀なデータアナリストとして、以下の売上データを分析し、
            重要な洞察と実用的な提案を提供してください。
            
            分析結果は以下の形式で提供してください：
            1. 概要：主要な発見と全体的な状況
            2. 重要な発見事項：箇条書きで具体的な発見を列挙
            3. 推奨アクション：実行可能な具体的な提案を箇条書きで提供
            """

            # データの整形
            data_str = json.dumps(data, ensure_ascii=False, default=str)
            
            if self.provider == "openai":
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"データ: {data_str}\n\n分析観点: {prompt}"}
                ]
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # レスポンスの解析
                result = response.choices[0].message.content
            # else:
            #     # Gemini用の実装（コメントアウト）
            #     response = self.model.generate_content([
            #         system_prompt,
            #         f"データ: {data_str}\n\n分析観点: {prompt}"
            #     ])
            #     result = response.text

            # 結果の構造化
            sections = result.split("\n\n")
            structured_result = {
                "summary": "",
                "findings": [],
                "recommendations": []
            }

            current_section = None
            for section in sections:
                if "概要" in section:
                    current_section = "summary"
                    structured_result["summary"] = section.replace("概要：", "").strip()
                elif "重要な発見事項" in section:
                    current_section = "findings"
                elif "推奨アクション" in section:
                    current_section = "recommendations"
                elif current_section in ["findings", "recommendations"]:
                    items = [item.strip("- ").strip() for item in section.split("\n") if item.strip()]
                    structured_result[current_section].extend(items)

            return structured_result

        except Exception as e:
            self.logger.error(f"Error in sales data analysis: {str(e)}")
            raise Exception(f"分析中にエラーが発生しました: {str(e)}")

    def _format_response(self, raw_response: str) -> Dict[str, Any]:
        """
        APIレスポンスを構造化された形式に変換
        
        Args:
            raw_response (str): 生のAPIレスポンス
        
        Returns:
            Dict[str, Any]: 構造化された分析結果
        """
        try:
            lines = raw_response.split('\n')
            result = {
                "summary": "",
                "findings": [],
                "recommendations": []
            }
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if "概要" in line:
                    current_section = "summary"
                elif "重要な発見事項" in line:
                    current_section = "findings"
                elif "推奨アクション" in line:
                    current_section = "recommendations"
                elif current_section == "summary":
                    result["summary"] += line + "\n"
                elif current_section in ["findings", "recommendations"]:
                    if line.startswith("- "):
                        result[current_section].append(line[2:])
                    else:
                        result[current_section].append(line)
            
            return result
        except Exception as e:
            self.logger.error(f"Error formatting response: {str(e)}")
            raise 