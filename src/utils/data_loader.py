import pandas as pd
import sqlite3
from pathlib import Path

def load_csv_data(file_path: str) -> pd.DataFrame:
    """
    CSVファイルを読み込み、DataFrameとして返す
    
    Args:
        file_path (str): CSVファイルのパス
        
    Returns:
        pd.DataFrame: 読み込んだデータ
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise Exception(f"CSVファイルの読み込みに失敗しました: {str(e)}")

def validate_csv_data(df: pd.DataFrame, required_columns: list) -> bool:
    """
    DataFrameのバリデーションを行う
    
    Args:
        df (pd.DataFrame): 検証するDataFrame
        required_columns (list): 必須カラムのリスト
        
    Returns:
        bool: バリデーション結果
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"必須カラムが不足しています: {missing_columns}")
    return True

def save_to_sqlite(df: pd.DataFrame, table_name: str, db_path: str = "data/sales.db"):
    """
    DataFrameをSQLiteデータベースに保存
    
    Args:
        df (pd.DataFrame): 保存するDataFrame
        table_name (str): テーブル名
        db_path (str): データベースファイルのパス
    """
    try:
        # データベースディレクトリの作成
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # データベース接続
        conn = sqlite3.connect(db_path)
        
        # DataFrameをSQLiteに保存
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        conn.close()
    except Exception as e:
        raise Exception(f"データベースへの保存に失敗しました: {str(e)}")

def load_from_sqlite(table_name: str, db_path: str = "data/sales.db") -> pd.DataFrame:
    """
    SQLiteデータベースからデータを読み込む
    
    Args:
        table_name (str): テーブル名
        db_path (str): データベースファイルのパス
        
    Returns:
        pd.DataFrame: 読み込んだデータ
    """
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        raise Exception(f"データベースからの読み込みに失敗しました: {str(e)}") 