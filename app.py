import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from openai import OpenAI

# ==========================================
# 1. 基础配置 (Configuration)
# ==========================================
st.set_page_config(
    page_title="稳盈AI - 债券私人顾问", 
    page_icon="💰", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔑 【重要】请在这里填入你的 DeepSeek API Key
# 在实际生产环境中，建议使用 st.secrets 管理密钥，不要直接硬编码在代码里
# API_KEY = "sk-XXXXXXXX" 
try:
    # st.secrets 是 Streamlit 专门用来读取环境变量的字典
    API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except FileNotFoundError:
    st.error("密钥未配置！请在 Secrets 中配置 DEEPSEEK_API_KEY。")
    st.stop()

BASE_URL = "https://api.deepseek.com"

# 初始化 DeepSeek 客户端
try:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
except Exception as e:
    st.error(f"⚠️ API 配置出错，请检查 Key 是否正确: {e}")

# ==========================================
# 2. 数据处理层 (Data Layer)
# ==========================================
@st.cache_data
def get_market_data():
    """
    获取宏观市场数据
    (目前使用模拟数据，确保演示稳定。后期可替换为 AkShare 真实接口)
    """
    # 生成最近 60 天的日期
    days = 60
    date_list = [datetime.now() - timedelta(days=x) for x in range(days)][::-1]
    
    # 模拟数据生成 (随机漫步)
    np.random.seed(42)
    cn_yields = [2.10] # 初始值
    us_yields = [4.20]
    
    for _ in range(days - 1):
        # 模拟每天微小的波动
        cn_yields.append(cn_yields[-1] + np.random.normal(0, 0.02))
        us_yields.append(us_yields[-1] + np.random.normal(0, 0.05))
        
    df = pd.DataFrame({
        '日期': date_list,
        '中国国债': np.round(cn_yields, 4),
        '美国国债': np.round(us_yields, 4)
    })
    return df

@st.cache_data
def get_etf_data():
    """
    获取推荐的债券 ETF 列表
    """
    data = {
        "代码": ["511260", "511010", "511090", "511220"],
        "名称": ["十年国债ETF", "国债ETF", "30年国债ETF", "城投债ETF"],
        "最新价": [103.5, 120.1, 105.2, 99.8],
        "近1月涨幅": ["+0.12%", "+0.05%", "+0.80%", "-0.02%"],
        "风险等级": ["R2 低风险", "R2 低风险", "R3 中风险", "R3 中风险"],
        "适合人群": ["稳健型", "保守型", "激进型", "稳健型"]
    }
    return pd.DataFrame(data)

# ==========================================
# 3. 页面 UI 布局 (Frontend)
# ==========================================

# --- 侧边栏: 用户设置 ---
with st.sidebar:
    st.header("⚙️ 顾问设置")
    
    # 1. 风险偏好设置
    user_risk = st.selectbox(
        "你的风险偏好", 
        ["保守型 (绝不亏本)", "稳健型 (跑赢通胀)", "激进型 (追求高波段)"],
        index=1
    )
    
    st.markdown("---")
    
    # 2. 功能介绍
    st.info(
        """
        **💡 提示:**
        - **首页:** 查看宏观“天气”。
        - **对话:** 问我具体的债券代码或投资建议。
        """
    )
    
    # 3. 清除历史按钮
    if st.button("🗑️ 清除对话历史"):
        st.session_state.messages = []
        st.rerun()

# --- 主界面 ---
st.title("💰 稳盈AI (BondBuddy)")
st.caption(f"—— 你的全天候债券私人顾问 | 当前模式: {user_risk}")

# 加载数据
df_macro = get_market_data()
df_etf = get_etf_data()

# 获取最新数据点
latest_cn = df_macro.iloc[-1]['中国国债']
latest_us = df_macro.iloc[-1]['美国国债']
prev_cn = df_macro.iloc[-2]['中国国债']

# --- 模块 1: 市场宏观看板 ---
st.subheader("1. 市场天气预报 🌤️")

# 使用 Streamlit 的列布局
col1, col2, col3 = st.columns(3)

with col1:
    delta_cn = round(latest_cn - prev_cn, 4)
    st.metric("🇨🇳 中国10年期国债收益率", f"{latest_cn}%", delta=f"{delta_cn}%", delta_color="inverse")
    # 注：收益率下跌代表债券价格上涨，所以 delta_color 用 inverse

with col2:
    st.metric("🇺🇸 美国10年期国债收益率", f"{latest_us}%")

with col3:
    # 简单的业务逻辑判断
    if latest_cn < 2.2:
        status_text = "🔥 牛市高位 (价格贵)"
        status_color = "red"
    elif latest_cn > 2.8:
        status_text = "💎 熊市低位 (便宜)"
        status_color = "green"
    else:
        status_text = "☁️ 震荡市"
        status_color = "gray"
        
    st.metric("当前市场状态", status_text)

# 画交互式图表 (Plotly)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_macro['日期'], y=df_macro['中国国债'], 
    mode='lines', name='中国国债 (10Y)',
    line=dict(color='#d62728', width=3)
))
fig.add_trace(go.Scatter(
    x=df_macro['日期'], y=df_macro['美国国债'], 
    mode='lines', name='美国国债 (10Y)',
    line=dict(color='#1f77b4', width=2, dash='dash')
))

fig.update_layout(
    title="近60天国债收益率走势",
    xaxis_title="日期",
    yaxis_title="收益率 (%)",
    hovermode="x unified",
    height=350,
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig, use_container_width=True)

# --- 模块 2: 智能对话区 ---
st.markdown("---")
st.subheader("2. AI 智能咨询 💬")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是你的债券顾问。看到上面的图表了吗？现在的市场有点意思。你想了解什么？"}
    ]

# 渲染历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理用户输入
if user_query := st.chat_input("输入你的问题... (例如：现在的行情适合买长债吗？)"):
    
    # 1. 展示用户问题
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. 构造 Prompt Context (注入上下文)
    context_data = f"""
    [当前市场核心数据]
    - 数据日期: {datetime.now().strftime('%Y-%m-%d')}
    - 中国10年期国债收益率: {latest_cn}% (收益率越低，债券价格越贵)
    - 美国10年期国债收益率: {latest_us}%
    
    [用户画像]
    - 风险偏好: {user_risk}
    
    [精选债券ETF池]
    {df_etf.to_string(index=False)}
    """
    
    system_prompt = f"""
    你是一个拥有10年经验的债券基金经理，现在为普通个人投资者提供咨询。
    
    【任务】
    基于提供的[当前市场核心数据]和[用户画像]，回答用户的问题。
    
    【原则】
    1. **说人话**：不要堆砌术语。如果提到“久期”或“YTM”，必须用大白话解释一遍。
    2. **有观点**：不要模棱两可。如果是牛市高位，明确提示风险；如果是低位，提示机会。
    3. **结合数据**：回答时必须引用上面的具体数值（例如：“现在的收益率是2.1%...”）。
    4. **推荐标的**：如果用户问买什么，优先从[精选债券ETF池]里挑选最匹配的。
    
    【背景信息】
    {context_data}
    """

    # 3. 调用 API 并流式输出
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                stream=True,
                temperature=0.7 
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # 保存 AI 回答到历史
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"❌ AI 掉线了: {e}")