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
            # CSVファイルの読み込み（日付列を適切に処理）
            df = pd.read_csv(uploaded_file, parse_dates=['日付'])
            
            # 必須カラムの確認
            required_columns = ['日付', '商品', '顧客', '売上']
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
    products = ['商品A', '商品B', '商品C', '商品D', '商品E']
    customers = ['顧客1', '顧客2', '顧客3', '顧客4', '顧客5']
    
    data = []
    for date in dates:
        for _ in range(10):  # 1日あたり10件の取引を生成
            product = np.random.choice(products)
            customer = np.random.choice(customers)
            amount = np.random.randint(1000, 50000)
            data.append({
                '日付': date,
                '商品': product,
                '顧客': customer,
                '売上': amount
            })
    
    df = pd.DataFrame(data)
    df['日付'] = pd.to_datetime(df['日付'])
    return df

def show_overview_tab(filtered_df):
    """概要タブの表示"""
    # データ概要の表示
    with st.expander("データ概要", expanded=False):
        st.write("データサマリー")
        # 売上のみの統計情報を表示
        summary_df = filtered_df['売上'].describe()
        # インデックス名を先に変更
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
        # スタイリングを適用
        summary_df = pd.DataFrame(summary_df).style.format(formatter='{:.2f}')
        st.dataframe(summary_df, use_container_width=True)
        
        st.write("データサンプル")
        # サンプルデータの表示用にコピーを作成
        sample_df = filtered_df.head().copy()
        # 日付のフォーマットを変更
        if '日付' in sample_df.columns:
            sample_df['日付'] = sample_df['日付'].dt.strftime('%Y-%m-%d')
        # 売上のフォーマットを変更
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
        daily_sales = filtered_df['売上'].resample('D').sum()
    else:
        daily_sales = filtered_df.set_index('日付')['売上'].resample('D').sum()
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
    """商品分析タブの表示"""
    st.header("商品分析")
    
    # 分析期間の選択
    analysis_period = st.selectbox(
        "分析期間",
        ["日次", "週次", "月次"],
        index=1
    )
    
    # 商品メトリクスの計算
    product_metrics = data_processor.calculate_product_metrics(filtered_df)
    
    # 商品別統計情報の表示
    st.subheader("商品別統計情報")
    stats_df = product_metrics['stats'].copy()
    # 数値フォーマットの適用
    stats_df = stats_df.style.format({
        '総売上': '¥{:,.0f}',
        '平均売上': '¥{:,.0f}',
        '取引回数': '{:,.0f}',
        '最大売上': '¥{:,.0f}',
        '最小売上': '¥{:,.0f}'
    }).background_gradient(subset=['総売上', '取引回数'], cmap='YlGn')
    st.dataframe(stats_df, use_container_width=True)
    
    # 商品別成長率の計算と表示
    st.subheader("商品別成長率")
    growth_df = data_processor.calculate_growth_rates(filtered_df, '商品', analysis_period)
    
    # 成長率のヒートマップ表示
    if not growth_df.empty:
        # NaNを0に置換
        growth_df = growth_df.fillna(0)
        # スタイリングを適用
        styled_growth = growth_df.style.format('{:,.1f}%').background_gradient(
            cmap='YlGn',
            vmin=-50,
            vmax=50
        )
        st.dataframe(styled_growth, use_container_width=True)
    
    # 商品別売上推移グラフ
    st.subheader("商品別売上推移")
    time_series = product_metrics['time_series']
    
    # グラフ表示用にデータを整形
    time_series.index = time_series.index.strftime('%Y-%m-%d')
    
    # グラフの表示オプション
    chart_options = {
        'height': 400,
        'use_container_width': True
    }
    st.line_chart(time_series, **chart_options)

def show_customer_analysis_tab(filtered_df: pd.DataFrame, data_processor: DataProcessor):
    """顧客分析タブの表示"""
    st.header("顧客分析")
    
    # 顧客メトリクスの計算
    customer_metrics = data_processor.calculate_customer_metrics(filtered_df)
    
    # 顧客基本統計情報の表示
    st.subheader("顧客基本統計情報")
    stats_df = customer_metrics['stats'].copy()
    # 数値フォーマットの適用
    stats_df = stats_df.style.format({
        '総売上': '¥{:,.0f}',
        '平均売上': '¥{:,.0f}',
        '取引回数': '{:,.0f}',
        '最大売上': '¥{:,.0f}',
        '最小売上': '¥{:,.0f}'
    }).background_gradient(subset=['総売上', '取引回数'], cmap='YlGn')
    st.dataframe(stats_df, use_container_width=True)
    
    # RFM分析の表示
    st.subheader("RFM分析")
    rfm_df = customer_metrics['rfm'].copy()
    
    # RFMスコアの分布を表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Recency分布")
        r_counts = rfm_df['R'].value_counts().sort_index()
        st.bar_chart(r_counts)
    
    with col2:
        st.write("Frequency分布")
        f_counts = rfm_df['F'].value_counts().sort_index()
        st.bar_chart(f_counts)
    
    with col3:
        st.write("Monetary分布")
        m_counts = rfm_df['M'].value_counts().sort_index()
        st.bar_chart(m_counts)
    
    # セグメント分布の表示
    st.subheader("顧客セグメント分布")
    segment_counts = rfm_df['セグメント'].value_counts()
    st.bar_chart(segment_counts)
    
    # RFMの詳細データ表示
    with st.expander("RFM詳細データ", expanded=False):
        # スタイリングを適用
        styled_rfm = rfm_df.style.format({
            'Recency': '{:,.0f}日',
            'Frequency': '{:,.0f}回',
            'Monetary': '¥{:,.0f}',
            'R': '{:,.0f}',
            'F': '{:,.0f}',
            'M': '{:,.0f}'
        }).background_gradient(
            subset=['Monetary', 'Frequency'],
            cmap='YlOrRd'
        )
        st.dataframe(styled_rfm, use_container_width=True)
    
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
    
    # 時系列指標の計算
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
    
    # 商品フィルター
    st.sidebar.subheader("商品選択")
    st.sidebar.markdown(
        """
        <style>
        /* マルチセレクトの選択項目の背景色を緑に */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #28a745 !important;
        }
        /* 選択項目の削除ボタンの色を白に */
        .stMultiSelect [data-baseweb="tag"] span[role="button"] {
            color: white !important;
        }
        /* 選択項目のテキストの色を白に */
        .stMultiSelect [data-baseweb="tag"] span {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    available_products = sorted(df['商品'].unique())
    selected_products = st.sidebar.multiselect(
        "商品を選択",
        available_products,
        default=available_products,
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
    available_customers = sorted(df['顧客'].unique())
    selected_customers = st.sidebar.multiselect(
        "顧客を選択",
        available_customers,
        default=available_customers,
        label_visibility="collapsed"
    )
    
    # フィルター適用
    filtered_df = df[
        (df['日付'].dt.date >= start_date) &
        (df['日付'].dt.date <= end_date) &
        (df['商品'].isin(selected_products)) &
        (df['売上'].between(sales_range[0], sales_range[1])) &
        (df['顧客'].isin(selected_customers))
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
        "📦 商品分析",
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