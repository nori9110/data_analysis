import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.data_processor import DataProcessor
from utils.visualization import plot_sales_trend, plot_product_sales, plot_customer_analysis
from utils.cache_manager import cached_data
from utils.data_loader import load_csv_data, validate_csv_data, save_to_sqlite

def load_data():
    """データの読み込み処理"""
    # ファイルアップロード
    uploaded_file = st.file_uploader(
        "CSVファイルをアップロード",
        type=['csv'],
        help="売上データのCSVファイルをアップロードしてください。"
    )
    
    if uploaded_file is not None:
        try:
            # CSVファイルの読み込み（エンコーディングとして'utf-8'を指定）
            df = pd.read_csv(uploaded_file, encoding='utf-8', parse_dates=['購入日'])
            
            # 必須カラムの確認
            required_columns = ['購入日', '購入カテゴリー', '顧客ID', '購入金額']
            if validate_csv_data(df, required_columns):
                # データの保存
                save_to_sqlite(df, 'sales_data')
                st.success('データのアップロードと保存が完了しました。')
                return df
        except Exception as e:
            st.error(f'エラーが発生しました: {str(e)}')
            return None
    
    # サンプルデータの作成と返却
    return create_sample_data()

@cached_data
def create_sample_data():
    """サンプルデータの作成"""
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    categories = {
        'スポーツ': ['テニス用品', 'ゴルフ用品', '野球用品', 'サッカー用品', 'フィットネス用品'],
        'ファッション': ['メンズウェア', 'レディースウェア', 'シューズ', 'バッグ', 'アクセサリー'],
        '家電': ['テレビ', 'パソコン', '冷蔵庫', '洗濯機', 'エアコン'],
        '食品': ['生鮮食品', '加工食品', '飲料', 'お菓子', '調味料'],
        'その他': ['文具', '日用品', 'ペット用品', 'インテリア', 'ギフト']
    }
    
    data = []
    for date in dates:
        for _ in range(10):  # 1日あたり10件の取引を生成
            category = np.random.choice(list(categories.keys()))
            subcategory = np.random.choice(categories[category])
            customer_id = f'顧客{np.random.randint(1, 6)}'
            age = np.random.randint(20, 71)
            gender = np.random.choice(['男性', '女性'])
            region = np.random.choice(['東京', '大阪', '名古屋', '福岡', '札幌'])
            amount = np.random.randint(1000, 50000)
            payment = np.random.choice(['現金', 'クレジットカード', '電子マネー'])
            
            data.append({
                '購入日': date,
                '購入カテゴリー': category,
                '商品': subcategory,
                '顧客ID': customer_id,
                '年齢': age,
                '性別': gender,
                '地域': region,
                '購入金額': amount,
                '支払方法': payment
            })
    
    df = pd.DataFrame(data)
    return df

