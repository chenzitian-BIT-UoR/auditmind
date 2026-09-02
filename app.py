
import streamlit as st
from openai import OpenAI
import json
import time

# 配置区域
API_KEY = "sk-xxxxxxxxxxxxxxxx"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

#系统提示词：定义 AI 的角色和输出格式
SYSTEM_PROMPT = """你是一名资深审计师 AI Agent，专门分析企业财务文本中的风险信号。

用户会提供一段年报、公告或审计底稿文本。你需要：
1. 识别文本中所有潜在的风险信号句子
2. 对每个风险信号给出风险等级（高/中/低）和触发原因
3. 综合评估整体风险等级（高/中/低）
4. 给出专业的审计师建议

请严格按照以下 JSON 格式输出，不要输出任何其他内容：
{
  "risk_signals": [
    {
      "sentence": "原文中的风险句子",
      "level": "高/中/低",
      "reason": "为什么这句话有风险"
    }
  ],
  "overall_level": "高/中/低",
  "overall_score": 75,
  "summary": "对该文本风险状况的整体评述（2-3句话）",
  "recommendations": [
    "具体的审计建议1",
    "具体的审计建议2",
    "具体的审计建议3"
  ]
}

overall_score 是0-100的整数，0=无风险，100=极高风险。
"""


def analyze_text(text: str) -> dict:
    """调用 DeepSeek API 分析文本风险"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"请分析以下文本的审计风险：\n\n{text}"}
        ],
        temperature=0.2,
        max_tokens=2000,
    )
    raw = response.choices[0].message.content.strip()
    # 清理可能的 markdown 代码块标记
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def highlight_risks(original_text: str, signals: list) -> str:
    """在原文中高亮显示风险句子，高风险用背景色，中低风险用下划线"""
    style_map = {
    "高": "background-color:#ff4b4b33; border-bottom: 2px solid #ff4b4b; padding: 1px 2px;",
    "中": "background-color:transparent; border-bottom: 2px solid #ffa500; padding: 1px 2px;",
    "低": "background-color:transparent; border-bottom: 2px solid #2ecc71; padding: 1px 2px; display:inline;",

    }

    result = original_text

    for sig in sorted(signals, key=lambda x: len(x["sentence"]), reverse=True):
        sentence = sig["sentence"].strip()
        style = style_map.get(sig["level"], "")

        if sentence in result:
            result = result.replace(
                sentence,
                f'<mark style="{style}">{sentence}</mark>',
                1
            )
        else:
            short = sentence[:20]
            if short in result:
                idx = result.index(short)
                end = idx + len(sentence)
                actual = result[idx:end]
                result = result[:idx] + f'<mark style="{style}">{actual}</mark>' + result[end:]

    result = result.replace("\n", "<br>")
    return result




# 示例文本，方便评委快速演示 
SAMPLE_TEXT = """本报告期内，公司实现营业收入38.6亿元，同比增长12.3%。
然而，公司应收账款余额较年初增加87%，达到14.2亿元，账龄超过一年的应收账款占比达34%，
坏账风险显著上升。同期，公司经营活动产生的现金流量净额为-2.1亿元，
连续两个季度呈现负值，与净利润存在较大背离。
公司前五大客户集中度达到71%，其中第一大客户贡献收入占比42%，
客户集中风险较为突出。此外，公司存货周转率由上年的6.8次下降至4.2次，
存货积压情况有所加剧。公司管理层表示，上述变化主要系行业周期性调整所致，
预计下一报告期将有所改善。"""



#  页面布局
st.set_page_config(
    page_title="AuditMind · 智能审计风险分析",
    page_icon="🔍",
    layout="wide"
)

# 顶部标题区 
st.markdown("""
<div style="background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 100%);
            padding: 2rem 2.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
    <h1 style="color: white; margin:0; font-size: 1.8rem;">
        🔍 AuditMind
    </h1>
    <p style="color: #86efac; margin: 0.3rem 0 0 0; font-size: 1rem;">
        AI 驱动的智能审计风险分析 Agent · 2026 Deloitte Digital Camp
    </p>
