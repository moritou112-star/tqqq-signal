import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="TQQQ Signal", page_icon="📈", layout="centered")

def clean(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=900)
def load_data():
    qqq = clean(yf.download("QQQ", period="2y", auto_adjust=True, progress=False))
    tqqq = clean(yf.download("TQQQ", period="1mo", auto_adjust=True, progress=False))
    qqq["SMA200"] = qqq["Close"].rolling(200).mean()
    qqq["GAP"] = qqq["Close"] / qqq["SMA200"] - 1
    return qqq.dropna(), tqqq.dropna()

st.title("TQQQ SIGNAL")
st.caption("V9固定ルール｜最新データで判定")

try:
    qqq, tqqq = load_data()
    now, prev = qqq.iloc[-1], qqq.iloc[-2]
    qclose, sma = float(now["Close"]), float(now["SMA200"])
    gap, tclose = float(now["GAP"]), float(tqqq.iloc[-1]["Close"])
    buy2 = qclose > sma*1.01 and float(prev["Close"]) > float(prev["SMA200"])*1.01

    if qclose < sma:
        signal, icon = "SELL", "🔴"
        message = "QQQが200日線を下回っています。V9では次の営業日始値でTQQQを売却する条件です。"
    elif buy2:
        signal, icon = "HOLD / BUY ZONE", "🟢"
        message = "QQQが200日線+1%を2営業日連続で上回っています。保有中ならHOLD、現金ならBUY条件です。"
    else:
        signal, icon = "WAIT", "🟡"
        message = "SELL条件ではありませんが、現金からのBUY条件もまだ成立していません。"

    st.markdown(f"""<div style="text-align:center;padding:24px;border:1px solid #ddd;border-radius:18px;margin:10px 0 22px">
    <div style="font-size:20px">{icon} 今日の判定</div>
    <div style="font-size:36px;font-weight:800;margin-top:6px">{signal}</div></div>""",
    unsafe_allow_html=True)

    a,b=st.columns(2); a.metric("QQQ",f"${qclose:.2f}"); b.metric("TQQQ",f"${tclose:.2f}")
    a,b=st.columns(2); a.metric("200日線",f"${sma:.2f}"); b.metric("200日線との乖離",f"{gap*100:+.2f}%")
    st.info(message)
    st.write(f"**現在値から200日線まで：{(sma/qclose-1)*100:.2f}%**")
    st.caption(f"判定データ日：{qqq.index[-1].date()}")

    with st.expander("V9ルール"):
        st.write("SELL：QQQ終値が200日線を下回る → 次営業日のTQQQ始値で売却")
        st.write("BUY：QQQ終値が200日線+1%を2営業日連続で上回る → 次営業日のTQQQ始値で購入")
        st.write("それ以外：HOLD / WAIT")
    st.warning("検証用表示です。実際の注文は出しません。")
except Exception as e:
    st.error("エラーが発生しました。")
    st.code(str(e))
