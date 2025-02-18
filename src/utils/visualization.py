import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import japanize_matplotlib

def plot_sales_trend(df: pd.DataFrame, date_column: str, sales_column: str):
    """
    売上推移の折れ線グラフを描画（インタラクティブ）
    
    Args:
        df (pd.DataFrame): 売上データ
        date_column (str): 日付カラム名
        sales_column (str): 売上カラム名
    """
    # 移動平均の計算
    df_ma = df.copy()
    df_ma['7日移動平均'] = df[sales_column].rolling(window=7, min_periods=1).mean()
    df_ma['30日移動平均'] = df[sales_column].rolling(window=30, min_periods=1).mean()
    
    # グラフの作成
    fig = go.Figure()
    
    # 実際の売上データ
    fig.add_trace(
        go.Scatter(
            x=df[date_column],
            y=df[sales_column],
            name='日次売上',
            mode='lines+markers',
            line=dict(color='#1f77b4'),
            hovertemplate='日付: %{x}<br>売上: ¥%{y:,.0f}<extra></extra>'
        )
    )
    
    # 7日移動平均
    fig.add_trace(
        go.Scatter(
            x=df_ma[date_column],
            y=df_ma['7日移動平均'],
            name='7日移動平均',
            line=dict(color='#ff7f0e', dash='dash'),
            hovertemplate='日付: %{x}<br>7日移動平均: ¥%{y:,.0f}<extra></extra>'
        )
    )
    
    # 30日移動平均
    fig.add_trace(
        go.Scatter(
            x=df_ma[date_column],
            y=df_ma['30日移動平均'],
            name='30日移動平均',
            line=dict(color='#2ca02c', dash='dash'),
            hovertemplate='日付: %{x}<br>30日移動平均: ¥%{y:,.0f}<extra></extra>'
        )
    )
    
    # レイアウトの設定
    fig.update_layout(
        title='売上推移',
        xaxis_title='日付',
        yaxis_title='売上 (円)',
        hovermode='x unified',
        showlegend=True,
        height=500,
        dragmode='zoom',  # ドラッグでズーム可能に
        modebar_add=['drawline', 'drawopenpath', 'eraseshape'],  # 追加のツール
        modebar_remove=['lasso', 'select'],  # 不要なツールを削除
    )
    
    # X軸の設定
    fig.update_xaxes(
        rangeslider=dict(visible=True),  # レンジスライダーを追加
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1週間", step="day", stepmode="backward"),
                dict(count=1, label="1ヶ月", step="month", stepmode="backward"),
                dict(count=3, label="3ヶ月", step="month", stepmode="backward"),
                dict(step="all", label="全期間")
            ])
        )
    )
    
    # Y軸のフォーマット設定
    fig.update_yaxes(tickformat=',')
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})

def plot_product_sales(df: pd.DataFrame, product_column: str, sales_column: str):
    """
    商品別売上の棒グラフとトレンドを描画（インタラクティブ）
    
    Args:
        df (pd.DataFrame): 売上データ
        product_column (str): 商品カラム名
        sales_column (str): 売上カラム名
    """
    # 商品別集計データの作成
    product_sales = df.groupby(product_column)[sales_column].sum().sort_values(ascending=True)
    
    # 商品別トレンドデータの作成
    product_trend = df.pivot_table(
        values=sales_column,
        index='日付',
        columns=product_column,
        aggfunc='sum'
    ).fillna(0)
    
    # サブプロットの作成
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('商品別売上合計', '商品別売上推移'),
        vertical_spacing=0.2,
        row_heights=[0.4, 0.6]
    )
    
    # 商品別売上合計（横棒グラフ）
    fig.add_trace(
        go.Bar(
            y=product_sales.index,
            x=product_sales.values,
            orientation='h',
            text=[f'¥{x:,.0f}' for x in product_sales.values],
            textposition='auto',
            name='売上合計',
            hovertemplate='商品: %{y}<br>売上: ¥%{x:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 商品別売上推移（折れ線グラフ）
    for product in product_trend.columns:
        fig.add_trace(
            go.Scatter(
                x=product_trend.index,
                y=product_trend[product],
                name=product,
                hovertemplate='日付: %{x}<br>売上: ¥%{y:,.0f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # レイアウトの設定
    fig.update_layout(
        height=800,
        showlegend=True,
        hovermode='x unified',
        dragmode='zoom',
        modebar_add=['drawline', 'drawopenpath', 'eraseshape'],
        modebar_remove=['lasso', 'select']
    )
    
    # X軸とY軸のフォーマット設定
    fig.update_xaxes(tickformat=',', row=1, col=1)
    fig.update_xaxes(
        title_text='日付',
        rangeslider=dict(visible=True),
        row=2, col=1
    )
    fig.update_yaxes(title_text='商品', row=1, col=1)
    fig.update_yaxes(title_text='売上 (円)', row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})

def plot_customer_analysis(df: pd.DataFrame, customer_column: str, sales_column: str):
    """
    顧客分析のヒートマップとトレンドを描画（インタラクティブ）
    
    Args:
        df (pd.DataFrame): 売上データ
        customer_column (str): 顧客カラム名
        sales_column (str): 売上カラム名
    """
    # 集計データの作成
    customer_metrics = df.groupby(customer_column).agg({
        sales_column: ['sum', 'mean', 'count']
    }).round(0)
    customer_metrics.columns = ['総売上', '平均売上', '取引回数']
    
    # ヒートマップデータの準備
    heatmap_data = customer_metrics.copy()
    for col in heatmap_data.columns:
        heatmap_data[col] = (heatmap_data[col] - heatmap_data[col].min()) / (heatmap_data[col].max() - heatmap_data[col].min())
    
    # ヒートマップの作成
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data.values.T,
        x=heatmap_data.index,
        y=heatmap_data.columns,
        colorscale='YlOrRd',
        hoverongaps=False,
        hovertemplate='顧客: %{x}<br>指標: %{y}<br>値: %{customdata:,.0f}<extra></extra>',
        customdata=customer_metrics.values.T
    ))
    
    fig_heatmap.update_layout(
        title='顧客分析ヒートマップ',
        xaxis_title='顧客',
        yaxis_title='指標',
        height=400,
        dragmode='zoom',
        modebar_add=['drawline', 'drawopenpath', 'eraseshape'],
        modebar_remove=['lasso', 'select']
    )
    
    # 顧客別トレンドの作成
    customer_trend = df.pivot_table(
        values=sales_column,
        index='日付',
        columns=customer_column,
        aggfunc='sum'
    ).fillna(0)
    
    fig_trend = go.Figure()
    
    for customer in customer_trend.columns:
        fig_trend.add_trace(
            go.Scatter(
                x=customer_trend.index,
                y=customer_trend[customer],
                name=customer,
                hovertemplate='日付: %{x}<br>売上: ¥%{y:,.0f}<extra></extra>'
            )
        )
    
    fig_trend.update_layout(
        title='顧客別売上推移',
        xaxis_title='日付',
        yaxis_title='売上 (円)',
        hovermode='x unified',
        height=400,
        dragmode='zoom',
        modebar_add=['drawline', 'drawopenpath', 'eraseshape'],
        modebar_remove=['lasso', 'select']
    )
    
    # X軸の設定
    fig_trend.update_xaxes(
        rangeslider=dict(visible=True),
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="1週間", step="day", stepmode="backward"),
                dict(count=1, label="1ヶ月", step="month", stepmode="backward"),
                dict(count=3, label="3ヶ月", step="month", stepmode="backward"),
                dict(step="all", label="全期間")
            ])
        )
    )
    
    # グラフの表示
    st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': True})
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': True}) 