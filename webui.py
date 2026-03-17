"""
Autonomous AI Engine - Web UI
一个简单的Web界面，用于与AI Agent交互
"""
import streamlit as st
import requests
import json
import os
from datetime import datetime

# 配置
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="Autonomous AI Engine",
    page_icon="🤖",
    layout="wide"
)

# 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_name" not in st.session_state:
    st.session_state.agent_name = "chatbot"

def call_api(endpoint, method="GET", data=None):
    """调用API"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            resp = requests.get(url, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=60)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# 侧边栏 - 设置
with st.sidebar:
    st.title("⚙️ 设置")
    
    st.subheader("Agent配置")
    agent_name = st.text_input("Agent名称", value=st.session_state.agent_name)
    model = st.selectbox("模型", ["qwen3:8b", "deepseek-r1:8b", "deepseek-r1:14b"])
    
    if st.button("创建Agent"):
        result = call_api("/api/agents", "POST", {"name": agent_name, "model": model})
        if "error" not in result:
            st.success(f"Agent {agent_name} 创建成功!")
            st.session_state.agent_name = agent_name
        else:
            st.error(result.get("error", "创建失败"))
    
    st.divider()
    
    st.subheader("Memory")
    if st.button("查看记忆"):
        result = call_api("/api/memory/default/search?q=test")
        st.json(result)
    
    st.divider()
    
    st.subheader("任务历史")
    if st.button("刷新历史"):
        result = call_api("/api/tasks?limit=5")
        st.json(result)
    
    st.divider()
    
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

# 主界面
st.title("🤖 Autonomous AI Engine")

# 显示对话历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入框
if prompt := st.chat_input("输入你的问题..."):
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用Agent
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            result = call_api(
                f"/api/agents/{st.session_state.agent_name}/think",
                "POST",
                {"prompt": prompt}
            )
        
        if "error" in result:
            st.error(f"错误: {result['error']}")
            response = f"抱歉，出错了: {result['error']}"
        else:
            response = result.get("result", "无响应")
            st.markdown(response)
        
        # 保存回复
        st.session_state.messages.append({"role": "assistant", "content": response})

# 底部信息
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.caption(f"🤖 Autonomous AI Engine v0.1.4")
with col2:
    st.caption(f"📡 API: {API_BASE}")