def show_overview_tab(filtered_df):
    """概要タブの表示"""
    # データ概要の表示
    with st.expander("データ概要", expanded=False):
        st.write("データサマリー")
        
        # 地域ごとの基本統計情報
        st.subheader("地域ごとの統計情報")
        region_stats = filtered_df.groupby('地域').agg({
            '売上': ['count', 'sum', 'mean'],
            '顧客': 'nunique'
        })
        region_stats.columns = ['取引件数', '総売上', '平均売上', 'ユニーク顧客数']
        
        # スタイリングを適用
        styled_region_stats = region_stats.style.format({
            '取引件数': '{:,.0f}',
            '総売上': '¥{:,.0f}',
            '平均売上': '¥{:,.0f}',
            'ユニーク顧客数': '{:,.0f}'
        }).background_gradient(cmap='YlGn')
        st.dataframe(styled_region_stats)
        
        # 性別ごとの基本統計情報
        st.subheader("性別ごとの統計情報")
        gender_stats = filtered_df.groupby('性別').agg({
            '売上': ['count', 'sum', 'mean'],
            '顧客': 'nunique'
        })
        gender_stats.columns = ['取引件数', '総売上', '平均売上', 'ユニーク顧客数']
        
        # スタイリングを適用
        styled_gender_stats = gender_stats.style.format({
            '取引件数': '{:,.0f}',
            '総売上': '¥{:,.0f}',
            '平均売上': '¥{:,.0f}',
            'ユニーク顧客数': '{:,.0f}'
        })
        st.dataframe(styled_gender_stats)
        
        # 既存の統計情報表示
        st.write("全体の統計情報")
        summary_df = filtered_df['売上'].describe()
        summary_df.index = [
            'データ数',
            '平均値',
            '標準偏差',
            '最小値',
            '第1四分位数',
            '中央値',
            '第3四分位数',
            '最大値'
        ]
        styled_df = pd.DataFrame(summary_df).style.format(formatter='{:,.2f}')
        st.dataframe(styled_df, use_container_width=True)
        
        st.write("データサンプル")
        sample_df = filtered_df.head().copy()
        if '日付' in sample_df.columns:
            sample_df['日付'] = sample_df['日付'].dt.strftime('%Y-%m-%d')
        sample_df = sample_df.style.format({
            '売上': '¥{:,.0f}'
        })
        st.dataframe(sample_df, use_container_width=True)
    
    # 基本統計情報の表示
    st.subheader("基本統計情報")
    total_sales = filtered_df['売上'].sum()
    avg_sales = filtered_df['売上'].mean()
    total_transactions = len(filtered_df)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("総売上", f"¥{total_sales:,.0f}")
    col2.metric("平均売上", f"¥{avg_sales:,.0f}")
    col3.metric("取引件数", f"{total_transactions:,}件")
    
    # 売上推移グラフ
    st.subheader("売上推移")
    # 日次売上の集計
    if '日付' not in filtered_df.columns and filtered_df.index.name == '日付':
        daily_sales = filtered_df['売上'].resample('ME').sum()
    else:
        daily_sales = filtered_df.set_index('日付')['売上'].resample('ME').sum()
    # 欠損値を0で埋める
    daily_sales = daily_sales.fillna(0)
    # グラフ表示用にデータフレームを作成
    sales_df = pd.DataFrame({
        '売上': daily_sales.values
    }, index=daily_sales.index.strftime('%Y-%m-%d'))
    
    # グラフの表示オプション
    chart_options = {
        'height': 400,
        'use_container_width': True
    }
    st.line_chart(sales_df, **chart_options)

def show_product_analysis_tab(filtered_df, data_processor):
    """カテゴリー分析タブの表示"""
    st.header("カテゴリー分析")

    # 地域×カテゴリーのクロス分析
    st.subheader("地域×カテゴリーのクロス分析")
    region_category_stats = pd.pivot_table(
        filtered_df,
        values='売上',
        index='地域',
        columns='カテゴリー',
        aggfunc=['sum', 'count'],
        fill_value=0
    )
    
    # マルチインデックスを解除して見やすく整形
    region_category_stats.columns = [f'{col[1]}_{col[0]}' for col in region_category_stats.columns]
    
    # スタイリングを適用
    styled_region_category_stats = region_category_stats.style.format({
        col: '¥{:,.0f}' if 'sum' in col else '{:,.0f}'
        for col in region_category_stats.columns
    }).background_gradient(cmap='YlGn')
    
    st.dataframe(styled_region_category_stats)

    # カテゴリーと性別でクロス集計
    st.subheader("カテゴリー×性別のクロス分析")
    cross_stats = pd.pivot_table(
        filtered_df,
        values='売上',
        index='カテゴリー',
        columns='性別',
        aggfunc=['sum', 'mean', 'count'],
        fill_value=0
    )
    
    # マルチインデックスを解除して見やすく整形
    cross_stats.columns = [f'{col[1]}_{col[0]}' for col in cross_stats.columns]
    
    # スタイリングを適用
    styled_cross_stats = cross_stats.style.format({
        col: '¥{:,.0f}' if '売上' in col else '{:,.0f}'
        for col in cross_stats.columns
    }).background_gradient(cmap='YlGn')
    
    st.dataframe(styled_cross_stats)

    # 既存のカテゴリー分析を表示
    category_metrics = data_processor.calculate_product_metrics(filtered_df)
    
    st.subheader("カテゴリー別統計情報")
    category_stats = category_metrics['category_stats'].copy()
    category_stats['総売上'] = category_stats['総売上'].map('{:,.0f}'.format)
    category_stats['平均売上'] = category_stats['平均売上'].map('{:,.0f}'.format)
    category_stats['取引回数'] = category_stats['取引回数'].map('{:,d}'.format)
    st.dataframe(category_stats.style.background_gradient())

    st.subheader("カテゴリー別売上推移")
    time_series = category_metrics['time_series']
    chart_options = {
        'height': 400,
        'use_container_width': True
    }
    st.line_chart(time_series, **chart_options)

