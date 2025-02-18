import pandas as pd
import numpy as np
from typing import Dict, List, Union
from datetime import datetime, timedelta

class DataProcessor:
    def __init__(self, df: pd.DataFrame):
        """
        データ処理クラスの初期化
        
        Args:
            df (pd.DataFrame): 処理対象のデータフレーム
        """
        self.df = df.copy()
        # 必須カラムの存在確認を先に行う
        self._validate_columns()
        self._preprocess_data()
    
    def _validate_columns(self):
        """必須カラムの存在確認"""
        required_columns = ['日付', '商品', '顧客', '売上']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(f"必須カラムが不足しています: {missing_columns}")
    
    def _preprocess_data(self):
        """データの前処理を行う"""
        try:
            # 日付型への変換
            if '日付' in self.df.columns:
                self.df['日付'] = pd.to_datetime(self.df['日付'])
        
            # 数値型への変換
            if '売上' in self.df.columns:
                self.df['売上'] = pd.to_numeric(self.df['売上'], errors='coerce')
        
            # 無効なデータの除外
            self.df = self.df[
                self.df['日付'].notna() &
                self.df['売上'].notna() &
                (self.df['売上'] >= 0) &
                self.df['商品'].notna() &
                (self.df['商品'].str.strip() != '') &
                self.df['顧客'].notna() &
                (self.df['顧客'].str.strip() != '')
            ]
        
            # 日付でソート
            self.df = self.df.sort_values('日付')
        
            # データの基本的な検証
            self._validate_data()
        
        except Exception as e:
            raise ValueError(f"データの前処理に失敗しました: {str(e)}")
    
    def _validate_data(self):
        """データの基本的な検証を行う"""
        # データ件数の確認
        if len(self.df) == 0:
            raise ValueError("有効なデータがありません")
        
        # 日付範囲の確認
        if '日付' in self.df.columns:
            min_date = self.df['日付'].min()
            max_date = self.df['日付'].max()
        else:
            min_date = self.df.index.min()
            max_date = self.df.index.max()
        
        if min_date and max_date:
            date_range = max_date - min_date
            if isinstance(date_range, pd.Timedelta) and date_range.total_seconds() < 0:
                raise ValueError("日付の範囲が不正です")
        
        # 基本統計量の計算と異常値の検出
        stats = self.df['売上'].describe()
        if stats['std'] > stats['mean'] * 10:  # 標準偏差が平均の10倍を超える場合
            print("警告: 売上データに大きなばらつきが見られます")
    
    def filter_by_date(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        日付でデータをフィルタリング
        
        Args:
            start_date (str): 開始日 (YYYY-MM-DD)
            end_date (str): 終了日 (YYYY-MM-DD)
        
        Returns:
            pd.DataFrame: フィルタリングされたデータ
        """
        df = self.df.copy()
        
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df.index.date >= start_dt.date()]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df.index.date <= end_dt.date()]
            
        return df
    
    def aggregate_sales(self, 
                       group_by: Union[str, List[str]], 
                       agg_funcs: Dict[str, List[str]] = None,
                       period: str = None) -> pd.DataFrame:
        """
        売上データの集計
        
        Args:
            group_by (str or List[str]): グループ化するカラム
            agg_funcs (Dict[str, List[str]]): 集計関数の指定
            period (str): 期間指定（日次/週次/月次）
            
        Returns:
            pd.DataFrame: 集計結果
        """
        if agg_funcs is None:
            agg_funcs = {
                '売上': ['sum', 'mean', 'count', 'std', 'min', 'max']
            }
        
        df = self.df.copy()
        
        # 期間でのグループ化が必要な場合
        if period:
            freq_map = {
                '日次': 'D',
                '週次': 'W-MON',
                '月次': 'ME'
            }
            if isinstance(group_by, str):
                group_by = [pd.Grouper(key='日付', freq=freq_map[period]), group_by]
            else:
                group_by = [pd.Grouper(key='日付', freq=freq_map[period])] + group_by
        
        result = df.groupby(group_by).agg(agg_funcs)
        
        # カラム名の設定
        if isinstance(result.columns, pd.MultiIndex):
            result.columns = [f'{col[0]}_{col[1]}' for col in result.columns]
        
        # 日付インデックスの文字列化
        if period and isinstance(result.index, pd.MultiIndex):
            result.index = result.index.set_levels(
                result.index.levels[0].strftime('%Y-%m-%d'),
                level=0
            )
        
        return result.round(2)
    
    def calculate_time_series_metrics(self, filtered_df: pd.DataFrame = None) -> Dict[str, pd.DataFrame]:
        """
        時系列指標の計算
        
        Args:
            filtered_df (pd.DataFrame, optional): フィルタリング済みのデータフレーム
            
        Returns:
            Dict[str, pd.DataFrame]: 各種時系列指標
        """
        df = filtered_df if filtered_df is not None else self.df.copy()
        
        # 基本的な集計関数の定義
        agg_funcs = {
            '売上': ['sum', 'count', 'mean', 'std', 'min', 'max']
        }
        
        # 日次集計
        daily = df.set_index('日付').groupby(pd.Grouper(freq='D')).agg(agg_funcs)
        daily.columns = ['日次売上', '日次取引数', '日次平均売上', '日次標準偏差', '日次最小売上', '日次最大売上']
        daily = daily.fillna(0)
        daily.index = daily.index.strftime('%Y-%m-%d')
        daily['日次前期比'] = daily['日次売上'].pct_change() * 100
        
        # 週次集計
        weekly = df.set_index('日付').groupby(pd.Grouper(freq='W-MON')).agg(agg_funcs)
        weekly.columns = ['週次売上', '週次取引数', '週次平均売上', '週次標準偏差', '週次最小売上', '週次最大売上']
        weekly = weekly.fillna(0)
        weekly.index = weekly.index.strftime('%Y-%m-%d')
        weekly['週次前期比'] = weekly['週次売上'].pct_change() * 100
        
        # 月次集計
        monthly = df.set_index('日付').groupby(pd.Grouper(freq='ME')).agg(agg_funcs)
        monthly.columns = ['月次売上', '月次取引数', '月次平均売上', '月次標準偏差', '月次最小売上', '月次最大売上']
        monthly = monthly.fillna(0)
        monthly.index = monthly.index.strftime('%Y-%m')
        monthly['月次前期比'] = monthly['月次売上'].pct_change() * 100
        
        return {
            'daily': daily.round(2),
            'weekly': weekly.round(2),
            'monthly': monthly.round(2)
        }
    
    def calculate_product_metrics(self, filtered_df: pd.DataFrame = None) -> Dict[str, pd.DataFrame]:
        """
        商品関連の指標を計算
        
        Args:
            filtered_df (pd.DataFrame, optional): フィルタリング済みのデータフレーム
            
        Returns:
            Dict[str, pd.DataFrame]: 商品関連の指標
        """
        df = filtered_df if filtered_df is not None else self.df.copy()
        
        # 商品別の基本統計量
        product_stats = df.groupby('商品').agg({
            '売上': ['sum', 'mean', 'count', 'max', 'min']
        })
        product_stats.columns = ['総売上', '平均売上', '取引回数', '最大売上', '最小売上']
        
        # 商品別の時系列データ
        product_time_series = df.pivot_table(
            values='売上',
            index='日付',
            columns='商品',
            aggfunc='sum'
        ).fillna(0)
        
        return {
            'stats': product_stats.round(2),
            'time_series': product_time_series
        }
    
    def calculate_customer_metrics(self, filtered_df: pd.DataFrame = None) -> Dict[str, pd.DataFrame]:
        """
        顧客関連の指標を計算
        
        Args:
            filtered_df (pd.DataFrame, optional): フィルタリング済みのデータフレーム
            
        Returns:
            Dict[str, pd.DataFrame]: 顧客関連の指標
        """
        df = filtered_df if filtered_df is not None else self.df.copy()
        
        # 日付カラムの取得
        try:
            date_col = self._get_date_column(df)
            current_date = date_col.max()
            
            # 顧客別の基本統計量
            customer_stats = df.groupby('顧客')['売上'].agg([
                ('総売上', 'sum'),
                ('平均売上', 'mean'),
                ('取引回数', 'count'),
                ('最大売上', 'max'),
                ('最小売上', 'min')
            ]).round(0)
            
            # 顧客別の時系列データ
            customer_time_series = pd.pivot_table(
                df,
                values='売上',
                index=date_col,
                columns='顧客',
                aggfunc='sum'
            ).fillna(0)
            
            # RFM分析
            rfm = df.groupby('顧客').agg({
                '日付': lambda x: (current_date - x.max()).days,  # Recency
                '売上': ['count', 'sum']  # Frequency, Monetary
            })
            
            # カラム名を設定
            rfm.columns = ['Recency', 'Frequency', 'Monetary']
            
            # 各指標のスコアリング
            def score_rfm(x, reverse=False):
                if x.isnull().any():
                    result = pd.Series([1] * len(x))
                    result[x.notnull()] = score_rfm(x.dropna(), reverse=reverse)
                    return result
                elif x.nunique() == 1:
                    return pd.Series([2] * len(x))
                else:
                    try:
                        labels = range(4, 0, -1) if reverse else range(1, 5)
                        return pd.qcut(x, q=4, labels=labels, duplicates='drop')
                    except ValueError:
                        return pd.Series([2] * len(x))
            
            # RFMスコアの計算
            rfm['R'] = score_rfm(rfm['Recency'], reverse=True)
            rfm['F'] = score_rfm(rfm['Frequency'])
            rfm['M'] = score_rfm(rfm['Monetary'])
            
            # スコアを数値型に変換
            for col in ['R', 'F', 'M']:
                rfm[col] = rfm[col].fillna(1)
                if not pd.api.types.is_integer_dtype(rfm[col]):
                    rfm[col] = rfm[col].astype('Int64')
            
            # セグメントの定義
            def segment_customer(row):
                if row['R'] >= 3 and row['F'] >= 3 and row['M'] >= 3:
                    return 'VIPカスタマー'
                elif row['R'] >= 3 and row['F'] >= 3:
                    return '優良カスタマー'
                elif row['R'] >= 2 and row['F'] >= 2:
                    return '通常カスタマー'
                else:
                    return '要フォローカスタマー'
            
            rfm['セグメント'] = rfm.apply(segment_customer, axis=1)
            
            # 日付を文字列形式に変換
            customer_time_series.index = customer_time_series.index.strftime('%Y-%m-%d')
            
            return {
                'stats': customer_stats,
                'time_series': customer_time_series,
                'rfm': rfm
            }
            
        except Exception as e:
            raise ValueError(f"顧客分析の計算中にエラーが発生しました: {str(e)}")
    
    def calculate_growth_rates(self, filtered_df: pd.DataFrame, group_by: str, period: str) -> pd.DataFrame:
        """
        成長率を計算
        
        Args:
            filtered_df (pd.DataFrame): フィルタリング済みのデータフレーム
            group_by (str): グループ化するカラム
            period (str): 期間（日次/週次/月次）
            
        Returns:
            pd.DataFrame: 成長率のデータフレーム
        """
        try:
            df = filtered_df.copy()
            
            # 日付カラムの確認と設定
            if '日付' not in df.columns:
                raise ValueError("日付カラムが見つかりません")
            
            # 日付型の確認と変換
            df['日付'] = pd.to_datetime(df['日付'])
            
            # 期間ごとの集計
            freq_map = {
                "日次": 'D',
                "週次": 'W-MON',
                "月次": 'ME'
            }
            
            # グループ化と集計
            grouped = df.groupby([pd.Grouper(key='日付', freq=freq_map[period]), group_by])['売上'].sum()
            grouped = grouped.reset_index()
            
            # 期間カラムのフォーマット設定
            if period == "月次":
                grouped['期間'] = grouped['日付'].dt.strftime('%Y-%m')
            else:
                grouped['期間'] = grouped['日付'].dt.strftime('%Y-%m-%d')
            
            # ピボットテーブルの作成
            pivot_table = pd.pivot_table(
                grouped,
                index='期間',
                columns=group_by,
                values='売上',
                fill_value=0
            )
            
            # 成長率の計算（非推奨警告の解消）
            growth_rates = pivot_table.pct_change(fill_method=None) * 100
            
            # 最初の行のNaNを0で埋める
            growth_rates = growth_rates.fillna(0)
            
            return growth_rates.round(2)
            
        except Exception as e:
            raise ValueError(f"成長率の計算中にエラーが発生しました: {str(e)}")
    
    def analyze_customer_behavior(self, filtered_df: pd.DataFrame) -> pd.DataFrame:
        """
        顧客行動分析
        
        Args:
            filtered_df (pd.DataFrame): フィルタリング済みのデータフレーム
            
        Returns:
            pd.DataFrame: 顧客行動分析の結果
        """
        df = filtered_df.copy()
        
        # 顧客ごとの基本指標
        customer_behavior = df.groupby('顧客').agg({
            '売上': ['count', 'sum', 'mean', 'std'],
            '日付': lambda x: (x.max() - x.min()).days + 1
        }).round(0)
        
        customer_behavior.columns = ['取引回数', '総売上', '平均売上', '売上標準偏差', '取引期間']
        
        # 平均取引間隔の計算
        customer_behavior['平均取引間隔'] = (customer_behavior['取引期間'] / customer_behavior['取引回数']).round(1)
        
        # 最終取引日からの経過日数
        latest_date = df['日付'].max()
        last_purchase = df.groupby('顧客')['日付'].max()
        customer_behavior['最終取引からの経過日数'] = (latest_date - last_purchase).dt.days
        
        return customer_behavior
    
    def analyze_trends(self, filtered_df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        トレンド分析
        
        Args:
            filtered_df (pd.DataFrame): フィルタリング済みのデータフレーム
            period (str): 期間（日次/週次/月次）
            
        Returns:
            pd.DataFrame: トレンド分析の結果
        """
        df = filtered_df.copy()
        df = df.set_index('日付')
        
        # 期間ごとの集計
        if period == "日次":
            sales = df['売上'].resample('D').sum()
        elif period == "週次":
            sales = df['売上'].resample('W-MON').sum()
        else:  # 月次
            sales = df['売上'].resample('ME').sum()
        
        # 移動平均の計算
        trends = pd.DataFrame({
            '売上': sales,
            '7期間移動平均': sales.rolling(window=7, min_periods=1).mean(),
            '30期間移動平均': sales.rolling(window=30, min_periods=1).mean()
        })
        
        return trends.round(0)
    
    def analyze_seasonality(self, filtered_df: pd.DataFrame, period: str) -> pd.DataFrame:
        """
        季節性分析
        
        Args:
            filtered_df (pd.DataFrame): フィルタリング済みのデータフレーム
            period (str): 期間（日次/週次/月次）
            
        Returns:
            pd.DataFrame: 季節性分析の結果
        """
        df = filtered_df.copy()
        
        # 時間的特徴の抽出
        df['年'] = df['日付'].dt.year
        df['月'] = df['日付'].dt.month
        df['曜日'] = df['日付'].dt.day_name()
        
        # 期間に応じた集計
        if period == "日次":
            seasonality = df.groupby('曜日')['売上'].agg(['mean', 'count']).round(0)
            seasonality.index = pd.CategoricalIndex(seasonality.index, categories=[
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ])
        elif period == "週次":
            seasonality = df.groupby(['年', '月'])['売上'].agg(['mean', 'count']).round(0)
        else:  # 月次
            seasonality = df.groupby('月')['売上'].agg(['mean', 'count']).round(0)
        
        return seasonality.sort_index()
    
    def validate_analysis_results(self, filtered_df: pd.DataFrame = None) -> Dict[str, bool]:
        """
        分析結果の検証を行う
        
        Args:
            filtered_df (pd.DataFrame, optional): フィルタリング済みのデータフレーム
            
        Returns:
            Dict[str, bool]: 各検証項目の結果
        """
        df = filtered_df if filtered_df is not None else self.df.copy()
        validation_results = {}
        
        try:
            # 1. 基本的なデータ整合性の検証
            total_sales = df['売上'].sum()
            daily_sales = df.groupby('日付')['売上'].sum().sum()
            validation_results['売上集計整合性'] = abs(total_sales - daily_sales) < 0.01
            
            # 2. 日付の連続性検証
            date_range = pd.date_range(df['日付'].min(), df['日付'].max())
            actual_dates = df['日付'].dt.date.unique()
            validation_results['日付の連続性'] = len(date_range) >= len(actual_dates)
            
            # 3. 商品別集計の検証
            product_totals = df.groupby('商品')['売上'].sum()
            product_daily_totals = df.groupby(['日付', '商品'])['売上'].sum().groupby('商品').sum()
            validation_results['商品別集計整合性'] = all(
                abs(product_totals - product_daily_totals) < 0.01
            )
            
            # 4. 顧客別集計の検証
            customer_totals = df.groupby('顧客')['売上'].sum()
            customer_daily_totals = df.groupby(['日付', '顧客'])['売上'].sum().groupby('顧客').sum()
            validation_results['顧客別集計整合性'] = all(
                abs(customer_totals - customer_daily_totals) < 0.01
            )
            
            # 5. 成長率計算の検証
            growth_rates = self.calculate_growth_rates(df, '商品', '月次')
            validation_results['成長率計算'] = not growth_rates.empty and not growth_rates.isnull().all().all()
            
            # 6. RFM分析の検証
            customer_metrics = self.calculate_customer_metrics(df)
            rfm_df = customer_metrics['rfm']
            validation_results['RFM分析'] = all([
                'R' in rfm_df.columns,
                'F' in rfm_df.columns,
                'M' in rfm_df.columns,
                'セグメント' in rfm_df.columns
            ])
            
            # 7. 時系列分析の検証
            time_metrics = self.calculate_time_series_metrics(df)
            validation_results['時系列分析'] = all([
                'daily' in time_metrics,
                'weekly' in time_metrics,
                'monthly' in time_metrics
            ])
            
            # 8. 異常値の検出
            mean_sales = df['売上'].mean()
            std_sales = df['売上'].std()
            outliers = df[abs(df['売上'] - mean_sales) > 3 * std_sales]
            validation_results['異常値の割合'] = len(outliers) / len(df) < 0.01  # 1%未満を正常とする
            
        except Exception as e:
            print(f"検証中にエラーが発生しました: {str(e)}")
            return {'エラー': False}
        
        return validation_results
    
    def print_validation_summary(self, validation_results: Dict[str, bool]) -> None:
        """
        検証結果のサマリーを表示
        
        Args:
            validation_results (Dict[str, bool]): 検証結果
        """
        print("\n=== 分析結果の検証サマリー ===")
        for item, result in validation_results.items():
            status = "✅ OK" if result else "❌ 要確認"
            print(f"{item}: {status}")
        print("===========================\n")

    def _get_date_column(self, df: pd.DataFrame) -> pd.Series:
        """日付カラムを取得する共通メソッド
        
        Args:
            df (pd.DataFrame): 対象のデータフレーム
            
        Returns:
            pd.Series: 日付カラム
        """
        if '日付' in df.columns:
            return pd.to_datetime(df['日付'])
        elif df.index.name == '日付':
            return pd.to_datetime(df.index)
        else:
            df = df.copy()
            df = df.reset_index()
            if '日付' in df.columns:
                return pd.to_datetime(df['日付'])
            raise ValueError("日付カラムが見つかりません") 