from typing import Dict, List, Optional
import json
import os
from datetime import datetime

class PromptManager:
    def __init__(self, storage_path: str = "data/prompts"):
        self.storage_path = storage_path
        self._ensure_storage_directory()
        self.templates = self._load_default_templates()

    def _ensure_storage_directory(self):
        """ストレージディレクトリの存在を確認し、必要に応じて作成"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def _load_default_templates(self) -> Dict[str, List[str]]:
        """デフォルトのプロンプトテンプレートを読み込む"""
        return {
            "sales": [
                "売上トレンドを分析し、重要なパターンと改善機会を提案してください",
                "前年同期比での変化点と要因を分析してください",
                "売上の季節性と対策について提案してください"
            ],
            "product": [
                "商品カテゴリー別のパフォーマンスを評価し、改善点を提示してください",
                "商品間の相関関係を分析し、クロスセル機会を特定してください",
                "在庫回転率の観点から商品戦略を提案してください"
            ],
            "customer": [
                "顧客セグメント別の特徴と対応戦略を提案してください",
                "優良顧客の特徴を分析し、類似顧客の開拓方法を提案してください",
                "顧客離反リスクの兆候と防止策を分析してください"
            ]
        }

    def save_prompt(self, prompt: str, category: str, tags: List[str] = None) -> str:
        """
        プロンプトを保存
        
        Args:
            prompt (str): 保存するプロンプト
            category (str): プロンプトのカテゴリ
            tags (List[str], optional): タグのリスト
        
        Returns:
            str: 保存されたプロンプトのID
        """
        prompt_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_data = {
            "id": prompt_id,
            "prompt": prompt,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "success_rate": 0.0,
            "use_count": 0
        }
        
        file_path = os.path.join(self.storage_path, f"{prompt_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
        return prompt_id

    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        """
        保存されたプロンプトを取得
        
        Args:
            prompt_id (str): プロンプトID
        
        Returns:
            Optional[Dict]: プロンプトデータ
        """
        file_path = os.path.join(self.storage_path, f"{prompt_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_templates(self, category: str) -> List[str]:
        """
        カテゴリに応じたテンプレートを取得
        
        Args:
            category (str): テンプレートのカテゴリ
        
        Returns:
            List[str]: テンプレートのリスト
        """
        return self.templates.get(category, []) 