def show_customer_analysis_tab(filtered_df: pd.DataFrame, data_processor: DataProcessor):
    """顧客分析タブの表示"""
    st.header("顧客分析")
    
    # 顧客分析の指標を計算
    customer_metrics = data_processor.calculate_customer_metrics(filtered_df)
    
    # 性別ごとの売上分布
    gender_sales_dist = filtered_df.groupby('性別')['売上'].sum()
    st.subheader("性別ごとの売上分布")
    st.bar_chart(gender_sales_dist)
    
    # RFM分析の表示
    if 'rfm' in customer_metrics:
        st.subheader("RFM分析")
        rfm_df = customer_metrics['rfm'].copy()
        
        # インデックスをリセットしてユニークにする
        rfm_df = rfm_df.reset_index()
        
        # 数値カラムのみを背景グラデーション対象にする
        numeric_columns = ['Recency', 'Frequency', 'Monetary', 'R', 'F', 'M']
        
        st.dataframe(
            rfm_df.style.background_gradient(
                cmap='YlGn',
                subset=numeric_columns
            )
        )
        
        # 地域ごとのセグメント分布
        if '地域' in rfm_df.columns:
            st.subheader("地域ごとの顧客セグメント分布")
            segment_region_counts = pd.crosstab(rfm_df['セグメント'], rfm_df['地域'])
            st.bar_chart(segment_region_counts)
    
    # 地域ごとの顧客分析
    st.subheader("地域ごとの顧客分析")
    region_customer_stats = filtered_df.groupby(['地域', '顧客']).agg({
        '売上': ['sum', 'mean', 'count'],
    }).round(0)
    
    region_customer_stats = region_customer_stats.groupby('地域').agg({
        ('売上', 'sum'): ['mean', 'std', 'min', 'max'],
        ('売上', 'count'): 'mean'
    }).round(0)
    
    region_customer_stats.columns = [
        '平均総売上', '総売上標準偏差', '最小総売上', '最大総売上',
        '平均取引回数'
    ]
    
    styled_region_stats = region_customer_stats.style.format({
        '平均総売上': '¥{:,.0f}',
        '総売上標準偏差': '¥{:,.0f}',
        '最小総売上': '¥{:,.0f}',
        '最大総売上': '¥{:,.0f}',
        '平均取引回数': '{:,.1f}'
    }).background_gradient(cmap='YlGn')
    st.dataframe(styled_region_stats)
    
    # 顧客行動分析の表示
    st.subheader("顧客行動分析")
    behavior_df = data_processor.analyze_customer_behavior(filtered_df)
    
    # スタイリングを適用
    styled_behavior = behavior_df.style.format({
        '取引回数': '{:,.0f}',
        '総売上': '¥{:,.0f}',
        '平均売上': '¥{:,.0f}',
        '売上標準偏差': '¥{:,.0f}',
        '取引期間': '{:,.0f}日',
        '平均取引間隔': '{:,.1f}日',
        '最終取引からの経過日数': '{:,.0f}日'
    }).background_gradient(
        subset=['総売上', '取引回数'],
        cmap='YlGn'
    )
    st.dataframe(styled_behavior, use_container_width=True)

