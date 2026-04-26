import streamlit as st
import pandas as pd
import akshare as ak

st.set_page_config(layout="wide")
st.title("📊 CPO / 算力 实盘监控系统")

TARGET_STOCKS = [
    "中际旭创","新易盛","天孚通信","剑桥科技","光迅科技",
    "浪潮信息","中科曙光","工业富联","紫光股份",
    "润泽科技","数据港","宝信软件"
]

@st.cache_data(ttl=300)
def load_data():
    df = ak.stock_zh_a_spot_em()
    df = df[df["名称"].isin(TARGET_STOCKS)]

    df = df.sort_values("成交量", ascending=False).head(10)

    df["sentiment"] = 50 + df["涨跌幅"] * 2
    df["sentiment"] = df["sentiment"].clip(20, 80)

    df["momentum"] = df["涨跌幅"]

    flow = ak.stock_fund_flow_individual(symbol="即时")
    flow = flow[["名称","主力净占比"]]

    df = df.merge(flow, on="名称", how="left")

    df["flow_score"] = 50 + df["主力净占比"] * 2
    df["flow_score"] = df["flow_score"].fillna(50)

    df["rank"] = df["成交量"].rank(ascending=False)
    df["volume_score"] = 100 - df["rank"] * 10

    df["score"] = (
        0.4 * df["sentiment"] +
        0.2 * df["momentum"] +
        0.2 * df["volume_score"] +
        0.2 * df["flow_score"]
    )

    df["signal"] = "HOLD"

    df.loc[
        (df["sentiment"] < 40) &
        (df["momentum"] < -2) &
        (df["flow_score"] > 55),
        "signal"
    ] = "BUY"

    df.loc[
        (df["sentiment"] > 65) &
        (df["flow_score"] < 45),
        "signal"
    ] = "SELL"

    df.rename(columns={"名称": "stock","成交量": "volume"}, inplace=True)

    return df

st.autorefresh(interval=300000, key="refresh")

df = load_data()

st.subheader("🔥 成交量Top10")
st.dataframe(df)

st.subheader("🚨 交易信号")
buy = df[df["signal"] == "BUY"]
sell = df[df["signal"] == "SELL"]

col1, col2 = st.columns(2)

with col1:
    st.write("🔥 买入")
    st.dataframe(buy)

with col2:
    st.write("⚠️ 卖出")
    st.dataframe(sell)

st.subheader("📈 情绪")
st.metric("市场情绪", round(df["sentiment"].mean(),2))
