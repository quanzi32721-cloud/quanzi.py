import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 页面设置
st.set_page_config(page_title="股票实时分析工具", page_icon="📈", layout="wide")
st.title("📈 股票实时数据分析&买卖信号系统")
st.write("数据实时更新，所有买卖信号均基于严谨的量化策略，100%真实行情数据")

# 侧边栏设置（小白可以直接选，不用改代码）
st.sidebar.header("参数设置")
stock_code = st.sidebar.text_input("输入股票代码", value="600519")
short_day = st.sidebar.slider("短期均线天数", min_value=3, max_value=10, value=5)
long_day = st.sidebar.slider("中期均线天数", min_value=10, max_value=30, value=20)
start_date = st.sidebar.date_input("数据起始日期", value=pd.to_datetime("2024-01-01"))

# 自动抓取数据
if st.sidebar.button("点击开始分析（自动更新最新数据）"):
    with st.spinner("正在抓取交易所实时行情数据，分析中..."):
        # 1. 抓取数据
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code, 
                period="daily", 
                start_date=start_date.strftime("%Y%m%d"), 
                end_date=datetime.now().strftime("%Y%m%d"), 
                adjust="qfq"
            )
            spot_df = ak.stock_zh_a_spot_em()
            stock_name = spot_df[spot_df['代码'] == stock_code]['名称'].values[0]
            latest_price = spot_df[spot_df['代码'] == stock_code]['最新价'].values[0]
            st.success(f"✅ 数据抓取成功！当前分析标的：{stock_name}({stock_code})")
        except Exception as e:
            st.error(f"数据抓取失败，请检查股票代码是否正确：{e}")
            st.stop()
        
        # 2. 计算核心指标
        df['短期均线'] = df['收盘'].rolling(window=short_day).mean()
        df['中期均线'] = df['收盘'].rolling(window=long_day).mean()
        df['EMA12'] = df['收盘'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['收盘'].ewm(span=26, adjust=False).mean()
        df['DIF'] = df['EMA12'] - df['EMA26']
        df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
        df['MACD'] = 2 * (df['DIF'] - df['DEA'])
        
        # 3. 计算买卖信号
        latest_data = df.iloc[-1]
        prev_data = df.iloc[-2]
        is_gold_cross = (prev_data['短期均线'] <= prev_data['中期均线']) & (latest_data['短期均线'] > latest_data['中期均线'])
        is_death_cross = (prev_data['短期均线'] >= prev_data['中期均线']) & (latest_data['短期均线'] < latest_data['中期均线'])
        macd_gold_cross = (prev_data['DIF'] <= prev_data['DEA']) & (latest_data['DIF'] > latest_data['DEA'])
        macd_death_cross = (prev_data['DIF'] >= prev_data['DEA']) & (latest_data['DIF'] < latest_data['DEA'])
        
        # 4. 生成建议
        if is_gold_cross and macd_gold_cross:
            signal = "✅ 强烈买入信号"
            suggest = "短期均线上穿中期均线（均线金叉），同时DIF上穿DEA（MACD金叉），双指标共振，短期上涨趋势确立，资金进场信号明确，符合买入条件。"
            color = "#00b42a"
        elif is_gold_cross:
            signal = "⚠️ 弱买入信号"
            suggest = "短期均线上穿中期均线（均线金叉），但MACD未同步金叉，短期趋势有转强迹象，但信号不够稳定，建议观望确认，不急于买入。"
            color = "#ff7d00"
        elif is_death_cross and macd_death_cross:
            signal = "❌ 强烈卖出信号"
            suggest = "短期均线下穿中期均线（均线死叉），同时DIF下穿DEA（MACD死叉），双指标共振，短期下跌趋势确立，资金离场信号明确，符合卖出条件，及时规避风险。"
            color = "#ff0000"
        elif is_death_cross:
            signal = "⚠️ 弱卖出信号"
            suggest = "短期均线下穿中期均线（均线死叉），但MACD未同步死叉，短期趋势有转弱迹象，信号不够稳定，建议减仓观望，不急于清仓。"
            color = "#ff7d00"
        else:
            if latest_data['短期均线'] > latest_data['中期均线']:
                signal = "📈 持有观望"
                suggest = "短期均线在中期均线上方，处于上涨趋势中，无明确买卖信号，继续持有观望即可。"
                color = "#00b42a"
            else:
                signal = "📉 空仓观望"
                suggest = "短期均线在中期均线下方，处于下跌趋势中，无明确买卖信号，继续空仓观望，不要抄底。"
                color = "#ff0000"
        
        # 页面展示核心数据
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="最新价格", value=f"{round(latest_price,2)} 元")
        with col2:
            st.metric(label=f"{short_day}日短期均线", value=f"{round(latest_data['短期均线'],2)} 元")
        with col3:
            st.metric(label=f"{long_day}日中期均线", value=f"{round(latest_data['中期均线'],2)} 元")
        with col4:
            st.markdown(f"<h3 style='color:{color}'>{signal}</h3>", unsafe_allow_html=True)
        
        # 展示分析建议
        st.subheader("📝 严谨分析建议")
        st.info(suggest)
        
        # 展示均线走势图
        st.subheader("📊 价格&均线走势图")
        fig, ax = plt.subplots(figsize=(12,6), dpi=300)
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        ax.plot(df['日期'], df['收盘'], label='收盘价', color='#1f77b4', linewidth=1)
        ax.plot(df['日期'], df['短期均线'], label=f'{short_day}日短期均线', color='#ff7f0e', linewidth=2)
        ax.plot(df['日期'], df['中期均线'], label=f'{long_day}日中期均线', color='#2ca02c', linewidth=2)
        ax.set_title(f"{stock_name}({stock_code}) 价格与均线走势", fontsize=14)
        ax.set_xlabel("日期", fontsize=12)
        ax.set_ylabel("价格（元）", fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        
        # 展示MACD走势图
        st.subheader("📈 MACD指标走势图")
        fig2, ax2 = plt.subplots(figsize=(12,4), dpi=300)
        ax2.plot(df['日期'], df['DIF'], label='DIF', color='#ff7f0e', linewidth=1.5)
        ax2.plot(df['日期'], df['DEA'], label='DEA', color='#2ca02c', linewidth=1.5)
        ax2.bar(df['日期'], df['MACD'], label='MACD', color=['#ff0000' if x < 0 else '#00b42a' for x in df['MACD']], alpha=0.5)
        ax2.axhline(y=0, color='black', linewidth=0.8)
        ax2.set_title(f"{stock_name}({stock_code}) MACD指标", fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig2)
        
        # 展示原始数据
        st.subheader("📋 完整历史数据（可核对）")
        st.dataframe(df.sort_values('日期', ascending=False), use_container_width=True)

# 底部说明
st.divider()
st.caption("⚠️ 风险提示：本工具仅供学习交流使用，所有分析建议均基于历史数据量化计算，不构成任何投资建议，股市有风险，投资需谨慎。")
st.caption("📊 数据来源：沪深交易所官方行情数据，由akshare提供实时数据接口")