def show_time_series_tab(filtered_df, data_processor):
    """時系列分析タブの表示"""
    st.subheader("時系列分析")
    
    # 地域別の時系列分析
    st.subheader("地域別売上推移")
    region_time_series = filtered_df.pivot_table(
        values='売上',
        index='日付',
        columns='地域',
        aggfunc='sum'
    ).fillna(0)
    
    # 日次データをリサンプリング
    region_time_series = region_time_series.resample('ME').sum()
    
    # グラフの表示
    st.line_chart(region_time_series)
    
    # 既存の時系列分析を表示
    time_metrics = data_processor.calculate_time_series_metrics(filtered_df)
    
    # 期間選択
    period = st.selectbox(
        "集計期間",
        ["日次", "週次", "月次"],
        index=1
    )
    
    # 期間別データの表示
    if period == "日次":
        metrics_df = time_metrics['daily']
        col_prefix = '日次'
    elif period == "週次":
        metrics_df = time_metrics['weekly']
        col_prefix = '週次'
    else:
        metrics_df = time_metrics['monthly']
        col_prefix = '月次'
    
    st.write(f"{period}データ")
    st.dataframe(metrics_df)
    
    # 売上推移グラフ
    st.subheader(f"{period}売上推移")
    sales_data = pd.DataFrame({
        '期間': metrics_df.index,
        '売上': metrics_df[f'{col_prefix}売上']
    }).set_index('期間')
    st.line_chart(sales_data)
    
    # トレンド分析
    if st.checkbox("トレンド分析を表示"):
        st.write("トレンド分析")
        trend_df = data_processor.analyze_trends(filtered_df, period)
        trend_data = pd.DataFrame({
            '期間': trend_df.index.strftime('%Y-%m-%d'),
            '売上': trend_df['売上'],
            '7期間移動平均': trend_df['7期間移動平均'],
            '30期間移動平均': trend_df['30期間移動平均']
        }).set_index('期間')
        st.line_chart(trend_data)
        
        # 季節性分析
        st.write("季節性分析")
        seasonality_df = data_processor.analyze_seasonality(filtered_df, period)
        if period == "日次":
            seasonality_df.index = seasonality_df.index.astype(str)
        st.dataframe(seasonality_df)

def show_validation_results(filtered_df: pd.DataFrame, data_processor: DataProcessor):
    """検証結果の表示"""
    st.subheader("データ分析の検証")
    
    with st.expander("分析結果の検証", expanded=False):
        validation_results = data_processor.validate_analysis_results(filtered_df)
        
        # 検証結果の表示
        for item, result in validation_results.items():
            status = "✅ 正常" if result else "❌ 要確認"
            color = "green" if result else "red"
            st.markdown(f"**{item}**: :{color}[{status}]")
        
        # 詳細情報の表示
        if st.checkbox("詳細情報を表示"):
            # 売上データの基本統計量のみを表示
            st.write("基本統計量:")
            stats_df = filtered_df['売上'].describe().round(2)
            st.dataframe(stats_df)
            
            st.write("日付範囲:")
            # 日付カラムの存在確認とアクセス
            if '日付' in filtered_df.columns:
                date_col = filtered_df['日付']
            elif filtered_df.index.name == '日付':
                date_col = filtered_df.index
            else:
                st.warning("日付カラムが見つかりません")
                return
            
            # 日付を文字列形式で表示
            st.write(f"開始日: {date_col.min().strftime('%Y-%m-%d')}")
            st.write(f"終了日: {date_col.max().strftime('%Y-%m-%d')}")
            
            st.write("異常値の検出:")
            mean_sales = filtered_df['売上'].mean()
            std_sales = filtered_df['売上'].std()
            outliers = filtered_df[abs(filtered_df['売上'] - mean_sales) > 3 * std_sales]
            
            # 異常値の統計情報を表示
            st.write(f"異常値の数: {len(outliers):,}件")
            st.write(f"全データに対する割合: {(len(outliers) / len(filtered_df)) * 100:.2f}%")
            
            if len(outliers) > 0:
                st.write("異常値の統計:")
                outlier_stats = outliers['売上'].describe().round(2)
                st.dataframe(outlier_stats)

