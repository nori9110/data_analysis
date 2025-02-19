from typing import Dict, Any, List, Optional
from .gemini_client import GeminiClient
import json
import logging

class AIAnalyzer:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.logger = logging.getLogger(__name__)

    def analyze_sales_data(self, data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """
        売上データの分析を実行
        
        Args:
            data (Dict[str, Any]): 分析対象の売上データ
            prompt (str): 分析プロンプト
        
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # プロンプトのバリデーション
            if not self.gemini_client.validate_prompt(prompt):
                raise ValueError("Invalid prompt")

            # 分析の実行
            analysis_result = self.gemini_client.analyze_data(data, prompt)
            
            # 結果の構造化
            structured_result = self._structure_analysis_result(analysis_result)
            
            return structured_result
            
        except Exception as e:
            self.logger.error(f"Error in sales data analysis: {str(e)}")
            raise

    def _structure_analysis_result(self, raw_result: str) -> Dict[str, Any]:
        """
        分析結果を構造化データに変換
        
        Args:
            raw_result (str): 生の分析結果テキスト
        
        Returns:
            Dict[str, Any]: 構造化された分析結果
        """
        try:
            # 結果をセクションに分割
            sections = raw_result.split('\n\n')
            
            structured_result = {
                'summary': '',
                'findings': [],
                'recommendations': []
            }
            
            current_section = None
            for section in sections:
                if '分析概要' in section:
                    current_section = 'summary'
                    structured_result['summary'] = section.split('\n', 1)[1] if '\n' in section else ''
                elif '重要な発見事項' in section:
                    current_section = 'findings'
                    findings = section.split('\n')[1:]
                    structured_result['findings'] = [f.strip('- ') for f in findings if f.strip()]
                elif '推奨アクション' in section:
                    current_section = 'recommendations'
                    recommendations = section.split('\n')[1:]
                    structured_result['recommendations'] = [r.strip('- ') for r in recommendations if r.strip()]
            
            return structured_result
            
        except Exception as e:
            self.logger.error(f"Error in structuring analysis result: {str(e)}")
            return {
                'summary': raw_result,
                'findings': [],
                'recommendations': []
            } 