</div>
""", unsafe_allow_html=True)

# 左右两栏布局 
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("#### 📄 输入财务文本")
    st.caption("支持年报、公告、审计底稿等非结构化文本")

    # 一键填入示例
    if st.button("📋 填入示例文本", use_container_width=True):
        st.session_state["input_text"] = SAMPLE_TEXT

    input_text = st.text_area(
        label="财务文本",
        value=st.session_state.get("input_text", ""),
        height=320,
        placeholder="在此粘贴年报段落、审计底稿或公司公告……",
        label_visibility="collapsed"
    )

    analyze_btn = st.button(
        "🚀 开始风险分析",
        type="primary",
        use_container_width=True,
        disabled=not input_text.strip()
    )

with col_right:
    st.markdown("#### 📊 分析结果")

    if not analyze_btn:
        st.info("👈 在左侧输入文本，点击「开始风险分析」查看结果")

    if analyze_btn and input_text.strip():
        with st.spinner("AI Agent 正在分析中……"):
            try:
                result = analyze_text(input_text)
            except json.JSONDecodeError:
                st.error("AI 返回格式异常，请重试。")
                st.stop()
            except Exception as e:
                st.error(f"调用失败：{e}")
                st.stop()

        # 整体风险评分 
        level = result.get("overall_level", "中")
        score = result.get("overall_score", 50)
        level_color = {"高": "#ff4b4b", "中": "#ffa500", "低": "#2ecc71"}.get(level, "#888")
        level_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(level, "⚪")

        st.markdown(f"""
        <div style="background:{level_color}18; border:1px solid {level_color}44;
                    border-radius:10px; padding:1rem 1.5rem; margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:1rem;">
                <div>
                    <div style="font-size:0.8rem; color:#888;">整体风险等级</div>
                    <div style="font-size:1.6rem; font-weight:700; color:{level_color};">
                        {level_emoji} {level}风险
                    </div>
                </div>
                <div style="margin-left:auto; text-align:right;">
                    <div style="font-size:0.8rem; color:#888;">风险评分</div>
                    <div style="font-size:2rem; font-weight:700; color:{level_color};">{score}</div>
                    <div style="font-size:0.7rem; color:#aaa;">/ 100</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 风险摘要
        st.markdown("**🧠 AI 风险评述**")
        st.markdown(
            f'<div style="background:#f8f9fa; border-radius:8px; padding:0.8rem 1rem; '
            f'color:#333; font-size:0.9rem;">{result.get("summary", "")}</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # 风险信号明细
        signals = result.get("risk_signals", [])
        st.markdown(f"**⚠️ 识别到 {len(signals)} 个风险信号**")

        color_map = {"高": "#ff4b4b", "中": "#ffa500", "低": "#2ecc71"}
        for i, sig in enumerate(signals):
            c = color_map.get(sig["level"], "#888")
            with st.expander(f"{sig['level']}风险 · {sig['sentence'][:30]}……"):
                st.markdown(f"""
                <div style="border-left: 3px solid {c}; padding-left: 0.8rem;">
                    <div style="font-size:0.85rem; color:#555; margin-bottom:0.4rem;">
                        📌 原文句子
                    </div>
                    <div style="font-style:italic; color:#333;">"{sig['sentence']}"</div>
                    <div style="font-size:0.85rem; color:#555; margin-top:0.6rem;">
                        💡 触发原因
                    </div>
                    <div style="color:#333;">{sig['reason']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # 审计建议
        st.markdown("**📋 审计师建议**")
        for rec in result.get("recommendations", []):
            st.markdown(f"- {rec}")

        st.markdown("---")

        # 高亮原文
        with st.expander("🔍 查看风险高亮原文"):
            # 图例
            st.markdown("""
            <div style="display:flex; gap:1.5rem; margin-bottom:0.8rem; font-size:0.82rem;">
                <span>
                    <mark style="background-color:#ff4b4b33; border-bottom:2px solid #ff4b4b; padding:1px 4px;">
                        高风险
                    </mark>（背景高亮）
                </span>
                <span>
                    <mark style="background-color:transparent; border-bottom:2px solid #ffa500; padding:1px 4px;">
                        中风险
                    </mark>（橙色下划线）
                </span>
                <span>
                    <mark style="background-color:transparent; border-bottom:2px solid #2ecc71; padding:1px 4px;">
                        低风险
                    </mark>（绿色下划线）
                </span>
            </div>
            """, unsafe_allow_html=True)

            highlighted = highlight_risks(input_text, signals)
            st.markdown(
                f'<div style="line-height:2.0; font-size:0.9rem;">{highlighted}</div>',
                unsafe_allow_html=True
            )

# 底部说明
st.markdown("---")
st.caption(
    "AuditMind · Team J · 陈梓天 · 北京理工大学 · "
    "2026 Deloitte Digital Camp"
)