def main():
    st.title("売上分析ダッシュボード")
    
    # データの読み込み
    with st.expander("データ読み込み設定", expanded=False):
        df = load_data()
        if df is None:
            st.warning("有効なデータがありません。CSVファイルをアップロードするか、サンプルデータを使用してください。")
            return
    
    # データプロセッサーの初期化
    data_processor = DataProcessor(df)
    df = data_processor.df  # 前処理済みのデータフレームを使用
    
    # サイドバーのフィルター
    st.sidebar.title("データフィルター")
    
    # 日付範囲フィルター
    st.sidebar.subheader("期間選択")
    min_date = df['日付'].min().date()
    max_date = df['日付'].max().date()
    start_date = st.sidebar.date_input("開始日", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("終了日", max_date, min_value=min_date, max_value=max_date)
    
    # カテゴリーフィルター
    st.sidebar.subheader("カテゴリー選択")
    available_categories = ["すべて"] + sorted(df['カテゴリー'].unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "カテゴリーを選択",
        available_categories,
        default=["すべて"],
        label_visibility="collapsed"
    )

    # 売上金額フィルター（緑色のスライダー）
    st.sidebar.subheader("売上金額範囲")
    st.sidebar.markdown(
        """
        <style>
        /* スライダーのトラック部分を緑色に */
        .stSlider [data-baseweb="slider"] div[class*="Track"] div {
            background-color: #28a745 !important;
        }
        /* スライダーのつまみ部分を緑色に */
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background-color: #28a745 !important;
            border-color: #28a745 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    min_sales = int(df['売上'].min())
    max_sales = int(df['売上'].max())
    sales_range = st.sidebar.slider(
        "売上金額範囲を選択",
        min_value=min_sales,
        max_value=max_sales,
        value=(min_sales, max_sales),
        step=1000,
        format="¥%d"
    )
    
    # 顧客フィルター
    st.sidebar.subheader("顧客選択")
    available_customers = ["すべて"] + sorted(df['顧客'].unique())
    selected_customers = st.sidebar.multiselect(
        "顧客を選択",
        available_customers,
        default=["すべて"],
        label_visibility="collapsed"
    )

    # 性別フィルター
    st.sidebar.subheader("性別選択")
    available_genders = ["すべて", "男性", "女性"]
    selected_genders = st.sidebar.multiselect(
        "性別を選択",
        available_genders,
        default=["すべて"],
        label_visibility="collapsed"
    )

    # 地域フィルター
    st.sidebar.subheader("地域選択")
    available_regions = ["すべて"] + sorted(df['地域'].unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "地域を選択",
        available_regions,
        default=["すべて"],
        label_visibility="collapsed"
    )

    # カテゴリーと顧客の選択ロジック
    if "すべて" in selected_categories:
        selected_categories = df['カテゴリー'].unique().tolist()
    
    if "すべて" in selected_customers:
        selected_customers = df['顧客'].unique().tolist()

    # 性別の選択ロジック
    if "すべて" in selected_genders:
        selected_genders = df['性別'].unique().tolist()

    # 地域の選択ロジック
    if "すべて" in selected_regions:
        selected_regions = df['地域'].unique().tolist()
    
    # フィルター適用
    filtered_df = df[
        (df['日付'].dt.date >= start_date) &
        (df['日付'].dt.date <= end_date) &
        (df['売上'].between(sales_range[0], sales_range[1])) &
        (df['顧客'].isin(selected_customers)) &
        (df['カテゴリー'].isin(selected_categories)) &
        (df['性別'].isin(selected_genders)) &
        (df['地域'].isin(selected_regions))
    ]
    
    # フィルター後のレコード数を表示
    st.sidebar.markdown("---")
    st.sidebar.write(f"フィルター後のレコード数: {len(filtered_df):,}件")
    
    if len(filtered_df) == 0:
        st.warning("選択された条件に一致するデータがありません。フィルターを調整してください。")
        return
    
    # タブの作成
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 概要",
        "📦 カテゴリー分析",
        "👥 顧客分析",
        "📈 時系列分析",
        "🔍 検証結果"
    ])
    
    # 各タブの内容を表示
    with tab1:
        show_overview_tab(filtered_df)
    
    with tab2:
        show_product_analysis_tab(filtered_df, data_processor)
    
    with tab3:
        show_customer_analysis_tab(filtered_df, data_processor)
    
    with tab4:
        show_time_series_tab(filtered_df, data_processor)
    
    with tab5:
        show_validation_results(filtered_df, data_processor)

if __name__ == "__main__":
    main() 